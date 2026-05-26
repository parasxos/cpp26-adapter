# FAQ

**My toolchain is clang 21 / gcc 15. Will the suggestions even compile?**
Often no — and that's by design. The reviewer's Pass 2 runs `clang -std=c++2c -fsyntax-only` and classifies each diagnostic as `compiler-lag` (paper adopted, compiler incomplete) or `bug` (genuine code error). You see both axes side by side. The suggestion is never silently downgraded to a pre-C++26 workaround. For reflection demos before clang 22 ships, use [`bloomberg/clang-p2996`](https://github.com/bloomberg/clang-p2996).

**Will it rewrite my legacy C++17/20/23 code?**
No. The plugin only fires on new generation and on files you explicitly hand to `@cpp26-reviewer`. Existing code is untouched. For a subdirectory you want fully exempt, drop a `.cpp26-adapter.yaml` containing `skip-skill: true` — the skill defers in that subtree.

**What about C++23 or C++29?**
Out of scope. The plugin is purpose-built for C++26 final form (ISO/IEC 14882:2026). C++23 idioms are not corrected; C++29 is not addressed.

**How is it kept current with paper revisions and compiler progress?**
Quarterly refresh — the paper index, the compiler-status table, and the eval suite are all re-run on a quarterly cadence so the corpus tracks WG21 meetings and compiler progress. Subsequent quarterly refreshes are tagged as patch or minor bumps under the v1.x line.

**How is the corpus sourced?**
`corpus/scripts/fetch_index.py` queries `cplusplus/papers` via the GitHub API and unions two filters to catch plenary-adopted-but-unlabelled papers. The 16 deep references are hand-authored against the canonical paper text; shallow and stub tiers are template-generated from the index. Everything in `corpus/` is CC-BY-SA-4.0 and derives from public WG21 material — see [`LICENSE-CORPUS`](../LICENSE-CORPUS) for attribution.

## What this plugin is **not**

- It does **not** retrain or fine-tune any model.
- It does **not** patch your compiler. `compiler-lag` is a label, not a fix.
- It does **not** ship C++29 support. That's a non-goal.
- It does **not** rewrite existing source files unprompted. The reviewer is opt-in; the hook only surfaces findings on edits Claude itself authored.
- It does **not** ship a fork of clang. If you need a reflection-capable build today, install [`bloomberg/clang-p2996`](https://github.com/bloomberg/clang-p2996).
