"""Skill garden CLI composition. AuthorityEffect: None."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from omega_engine_operads.infrastructure.skill_garden.archive_lane import (
    ArchiveRefusal,
    archive_skills,
    restore_skills,
    verify_archive,
)
from omega_engine_operads.infrastructure.skill_garden.usage_ledger import (
    repo_root_from,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Archive or restore a skill package.")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("plan", "archive"):
        node = sub.add_parser(name)
        node.add_argument("--repo-root", default=None)
        node.add_argument("--skill-id", action="append", default=[])
        node.add_argument(
            "--manifest",
            default=(
                "omega_engine_product_planning_office/"
                "_project_anomalon_codename_woland/planned_archive.md"
            ),
        )
        if name == "archive":
            node.add_argument("--apply", action="store_true")

    restore = sub.add_parser("restore")
    restore.add_argument("--repo-root", default=None)
    restore.add_argument("--skill-id", action="append", required=True)
    restore.add_argument("--apply", action="store_true")

    verify = sub.add_parser("verify")
    verify.add_argument("--repo-root", default=None)

    args = parser.parse_args(list(argv) if argv is not None else None)
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()

    try:
        if args.command == "verify":
            findings = verify_archive(root)
            for finding in findings:
                print(f"  [ARCHIVE_DRIFT] {finding}")
            print("PASS" if not findings else f"REFUSED: {len(findings)} finding(s)")
            return 1 if findings else 0

        if args.command == "restore":
            result = restore_skills(root, args.skill_id, apply=args.apply)
        else:
            result = archive_skills(
                root,
                args.skill_id,
                manifest_path=root / args.manifest,
                apply=getattr(args, "apply", False),
            )
    except ArchiveRefusal as refusal:
        print(f"REFUSED: {refusal}")
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=True, default=str))
    if result.get("applied") and not result.get("parity_green", True):
        print()
        print("REFUSED to report success: four-host parity is not green after the move.")
        return 1
    print()
    print("AuthorityEffect: None.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
