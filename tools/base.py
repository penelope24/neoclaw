from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolResult:
    success: bool
    output: str       # 成功时的结果内容，失败时的错误信息


class BaseTool(ABC):
    """所有 tool 的抽象基类。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool 的唯一标识名，模型调用时使用。"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool 的功能描述，用于写入 system prompt 告知模型。"""
        ...

    @abstractmethod
    def run(self, **kwargs) -> ToolResult:
        """执行 tool，返回结果。子类必须实现此方法。"""
        ...