"""CLI entrypoint for normal forms verification, evaluation, and example execution.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

if __name__ == "__main__" and __package__ is None:
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from omega_engine_pfp.domain.normal_forms.examples import (
    order_line,
    order_line_fails_second_normal_form,
    street_journal_title,
    street_journal_title_passes_third_and_fails_boyce_codd,
    street_journal_title_split,
)
from omega_engine_pfp.domain.normal_forms.relational import find_candidate_keys
from omega_engine_pfp.infrastructure.normal_forms import (
    CONTRACTS_DIR,
    NormalFormsEvaluator,
    check_catalog,
)


def run_normal_forms_cli(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="omega_engine_education_nf",
        description="Normal Forms Verification and Evaluation CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. audit-contracts
    ac = subparsers.add_parser("audit-contracts", help="Audit YAML contracts against standard.yaml")
    ac.add_argument(
        "--directory", type=Path, default=CONTRACTS_DIR, help="Directory containing contracts"
    )

    # 2. run-examples
    subparsers.add_parser("run-examples", help="Run relational normal form decomposition examples")

    # 3. eval-bqnf
    subparsers.add_parser("eval-bqnf", help="Run SQLite evaluator for 0NF-6NF and BQNF")

    args = parser.parse_args(argv)

    if args.command == "audit-contracts":
        findings = check_catalog(args.directory)
        print("Structural catalog audit only; not semantic verification of candidate execution.")
        print(f"Contracts directory: {args.directory}")
        print(f"Total findings: {len(findings)}")
        for f in findings:
            print(f"  {f.format()}")
        return 0 if not findings else 1

    if args.command == "run-examples":
        schema_ol = order_line()
        print(
            f"[Order Line] Keys: {find_candidate_keys(schema_ol)} | 2NF Fails: {order_line_fails_second_normal_form()}"
        )
        schema_sjt = street_journal_title()
        print(
            f"[Street Journal Title] Keys: {find_candidate_keys(schema_sjt)} | 3NF and not BCNF: {street_journal_title_passes_third_and_fails_boyce_codd()}"
        )
        lossless, preserved = street_journal_title_split()
        print(f"[Street Journal Title Split] Lossless: {lossless} | Preserved SJ->T: {preserved}")
        return 0

    if args.command == "eval-bqnf":
        evaluator = NormalFormsEvaluator(in_memory=True)
        # Test basic 0NF -> 1NF
        sample = [(1, "Alice", "CS101,MATH201"), (2, "Bob", "PHYS101")]
        res = evaluator.normalize_0nf_to_1nf(sample)
        print(
            f"[NormalFormsEvaluator] Flattened {len(sample)} 0NF records into {len(res)} 1NF records."
        )
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(run_normal_forms_cli())
