#!/usr/bin/env python3
"""CLI Entrypoint: Intake OMC DAGs into the Adversary Swarm.

Parses Operad Morphism Calculus (OMC) and Red Team Red Team JSONL receipts,
routes and classifies them across the four canonical Engine domains:
  - DDC: Discrete Deformation Calculus
  - OEWAS: Engine Workflows, Agents & Skills
  - OEEIS: Engine Epistemic Immune System
  - OEPRMPTCIV: Prompt Civilization

Farms decisive blockers and failing gates for anti-skills/antibodies,
extracts surviving invariants for positive skills, and optionally seals
a canonical Adversary five-file run bundle under _ic/darpa/adversary/runs/.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from operating_system.adapters.intelligence_custody.ic_routing import intelligence_path
from operating_system.adapters.intelligence_custody.intelligence_root import (
    try_resolve_intelligence_repo_root,
)
from adversary.infrastructure.native import DefaultNativeOperationPort
from adversary.use_cases.omc_dag_intake import OmcDagIntakeService


def _find_default_repo_root() -> Path:
    res = try_resolve_intelligence_repo_root()
    if res.is_ok:
        return res.unwrap()
    cur = Path(__file__).resolve()
    for parent in [cur, *cur.parents]:
        if (parent / ".git").is_dir() or (parent / "_ic").is_dir():
            return parent
    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Intake OMC DAGs and farm obstructions for the Adversary Swarm."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Path to directory containing OMC DAG .jsonl files (default: _intelligence/omc_dags)",
    )
    parser.add_argument(
        "--domain",
        choices=["ALL", "DDC", "OEWAS", "OEEIS", "OEPRMPTCIV"],
        default="ALL",
        help="Filter findings by canonical domain (default: ALL)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional path to write full harvest JSON report",
    )
    parser.add_argument(
        "--persist-adversary-run",
        action="store_true",
        help="Persist a canonical Adversary five-file run bundle under _intelligence/_adversary/runs/",
    )
    parser.add_argument(
        "--task-key",
        default=None,
        help="Explicit task key for the persisted Adversary run bundle",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Optional root repository path (defaults to auto-detection)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed obstruction and skill breakdowns to stdout",
    )

    args = parser.parse_args(argv)
    repo_root = args.repo_root or _find_default_repo_root()

    input_dir = args.input_dir or (intelligence_path(repo_root, "_intelligence/omc_dags"))
    if not input_dir.is_dir():
        print(f"[-] Error: input directory not found: {input_dir}", file=sys.stderr)
        return 2

    service = OmcDagIntakeService(native_support=DefaultNativeOperationPort())
    harvest_res = service.intake_directory(input_dir)
    if harvest_res.is_err:
        refusal = harvest_res.unwrap_err()
        print(f"[-] Intake Refused ({refusal.code}): {refusal.message}", file=sys.stderr)
        return 2

    harvest = harvest_res.unwrap()

    # Apply domain filter if requested
    if args.domain != "ALL":
        harvest = service.filter_by_domain(harvest, args.domain)

    # Print summary banner
    print("=" * 78)
    print("  ADVERSARY INQUEST & OMC DAGs OBSTRUCTION FARMING APPARATUS")
    print("=" * 78)
    print(f"Input Directory  : {input_dir}")
    print(f"Domain Scope     : {args.domain}")
    print(f"Total Records    : {harvest.total_records}")
    print("Domain Breakdown :")
    for dom, count in harvest.records_by_domain.items():
        print(f"  - {dom:<12}: {count} records")
    print(f"Farmed Obstructions (Anti-Skills / Antibodies) : {len(harvest.obstructions)}")
    print(f"Surviving Invariants (Skills / Rules)          : {len(harvest.surviving_skills)}")
    print("-" * 78)

    if args.verbose:
        if harvest.obstructions:
            print("\n[!] Top Farmed Obstructions:")
            for obs in harvest.obstructions[:15]:
                doms = ",".join(d.value for d in obs.domains)
                print(f"  * [{obs.severity.value}] {obs.obstruction_id} ({doms})")
                print(f"    Class     : {obs.failure_class}")
                print(f"    Blocker   : {obs.description}")
                print(f"    Anti-Skill: {obs.suggested_anti_skill}")
                print(f"    Repair    : {obs.suggested_skill_repair}\n")

        if harvest.surviving_skills:
            print("\n[+] Top Surviving Invariants:")
            for skill in harvest.surviving_skills[:10]:
                doms = ",".join(d.value for d in skill.domains)
                print(f"  * {skill.skill_id} ({doms})")
                print(f"    Pattern   : {skill.surviving_pattern}")
                print(f"    Skill     : {skill.suggested_skill_name}\n")

    # Persist Adversary run bundle if requested
    if args.persist_adversary_run:
        print("[*] Persisting canonical Adversary run bundle into _intelligence/_adversary/runs/...")
        persist_res = service.persist_adversary_harvest_run(
            repo_root=repo_root,
            harvest=harvest,
            task_key=args.task_key,
            domain_filter=args.domain if args.domain != "ALL" else None,
        )
        if persist_res.is_err:
            refusal = persist_res.unwrap_err()
            print(f"[-] Persistence Refused ({refusal.code}): {refusal.message}", file=sys.stderr)
            return 2
        run_folder = persist_res.unwrap()
        print(f"[+] Adversary Run Persisted Successfully: {run_folder}")
        print("    - uns.md")
        print("    - ddc.jsonl (merged DDA/DDC letter tape)")
        print("    - uts.jsonl")
        print("    - summary.json")
        print("    - receipt.json (Verdict: OPEN_RESIDUAL)")

    # Write full JSON report if requested
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(harvest.to_dict(), indent=2), encoding="utf-8")
        print(f"[+] Harvest JSON Report written to: {out_path}")

    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
