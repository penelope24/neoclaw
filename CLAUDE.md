# Neoclaw — CLAUDE.md

## 项目简介

Neoclaw 是一个本地 LLM 驱动的 AI 助手框架，核心目标是通过 WhatsApp 与用户对话，并具备工具调用（tool use）能力。

运行模式：
- `python main.py` — 命令行对话模式
- `python main.py whatsapp` — WhatsApp 模式（需同时运行 Node.js bridge）

WhatsApp 模式下的双进程架构：
```
WhatsApp <-> Node.js (whatsapp-bridge/) <-> Python FastAPI (gateway/) <-> Agent
```

## 代码结构

```
agent.py          # 核心 Agent：tool call loop、对话历史管理
config.py         # 全局配置（模型、sandbox 路径等）
main.py           # 入口：CLI 模式 / WhatsApp 模式

llm/
  base.py         # BaseLLM 抽象类，Message、ChatOptions dataclass
  ollama.py       # Ollama 本地模型适配器（当前主力）
  anthropic.py    # Claude 适配器（待实现）

tools/
  base.py         # BaseTool 抽象类，ToolResult dataclass
  file_ops.py     # 文件读写工具，沙盒路径隔离
  shell.py        # Shell 工具（待实现）

gateway/
  base.py         # BaseGateway 抽象类
  whatsapp.py     # FastAPI 服务，接收 Node.js 转发的消息

whatsapp-bridge/
  index.js        # Node.js：连接 WhatsApp Web，转发消息给 Python
  package.json
```

## 关键设计

**Tool call 机制**：Agent 通过 system prompt 告知模型可用工具，模型输出 JSON 格式的 tool call，Agent 解析后执行并将结果注入 history，最多循环 `AGENT_MAX_TOOL_ROUNDS` 次。这是自制的简单 tool use 协议，不依赖 Ollama 的 native function calling。

**沙盒安全**：所有文件操作通过 `_safe_path()` 验证，使用 `Path.resolve()` 防止路径穿越攻击，只允许访问 `SANDBOX_DIR`（默认 `~/neoclaw-sandbox`）。

**扩展方式**：
- 新 LLM：继承 `BaseLLM`，实现 `chat()`
- 新工具：继承 `BaseTool`，实现 `name`、`description`、`run()`，在 `main.py` 的 `build_agent()` 中注册
- 新平台：继承 `BaseGateway`，实现 `send()` 和 `start()`

## 开发约定

- 配置统一在 `config.py` 管理，不要在各模块里硬编码常量
- 调试信息使用 `_debug()` + `DEBUG=1` 环境变量，不要留裸 print
- Tool 的 `description` 要写清楚参数名和用途，这是模型理解工具的唯一依据
- 不要在 `gateway/` 层直接操作 history，保持 Agent 的封装

## 待解决的重要问题

按优先级排列，详见 `docs/todo.md`：

1. **多用户 history 隔离**（高）——目前所有 WhatsApp 用户共用一个 Agent，会串对话
2. **History 长度限制**（高）——长对话会导致 context window 溢出
3. **Ollama keep-alive**（高）——冷启动会超时丢消息
4. **AnthropicLLM 实现**（中）
5. **持久化对话历史**（中）

## 启动方式

```bash
# 安装依赖
pip install -r requirements.txt

# CLI 模式
python main.py

# WhatsApp 模式（两个终端分别运行）
cd whatsapp-bridge && node index.js
python main.py whatsapp

# 开启 debug 输出
DEBUG=1 python main.py
DEBUG=1 node index.js
```
