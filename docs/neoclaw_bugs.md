# Neoclaw 问题报告

> 基于 `youtube_summary` tool 执行记录的分析，发现以下两类问题。

---

## Bug 1：超长 tool call 无法被正确解析

### 现象

模型输出了合法的 `write_file` tool call JSON，但 `parse_tool_call()` 判断为"普通回复，无 tool call"，导致 JSON 被直接打印给用户，文件从未被写入。

### 根本原因

`parse_tool_call()` 使用正则 `re.search(r'\{.*"tool".*"args".*\}', text, re.DOTALL)` 解析。当 `args` 中包含超长内容（如整篇文章）时，正则贪婪匹配不稳定，导致解析失败。

### 修复方案

用 `find` + `rfind` 提取最外层 JSON 块，替代正则：

```python
def parse_tool_call(text: str) -> dict | None:
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        return None
    try:
        data = json.loads(text[start:end+1])
        if "tool" in data and "args" in data:
            return data
    except json.JSONDecodeError:
        pass
    return None
```

---

## Bug 2：长视频字幕内容被截断，总结不完整

### 现象

`youtube_summary` tool 对长视频的字幕做了 12000 字符硬截断，导致视频后半段内容完全丢失，生成的笔记不完整。

### 根本原因

`youtube_summary.py` 中有以下处理：

```python
if len(full_text) > 12000:
    full_text = full_text[:12000] + "\n\n[字幕过长，以上为前半部分]"
```

此外，即使拿到完整字幕，将全文塞入 `write_file` 的 JSON args 也会同时触发 Bug 1，形成双重失败。

### 修复方案

将"获取字幕 → 总结 → 写文件"拆分为分块总结流程（Map-Reduce 模式）：

```
字幕原文（完整）
    ↓
分块（每块 ~3000 字）→ LLM 对每块单独总结
    ↓
将所有块的小结合并 → LLM 再做一次整体总结
    ↓
write_file 只写入最终总结（内容短，不触发解析问题）
```

这样每次传给模型的内容长度可控，`write_file` 收到的也只是几百字的摘要。

---

## 问题关联

两个 bug 会相互叠加：长视频触发截断（Bug 2），同时模型试图把大量内容塞入 tool call，又触发解析失败（Bug 1）。**优先修复 Bug 1**，再重构 `youtube_summary.py` 的分块逻辑解决 Bug 2。
