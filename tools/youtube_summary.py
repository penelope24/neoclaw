import re
import config
from .base import BaseTool, ToolResult
from llm.base import ChatOptions

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )
    _TRANSCRIPT_AVAILABLE = True
except ImportError:
    _TRANSCRIPT_AVAILABLE = False

_CHARS_PER_TOKEN = 4
_OVERHEAD_TOKENS = 2000
# 直接传入 LLM 的字符上限（超过则触发分段）
_DIRECT_THRESHOLD = (config.LLM_CONTEXT_WINDOW - _OVERHEAD_TOKENS) * _CHARS_PER_TOKEN
# 文章生成每段的字符大小（约 5000 tokens 输入，留足输出空间）
_ARTICLE_CHUNK_SIZE = 20_000


class YouTubeSummaryTool(BaseTool):

    def __init__(self, llm=None):
        self.llm = llm

    @property
    def name(self) -> str:
        return "youtube_summary"

    @property
    def description(self) -> str:
        return (
            "获取 YouTube 视频的字幕，生成一份完整的课堂笔记。"
            "输出包含：流畅的叙述文章、结构化知识点、以及简短总结。"
            "适合讲座、网课、演讲类视频。"
            "参数：url（YouTube 视频链接）"
        )

    # ── 主入口 ────────────────────────────────────────────────────────────────

    def run(self, url: str) -> ToolResult:
        if not _TRANSCRIPT_AVAILABLE:
            return ToolResult(
                success=False,
                output="缺少依赖库，请先安装：\n  pip install youtube-transcript-api",
            )

        video_id = self._extract_video_id(url)
        if not video_id:
            return ToolResult(
                success=False,
                output=f"无法识别视频 ID，请确认是合法的 YouTube 链接：{url}",
            )

        transcript, lang, error = self._fetch_transcript(video_id)
        if error:
            return ToolResult(success=False, output=error)

        if self.llm is None:
            # 没有 LLM，退化为直接返回字幕（兜底）
            truncated = transcript[:_DIRECT_THRESHOLD]
            return ToolResult(success=True, output=truncated)

        video_url = f"https://www.youtube.com/watch?v={video_id}"

        article = self._generate_article(transcript, lang)
        notes   = self._generate_notes(article, lang)
        summary = self._generate_summary(article, notes, lang)

        output = self._format_output(video_url, article, notes, summary)
        return ToolResult(success=True, output=output)

    # ── Step 1：文章生成 ──────────────────────────────────────────────────────

    def _generate_article(self, transcript: str, lang: str) -> str:
        """将字幕整理为流畅的叙述文章，长字幕分段生成后拼接。"""
        system = (
            f"你是一位专业的文字编辑。你的任务是将视频字幕整理为流畅的书面文章。"
            f"必须使用与字幕完全相同的语言（{lang}）输出，不得切换语言。"
            f"要求：\n"
            f"- 将口语化的碎句整理为连贯的书面语句，去除明显的停顿词和无意义重复\n"
            f"- 完整保留讲者的所有论述，包括举的例子、引用的数据、打的比方、以及对话片段\n"
            f"- 不压缩、不省略任何实质内容，目标是最大程度还原讲座原貌\n"
            f"- 不添加任何字幕以外的信息\n"
            f"- 按自然段落组织，不加标题\n"
            f"直接输出整理好的文章，不加任何说明。"
        )
        options = ChatOptions(max_tokens=4096)

        if len(transcript) <= _ARTICLE_CHUNK_SIZE:
            return self.llm.simple_chat(transcript, system_prompt=system, options=options)

        # 分段生成
        chunks = self._split_chunks(transcript, _ARTICLE_CHUNK_SIZE)
        parts = []
        for i, chunk in enumerate(chunks):
            prompt = (
                f"这是第 {i + 1}/{len(chunks)} 段字幕，"
                f"请使用 {lang} 整理为流畅的文章片段，完整保留所有例子和细节：\n\n{chunk}"
            )
            part = self.llm.simple_chat(prompt, system_prompt=system, options=options)
            parts.append(part)

        return "\n\n".join(parts)

    # ── Step 2：结构化笔记 ────────────────────────────────────────────────────

    def _generate_notes(self, article: str, lang: str) -> str:
        """从文章中提取核心知识点，自主选择最合适的呈现格式。"""
        system = (
            "你是一位善于整理知识的助教。请从以下文章中提取核心知识点，使用中文输出。"
            "根据内容性质自主选择最合适的 Markdown 格式：\n"
            "- 有对比关系 → 表格\n"
            "- 有步骤或流程 → 编号列表\n"
            "- 有核心术语 → 术语加定义\n"
            "- 有重要数据或例子 → 引用块\n"
            "提取 4-8 个最重要的知识点或结论，不重复文章原文，只保留精华。"
            "直接输出结构化笔记，不加任何说明。"
        )
        options = ChatOptions(max_tokens=3000)
        # 笔记的输入来自文章，文章可能很长，截取前 _DIRECT_THRESHOLD 字符已足够
        article_input = article[:_DIRECT_THRESHOLD]
        return self.llm.simple_chat(article_input, system_prompt=system, options=options)

    # ── Step 3：总结 ──────────────────────────────────────────────────────────

    def _generate_summary(self, article: str, notes: str, lang: str) -> str:
        """生成 100 字以内的一段话总结。"""
        system = (
            "请根据以下文章和笔记，用中文、100 字以内概括：这个视频讲了什么，看完能学到什么。"
            "直接输出总结，不加任何说明。"
        )
        options = ChatOptions(max_tokens=512)
        prompt = f"【文章节选】\n{article[:3000]}\n\n【笔记】\n{notes}"
        return self.llm.simple_chat(prompt, system_prompt=system, options=options)

    # ── 格式化输出 ────────────────────────────────────────────────────────────

    @staticmethod
    def _format_output(video_url: str, article: str, notes: str, summary: str) -> str:
        return (
            f"# 课堂笔记\n"
            f"视频：{video_url}\n\n"
            f"---\n\n"
            f"## 一、完整笔记\n\n"
            f"{article}\n\n"
            f"---\n\n"
            f"## 二、核心知识点\n\n"
            f"{notes}\n\n"
            f"---\n\n"
            f"## 三、总结\n\n"
            f"{summary}"
        )

    # ── 工具方法 ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_video_id(url: str) -> str | None:
        patterns = [
            r"[?&]v=([a-zA-Z0-9_-]{11})",
            r"youtu\.be/([a-zA-Z0-9_-]{11})",
            r"embed/([a-zA-Z0-9_-]{11})",
            r"shorts/([a-zA-Z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _fetch_transcript(video_id: str) -> tuple[str, str, str | None]:
        api = YouTubeTranscriptApi()

        try:
            transcript_list = api.list(video_id)
        except VideoUnavailable:
            return "", "", f"视频不可用或已被删除（ID: {video_id}）"
        except TranscriptsDisabled:
            return "", "", "该视频已关闭字幕功能，无法获取文字内容。"
        except Exception as e:
            return "", "", f"获取字幕列表失败：{e}"

        try:
            transcript = transcript_list.find_manually_created_transcript(
                list(transcript_list._manually_created_transcripts.keys())
            )
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_generated_transcript(
                    list(transcript_list._generated_transcripts.keys())
                )
            except NoTranscriptFound:
                return "", "", "该视频没有可用的字幕（包括自动生成字幕）。"

        try:
            snippets = transcript.fetch()
        except Exception as e:
            return "", "", f"字幕下载失败：{e}"

        lang = transcript.language
        lines = []
        for s in snippets:
            text = s.text.strip()
            if not text:
                continue
            seconds = int(s.start)
            timestamp = f"[{seconds // 60}:{seconds % 60:02d}]"
            lines.append(f"{timestamp} {text}")

        return "\n".join(lines), lang, None

    @staticmethod
    def _split_chunks(text: str, chunk_size: int) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunks.append(text[start:])
                break
            split_pos = text.rfind("\n", start, end)
            if split_pos == -1:
                split_pos = end
            chunks.append(text[start:split_pos])
            start = split_pos + 1
        return chunks
