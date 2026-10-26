"""Skill garden CLI composition. AuthorityEffect: None."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from omega_engine_operads.frontend.presenters.skill_cull import render_manifest
from omega_engine_operads.infrastructure.skill_garden.cull_candidates import (
    compute_candidates,
    load_policy,
)
from omega_engine_operads.infrastructure.skill_garden.usage_ledger import (
    repo_root_from,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Propose skills for archival, refusing on suspicious shapes."
    )
    parser.add_argument("--repo-root", default=None)
    parser.add_argument(
        "--manifest",
        action="store_true",
        help="print the planned_archive.md manifest instead of the summary",
    )
    parser.add_argument(
        "--skip-parity", action="store_true", help="skip the four-host parity refusal"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    now = datetime.now(timezone.utc)
    policy = load_policy(root)
    report = compute_candidates(root, now=now, policy=policy, check_parity=not args.skip_parity)

    if args.manifest:
        print(render_manifest(report, now=now))
        return 1 if report.refused else 0

    print("=== CULL CANDIDATES ===")
    print(f"roster            : {report.roster_size}")
    print(f"ledger span (days): {report.span_days:.1f}")
    print(f"exempt            : {len(report.exempt)}")
    print(f"within grace      : {len(report.in_grace)}")
    print(f"used in window    : {len(report.used_recently)}")
    print(f"nominated         : {len(report.candidates)}")
    if report.refusals:
        print()
        print("REFUSED, and no candidates are emitted:")
        for reason in report.refusals:
            print(f"  - {reason}")
        print()
        print("AuthorityEffect: None.")
        return 1
    print()
    for row in report.candidates:
        print(f"  {row['skill_id']:<48} last used {row['last_used'] or 'never'}")
    print()
    print("Proposal only. AuthorityEffect: None.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
