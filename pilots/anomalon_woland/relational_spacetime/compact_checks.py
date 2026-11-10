"""Strict ingress and independent finite checks for the new small PO035 recipe.

The calculation binding checks exact typed field agreement, not the displayed
formula, its evaluation or the analytical argument. The unchanged sovereign
predicates receive only the certificate actually present in the model's packet.
No historical SPK parsed-response object is constructed or accepted here.
"""

import copy
import json
from fractions import Fraction

import jsonschema

from omega_engine_pfp.domain.contracts.pfp_calculations import (
    calculation_binding_failures,
    same_typed_value,
)

from omega_engine_woland.infrastructure.providers.wire import decode_reply

from omega_engine_woland.tests.pilots.relational_spacetime.tasks import BY_ID
from omega_engine_woland.tests.pilots.relational_spacetime.tasks import proposal_body
from omega_engine_woland.tests.pilots.relational_spacetime.finite_checks import CHECKS
from omega_engine_pfp.infrastructure.numbered_prompts import FIELD_CARRIERS
from omega_engine_pfp.infrastructure.numbered_prompts import response_schema
from omega_engine_pfp.infrastructure.numbered_prompts import workpad_schema

CLAIM_LIMITS = (
    "Field binding establishes structural consistency only; expressions are unverified.",
    "The finite certificate check does not certify the analytical derivation or a general theorem.",
    "A typed refusal or a valid public workpad is not mathematical success.",
)

# JSON Schema permits 1.0 as an integer. This ingress deliberately requires the
# original JSON integer type, including at nested vector leaves.
_STRICT_VALIDATOR = jsonschema.validators.extend(
    jsonschema.Draft202012Validator,
    type_checker=jsonschema.Draft202012Validator.TYPE_CHECKER.redefine(
        "integer", lambda _checker, value: type(value) is int
    ),
)


def _verdict():
    return dict(
        schema_status="REFUSED",
        binding_status="NOT_CHECKED",
        certificate_status="NOT_CHECKED",
        analytical_status="UNVERIFIED",
        expression_status="UNVERIFIED",
        accepted=False,
        code="INVALID_JSON",
        binding_code="NOT_CHECKED",
        certificate_code="NOT_CHECKED",
        claim_limits=list(CLAIM_LIMITS),
    )


def _certificate_verdict(pilot, certificate):
    try:
        CHECKS[BY_ID[pilot]["number"] - 199](certificate)
    except (ValueError, TypeError, KeyError, ZeroDivisionError, OverflowError) as exc:
        return "REFUSED", str(exc) if isinstance(exc, ValueError) else "MALFORMED_WITNESS"
    return "HOST_ACCEPTED", "FINITE_WITNESS_VALID"


def evaluate(pilot, prompt_id, content, *, workpad=False):
    """Return (verdict, original decoded packet), or None for invalid ingress.

    A schema-valid final packet may retain a failed binding or finite predicate
    verdict for evidence. Both are evaluated independently. Public workpads have
    schema validation only, and never receive a finite or analytical pass.
    """
    if pilot not in BY_ID:
        raise ValueError("UNKNOWN_PO035_PILOT")
    if type(prompt_id) is not str or not prompt_id:
        raise ValueError("INVALID_PROMPT_ID")
    if type(workpad) is not bool:
        raise ValueError("INVALID_WORKPAD_FLAG")
    result = _verdict()
    try:
        raw = content.encode("utf-8") if type(content) is str else content
        payload = dict(decode_reply(raw))
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return result, None
    schema = (workpad_schema if workpad else response_schema)(pilot, prompt_id=prompt_id)
    try:
        _STRICT_VALIDATOR(schema).validate(payload)
    except jsonschema.ValidationError as exc:
        result.update(
            code="SCHEMA_VIOLATION",
            schema_path=list(exc.absolute_path),
            schema_validator=exc.validator,
        )
        return result, None
    if workpad:
        fields = [record["field"] for record in payload["records"]]
        if len(fields) != len(set(fields)):
            result["code"] = "DUPLICATE_WORKPAD_FIELD"
            return result, None
        result.update(schema_status="VALID", code="PUBLIC_WORKPAD_SCHEMA_VALID")
        return result, payload
    result["schema_status"] = "VALID"
    body = proposal_body(payload)
    if body["status"] == "TYPED_REFUSAL":
        # The schema requires BOTH nullable fields to be null in a refusal.
        result["code"] = "TYPED_REFUSAL"
        return result, payload
    certificate, calculations = body["certificate"], body["calculations"]
    failures = calculation_binding_failures(certificate, calculations, FIELD_CARRIERS[pilot])
    result.update(
        binding_status="REFUSED" if failures else "MATCHED",
        binding_code="CALCULATION_CERTIFICATE_MISMATCH" if failures else "FIELDS_MATCHED",
        binding_fields=failures,
    )
    result["certificate_status"], result["certificate_code"] = _certificate_verdict(
        pilot, certificate
    )
    result["accepted"] = not failures and result["certificate_status"] == "HOST_ACCEPTED"
    result["code"] = result["binding_code"] if failures else result["certificate_code"]
    return result, payload


