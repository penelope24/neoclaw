from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# ── 模型提供方选择 ────────────────────────────────────────────────────────────
# 可选值：
#   "ollama"    — 本地 Ollama（默认）
#   "deepseek"  — ARK 平台 DeepSeek V3
#   "doubao"    — ARK 平台 Doubao-seed-1.8
#   "glm"       — ARK 平台 GLM 4.7
LLM_PROVIDER = "deepseek"

# ── Ollama 配置 ───────────────────────────────────────────────────────────────
OLLAMA_MODEL    = "qwen3.5:9b"
OLLAMA_BASE_URL = "http://localhost:11434"

# ── ARK 平台配置（DeepSeek / Doubao / GLM 共用） ─────────────────────────────
ARK_API_KEY  = os.getenv("ARK_API_KEY", "")
ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
ARK_MODELS = {
    "deepseek": "deepseek-v3-2-251201",
    "doubao":   "doubao-seed-1-8-251228",
    "glm":      "glm-4-7-251222",
}

# ── 通用模型参数 ──────────────────────────────────────────────────────────────
LLM_MAX_TOKENS  = 2048
LLM_TEMPERATURE = 0.7

# ── 模型 context window ───────────────────────────────────────────────────────
LLM_CONTEXT_WINDOW = 32000       # tokens

# ── Agent 配置 ────────────────────────────────────────────────────────────────
AGENT_THINK          = False     # 默认关闭 thinking mode
AGENT_MAX_TOOL_ROUNDS = 5        # 单次消息最多执行几轮 tool call

# ── 文件沙盒 ──────────────────────────────────────────────────────────────────
SANDBOX_DIR = Path.home() / "neoclaw-sandbox"

# ── 只读：当前生效的模型名（供启动信息展示用）────────────────────────────────
def current_model_name() -> str:
    if LLM_PROVIDER == "ollama":
        return OLLAMA_MODEL
    return ARK_MODELS.get(LLM_PROVIDER, LLM_PROVIDER)
