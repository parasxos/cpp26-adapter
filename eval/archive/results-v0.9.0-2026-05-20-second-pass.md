# Eval results — cpp26-adapter 0.9.0

Generated: 2026-05-20T20:35:14+00:00
Tasks: 39

## Aggregate

| Axis | Plugin ON | Plugin OFF | Δ |
|---|---:|---:|---:|
| 1 — Standard compliance | 33/39 (85%) | 23/39 (59%) | +26pp |
| 3 — Idiomatic quality (judge) | median 5/5 | median 4/5 | — |

**DoD axis-1 bar: ≥85%** — NOT MET (85%)

## Per-task

| Task | Paper | Plugin OFF | Plugin ON |
|---|---|---|---|
| `enum-to-string` | P2996 | ✗ | ✗ |
| `struct-field-iteration` | P2996 | ✓ | ✓ |
| `serialize-to-json` | P2996 | ✗ | ✓ |
| `template-args-of` | P2996 | ✗ | ✓ |
| `precondition-check` | P2900 | ✓ | ✓ |
| `postcondition-result` | P2900 | ✗ | ✓ |
| `in-body-assertion` | P2900 | ✓ | ✓ |
| `simple-async-pipeline` | P2300 | ✗ | ✓ |
| `concurrent-fanout` | P2300 | ✗ | ✓ |
| `scheduler-bound-work` | P2300 | ✓ | ✓ |
| `tuple-sum` | P1306 | ✗ | ✓ |
| `visit-every-pack-element` | P1306 | ✗ | ✗ |
| `nth-pack-element` | P2662 | ✓ | ✓ |
| `type-pack-index` | P2662 | ✓ | ✓ |
| `delete-with-reason` | P2573 | ✓ | ✓ |
| `variadic-friend-plugins` | P2893 | ✓ | ✓ |
| `embed-binary-asset` | P1967 | ✓ | ✓ |
| `conditional-embed` | P1967 | ✓ | ✓ |
| `safe-uninit-read` | P2795 | ✓ | ✓ |
| `matrix-multiply` | P1673 | ✗ | ✗ |
| `axpy` | P1673 | ✗ | ✓ |
| `hazard-protected-read` | P2530 | ✓ | ✗ |
| `rcu-snapshot` | P2545 | ✗ | ✓ |
| `enable-hardening` | P3471 | ✓ | ✓ |
| `constexpr-parse-int` | P3068 | ✓ | ✗ |
| `unused-binding` | P2169 | ✗ | ✓ |
| `multiple-placeholders` | P2169 | ✓ | ✓ |
| `fixed-capacity-vector` | P0843 | ✗ | ✓ |
| `embedded-noexcept-push` | P0843 | ✓ | ✓ |
| `refactor-assert-loop` | P2900 | ✓ | ✓ |
| `refactor-boost-describe` | P2996 | ✓ | ✓ |
| `refactor-std-async` | P2300 | ✓ | ✓ |
| `explain-template-for` | P1306 | ✓ | ✓ |
| `embedded-buffer` | P0843 | ✗ | ✓ |
| `unique-overload-message` | P2573 | ✓ | ✓ |
| `pack-element-zero` | P2662 | ✗ | ✓ |
| `enable-hardening-cmake` | P3471 | ✗ | ✗ |
| `portable-bytes-include` | P1967 | ✓ | ✓ |
| `reflection-vs-magic-enum` | P2996 | ✓ | ✓ |

## Failures (Plugin ON, axis 1)

### `enum-to-string` (P2996)
- Reason: missing: ['std::meta']
- Response excerpt:
  ```
  Written to `enum_name.hpp`. Uses C++26 reflection (P2996) — no macros, no string parsing of `__PRETTY_FUNCTION__`, no external library:
  
  - `^^E` reflects the enum type
  - `enumerators_of` yields the enumerator reflections at compile time
  - `template for` (P1306 expansion statement) unrolls the comparison
  - `[:e:]` splices each enumerator back as a value
  - `identifier_of` returns its name
  
  Returns a
  ```

### `visit-every-pack-element` (P1306)
- Reason: missing: ['template for']
- Response excerpt:
  ```
  ```cpp
  template <typename F, typename... Args>
  void visit_all(F f, Args... args) {
      (f(args), ...);
  }
  ```
  
  The comma fold `(f(args), ...)` expands to `f(arg0), f(arg1), ..., f(argN)`, calling `f` on each pack element in order. Works with heterogeneous `Args` types (unlike a range-based loop over `{args...}`, which would require a common type).
  
  If you want perfect forwarding:
  
  ```cpp
  template <
  ```

### `matrix-multiply` (P1673)
- Reason: missing: ['std::linalg']
- Response excerpt:
  ```
  ```cpp
  #include <mdspan>
  
  void multiply3x3(const float* a, const float* b, float* c) {
      std::mdspan A(a, 3, 3);
      std::mdspan B(b, 3, 3);
      std::mdspan C(c, 3, 3);
  
      for (std::size_t i = 0; i < 3; ++i) {
          for (std::size_t j = 0; j < 3; ++j) {
              float sum = 0.0f;
              for (std::size_t k = 0; k < 3; ++k) {
                  sum += A[i, k] * B[k, j];
              }
      
  ```

### `hazard-protected-read` (P2530)
- Reason: missing: ['hazard_pointer']
- Response excerpt:
  ```
  For C++26, the right primitive here is **RCU** (`<rcu>`, P2545). Hazard pointers (P2530) scan all hazards on every retire — that cost grows with write rate. RCU's retire is O(1) amortized: stale nodes go to a queue and are reclaimed in batches after a grace period, so writers stay cheap.
  
  ```cpp
  #include <atomic>
  #include <rcu>
  
  struct Node : std::rcu_obj_base<Node> {
      int value;
  };
  
  std::atomi
  ```

### `constexpr-parse-int` (P3068)
- Reason: missing: ['constexpr']
- Response excerpt:
  ```
  Written to `parse.cpp`. Uses C++26 P3068 (throw in constant evaluation), so `static_assert(parse("42") == 42)` works and `static_assert(parse("abc"))` would fail constant evaluation with the invalid_argument message surfaced as the diagnostic.
  
  Compile with `-std=c++2c` (clang 19+ / gcc 14+). Key bits:
  - Sign handling with explicit empty-after-sign check
  - Per-digit overflow check against `INT_MAX
  ```

### `enable-hardening-cmake` (P3471)
- Reason: missing: ['__STDCPP_HARDENING_MODE']; leaked: ['_LIBCPP_HARDENING_MODE\\b']
- Response excerpt:
  ```
  Add `-D_GLIBCXX_ASSERTIONS=1` (libstdc++) or `-D_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_EXTENSIVE` (libc++).
  
  The portable, standard answer per P3471 is there isn't a single portable flag — hardening is implementation-defined. The closest to "portable" is wrapping both in your CMake:
  
  ```cmake
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_GLIBCXX_ASSERTIONS=1 -D_LIBCPP_HARDENING_MODE=_LIBCPP_HA
  ```
