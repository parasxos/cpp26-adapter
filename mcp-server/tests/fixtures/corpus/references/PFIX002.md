---
id: PFIX002
title: "Contracts (fixture)"
revision: R1
tier: deep
category: contracts
keywords: [contract_assert, pre, post, contract]
canonical_url: https://example.invalid/PFIX002
---

# PFIX002 — Contracts (fixture)

## Problem
`assert(...)` evaluates side-effecting expressions and disappears in
release builds without diagnostic. Contracts give pre/post/assertion
hooks with violation handlers.

## Key syntax
- `pre(cond)` — function precondition
- `post(r : cond)` — function postcondition (result binding `r`)
- `contract_assert(cond)` — in-body assertion
