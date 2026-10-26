"""Pinned native OEWAS truth-boundary detector through the canonical OS host.

The compiled snapshot is a bounded detector deployment, not legacy human admission.
Python validates semantic subject identity; Rust independently binds exact raw bytes.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from omega_engine_woland.domain.estate_ports import AntiSkillDecisionV1
from omega_engine_woland.domain.evidence import is_sha256_ref
from omega_engine_woland.domain.specialization import PortName
from omega_engine_operads.domain.anti_skills.anti_skill_v2 import (
    AntiSkillSubjectV1,
    canonical_json_bytes,
)

from .probe_support import observed

_LOCUS = "omega_engine_woland.infrastructure.estates.oewas_native_anti_skill"
_REQUEST = "omega.native.anti-skill-request.v1"
_STAGES = ("PRE_DISPATCH", "POST_PRODUCTION", "PRE_SELECTION", "PRE_SEAL")
_SPECS = (
    "truth-bounded-as-unrestricted",
    "truth-model-self-certification",
    "truth-proposal-authority-collapse",
)
_SNAPSHOT_FIELDS = frozenset(
    (
        "schema_version",
        "profile_id",
        "registry_id",
        "activation_profile_digest",
        "implementation_digest",
        "active_spec_ids",
        "subject_scopes",
        "supported_stages",
        "spec_documents_sha256",
        "authority_effect",
        "can_authorize",
    )
)
_DECISION_FIELDS = frozenset(
    (
        "schema_version",
        "task_key",
        "stage",
        "subject_id",
        "subject_raw_sha256",
        "registry_id",
        "activation_profile_digest",
        "implementation_digest",
        "hit_ids",
        "hit_spec_ids",
        "disposition",
        "receipt_id",
        "authority_effect",
        "can_authorize",
    )
)


def _sha(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _closed(value: Any, fields: frozenset[str]) -> dict[str, Any]:
    if type(value) is not dict or set(value) != fields:
        raise ValueError("native wire has missing or unknown fields")
    if value["authority_effect"] != "None" or value["can_authorize"] is not False:
        raise ValueError("native detector cannot carry authority")
    return value


@dataclass(frozen=True, slots=True)
class NativeAntiSkillSnapshot:
    registry_id: str
    activation_profile_digest: str
    implementation_digest: str
    spec_documents_sha256: tuple[tuple[str, str], ...]

    @classmethod
    def decode(cls, value: Any) -> NativeAntiSkillSnapshot:
        wire = _closed(value, _SNAPSHOT_FIELDS)
        expected = {
            "schema_version": "omega.native.anti-skill-snapshot.v1",
            "profile_id": "woland-truth-boundary-native-v1",
            "active_spec_ids": list(_SPECS),
            "subject_scopes": ["candidate_patch", "candidate_result", "woland_bout_dispatch"],
            "supported_stages": list(_STAGES),
        }
        if any(wire[k] != v for k, v in expected.items()):
            raise ValueError("unsupported native detector profile")
        pins = tuple(
            wire[k] for k in ("registry_id", "activation_profile_digest", "implementation_digest")
        )
        documents = wire["spec_documents_sha256"]
        if type(documents) is not dict or set(documents) != set(_SPECS):
            raise ValueError("native snapshot must bind all three specification bytes")
        if not all(is_sha256_ref(v) for v in (*pins, *documents.values())):
            raise ValueError("native snapshot requires content-addressed pins")
        return cls(*pins, tuple(sorted(documents.items())))


def _invoke(host: RustSymbolGameHost, payload: dict[str, Any]) -> Result[Any, Refusal]:
    outcome = host.invoke_runtime("anti_skill_detect", payload)
    if isinstance(outcome, Err):
        return outcome
    if not isinstance(outcome, Ok) or type(outcome.value) is not dict:
        return Err(Refusal("NATIVE_ANTI_SKILL_INVALID", "host returned no outcome", _LOCUS))
    if outcome.value.get("success") is not True:
        return Err(
            Refusal(
                "NATIVE_ANTI_SKILL_REFUSED",
                str(outcome.value.get("error", "native refusal")),
                _LOCUS,
            )
        )
    return Ok(outcome.value.get("result"))


def _check_binary(binary: Path, expected: str) -> None:
    if type(expected) is not str or not is_sha256_ref("sha256:" + expected):
        raise ValueError("an explicit lowercase binary SHA-256 is required")
    if hashlib.sha256(binary.read_bytes()).hexdigest() != expected:
        raise ValueError("native binary differs from its explicit deployment pin")


def _task_key(subject: AntiSkillSubjectV1) -> str:
    tasks = [v[5:] for v in subject.evidence_scope if v.startswith("task:")]
    requests = [v[8:] for v in subject.evidence_scope if v.startswith("request:")]
    if len(tasks) != 1 or not tasks[0] or len(requests) != 1 or not is_sha256_ref(requests[0]):
        raise ValueError("native subject needs one exact task and request digest")
    return tasks[0]


def _decision(
    value: Any, payload: dict[str, Any], snapshot: NativeAntiSkillSnapshot
) -> AntiSkillDecisionV1:
    wire = _closed(value, _DECISION_FIELDS)
    expected = {
        k: payload[k]
        for k in (
            "task_key",
            "stage",
            "subject_id",
            "subject_raw_sha256",
            "registry_id",
            "activation_profile_digest",
            "implementation_digest",
        )
    }
    expected["schema_version"] = "omega.native.anti-skill-decision.v1"
    if any(wire[k] != v for k, v in expected.items()):
        raise ValueError("native decision does not bind this exact request and deployment")
    receipt_body = {k: v for k, v in wire.items() if k != "receipt_id"}
    if wire["receipt_id"] != _sha(canonical_json_bytes(receipt_body)):
        raise ValueError("native decision receipt digest mismatch")
    hits, specs = wire["hit_ids"], wire["hit_spec_ids"]
    if type(hits) is not list or type(specs) is not list:
        raise ValueError("native hits must be arrays")
    if not all(is_sha256_ref(v) for v in hits) or len(set(hits)) != len(hits):
        raise ValueError("native hit identities are invalid")
    if any(type(v) is not str or v not in _SPECS for v in specs):
        raise ValueError("native decision names an unsupported detector")
    if len(hits) != len(specs) or len(set(specs)) != len(specs):
        raise ValueError("native hit and specification identities disagree")
    if specs:
        expected_disposition = "REFUSE" if any(v != _SPECS[0] for v in specs) else "HOLD"
        if wire["disposition"] != expected_disposition:
            raise ValueError("native disposition contradicts detector evidence")
    elif wire["disposition"] not in ("CLEAR", "HOLD"):
        raise ValueError("native disposition has no detector evidence")
    return AntiSkillDecisionV1(
        stage=wire["stage"],
        subject_id=wire["subject_id"],
        disposition=wire["disposition"],
        registry_id=snapshot.registry_id,
        activation_profile_digest=snapshot.activation_profile_digest,
        hit_ids=tuple(hits),
        receipt_id=wire["receipt_id"],
    )


@dataclass(frozen=True, slots=True)
class NativeOeopAntiSkillAdapter:
    binary: Path
    expected_binary_sha256: str
    snapshot: NativeAntiSkillSnapshot
    host: RustSymbolGameHost
    estate = EstateName.OEWAS
    port = PortName.OEWAS_ANTI_SKILL
    adapter_id = "oewas.native.truth-boundary.v1"

    def evaluate(
        self, stage: str, subject: Mapping[str, Any]
    ) -> Result[AntiSkillDecisionV1, Refusal]:
        try:
            _check_binary(self.binary, self.expected_binary_sha256)
            parsed = AntiSkillSubjectV1.from_dict(subject)
            if stage not in _STAGES:
                raise ValueError("unsupported anti-skill stage")
            raw = canonical_json_bytes(parsed.to_dict())
            payload = {
                "schema_version": _REQUEST,
                "operation": "evaluate",
                "task_key": _task_key(parsed),
                "stage": stage,
                "subject_id": parsed.subject_id,
                "subject_json": raw.decode("utf-8"),
                "subject_raw_sha256": _sha(raw),
                "registry_id": self.snapshot.registry_id,
                "activation_profile_digest": self.snapshot.activation_profile_digest,
                "implementation_digest": self.snapshot.implementation_digest,
            }
            evaluated = _invoke(self.host, payload)
            if isinstance(evaluated, Err):
                return evaluated
            return Ok(_decision(evaluated.value, payload, self.snapshot))
        except (OSError, KeyError, TypeError, ValueError) as exc:
            return Err(Refusal("NATIVE_ANTI_SKILL_BINDING_INVALID", str(exc), _LOCUS))

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        subject = AntiSkillSubjectV1(
            claim_scope=("candidate_result",),
            evidence_scope=("task:native-gate-probe", "request:sha256:" + "a" * 64),
            producer_identity="woland.connection_probe",
            verifier_identity="omega_symbol_game.woland_bout",
            claim_mode="PROPOSAL",
            requested_effect="NONE",
            nonclaims=("A connection probe carries no authority.",),
        )
        evaluated = self.evaluate("PRE_SEAL", subject.to_dict())
        if isinstance(evaluated, Err):
            return disconnected(self.estate, self.port, self.adapter_id, evaluated.error.code)
        return observed(
            self.estate,
            self.port,
            self.adapter_id,
            canonical_json_bytes(asdict(evaluated.value)),
            "real native evaluation under an explicitly pinned detector deployment",
        )


def load_native_anti_skill_gate(
    binary_path: Path | str, expected_binary_sha256: str
) -> Result[NativeOeopAntiSkillAdapter, Refusal]:
    """Load a compiled profile from an explicitly pinned operator-selected binary."""
    try:
        binary = Path(binary_path).resolve()
        _check_binary(binary, expected_binary_sha256)
        host = RustSymbolGameHost(binary=binary, timeout_seconds=15.0)
        described = _invoke(host, {"schema_version": _REQUEST, "operation": "describe"})
        if isinstance(described, Err):
            return described
        snapshot = NativeAntiSkillSnapshot.decode(described.value)
        return Ok(NativeOeopAntiSkillAdapter(binary, expected_binary_sha256, snapshot, host))
    except (OSError, KeyError, TypeError, ValueError) as exc:
        return Err(Refusal("NATIVE_ANTI_SKILL_DEPLOYMENT_INVALID", str(exc), _LOCUS))


__all__ = ["NativeOeopAntiSkillAdapter", "load_native_anti_skill_gate"]
