"""Deterministic Rust lexical triage for Engine crates and loose files.

Audits:
1. AP_RS_002: Domain enums / status types missing PartialOrd/Ord.
2. AP_RS_001: Local target/ duplication in crate folders.
3. Unsafe blocks and raw pointer operations.
4. unwrap() / expect() / panic! in library code vs tests.
5. Non-deterministic collections (HashMap/HashSet vs BTreeMap/BTreeSet).
6. TODO / FIXME token markings.

This is not an AST, compiler, dependency audit or proof of a defect. Derive and
collection signatures need type/use review; do not mass-add Ord to carriers.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_BASE_DIR = Path("engine/crates_rs")
NON_CRATE_FILES = "<non-crate>"

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from operations.use_cases.verification.rust_lexical_audit import (  # noqa: E402
    enum_declarations,
    in_test_span,
    mask_non_code,
    rust_files,
    test_item_spans,
)

UNSAFE_REGEX = re.compile(r"\bunsafe\s*(\{|fn\b|trait\b|impl\b)")
PANIC_REGEX = re.compile(r"\bpanic!\s*\(")
UNWRAP_REGEX = re.compile(r"\.(?:unwrap|expect)\s*\(")
HASHMAP_REGEX = re.compile(r"\b(?:std::collections::)?(?:HashMap|HashSet)\b")
BTREEMAP_REGEX = re.compile(r"\b(?:std::collections::)?(?:BTreeMap|BTreeSet)\b")


def discover_crates(base_dir: Path) -> List[str]:
    """Dynamically discover all Cargo crates under the base crates directory."""
    crates = []
    if not base_dir.is_dir():
        return crates
    for item in sorted(base_dir.iterdir()):
        if item.is_dir() and (item / "Cargo.toml").is_file():
            crates.append(item.name)
    return crates


def audit_crate(
    crate_name: str, base_dir: Path, *, files: Optional[List[Path]] = None
) -> Dict[str, Any]:
    crate_path = base_dir / crate_name
    if crate_name == NON_CRATE_FILES:
        crate_path = base_dir

    results: Dict[str, Any] = {
        "crate": crate_name,
        "exists": crate_path.is_dir(),
        # Loose files share the workspace root; its cache is not a crate-local
        # duplication. Worktree cache placement is a separate policy check.
        "has_local_target": crate_name != NON_CRATE_FILES and (crate_path / "target").is_dir(),
        "total_rs_files": 0,
        "src_files": 0,
        "test_files": 0,
        "enums_missing_ord": [],
        "unsafe_usages": [],
        "unwraps_in_src": [],
        "panics_in_src": [],
        "hashmap_usages": [],
        "btreemap_usages": [],
        "todos": [],
        "scan_kind": "lexical_triage_not_ast",
        "errors": [],
        "files": [],
    }

    if not crate_path.is_dir():
        results["errors"].append(f"Rust audit root is not a directory: {crate_path}")
        return results

    try:
        selected = rust_files(crate_path) if files is None else files
    except (OSError, ValueError) as error:
        results["errors"].append(str(error))
        return results
    for rs_file in sorted(selected):
        results["total_rs_files"] += 1
        rel_path = rs_file.relative_to(base_dir).as_posix()
        results["files"].append(rel_path)
        is_test = "tests" in rs_file.relative_to(crate_path).parts
        if is_test:
            results["test_files"] += 1
        else:
            results["src_files"] += 1

        try:
            content = rs_file.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            results["errors"].append(f"{rel_path}: {error}")
            continue

        code = mask_non_code(content)
        lines = code.splitlines()
        original_lines = content.splitlines()
        test_spans = test_item_spans(code)

        # 1. Audit Enums for AP_RS_002 (PartialOrd, Ord)
        for enum in enum_declarations(code):
            has_ord = {"PartialOrd", "Ord"}.issubset(enum["traits"])
            if not has_ord:
                results["enums_missing_ord"].append(
                    {
                        "file": rel_path,
                        "line": enum["line"],
                        "enum": enum["name"],
                        "has_eq": "Eq" in enum["traits"],
                        "has_partial_eq": "PartialEq" in enum["traits"],
                        "severity": "REVIEW",
                        "confirmation": "unverified",
                        "trait_resolution": "derive_only",
                        "is_test": is_test or in_test_span(enum["offset"], test_spans),
                        "derives": enum["derives"],
                    }
                )

        # 2. Line-by-line checks in src/ vs tests/
        line_offset = 0
        for idx, line in enumerate(lines, start=1):
            line_strip = original_lines[idx - 1].strip()

            def in_test(match: re.Match) -> bool:
                return is_test or in_test_span(line_offset + match.start(), test_spans)

            # In library code (not test files and not test modules)
            if any(not in_test(match) for match in PANIC_REGEX.finditer(line)):
                results["panics_in_src"].append(
                    {
                        "file": rel_path,
                        "line": idx,
                        "code": line_strip,
                    }
                )
            if any(not in_test(match) for match in UNWRAP_REGEX.finditer(line)):
                results["unwraps_in_src"].append(
                    {
                        "file": rel_path,
                        "line": idx,
                        "code": line_strip[:80],
                    }
                )

            for match in UNSAFE_REGEX.finditer(line):
                results["unsafe_usages"].append(
                    {
                        "file": rel_path,
                        "line": idx,
                        "code": line_strip[:80],
                        "is_test": in_test(match),
                    }
                )

            if HASHMAP_REGEX.search(line):
                results["hashmap_usages"].append(
                    {
                        "file": rel_path,
                        "line": idx,
                        "code": line_strip[:80],
                    }
                )

            if BTREEMAP_REGEX.search(line):
                results["btreemap_usages"].append(
                    {
                        "file": rel_path,
                        "line": idx,
                        "code": line_strip[:80],
                    }
                )

            if re.search(r"\b(?:TODO|FIXME)\b", line):
                results["todos"].append(
                    {
                        "file": rel_path,
                        "line": idx,
                        "code": line_strip[:80],
                    }
                )
            line_offset += len(line) + 1

    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rust_crate_reviewer",
        description="Rust lexical triage, not an AST or compiler audit",
    )
    parser.add_argument(
        "--crate",
        default=None,
        help="Specific crate name to audit (default: all Rust files, including files outside crates)",
    )
    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help=f"Path to crates root directory (default: {DEFAULT_BASE_DIR})",
    )
    parser.add_argument(
        "--report-out",
        default=None,
        help="Optional path to emit JSON audit report",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 for local target duplication or untriaged ordering candidates; not a defect verdict",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    base_dir = Path(args.base_dir)
    if not base_dir.is_dir():
        sys.stderr.write(f"Rust audit base is not a directory: {base_dir}\n")
        return 2
    extra_files: List[Path] = []
    if args.crate:
        if (
            Path(args.crate).is_absolute()
            or len(Path(args.crate).parts) != 1
            or args.crate in {".", ".."}
        ):
            sys.stderr.write("--crate must name one direct crate directory\n")
            return 2
        crate_names = [args.crate]
    else:
        try:
            crate_names = discover_crates(base_dir)
            extra_files = [
                path
                for path in rust_files(base_dir)
                if path.relative_to(base_dir).parts[0] not in crate_names
            ]
        except (OSError, ValueError) as error:
            sys.stderr.write(f"Rust enumeration failed: {error}\n")
            return 2
        if extra_files:
            crate_names.append(NON_CRATE_FILES)
        if not crate_names:
            sys.stderr.write(f"No Rust files or crates found under {base_dir}\n")
            return 2

    report: Dict[str, Any] = {}
    total_local_targets = 0
    total_enums_missing_ord = 0
    total_panics = 0
    total_unwraps = 0
    total_errors = 0

    for crate in crate_names:
        data = audit_crate(crate, base_dir, files=extra_files if crate == NON_CRATE_FILES else None)
        report[crate] = data
        total_errors += len(data["errors"])
        if data["has_local_target"]:
            total_local_targets += 1
        total_enums_missing_ord += len(data["enums_missing_ord"])
        total_panics += len(data["panics_in_src"])
        total_unwraps += len(data["unwraps_in_src"])

    if args.report_out:
        out_file = Path(args.report_out)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report written to {out_file}")

    print(f"\n--- Rust Lexical Review Summary ({len(crate_names)} Scope Groups) ---")
    for crate, data in report.items():
        if not data["exists"]:
            print(f"[{crate}] MISSING")
            continue
        print(f"[{crate}]")
        print(
            f"  Files: {data['src_files']} src, {data['test_files']} tests | "
            f"Local target/: {data['has_local_target']}"
        )
        print(
            f"  Missing Ord Enums: {len(data['enums_missing_ord'])} | "
            f"Unsafe: {len(data['unsafe_usages'])}"
        )
        print(
            f"  Panics in src: {len(data['panics_in_src'])} | "
            f"Unwraps in src: {len(data['unwraps_in_src'])}"
        )
        print(
            f"  HashMap: {len(data['hashmap_usages'])} vs BTreeMap: {len(data['btreemap_usages'])} | "
            f"TODOs: {len(data['todos'])}"
        )

    print("\n--- Estate Health Totals ---")
    print(f"  Local target/ directories (AP_RS_001): {total_local_targets}")
    print(f"  Enums missing PartialOrd/Ord (AP_RS_002): {total_enums_missing_ord}")
    print(f"  Panics in library src/: {total_panics}")
    print(f"  Unwraps in library src/: {total_unwraps}")
    print("  Interpretation: lexical candidates for review, not verified defects")

    if total_errors:
        for data in report.values():
            for error in data["errors"]:
                sys.stderr.write(f"Rust audit error: {error}\n")
        return 2

    if args.check and (total_local_targets > 0 or total_enums_missing_ord > 0):
        sys.stderr.write("REFUSED: Rust crate review audit failed --check invariants.\n")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
