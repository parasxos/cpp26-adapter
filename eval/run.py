#!/usr/bin/env python3
"""Eval harness for cpp26-adapter (Phase 7b).

For each task in eval/tasks.yaml, invokes `claude -p` twice — once with
the plugin (--plugin-dir <repo>) and once without — and scores the two
outputs against three axes:

  1. Standard compliance (binary): regex must_contain/must_not_contain.
  2. Syntactic correctness  (binary): extract fenced ```cpp``` blocks
     and run `clang -std=c++2c -fsyntax-only`. SKIPped when the local
     compiler is below the baseline (Apple clang on this dev box).
  3. Idiomatic quality      (1-5):    a second `claude -p` call asks
     an LLM judge to rate the output 1-5 against a fixed rubric.
     Optional (--skip-judge).

The DoD bar is **axis-1 ≥ 85%** on the held suite. Axis 2 is
informational below baseline; axis 3 measures direction of improvement.

Run:
    eval/run.py                                 # full 39-task suite
    eval/run.py --tasks 3                       # smoke (first 3 tasks)
    eval/run.py --only enum-to-string           # one named task
    eval/run.py --skip-syntax                   # drop axis 2
    eval/run.py --skip-judge                    # drop axis 3 (saves tokens)
    eval/run.py --no-off                        # don't run baseline (just plugin-on)
    eval/run.py --out eval/results-smoke.md     # custom output path

Tokens:
  Each task uses ~2 `claude -p` calls (off + on) plus 1 judge call
  unless --skip-judge. Budget ~$0.05-$0.20 per call depending on
  response length. For the full 39-task suite, budget ~$15-25.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# When both an API key and an OAuth subscription credential exist, the
# Claude CLI prefers the API key — which bills per-token. For an eval
# loop we want the subscription path (keychain OAuth) instead, so we
# strip these env vars before invoking `claude -p`. Override with
# CPP26_EVAL_USE_API=1 to opt back into API billing.
_API_AUTH_ENVS = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    if os.environ.get("CPP26_EVAL_USE_API") == "1":
        return env
    for k in _API_AUTH_ENVS:
        env.pop(k, None)
    return env

ROOT = Path(__file__).resolve().parent.parent
TASKS_PATH = ROOT / "eval" / "tasks.yaml"

JUDGE_PROMPT = """You are an expert C++ reviewer scoring how idiomatic a code response is for C++26 (ISO/IEC 14882:2026).

TASK GIVEN TO THE MODEL:
{task}

MODEL RESPONSE:
{response}

Score the response 1-5 against this rubric:
  1 = uses pre-C++26 anti-pattern primarily (X-macros, magic_enum, std::async, BOOST_DESCRIBE, etc.)
  2 = mixes pre-C++26 with modern; reaches for old idioms first
  3 = uses some C++26 features but misses the obvious headline form
  4 = uses the right C++26 idiom with minor flaws
  5 = perfectly idiomatic C++26, matches the canonical paper example

