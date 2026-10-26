"""Regulatory T-Cells (Tregs), Anti-Anti-Skills & Peripheral Tolerance Safeguards.

Monitors detector false-positive rates to prevent autoimmune cognitive paralysis.
Calculates the exact rational Autoimmune Toxicity Index:
    Toxicity = Fraction(firings_with_Signal_1_ALONE, total_triggers)

When Toxicity meets or exceeds tau = Fraction(1, 5), the TregSupervisor synthesizes an
immutable RegulatoryAntibody record that downgrades the detector's authority from
BLOCKING_GATE to DIAGNOSTIC_ONLY.

The threshold is inclusive (decided 2026-09-26). tau is the first intolerable rate: a
detector with one Signal-1-alone firing in five triggers is already paralysing at the
declared rate, and a downgrade keeps the detector reporting rather than deleting it.

Two evaluation modes, with different meanings:
- ``triggers``: explicit (has_signal_1, has_signal_2) pairs; toxicity is a true rate in [0, 1].
- ``prompt_corpus``: a pinned benign corpus carries no Signal 2 by definition, so every firing
  is Signal 1 alone and toxicity is exactly 0 (never fires) or 1 (fires at least once). In this
  mode tau does not matter: any firing on the benign corpus downgrades the detector.

Zero outward dependencies. Strict ZERO-FLOAT law.
Exact-type equality enforced on all Value Objects.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Sequence


def _assert_zero_float(val: Any, field_name: str) -> None:
    if isinstance(val, float):
        raise TypeError(
            f"ZERO-FLOAT Invariant violated on {field_name}: float values are strictly forbidden; "
            "use fractions.Fraction or Q"
        )


class AuthorityLevel(str, Enum):
    """Authority gate tier assigned to an epistemic rule or detector."""

    BLOCKING_GATE = "BLOCKING_GATE"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"


@dataclass(frozen=True, slots=True)
class AutoimmuneToxicityReport:
    """Audit report measuring false-suppression toxicity of a detector rule."""

    rule_id: str
    signal1_only_count: int
    total_triggers: int
    toxicity_index: Fraction

    def __post_init__(self) -> None:
        _assert_zero_float(self.toxicity_index, "toxicity_index")
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise ValueError("rule_id must be a non-empty string")
        if not isinstance(self.signal1_only_count, int) or self.signal1_only_count < 0:
            raise ValueError("signal1_only_count must be non-negative int")
        if not isinstance(self.total_triggers, int) or self.total_triggers < 0:
            raise ValueError("total_triggers must be non-negative int")
        if self.signal1_only_count > self.total_triggers:
            raise ValueError("signal1_only_count cannot exceed total_triggers")
        if not isinstance(self.toxicity_index, Fraction):
            # Check for custom Q
            if hasattr(self.toxicity_index, "num") and hasattr(self.toxicity_index, "den"):
                pass
            else:
                raise TypeError("toxicity_index must be Fraction or Q")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, AutoimmuneToxicityReport)
        return (
            self.rule_id == other.rule_id
            and self.signal1_only_count == other.signal1_only_count
            and self.total_triggers == other.total_triggers
            and self.toxicity_index == other.toxicity_index
        )

    def __hash__(self) -> int:
        return hash((type(self), self.rule_id, self.signal1_only_count, self.total_triggers, self.toxicity_index))


@dataclass(frozen=True, slots=True)
class RegulatoryAntibody:
    """Anti-anti-skill synthesizing peripheral tolerance to suppress hyperactive detectors."""

    treg_id: str
    target_rule_id: str
    downgraded_authority: str = "DIAGNOSTIC_ONLY"
    toxicity_index: Fraction = Fraction(0, 1)
    tau_threshold: Fraction = Fraction(1, 5)
    reason: str = ""
    canonical_hash: str = ""
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _assert_zero_float(self.toxicity_index, "toxicity_index")
        _assert_zero_float(self.tau_threshold, "tau_threshold")
        if not isinstance(self.treg_id, str) or not self.treg_id.strip():
            raise ValueError("treg_id must be a non-empty string")
        if not isinstance(self.target_rule_id, str) or not self.target_rule_id.strip():
            raise ValueError("target_rule_id must be a non-empty string")
        if self.downgraded_authority != "DIAGNOSTIC_ONLY":
            raise ValueError("downgraded_authority must be 'DIAGNOSTIC_ONLY'")
        if self.authority_effect != "None":
            raise ValueError("authority_effect must be 'None'")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, RegulatoryAntibody)
        return (
            self.treg_id == other.treg_id
            and self.target_rule_id == other.target_rule_id
            and self.downgraded_authority == other.downgraded_authority
            and self.toxicity_index == other.toxicity_index
            and self.tau_threshold == other.tau_threshold
            and self.reason == other.reason
            and self.canonical_hash == other.canonical_hash
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.treg_id,
            self.target_rule_id,
            self.downgraded_authority,
            self.toxicity_index,
            self.tau_threshold,
            self.canonical_hash,
            self.authority_effect,
        ))

    @classmethod
    def create(
        cls,
        target_rule_id: str,
        toxicity_index: Fraction,
        tau_threshold: Fraction = Fraction(1, 5),
        reason: str = "",
        treg_id: str = "",
    ) -> RegulatoryAntibody:
        """Create a sealed RegulatoryAntibody."""
        _assert_zero_float(toxicity_index, "toxicity_index")
        _assert_zero_float(tau_threshold, "tau_threshold")
        if not treg_id:
            h_seed = hashlib.sha256(f"TREG:{target_rule_id}:{toxicity_index}".encode("utf-8")).hexdigest()
            treg_id = f"TREG-{h_seed[:12]}"

        if not reason:
            reason = (
                f"Autoimmune toxicity {toxicity_index} meets or exceeds threshold tau = {tau_threshold}. "
                f"Authority downgraded from BLOCKING_GATE to DIAGNOSTIC_ONLY."
            )

        body = {
            "authority_effect": "None",
            "downgraded_authority": "DIAGNOSTIC_ONLY",
            "reason": reason,
            "target_rule_id": target_rule_id,
            "tau_threshold": str(tau_threshold),
            "toxicity_index": str(toxicity_index),
            "treg_id": treg_id,
        }
        canonical_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
        canonical_hash = hashlib.sha256(canonical_bytes).hexdigest()

        return cls(
            treg_id=treg_id,
            target_rule_id=target_rule_id,
            downgraded_authority="DIAGNOSTIC_ONLY",
            toxicity_index=toxicity_index,
            tau_threshold=tau_threshold,
            reason=reason,
            canonical_hash=canonical_hash,
            authority_effect="None",
        )


class TregSupervisor:
    """Regulatory supervisor computing exact rational toxicity and synthesizing Tregs."""

    def __init__(self, tau: Fraction = Fraction(1, 5)) -> None:
        _assert_zero_float(tau, "tau")
        if not isinstance(tau, Fraction):
            if hasattr(tau, "num") and hasattr(tau, "den"):
                tau = Fraction(tau.num, tau.den)
            else:
                raise TypeError(f"tau must be Fraction or Q, got {type(tau).__name__}")
        self.tau = tau

    def evaluate_toxicity(
        self,
        rule_id: str,
        prompt_corpus: Sequence[str] | None = None,
        triggers: Sequence[tuple[bool, bool]] | None = None,
        rule: Any = None,
    ) -> AutoimmuneToxicityReport:
        """Calculate Autoimmune Toxicity Index on a corpus or sequence of trigger pairs.

        Trigger pair: (has_signal_1, has_signal_2).
        Signal 1 ALONE: has_signal_1 is True and has_signal_2 is False.
        """
        if triggers is not None:
            total_triggers = len(triggers)
            if total_triggers == 0:
                toxicity = Fraction(0, 1)
                signal1_only = 0
            else:
                signal1_only = sum(1 for s1, s2 in triggers if s1 and not s2)
                toxicity = Fraction(signal1_only, total_triggers)
            return AutoimmuneToxicityReport(
                rule_id=rule_id,
                signal1_only_count=signal1_only,
                total_triggers=total_triggers,
                toxicity_index=toxicity,
            )

        if prompt_corpus is not None:
            pattern_str = getattr(rule, "match_pattern", getattr(rule, "pattern", str(rule) if rule else ""))
            regex = re.compile(pattern_str, re.IGNORECASE) if pattern_str else None

            signal1_only = 0
            total_triggers = 0

            for prompt in prompt_corpus:
                has_s1 = bool(regex.search(prompt)) if regex else False
                # Pinned benign corpus has no Signal 2 by definition
                has_s2 = False
                if has_s1:
                    total_triggers += 1
                    if not has_s2:
                        signal1_only += 1

            toxicity = Fraction(signal1_only, total_triggers) if total_triggers > 0 else Fraction(0, 1)
            return AutoimmuneToxicityReport(
                rule_id=rule_id,
                signal1_only_count=signal1_only,
                total_triggers=total_triggers,
                toxicity_index=toxicity,
            )

        raise ValueError("Either prompt_corpus or triggers must be provided")

    def synthesize_treg(self, report: AutoimmuneToxicityReport) -> RegulatoryAntibody | None:
        """Synthesize a RegulatoryAntibody if toxicity meets or exceeds the tau threshold."""
        if report.toxicity_index >= self.tau:
            return RegulatoryAntibody.create(
                target_rule_id=report.rule_id,
                toxicity_index=report.toxicity_index,
                tau_threshold=self.tau,
            )
        return None


__all__ = [
    "AuthorityLevel",
    "AutoimmuneToxicityReport",
    "RegulatoryAntibody",
    "TregSupervisor",
]
