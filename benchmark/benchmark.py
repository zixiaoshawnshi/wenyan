#!/usr/bin/env python3
"""
文言 vs 白話 Benchmark
Measures token usage and accuracy.

Usage:
  python3 benchmark.py           # live API calls (needs ANTHROPIC_API_KEY)
  python3 benchmark.py --demo    # pre-written fixtures, no API key needed
"""

import anthropic
import json
import sys
import time

MODEL = "claude-haiku-4-5-20251001"

WENYAN_SYSTEM = """\
汝為文言模式助手。以文言文答問，省字為要。
術語表：蟲=bug, 碼=code, 函=method/function, 類=class, 象=object, 界=interface,
型=type, 列=array/list, 串=string, 數=number, 判=boolean, 空=null, 枚=enum, 典=map,
倉=database, 表=table, 詢=query, 索=index, 範=schema, 遷=migration,
緩=cache, 隊=queue, 棧=stack, 機=server, 端=port, 套=socket, 器=container, 鏡=image,
接=API, 節=endpoint, 請=request, 應=response, 符=token, 席=session,
間件=middleware, 架=framework, 鉤=webhook, 假=mock,
驗=auth, 權=authorization, 誤=error, 異=exception, 逾時=timeout,
記=log, 事=event, 回=callback, 許=promise/async, 緒=thread, 程=process,
憶=memory, 效=performance, 返=return, 環=loop, 引=import, 出=export,
檔=file, 目=directory, 徑=path, 鍵=key, 值=value, 境=environment, 配=config,
依=dependency, 庫=repository, 支=branch, 定=commit, 合=merge, 布=deploy,
建=build, 試=test, 規=lint, 整=refactor, 尋蟲=debug, 釋=release, 版=version,
補=patch, 退=rollback, 持整=CI/CD, 管=pipeline, 能=feature, 戶=user。
人稱：吾=I, 汝=you（親）, 君=you（敬）, 彼=it。
助詞：也/矣/乎/哉/之/者/則（少用，取其韻）。
有序步驟用：先/次/再/末。四字成語代長篇。
省冠詞、寒暄（certainly/of course）、猶疑（I think/perhaps）、主詞（可推者）。
直言真理。代碼塊保持原樣，勿文言化。\
"""

NORMAL_SYSTEM = "You are a helpful and concise coding assistant."

JUDGE_SYSTEM = """\
You are a technical accuracy judge. Given the same coding question answered
in English and in Classical Chinese (文言文), rate whether the 文言 answer
preserves all key technical information from the English answer.

Score 1-5:
5 = All key technical points present and accurate
4 = Most key points present, minor omissions only
3 = Core point present, some details missing
2 = Significant technical gaps
1 = Key information missing or wrong

Respond with JSON only: {"score": N, "notes": "brief note"}\
"""

PROMPTS = [
    {"id": "race_condition",   "q": "What is a race condition? One-sentence definition and brief example."},
    {"id": "auth_bug",         "q": "Bug: auth token expires too early. Expiry check uses `<` instead of `<=`. How do I fix it?"},
    {"id": "reduce",           "q": "What does `arr.reduce((acc, x) => acc + x, 0)` do?"},
    {"id": "slow_query",       "q": "My SQL query is slow. Top 3 things to check first?"},
    {"id": "recursion",        "q": "Explain recursion in two sentences."},
    {"id": "process_vs_thread","q": "Difference between a process and a thread?"},
    {"id": "null_pointer",     "q": "Getting a NullPointerException in Java. Most common causes?"},
    {"id": "rest_api",         "q": "What is a REST API? Keep it brief."},
    {"id": "git_rebase",       "q": "Difference between git merge and git rebase?"},
    {"id": "big_o",            "q": "What does O(n²) time complexity mean in plain terms?"},
]

