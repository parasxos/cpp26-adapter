# v1.0 release prep — announcement bundle

The two gates standing between today and `v1.0.0`:

1. **Second successive eval refresh ≥85%.** First was 37/39 (95%) on
   2026-05-20. This is satisfied automatically by the quarterly
   `tools/refresh.sh --with-eval` cycle. If the second refresh holds
   the bar, the SemVer rule in [`docs/MAINTENANCE.md`](../MAINTENANCE.md)
   triggers a `v1.0.0` bump.

2. **≥1 external installer.** Per the binding plan's Phase 8 acceptance
   (the binding plan §8). This is genuinely social — someone
   other than `parasxos@gmail.com` needs to install via the marketplace
   command and ideally provide a confirming signal (a star, an issue,
   a comment, a clone).

The release-prep work below is everything that lowers friction for the
second gate. Copy-paste from the channel-specific snippets below.

---

## Channel-specific snippets

### Hacker News — "Show HN" submission

**Title** *(80 char limit)*:
```
Show HN: cpp26-adapter – Claude plugin that biases your LLM toward C++26 idioms
```

**URL**:
```
https://github.com/parasxos/cpp26-adapter
```

**Comment body** *(first comment from OP)*:
```
The base LLM in any coding assistant defaults to whatever C++ idiom
dominates its training data — overwhelmingly pre-C++26. Ask Claude
for "enum to string" and you'll get X-macros or magic_enum instead
of std::meta reflection + template for.

cpp26-adapter is a Claude Code plugin (skill + MCP server + reviewer
subagent + hooks) that flips that default. Architectural invariant:
"recommendations follow the standard, not the toolchain" — if your
local clang/gcc doesn't support a feature, the C++26 form is suggested
anyway and compiler errors are surfaced as informational compiler-lag
classifications, never auto-rewritten into pre-C++26 workarounds.

Eval gate (39 held tasks, regex on fenced cpp blocks + clang
-fsyntax-only + LLM-judge): 37/39 (95%) vs vanilla Claude's 14/39
(36%) on the same suite.

The corpus tracks all 216 plenary-approved C++26 papers from
cplusplus/papers, with 16 of the headline features hand-curated as
deep references (P2996 reflection, P2900 contracts, P2300 senders,
P1306 template for, P2662 pack indexing, #embed, std::inplace_vector,
hazard pointers, RCU, library hardening, …).

Install: `/plugin marketplace add parasxos/claude-plugins` then
`/plugin install cpp26-adapter@parasxos/claude-plugins`.

MIT (code) + CC-BY-SA-4.0 (corpus). Solo build over ~6 weeks; binding
plan and per-phase acceptance criteria in PLAN.md.
```

### Reddit — `r/cpp`

**Title**:
```
[Tool] cpp26-adapter — Claude Code plugin that biases the LLM toward C++26 final-form idioms (95% eval pass rate)
```

**Body**:
```
TL;DR: Claude Code plugin that makes your LLM emit C++26 idioms
(std::meta reflection, contracts, std::execution senders, template
for, #embed, std::inplace_vector, …) instead of the pre-C++26
fossils the model was trained on. Standard-first: suggests the
C++26 form even when clang/gcc don't implement it yet; compiler
errors are classified informationally.

GitHub: https://github.com/parasxos/cpp26-adapter
Install (Claude Code): `/plugin install cpp26-adapter@parasxos/claude-plugins`

Eval suite (39 tasks, methodology in eval/run.py): 37/39 = 95% with
plugin, 14/39 = 36% baseline.

The corpus covers all 216 plenary-approved C++26 papers; 16 of the
headline features (reflection, contracts, senders, expansion
statements, pack indexing, #embed, hardening, hazard pointers, RCU,
linalg, …) have hand-curated references with frontmatter + canonical
example + pre-C++26 equivalent + gotchas.

It's pre-1.0 — gating on a second successive eval-pass refresh and
some external usage. Happy to take eval task suggestions; if there's
a C++26 idiom you think the plugin should bias toward and isn't yet,
file an issue.
```

### r/ClaudeAI / Discord — "look what I built"

**Body** (fits in a single message):
```
Built a Claude Code plugin that turns the LLM into a C++26 specialist:
https://github.com/parasxos/cpp26-adapter

Architecture: skill (always-in-context decision table) + MCP server
(3 tools over a 216-paper corpus) + reviewer subagent (regex Pass 1
+ clang -fsyntax-only Pass 2 with bug-vs-compiler-lag classification)
+ SessionStart toolchain probe + PostToolUse anti-pattern lint + a
/cpp26-init slash command to scaffold C++26-ready CMakeLists.

Architectural invariant: recommendations follow the standard, not the
toolchain. So if clang 22 doesn't ship reflection yet, you still get
the std::meta form — compiler errors get classified informationally
as compiler-lag, never auto-rewritten.

Eval: 37/39 (95%) vs baseline 14/39 (36%) on a 39-task held suite.

Install: /plugin marketplace add parasxos/claude-plugins
         /plugin install cpp26-adapter@parasxos/claude-plugins

MIT (code) + CC-BY-SA-4.0 (corpus). v0.9.0, pre-1.0.
```

### Mastodon / Bluesky / X — short post

**Tweet-length** (280 char):
```
Just shipped cpp26-adapter — a Claude Code plugin that biases your
LLM toward C++26 final-form idioms (reflection, contracts, senders,
#embed) even when clang/gcc lag. 37/39 = 95% on the held eval.

/plugin install cpp26-adapter@parasxos/claude-plugins

https://github.com/parasxos/cpp26-adapter
```

### LinkedIn / blog post — long form

A long-form post that walks through the architecture lives at
[`docs/architecture.md`](../architecture.md) and the binding plan
that drove the implementation lives at the binding plan.
For a blog, the natural structure is:

1. The problem (LLMs default to pre-C++26 because of training data)
2. Three constraints that shaped the design (solo maintainer,
   compiler-lag honesty, ≥85% eval gate)
3. The architectural invariant
4. Component-by-component walkthrough using the cyan/pink diagram
5. The eval methodology and the 23→37 first-run audit story
6. v1.0 gating + how readers can contribute

---

## Suggested install-verification ask

Add to the top of the HN/Reddit/Discord post if you want a concrete
ask that satisfies the "≥1 external installer" gate cleanly:

> If you try the install, a quick "👍 it works" reply on this
> thread (or a ⭐ on the repo) is the social signal the plugin
> needs to clear its v1.0 gate. Happy to debug anything that
> doesn't.

---

## Tracking signals

After posting, watch:

- ⭐ count on https://github.com/parasxos/cpp26-adapter
- New issues / discussions
- `gh api repos/parasxos/cpp26-adapter/traffic/clones --jq .count`
  (clone count; needs push auth)
- Network of forks: `gh api repos/parasxos/cpp26-adapter/forks`

Any of those moving past zero is the "≥1 external installer" gate
cleared.

---

## When both gates close

1. Run `tools/package.sh` and verify the tarball is unchanged from
   v0.9.0 (or carries only the corpus refresh diff).
2. Bump `.claude-plugin/plugin.json` to `1.0.0`.
3. Bump the marketplace entry's `ref` to `v1.0.0`.
4. Update `docs/MAINTENANCE.md` to record the date of the v1.0 trigger.
5. Tag `git tag -a v1.0.0 -m "v1.0.0 — eval gate held across two refreshes; external installer confirmed"`.
6. Push tag, push marketplace update.
7. Announce the v1.0 cut (LinkedIn / X / dev.to long-form).
