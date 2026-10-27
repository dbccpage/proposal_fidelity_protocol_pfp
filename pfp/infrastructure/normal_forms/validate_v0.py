"""Validator for smplx.nf.contract.v0 four-pillar contracts.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pfp.infrastructure.normal_forms.contract_model import (
    CANONICAL_TERMINALS_DEFAULT,
)
from pfp.infrastructure.normal_forms.contract_model import Finding
from pfp.infrastructure.normal_forms.contract_model import as_text
from pfp.infrastructure.normal_forms.contract_model import check_index_status
from pfp.infrastructure.normal_forms.contract_model import check_schema_ref
from pfp.infrastructure.normal_forms.contract_model import (
    check_verified_claim,
)
from pfp.infrastructure.normal_forms.contract_model import declared_routes
from pfp.infrastructure.normal_forms.contract_model import document_label
from pfp.infrastructure.normal_forms.contract_model import lookup
from pfp.infrastructure.normal_forms.contract_model import quadrilateral_of
from pfp.infrastructure.normal_forms.contract_model import (
    reject_unknown_fields,
)
from pfp.infrastructure.normal_forms.contract_model import route_image


def validate_contract_v0(
    doc: Any,
    standard: dict,
    path: Path | None = None,
    index_data: dict | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    label = document_label(doc, path, "contract_v0")

    def fail(code: str, message: str) -> None:
        findings.append(Finding(label, code, message))

    if not isinstance(doc, dict):
        fail("document", "the file does not hold a mapping")
        return findings

    reject_unknown_fields(doc, fail)
    shape = standard["document"]
    if doc.get("schema_version") != "smplx.nf.contract.v0":
        fail("schema_version", f"expected smplx.nf.contract.v0, got {doc.get('schema_version')}")
    if doc.get("contract_kind") not in shape["contract_kinds"]:
        fail("contract_kind", "contract_kind is missing or outside the standard")
    check_schema_ref(doc, path, fail, require_path=False)

    identity = doc.get("identity")
    if not isinstance(identity, dict):
        fail("identity", "identity is missing")
        identity = {}
    for field_name in shape["identity_required"]:
        if not as_text(identity.get(field_name)):
            fail("identity", f"identity.{field_name} is missing")
    contract_id = identity.get("id")
    if path is not None and isinstance(contract_id, str) and contract_id != path.stem:
        fail("id_filename_mismatch", f"{contract_id} does not match {path.stem}")
    check_index_status(identity, index_data, fail)
    check_verified_claim(doc, identity, fail)

    purpose = doc.get("purpose") if isinstance(doc.get("purpose"), dict) else {}
    for field_name in shape["purpose_required"]:
        value = purpose.get(field_name)
        if field_name == "non_claims":
            if not isinstance(value, list) or not value:
                fail("non_claims", "purpose.non_claims needs at least one entry")
        elif field_name == "protected_skeleton":
            if not isinstance(value, list) or not value:
                fail("protected_skeleton", "purpose.protected_skeleton needs at least one entry")
        elif not as_text(value):
            fail("purpose", f"purpose.{field_name} is missing")

    if not isinstance(doc.get("declarations_required"), list) or not doc["declarations_required"]:
        fail("declarations", "declarations_required needs at least one entry")
    if not isinstance(doc.get("validation_criteria"), list) or not doc["validation_criteria"]:
        fail("validation", "validation_criteria needs at least one entry")
    if not declared_routes(doc):
        fail("terminals", "terminal_routes needs at least one route")

    quad = quadrilateral_of(doc)
    if quad is None:
        fail("quadrilateral", "the four-pillar block is missing")
        quad = {}
    for field_name in shape["quadrilateral_required"]:
        if field_name not in quad:
            fail("quadrilateral", f"quadrilateral.{field_name} is missing")
    if "qualifies_as_true_normal_form" in quad and not isinstance(
        quad.get("qualifies_as_true_normal_form"), bool
    ):
        fail("quadrilateral", "qualifies_as_true_normal_form is not a boolean")
    if not as_text(quad.get("anomaly_exclusion")):
        fail("anomaly_exclusion", "pillar I does not name an anomaly")

    for pillar in ("lossless_join", "dependency_preservation", "syntactic_decision"):
        block = quad.get(pillar)
        if not isinstance(block, dict):
            fail(pillar, f"pillar {pillar} is missing")
            continue
        for field_name in shape["pillar_fields"]:
            if not as_text(block.get(field_name)):
                fail(pillar, f"{pillar}.{field_name} is missing")

    if quad.get("qualifies_as_true_normal_form") is True:
        status = (quad.get("lossless_join") or {}).get("status")
        allowed = set(standard["true_normal_form_reconstruction_statuses"])
        if status not in allowed:
            fail(
                "true_form_reconstruction",
                f"a true normal form needs reconstruction status in {sorted(allowed)}",
            )

    canonical = set(standard.get("canonical_terminals", CANONICAL_TERMINALS_DEFAULT))
    for route in declared_routes(doc):
        if route_image(doc, route, canonical) is None:
            fail("unmapped_terminal", f"{route} has no canonical terminal")

    authorization = doc.get("authorization")
    expected = shape["authorization"]["certified_implies_authorized"]
    if (
        not isinstance(authorization, dict)
        or authorization.get("certified_implies_authorized") is not expected
    ):
        fail("authorization", "certified_implies_authorized must be false")

    for check in standard.get("membership_checks", []):
        if check.get("id") != contract_id:
            continue
        if "qualifies_as_true_normal_form" in check:
            actual = quad.get("qualifies_as_true_normal_form")
            if actual is not check["qualifies_as_true_normal_form"]:
                fail("membership", f"qualifies_as_true_normal_form is {actual}")
        statement = as_text((doc.get("definition") or {}).get("formal_statement")).lower()
        for phrase in check.get("formal_statement_contains", []):
            if phrase.lower() not in statement:
                fail("membership", f"formal statement does not contain {phrase}")
        for dotted, expected_value in (check.get("fields") or {}).items():
            actual = lookup(doc, dotted)
            if actual != expected_value:
                fail("membership", f"{dotted} is {actual!r}")
    return findings