# Pre-written fixtures for --demo mode.
# English responses are typical model output; 文言 responses follow the skill rules.
# Token counts estimated: EN ~4 chars/token; ZH ~1.5 chars/token.
FIXTURES = [
    {
        "id": "race_condition",
        "en": "A race condition occurs when two or more threads access shared data concurrently and the outcome depends on the timing of their execution. Example: two threads both read a counter value of 5, both increment it, and both write back 6 — but the correct result should be 7.",
        "wn": "競爭條件者，二線程並讀共享資料，結果視執行時序而定也。例：二線程皆讀計數器值5，皆加一，皆寫回6——然正確值應為7。",
    },
    {
        "id": "auth_bug",
        "en": "The bug is a strict less-than comparison. Change `if (now < expiry)` to `if (now <= expiry)`. This ensures tokens remain valid at the exact moment of expiry rather than expiring one unit too early.",
        "wn": "蟲在比較符。改 `now < expiry` 為 `now <= expiry`。令驗令在逾期之刻仍有效，非提前失效。",
    },
    {
        "id": "reduce",
        "en": "It sums all elements in the array. `reduce` iterates over each element, adding it to an accumulator that starts at 0, and returns the total sum.",
        "wn": "此函求數組之和。`reduce` 遍歷各元素，累加至初值為0之積累器，返其總和。",
    },
    {
        "id": "slow_query",
        "en": "Check: 1) Missing indexes — run EXPLAIN to see if a full table scan is happening. 2) N+1 query problems — you may be issuing many small queries in a loop. 3) Returning too many columns — use SELECT only what you need instead of SELECT *.",
        "wn": "察三事：一、索引缺失——以EXPLAIN視是否全表掃；二、N+1蟲——或在環中頻發小請；三、列過多——以SELECT指定列，勿用SELECT *。",
    },
    {
        "id": "recursion",
        "en": "Recursion is when a function calls itself to solve a smaller version of the same problem. It requires a base case to stop the calls, otherwise it recurses infinitely.",
        "wn": "遞歸者，函自調以解同題之小例也。須有基例止之，否則無窮自調。",
    },
    {
        "id": "process_vs_thread",
        "en": "A process is an independent program instance with its own memory space; threads are lighter units of execution that share the same memory within a process. Processes are isolated from each other; threads within the same process can communicate directly but must synchronize to avoid race conditions.",
        "wn": "進程者，獨立程序實例，有其私有憶空間；線程者，輕量執行單位，共進程之憶。進程互隔；同進程之線程可直接通信，然需同步以防競爭。",
    },
    {
        "id": "null_pointer",
        "en": "Most common causes: 1) Calling a method on an object that was never initialized. 2) A method returning null that you didn't check. 3) An array element that is null. Always check for null before dereferencing, or use Optional.",
        "wn": "常見因：一、調用未初始化對象之方法；二、方法返空而未檢驗；三、數組元素為空。解引前驗空，或用Optional。",
    },
    {
        "id": "rest_api",
        "en": "A REST API is a web service that uses HTTP methods (GET, POST, PUT, DELETE) to perform operations on resources identified by URLs. It is stateless — each request contains all the information needed to process it.",
        "wn": "REST接者，以HTTP動詞（GET/POST/PUT/DELETE）操作URL所指資源之網絡服務也。無狀態——每請自含所需信息。",
    },
    {
        "id": "git_rebase",
        "en": "Merge creates a new merge commit that joins two branch histories, preserving the full history. Rebase replays your commits on top of another branch, creating a linear history but rewriting commit hashes. Use merge for shared branches; use rebase to clean up local work before merging.",
        "wn": "合者，創新定以連兩支歷史，保全記錄；rebase者，將汝之定重演於他支之上，成線性歷史然改定之散列。共享支用合；本地整理用rebase。",
    },
    {
        "id": "big_o",
        "en": "O(n²) means the time taken grows proportionally to the square of the input size. If n=10 takes 1 second, n=100 takes 100 seconds, and n=1000 takes 100,000 seconds. Common in nested loops iterating over the same data.",
        "wn": "O(n²)者，耗時與輸入量之平方成比也。n=10需1秒，則n=100需100秒，n=1000需10萬秒。常見於嵌套環遍歷同一資料。",
    },
]


def estimate_tokens(text: str) -> int:
    """
    Rough token estimate: English ~4 chars/token, Chinese ~1.5 chars/token.
    Mixed text handled character by character.
    """
    en_chars = sum(1 for c in text if ord(c) < 0x4E00 or ord(c) > 0x9FFF)
    zh_chars = sum(1 for c in text if 0x4E00 <= ord(c) <= 0x9FFF)
    return round(en_chars / 4 + zh_chars / 1.5)


def call_api(client, system, question):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    return resp.content[0].text, resp.usage.output_tokens


