# YouTube 视频总结功能 — 实现计划

## 核心思路

YouTube 提供视频字幕（transcript），我们可以通过第三方库 `youtube-transcript-api` 免费抓取，
无需 YouTube API Key，无需登录。

整体流程：

```
用户发送视频链接
    → Agent 识别意图，调用 youtube_summary tool
    → tool 从 YouTube 抓取字幕文本（含时间戳）
    → 字幕作为 tool 结果注入对话历史
    → LLM 读取字幕，输出结构化总结
    → 回复用户
```

这与现有 tool call 机制完全一致，不需要改动 Agent 核心逻辑。

---

## 文件改动清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | `tools/youtube_summary.py` | Tool 本体（从 `docs/youtube_summary.py` 移入并修复） |
| 修改 | `main.py` | 在 `build_agent()` 中注册新 tool |
| 修改 | `requirements.txt` | 新增 `youtube-transcript-api` 依赖 |

---

## YouTubeSummaryTool 逻辑说明

### 1. URL 解析 — `_extract_video_id(url)`

支持四种 YouTube 链接格式，用正则提取 11 位 video ID：

```
https://www.youtube.com/watch?v=dQw4w9WgXcQ   → 标准链接
https://youtu.be/dQw4w9WgXcQ                   → 短链接
https://www.youtube.com/embed/dQw4w9WgXcQ      → 嵌入链接
https://www.youtube.com/shorts/dQw4w9WgXcQ     → Shorts
```

### 2. 字幕抓取 — `_fetch_transcript(video_id)`

优先级：**手动字幕 > 自动生成字幕**，语言不限（取第一个可用的）。

抓取后保留时间戳，格式化为：
```
[0:00] Welcome to this video
[0:05] Today we're going to talk about...
[1:23] First, let's look at the problem
```

超长字幕截断到约 12000 字符，避免撑爆 LLM context window。

### 3. 注入提示 — `_build_summary_prompt()`

字幕文本被包装成一段提示，作为 tool result 注入对话历史。
LLM 下一轮会读取这段内容，自然地输出总结。

要求 LLM 输出：
- **内容摘要**：2-4 句话概括
- **关键要点**：4-6 条核心观点
- **章节划分**：4-8 个章节，每章节附时间戳和简述

### 4. 错误处理

| 情况 | 返回信息 |
|------|----------|
| 缺少依赖库 | 提示 `pip install youtube-transcript-api` |
| 无法识别视频 ID | 提示链接格式有误 |
| 视频不可用/已删除 | 告知用户 |
| 视频已关闭字幕 | 告知用户 |
| 没有任何字幕 | 告知用户（部分视频无字幕） |

---

## 需要修复的两处问题

相比 `docs/youtube_summary.py` 中的原版，实现时需修复：

**① 字幕丢失时间戳**

原版在拼接字幕时丢弃了时间信息，导致 LLM 无法生成准确的章节时间戳。
修复：在拼接时将 `.start`（秒数）转换为 `分:秒` 格式并保留。

**② 文件位置错误**

原版放在 `docs/`，但代码写的是 `from .base import ...`，实际运行会报 ImportError。
修复：直接建在 `tools/youtube_summary.py`。

---

## 安装依赖

```bash
pip install youtube-transcript-api
```

或在 `requirements.txt` 中添加后统一安装：

```bash
pip install -r requirements.txt
```

---

## 使用方式

安装依赖、完成代码改动后，直接启动项目，对话时发送视频链接即可：

```
你：帮我总结这个视频 https://www.youtube.com/watch?v=dQw4w9WgXcQ
Neo：[自动调用 youtube_summary tool，输出结构化总结]
```

WhatsApp 模式同理，发送链接给绑定的号码即可。

---

## 局限性

- 视频必须有字幕（手动或自动生成），纯音频/无字幕视频无法处理
- 超长视频（字幕 > 12000 字符）只总结前半部分
- 章节时间戳是 LLM 根据字幕内容估算的，不一定与视频实际章节完全吻合
