"""Load a normal-form catalog and dispatch v0 or v1 validation.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

from omega_engine_pfp.infrastructure.normal_forms.contract_model import Finding
from omega_engine_pfp.infrastructure.normal_forms.contract_model import load_yaml
from omega_engine_pfp.infrastructure.normal_forms.contract_paths import CONTRACTS_DIR
from omega_engine_pfp.infrastructure.normal_forms.contract_paths import INDEX_PATH
from omega_engine_pfp.infrastructure.normal_forms.contract_paths import STANDARD_PATH
from omega_engine_pfp.infrastructure.normal_forms.validate_v0 import validate_contract_v0
from omega_engine_pfp.infrastructure.normal_forms.validate_v1 import validate_contract_v1


def validate_contract(
    doc: Any,
    standard: dict | None = None,
    schema_v1: dict | None = None,
    path: Path | None = None,
    index_data: dict | None = None,
) -> list[Finding]:
    if not isinstance(doc, dict):
        label = path.name if path else "contract"
        return [Finding(label, "document", "the file does not hold a mapping")]
    if standard is None:
        standard = load_yaml(STANDARD_PATH) if STANDARD_PATH.is_file() else {}
    version = doc.get("schema_version")
    if version in ("smplx.nf.contract.v1", "smplx.nf.contract_schema.v1"):
        return validate_contract_v1(doc, schema_v1, path, standard, index_data)
    return validate_contract_v0(doc, standard, path, index_data)


def check_document(
    path: Path,
    doc: Any,
    standard: dict,
    index_data: dict | None = None,
    schema_v1: dict | None = None,
) -> list[Finding]:
    return validate_contract(doc, standard, schema_v1, path, index_data)


def _contract_paths(catalog: Path) -> list[Path]:
    paths = set(catalog.glob("nf.*.yaml"))
    bqnf = catalog / "bqnf"
    if bqnf.is_dir():
        paths |= set(bqnf.glob("nf.*.yaml"))
    return sorted(paths)


def check_catalog(
    catalog: Path | None = None,
    standard_path: Path | None = None,
    index_path: Path | None = None,
) -> list[Finding]:
    catalog = catalog or CONTRACTS_DIR
    standard_path = standard_path or STANDARD_PATH
    index_path = index_path or INDEX_PATH
    try:
        standard = load_yaml(standard_path)
    except yaml.YAMLError as exc:
        return [Finding(standard_path.name, "yaml_error", str(exc))]
    if not isinstance(standard, dict):
        return [Finding(standard_path.name, "standard", "the standard file is not a mapping")]

    index_data = None
    if index_path.is_file():
        try:
            index_data = load_yaml(index_path)
        except yaml.YAMLError:
            index_data = None

    findings: list[Finding] = []
    paths = _contract_paths(catalog)
    if not paths:
        findings.append(Finding(catalog.name, "catalog", "no nf.*.yaml contracts were found"))
    seen: dict[str, str] = {}
    for path in paths:
        try:
            document = load_yaml(path)
        except yaml.YAMLError as exc:
            findings.append(Finding(path.name, "yaml_error", str(exc).splitlines()[0]))
            continue
        findings.extend(check_document(path, document, standard, index_data))
        identity = document.get("identity") if isinstance(document, dict) else None
        contract_id = identity.get("id") if isinstance(identity, dict) else None
        if isinstance(contract_id, str):
            previous = seen.get(contract_id)
            if previous is not None:
                findings.append(
                    Finding(
                        path.name,
                        "duplicate_id",
                        f"{contract_id} is also declared by {previous}",
                    )
                )
            else:
                seen[contract_id] = path.name
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check normal-form contracts against the standard."
    )
    parser.add_argument("--catalog", type=Path, default=CONTRACTS_DIR)
    parser.add_argument("--standard", type=Path, default=STANDARD_PATH)
    parser.add_argument("--index", type=Path, default=INDEX_PATH)
    args = parser.parse_args(argv)
    findings = check_catalog(args.catalog, args.standard, args.index)
    for finding in findings:
        print(finding.format())
    if findings:
        print(f"{len(findings)} finding(s)")
        return 1
    count = len(list(args.catalog.glob("nf.*.yaml")))
    print(f"{count} normal-form contracts match {args.standard.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
