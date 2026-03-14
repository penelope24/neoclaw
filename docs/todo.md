# Neoclaw TODO

## 已完成 ✅
- `llm/` 模块：Ollama 适配器，`think=false` 默认关闭
- `tools/` 模块：文件读写，sandbox 路径隔离，路径穿越防护
- `agent.py`：tool call loop，对话历史管理，debug 可观测性
- `gateway/` 模块：FastAPI HTTP 服务，WhatsApp bridge（Node.js）
- `main.py`：CLI 模式 + WhatsApp 模式
- `config.py`：全局配置集中管理
- `benchmark.py`：速度对比 + 流式观察 + thinking mode 可视化
- Debug 模式：`DEBUG=1` 环境变量，Node.js 和 Python 两侧均支持

---

## 待完成

### 高优先级

- [ ] **History 长度限制**
  在 `config.py` 加 `AGENT_MAX_HISTORY`，`chat()` 里只取最近 N 条，防止 context window 溢出

- [ ] **Ollama keep-alive**
  定期发空请求防止模型被卸载，避免冷启动导致的 timeout 和丢消息

- [ ] **错误重试机制**
  Ollama 请求失败时自动重试 1-2 次，而不是直接报错

- [ ] **WhatsApp 消息发送失败处理**
  Node.js 侧发送失败时记录日志，必要时重试

### 中优先级

- [ ] **持久化对话历史**
  进程退出时把 `history` 序列化写入 JSON 文件，下次启动时读回来

- [ ] **多用户 history 隔离**
  目前所有用户共享同一个 Agent 实例和 history，需要按 `sender` 分开管理

- [ ] **LLM Logger**
  记录每次调用的耗时、token 数，写入文件，方便长期性能分析

- [ ] **`shell.py` 实现**
  实现 `run_shell` 工具，加入白名单机制控制可执行的命令

### 低优先级 / 未来扩展

- [ ] **分级 thinking 模式**
  简单请求保持 `think=false`，复杂请求（用户明确要求或触发关键词）可选开启

- [ ] **Telegram 支持**
  实现 `gateway/telegram.py`，复用现有 agent 逻辑

- [ ] **Anthropic LLM 适配器**
  实现 `llm/anthropic.py`，支持切换到 Claude

- [ ] **Context 摘要压缩**
  history 过长时自动摘要，而不是简单截断最早的消息

- [ ] **白名单发送者**
  只响应指定手机号的消息，防止陌生人调用 agent

---

## 已知问题

- whatsapp-web.js 偶发丢消息，原因未确认（疑似 Ollama 冷启动 timeout）
- `msg.isGroupMsg` 字段在新版 whatsapp-web.js 失效，目前用 `@c.us` 过滤替代