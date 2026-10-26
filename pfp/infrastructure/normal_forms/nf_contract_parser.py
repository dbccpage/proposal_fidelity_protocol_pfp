"""Parse normal-form contracts against standard.yaml and v1 JSON/YAML schema.

The standard is the four-pillar reading of normal_form_foundational_definitions.md.
Implements machine validators for:
1. smplx.nf.contract.v0: Four-pillar quadrilateral contracts.
2. smplx.nf.contract.v1: Flat standalone schema matching normal_form_contract_schema.yaml.
3. migrate_v0_to_v1: Explicit migration from v0 to v1.
4. Relative schema_ref and reference validation.
5. Strict identity/status consistency checks against index.yaml.
6. Rejection of unsupported active/verified claims without verifier receipts.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any, Mapping

import yaml

from omega_engine_pfp.infrastructure.normal_forms.contract_paths import (
    CONTRACTS_DIR,
    INDEX_PATH,
    SCHEMA_V1_PATH,
    STANDARD_PATH,
)


def _repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent
    # Installed packages may use their own bundled NF resources. This candidate
    # is only the package's containing directory, never historical Git context.
    return Path(__file__).resolve().parents[4]


CANONICAL_TERMINALS_DEFAULT: frozenset[str] = frozenset({
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
})

ALLOWED_TOP_LEVEL_KEYS: frozenset[str] = frozenset({
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
})


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


# =============================================================================
# Machine Validator 1: smplx.nf.contract.v0 (Four-Pillar Quadrilateral)
# =============================================================================


def validate_contract_v0(
    doc: Any,
    standard: dict,
    path: Path | None = None,
    index_data: dict | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    label = path.name if path else (doc.get("identity", {}).get("id", "contract_v0") if isinstance(doc, dict) and isinstance(doc.get("identity"), dict) else "contract_v0")

    def fail(code: str, message: str) -> None:
        findings.append(Finding(label, code, message))

    if not isinstance(doc, dict):
        fail("document", "the file does not hold a mapping")
        return findings

    # Check for unknown top-level fields
    for k in doc:
        if k not in ALLOWED_TOP_LEVEL_KEYS:
            fail("unknown_field", f"unknown top-level field '{k}'; must be in extensions")

    shape = standard["document"]
    if doc.get("schema_version") != "smplx.nf.contract.v0":
        fail("schema_version", f"expected smplx.nf.contract.v0, got {doc.get('schema_version')}")

    if doc.get("contract_kind") not in shape["contract_kinds"]:
        fail("contract_kind", "contract_kind is missing or outside the standard")

    # Schema ref validation on relative path
    if "schema_ref" in doc:
        sref = doc["schema_ref"]
        if not isinstance(sref, str) or not sref.strip():
            fail("invalid_schema_ref", "schema_ref must be a non-empty string path")
        elif path is not None:
            ref_path = (path.parent / sref).resolve()
            if not ref_path.exists():
                candidate = (path.parent / Path(sref).name).resolve()
                if candidate.exists():
                    ref_path = candidate
                else:
                    candidate = (path.parent.parent / "contracts_nf_standards" / Path(sref).name).resolve()
                    if candidate.exists():
                        ref_path = candidate
                    else:
                        fail("invalid_schema_ref", f"schema_ref '{sref}' does not exist on disk")

    # Identity block
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

    # Check status consistency against index.yaml
    if index_data is not None and isinstance(contract_id, str):
        contracts_sec = index_data.get("contracts", {})
        draft_ids = set(contracts_sec.get("draft", []))
        c_status = identity.get("contract_status") or identity.get("status")
        if contract_id in draft_ids and c_status == "active":
            fail("misleading_active_status", f"contract '{contract_id}' is indexed under draft but claims contract_status: active")

    # Check verification status evidence
    v_status = identity.get("verification_status")
    if v_status in ("verified", "machine_checked"):
        cert = doc.get("certification", {})
        has_receipt = bool(isinstance(cert, dict) and cert.get("verifier_receipt"))
        has_evidence = bool(doc.get("evidence_required"))
        if not has_receipt and not has_evidence:
            fail("unsupported_verified_status", f"contract claims verification_status: '{v_status}' without verified receipt or checked proof")

    # Purpose block
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

    # Quadrilateral block (Four pillars)
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
    if not isinstance(authorization, dict) or authorization.get("certified_implies_authorized") is not expected:
        fail("authorization", "certified_implies_authorized must be false")

    # Membership checks from standard
    for check in standard.get("membership_checks", []):
        if check.get("id") != contract_id:
            continue
        if "qualifies_as_true_normal_form" in check:
            actual = quad.get("qualifies_as_true_normal_form")
            if actual is not check["qualifies_as_true_normal_form"]:
                fail(
                    "membership",
                    f"qualifies_as_true_normal_form is {actual}",
                )
        statement = as_text((doc.get("definition") or {}).get("formal_statement")).lower()
        for phrase in check.get("formal_statement_contains", []):
            if phrase.lower() not in statement:
                fail("membership", f"formal statement does not contain {phrase}")
        for dotted, expected_value in (check.get("fields") or {}).items():
            actual = lookup(doc, dotted)
            if actual != expected_value:
                fail("membership", f"{dotted} is {actual!r}")

    return findings


# =============================================================================
# Machine Validator 2: smplx.nf.contract.v1 (Flat Standalone Schema)
# =============================================================================


def validate_contract_v1(
    doc: Any,
    schema_v1: dict | None = None,
    path: Path | None = None,
    standard: dict | None = None,
    index_data: dict | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    label = path.name if path else (doc.get("identity", {}).get("id", "contract_v1") if isinstance(doc, dict) and isinstance(doc.get("identity"), dict) else "contract_v1")

    def fail(code: str, message: str) -> None:
        findings.append(Finding(label, code, message))

    if not isinstance(doc, dict):
        fail("document", "the file does not hold a mapping")
        return findings

    if doc.get("schema_version") not in ("smplx.nf.contract.v1", "smplx.nf.contract_schema.v1"):
        fail("schema_version", f"expected smplx.nf.contract.v1, got {doc.get('schema_version')}")

    required_sections = (
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
    for sec in required_sections:
        if sec not in doc:
            fail(sec, f"missing required v1 top-level section: '{sec}'")

    for k in doc:
        if k not in ALLOWED_TOP_LEVEL_KEYS:
            fail("unknown_field", f"unknown top-level field '{k}'; must be in extensions")

    # Schema ref validation
    if "schema_ref" in doc and path is not None:
        sref = doc["schema_ref"]
        if not isinstance(sref, str) or not sref.strip():
            fail("invalid_schema_ref", "schema_ref must be a non-empty string path")
        else:
            ref_path = (path.parent / sref).resolve()
            if not ref_path.exists():
                fail("invalid_schema_ref", f"schema_ref '{sref}' does not exist on disk")

    # Identity block
    ident = doc.get("identity")
    if not isinstance(ident, dict):
        fail("identity", "identity section must be a mapping")
        ident = {}
    for f in ("id", "name", "short_name", "version", "family", "theory_status", "contract_status", "verification_status"):
        if not as_text(ident.get(f)):
            fail("identity", f"identity.{f} is missing")

    contract_id = ident.get("id")
    if path is not None and isinstance(contract_id, str) and contract_id != path.stem:
        fail("id_filename_mismatch", f"{contract_id} does not match {path.stem}")

    if index_data is not None and isinstance(contract_id, str):
        contracts_sec = index_data.get("contracts", {})
        draft_ids = set(contracts_sec.get("draft", []))
        c_status = ident.get("contract_status") or ident.get("status")
        if contract_id in draft_ids and c_status == "active":
            fail("misleading_active_status", f"contract '{contract_id}' is indexed under draft but claims contract_status: active")

    v_status = ident.get("verification_status")
    if v_status in ("verified", "machine_checked"):
        cert = doc.get("certification", {})
        has_receipt = bool(isinstance(cert, dict) and cert.get("verifier_receipt"))
        has_evidence = bool(doc.get("evidence_required"))
        if not has_receipt and not has_evidence:
            fail("unsupported_verified_status", f"contract claims verification_status: '{v_status}' without verified receipt or checked proof")

    # Purpose block
    purpose = doc.get("purpose")
    if not isinstance(purpose, dict):
        fail("purpose", "purpose section must be a mapping")
        purpose = {}
    for f in ("excludes_anomaly", "preserves_invariant", "protected_skeleton", "non_claims"):
        if not purpose.get(f):
            fail("purpose", f"purpose.{f} is missing or empty")

    # Terminal routes & canonical mapping
    routes = doc.get("terminal_routes", [])
    if not routes:
        fail("terminals", "terminal_routes needs at least one route")
    canonical = set(standard["canonical_terminals"]) if standard and "canonical_terminals" in standard else CANONICAL_TERMINALS_DEFAULT
    for r in routes:
        if route_image(doc, r, canonical) is None:
            fail("unmapped_terminal", f"{r} has no canonical terminal")

    # Authorization
    auth = doc.get("authorization")
    if not isinstance(auth, dict) or auth.get("certified_implies_authorized") is not False:
        fail("authorization", "certified_implies_authorized must be false")

    return findings


# =============================================================================
# Migration: smplx.nf.contract.v0 -> smplx.nf.contract.v1
# =============================================================================


def migrate_v0_to_v1(doc: dict) -> dict[str, Any]:
    """Migrates a smplx.nf.contract.v0 contract dictionary to smplx.nf.contract.v1."""
    if not isinstance(doc, dict):
        raise ValueError("doc must be a dictionary")

    quad = quadrilateral_of(doc) or {}
    is_true = bool(quad.get("qualifies_as_true_normal_form", False))

    v1: dict[str, Any] = {
        "schema_version": "smplx.nf.contract.v1",
        "contract_kind": doc.get("contract_kind", "normal_form_contract"),
    }

    # Identity
    ident = dict(doc.get("identity", {}))
    ident.setdefault("theory_status", "established" if is_true else "proposed")
    ident.setdefault("contract_status", ident.get("status", "draft"))
    ident.setdefault("verification_status", "absent")
    v1["identity"] = ident

    # Classification
    classif = dict(doc.get("classification", {}))
    classif.setdefault("hierarchy_level", "normal_form" if is_true else "form")
    classif.setdefault("subject_kind", doc.get("purpose", {}).get("protected_skeleton", ["relational_schema"]))
    classif.setdefault("data_posture", "at_rest")
    classif.setdefault("mathematical_posture", "operational")
    v1["classification"] = classif

    # Purpose
    purpose = dict(doc.get("purpose", {}))
    purpose.setdefault("excludes_anomaly", quad.get("anomaly_exclusion", ""))
    purpose.setdefault("preserves_invariant", "")
    purpose.setdefault("protected_skeleton", ["relational_schema"])
    purpose.setdefault("erased_structure", [])
    purpose.setdefault("non_claims", ["does not imply external authorization"])
    v1["purpose"] = purpose

    # Declarations, Evidence, Validation
    v1["declarations_required"] = list(doc.get("declarations_required", []))
    v1["evidence_required"] = list(doc.get("evidence_required", []))
    v1["validation_criteria"] = list(doc.get("validation_criteria", []))

    # Routes
    v1["terminal_routes"] = list(doc.get("terminal_routes", []))
    v1["terminal_route_map"] = dict(doc.get("terminal_route_map") or doc.get("canonical_terminal_map", {}))

    # Certification
    cert = dict(doc.get("certification", {}))
    cert.setdefault("certificate_required", False)
    cert.setdefault("certificate_kind", None)
    cert.setdefault("obstruction_class_required", False)
    cert.setdefault("loss_ledger_required", False)
    cert.setdefault("loss_ledger_trigger_id", None)
    cert.setdefault("verifier_required", False)
    v1["certification"] = cert

    # Authorization
    auth = dict(doc.get("authorization", {}))
    auth.setdefault("authorized_by", None)
    auth["certified_implies_authorized"] = False
    v1["authorization"] = auth

    # Extensions
    exts = dict(doc.get("extensions", {}))
    if "definition" in doc:
        exts["definition"] = doc["definition"]
    if "quadrilateral" in doc and "quadrilateral" not in exts.get("definition", {}):
        exts["quadrilateral"] = doc["quadrilateral"]
    if exts:
        v1["extensions"] = exts

    return v1


# =============================================================================
# Unified Contract Dispatcher
# =============================================================================


def validate_contract(
    doc: Any,
    standard: dict | None = None,
    schema_v1: dict | None = None,
    path: Path | None = None,
    index_data: dict | None = None,
) -> list[Finding]:
    """Unified validation entrypoint dispatching by schema_version."""
    if not isinstance(doc, dict):
        label = path.name if path else "contract"
        return [Finding(label, "document", "the file does not hold a mapping")]

    standard = standard or (load_yaml(STANDARD_PATH) if STANDARD_PATH.is_file() else {})
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


def check_catalog(
    catalog: Path | None = None,
    standard_path: Path | None = None,
    index_path: Path | None = None,
) -> list[Finding]:
    catalog = catalog or CONTRACTS_DIR
    standard_path = standard_path or STANDARD_PATH
    index_path = index_path or INDEX_PATH

    findings: list[Finding] = []
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
            pass

    seen: dict[str, str] = {}
    paths = sorted(catalog.glob("nf.*.yaml"))
    if not paths:
        findings.append(Finding(catalog.name, "catalog", "no nf.*.yaml contracts were found"))
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
                    Finding(path.name, "duplicate_id", f"{contract_id} is also declared by {previous}")
                )
            else:
                seen[contract_id] = path.name
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check normal-form contracts against the standard.")
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
