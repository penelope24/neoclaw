from pathlib import Path
from .base import BaseTool, ToolResult
import config

# 只允许在这个目录下读写文件，防止误操作其他路径
SANDBOX_DIR = config.SANDBOX_DIR


def _safe_path(path_str: str) -> Path | None:
    """
    将输入路径解析为绝对路径，并验证是否在 SANDBOX_DIR 内。
    使用 resolve() 防止路径穿越攻击（如 ../../etc/passwd）。
    如果路径越界返回 None。
    通过绝对路径比较可以防止路径穿越攻击（Path Traversal）
    """
    target = Path(path_str).expanduser().resolve()
    sandbox = SANDBOX_DIR.resolve()
    if sandbox in target.parents or target == sandbox:
        return target
    return None


class ReadFileTool(BaseTool):

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            f"读取文件内容。只能读取 {SANDBOX_DIR} 目录下的文件。"
            f"参数：path（文件路径，相对于 {SANDBOX_DIR}）"
        )

    def run(self, path: str) -> ToolResult:
        target = _safe_path(str(SANDBOX_DIR / path))
        if target is None:
            return ToolResult(success=False, output=f"路径不合法：只允许访问 {SANDBOX_DIR} 内的文件")

        if not target.exists():
            return ToolResult(success=False, output=f"文件不存在：{target}")

        if not target.is_file():
            return ToolResult(success=False, output=f"路径不是文件：{target}")

        try:
            content = target.read_text(encoding="utf-8")
            return ToolResult(success=True, output=content)
        except Exception as e:
            return ToolResult(success=False, output=f"读取失败：{e}")


class WriteFileTool(BaseTool):

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return (
            f"写入内容到文件。只能写入 {SANDBOX_DIR} 目录下的文件，目录不存在时自动创建。"
            f"参数：path（文件路径，相对于 {SANDBOX_DIR}），content（写入内容）"
        )

    def run(self, path: str, content: str) -> ToolResult:
        target = _safe_path(str(SANDBOX_DIR / path))
        if target is None:
            return ToolResult(success=False, output=f"路径不合法：只允许访问 {SANDBOX_DIR} 内的文件")

        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(success=True, output=f"已写入：{target}")
        except Exception as e:
            return ToolResult(success=False, output=f"写入失败：{e}")