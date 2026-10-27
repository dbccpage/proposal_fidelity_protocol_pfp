"""The OEWAS anti-skill gate as the Adversary anti-skill port.

The gate detects; it never repairs, admits or activates. It runs only over a verified,
profile-scoped immutable runtime snapshot supplied by the composition root. Without one the gate holds
every subject (disposition ``HOLD``) and the probe reports the port disconnected: the
Python truth-boundary loader is retired. Explicit native deployments use
``load_native_anti_skill_gate`` and inject the resulting adapter at the composition root.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from adversary.domain.estate_ports import AntiSkillDecisionV1
from adversary.domain.specialization import PortName
from adversary.profile.anti_skill import evaluate_adversary_anti_skill_gate
from operads.application.anti_skill.anti_skill_v2 import (
    ActiveAntiSkillRuntimeV1,
)
from operads.domain.anti_skills.anti_skill_v2 import (
    AntiSkillSubjectV1,
)

from .probe_support import canonical_bytes, observed, refusal, run_probe

_LOCUS = "adversary.infrastructure.estates.oewas_anti_skill"
_PROBE_SUBJECT = {
    "claim_scope": ["candidate_result"],
    "evidence_scope": ["adversary_bout_receipt"],
    "producer_identity": "adversary.connection_probe",
    "verifier_identity": "core_symbol_game.adversary_bout",
    "claim_mode": "PROPOSAL",
    "requested_effect": "NONE",
    "approval_reference": "",
    "nonclaims": ["A connection probe carries no authority."],
}


@dataclass(frozen=True, slots=True)
class OeopAntiSkillAdapter:
    estate = EstateName.OEWAS
    port = PortName.OEWAS_ANTI_SKILL
    adapter_id = "oewas.anti_skill_v2"
    runtime: ActiveAntiSkillRuntimeV1 | None = None

    def __post_init__(self) -> None:
        if self.runtime is not None and type(self.runtime) is not ActiveAntiSkillRuntimeV1:
            raise TypeError("runtime must be an exact ActiveAntiSkillRuntimeV1 or None")

    def evaluate(
        self, stage: str, subject: Mapping[str, Any]
    ) -> Result[AntiSkillDecisionV1, Refusal]:
        # The existing closed wire decoder validates all fields and the supplied identity.
        try:
            parsed = AntiSkillSubjectV1.from_dict(subject)
            receipt = evaluate_adversary_anti_skill_gate(
                stage=stage, subject=parsed, runtime=self.runtime
            )
            return Ok(
                AntiSkillDecisionV1(
                    stage=receipt.stage,
                    subject_id=receipt.subject_id,
                    disposition=receipt.disposition,
                    registry_id=receipt.registry_id,
                    hit_ids=receipt.hit_ids,
                    receipt_id=receipt.receipt_id,
                    activation_profile_digest=receipt.activation_profile_digest,
                )
            )
        except (KeyError, TypeError, ValueError) as exc:
            return Err(refusal("ANTI_SKILL_SUBJECT_INVALID", exc, _LOCUS))

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            if self.runtime is None:
                return disconnected(
                    self.estate,
                    self.port,
                    self.adapter_id,
                    "NO_VERIFIED_RUNTIME: the gate holds every subject",
                )
            probe_subject = AntiSkillSubjectV1(
                claim_scope=tuple(_PROBE_SUBJECT["claim_scope"]),
                evidence_scope=tuple(_PROBE_SUBJECT["evidence_scope"]),
                producer_identity=_PROBE_SUBJECT["producer_identity"],
                verifier_identity=_PROBE_SUBJECT["verifier_identity"],
                claim_mode=_PROBE_SUBJECT["claim_mode"],
                requested_effect=_PROBE_SUBJECT["requested_effect"],
                approval_reference=_PROBE_SUBJECT["approval_reference"],
                nonclaims=tuple(_PROBE_SUBJECT["nonclaims"]),
            )
            decided = self.evaluate("PRE_SEAL", probe_subject.to_dict())
            if isinstance(decided, Err):
                return disconnected(self.estate, self.port, self.adapter_id, decided.error.code)
            decision = decided.value
            if not decision.registry_id:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "the receipt names no registry"
                )
            return observed(
                self.estate,
                self.port,
                self.adapter_id,
                canonical_bytes(
                    {
                        "receipt_id": decision.receipt_id,
                        "registry_id": decision.registry_id,
                        "disposition": decision.disposition,
                        "hit_ids": list(decision.hit_ids),
                    }
                ),
                f"evaluated one subject against registry {decision.registry_id}",
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)


__all__ = ["OeopAntiSkillAdapter"]
