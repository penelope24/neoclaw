from pathlib import Path

# ── 模型配置 ────────────────────────────────────────────────────────────────
LLM_PROVIDER = "ollama"          # 当前使用的模型提供方
LLM_MODEL = "qwen3.5:9b"        # 模型名
LLM_BASE_URL = "http://localhost:11434"  # Ollama 服务地址
LLM_MAX_TOKENS = 2048
LLM_TEMPERATURE = 0.7

# ── Agent 配置 ───────────────────────────────────────────────────────────────
AGENT_THINK = False              # 默认关闭 thinking mode
AGENT_MAX_TOOL_ROUNDS = 5        # 单次消息最多执行几轮 tool call

# ── 文件沙盒 ─────────────────────────────────────────────────────────────────
# agent 只能读写这个目录内的文件
SANDBOX_DIR = Path.home() / "neoclaw-sandbox"