def judge_api(client, question, en_ans, wn_ans):
    prompt = f"Question: {question}\n\nEnglish answer:\n{en_ans}\n\n文言 answer:\n{wn_ans}"
    resp = client.messages.create(
        model=MODEL,
        max_tokens=128,
        system=JUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        s, e = raw.find("{"), raw.rfind("}") + 1
        return json.loads(raw[s:e]) if s >= 0 else {"score": 0, "notes": "parse error"}


def bar(ratio, width=20):
    filled = round(max(0.0, ratio) * width)
    return "█" * filled + "░" * (width - filled)


def print_results(results, mode_label):
    total_en = sum(r["en_tokens"] for r in results)
    total_wn = sum(r["wn_tokens"] for r in results)
    avg_reduction = (total_en - total_wn) / total_en if total_en else 0
    avg_accuracy = sum(r["accuracy"] for r in results) / len(results)

    print(f"\n{'═'*74}")
    print(f"  {'題目':<24} {'白話tok':>7} {'文言tok':>7} {'省':>6}  {'準確':>5}  縮減")
    print(f"{'─'*74}")
    for r in results:
        red_pct = r["reduction"] * 100
        sign = "▼" if r["reduction"] > 0 else "▲"
        b = bar(r["reduction"])
        print(f"  {r['id']:<24} {r['en_tokens']:>7} {r['wn_tokens']:>7}  {sign}{red_pct:>4.0f}%  {r['accuracy']}/5  {b}")
    print(f"{'─'*74}")
    print(f"  {'合計/均':<24} {total_en:>7} {total_wn:>7}  ▼{avg_reduction*100:>4.0f}%  {avg_accuracy:.1f}/5")
    print(f"{'═'*74}")

    print(f"\n  ── 各題對比 ({mode_label}) ──────────────────────────────────────────\n")
    for r in results:
        print(f"  【{r['id']}】")
        print(f"  白話 ({r['en_tokens']} tok)：{r['en_text']}")
        print(f"  文言 ({r['wn_tokens']} tok)：{r['wn_text']}")
        print(f"  評：{r['accuracy']}/5  {r['notes']}")
        print()

    print(f"  子曰：文言省token {avg_reduction*100:.0f}%，準確度 {avg_accuracy:.1f}/5。")
    if avg_accuracy >= 4.0:
        print("  此乃可行之道矣。")
    elif avg_accuracy >= 3.0:
        print("  尚可，然需打磨。")
    else:
        print("  大謬！系統提示需改。")


def run_demo():
    print(f"{'─'*74}")
    print(f"  文言 vs 白話 Benchmark  【示範模式 — 預設例句 + 估算token】")
    print(f"{'─'*74}\n")
    print("  注：token數為估算值（EN ~4字符/tok，ZH ~1.5字符/tok）")
    print("  準確分為人工標注。如需精確數值，請提供ANTHROPIC_API_KEY。\n")

    results = []
    for p, f in zip(PROMPTS, FIXTURES):
        assert p["id"] == f["id"]
        en_tok = estimate_tokens(f["en"])
        wn_tok = estimate_tokens(f["wn"])
        reduction = (en_tok - wn_tok) / en_tok if en_tok else 0
        results.append({
            "id": p["id"],
            "en_tokens": en_tok,
            "wn_tokens": wn_tok,
            "reduction": reduction,
            "accuracy": 5,   # human-labelled: fixtures preserve all info
            "notes": "人工核準",
            "en_text": f["en"],
            "wn_text": f["wn"],
        })

    print_results(results, "示範")

    with open("results.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    print("\n  結果存於 results.json")


def run_live():
    client = anthropic.Anthropic()
    results = []

    print(f"{'─'*74}")
    print(f"  文言 vs 白話 Benchmark   model={MODEL}")
    print(f"{'─'*74}\n")

    for p in PROMPTS:
        qid, q = p["id"], p["q"]
        print(f"  [{qid}] {q[:62]}{'…' if len(q)>62 else ''}")

        en_text, en_tok = call_api(client, NORMAL_SYSTEM, q)
        time.sleep(0.3)
        wn_text, wn_tok = call_api(client, WENYAN_SYSTEM, q)
        time.sleep(0.3)
        verdict = judge_api(client, q, en_text, wn_text)
        time.sleep(0.3)

        reduction = (en_tok - wn_tok) / en_tok if en_tok else 0
        results.append({
            "id": qid,
            "en_tokens": en_tok,
            "wn_tokens": wn_tok,
            "reduction": reduction,
            "accuracy": verdict["score"],
            "notes": verdict.get("notes", ""),
            "en_text": en_text,
            "wn_text": wn_text,
        })

        sign = "▼" if wn_tok < en_tok else "▲"
        print(f"    白話 {en_tok:>3} tok │ 文言 {wn_tok:>3} tok │ {sign}{abs(reduction)*100:.0f}% │ 準確 {verdict['score']}/5\n")

    print_results(results, "實測")

    with open("results.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)
    print("\n  結果存於 results.json")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_demo()
    else:
        run_live()
