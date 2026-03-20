from typing import Any
from openai import OpenAI
from .base import BaseLLM, Message, ChatOptions


class OpenAICompatibleLLM(BaseLLM):
    """
    通用 OpenAI 兼容适配器，支持任何兼容 OpenAI Chat Completions 协议的服务。
    当前支持：ARK 平台（DeepSeek V3、Doubao、GLM）
    """

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def chat(self, messages: list[Message], options: ChatOptions | None = None) -> str:
        options = options or ChatOptions()

        params: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "max_tokens": options.max_tokens,
            "temperature": options.temperature,
        }

        # thinking 模式：GLM 支持，其他模型忽略
        if options.think:
            params["thinking"] = {"type": "enabled"}

        try:
            response = self.client.chat.completions.create(**params)
        except Exception as e:
            raise RuntimeError(f"API 请求失败：{e}")

        return response.choices[0].message.content
