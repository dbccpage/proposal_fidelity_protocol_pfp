"""Migrate a smplx.nf.contract.v0 document to smplx.nf.contract.v1.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from pfp.infrastructure.normal_forms.contract_model import quadrilateral_of


def migrate_v0_to_v1(doc: dict) -> dict[str, Any]:
    if not isinstance(doc, dict):
        raise ValueError("doc must be a dictionary")

    quad = quadrilateral_of(doc) or {}
    is_true = bool(quad.get("qualifies_as_true_normal_form", False))
    identity = dict(doc.get("identity", {}))
    identity.setdefault("theory_status", "established" if is_true else "proposed")
    identity.setdefault("contract_status", identity.get("status", "draft"))
    identity.setdefault("verification_status", "absent")

    classification = dict(doc.get("classification", {}))
    classification.setdefault("hierarchy_level", "normal_form" if is_true else "form")
    classification.setdefault(
        "subject_kind",
        doc.get("purpose", {}).get("protected_skeleton", ["relational_schema"]),
    )
    classification.setdefault("data_posture", "at_rest")
    classification.setdefault("mathematical_posture", "operational")

    purpose = dict(doc.get("purpose", {}))
    purpose.setdefault("excludes_anomaly", quad.get("anomaly_exclusion", ""))
    purpose.setdefault("preserves_invariant", "")
    purpose.setdefault("protected_skeleton", ["relational_schema"])
    purpose.setdefault("erased_structure", [])
    purpose.setdefault("non_claims", ["does not imply external authorization"])

    certification = dict(doc.get("certification", {}))
    certification.setdefault("certificate_required", False)
    certification.setdefault("certificate_kind", None)
    certification.setdefault("obstruction_class_required", False)
    certification.setdefault("loss_ledger_required", False)
    certification.setdefault("loss_ledger_trigger_id", None)
    certification.setdefault("verifier_required", False)

    authorization = dict(doc.get("authorization", {}))
    authorization.setdefault("authorized_by", None)
    authorization["certified_implies_authorized"] = False

    migrated: dict[str, Any] = {
        "schema_version": "smplx.nf.contract.v1",
        "contract_kind": doc.get("contract_kind", "normal_form_contract"),
        "identity": identity,
        "classification": classification,
        "purpose": purpose,
        "declarations_required": list(doc.get("declarations_required", [])),
        "evidence_required": list(doc.get("evidence_required", [])),
        "validation_criteria": list(doc.get("validation_criteria", [])),
        "terminal_routes": list(doc.get("terminal_routes", [])),
        "terminal_route_map": dict(
            doc.get("terminal_route_map") or doc.get("canonical_terminal_map", {})
        ),
        "certification": certification,
        "authorization": authorization,
    }
    extensions = dict(doc.get("extensions", {}))
    if "definition" in doc:
        extensions["definition"] = doc["definition"]
    definition = extensions.get("definition", {})
    if "quadrilateral" in doc and "quadrilateral" not in definition:
        extensions["quadrilateral"] = doc["quadrilateral"]
    if extensions:
        migrated["extensions"] = extensions
    return migrated
