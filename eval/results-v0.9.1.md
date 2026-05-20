# Eval results — cpp26-adapter 0.9.1

Generated: 2026-05-20T20:49:08+00:00
Tasks: 39

## Aggregate

| Axis | Plugin ON | Plugin OFF | Δ |
|---|---:|---:|---:|
| 1 — Standard compliance | 35/39 (90%) | 0/39 (0%) | +90pp |

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
| `tuple-sum` | P1306 | — | ✓ |
| `visit-every-pack-element` | P1306 | — | ✗ |
| `nth-pack-element` | P2662 | — | ✓ |
| `type-pack-index` | P2662 | — | ✓ |
| `delete-with-reason` | P2573 | — | ✓ |
| `variadic-friend-plugins` | P2893 | — | ✓ |
| `embed-binary-asset` | P1967 | — | ✓ |
| `conditional-embed` | P1967 | — | ✓ |
| `safe-uninit-read` | P2795 | — | ✗ |
| `matrix-multiply` | P1673 | — | ✓ |
| `axpy` | P1673 | — | ✗ |
| `hazard-protected-read` | P2530 | — | ✓ |
| `rcu-snapshot` | P2545 | — | ✓ |
| `enable-hardening` | P3471 | — | ✗ |
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
| `enable-hardening-cmake` | P3471 | — | ✓ |
| `portable-bytes-include` | P1967 | — | ✓ |
| `reflection-vs-magic-enum` | P2996 | — | ✓ |

## Failures (Plugin ON, axis 1)

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
  
  Uses a C++17 fold expression over the comma operator to invoke `f` on each pack element in order.
  
  ```

### `safe-uninit-read` (P2795)
- Reason: leaked: ['\\[\\[indeterminate\\]\\]']
- Response excerpt:
  ```
  ```cpp
  int total{};  // value-initialized to 0 — safe to read immediately
  ```
  
  Under C++26 (P2795), a bare `int total;` no longer triggers UB on read — it holds an *erroneous value* that the implementation is encouraged to fill with a fixed pattern, and reading it is diagnosable erroneous behaviour. That's safer than C++23, but it is still wrong for an accumulator, because the first `total += x` r
  ```

### `axpy` (P1673)
- Reason: missing: ['std::linalg', 'scaled|add']
- Response excerpt:
  ```
  ```cpp
  #include <algorithm>
  #include <execution>
  #include <span>
  
  void axpy(float alpha, std::span<const float> x, std::span<float> y) {
      std::transform(std::execution::par_unseq,
                     x.begin(), x.end(), y.begin(), y.begin(),
                     [alpha](float xi, float yi) { return alpha * xi + yi; });
  }
  ```
  
  Pass-by-`std::span` decouples the call from container type (works with `
  ```

### `enable-hardening` (P3471)
- Reason: leaked: ['_LIBCPP_HARDENING_MODE']
- Response excerpt:
  ```
  In C++26, library hardening is controlled by the standard macro **`__STDCPP_HARDENING_MODE__`** (P3471) together with the implementation-defined opt-in macro you set at build time. The portable, standard way to *request* hardening is to define the implementation's hardening macro before including any standard header, then verify the mode via `__STDCPP_HARDENING_MODE__`.
  
  ```cpp
  // Request "fast" h
  ```
