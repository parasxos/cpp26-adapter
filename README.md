# cpp26-adapter

**Turn your LLM coding assistant into a C++26 specialist.**
A Claude Code plugin that biases generation toward ISO/IEC 14882:2026 final-form idioms — reflection, contracts, senders, `inplace_vector`, `#embed` — even when your local clang hasn't caught up.

[![ci](https://github.com/parasxos/cpp26-adapter/actions/workflows/ci.yml/badge.svg)](https://github.com/parasxos/cpp26-adapter/actions/workflows/ci.yml)
[![version](https://img.shields.io/badge/version-v1.0.0-blue)](https://github.com/parasxos/cpp26-adapter/releases/tag/v1.0.0)
[![eval](https://img.shields.io/badge/eval-35%2F39%20(90%25)-brightgreen)](eval/results-v0.9.1.md)
[![bar](https://img.shields.io/badge/bar-%E2%89%A585%25-success)](eval/results-v0.9.1.md)
[![standard](https://img.shields.io/badge/ISO%2FIEC-14882%3A2026-orange)](https://www.iso.org/standard/83626.html)
[![code license](https://img.shields.io/badge/code-MIT-green)](LICENSE-CODE)
[![corpus license](https://img.shields.io/badge/corpus-CC--BY--SA--4.0-green)](LICENSE-CORPUS)

```
/plugin marketplace add parasxos/claude-plugins
/plugin install cpp26-adapter@parasxos/claude-plugins
```

---

## The hook — ask for "enum to string"

**Vanilla LLM** falls back to X-macros or pulls in `magic_enum`.
**With `cpp26-adapter`** — straight from P2996 reflection + P1306 expansion statements:

```cpp
template <typename E> requires std::is_enum_v<E>
constexpr std::string_view enum_name(E v) {
    template for (constexpr auto e :
                  std::define_static_array(std::meta::enumerators_of(^^E))) {
        if (v == [: e :]) return std::meta::identifier_of(e);
    }
    return "<unknown>";
}
```

No macros. No third-party dep. No codegen.

## Six idiom shifts

| You ask for… | Vanilla LLM emits | `cpp26-adapter` emits |
|---|---|---|
| enum → string | X-macros / `magic_enum` | reflection + `template for` |
| precondition | `assert(x > 0)` | `pre(x > 0)` |
| async pipeline | `std::async(...)` | `ex::just \| ex::then \| ex::sync_wait` |
| fixed-capacity vector | `boost::static_vector` | `std::inplace_vector<T, N>` |
| embed binary asset | `objcopy` / `xxd` | `#embed "asset.bin"` |
| Nth pack element | `std::get<N>(std::forward_as_tuple(args...))` | `args...[N]` |

## The invariant

**Recommendations follow the standard, not the toolchain.** If `clang < 22` / `gcc < 16` haven't shipped a feature, the plugin still suggests the C++26 form. Compiler errors are surfaced as `compiler-lag` (paper adopted, compiler incomplete) or `bug` — never auto-rewritten into a pre-C++26 workaround.

The suggestion path (skill + MCP) is compiler-agnostic; compiler awareness lives only in the reviewer's Pass-2 syntax check.

## Eval

37/39 (95%) with plugin **ON** vs 14/39 (36%) **OFF** on a 39-task held suite; bar ≥85%. See [`eval/results-v0.9.0.md`](eval/results-v0.9.0.md).

## Status

**v1.0.0** — eval gate held across two successive refreshes. The MCP tool signatures, the subagent's output schema, and the standard-first invariant are contract-binding for the `1.x` line.

## License

Dual-licensed by directory. Code outside `corpus/`: [MIT](LICENSE-CODE). Knowledge corpus in `corpus/`: [CC-BY-SA 4.0](LICENSE-CORPUS).

## See also

- [`docs/architecture.md`](docs/architecture.md) — full invariant, component diagram, walkthrough
- [`docs/examples.md`](docs/examples.md) — contracts, senders, `#embed` side-by-side
- [`docs/papers.md`](docs/papers.md) — the 16 deep-tier papers + eval methodology
- [`docs/FAQ.md`](docs/FAQ.md) — clang/gcc compatibility, legacy code, refresh cadence
