import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import Agent
from gateway.base import BaseGateway, IncomingMessage
import config


# ── Node.js 那侧发过来的请求格式 ─────────────────────────────────────────────
class WhatsAppIncoming(BaseModel):
    sender: str      # 发送者手机号，如 "85291234567@c.us"
    message: str     # 消息内容


# ── Node.js 那侧暴露的发送接口 ────────────────────────────────────────────────
WHATSAPP_SEND_URL = "http://localhost:3000/send"


class WhatsAppGateway(BaseGateway):

    def __init__(self, agent: Agent, host: str = "0.0.0.0", port: int = 8000):
        self.agent = agent
        self.host = host
        self.port = port
        self.app = FastAPI()
        self._register_routes()

    def _register_routes(self):

        @self.app.get("/health")
        def health():
            """供 Node.js 检查 Python 服务是否就绪。"""
            return {"status": "ok", "model": config.LLM_MODEL}

        @self.app.post("/message")
        def receive_message(incoming: WhatsAppIncoming):
            """接收 Node.js 转发过来的 WhatsApp 消息，返回回复内容。"""
            print(f"[收到] {incoming.sender}: {incoming.message}")

            try:
                msg = IncomingMessage(
                    sender=incoming.sender,
                    content=incoming.message,
                    platform="whatsapp",
                )
                reply = self.agent.chat(msg.content)
                print(f"[回复] {reply}")
                return {"reply": reply}

            except Exception as e:
                print(f"[错误] {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def send(self, recipient: str, message: str) -> None:
        """主动发送消息给某个用户（目前由 Node.js 侧处理，此方法备用）。"""
        try:
            requests.post(WHATSAPP_SEND_URL, json={
                "recipient": recipient,
                "message": message,
            }, timeout=10)
        except Exception as e:
            print(f"[发送失败] {e}")

    def start(self) -> None:
        """启动 FastAPI 服务器。"""
        print(f"WhatsApp Gateway 启动，监听 {self.host}:{self.port}")
        uvicorn.run(self.app, host=self.host, port=self.port)