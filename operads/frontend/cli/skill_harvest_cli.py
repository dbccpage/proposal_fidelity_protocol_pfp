"""Skill garden CLI composition. AuthorityEffect: None."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from operads.infrastructure.skill_garden.transcript_harvester import (
    harvest,
)
from operads.infrastructure.skill_garden.usage_ledger import (
    repo_root_from,
    summarize,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Harvest skill invocations from Claude Code transcripts."
    )
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--home", default=None, help="override ~ (for tests)")
    parser.add_argument("--since", default=None, help="YYYY-MM-DD lower bound")
    parser.add_argument(
        "--apply", action="store_true", help="write to the ledger (default: dry run)"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    home = Path(args.home).resolve() if args.home else None
    report = harvest(root, home=home, since=args.since, apply=args.apply)

    print("=== TRANSCRIPT HARVEST %s ===" % ("(applied)" if args.apply else "(dry run)"))
    print(f"project dirs        : {report['project_dirs']}")
    print(f"transcripts read    : {report['transcripts']}")
    print(f"invocations matched : {report['invocations_found']}")
    if args.apply:
        print(f"written             : {report.get('written')}")
        print(f"already on file     : {report.get('skipped')}")
    if report["unmatched"]:
        print()
        print("names recorded that are not garden packages:")
        for name, count in list(report["unmatched"].items())[:20]:
            print(f"  {count:4d}  {name}")
        print(
            "  (plugin and built-in skills, plus packages renamed away -- those "
            "calls failed when they were made)"
        )
    if args.apply:
        print()
        summary = summarize(root)
        print(
            "ledger: %d of %d packages seen, span %.1f days"
            % (summary["seen"], summary["roster"], summary["span_days"])
        )
    print()
    print("AuthorityEffect: None. Invocation is not use; this sees one host.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