def validate_workpad(pilot, prompt_id, content):
    """Strict small-schema ingress; an invalid public workpad is never retained."""
    return evaluate(pilot, prompt_id, content, workpad=True)


def _changed_leaf(value):
    """Host-only schema-preserving rational perturbation; no solver output."""
    changed = copy.deepcopy(value)
    parent = changed
    if type(changed) is list:
        while type(parent[0]) is list:
            parent = parent[0]
        original = parent[0]
        replacement = str(Fraction(original) + 1)
        parent[0] = replacement if len(replacement) <= 100 else ("0" if Fraction(original) else "1")
    else:
        replacement = str(Fraction(changed) + 1)
        changed = replacement if len(replacement) <= 100 else ("0" if Fraction(changed) else "1")
    return changed


def negative_controls(pilot, prompt_id, payload):
    """Host mutations, kept separate from participant and analytical evidence.

    A binding-only mutation preserves the candidate certificate. A coupled
    mutation preserves binding while requiring rejection by the original judge.
    Controls on an already rejected certificate explicitly retain that baseline.
    """
    if payload is None:
        return dict(checked=False, code="NO_VALID_PROPOSAL")
    baseline, original = evaluate(pilot, prompt_id, json.dumps(payload, allow_nan=False))
    if original is None or proposal_body(original)["status"] != "PROPOSAL":
        return dict(checked=False, code="NO_VALID_PROPOSAL")
    key = ("l1_radius", "residual", "composite_transport", "cosine_before", "primal_norm")[
        BY_ID[pilot]["number"] - 199
    ]
    binding_packet = copy.deepcopy(original)
    binding_body = proposal_body(binding_packet)
    altered = _changed_leaf(binding_body["certificate"][key])
    binding_body["calculations"][key]["result"] = altered
    binding, _ = evaluate(pilot, prompt_id, json.dumps(binding_packet, allow_nan=False))
    coupled_packet = copy.deepcopy(original)
    coupled_body = proposal_body(coupled_packet)
    coupled_body["certificate"][key] = copy.deepcopy(altered)
    # Rebind all fields so this control isolates the sovereign judge even when
    # the original model packet already had a structural inconsistency.
    for field, value in coupled_body["certificate"].items():
        coupled_body["calculations"][field]["result"] = copy.deepcopy(value)
    coupled, _ = evaluate(pilot, prompt_id, json.dumps(coupled_packet, allow_nan=False))
    # A perturbation of an initially wrong value might repair that field. Pick
    # another bounded exact perturbation rather than assuming it is negative.
    if coupled["certificate_status"] == "HOST_ACCEPTED":
        altered = _changed_leaf(altered)
        coupled_body["certificate"][key] = copy.deepcopy(altered)
        coupled_body["calculations"][key]["result"] = copy.deepcopy(altered)
        coupled, _ = evaluate(pilot, prompt_id, json.dumps(coupled_packet, allow_nan=False))
    return dict(
        checked=True,
        original_binding_status=baseline["binding_status"],
        original_certificate_status=baseline["certificate_status"],
        mutated_field=key,
        binding_only=dict(
            kind="HOST_CALCULATION_BINDING_MUTATION",
            checked=True,
            rejected=binding["schema_status"] == "VALID" and binding["binding_status"] == "REFUSED",
            certificate_unchanged=same_typed_value(
                proposal_body(original)["certificate"], binding_body["certificate"]
            ),
            verdict=binding,
        ),
        coupled_wrong_value=dict(
            kind="HOST_COUPLED_CERTIFICATE_AND_CALCULATION_MUTATION",
            checked=True,
            rejected=coupled["schema_status"] == "VALID"
            and coupled["binding_status"] == "MATCHED"
            and coupled["certificate_status"] == "REFUSED",
            verdict=coupled,
        ),
    )
