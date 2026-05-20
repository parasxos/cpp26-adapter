---
name: "Install confirmation \U0001F44D"
about: "Quick reply: I installed the plugin and it worked"
title: "Install works — [your-handle]"
labels: ["installed", "external"]
---

Quick install confirmation — closes part of the v1.0 gate
(per [`PLAN.md`](../../PLAN.md) §8).

- [ ] I ran `/plugin marketplace add parasxos/claude-plugins`
- [ ] I ran `/plugin install cpp26-adapter@parasxos/claude-plugins`
- [ ] I asked Claude for *"enum to string for `enum class E { A, B }`"*
      and the response used `std::meta` reflection (not X-macros or `magic_enum`)

**My toolchain** (so the maintainer knows what was tested):

- OS: <macOS / Ubuntu / Windows / …>
- Claude Code version: <output of `claude --version`>
- C++ compiler: <output of `clang --version` or `g++ --version`>

**Anything that didn't work?** *(Optional — leave blank if everything was clean.)*

<!-- Maintainer note: every confirming install is the social signal the
     plugin needs to clear its Phase 8 acceptance criterion. Thanks. -->
