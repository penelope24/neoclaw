"""
youtube_summary 测试套件

运行全部测试：
    pytest tests/test_youtube_summary.py -v

只跑快速测试（不需要网络/LLM）：
    pytest tests/test_youtube_summary.py -v -m "not network and not llm"

只跑字幕抓取测试：
    pytest tests/test_youtube_summary.py -v -m network

完整集成测试（需要网络 + 真实 LLM）：
    pytest tests/test_youtube_summary.py -v -m integration
"""

import re
import pytest
from unittest.mock import MagicMock
from tools.youtube_summary import YouTubeSummaryTool
from llm.base import BaseLLM, Message, ChatOptions


# ── Mock LLM ──────────────────────────────────────────────────────────────────

class MockLLM(BaseLLM):
    """返回固定字符串的假 LLM，用于隔离模型依赖。"""

    def __init__(self, response: str = "MOCK_RESPONSE"):
        self.response = response
        self.call_count = 0
        self.last_messages = None

    def chat(self, messages: list[Message], options: ChatOptions | None = None) -> str:
        self.call_count += 1
        self.last_messages = messages
        return self.response


# ── 第一层：纯函数测试（无任何外部依赖）─────────────────────────────────────

class TestExtractVideoId:

    def test_standard_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert YouTubeSummaryTool._extract_video_id(url) == "dQw4w9WgXcQ"

    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert YouTubeSummaryTool._extract_video_id(url) == "dQw4w9WgXcQ"

    def test_embed_url(self):
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert YouTubeSummaryTool._extract_video_id(url) == "dQw4w9WgXcQ"

    def test_shorts_url(self):
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        assert YouTubeSummaryTool._extract_video_id(url) == "dQw4w9WgXcQ"

    def test_url_with_playlist(self):
        """含 playlist 参数的链接仍能正确提取 video ID。"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLxxx&index=2"
        assert YouTubeSummaryTool._extract_video_id(url) == "dQw4w9WgXcQ"

    def test_invalid_url(self):
        assert YouTubeSummaryTool._extract_video_id("https://www.google.com") is None

    def test_empty_string(self):
        assert YouTubeSummaryTool._extract_video_id("") is None


class TestSplitChunks:

    def test_short_text_no_split(self):
        text = "line1\nline2\nline3"
        chunks = YouTubeSummaryTool._split_chunks(text, chunk_size=1000)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_splits_at_newline(self):
        """切分点应落在换行处，不在单词中间。"""
        text = "a" * 10 + "\n" + "b" * 10
        chunks = YouTubeSummaryTool._split_chunks(text, chunk_size=15)
        assert len(chunks) == 2
        assert "\n" not in chunks[0]
        assert chunks[1] == "b" * 10

    def test_no_content_lost(self):
        """切分后拼接应还原原文。"""
        text = "\n".join(f"[{i}:00] line {i}" for i in range(50))
        chunks = YouTubeSummaryTool._split_chunks(text, chunk_size=100)
        assert "\n".join(chunks) == text


class TestFormatOutput:

    def test_format_contains_all_sections(self):
        output = YouTubeSummaryTool._format_output(
            video_url="https://www.youtube.com/watch?v=test",
            article="article content",
            notes="notes content",
            summary="summary content",
        )
        assert "article content" in output
        assert "notes content" in output
        assert "summary content" in output
        assert "https://www.youtube.com/watch?v=test" in output


# ── 第二层：Mock LLM 测试（验证流程编排，无模型依赖）────────────────────────

class TestRunWithMockLLM:

    def setup_method(self):
        self.mock_llm = MockLLM("MOCK_RESPONSE")
        self.tool = YouTubeSummaryTool(llm=self.mock_llm)

    def test_invalid_url_returns_failure(self):
        result = self.tool.run("not-a-url")
        assert result.success is False
        assert "无法识别" in result.output

    def test_missing_dependency_returns_failure(self, monkeypatch):
        monkeypatch.setattr("tools.youtube_summary._TRANSCRIPT_AVAILABLE", False)
        result = self.tool.run("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.success is False
        assert "pip install" in result.output

    def test_three_llm_calls_for_short_transcript(self, monkeypatch):
        """短字幕应触发 3 次 LLM 调用（文章 + 笔记 + 总结）。"""
        fake_transcript = "[0:00] Hello world\n[0:05] This is a test"
        monkeypatch.setattr(
            YouTubeSummaryTool,
            "_fetch_transcript",
            staticmethod(lambda video_id: (fake_transcript, "English", None)),
        )
        result = self.tool.run("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.success is True
        assert self.mock_llm.call_count == 3

    def test_output_contains_three_sections(self, monkeypatch):
        """输出应包含三个章节标题。"""
        fake_transcript = "[0:00] Hello world"
        monkeypatch.setattr(
            YouTubeSummaryTool,
            "_fetch_transcript",
            staticmethod(lambda video_id: (fake_transcript, "English", None)),
        )
        result = self.tool.run("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert "一、完整笔记" in result.output
        assert "二、核心知识点" in result.output
        assert "三、总结" in result.output

    def test_fetch_error_returns_failure(self, monkeypatch):
        """字幕抓取失败时应直接返回错误，不调用 LLM。"""
        monkeypatch.setattr(
            YouTubeSummaryTool,
            "_fetch_transcript",
            staticmethod(lambda video_id: ("", "", "字幕不可用")),
        )
        result = self.tool.run("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.success is False
        assert self.mock_llm.call_count == 0

    def test_no_llm_falls_back_to_truncated_transcript(self, monkeypatch):
        """没有 LLM 时应退化为返回截断字幕，不报错。"""
        tool = YouTubeSummaryTool(llm=None)
        fake_transcript = "[0:00] Hello world"
        monkeypatch.setattr(
            YouTubeSummaryTool,
            "_fetch_transcript",
            staticmethod(lambda video_id: (fake_transcript, "English", None)),
        )
        result = tool.run("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result.success is True


# ── 第三层：字幕抓取测试（需要网络，不需要 LLM）────────────────────────────

@pytest.mark.network
class TestFetchTranscript:
    """
    需要网络访问 YouTube。
    如果 IP 被限制会失败，属正常现象。
    """

    # 这个视频有英文字幕，测试中用过
    # VIDEO_ID = "ajFXykT9Joo"
    url = "https://www.youtube.com/watch?v=xfxd-k9MLCw&t=304s"
    VIDEO_ID = YouTubeSummaryTool._extract_video_id(url)


    def test_fetch_returns_text_and_language(self):
        text, lang, error = YouTubeSummaryTool._fetch_transcript(self.VIDEO_ID)
        assert error is None, f"字幕抓取失败：{error}"
        assert len(text) > 0
        assert lang != ""

    def test_fetch_contains_timestamps(self):
        text, lang, error = YouTubeSummaryTool._fetch_transcript(self.VIDEO_ID)
        assert error is None
        # 验证时间戳格式为 [分:秒]，例如 [0:01] 或 [12:34]
        assert re.search(r'\[\d+:\d{2}\]', text) is not None

    def test_invalid_video_id_returns_error(self):
        _, _, error = YouTubeSummaryTool._fetch_transcript("invalidid123")
        assert error is not None


# ── 第四层：完整集成测试（需要网络 + 真实 LLM）──────────────────────────────

@pytest.mark.integration
class TestFullIntegration:
    """
    端到端测试，需要：
    - 网络可访问 YouTube
    - 本地 Ollama 或 ARK API 可用

    运行方式：pytest -m integration -v（耗时较长）
    """

    VIDEO_ID = "ajFXykT9Joo"

    def test_full_run_produces_valid_output(self):
        from llm.ollama import OllamaLLM
        import config
        llm = OllamaLLM(model=config.OLLAMA_MODEL, base_url=config.OLLAMA_BASE_URL)
        tool = YouTubeSummaryTool(llm=llm)
        url = f"https://www.youtube.com/watch?v={self.VIDEO_ID}"
        result = tool.run(url)
        assert result.success is True
        assert len(result.output) > 100
