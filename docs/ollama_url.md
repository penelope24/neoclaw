# Ollama 本地 URL

Ollama 启动后会在本机创建一个 HTTP 服务器，监听 `11434` 端口。
所有与模型的交互都通过这个接口进行，无论模型跑在本地还是远程。

```
http://localhost:11434
         │        │
         │        └─ 端口号，Ollama 默认值，可通过 OLLAMA_HOST 修改
         └─ localhost = 127.0.0.1 = 本机
```

Ollama 用 HTTP API 作为唯一的对话方式，不区分本地和远程模式。切换运行环境时，只需改一行配置，代码其他部分完全不用动。

## 在 neoclaw 中

`OllamaLLM` 初始化时接收 `base_url` 参数，默认为 `http://localhost:11434`。
如果未来需要连接远程机器，只需在 `config.py` 里修改这个地址即可。