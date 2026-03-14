from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IncomingMessage:
    sender: str       # 发送者 ID（如 WhatsApp 的手机号）
    content: str      # 消息内容
    platform: str     # 来源平台，如 "whatsapp"、"telegram"


class BaseGateway(ABC):
    """所有消息平台适配器的抽象基类。"""

    @abstractmethod
    def send(self, recipient: str, message: str) -> None:
        """发送消息给指定用户。"""
        ...

    @abstractmethod
    def start(self) -> None:
        """启动网关，开始监听消息。"""
        ...