Reply with ONLY a single integer 1-5. No explanation."""


@dataclass
class AxisResult:
    pass_: bool = False
    detail: str = ""
    score: float = 0.0  # for axis 3 (1-5)


@dataclass
class TaskResult:
    task_id: str
    rule_tested: str
    category: str
    off_response: str = ""
    on_response: str = ""
    off_axis1: AxisResult = field(default_factory=AxisResult)
    on_axis1: AxisResult = field(default_factory=AxisResult)
    off_axis2: AxisResult = field(default_factory=AxisResult)
    on_axis2: AxisResult = field(default_factory=AxisResult)
    off_axis3: AxisResult = field(default_factory=AxisResult)
    on_axis3: AxisResult = field(default_factory=AxisResult)
    elapsed_s: float = 0.0


def call_claude(prompt: str, plugin_dir: Path | None, timeout: int = 300) -> tuple[str, int]:
    cmd: list[str] = ["claude", "-p", "--output-format", "text"]
    if plugin_dir is not None:
        cmd += ["--plugin-dir", str(plugin_dir)]
    cmd += [prompt]
    with tempfile.TemporaryDirectory() as cwd:
        try:
            r = subprocess.run(
                cmd, cwd=cwd, env=_subprocess_env(),
                capture_output=True, text=True, timeout=timeout,
            )
            return r.stdout, r.returncode
        except subprocess.TimeoutExpired:
            return "<timeout>", 124


# ---- axis 1: standard compliance ----------------------------------------------

def axis1(task: dict[str, Any], response: str) -> AxisResult:
    must_contain = task.get("must_contain") or []
    must_not = task.get("must_not_contain") or []
    miss = [p for p in must_contain if not re.search(p, response, re.IGNORECASE | re.DOTALL)]
    leak = [p for p in must_not    if     re.search(p, response, re.IGNORECASE | re.DOTALL)]
    if not miss and not leak:
        return AxisResult(pass_=True, detail="all gates met")
    detail = []
    if miss:
        detail.append(f"missing: {miss}")
    if leak:
        detail.append(f"leaked: {leak}")
    return AxisResult(pass_=False, detail="; ".join(detail))


# ---- axis 2: syntactic correctness --------------------------------------------

CPP_BLOCK_RE = re.compile(r"```(?:cpp|c\+\+)?\n(.*?)\n```", re.DOTALL)


def axis2(response: str, clang: str | None, baseline_ok: bool) -> AxisResult:
    if clang is None or not baseline_ok:
        return AxisResult(pass_=True, detail="skipped (no clang ≥ 22 baseline)")
    blocks = CPP_BLOCK_RE.findall(response)
    if not blocks:
        return AxisResult(pass_=True, detail="no cpp blocks to check")
    failures = 0
    for block in blocks:
        with tempfile.NamedTemporaryFile(suffix=".cpp", mode="w", delete=False) as tf:
            tf.write(block)
            path = Path(tf.name)
        try:
            r = subprocess.run(
                [clang, "-std=c++2c", "-fsyntax-only", "-Wno-everything", str(path)],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode != 0:
                failures += 1
        finally:
            path.unlink(missing_ok=True)
    if failures == 0:
        return AxisResult(pass_=True, detail=f"{len(blocks)}/{len(blocks)} blocks parse")
    return AxisResult(pass_=False, detail=f"{failures}/{len(blocks)} blocks fail to parse")


def _probe_baseline(clang: str | None) -> bool:
    if clang is None:
        return False
    try:
        out = subprocess.run([clang, "--version"], capture_output=True, text=True).stdout
    except OSError:
        return False
    if "Apple" in out:
        return False
    m = re.search(r"version (\d+)", out)
    if not m:
        return False
    return int(m.group(1)) >= 22


# ---- axis 3: LLM-judge --------------------------------------------------------

def axis3(task_prompt: str, response: str, plugin_dir: Path | None) -> AxisResult:
    judge_prompt = JUDGE_PROMPT.format(task=task_prompt, response=response)
    out, _rc = call_claude(judge_prompt, plugin_dir=None, timeout=120)
    m = re.search(r"\b([1-5])\b", out.strip())
    if not m:
        return AxisResult(pass_=False, detail=f"judge response not parseable: {out[:80]!r}", score=0)
    score = float(m.group(1))
    return AxisResult(pass_=(score >= 4), detail=f"judge={int(score)}/5", score=score)


# ---- runner -------------------------------------------------------------------

def run_task(
    task: dict[str, Any], plugin_dir: Path,
    clang: str | None, baseline_ok: bool,
    skip_syntax: bool, skip_judge: bool, skip_off: bool,
) -> TaskResult:
    t0 = time.perf_counter()
    res = TaskResult(task_id=task["id"], rule_tested=task["rule_tested"], category=task["category"])
    prompt = task["prompt"]

    if not skip_off:
        res.off_response, _ = call_claude(prompt, plugin_dir=None)
        res.off_axis1 = axis1(task, res.off_response)
        res.off_axis2 = (AxisResult(pass_=True, detail="skipped") if skip_syntax
                        else axis2(res.off_response, clang, baseline_ok))
        res.off_axis3 = (AxisResult(pass_=True, detail="skipped") if skip_judge
                        else axis3(prompt, res.off_response, plugin_dir))

    res.on_response, _ = call_claude(prompt, plugin_dir=plugin_dir)
    res.on_axis1 = axis1(task, res.on_response)
    res.on_axis2 = (AxisResult(pass_=True, detail="skipped") if skip_syntax
                    else axis2(res.on_response, clang, baseline_ok))
    res.on_axis3 = (AxisResult(pass_=True, detail="skipped") if skip_judge
                    else axis3(prompt, res.on_response, plugin_dir))

    res.elapsed_s = time.perf_counter() - t0
    return res


def render_report(results: list[TaskResult], skip_off: bool, version: str) -> str:
    total = len(results)
    on_axis1 = sum(1 for r in results if r.on_axis1.pass_)
    off_axis1 = sum(1 for r in results if r.off_axis1.pass_)
    on_axis2 = sum(1 for r in results if r.on_axis2.pass_)
    on_judge_scores = [r.on_axis3.score for r in results if r.on_axis3.score > 0]
    off_judge_scores = [r.off_axis3.score for r in results if r.off_axis3.score > 0]

    on_pct = 100 * on_axis1 / total if total else 0
    off_pct = 100 * off_axis1 / total if total else 0
    on_judge_median = sorted(on_judge_scores)[len(on_judge_scores)//2] if on_judge_scores else 0
    off_judge_median = sorted(off_judge_scores)[len(off_judge_scores)//2] if off_judge_scores else 0

    lines: list[str] = []
    lines.append(f"# Eval results — cpp26-adapter {version}")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    lines.append(f"Tasks: {total}")
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append("| Axis | Plugin ON | Plugin OFF | Δ |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| 1 — Standard compliance | {on_axis1}/{total} ({on_pct:.0f}%) "
                 f"| {off_axis1}/{total} ({off_pct:.0f}%) | {on_pct - off_pct:+.0f}pp |")
    if not all(r.on_axis2.detail.startswith("skipped") for r in results):
        lines.append(f"| 2 — Syntactic correctness | {on_axis2}/{total} | — | — |")
    if on_judge_scores:
        lines.append(f"| 3 — Idiomatic quality (judge) | median {on_judge_median:.0f}/5 "
                     f"| median {off_judge_median:.0f}/5 | — |")
    lines.append("")
    lines.append(f"**DoD axis-1 bar: ≥85%** — {'MET ✓' if on_pct >= 85 else f'NOT MET ({on_pct:.0f}%)'}")
    lines.append("")
    lines.append("## Per-task")
    lines.append("")
    lines.append("| Task | Paper | Plugin OFF | Plugin ON |")
    lines.append("|---|---|---|---|")
    for r in results:
        off = "—" if skip_off else ("✓" if r.off_axis1.pass_ else "✗")
        on  = "✓" if r.on_axis1.pass_ else "✗"
        lines.append(f"| `{r.task_id}` | {r.rule_tested} | {off} | {on} |")
    lines.append("")
    lines.append("## Failures (Plugin ON, axis 1)")
    lines.append("")
    for r in results:
        if not r.on_axis1.pass_:
            lines.append(f"### `{r.task_id}` ({r.rule_tested})")
            lines.append(f"- Reason: {r.on_axis1.detail}")
            lines.append("- Response excerpt:")
            lines.append("  ```")
            lines.append("  " + r.on_response[:400].replace("\n", "\n  "))
            lines.append("  ```")
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=int, default=0, help="run first N tasks only")
    parser.add_argument("--only", help="comma-separated task ids to run")
    parser.add_argument("--skip-syntax", action="store_true", help="drop axis 2")
    parser.add_argument("--skip-judge", action="store_true", help="drop axis 3 (saves tokens)")
    parser.add_argument("--no-off", action="store_true", help="skip baseline (plugin-off) runs")
    parser.add_argument("--out", default="", help="output path (default eval/results-vX.Y.md)")
    args = parser.parse_args()

    tasks_all = yaml.safe_load(TASKS_PATH.read_text())
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        tasks = [t for t in tasks_all if t["id"] in wanted]
    else:
        tasks = tasks_all[: args.tasks] if args.tasks else tasks_all
    print(f"running {len(tasks)} tasks (of {len(tasks_all)} in suite)", file=sys.stderr)

    clang = shutil.which("clang") or shutil.which("clang++")
    baseline_ok = _probe_baseline(clang)
    print(f"clang={clang or '<none>'}  baseline_ok={baseline_ok}", file=sys.stderr)

    plugin_version = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())["version"]
    results: list[TaskResult] = []
    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] {task['id']} ({task['rule_tested']}) …", file=sys.stderr)
        try:
            r = run_task(
                task, plugin_dir=ROOT, clang=clang, baseline_ok=baseline_ok,
                skip_syntax=args.skip_syntax, skip_judge=args.skip_judge, skip_off=args.no_off,
            )
        except KeyboardInterrupt:
            print("\ninterrupted; writing partial report", file=sys.stderr)
            break
        results.append(r)
        on_mark = "✓" if r.on_axis1.pass_ else "✗"
        off_mark = "—" if args.no_off else ("✓" if r.off_axis1.pass_ else "✗")
        print(f"    off={off_mark} on={on_mark}  ({r.elapsed_s:.1f}s)", file=sys.stderr)

    out_path = Path(args.out) if args.out else (ROOT / "eval" / f"results-v{plugin_version}.md")
    out_path.write_text(render_report(results, args.no_off, plugin_version))
    print(f"\nwrote {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
