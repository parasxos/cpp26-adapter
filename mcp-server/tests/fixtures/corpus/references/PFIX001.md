---
id: PFIX001
title: "Reflection for C++26 (fixture)"
revision: R1
tier: deep
category: reflection
keywords: [reflect, std::meta, splice, "^^", template for]
canonical_url: https://example.invalid/PFIX001
---

# PFIX001 — Reflection (fixture)

## Problem
Compile-time introspection over enums, classes, namespaces — without
external codegen, X-macros, or Boost.Describe.

## Key syntax
- `^^E` — reflection operator
- `[: e :]` — splicer
- `std::meta::*` — introspection API

## Canonical example: enum to string
```cpp
template <typename E> requires std::is_enum_v<E>
constexpr std::string_view enum_name(E v);
```
