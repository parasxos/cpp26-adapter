# Knowledge corpus

**216 papers indexed** from `cplusplus/papers` (union of `label:C++26 + plenary-approved` with `label:IS + plenary-approved` minus other-version IS papers — this catches plenary-adopted papers that were never re-labelled). Spot-checked against [cppreference.com/w/cpp/26](https://en.cppreference.com/w/cpp/26): **19/20 random rows match.**

Tiering: **16 hand-curated deep references** with frontmatter + Problem + Key syntax + Canonical example + Pre-C++26 equivalent + Gotchas + Related; **52 templated shallow refs**; **148 stubs** for full surface coverage and search recall.

## The 16 deep-tier papers

The C++26 surface the plugin biases hardest toward:

| Paper | Feature | Headline idiom |
|---|---|---|
| **P2996** | Reflection | `^^`, splicers, `std::meta` |
| **P2900** | Contracts | `pre`/`post`/`contract_assert` |
| **P2300** | `std::execution` | senders / receivers |
| **P1306** | Expansion statements | `template for` |
| **P2662** | Pack indexing | `args...[N]` |
| **P2573** | `= delete("reason")` | deletion with diagnostics |
| **P2893** | Variadic friends | `friend Ts...;` |
| **P1967** | `#embed` | binary-asset embedding |
| **P2795** | Erroneous behaviour | uninit-read sanitization |
| **P1673** | `std::linalg` | BLAS-style linear algebra |
| **P2530** | Hazard pointers | lock-free reclamation |
| **P2545** | RCU | read-copy-update |
| **P3471** | Library hardening | bounds-checked containers |
| **P3068** | `throw` in constexpr | constant-eval diagnostics |
| **P2169** | Placeholder `_` | unused-binding placeholder |
| **P0843** | `std::inplace_vector` | fixed-capacity container |

## Eval gate (methodology)

A held suite of **39 tasks** (≥1 per deep-tier idiom, ≥1 per category) scored on three axes per task: standard-compliance (regex on fenced cpp blocks), syntactic correctness (`clang -std=c++2c -fsyntax-only`), and idiomatic quality (LLM-judge, 1–5 rubric).

| Suite | Plugin ON | Plugin OFF | Bar | Margin |
|---|---:|---:|---:|---:|
| 39-task held suite | **37/39 (95%)** | 14/39 (36%) | ≥85% | **+10 pp** |

Per-task breakdown: [`eval/results-v0.9.0.md`](../eval/results-v0.9.0.md). Harness: [`eval/run.py`](../eval/run.py).

**Methodology note.** The first audited run scored 23/39 (59%). The audit traced the gap to the eval regex matching prose mentions of pre-C++26 names rather than the fenced `cpp` answer block. A one-line harness change (anchor `must_not_contain` to the last fenced block) recovered the full delta — **no `SKILL.md` changes were required.** That distinction matters: the eval gate measures the plugin, not the harness.
