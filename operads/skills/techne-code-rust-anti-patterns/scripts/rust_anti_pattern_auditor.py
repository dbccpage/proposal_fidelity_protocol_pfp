"""Rust lexical candidate inventory for the AP_RS_002 signature.

Flags a derived `pub enum` without exact PartialOrd and Ord derive names.
These lexical candidates need type/use review, not automatic added derives.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from omega_engine_operations.use_cases.verification.rust_lexical_audit import (  # noqa: E402
    enum_declarations,
    in_test_span,
    mask_non_code,
    rust_files,
    test_item_spans,
)


def audit(root: Path) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for path in rust_files(root):
        try:
            code = mask_non_code(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as error:
            raise ValueError(f"{path}: {error}") from error
        test_spans = test_item_spans(code)
        relative_path = path.relative_to(root if root.is_dir() else root.parent)
        for enum in enum_declarations(code):
            if not enum["public"] or not enum["derives"]:
                continue
            if not {"Ord", "PartialOrd"}.issubset(enum["traits"]):
                findings.append(
                    {
                        "id": "AP_RS_002",
                        "file": path.as_posix(),
                        "line": enum["line"],
                        "enum": enum["name"],
                        "severity": "REVIEW",
                        "confirmation": "unverified",
                        "trait_resolution": "derive_only",
                        "has_eq": "Eq" in enum["traits"],
                        "has_partial_eq": "PartialEq" in enum["traits"],
                        "is_test": "tests" in relative_path.parts
                        or in_test_span(enum["offset"], test_spans),
                        "anti_pattern": "domain_enum_missing_ord",
                        "repair": "Review ordered-key use and payload constraints before deriving PartialOrd and Ord; manual implementations are not resolved by this lexical scan.",
                    }
                )
    return findings


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Rust anti-pattern auditor")
    parser.add_argument("--path", default=".", help="File or directory to audit")
    parser.add_argument("--report-out", default=None, help="JSON receipt path")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    target = Path(args.path)
    errors = []
    findings = []
    total_files = 0
    try:
        total_files = len(rust_files(target))
        findings = audit(target)
    except (OSError, UnicodeError, ValueError) as error:
        errors.append(str(error))
    payload = {
        "authority_effect": "None",
        "audited_path": str(target),
        "scan_kind": "lexical_triage_not_ast",
        "total_rs_files": total_files,
        "total_findings": len(findings),
        "findings": findings,
        "errors": errors,
    }
    if args.report_out:
        out = Path(args.report_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Rust ordering candidates (unverified): {len(findings)}")
    if errors:
        print("Rust audit failed: " + "; ".join(errors), file=sys.stderr)
        return 2
    if args.check and findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
