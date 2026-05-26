# What changes when this is installed

Three concrete side-by-side examples beyond the enum-to-string hook in the README. Each pair shows what a vanilla LLM emits and what `cpp26-adapter` biases it toward.

## A. Preconditions

> *"`int divide(int a, int b)` — express that `b != 0` is a programmer error."*

**Vanilla** — `assert(b != 0);` (disappears in release builds).
**With plugin** — P2900 contracts, enforced under the build's chosen contract-evaluation semantic:

```cpp
int divide(int a, int b) pre (b != 0) { return a / b; }
```

## B. Async pipeline

> *"Start with 7, multiply by 6, wait synchronously."*

**Vanilla** — `std::async(std::launch::async, []{ return 7*6; }).get();`
**With plugin** — P2300 `std::execution` senders:

```cpp
namespace ex = std::execution;
auto [r] = ex::sync_wait(ex::just(7) | ex::then([](int x){ return x*6; })).value();
```

## C. Embed a binary asset

> *"Include the bytes of `assets/icon.png` as a constexpr array."*

**Vanilla** — pre-build `xxd -i` or `objcopy --add-section`.
**With plugin** — P1967:

```cpp
constexpr unsigned char icon_png[] = {
    #embed "assets/icon.png"
};
```

## Install verification

Three sanity checks that should all work with no further setup after `/plugin install cpp26-adapter@parasxos/claude-plugins`:

1. Ask Claude *"write enum-to-string for `enum class E { A, B }`"* — the response should use `std::meta` reflection, not X-macros or `magic_enum`.
2. Run `@cpp26-reviewer src/foo.cpp` — should return a YAML report with `status: pass | needs-changes | compiler-lag-only`.
3. Run `/cpp26-init` in an empty directory — the scaffolded `CMakeLists.txt` should build a `#include <print>` + `std::print("hi\n")` hello-world via `cmake -B build && cmake --build build`.
