from .base import BaseTool, ToolResult


class ShellTool(BaseTool):
    """执行 shell 命令（占位，待实现）。"""

    @property
    def name(self) -> str:
        return "run_shell"

    @property
    def description(self) -> str:
        return "执行 shell 命令（尚未实现）"

    def run(self, command: str) -> ToolResult:
        raise NotImplementedError("ShellTool 尚未实现")