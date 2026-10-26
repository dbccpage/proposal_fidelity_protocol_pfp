"""Documentation-integrity bounded-context module. AuthorityEffect: None."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .configuration import read_jsonl
from .content_validation import ContentSelection, check_content, check_llms
from .domain import LEDGER_PATH, Findings, IntegrityError
from .drift_validation import (
    check_changed_education_source,
    check_changed_raw_archive,
    check_source_drift,
)
from .inventory import collect_inventory
from .ledger_validation import (
    check_archive_lock,
    check_archive_record_coverage,
    check_destination_targets,
    check_education_lock,
    check_ledger,
    check_migration_map,
)


def validate(repo_root: Path, contract: dict[str, Any], args: argparse.Namespace) -> Findings:
    findings = Findings()
    if not LEDGER_PATH.exists():
        findings.error("Missing source-ledger.jsonl; run inventory")
        return findings
    try:
        rows = read_jsonl(LEDGER_PATH)
        current = collect_inventory(repo_root, contract)
        check_ledger(rows, current, contract, findings)
        check_destination_targets(repo_root, rows, contract, findings)
        check_migration_map(rows, findings)
        check_archive_lock(current, contract, findings)
        check_archive_record_coverage(
            current, contract, findings, required=args.require_archive_records
        )
        check_education_lock(
            current, repo_root, contract, findings, require_copies=args.require_education_copies
        )
        scope = "all" if args.strict_content else args.content_scope
        check_content(
            repo_root,
            contract,
            findings,
            ContentSelection(
                scope,
                args.changed_base,
                args.changed_content,
            ),
        )
        check_llms(repo_root, contract, findings, required=args.require_llms)
        if args.changed_base:
            check_changed_raw_archive(repo_root, contract, args.changed_base, findings)
            check_changed_education_source(repo_root, contract, args.changed_base, findings)
            check_source_drift(repo_root, rows, contract, args.changed_base, findings)
    except IntegrityError as error:
        findings.error(str(error))
    return findings
