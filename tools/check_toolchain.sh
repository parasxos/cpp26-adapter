#!/usr/bin/env bash
# SessionStart probe for cpp26-adapter.
#
# Prints a short toolchain summary to stderr (so Claude surfaces it as
# session context). If neither clang nor gcc meets the C++26 baseline
# (clang>=22, gcc>=16, or msvc>=19.40) we emit an informational note
# pointing at the bloomberg/clang-p2996 fork for reflection demos.
#
# The probe never fails: missing compilers, unparseable version strings,
# and below-threshold versions are all reported informationally, never
# as a blocking error. The plugin's Constitution is compiler-agnostic
# by design.

set -u

CLANG_MIN=22
GCC_MIN=16
MSVC_MIN=19.40

emit() { printf '[cpp26-adapter] %s\n' "$*" >&2; }

# Helper: extract the leading major number from a "X.Y.Z" version string.
# Falls back to "unknown" if the input is empty or non-numeric.
major_of() {
    local v="${1:-}"
    [[ -z "$v" ]] && { printf 'unknown'; return; }
    printf '%s' "$v" | awk '{ split($0, a, /\./); print a[1] }'
}

probe_clang() {
    command -v clang >/dev/null 2>&1 || command -v clang++ >/dev/null 2>&1 || return 1
    # Apple's clang prints "Apple clang version X.Y.Z"; mainline prints
    # "clang version X.Y.Z". Both have the X.Y.Z token after "version ".
    local raw
    raw=$(clang --version 2>/dev/null | head -1)
    local v
    v=$(printf '%s' "$raw" | sed -E 's/.* version ([0-9]+(\.[0-9]+)*)([^0-9].*)?$/\1/')
    local major
    major=$(major_of "$v")
    printf '%s|%s|%s\n' "clang" "$major" "$raw"
}

probe_gcc() {
    command -v g++ >/dev/null 2>&1 || command -v gcc >/dev/null 2>&1 || return 1
    local raw
    raw=$(g++ --version 2>/dev/null | head -1)
    # On macOS, /usr/bin/g++ is a clang shim; skip if it reports "clang"
    # to avoid double-counting.
    if printf '%s' "$raw" | grep -qiE 'clang|apple'; then
        return 1
    fi
    local v
    v=$(printf '%s' "$raw" | sed -E 's/^[^0-9]*([0-9]+(\.[0-9]+)*).*/\1/')
    local major
    major=$(major_of "$v")
    printf '%s|%s|%s\n' "gcc" "$major" "$raw"
}

probe_msvc() {
    # Rarely on the same host as we're shipped, but check anyway.
    command -v cl.exe >/dev/null 2>&1 || return 1
    local raw
    raw=$(cl.exe 2>&1 | head -1)
    local v
    v=$(printf '%s' "$raw" | sed -E 's/.*Version ([0-9]+(\.[0-9]+)*).*/\1/')
    printf '%s|%s|%s\n' "msvc" "$v" "$raw"
}

emit "C++26 toolchain probe ($(date -u '+%Y-%m-%dT%H:%M:%SZ'))"

any_above_threshold=0
results=()

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    results+=("$line")
done < <( probe_clang; probe_gcc; probe_msvc; )

if [[ ${#results[@]} -eq 0 ]]; then
    emit "  no C++ compiler found on PATH (clang / g++ / cl.exe). Suggestions are still standard-first."
    exit 0
fi

for line in "${results[@]}"; do
    IFS='|' read -r kind major raw <<< "$line"
    case "$kind" in
        clang)
            if [[ "$major" =~ ^[0-9]+$ ]] && (( major >= CLANG_MIN )); then
                emit "  ✓ ${kind}: ${raw}  (>= ${CLANG_MIN}, expected to cover most of C++26)"
                any_above_threshold=1
            else
                emit "  ⚠ ${kind}: ${raw}  (below ${CLANG_MIN}; reflection/template-for require bloomberg/clang-p2996 fork)"
            fi
            ;;
        gcc)
            if [[ "$major" =~ ^[0-9]+$ ]] && (( major >= GCC_MIN )); then
                emit "  ✓ ${kind}: ${raw}  (>= ${GCC_MIN}, expected to cover most of C++26)"
                any_above_threshold=1
            else
                emit "  ⚠ ${kind}: ${raw}  (below ${GCC_MIN}; contracts/std::execution may not be implemented yet)"
            fi
            ;;
        msvc)
            emit "  ℹ ${kind}: ${raw}  (Visual Studio; cross-check with status.yaml when reviewing)"
            ;;
    esac
done

if (( any_above_threshold == 0 )); then
    emit "  Recommendations follow the C++26 standard regardless. Compile-time errors from older toolchains are informational, classified as compiler-lag by @cpp26-reviewer Pass 2."
fi

exit 0
