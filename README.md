# 文言 (Wenyan) — Classical Chinese Mode for AI Agents

> 話多費錢古人嗤，聖賢文言字字奇。
> 今有模型學古道，子曰：省token不亦宜？
>
> *The ancients sneered at verbose men. The sages' every character was precious.*
> *Now a model learns the ancient way. The Master said: is it not fitting to save tokens?*

---

Your AI is burning money talking like this:

> *"That's a great question! The issue you're experiencing is most likely caused by a race condition in the authentication middleware, where the token expiry check is using a strict less-than operator instead of less-than-or-equal-to, which means your tokens are expiring approximately one second earlier than they should be. I would recommend addressing this by modifying the comparison operator in your auth logic."*

When it could just say:

> 驗件競爭。`<`→`<=`。改。

**Same information. 75% fewer tokens. Infinitely more gravitas.**

---

## 🏆 Benchmark Results

10 coding prompts. Two modes. One winner (it's 2,000 years old).

```
══════════════════════════════════════════════════════════════════════════
  Topic                    English    文言    Saved   Accuracy
──────────────────────────────────────────────────────────────────────────
  race_condition               68      34     ▼ 50%    5/5  ██████████░░
  auth_bug                     49      24     ▼ 51%    5/5  ██████████░░
  reduce                       36      21     ▼ 42%    5/5  ████████░░░░
  slow_query                   59      33     ▼ 44%    5/5  █████████░░░
  recursion                    42      18     ▼ 57%    5/5  ███████████░
  process_vs_thread            75      38     ▼ 49%    5/5  ██████████░░
  null_pointer                 56      30     ▼ 46%    5/5  █████████░░░
  rest_api                     53      28     ▼ 47%    5/5  █████████░░░
  git_rebase                   71      37     ▼ 48%    5/5  ██████████░░
  big_o                        54      30     ▼ 44%    5/5  █████████░░░
──────────────────────────────────────────────────────────────────────────
  TOTAL / AVG                 563     293     ▼ 48%    5.0/5
══════════════════════════════════════════════════════════════════════════
```

子曰：文言省token 48%，準確度 5.0/5。此乃可行之道矣。
*(The Master said: 48% token savings, 5.0/5 accuracy. This is the right path.)*

> Run it yourself: `python3 benchmark/benchmark.py --demo`
> With API key: `python3 benchmark/benchmark.py`

---

## Why Does This Work?

Classical Chinese was the written lingua franca of East Asia for **two thousand years**, refined by scholars who had to carve characters into oracle bones and bamboo strips. Brevity was not a style choice — it was a physical constraint.

The result: a language where one character routinely does the work of five English words, subjects are dropped when obvious, and "The function returned null because the database connection pool was exhausted" becomes:

**函返空，倉接竭也。**

Silicon Valley spent decades building compression algorithms. Confucius did it with a brush.

---

## Install

### Claude Code (recommended)

**Global** — available in every project:

```bash
curl -o ~/.claude/skills/wenyan.md \
  https://raw.githubusercontent.com/zixiaoshawnshi/wenyan/master/skills/wenyan/SKILL.md
```

**Project-level** — current repo only:

```bash
mkdir -p .claude/skills && curl -o .claude/skills/wenyan.md \
  https://raw.githubusercontent.com/zixiaoshawnshi/wenyan/master/skills/wenyan/SKILL.md
```

Then invoke with `/wenyan` in any Claude Code session.

### Other agents / custom system prompts

Copy the contents of [`skills/wenyan/SKILL.md`](skills/wenyan/SKILL.md) into your agent's system prompt, then:

```
User: wenyan mode

Agent: 文言模式起用矣。
```

---

## Usage

**Intensity levels:**

| Command | Mode | Style |
|---------|------|-------|
| `/wenyan lite` | 文言·疏 | Drops filler, keeps English structure |
| `/wenyan` | 文言·正 *(default)* | Full Classical Chinese grammar |
| `/wenyan ultra` | 文言·密 | Oracle bone script energy, ~80% reduction |

**Stop it:**
```
User: stop wenyan / normal mode / speak english / I can't read this
```

---

## Vocabulary Cheat Sheet

The skill ships with a full tech glossary. Highlights:

| English | 文言 | Why it's perfect |
|---------|------|-----------------|
| bug | 蟲 | Literally "worm." Poetic justice. |
| database | 倉 | "Storehouse." Confucius would approve. |
| deploy | 布 | "Spread across the land." Very dramatic. |
| error | 誤 | One stroke. Maximum disappointment. |
| null | 空 | "The void." Philosophically accurate. |
| done | 完矣 | "It is complete." Drop the mic. |

---

## Situational Classics

| Situation | 文言 | Translation |
|-----------|------|-------------|
| Bug found | 蟲已得 | The worm has been caught |
| Tests pass | 試皆通 | All trials succeeded |
| Code is good | 碼善，可布 | The code is virtuous, deploy it |
| Catastrophic error | 大謬！ | GREAT WRONGNESS |
| Task complete | 完矣 | It is complete |
| Genius solution | 妙哉！ | How wondrous! |
| Hard disagree | 大謬，非也！ | Great wrongness, NO! |
| Deep in thought | 吾沉思焉⋯ | I am pondering therein… |

---

## Inspired By

- [caveman](https://github.com/JuliusBrussee/caveman) — the original token-compression skill. We took it back another 50,000 years.
- 《論語》— *The Analects of Confucius*. The original compressed reasoning traces.
- 甲骨文 — Oracle bone script. The original low-context, high-density encoding.

---

## Safety

文言 mode suspends itself for:
- Security warnings and irreversible actions
- Any time you say you're confused

夫子諒之。 *(The Master understands.)*

---

*子曰：學而時習之，不亦說乎？*
*(The Master was almost certainly talking about token efficiency. Probably.)*
