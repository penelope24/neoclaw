from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str   # "user" | "assistant" | "system"
    content: str


@dataclass
class ChatOptions:
    think: bool = False
    max_tokens: int = 2048
    temperature: float = 0.7
    extra: dict = field(default_factory=dict)


class BaseLLM(ABC):
    """所有 LLM 适配器的抽象基类。"""

    @abstractmethod
    def chat(self, messages: list[Message], options: ChatOptions | None = None) -> str:
        """
        发送消息列表，返回模型的文字回复。
        子类必须实现此方法。
        """
        ...

    def simple_chat(
        self,
        user_message: str,
        system_prompt: str | None = None,
        options: "ChatOptions | None" = None,
    ) -> str:
        """便捷方法：单轮对话，不需要手动构建 Message 列表。"""
        messages = []
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        messages.append(Message(role="user", content=user_message))
        return self.chat(messages, options)
