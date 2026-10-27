"""Native WDP certificate replay and byte-compatible local receipt custody.

The active kernel/P1 path imports no paper runtime and never falls back from an
unavailable native checker. Issuance binds bytes; it does not check mathematics.
AuthorityEffect: None.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from fractions import Fraction
from math import isfinite
from pathlib import Path
from typing import Any

from operating_system.adapters.rust_host import RustSymbolGameHost
from operations.domain.rop.result import Err

from .contracts import (
    CertificateChecker,
    CheckReceipt,
    ReceiptIssuer,
    ReceiptRecord,
    TypedRefusal,
)

PILOT_ARENA_TASK_ID = "pilot-g5-provenance-repair-loop"
PILOT_ARENA_USABLE_BUDGET = "3"
CHECKER_PROFILE = "wdp-finite-belief-model-v1/native-replay-v1"
CHECKER_SOURCE = Path(__file__).resolve().parents[3] / "engine/crates_rs/core_wdp/src/application_kernel.rs"

def canonical_data(value: Any) -> Any:
    """Convert supported objects into typed deterministic JSON data.

    Every non-primitive shape has an explicit type envelope.  In particular,
    a user mapping can never collide with the internal representation of a
    fraction, byte string, complex number, enum, dataclass, or container.
    """

    if is_dataclass(value) and not isinstance(value, type):
        return {
            "__wdp_type__": "dataclass",
            "class": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": [
                [field.name, canonical_data(getattr(value, field.name))]
                for field in fields(value)
            ],
        }
    if isinstance(value, Enum):
        return {
            "__wdp_type__": "enum",
            "class": f"{type(value).__module__}.{type(value).__qualname__}",
            "value": canonical_data(value.value),
        }
    if isinstance(value, Fraction):
        return {
            "__wdp_type__": "fraction",
            "denominator": value.denominator,
            "numerator": value.numerator,
        }
    if isinstance(value, complex):
        if not isfinite(value.real) or not isfinite(value.imag):
            raise TypeError("canonical complex values must have finite components")
        real = 0.0 if value.real == 0 else value.real
        imag = 0.0 if value.imag == 0 else value.imag
        return {
            "__wdp_type__": "complex",
            "imag_hex": imag.hex(),
            "real_hex": real.hex(),
        }
    if isinstance(value, bytes):
        return {"__wdp_type__": "bytes", "hex": value.hex()}
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("canonical mappings require string keys; keys are never coerced")
        return {
            "__wdp_type__": "mapping",
            "items": [
                [key, canonical_data(item)]
                for key, item in sorted(value.items())
            ],
        }
    if isinstance(value, (set, frozenset)):
        converted = [canonical_data(item) for item in value]
        converted.sort(
            key=lambda item: json.dumps(
                item, ensure_ascii=True, separators=(",", ":"), sort_keys=True
            )
        )
        return {
            "__wdp_type__": "frozenset" if isinstance(value, frozenset) else "set",
            "items": converted,
        }
    if isinstance(value, list):
        return {"__wdp_type__": "list", "items": [canonical_data(item) for item in value]}
    if isinstance(value, tuple):
        return {"__wdp_type__": "tuple", "items": [canonical_data(item) for item in value]}
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")

def content_hash(value):
    raw = json.dumps(canonical_data(value), ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def model_json_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _artifact_digest(value: object) -> str:
    """Compute a 64-char hex SHA-256 digest matching certified_progress.model.digest when valid."""
    try:
        return model_json_digest(value)
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        return content_hash(value)
    except (TypeError, ValueError, ZeroDivisionError, OverflowError):
        return hashlib.sha256(f"{type(value).__qualname__}:{repr(value)}".encode("utf-8")).hexdigest()

def to_receipt_record(receipt) -> ReceiptRecord:
    """Read a retained external receipt into the unchanged local DTO."""
    if isinstance(receipt, dict) or not all(hasattr(receipt, k) for k in ReceiptRecord.model_fields):
        raise TypeError(f"Expected Receipt, got {type(receipt)}")
    return ReceiptRecord(**{k: ("None" if k == "authority_effect" else getattr(receipt, k))
                            for k in ReceiptRecord.model_fields})

def from_receipt_record(record: ReceiptRecord) -> ReceiptRecord:
    """Compatibility mapping retains the local wire DTO without paper imports."""
    if not isinstance(record, ReceiptRecord):
        raise TypeError(f"Expected ReceiptRecord, got {type(record)}")
    return record

def to_typed_refusal(refused) -> TypedRefusal:
    if not hasattr(refused, "code") or not hasattr(refused, "detail"):
        raise TypeError(f"Expected Refused, got {type(refused)}")
    code = refused.code.value if hasattr(refused.code, "value") else str(refused.code)
    return TypedRefusal(code=code, reason=refused.detail)

def to_check_receipt(
    raw_receipt: Mapping[str, object], *, model: object, certificate: object
) -> CheckReceipt:
    """Map a certified_progress.check_certificate dict onto a kernel CheckReceipt."""
    if not isinstance(raw_receipt, Mapping):
        raise TypeError(f"Expected Mapping from check_certificate, got {type(raw_receipt)}")
    accepted = raw_receipt.get("accepted")
    if not isinstance(accepted, bool):
        raise ValueError("Expected boolean 'accepted' field in check_certificate output")

    certificate_digest = _artifact_digest(certificate)
    raw_model_digest = raw_receipt.get("model_digest")
    model_digest = (
        raw_model_digest
        if isinstance(raw_model_digest, str) and len(raw_model_digest) == 64
        else _artifact_digest(model)
    )

    if not accepted:
        reason = raw_receipt.get("reason")
        failure = reason if isinstance(reason, str) and reason else "certificate check refused"
        return CheckReceipt(
            accepted=False,
            model_digest=model_digest,
            certificate_digest=certificate_digest,
            failures=(failure,),
            authority_effect="None",
        )

    claim = raw_receipt.get("claim")
    if claim == "LOSS":
        termination = raw_receipt.get("termination")
        if termination not in ("Stalled", "Trapped"):
            raise ValueError(f"Unexpected LOSS termination in check_certificate output: {termination!r}")
        return CheckReceipt(
            accepted=True,
            model_digest=model_digest,
            certificate_digest=certificate_digest,
            claim="LOSS",
            initial_stalled=(termination == "Stalled"),
            authority_effect="None",
        )

    if claim in ("WIN_OPTIMAL", "WIN_FEASIBLE"):
        initial_value = raw_receipt.get("initial_value")
        if not isinstance(initial_value, str):
            raise ValueError("Accepted WIN receipt requires string initial_value")
        return CheckReceipt(
            accepted=True,
            model_digest=model_digest,
            certificate_digest=certificate_digest,
            claim=claim,
            initial_value=initial_value,
            authority_effect="None",
        )

    raise ValueError(f"Unexpected claim in accepted check_certificate output: {claim!r}")

class WdpReceiptIssuer:
    """Historical canonical custody bytes, independent of certificate checking."""
    def __init__(self, implementation_version="0.1.0"):
        self.implementation_version = implementation_version

    @staticmethod
    def _body(record):
        return {k: (list(record.claim_ids) if k == "claim_ids" else getattr(record, k))
                for k in ("authority_effect", "claim_ids", "implementation_version",
                          "input_digest", "output_digest", "subject")}

    def issue(self, subject, inputs, output, claim_ids):
        if (not isinstance(subject, str) or not subject or
            not isinstance(self.implementation_version, str) or not self.implementation_version or
            type(claim_ids) is not tuple or not claim_ids or
            any(not isinstance(c, str) or not c for c in claim_ids)):
            return TypedRefusal(code="invalid_input", reason="subject, version, and nonempty claim ids are required")
        try:
            payload = dict(subject=subject, input_digest=content_hash(inputs), output_digest=content_hash(output),
                claim_ids=tuple(sorted(set(claim_ids))), implementation_version=self.implementation_version,
                authority_effect="None")
            return ReceiptRecord(**payload, receipt_digest=content_hash({**payload, "claim_ids": list(payload["claim_ids"])}))
        except (TypeError, ValueError, ZeroDivisionError, OverflowError):
            return TypedRefusal(code="invalid_input", reason="receipt inputs and output must be canonicalizable")

    def verify(self, receipt, inputs, output):
        if not isinstance(receipt, ReceiptRecord):
            return TypedRefusal(code="invalid_input", reason="receipt has the wrong type")
        if receipt.receipt_digest != content_hash(self._body(receipt)):
            return TypedRefusal(code="receipt_mismatch", reason="receipt body was modified")
        try:
            input_digest, output_digest = content_hash(inputs), content_hash(output)
        except (TypeError, ValueError, ZeroDivisionError, OverflowError):
            return TypedRefusal(code="invalid_input", reason="receipt inputs and output must be canonicalizable")
        if receipt.input_digest != input_digest:
            return TypedRefusal(code="digest_mismatch", reason="input artifact differs from receipt")
        if receipt.output_digest != output_digest:
            return TypedRefusal(code="digest_mismatch", reason="output artifact differs from receipt")
        return True

class WdpCertificateChecker:
    """Independent finite certificate replay through the existing OEOS host.

    Missing transport or mismatched current checker source returns a rejected
    CheckReceipt, never a Python computation or replacement certificate.
    """
    def __init__(self, native_host=None, *, checker_source=CHECKER_SOURCE):
        self.native_host = native_host if native_host is not None else RustSymbolGameHost()
        self.checker_source = Path(checker_source)

    def check(self, model, certificate):
        def refused(reason):
            return to_check_receipt({"accepted": False, "reason": reason}, model=model, certificate=certificate)
        try:
            model_digest, certificate_digest = model_json_digest(model), model_json_digest(certificate)
            source_digest = hashlib.sha256(self.checker_source.read_bytes()).hexdigest()
            reply = self.native_host.invoke_runtime("wdp_certificate_check", {"model": model, "certificate": certificate})
            if isinstance(reply, Err):
                return refused("WDP_NATIVE_UNAVAILABLE: " + reply.error.code)
            wire = reply.value
            if type(wire) is not dict:
                return refused("WDP_NATIVE_BINDING_MISMATCH")
            if wire.get("success") is not True:
                return refused("WDP_NATIVE_REFUSED: " + str(wire.get("error")))
            result = wire["result"]
            if type(result) is not dict or type(result.get("check")) is not dict:
                return refused("WDP_NATIVE_BINDING_MISMATCH")
            if (result.get("checker_profile") != CHECKER_PROFILE or
                result.get("checker_source_sha256") != source_digest or
                result.get("model_digest") != model_digest or
                result.get("certificate_digest") != certificate_digest or
                result.get("authority_effect") != "None"):
                return refused("WDP_NATIVE_BINDING_MISMATCH")
            if (hashlib.sha256(self.checker_source.read_bytes()).hexdigest() != source_digest or
                (result["check"].get("accepted") is True and
                 result["check"].get("model_digest") != model_digest)):
                return refused("WDP_NATIVE_BINDING_MISMATCH")
            return to_check_receipt(result["check"], model=model, certificate=certificate)
        except (OSError, TypeError, ValueError, OverflowError, KeyError) as exc:
            return refused("WDP_NATIVE_UNAVAILABLE: " + str(exc))

_PILOT_ARENA_JSON = '{"actions":["issue_receipt","manual_audit","repair_provenance","run_g5_gate"],"assumptions":["A1","A2","A4","A5","A6"],"authorization":{"effect":"None"},"costs":[{"action":"manual_audit","belief":["draft"],"cost":"5"},{"action":"run_g5_gate","belief":["draft"],"cost":"1"},{"action":"issue_receipt","belief":["gated"],"cost":"1"},{"action":"repair_provenance","belief":["rejected"],"cost":"1"}],"emissions":{"issue_receipt":"emit_verified_claim"},"enabled":{"draft":["manual_audit","run_g5_gate"],"gated":["issue_receipt"],"rejected":["repair_provenance"],"verified":[]},"initial":["draft"],"reports":[{"action":"repair_provenance","observation":"gated","state":"gated"},{"action":"run_g5_gate","observation":"gated","state":"gated"},{"action":"run_g5_gate","observation":"rejected","state":"rejected"},{"action":"issue_receipt","observation":"verified","state":"verified"},{"action":"manual_audit","observation":"verified","state":"verified"}],"resolutions":["emit_verified_claim"],"schema":"wdp-finite-belief-model-v1","states":["draft","gated","rejected","verified"],"targets":[["verified"]],"task_id":"pilot-g5-provenance-repair-loop","transitions":[{"action":"manual_audit","state":"draft","successors":["verified"]},{"action":"run_g5_gate","state":"draft","successors":["gated","rejected"]},{"action":"issue_receipt","state":"gated","successors":["verified"]},{"action":"repair_provenance","state":"rejected","successors":["gated"]}],"valid_resolutions":{"draft":[],"gated":["emit_verified_claim"],"rejected":[],"verified":["emit_verified_claim"]}}'

def declare_pilot_agent_loop_arena():
    """Return the retained public finite declaration; no search or checker call."""
    return json.loads(_PILOT_ARENA_JSON)

def pilot_agent_loop_certificate(arena: dict[str, object] | None = None) -> dict[str, object]:
    """Return the static WIN_OPTIMAL progress certificate for the pilot arena without calling producer."""
    model = declare_pilot_agent_loop_arena() if arena is None else arena
    return {
        "schema": "wdp-progress-certificate-v1",
        "kind": "WIN_OPTIMAL",
        "model_digest": model_json_digest(model),
        "task_id": PILOT_ARENA_TASK_ID,
        "assumptions": ["A1", "A2", "A4", "A5", "A6"],
        "authorization": {"effect": "None"},
        "initial": ["draft"],
        "winning": [["draft"], ["gated"], ["rejected"], ["verified"]],
        "losing": [],
        "stalled": [],
        "closure": [],
        "strategy": [
            {"belief": ["draft"], "action": "run_g5_gate"},
            {"belief": ["gated"], "action": "issue_receipt"},
            {"belief": ["rejected"], "action": "repair_provenance"},
        ],
        "ranks": [
            {"belief": ["draft"], "rank": 3},
            {"belief": ["gated"], "rank": 1},
            {"belief": ["rejected"], "rank": 2},
            {"belief": ["verified"], "rank": 0},
        ],
        "values": [
            {"belief": ["draft"], "value": "3"},
            {"belief": ["gated"], "value": "1"},
            {"belief": ["rejected"], "value": "2"},
            {"belief": ["verified"], "value": "0"},
        ],
        "resolutions": [
            {"belief": ["gated"], "resolution": "emit_verified_claim"},
            {"belief": ["verified"], "resolution": "emit_verified_claim"},
        ],
        "optimality_requested": True,
    }

def evaluate_pilot_kernel_kill_conditions(
    certificate: dict[str, object] | None = None,
) -> dict[str, object]:
    """Evaluate PROD-KERNEL-KILL on the pilot G.5 provenance-repair workflow.

    A native certificate result determines the finite-arena condition; missing
    transport or source binding leaves it undecided (None), not killed or passed.
    Local receipt custody replay is evaluated separately and does not establish
    the native certificate's mathematics. A known kill dominates the aggregate;
    otherwise any undecided condition leaves the aggregate undecided.
    AuthorityEffect: None.
    """
    arena = declare_pilot_agent_loop_arena()
    cert = pilot_agent_loop_certificate(arena) if certificate is None else certificate
    checker = WdpCertificateChecker()
    check_rec = checker.check(arena, cert)
    native_check_failures = tuple(
        reason for reason in check_rec.failures
        if reason.startswith(("WDP_NATIVE_UNAVAILABLE", "WDP_NATIVE_BINDING_MISMATCH", "WDP_NATIVE_REFUSED"))
    )
    arena_has_usable_budget = (
        check_rec.accepted
        and check_rec.claim == "WIN_OPTIMAL"
        and check_rec.initial_value == PILOT_ARENA_USABLE_BUDGET
    )

    issuer = WdpReceiptIssuer()
    check_payload = check_rec.model_dump(mode="json")
    receipt = issuer.issue(
        PILOT_ARENA_TASK_ID,
        arena,
        check_payload,
        ("WDP-CHS-P04", "WDP-CHS-P18"),
    )
    downstream_replayed = (
        isinstance(receipt, ReceiptRecord)
        and issuer.verify(receipt, arena, check_payload) is True
    )

    kill_no_finite_arena = None if native_check_failures else not arena_has_usable_budget
    kill_receipts_unreplayed = not downstream_replayed
    kill_conditions = (kill_no_finite_arena, kill_receipts_unreplayed)
    any_kill = (
        True if any(condition is True for condition in kill_conditions)
        else None if any(condition is None for condition in kill_conditions)
        else False
    )
    return {
        "goal_id": "PROD-KERNEL-KILL",
        "task_id": PILOT_ARENA_TASK_ID,
        "usable_budget": PILOT_ARENA_USABLE_BUDGET,
        "initial_value": check_rec.initial_value,
        "check_receipt": check_rec,
        "native_check_status": "UNAVAILABLE" if native_check_failures else "REPLAYED",
        "native_check_failures": native_check_failures,
        "receipt_record": receipt,
        "kill_no_finite_arena": kill_no_finite_arena,
        "kill_receipts_unreplayed": kill_receipts_unreplayed,
        "any_kill_condition_holds": any_kill,
        "authority_effect": check_rec.authority_effect,
    }

_check_protocol: ReceiptIssuer = WdpReceiptIssuer()
_check_certificate_protocol: CertificateChecker = WdpCertificateChecker()
