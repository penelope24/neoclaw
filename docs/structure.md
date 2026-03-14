# Neoclaw 项目结构

```
neoclaw/
├── main.py              # 入口，启动 bot
├── agent.py             # 核心编排逻辑（平台无关）
├── config.py            # 全局配置
├── benchmark.py         # 开发工具：测速 & 观察 token 生成
├── requirements.txt     # 依赖管理
│
├── llm/                 # 模型适配器
│   ├── __init__.py
│   ├── base.py          # 抽象基类：Message, ChatOptions, BaseLLM
│   ├── ollama.py        # Ollama 实现 ✅
│   └── anthropic.py     # 占位，待实现
│
├── gateway/             # 消息平台适配器
│   ├── __init__.py
│   ├── base.py          # 抽象基类：定义 send/receive 接口
│   ├── whatsapp.py      # WhatsApp 实现
│   └── telegram.py      # 占位，待实现
│
└── tools/               # Tool 实现
    ├── __init__.py
    ├── base.py          # 抽象基类
    ├── file_ops.py      # 文件读写
    └── shell.py         # 占位，待实现
```

## 当前进度

| 模块 | 状态 |
|------|------|
| `llm/` | ✅ 完成 |
| `tools/` | 🔲 下一步 |
| `gateway/` | 🔲 待开发 |
| `agent.py` | 🔲 待开发 |
| `main.py` | 🔲 待开发 |