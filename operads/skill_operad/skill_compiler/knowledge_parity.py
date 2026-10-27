#!/usr/bin/env python3
"""Semantic knowledge-parity scan for CODA skill prose.

Six-host SHA parity can be perfect while all six hosts share obsolete law.
This gate flags stale four- or five-host doctrine in live SKILL.md files.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Patterns that must not appear as live doctrine in skill packages.
# Historical fences may mention them if the same file also marks them STALE/removed.
BANNED_LIVE = [
    (
        r"\bonly\s+(?:four|4)\s+(?:live\s+)?(?:hosts?|roots?)\b|\bfour[- ]host\b|\bHOST_SKILL_ROOTS\b[^\n]{0,80}\b(?:four|4)\b",
        "four-host doctrine omits tracked .antigravity and .gemini roots",
    ),
    (
        r"\bonly\s+(?:five|5)\s+(?:live\s+)?(?:hosts?|roots?)\b|\bfive[- ]host\b|\bHOST_SKILL_ROOTS\b[^\n]{0,80}\b(?:five|5)\b",
        "five-host doctrine omits one tracked CODA root",
    ),
]

# If these appear nearby, treat as historical fence (soft pass with note).
HISTORICAL_FENCE = re.compile(
    r"STALE_RULE|historical|former|superseded|not a live promotion|at last audit|workstation debris",
    re.I,
)


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / ".agents").is_dir():
            return candidate
    return Path.cwd().resolve()


def scan_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    hits: list[str] = []
    for pattern, label in BANNED_LIVE:
        for m in re.finditer(pattern, text, re.I):
            start = max(0, m.start() - 120)
            end = min(len(text), m.end() + 120)
            window = text[start:end]
            if HISTORICAL_FENCE.search(window):
                continue
            hits.append(f"{label} @ byte {m.start()}")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--skills-root",
        default="operads/skills",
        help="Relative skills root to scan",
    )
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    skills = root / args.skills_root
    if not skills.is_dir():
        print(f"ERROR: missing {skills}", file=sys.stderr)
        return 2

    bad = 0
    print("=== KNOWLEDGE PARITY (banned live doctrine) ===")
    for skill_md in sorted(skills.glob("*/SKILL.md")):
        hits = scan_file(skill_md)
        if hits:
            bad += 1
            rel = skill_md.relative_to(root)
            print(f"  [STALE] {rel}")
            for h in hits:
                print(f"           - {h}")
    if bad:
        print(f"\nFAIL: {bad} skill package(s) carry unfenced stale host doctrine.")
        return 1
    print("PASS: no unfenced four- or five-host doctrine in the six-root CODA garden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
