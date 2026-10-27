#!/usr/bin/env python3
"""Automated Normal Form Contract Validator Script.

Validates all normal form YAML contracts in pfp/infrastructure/yaml/normal_forms/
against standard.yaml, normal_form_contract_schema.yaml, index.yaml, and the canonical
testing harness in pfp/infrastructure/yaml/normal_forms/.

Invariants Checked:
1. Deterministic YAML parsing across all contracts.
2. Complete top-level sections conforming to smplx.nf.contract.v0 / smplx.nf.contract.v1.
3. 1:1 ID to filename-stem bijection and index.yaml registration consistency.
4. Four-Pillar Quadrilateral integrity:
   - Pillar I: Anomaly Exclusion
   - Pillar II: Lossless Join / Reconstruction
   - Pillar III: Dependency Preservation
   - Pillar IV: Syntactic Decision Procedure
5. Non-claims discipline (purpose.non_claims non-empty with bounded scope).
6. Terminal route completeness (all declared routes map to canonical terminals).
7. Load-bearing authorization invariant:
   - authorized_by: null
   - certified_implies_authorized: false

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _find_repo_root(p: Path = Path(__file__).resolve()) -> Path:
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[1]


REPO_ROOT = _find_repo_root()
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from pfp.infrastructure.normal_form_loading import audit_specs_directory
from pfp.infrastructure.normal_forms.catalog import (
    _contract_paths,
    check_catalog,
    validate_contract,
)
from pfp.infrastructure.normal_forms.contract_model import load_yaml

DEFAULT_CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "infrastructure/yaml/normal_forms"
_STANDARDS_DIR = DEFAULT_CONTRACTS_DIR / "_golden_nfs"
DEFAULT_STANDARD_PATH = (
    _STANDARDS_DIR / "standard.yaml"
    if (_STANDARDS_DIR / "standard.yaml").is_file()
    else DEFAULT_CONTRACTS_DIR / "standard.yaml"
)
DEFAULT_SCHEMA_PATH = (
    _STANDARDS_DIR / "normal_form_contract_schema.yaml"
    if (_STANDARDS_DIR / "normal_form_contract_schema.yaml").is_file()
    else DEFAULT_CONTRACTS_DIR / "normal_form_contract_schema.yaml"
)
DEFAULT_INDEX_PATH = DEFAULT_CONTRACTS_DIR / "index.yaml"


def verify_normal_forms(
    contracts_dir: Path | None = None,
    standard_path: Path | None = None,
    schema_path: Path | None = None,
    index_path: Path | None = None,
    verbose: bool = True,
) -> tuple[int, list[str]]:
    """Run comprehensive validation across all normal-form contracts."""
    c_dir = contracts_dir or DEFAULT_CONTRACTS_DIR
    std_path = standard_path or DEFAULT_STANDARD_PATH
    sch_path = schema_path or DEFAULT_SCHEMA_PATH
    idx_path = index_path or DEFAULT_INDEX_PATH

    errors: list[str] = []

    if not c_dir.is_dir():
        errors.append(f"Contracts directory not found: {c_dir}")
        return 1, errors

    if not std_path.is_file():
        errors.append(f"Standard file not found: {std_path}")
        return 1, errors

    if not idx_path.is_file():
        errors.append(f"Index file not found: {idx_path}")
        return 1, errors

    # 1. Parse standard and index
    try:
        standard_doc = load_yaml(std_path)
    except Exception as exc:
        errors.append(f"Failed to parse standard {std_path.name}: {exc}")
        return 1, errors

    try:
        index_doc = load_yaml(idx_path)
    except Exception as exc:
        errors.append(f"Failed to parse index {idx_path.name}: {exc}")
        return 1, errors

    schema_doc = None
    if sch_path.is_file():
        try:
            schema_doc = load_yaml(sch_path)
        except Exception as exc:
            errors.append(f"Failed to parse schema {sch_path.name}: {exc}")

    # 2. Discover contract files
    contract_paths = _contract_paths(c_dir)
    if not contract_paths:
        errors.append(f"No nf.*.yaml contract files found in {c_dir}")
        return 1, errors

    if verbose:
        print(f"Discovered {len(contract_paths)} contract files in {c_dir}")

    # 3. Catalog-level check via nf_contract_parser
    catalog_findings = check_catalog(
        catalog=c_dir,
        standard_path=std_path,
        index_path=idx_path,
    )
    for finding in catalog_findings:
        errors.append(f"Catalog check finding: {finding.format()}")

    # 4. Contract structural audit via the filesystem loading adapter
    harness_results = audit_specs_directory(c_dir)
    for filename, defects in harness_results.items():
        for d in defects:
            errors.append(f"Structural defect in {filename}: [{d.field}] {d.message}")

    # 5. Index parity assertion
    contracts_sec = index_doc.get("contracts", {})
    active_ids = set(contracts_sec.get("active", []))
    draft_ids = set(contracts_sec.get("draft", []))
    deprecated_ids = set(contracts_sec.get("deprecated", []))
    all_indexed_ids = active_ids | draft_ids | deprecated_ids

    file_ids = {p.stem for p in contract_paths}
    unindexed = file_ids - all_indexed_ids
    if unindexed:
        errors.append(f"Contracts on disk missing from index.yaml: {sorted(unindexed)}")

    missing_files = all_indexed_ids - file_ids
    if missing_files:
        errors.append(
            f"Contracts declared in index.yaml but missing from disk: {sorted(missing_files)}"
        )

    # 6. Per-contract deep inspection
    validated_count = 0
    for p in contract_paths:
        try:
            doc = load_yaml(p)
        except Exception as exc:
            errors.append(f"{p.name}: YAML parsing error: {exc}")
            continue

        if not isinstance(doc, dict):
            errors.append(f"{p.name}: Contract root is not a dictionary mapping")
            continue

        # In-depth validation via validate_contract
        findings = validate_contract(
            doc,
            standard=standard_doc,
            schema_v1=schema_doc,
            path=p,
            index_data=index_doc,
        )
        for f in findings:
            errors.append(f"{p.name}: {f.code}: {f.message}")

        # Authorization fence assertion (the load-bearing invariant)
        auth = doc.get("authorization")
        if not isinstance(auth, dict):
            errors.append(f"{p.name}: Missing authorization block")
        else:
            if auth.get("authorized_by") is not None:
                errors.append(
                    f"{p.name}: authorized_by must be null, found {auth.get('authorized_by')!r}"
                )
            if auth.get("certified_implies_authorized") is not False:
                errors.append(f"{p.name}: certified_implies_authorized must be explicitly false")

        validated_count += 1

    if verbose:
        print(
            f"Validated {validated_count}/{len(contract_paths)} contracts against schema, standard, and invariants."
        )
        print(f"Active contracts:     {len(active_ids)}")
        print(f"Draft contracts:      {len(draft_ids)}")
        print(f"Deprecated contracts: {len(deprecated_ids)}")

    exit_code = 1 if errors else 0
    return exit_code, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate normal-form YAML contracts against schema and standard."
    )
    parser.add_argument(
        "--contracts-dir",
        type=Path,
        default=DEFAULT_CONTRACTS_DIR,
        help="Path to normal-form contracts directory.",
    )
    parser.add_argument(
        "--standard",
        type=Path,
        default=DEFAULT_STANDARD_PATH,
        help="Path to standard.yaml specification.",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA_PATH,
        help="Path to normal_form_contract_schema.yaml.",
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        help="Path to index.yaml catalog.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress verbose diagnostic messages.",
    )
    args = parser.parse_args(argv)

    print("=== AUTOMATED NORMAL FORM CONTRACT VALIDATOR ===")
    print(f"Contracts Directory: {args.contracts_dir}")
    print(f"Standard Path:       {args.standard}")
    print(f"Schema Path:         {args.schema}")
    print(f"Index Path:          {args.index}")
    print("-" * 60)

    exit_code, errors = verify_normal_forms(
        contracts_dir=args.contracts_dir,
        standard_path=args.standard,
        schema_path=args.schema,
        index_path=args.index,
        verbose=not args.quiet,
    )

    print("-" * 60)
    if exit_code == 0:
        print(
            f"ALL CHECKS PASSED: All {len(_contract_paths(args.contracts_dir))} normal form YAML contracts conform to standard and schema."
        )
        print(
            "Zero structural defects, 100% index parity, and load-bearing authorization invariants verified."
        )
    else:
        print(f"VALIDATION FAILED: Found {len(errors)} error(s):")
        for err in errors:
            print(f"  [DEFECT] {err}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
