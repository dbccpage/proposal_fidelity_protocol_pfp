"""Skill garden CLI composition. AuthorityEffect: None."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from omega_engine_operads.infrastructure.skill_garden.skill_memory import (
    INVOCATION_FLOOR,
    record_cohort,
    select,
)
from omega_engine_operads.infrastructure.skill_garden.usage_ledger import (
    repo_root_from,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Select skills for bounded memory.")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--floor", type=int, default=INVOCATION_FLOOR)
    parser.add_argument(
        "--record-cohort",
        action="store_true",
        help="freeze the granted/control sets for later comparison",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()

    selection = select(root, floor=args.floor)
    print("=== SKILL MEMORY SELECTION ===")
    print(f"ledger span (days) : {selection.span_days:.1f}")
    print(f"skills ever invoked: {len(selection.counts)}")
    print(f"invocation floor   : {args.floor}")
    print()
    for name, count in sorted(selection.counts.items(), key=lambda i: (-i[1], i[0])):
        print(f"  {name:<40} {count}")
    print()
    if selection.refused:
        print("REFUSED, and no skill is granted memory:")
        for reason in selection.refusals:
            print(f"  - {reason}")
        print()
        print("AuthorityEffect: None.")
        return 1

    print(f"granted: {list(selection.granted)}")
    print(f"control: {list(selection.control)}")
    if args.record_cohort:
        print(f"cohort recorded at {record_cohort(root, selection)}")
    print()
    print("AuthorityEffect: None.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
