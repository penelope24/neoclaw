from .base import BaseLLM, Message, ChatOptions


class AnthropicLLM(BaseLLM):
    """Anthropic Claude 适配器（占位，待实现）。"""

    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key

    def chat(self, messages: list[Message], options: ChatOptions | None = None) -> str:
        raise NotImplementedError("AnthropicLLM 尚未实现，敬请期待")
