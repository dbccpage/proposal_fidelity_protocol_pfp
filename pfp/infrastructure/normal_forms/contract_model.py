"""Shared contract text, findings, and schema-ref resolution.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CANONICAL_TERMINALS_DEFAULT: frozenset[str] = frozenset(
    {
        "Preserve",
        "Repair",
        "Invalidate",
        "Recompute",
        "Serialize",
        "Lift",
        "Escalate",
        "Unsupported",
        "ClosureFailure",
        "BudgetUnknown",
        "ConservativeInvalidate",
        "Quarantine",
        "Decompose",
        "Refuse",
        "Reject",
        "Abstain",
    }
)

ALLOWED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "schema_ref",
        "contract_kind",
        "identity",
        "classification",
        "purpose",
        "declarations_required",
        "evidence_required",
        "validation_criteria",
        "terminal_routes",
        "local_terminal_routes",
        "terminal_route_map",
        "canonical_terminal_map",
        "definition",
        "quadrilateral",
        "certification",
        "authorization",
        "failure_modes",
        "examples",
        "references",
        "proof_obligations",
        "obstruction_substrate",
        "activity_predicate",
        "authority_effect",
        "extensions",
    }
)


@dataclass(frozen=True)
class Finding:
    path: str
    code: str
    message: str

    def format(self) -> str:
        return f"{self.path}: {self.code}: {self.message}"


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def lookup(doc: Any, dotted: str) -> Any:
    current = doc
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def quadrilateral_of(doc: dict) -> dict | None:
    definition = doc.get("definition")
    if isinstance(definition, dict) and isinstance(definition.get("quadrilateral"), dict):
        return definition["quadrilateral"]
    top = doc.get("quadrilateral")
    if isinstance(top, dict):
        return top
    return None


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return " ".join(as_text(item) for item in value).strip()
    return str(value).strip()


def route_image(doc: dict, route: str, canonical: set[str] | frozenset[str]) -> str | None:
    if route in canonical:
        return route
    for key in ("terminal_route_map", "canonical_terminal_map"):
        table = doc.get(key)
        if isinstance(table, dict):
            image = table.get(route)
            if isinstance(image, str) and image in canonical:
                return image
    return None


def declared_routes(doc: dict) -> list[str]:
    routes: list[str] = []
    for key in ("terminal_routes", "local_terminal_routes"):
        values = doc.get(key)
        if isinstance(values, list):
            routes.extend(item for item in values if isinstance(item, str))
    return routes


def document_label(doc: Any, path: Path | None, fallback: str) -> str:
    if path is not None:
        return path.name
    if isinstance(doc, dict):
        identity = doc.get("identity")
        if isinstance(identity, dict) and identity.get("id"):
            return str(identity["id"])
    return fallback


def resolve_schema_ref(contract_path: Path, schema_ref: str) -> Path | None:
    direct = (contract_path.parent / schema_ref).resolve()
    if direct.is_file():
        return direct
    name = Path(schema_ref).name
    for candidate in (
        contract_path.parent / "_golden_nfs" / name,
        contract_path.parent.parent / "_golden_nfs" / name,
    ):
        if candidate.is_file():
            return candidate.resolve()
    return None


def reject_unknown_fields(doc: dict, fail) -> None:
    for key in doc:
        if key not in ALLOWED_TOP_LEVEL_KEYS:
            fail("unknown_field", f"unknown top-level field '{key}'; must be in extensions")


def check_schema_ref(doc: dict, path: Path | None, fail, *, require_path: bool) -> None:
    if "schema_ref" not in doc:
        return
    if require_path and path is None:
        return
    schema_ref = doc["schema_ref"]
    if not isinstance(schema_ref, str) or not schema_ref.strip():
        fail("invalid_schema_ref", "schema_ref must be a non-empty string path")
        return
    if path is not None and resolve_schema_ref(path, schema_ref) is None:
        fail("invalid_schema_ref", f"schema_ref '{schema_ref}' does not exist on disk")


def check_index_status(identity: dict, index_data: dict | None, fail) -> None:
    contract_id = identity.get("id")
    if index_data is None or not isinstance(contract_id, str):
        return
    draft_ids = set(index_data.get("contracts", {}).get("draft", []))
    status = identity.get("contract_status") or identity.get("status")
    if contract_id in draft_ids and status == "active":
        fail(
            "misleading_active_status",
            f"contract '{contract_id}' is indexed under draft but claims contract_status: active",
        )


def check_verified_claim(doc: dict, identity: dict, fail) -> None:
    status = identity.get("verification_status")
    if status not in ("verified", "machine_checked"):
        return
    certification = doc.get("certification", {})
    has_receipt = bool(isinstance(certification, dict) and certification.get("verifier_receipt"))
    if not has_receipt and not doc.get("evidence_required"):
        fail(
            "unsupported_verified_status",
            f"contract claims verification_status: '{status}' without verified receipt or checked proof",
        )
