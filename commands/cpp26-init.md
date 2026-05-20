---
name: cpp26-init
description: |
  Scaffold a C++26-ready project in the current directory. Creates (or
  upgrades) CMakeLists.txt to CXX_STANDARD 26 with compile_commands
  export, writes a .clangd that points at the user-preferred toolchain,
  and writes a .cpp26-adapter.yaml the plugin reads for per-project
  overrides (skip-skill flag, custom anti-pattern allow-list).
---

# /cpp26-init — scaffold a C++26 project

Run this once per project to wire up the toolchain expectations the
cpp26-adapter plugin assumes. The command is **idempotent**: re-running
on a configured project diffs against the desired state and only writes
files that are missing or out-of-date. Existing user content is never
clobbered without a backup.

## What this does

1. **Detect the project root.** Walk up from the current directory
   looking for `.git`, `CMakeLists.txt`, or `package.json`. If none
   exists, use the current directory.

2. **CMakeLists.txt** — if missing, scaffold a minimal C++26 project:

   ```cmake
   cmake_minimum_required(VERSION 3.28)
   project(my_project LANGUAGES CXX)

   set(CMAKE_CXX_STANDARD 26)
   set(CMAKE_CXX_STANDARD_REQUIRED ON)
   set(CMAKE_CXX_EXTENSIONS OFF)
   set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

   # Pin -std=c++2c so build is portable even when compilers don't
   # recognize CXX_STANDARD 26 yet.
   add_compile_options(-std=c++2c)

   add_executable(my_project main.cpp)
   ```

   If `CMakeLists.txt` already exists:
   - Check for `set(CMAKE_CXX_STANDARD 26)` (or equivalent). If missing
     or set lower, emit a suggested patch but do **not** apply it
     without consent.
   - Check for `CMAKE_EXPORT_COMPILE_COMMANDS`. If missing, suggest
     adding it (clangd-driven editing depends on this).

3. **.clangd** — if missing, scaffold:

   ```yaml
   CompileFlags:
     Add:
       - "-std=c++2c"
       - "-Wno-unknown-pragmas"  # quiet pragmas the user has opted into
     # If the user has clang-p2996 installed elsewhere:
     # CompilerPath: /opt/clang-p2996/bin/clang++

   Diagnostics:
     UnusedIncludes: Strict
     MissingIncludes: Strict
     ClangTidy:
       Add: [modernize-*, performance-*]
       Remove: [modernize-use-trailing-return-type]
   ```

4. **.cpp26-adapter.yaml** — write a default that opts the project
   into the plugin's defaults:

   ```yaml
   # cpp26-adapter project overrides.
   #   Set skip-skill: true to disable the cpp26-idioms skill for
   #   legacy modules that should remain pre-C++26 idiomatic.
   #   Add anti-pattern ids to allow-list to silence specific
   #   PostToolUse findings.
   skip-skill: false
   allow-list: []
   # Optional: override the compiler the reviewer uses on this project.
   # compiler: clang-p2996
   ```

5. **README.md** — if a README exists, append a "## Toolchain
   expectations" section noting:

   ```markdown
   ## Toolchain expectations

   This project targets C++26 (ISO/IEC 14882:2026). Recommended
   compilers: clang >= 22, gcc >= 16, MSVC >= 19.40. For reflection
   (P2996) demos before clang 22 ships, use the
   [bloomberg/clang-p2996](https://github.com/bloomberg/clang-p2996)
   fork.
   ```

   If no README exists, do **not** create one — the user may not want
   one yet.

6. **main.cpp** — if the project has no C++ source at all, scaffold
   a minimal hello-world that demonstrates the toolchain works:

   ```cpp
   #include <print>

   int main() {
       std::print("hello, C++26\n");
       return 0;
   }
   ```

## Required reasoning before writing

- Read the existing CMakeLists.txt (if any) end-to-end before
  suggesting edits. Note any `add_subdirectory` calls — those
  subdirectories may have their own standard version that the user
  intentionally left lower.
- Detect whether the project is an *executable* vs a *library*
  scaffold. Libraries should use `add_library` and set the standard
  via `target_compile_features(<tgt> PUBLIC cxx_std_26)` so consumers
  inherit it.
- If the project is non-trivial (>10 source files), do not auto-touch
  any of them. Limit edits to the root config files.

## Output to the user

After scaffolding (or proposing edits), print a short summary:

```
Wrote: CMakeLists.txt, .clangd, .cpp26-adapter.yaml
Suggested but not applied: README "Toolchain expectations" section
Next: `cmake -B build && cmake --build build`
```

If any file was *suggested* rather than written (because it conflicts
with existing user content), list the proposed diff and the file path
and let the user accept or reject manually.

## Pitfalls to avoid

- Do not assume the user wants `-Werror`. Some projects rely on
  warnings firing without halting the build.
- Do not enable hardening via `-D__STDCPP_HARDENING_MODE` by default
  — that's a per-binary decision the user should make consciously.
- Do not create `.gitignore` entries. Leave version control hygiene
  to the user.
