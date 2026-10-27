"""File input for exact normal-form predicates and index models."""

from __future__ import annotations

from pathlib import Path

import yaml

from pfp.domain.normal_forms.contract_validation import (
    ContractDefect,
    validate_contract_dict,
)
from pfp.domain.normal_forms.nf_domain_index import NfIndexEntry


def validate_contract_file(path: Path) -> list[ContractDefect]:
    """Parses and validates a contract file from disk."""
    if not path.is_file():
        return [ContractDefect(str(path), f"File not found: {path}")]
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as exc:
        return [ContractDefect(str(path), f"YAML parse error: {exc}")]

    if not isinstance(data, dict):
        return [ContractDefect(str(path), "Root YAML element must be a mapping")]

    return validate_contract_dict(data, filename_stem=path.stem)


def audit_specs_directory(specs_dir: Path) -> dict[str, list[ContractDefect]]:
    """Audits all YAML contracts in the specified directory."""
    results: dict[str, list[ContractDefect]] = {}
    candidate_paths = sorted(specs_dir.glob("*.yaml"))
    if (specs_dir / "bqnf").is_dir():
        candidate_paths = sorted(set(candidate_paths) | set((specs_dir / "bqnf").glob("*.yaml")))
    for p in candidate_paths:
        if p.name in (
            "normal_form_contract_schema.yaml",
            "index.yaml",
            "standard.yaml",
            "nf_domain_index.yaml",
            "normal_form_definitions.yaml",
            "packaged_demo_catalog.yaml",
            "bqnf_fsign_contract.yaml",
        ):
            continue
        results[p.name] = validate_contract_file(p)
    return results


audit_contracts_directory = audit_specs_directory

def check_contract_file(entry: NfIndexEntry, contracts_dir: Path) -> None:
    """Cross-check an index entry against its ``nf.*.yaml`` identity block.

    Raises ValueError on disagreement of id, short name, family, the
    authorization firewall, or a true-normal-form declaration.
    """
    raw = yaml.safe_load((contracts_dir / f"{entry.nf_id}.yaml").read_text(encoding="utf-8"))
    ident = raw["identity"]
    if ident["id"] != entry.nf_id or ident["short_name"] != entry.short_name:
        raise ValueError(f"{entry.nf_id}: identity disagrees with index")
    if ident["family"] != entry.family.value:
        raise ValueError(f"{entry.nf_id}: family disagrees with index")
    auth = raw["authorization"]
    if auth["authorized_by"] is not None or auth["certified_implies_authorized"] is not False:
        raise ValueError(f"{entry.nf_id}: authorization firewall violated")
