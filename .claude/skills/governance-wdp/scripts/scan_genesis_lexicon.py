#!/usr/bin/env python3
"""Lexical candidate scan for Genesis-Bias / observer-from-nowhere routes.

AuthorityEffect: None. Hits are candidates, not verdicts.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# (severity, pattern, tag)
RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("HIGH", re.compile(r"\bview from nowhere\b", re.I), "OFN"),
    ("HIGH", re.compile(r"\bfrom nowhere\b", re.I), "OFN"),
    ("HIGH", re.compile(r"\bgod'?s[- ]eye\b", re.I), "OFN"),
    ("HIGH", re.compile(r"\bfor all observers\b", re.I), "OFN"),
    ("HIGH", re.compile(r"\bindependent of any (carrier|observer|packet)\b", re.I), "OFN"),
    ("HIGH", re.compile(r"\bthe world offers\b", re.I), "OFN"),
    ("HIGH", re.compile(r"\ball (possible )?cuts\b", re.I), "OFN"),
    ("HIGH", re.compile(r"\ball possible re-?cuts\b", re.I), "OFN"),
    ("MEDIUM", re.compile(r"\bthe observer\b", re.I), "OFN"),
    ("MEDIUM", re.compile(r"\bwe observe\b", re.I), "OFN"),
    ("MEDIUM", re.compile(r"\bobjectively\b", re.I), "OFN"),
    ("MEDIUM", re.compile(r"\bfrom outside\b", re.I), "OFN"),
    ("HIGH", re.compile(r"\bcreates its own carrier\b", re.I), "PRIMDIFF"),
    ("HIGH", re.compile(r"\bfloat in nothing\b", re.I), "PRIMDIFF"),
    ("MEDIUM", re.compile(r"\bcapacity to (exhibit|host|contain)\b", re.I), "PRIMDIFF"),
    ("MEDIUM", re.compile(r"\bantecedent (domain|host|container|substrate)\b", re.I), "HOST"),
    ("MEDIUM", re.compile(r"\bstate[- ]space\b", re.I), "HOST"),
    ("MEDIUM", re.compile(r"\bsubstrate\b", re.I), "HOST"),
    ("LOW", re.compile(r"\b(creates|produces|generates|emerges|arises)\b", re.I), "HOST"),
    ("LOW", re.compile(r"\b(background|fundamental|hosts|contains)\b", re.I), "HOST"),
    ("LOW", re.compile(r"\b(always|whenever|eventually)\b", re.I), "TIME"),
    ("LOW", re.compile(r"\b(before|after|then|next)\b", re.I), "TIME"),
]

TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".lean", ".py", ".tex", ".bib"}
SKIP_DIR = {
    ".git",
    "node_modules",
    "__pycache__",
    ".lake",
    "target",
    "dist",
    "build",
}


def iter_files(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_file():
            if p.suffix.lower() in TEXT_SUFFIXES:
                out.append(p)
            continue
        if not p.is_dir():
            continue
        for f in p.rglob("*"):
            if not f.is_file():
                continue
            if any(part in SKIP_DIR for part in f.parts):
                continue
            if f.suffix.lower() in TEXT_SUFFIXES:
                out.append(f)
    return sorted(set(out))


def scan_file(path: Path) -> list[tuple[int, str, str, str, str]]:
    """Return list of (line_no, severity, tag, match, line)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"WARN cannot read {path}: {e}", file=sys.stderr)
        return []
    hits: list[tuple[int, str, str, str, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        for sev, pat, tag in RULES:
            m = pat.search(line)
            if m:
                hits.append((i, sev, tag, m.group(0), line.strip()[:160]))
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path, help="files or directories")
    ap.add_argument(
        "--min-severity",
        choices=["LOW", "MEDIUM", "HIGH"],
        default="LOW",
        help="minimum severity to print (default LOW)",
    )
    args = ap.parse_args(argv)
    order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    min_s = order[args.min_severity]

    files = iter_files(args.paths)
    if not files:
        print("No text files found.", file=sys.stderr)
        return 2

    total = 0
    by_sev = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    # Public marker aligned with skill rename (candidates only; not a verdict).
    print("PRIMDIFF_OBSERVER_AUDIT: CANDIDATES_ONLY")
    print("AuthorityEffect: None")
    print(f"files: {len(files)}")
    print()
    for f in files:
        hits = scan_file(f)
        shown = [h for h in hits if order[h[1]] >= min_s]
        if not shown:
            continue
        print(f"## {f.as_posix()}")
        for ln, sev, tag, match, snippet in shown:
            by_sev[sev] += 1
            total += 1
            print(f"- L{ln} [{sev}/{tag}] `{match}` — {snippet}")
        print()
    print("## totals")
    print(f"hits={total} HIGH={by_sev['HIGH']} MEDIUM={by_sev['MEDIUM']} LOW={by_sev['LOW']}")
    print("Note: license, Import Ledger, OBSTRUCTION, or exposition may clear any hit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
