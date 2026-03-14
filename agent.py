import json
import os
import re
import config
from llm.base import BaseLLM, Message, ChatOptions
from tools.base import BaseTool

# 单次用户消息处理中，tool call 最多执行几轮，防止死循环。
# 注意：这不是对话历史的限制——self.history 会持续累积所有对话，
# 每次调用 Ollama 都会携带完整历史。历史过长会导致 context window 溢出
# 或响应变慢，这是后续需要处理的问题（保留最近 N 条或摘要压缩）。
MAX_TOOL_ROUNDS = config.AGENT_MAX_TOOL_ROUNDS

DEBUG = os.environ.get("DEBUG") == "1"

# ANSI 颜色
_GRAY   = "\033[90m"
_CYAN   = "\033[36m"
_YELLOW = "\033[33m"
_GREEN  = "\033[32m"
_RED    = "\033[31m"
_RESET  = "\033[0m"
_BOLD   = "\033[1m"


def _debug(label: str, content: str = "", color: str = _GRAY):
    if DEBUG:
        prefix = f"{color}{_BOLD}[{label}]{_RESET}"
        body = f"{color}{content}{_RESET}" if content else ""
        print(f"{prefix} {body}" if body else prefix)


def build_system_prompt(tools: list[BaseTool]) -> str:
    """根据可用的 tool 列表，生成 system prompt。"""
    if not tools:
        return "你是一个友好的助手。"

    tool_descriptions = "\n".join(
        f"- {tool.name}：{tool.description}" for tool in tools
    )

    return f"""你是一个友好的助手，可以使用以下工具：

{tool_descriptions}

如果需要调用工具，请只输出以下 JSON 格式，不要包含其他内容：
{{"tool": "工具名", "args": {{"参数名": "参数值"}}}}

如果不需要调用工具，直接用自然语言回复。"""


def parse_tool_call(text: str) -> dict | None:
    """
    尝试从模型输出中解析 tool call。
    返回 {"tool": ..., "args": {...}} 或 None。
    """
    # 先尝试整体解析
    try:
        data = json.loads(text.strip())
        if "tool" in data and "args" in data:
            return data
    except json.JSONDecodeError:
        pass

    # 再尝试从文字中提取 JSON 块
    match = re.search(r'\{.*"tool".*"args".*\}', text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            if "tool" in data and "args" in data:
                return data
        except json.JSONDecodeError:
            pass

    return None


class Agent:
    def __init__(self, llm: BaseLLM, tools: list[BaseTool] | None = None):
        self.llm = llm
        self.tools = {tool.name: tool for tool in (tools or [])}
        self.system_prompt = build_system_prompt(list(self.tools.values()))
        self.history: list[Message] = []

    def _find_tool(self, name: str) -> BaseTool | None:
        return self.tools.get(name)

    def chat(self, user_message: str) -> str:
        """
        处理一条用户消息，返回最终回复。
        内部自动处理 tool call loop。
        """
        _debug("用户消息", user_message, _CYAN)

        self.history.append(Message(role="user", content=user_message))

        for round_num in range(MAX_TOOL_ROUNDS):
            _debug(f"调用模型", f"第 {round_num + 1} 轮，历史长度 {len(self.history)} 条", _YELLOW)

            messages = [
                Message(role="system", content=self.system_prompt)
            ] + self.history

            if DEBUG:
                print(f"{_YELLOW}{_BOLD}[发送给模型]{_RESET}")
                for m in messages:
                    print(f"  {_GRAY}{m.role.upper()}{_RESET}: {m.content[:300]}{"..." if len(m.content) > 300 else ""}")
                print()

            options = ChatOptions(think=config.AGENT_THINK)
            response = self.llm.chat(messages, options)

            _debug("模型输出", response[:200] + ("..." if len(response) > 200 else ""), _GRAY)

            tool_call = parse_tool_call(response)

            if tool_call is None:
                _debug("判断", "普通回复，无 tool call", _GREEN)
                self.history.append(Message(role="assistant", content=response))
                return response

            tool_name = tool_call["tool"]
            tool_args = tool_call.get("args", {})
            _debug("判断", f"检测到 tool call → {tool_name}，参数：{tool_args}", _YELLOW)

            tool = self._find_tool(tool_name)

            if tool is None:
                _debug("错误", f"工具 '{tool_name}' 不存在", _RED)
                self.history.append(Message(role="assistant", content=response))
                self.history.append(Message(role="user", content=f"[系统] 工具 '{tool_name}' 不存在"))
                continue

            result = tool.run(**tool_args)
            status = "成功" if result.success else "失败"
            _debug(f"tool 结果", f"{tool_name} → {status}：{result.output[:100]}", _GREEN if result.success else _RED)

            self.history.append(Message(role="assistant", content=response))
            self.history.append(Message(
                role="user",
                content=f"[工具结果] {tool_name}：{status}\n{result.output}"
            ))

        _debug("超出轮次", f"已达 {MAX_TOOL_ROUNDS} 轮上限", _RED)
        return "抱歉，处理这个请求时遇到了问题，请重试。"

    def reset(self):
        """清空对话历史。"""
        self.history = []