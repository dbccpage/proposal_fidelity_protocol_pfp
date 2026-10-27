"""Skill garden CLI composition. AuthorityEffect: None."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from operads.infrastructure.skill_garden.usage_ledger import (
    repo_root_from,
    summarize,
)


def main(argv: Sequence[str] | None = None) -> int:

    parser = argparse.ArgumentParser(description="Summarise the skill usage ledger.")
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()

    report = summarize(root)
    print("=== SKILL USAGE LEDGER ===")
    print(f"roster      : {report['roster']}")
    print(f"seen        : {report['seen']}")
    print(f"never seen  : {report['never_seen']}")
    print(f"span        : {report['span_start']} -> {report['span_end']}")
    print(f"span (days) : {report['span_days']:.1f}")
    print()
    for skill in report["seen_skills"]:
        print(f"  {skill}")
    print()
    print(
        "Invocation is not use, and this sees one host. Absence of a record is "
        "not evidence of absence of use. AuthorityEffect: None."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
