import sys
import config
from llm.ollama import OllamaLLM
from tools.file_ops import ReadFileTool, WriteFileTool
from agent import Agent


def build_agent() -> Agent:
    llm = OllamaLLM(
        model=config.LLM_MODEL,
        base_url=config.LLM_BASE_URL,
    )
    tools = [
        ReadFileTool(),
        WriteFileTool(),
    ]
    return Agent(llm=llm, tools=tools)


def run_cli(agent: Agent):
    """命令行模式，直接在终端对话。"""
    print("Neoclaw 启动 👾  （命令行模式）")
    print(f"模型：{config.LLM_MODEL}  沙盒：{config.SANDBOX_DIR}")
    print("输入 'quit' 退出，'reset' 清空对话历史\n")

    while True:
        try:
            user_input = input("你：").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("再见！")
            break

        if user_input.lower() == "reset":
            agent.reset()
            print("--- 对话历史已清空 ---\n")
            continue

        response = agent.chat(user_input)
        print(f"Neo：{response}\n")


def run_whatsapp(agent: Agent):
    """WhatsApp 模式，启动 HTTP 服务器等待消息。"""
    from gateway.whatsapp import WhatsAppGateway
    print("Neoclaw 启动 👾  （WhatsApp 模式）")
    gateway = WhatsAppGateway(agent=agent)
    gateway.start()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "cli"
    agent = build_agent()

    if mode == "whatsapp":
        run_whatsapp(agent)
    else:
        run_cli(agent)