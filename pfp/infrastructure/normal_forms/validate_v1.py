"""Validator for smplx.nf.contract.v1 flat contracts.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from omega_engine_pfp.infrastructure.normal_forms.contract_model import (
    CANONICAL_TERMINALS_DEFAULT,
)
from omega_engine_pfp.infrastructure.normal_forms.contract_model import Finding
from omega_engine_pfp.infrastructure.normal_forms.contract_model import as_text
from omega_engine_pfp.infrastructure.normal_forms.contract_model import check_index_status
from omega_engine_pfp.infrastructure.normal_forms.contract_model import check_schema_ref
from omega_engine_pfp.infrastructure.normal_forms.contract_model import (
    check_verified_claim,
)
from omega_engine_pfp.infrastructure.normal_forms.contract_model import document_label
from omega_engine_pfp.infrastructure.normal_forms.contract_model import (
    reject_unknown_fields,
)
from omega_engine_pfp.infrastructure.normal_forms.contract_model import route_image

_REQUIRED_SECTIONS = (
    "schema_version",
    "contract_kind",
    "identity",
    "classification",
    "purpose",
    "declarations_required",
    "validation_criteria",
    "terminal_routes",
    "terminal_route_map",
    "certification",
    "authorization",
)

_IDENTITY_FIELDS = (
    "id",
    "name",
    "short_name",
    "version",
    "family",
    "theory_status",
    "contract_status",
    "verification_status",
)

_PURPOSE_FIELDS = (
    "excludes_anomaly",
    "preserves_invariant",
    "protected_skeleton",
    "non_claims",
)


def validate_contract_v1(
    doc: Any,
    schema_v1: dict | None = None,
    path: Path | None = None,
    standard: dict | None = None,
    index_data: dict | None = None,
) -> list[Finding]:
    del schema_v1
    findings: list[Finding] = []
    label = document_label(doc, path, "contract_v1")

    def fail(code: str, message: str) -> None:
        findings.append(Finding(label, code, message))

    if not isinstance(doc, dict):
        fail("document", "the file does not hold a mapping")
        return findings

    if doc.get("schema_version") not in ("smplx.nf.contract.v1", "smplx.nf.contract_schema.v1"):
        fail("schema_version", f"expected smplx.nf.contract.v1, got {doc.get('schema_version')}")
    for section in _REQUIRED_SECTIONS:
        if section not in doc:
            fail(section, f"missing required v1 top-level section: '{section}'")
    reject_unknown_fields(doc, fail)
    check_schema_ref(doc, path, fail, require_path=True)

    identity = doc.get("identity")
    if not isinstance(identity, dict):
        fail("identity", "identity section must be a mapping")
        identity = {}
    for field_name in _IDENTITY_FIELDS:
        if not as_text(identity.get(field_name)):
            fail("identity", f"identity.{field_name} is missing")
    contract_id = identity.get("id")
    if path is not None and isinstance(contract_id, str) and contract_id != path.stem:
        fail("id_filename_mismatch", f"{contract_id} does not match {path.stem}")
    check_index_status(identity, index_data, fail)
    check_verified_claim(doc, identity, fail)

    purpose = doc.get("purpose")
    if not isinstance(purpose, dict):
        fail("purpose", "purpose section must be a mapping")
        purpose = {}
    for field_name in _PURPOSE_FIELDS:
        if not purpose.get(field_name):
            fail("purpose", f"purpose.{field_name} is missing or empty")

    routes = doc.get("terminal_routes", [])
    if not routes:
        fail("terminals", "terminal_routes needs at least one route")
    if standard and "canonical_terminals" in standard:
        canonical = set(standard["canonical_terminals"])
    else:
        canonical = set(CANONICAL_TERMINALS_DEFAULT)
    for route in routes:
        if route_image(doc, route, canonical) is None:
            fail("unmapped_terminal", f"{route} has no canonical terminal")

    authorization = doc.get("authorization")
    if (
        not isinstance(authorization, dict)
        or authorization.get("certified_implies_authorized") is not False
    ):
        fail("authorization", "certified_implies_authorized must be false")
    return findings
