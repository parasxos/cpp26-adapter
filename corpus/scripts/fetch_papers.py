#!/usr/bin/env python3
"""Fetch raw WG21 paper content (HTML or PDF) into corpus/raw/.

For each paper in `corpus/index.yaml`, resolve `wg21.link/<id><revision>`
and cache the body under `corpus/raw/<id><revision>.{html,pdf,bs}`. The
extension is chosen from the response Content-Type. Reruns skip files
that already exist, so this is safe to re-execute.

Failures are written to `corpus/raw/fetch_log.json` with the HTTP status,
final URL, and error string. The script exits 0 even on per-paper
failures; check the log to retry.

Run:
    mcp-server/.venv/bin/python corpus/scripts/fetch_papers.py
    # add --only P2996,P2900 to fetch a subset
    # add --force to re-download even if the file is cached
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "index.yaml"
RAW_DIR = ROOT / "raw"
LOG_PATH = RAW_DIR / "fetch_log.json"

USER_AGENT = (
    "cpp26-adapter/0.0.1 (https://github.com/parasxos/claude-plugins; "
    "fetch_papers.py; +parasxos@gmail.com)"
)
REQUEST_TIMEOUT = 30  # seconds
POLITE_DELAY = 0.4    # seconds between requests

CONTENT_TYPE_EXT = {
    "text/html":         "html",
    "application/xhtml": "html",
    "application/pdf":   "pdf",
    "text/plain":        "bs",  # Bikeshed source occasionally served as text/plain
}


def ext_for(content_type: str) -> str:
    base = content_type.split(";", 1)[0].strip().lower()
    return CONTENT_TYPE_EXT.get(base, "bin")


def fetch_one(paper_id: str, revision: str | None) -> tuple[str, int | None, str | None]:
    """Return (final_url, status, error_or_None)."""
    rev_suffix = revision or ""
    url = f"https://wg21.link/{paper_id}{rev_suffix}"
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html, application/pdf;q=0.9"})
    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            body = resp.read()
            ext = ext_for(resp.headers.get("Content-Type", ""))
            target = RAW_DIR / f"{paper_id}{rev_suffix}.{ext}"
            target.write_bytes(body)
            return resp.geturl(), resp.status, None
    except HTTPError as e:
        return getattr(e, "url", url), e.code, f"HTTPError {e.code}: {e.reason}"
    except URLError as e:
        return url, None, f"URLError: {e.reason}"
    except TimeoutError:
        return url, None, "timeout"
    except OSError as e:
        return url, None, f"OSError: {e}"


def already_cached(paper_id: str, revision: str | None) -> Path | None:
    rev_suffix = revision or ""
    for ext in ("html", "pdf", "bs"):
        p = RAW_DIR / f"{paper_id}{rev_suffix}.{ext}"
        if p.exists() and p.stat().st_size > 0:
            return p
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Comma-separated paper ids to fetch (e.g. P2996,P2900)")
    parser.add_argument("--force", action="store_true", help="Re-download even if cached")
    parser.add_argument("--limit", type=int, default=0, help="Stop after N papers (0 = all)")
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        print(f"error: {INDEX_PATH} not found; run fetch_index.py first", file=sys.stderr)
        return 1

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rows = yaml.safe_load(INDEX_PATH.read_text())

    only_set: set[str] | None = None
    if args.only:
        only_set = {x.strip() for x in args.only.split(",") if x.strip()}

    targets = [r for r in rows if (only_set is None or r["id"] in only_set)]
    if args.limit:
        targets = targets[: args.limit]
    print(f"target papers: {len(targets)}", file=sys.stderr)

    succeeded: list[dict] = []
    failed: list[dict] = []
    cached_count = 0

    for i, row in enumerate(targets, 1):
        pid = row["id"]
        rev = row.get("revision")
        if not args.force:
            cached = already_cached(pid, rev)
            if cached is not None:
                cached_count += 1
                continue
        if i % 25 == 1:
            print(f"  [{i}/{len(targets)}] fetching {pid}{rev or ''}…", file=sys.stderr)
        final_url, status, err = fetch_one(pid, rev)
        record = {
            "id": pid,
            "revision": rev,
            "url": final_url,
            "status": status,
            "error": err,
        }
        if err is None:
            succeeded.append(record)
        else:
            failed.append(record)
            print(f"  ✗ {pid}{rev or ''}: {err}", file=sys.stderr)
        time.sleep(POLITE_DELAY)

    log = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total_targets": len(targets),
        "cached": cached_count,
        "succeeded": len(succeeded),
        "failed": len(failed),
        "failures": failed,
    }
    LOG_PATH.write_text(json.dumps(log, indent=2))

    total_obtained = cached_count + len(succeeded)
    pct = 100 * total_obtained / max(len(targets), 1)
    print(
        f"\nresult: cached={cached_count} new={len(succeeded)} failed={len(failed)} "
        f"→ {total_obtained}/{len(targets)} ({pct:.1f}%)",
        file=sys.stderr,
    )
    print(f"log: {LOG_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
