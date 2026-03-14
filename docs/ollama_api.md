# Ollama API 格式笔记

## 流式响应结构

开启 `stream: true` 时，Ollama 每生成一个 token 就返回一行 JSON。
每一行的基本结构：

```json
{
  "model": "qwen3.5:9b",
  "message": {
    "role": "assistant",
    "content": "你好",
    "thinking": ""
  },
  "done": false
}
```

`done` 字段由 Ollama 统一添加，与使用哪个模型无关。所有 Ollama 支持的模型都遵循这个格式。

## thinking mode 的字段规则

开启 `think: true` 时，`thinking` 和 `content` 是互斥的——同一条消息里只有一个字段有内容。

```json
// 思维链阶段：thinking 有内容，content 为空
{"message": {"content": "", "thinking": "好的，用户发来了..."}, "done": false}

// 正式回复阶段：content 有内容，thinking 为空
{"message": {"content": "你好！", "thinking": ""}, "done": false}
```

## 结束信号

最后一条消息 `done: true`，此时 `content` 为空，携带本次调用的统计信息。

```json
{
  "message": {"role": "assistant", "content": ""},
  "done": true,
  "done_reason": "stop",
  "total_duration": 31503986667,
  "prompt_eval_count": 11,
  "eval_count": 239
}
```

`done_reason` 的常见值：`"stop"`（正常结束）、`"length"`（达到 max_tokens 被截断）。