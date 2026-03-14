import requests
from .base import BaseLLM, Message, ChatOptions


class OllamaLLM(BaseLLM):
    """Ollama 本地模型适配器。"""

    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(self, messages: list[Message], options: ChatOptions | None = None) -> str:
        options = options or ChatOptions()

        payload = {
            "model": self.model,
            "think": options.think,
            "stream": False,
            "options": {
                "temperature": options.temperature,
                "num_predict": options.max_tokens,
            },
            "messages": [
                {"role": m.role, "content": m.content}
                for m in messages
            ],
            **options.extra,
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
        except requests.Timeout:
            raise RuntimeError("Ollama 请求超时（>120s），请检查模型是否正常运行")
        except requests.RequestException as e:
            raise RuntimeError(f"Ollama 请求失败：{e}")

        data = response.json()
        return data["message"]["content"]
