---
name: "Bug report"
about: "Something the plugin did wrong"
title: "Bug: <one-line summary>"
labels: ["bug"]
---

**What happened**

…

**What you expected to happen**

…

**Reproduction**

1. …
2. …

**Environment**

- Claude Code version: <`claude --version`>
- Plugin version: <from `/plugin` listing>
- C++ compiler: <`clang --version` or `g++ --version`>
- OS:

**Classification (please pick one if you can)**

- [ ] Wrong suggestion — the plugin recommended a non-C++26 idiom
- [ ] Wrong classification — `@cpp26-reviewer` mis-classified a
      diagnostic (bug vs compiler-lag)
- [ ] Activation failure — the skill didn't load when it should have
- [ ] MCP failure — `lookup_paper` / `search` / `compiler_status`
      returned something wrong
- [ ] Tool failure — slash command / hook misbehaved
- [ ] Other

**Logs** (if you have them):

```
…
```
