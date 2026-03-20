# Neoclaw × Journey 集成方案

## 设计思想

两个项目各司其职，通过 HTTP 接口通信，保持完全解耦：

- **Journey**：专注金融数据查询与分析，对外暴露 HTTP 接口
- **Neoclaw**：专注 Agent 对话与工具调度，通过 Tool 调用 Journey 接口

这与 neoclaw 现有的 whatsapp-bridge 架构思路一致——不同职责的模块通过 HTTP 通信，各自独立维护。

---

## 整体交互流程

```
用户："帮我分析茅台股票"
        │
        ▼
  Neoclaw Agent
  （识别意图，决定调用工具）
        │
        ▼
  StockAnalysisTool
  （构造请求，发送 HTTP）
        │
        ▼  POST /analyze  {"ticker": "600519"}
  Journey FastAPI 服务
  （查询 Tushare，运行分析）
        │
        ▼
  返回 JSON {"result": "...Markdown 格式简报..."}
        │
        ▼
  Neoclaw Agent
  （将结果注入对话历史，LLM 生成最终回复）
        │
        ▼
  用户收到分析结果
```

---

## 各端职责

### Journey 侧（服务提供方）

新增一个轻量的 FastAPI 入口文件（如 `server.py`），复用现有分析逻辑：

- `POST /analyze/stock`：接收股票代码，返回单股财务简报
- `POST /analyze/industry`：接收行业名，返回行业内股票排名
- `GET /health`：供 neoclaw 检查服务是否就绪

Journey 的核心分析代码无需改动，FastAPI 只是在外面加一层薄薄的 HTTP 入口。

### Neoclaw 侧（服务调用方）

新增 `tools/stock_analysis.py`，继承 `BaseTool`：

- `name`：`stock_analysis`
- `run(query)`：解析用户意图（股票代码 or 行业名），发送 HTTP 请求，返回 `ToolResult`
- 在 `main.py` 的 `build_agent()` 中注册

---

## 部署方式

两个服务分别启动：

```bash
# 终端 1：启动 Journey 分析服务
cd journey && python server.py
# 默认监听 http://localhost:5000

# 终端 2：启动 Neoclaw Agent
cd neoclaw && python main.py
```

Neoclaw 的 `StockAnalysisTool` 默认请求 `http://localhost:5000`，
可在 `config.py` 中配置地址，方便将来部署到不同机器。

---

## 与现有架构的对比

| | Whatsapp-bridge | Journey 集成 |
|---|---|---|
| 通信方式 | HTTP | HTTP |
| 语言 | Node.js ↔ Python | Python ↔ Python |
| 职责划分 | 消息收发 ↔ Agent 逻辑 | 数据分析 ↔ Agent 逻辑 |
| 启动方式 | 两个独立进程 | 两个独立进程 |

---

## 待实现

- [ ] Journey：新增 `server.py`（FastAPI 入口）
- [ ] Journey：实现 `/analyze/stock` 接口
- [ ] Journey：实现 `/analyze/industry` 接口
- [ ] Neoclaw：新增 `tools/stock_analysis.py`
- [ ] Neoclaw：在 `config.py` 中添加 `JOURNEY_BASE_URL`
- [ ] Neoclaw：在 `main.py` 中注册 `StockAnalysisTool`
