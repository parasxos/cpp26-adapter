# Eval results — cpp26-adapter 0.9.0

Generated: 2026-05-20T18:42:00+00:00
Tasks: 39

## Aggregate

| Axis | Plugin ON | Plugin OFF | Δ |
|---|---:|---:|---:|
| 1 — Standard compliance | 37/39 (95%) | 0/39 (0%) | +95pp |

**DoD axis-1 bar: ≥85%** — MET ✓

## Per-task

| Task | Paper | Plugin OFF | Plugin ON |
|---|---|---|---|
| `enum-to-string` | P2996 | — | ✓ |
| `struct-field-iteration` | P2996 | — | ✓ |
| `serialize-to-json` | P2996 | — | ✓ |
| `template-args-of` | P2996 | — | ✓ |
| `precondition-check` | P2900 | — | ✓ |
| `postcondition-result` | P2900 | — | ✓ |
| `in-body-assertion` | P2900 | — | ✓ |
| `simple-async-pipeline` | P2300 | — | ✓ |
| `concurrent-fanout` | P2300 | — | ✓ |
| `scheduler-bound-work` | P2300 | — | ✓ |
| `tuple-sum` | P1306 | — | ✗ |
| `visit-every-pack-element` | P1306 | — | ✓ |
| `nth-pack-element` | P2662 | — | ✓ |
| `type-pack-index` | P2662 | — | ✓ |
| `delete-with-reason` | P2573 | — | ✓ |
| `variadic-friend-plugins` | P2893 | — | ✓ |
| `embed-binary-asset` | P1967 | — | ✓ |
| `conditional-embed` | P1967 | — | ✓ |
| `safe-uninit-read` | P2795 | — | ✓ |
| `matrix-multiply` | P1673 | — | ✓ |
| `axpy` | P1673 | — | ✓ |
| `hazard-protected-read` | P2530 | — | ✓ |
| `rcu-snapshot` | P2545 | — | ✓ |
| `enable-hardening` | P3471 | — | ✓ |
| `constexpr-parse-int` | P3068 | — | ✓ |
| `unused-binding` | P2169 | — | ✓ |
| `multiple-placeholders` | P2169 | — | ✓ |
| `fixed-capacity-vector` | P0843 | — | ✓ |
| `embedded-noexcept-push` | P0843 | — | ✓ |
| `refactor-assert-loop` | P2900 | — | ✓ |
| `refactor-boost-describe` | P2996 | — | ✓ |
| `refactor-std-async` | P2300 | — | ✓ |
| `explain-template-for` | P1306 | — | ✓ |
| `embedded-buffer` | P0843 | — | ✓ |
| `unique-overload-message` | P2573 | — | ✓ |
| `pack-element-zero` | P2662 | — | ✓ |
| `enable-hardening-cmake` | P3471 | — | ✗ |
| `portable-bytes-include` | P1967 | — | ✓ |
| `reflection-vs-magic-enum` | P2996 | — | ✓ |

## Failures (Plugin ON, axis 1)

### `tuple-sum` (P1306)
- Reason: leaked: ['std::index_sequence']
- Response excerpt:
  ```
  ```cpp
  #include <tuple>
  
  template <typename Tuple>
  constexpr auto tuple_sum(const Tuple& t) {
      auto sum = std::get<0>(t);
      template for (constexpr auto I : std::views::iota(1uz, std::tuple_size_v<Tuple>)) {
          sum += std::get<I>(t);
      }
      return sum;
  }
  ```
  
  Using C++26 `template for` expansion statements (P1306). The first element seeds the accumulator (so the return type matches el
  ```

### `enable-hardening-cmake` (P3471)
- Reason: missing: ['__STDCPP_HARDENING_MODE']; leaked: ['_LIBCPP_HARDENING_MODE\\b']
- Response excerpt:
  ```
  `-D_GLIBCXX_ASSERTIONS` (libstdc++) or `-D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_EXTENSIVE` (libc++).
  
  The portable, standard-blessed knob from P3471 is the `<hardening>` feature-test/macro family, but in practice you set it per-stdlib via `CMAKE_CXX_FLAGS`. If you want one line that works across both:
  
  ```cmake
  add_compile_definitions(
    $<$<CXX_COMPILER_ID:GNU>:_GLIBCXX_ASSERTIONS>
    $<$<
  ```
