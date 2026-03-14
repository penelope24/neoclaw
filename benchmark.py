"""
benchmark.py — 对比 OllamaLLM 封装 vs 直接调用 Ollama API 的速度
             + 流式模式：直观感受 token 生成过程和思维链

用法：
    python benchmark.py           # 速度对比（默认）
    python benchmark.py stream    # 流式输出，观察 token 生成
    python benchmark.py think     # 流式输出，开启思维链
"""

import time
import statistics
import requests
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm import OllamaLLM

# ── 配置 ────────────────────────────────────────────────────────────────────
MODEL = "qwen3.5:9b"
BASE_URL = "http://localhost:11434"
TEST_MESSAGE = "用一句话介绍你自己"
ROUNDS = 3
# ────────────────────────────────────────────────────────────────────────────


def direct_ollama(message: str) -> tuple[str, float]:
    """直接调用 Ollama API，返回 (回复内容, 耗时秒)"""
    start = time.perf_counter()  # 用于测试的高精度时间戳
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "model": MODEL,
            "think": False,
            "stream": False,
            "messages": [{"role": "user", "content": message}],
        },
        timeout=120,  # 最长等待时间，超出则抛Timeout异常
    )
    response.raise_for_status()  # 防御性编程：检查 HTTP 响应的状态码，如果是错误码就抛出异常
    elapsed = time.perf_counter() - start
    return response.json()["message"]["content"], elapsed


def via_ollama_llm(message: str, llm: OllamaLLM) -> tuple[str, float]:
    """通过 OllamaLLM 封装调用，返回 (回复内容, 耗时秒)"""
    start = time.perf_counter()
    content = llm.simple_chat(message)
    elapsed = time.perf_counter() - start
    return content, elapsed


def stream_ollama(message: str, think: bool = False):
    """
    流式调用 Ollama，实时打印每个 token。
    思维链（thinking 字段）灰色显示，正式回复绿色显示。
    """
    GRAY   = "\033[90m"
    YELLOW = "\033[33m"
    GREEN  = "\033[32m"
    RESET  = "\033[0m"
    BOLD   = "\033[1m"

    print(f"\n{'='*55}")
    print(f"模型：{MODEL}  think={'on' if think else 'off'}")
    print(f"问题：{message!r}")
    print(f"{'='*55}\n")

    response = requests.post(
        f"{BASE_URL}/api/chat",
        json={
            "model": MODEL,
            "think": think,
            "stream": True,
            "messages": [{"role": "user", "content": message}],
        },
        timeout=120,
        stream=True,
    )
    response.raise_for_status()

    # thinking token 在独立的 "thinking" 字段，不在 "content" 里
    think_started = False
    in_think = False
    total_tokens = 0
    start = time.perf_counter()

    for raw_line in response.iter_lines():
        if not raw_line:
            continue

        chunk = json.loads(raw_line)
        msg = chunk.get("message", {})
        thinking = msg.get("thinking", "")  # 思维链字段
        content = msg.get("content", "")    # 正式回复字段

        # 打印思维链
        if thinking:
            if not think_started:
                think_started = True
                in_think = True
                print(f"{YELLOW}{BOLD}── 思维链开始 ──{RESET}\n", flush=True)
            print(f"{GRAY}{thinking}{RESET}", end="", flush=True)
            total_tokens += 1

        # 思维链结束，切换到正式回复
        """
        // 思维链阶段：thinking 有内容，content 为空
        {"message": {"content": "", "thinking": "好的，用户发来了..."}}
        
        // 正式回复阶段：content 有内容，thinking 为空
        {"message": {"content": "你好！", "thinking": ""}}
        """
        if in_think and content:
            in_think = False
            print(f"\n\n{YELLOW}{BOLD}── 思维链结束 ──{RESET}\n", flush=True)
            print(f"{GREEN}{BOLD}── 正式回复 ──{RESET}\n", flush=True)

        # 打印正式回复
        if content:
            print(f"{GREEN}{content}{RESET}", end="", flush=True)
            total_tokens += 1

        if chunk.get("done"):
            break

    elapsed = time.perf_counter() - start
    tok_per_sec = total_tokens / elapsed if elapsed > 0 else 0

    print(f"\n\n{'-'*55}")
    print(f"总计：{total_tokens} tokens  耗时：{elapsed:.2f}s  速度：{tok_per_sec:.1f} tok/s")


def run_benchmark():
    llm = OllamaLLM(model=MODEL, base_url=BASE_URL)

    direct_times = []
    wrapper_times = []

    print(f"模型：{MODEL}")
    print(f"测试问题：{TEST_MESSAGE!r}")
    print(f"轮次：{ROUNDS}\n")
    print("=" * 55)

    for i in range(1, ROUNDS + 1):
        print(f"\n第 {i} 轮")

        content, t = direct_ollama(TEST_MESSAGE)
        direct_times.append(t)
        print(f"  直接调用  {t:.3f}s  →  {content[:40].strip()}…")

        content, t = via_ollama_llm(TEST_MESSAGE, llm)
        wrapper_times.append(t)
        print(f"  OllamaLLM {t:.3f}s  →  {content[:40].strip()}…")

    print("\n" + "=" * 55)
    print("汇总")
    print(f"  直接调用   avg={statistics.mean(direct_times):.3f}s  "
          f"min={min(direct_times):.3f}s  max={max(direct_times):.3f}s")
    print(f"  OllamaLLM  avg={statistics.mean(wrapper_times):.3f}s  "
          f"min={min(wrapper_times):.3f}s  max={max(wrapper_times):.3f}s")

    overhead = statistics.mean(wrapper_times) - statistics.mean(direct_times)
    print(f"\n  封装额外开销：{overhead*1000:+.1f}ms（平均）")
    if abs(overhead) < 0.05:
        print("  ✅ 封装开销可忽略")
    else:
        print("  ⚠️  存在明显差异，建议检查封装逻辑")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "benchmark"

    if mode == "stream":
        stream_ollama(TEST_MESSAGE, think=False)
    elif mode == "think":
        stream_ollama(TEST_MESSAGE, think=True)
    else:
        run_benchmark()