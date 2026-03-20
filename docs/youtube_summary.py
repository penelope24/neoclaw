"""
YouTube 视频内容总结 skill
依赖：pip install youtube-transcript-api

用法示例（在 neoclaw 中）：
    from tools.youtube_summary import YouTubeSummaryTool
    agent = Agent(llm=llm, tools=[ReadFileTool(), WriteFileTool(), YouTubeSummaryTool()])

然后直接跟 agent 说：
    "帮我总结这个视频：https://www.youtube.com/watch?v=xxxx"
"""

import re
from .base import BaseTool, ToolResult

# ── 尝试导入依赖，给出清晰的安装提示 ──────────────────────────────────────
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


# ── 工具本体 ──────────────────────────────────────────────────────────────
class YouTubeSummaryTool(BaseTool):

    @property
    def name(self) -> str:
        return "youtube_summary"

    @property
    def description(self) -> str:
        return (
            "获取 YouTube 视频的字幕并总结内容。"
            "会自动提取：内容摘要、关键要点、带时间戳的章节划分。"
            "输出语言与视频字幕语言一致。"
            "参数：url（YouTube 视频链接）"
        )

    # ── 公共入口 ──────────────────────────────────────────────────────────
    def run(self, url: str) -> ToolResult:
        if not _TRANSCRIPT_AVAILABLE:
            return ToolResult(
                success=False,
                output=(
                    "缺少依赖库，请先安装：\n"
                    "  pip install youtube-transcript-api"
                ),
            )

        video_id = self._extract_video_id(url)
        if not video_id:
            return ToolResult(
                success=False,
                output=f"无法识别视频 ID，请确认是合法的 YouTube 链接：{url}",
            )

        transcript_text, lang, error = self._fetch_transcript(video_id)
        if error:
            return ToolResult(success=False, output=error)

        # 把字幕原文返回给 agent，让 LLM 自行总结
        # agent 的 system prompt 已经描述了 tool 的用途，
        # LLM 收到字幕后会自然地进行结构化总结
        prompt_hint = self._build_summary_prompt(transcript_text, lang, video_id)
        return ToolResult(success=True, output=prompt_hint)

    # ── 私有方法 ──────────────────────────────────────────────────────────
    @staticmethod
    def _extract_video_id(url: str) -> str | None:
        """从各种格式的 YouTube 链接中提取 video ID。"""
        patterns = [
            r"[?&]v=([a-zA-Z0-9_-]{11})",   # 标准链接
            r"youtu\.be/([a-zA-Z0-9_-]{11})", # 短链接
            r"embed/([a-zA-Z0-9_-]{11})",     # 嵌入链接
            r"shorts/([a-zA-Z0-9_-]{11})",    # Shorts
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def _fetch_transcript(video_id: str) -> tuple[str, str, str | None]:
        """
        获取字幕文本。
        返回 (transcript_text, language, error_message)
        出错时 transcript_text 和 language 为空字符串，error_message 有内容。
        """
        api = YouTubeTranscriptApi()

        try:
            transcript_list = api.list(video_id)
        except VideoUnavailable:
            return "", "", f"视频不可用或已被删除（ID: {video_id}）"
        except TranscriptsDisabled:
            return "", "", "该视频已关闭字幕功能，无法获取文字内容。"
        except Exception as e:
            return "", "", f"获取字幕列表失败：{e}"

        # 优先顺序：手动字幕 > 自动生成字幕，语言不限
        try:
            transcript = transcript_list.find_manually_created_transcript(
                transcript_list._manually_created_transcripts.keys()
                or ["zh", "zh-Hans", "zh-Hant", "en"]
            )
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_generated_transcript(
                    transcript_list._generated_transcripts.keys()
                    or ["zh", "zh-Hans", "zh-Hant", "en"]
                )
            except NoTranscriptFound:
                return "", "", "该视频没有可用的字幕（包括自动生成字幕）。"

        try:
            snippets = transcript.fetch()
        except Exception as e:
            return "", "", f"字幕下载失败：{e}"

        lang = transcript.language
        # 拼接纯文本，保留换行以便 LLM 理解段落节奏
        lines = [s.text.strip() for s in snippets if s.text.strip()]
        full_text = "\n".join(lines)

        # 超长字幕截断，避免撑爆 context window（保留前 ~12000 字符）
        if len(full_text) > 12000:
            full_text = full_text[:12000] + "\n\n[字幕过长，以上为前半部分]"

        return full_text, lang, None

    @staticmethod
    def _build_summary_prompt(transcript: str, lang: str, video_id: str) -> str:
        """
        把字幕包装成结构化提示，引导 LLM 输出总结。
        这段文字会作为 tool 结果注入 agent 的对话历史，
        LLM 下一轮会基于它生成最终回复。
        """
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return f"""以下是 YouTube 视频的字幕内容（语言：{lang}）：
视频链接：{video_url}

--- 字幕开始 ---
{transcript}
--- 字幕结束 ---

请根据以上字幕，用与字幕相同的语言输出结构化总结，包含：
1. 内容摘要（2-4句话概括整个视频）
2. 关键要点（4-6条最重要的观点或信息）
3. 章节划分（按内容逻辑划分4-8个章节，每章节给出大致时间范围和简短描述）"""
