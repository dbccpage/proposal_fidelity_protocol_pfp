"""Declarative normal-form contract validation.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# =============================================================================
# Part 1: Declarative Contract Schema Validation Harness
# =============================================================================


@dataclass(frozen=True)
class ContractDefect:
    """One structural or semantic defect identified in a contract specification."""

    field: str
    message: str


REQUIRED_TOP_LEVEL_SECTIONS: tuple[str, ...] = (
    "schema_version",
    "contract_kind",
    "identity",
    "classification",
    "purpose",
    "declarations_required",
    "evidence_required",
    "validation_criteria",
    "terminal_routes",
    "certification",
    "authorization",
)

VALID_STATUSES: frozenset[str] = frozenset({"active", "draft", "deprecated"})
VALID_FAMILIES: frozenset[str] = frozenset(
    {
        "classical",
        "change",
        "physics",
        "epistemic",
        "evidence",
        "derivation",
        "coda",
        "representation",
        "fsp",
        "cochain",
        "cohomology",
        "recursion",
        "logic",
        "runtime",
        "motion",
        "relativistic",
        "query",
        "transport",
        "experimental",
        "compilation",
        "genesis",
        "bridge",
        "shape",
        "topology",
        "authority",
        "security",
        "code",
    }
)
VALID_HIERARCHIES: frozenset[str] = frozenset(
    {
        "genesis_form",
        "bridge_form",
        "form",
        "normal_form",
        "certified_normal_form",
        "authorized_normal_form",
        "transformation_contract",
        "authority_contract",
    }
)
VALID_DATA_POSTURES: frozenset[str] = frozenset({"at_rest", "in_motion", "in_transformation"})
VALID_MATH_POSTURES: frozenset[str] = frozenset(
    {"operational", "formal_algebraic", "verified_mechanized"}
)


VALID_CONTRACT_KINDS: frozenset[str] = frozenset(
    {
        "normal_form_contract",
        "form_contract",
        "genesis_contract",
        "bridge_contract",
        "transformation_contract",
        "authority_contract",
        "evidence_contract",
    }
)


_STANDARD_TERMINAL_ROUTES: frozenset[str] = frozenset(
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


def _validate_contract_top_level(data: dict[str, Any]) -> list[ContractDefect]:
    defects: list[ContractDefect] = []
    for section in REQUIRED_TOP_LEVEL_SECTIONS:
        if section not in data:
            defects.append(
                ContractDefect(section, f"Missing required top-level section: '{section}'")
            )
    return defects


def _validate_contract_schema_and_kind(data: dict[str, Any]) -> list[ContractDefect]:
    defects: list[ContractDefect] = []
    if data.get("schema_version") not in ("smplx.nf.contract.v0", "smplx.nf.contract.v1"):
        defects.append(
            ContractDefect(
                "schema_version", f"Unsupported schema_version: {data.get('schema_version')!r}"
            )
        )
    if data.get("contract_kind") not in VALID_CONTRACT_KINDS:
        defects.append(
            ContractDefect(
                "contract_kind", f"Unsupported contract_kind: {data.get('contract_kind')!r}"
            )
        )
    return defects


def _validate_contract_identity(
    ident: Any, filename_stem: str | None = None
) -> list[ContractDefect]:
    if not isinstance(ident, dict):
        return [ContractDefect("identity", "identity section must be a mapping")]

    defects: list[ContractDefect] = []
    for req in ("id", "name", "short_name", "version", "status", "family"):
        if req not in ident:
            defects.append(ContractDefect(f"identity.{req}", f"Missing identity field: '{req}'"))

    if ident.get("status") not in VALID_STATUSES:
        defects.append(
            ContractDefect("identity.status", f"Invalid status: {ident.get('status')!r}")
        )
    if ident.get("family") not in VALID_FAMILIES:
        defects.append(
            ContractDefect("identity.family", f"Invalid family: {ident.get('family')!r}")
        )
    return defects


def _validate_contract_classification(classif: Any) -> list[ContractDefect]:
    if not isinstance(classif, dict):
        return [ContractDefect("classification", "classification section must be a mapping")]

    defects: list[ContractDefect] = []
    if classif.get("hierarchy_level") not in VALID_HIERARCHIES:
        defects.append(
            ContractDefect(
                "classification.hierarchy_level",
                f"Invalid hierarchy: {classif.get('hierarchy_level')!r}",
            )
        )
    if (
        not isinstance(classif.get("subject_kind"), list)
        or len(classif.get("subject_kind", [])) == 0
    ):
        defects.append(
            ContractDefect(
                "classification.subject_kind", "subject_kind must be a non-empty sequence"
            )
        )
    if classif.get("data_posture") not in VALID_DATA_POSTURES:
        defects.append(
            ContractDefect(
                "classification.data_posture",
                f"Invalid data_posture: {classif.get('data_posture')!r}",
            )
        )
    if classif.get("mathematical_posture") not in VALID_MATH_POSTURES:
        defects.append(
            ContractDefect(
                "classification.mathematical_posture",
                f"Invalid math posture: {classif.get('mathematical_posture')!r}",
            )
        )
    return defects


def _validate_contract_purpose(purpose: Any) -> list[ContractDefect]:
    if not isinstance(purpose, dict):
        return [ContractDefect("purpose", "purpose section must be a mapping")]

    defects: list[ContractDefect] = []
    for field in (
        "excludes_anomaly",
        "preserves_invariant",
        "protected_skeleton",
        "erased_structure",
        "non_claims",
    ):
        if field not in purpose:
            defects.append(ContractDefect(f"purpose.{field}", f"Missing purpose field: '{field}'"))

    non_claims = purpose.get("non_claims")
    if not isinstance(non_claims, list) or len(non_claims) == 0:
        defects.append(
            ContractDefect(
                "purpose.non_claims",
                "non_claims must be a non-empty sequence of explicit boundaries",
            )
        )
    return defects


def _validate_contract_routes_map(data: dict[str, Any]) -> list[ContractDefect]:
    defects: list[ContractDefect] = []
    for list_sec in ("declarations_required", "validation_criteria", "terminal_routes"):
        val = data.get(list_sec)
        if not isinstance(val, list) or len(val) == 0:
            defects.append(ContractDefect(list_sec, f"{list_sec} must be a non-empty list"))

    if not isinstance(data.get("evidence_required"), list):
        defects.append(ContractDefect("evidence_required", "evidence_required must be a list"))

    t_map = data.get("terminal_route_map")
    c_map = data.get("canonical_terminal_map")
    combined_map: dict[str, Any] = {}
    if isinstance(t_map, dict):
        combined_map.update(t_map)
    if isinstance(c_map, dict):
        combined_map.update(c_map)

    routes = data.get("terminal_routes", [])
    if isinstance(routes, list) and combined_map:
        for route in routes:
            if route not in combined_map and route not in _STANDARD_TERMINAL_ROUTES:
                defects.append(
                    ContractDefect(
                        "terminal_route_map",
                        f"Terminal route '{route}' has no mapping entry in terminal_route_map",
                    )
                )
    return defects


def _validate_contract_certification_auth(data: dict[str, Any]) -> list[ContractDefect]:
    defects: list[ContractDefect] = []
    cert = data.get("certification")
    if not isinstance(cert, dict):
        defects.append(ContractDefect("certification", "certification section must be a mapping"))
    else:
        if not isinstance(cert.get("certificate_required"), bool):
            defects.append(
                ContractDefect(
                    "certification.certificate_required", "certificate_required must be a boolean"
                )
            )
        if not isinstance(cert.get("verifier_required"), bool):
            defects.append(
                ContractDefect(
                    "certification.verifier_required", "verifier_required must be a boolean"
                )
            )

    auth = data.get("authorization")
    if not isinstance(auth, dict):
        defects.append(ContractDefect("authorization", "authorization section must be a mapping"))
    else:
        if auth.get("authorized_by") is not None:
            defects.append(
                ContractDefect(
                    "authorization.authorized_by",
                    f"authorized_by must be null (AuthorityEffect: None), got {auth.get('authorized_by')!r}",
                )
            )
        if auth.get("certified_implies_authorized") is not False:
            defects.append(
                ContractDefect(
                    "authorization.certified_implies_authorized",
                    "certified_implies_authorized must be explicitly false",
                )
            )
    return defects


def validate_contract_dict(
    data: dict[str, Any], filename_stem: str | None = None
) -> list[ContractDefect]:
    """Validates an in-memory dictionary against smplx.nf.contract.v0 invariants."""
    top_defects = _validate_contract_top_level(data)
    if top_defects:
        return top_defects

    defects: list[ContractDefect] = []
    defects.extend(_validate_contract_schema_and_kind(data))
    defects.extend(_validate_contract_identity(data.get("identity"), filename_stem=filename_stem))
    defects.extend(_validate_contract_classification(data.get("classification")))
    defects.extend(_validate_contract_purpose(data.get("purpose")))
    defects.extend(_validate_contract_routes_map(data))
    defects.extend(_validate_contract_certification_auth(data))
    return defects
