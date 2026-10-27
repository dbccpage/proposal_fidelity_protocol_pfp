"""Learned-guard activation on two independent signals (`EPIC-OE-IMMUNE-002`).

Moved on 2026-09-29 from
`projects/ms_majorana/code/tests/support/prompt_civilization/domain/negative_selection_v1.py`,
where it was the only implementation of the epic's activation law and was
reachable only from a test support folder.

The epic states the activation law for a learned guard `g` in subject scope `s`:

    externally_admitted(g, s)
    AND detector_match(g, subject)
    AND independent_danger_signal(subject, context)
    AND not_suspended(g, s)

and names the way implementations get it wrong:

> An implementation must name which inputs are independent. Counting the same
> predicate twice, deriving the danger bit from the detector match, or accepting
> a model-authored danger flag is `TWO_SIGNAL_COLLAPSE`.

Independence is witnessed, not asserted: the danger receipt names a host
observer and an evidence digest, and both are checked against the detector
hit. Three collapses are refused separately:

- the danger receipt's evidence is the detector's own finding digest;
- the danger receipt's observer is the detector spec or its failure code;
- the danger receipt was authored by a model rather than observed by a host.

The detector hit enters as a `DetectorHitRefV1` (the fields of an OEWAS
`AntiSkillHitV1` that activation reads), so this domain does not import OEWAS.
The activation profile enters as its content digest.

The gate emits `FINDING`, `HOLD` or `REFUSE` and nothing else; there is no
repair, admit, merge, publish or execute path in this module.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .canonical import canonical_id
from .danger_signals import HOST_DANGER_SIGNAL_KINDS
from .ports import GuardActivationPolicyPort

AUTHORITY_EFFECT_NONE = "None"
DANGER_SIGNAL_SCHEMA_V1 = "core.antiskill.danger-signal-receipt.v1"
GUARD_ACTIVATION_SCHEMA_V1 = "core.antiskill.guard-activation-receipt.v1"

# `IMMUNE-002-W3`: the closed registry of host-observable danger signals, shared
# with the screening path.
DANGER_SIGNAL_KINDS = HOST_DANGER_SIGNAL_KINDS

# Only a host observes danger. A model proposing one is a model authorising its
# own activation.
DANGER_PRODUCER_HOST = "HOST"
FORBIDDEN_DANGER_PRODUCERS = frozenset({"MODEL", "LLM", "AGENT", "DETECTOR"})

# The only dispositions activation may select. Repair, admission, merge, publish
# and execute are absent by construction, not by policy.
ACTIVATION_DISPOSITIONS = frozenset({"FINDING", "HOLD", "REFUSE"})

REFUSAL_CODES = frozenset(
    {
        "NOT_EXTERNALLY_ADMITTED",
        "NO_DETECTOR_MATCH",
        "NO_DANGER_SIGNAL",
        "SUSPENDED",
        "TWO_SIGNAL_COLLAPSE",
        "SUBJECT_MISMATCH",
        "HOST_HEALTH_UNAVAILABLE",
        "HOST_HEALTH_UNHEALTHY",
        "HOST_HEALTH_UNVERIFIED",
    }
)

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")
_MAX_TEXT_BYTES = 4096


def _text(value: Any, label: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be an exact string")
    if len(value.encode("utf-8")) > _MAX_TEXT_BYTES:
        raise ValueError(f"{label} exceeds the text limit")
    if not value or value.strip() != value:
        raise ValueError(f"{label} must be a normalized nonempty string")
    return value


def _identifier(value: Any, label: str) -> str:
    result = _text(value, label)
    if _IDENTIFIER.fullmatch(result) is None:
        raise ValueError(f"{label} must be a canonical identifier")
    return result


def _digest(value: Any, label: str) -> str:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase sha256 digest")
    return value


class ActivationRefusal(RuntimeError):
    """A typed refusal. Activation fails closed and says which conjunct failed."""

    def __init__(self, code: str, message: str) -> None:
        if code not in REFUSAL_CODES:
            raise ValueError(f"unknown activation refusal code: {code}")
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class DetectorHitRefV1:
    """The detector hit fields activation reads.

    Built from an OEWAS `AntiSkillHitV1` by `from_hit`, which re-validates each
    field rather than trusting the source object.
    """

    hit_id: str
    spec_id: str
    failure_code: str
    subject_id: str

    def __post_init__(self) -> None:
        _digest(self.hit_id, "hit_id")
        _identifier(self.spec_id, "spec_id")
        _identifier(self.failure_code, "failure_code")
        _digest(self.subject_id, "subject_id")

    @classmethod
    def from_hit(cls, hit: object) -> "DetectorHitRefV1":
        return cls(
            hit_id=getattr(hit, "hit_id", None),  # type: ignore[arg-type]
            spec_id=getattr(hit, "spec_id", None),  # type: ignore[arg-type]
            failure_code=getattr(hit, "failure_code", None),  # type: ignore[arg-type]
            subject_id=getattr(hit, "subject_id", None),  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class DangerSignalReceiptV1:
    """A host observation, independent of any detector.

    `signal_kind` comes from a closed registry; `observer_id` names the host
    component that saw it; `evidence_digest` is the digest of the observed bytes.
    Independence is checked against these two fields, so a receipt that cannot
    say who observed what cannot be used as a second signal at all.
    """

    signal_kind: str
    observer_id: str
    subject_id: str
    evidence_digest: str
    producer_kind: str = DANGER_PRODUCER_HOST
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = DANGER_SIGNAL_SCHEMA_V1
    receipt_id: str = ""

    def __post_init__(self) -> None:
        if self.signal_kind not in DANGER_SIGNAL_KINDS:
            raise ValueError(
                "danger signal_kind is not in the closed registry: "
                + ", ".join(sorted(DANGER_SIGNAL_KINDS))
            )
        _identifier(self.observer_id, "observer_id")
        _digest(self.subject_id, "subject_id")
        _digest(self.evidence_digest, "evidence_digest")
        if self.producer_kind in FORBIDDEN_DANGER_PRODUCERS:
            raise ValueError(
                f"a danger signal may not be authored by {self.producer_kind}; "
                "danger is observed by a host, not proposed by a model"
            )
        if self.producer_kind != DANGER_PRODUCER_HOST:
            raise ValueError("danger signal producer_kind must be HOST")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("danger signal authority_effect must be None")
        if self.schema_version != DANGER_SIGNAL_SCHEMA_V1:
            raise ValueError("unsupported danger signal schema")
        expected = canonical_id(DANGER_SIGNAL_SCHEMA_V1, self._payload())
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("receipt_id does not match canonical content")
        object.__setattr__(self, "receipt_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "evidence_digest": self.evidence_digest,
            "observer_id": self.observer_id,
            "producer_kind": self.producer_kind,
            "schema_version": self.schema_version,
            "signal_kind": self.signal_kind,
            "subject_id": self.subject_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "receipt_id": self.receipt_id}


@dataclass(frozen=True, slots=True)
class GuardActivationReceiptV1:
    """What an activation produced, and the two signals it stood on.

    It carries the digests of the profile, hit and danger receipt rather than
    their contents, so it cannot restate -- and therefore cannot contradict --
    what they say.
    """

    profile_digest: str
    hit_id: str
    danger_receipt_id: str
    subject_id: str
    disposition: str
    independence_basis: str
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = GUARD_ACTIVATION_SCHEMA_V1
    receipt_id: str = ""

    def __post_init__(self) -> None:
        _digest(self.profile_digest, "profile_digest")
        _digest(self.hit_id, "hit_id")
        _digest(self.danger_receipt_id, "danger_receipt_id")
        _digest(self.subject_id, "subject_id")
        if self.disposition not in ACTIVATION_DISPOSITIONS:
            raise ValueError(
                "activation disposition is not closed; activation may select "
                "only FINDING, HOLD or REFUSE"
            )
        # A receipt that cannot say why its two signals are independent is not
        # evidence of independence, so the field is required and non-empty.
        _text(self.independence_basis, "independence_basis")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("guard activation authority_effect must be None")
        if self.schema_version != GUARD_ACTIVATION_SCHEMA_V1:
            raise ValueError("unsupported guard activation schema")
        expected = canonical_id(GUARD_ACTIVATION_SCHEMA_V1, self._payload())
        if self.receipt_id and self.receipt_id != expected:
            raise ValueError("receipt_id does not match canonical content")
        object.__setattr__(self, "receipt_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "danger_receipt_id": self.danger_receipt_id,
            "disposition": self.disposition,
            "hit_id": self.hit_id,
            "independence_basis": self.independence_basis,
            "profile_digest": self.profile_digest,
            "schema_version": self.schema_version,
            "subject_id": self.subject_id,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "receipt_id": self.receipt_id}


def evaluate_activation(
    profile_digest: str,
    hit: DetectorHitRefV1 | None,
    danger: DangerSignalReceiptV1 | None,
    *,
    externally_admitted: bool,
    suspended: bool,
    disposition: str = "FINDING",
    policy: GuardActivationPolicyPort | None = None,
) -> GuardActivationReceiptV1:
    """Evaluate the receipt-bound activation law through an inward policy port."""
    _validate_activation_inputs(profile_digest, hit, danger, externally_admitted, suspended)
    if policy is not None:
        return policy.evaluate_activation(
            profile_digest,
            hit,
            danger,
            externally_admitted=externally_admitted,
            suspended=suspended,
            disposition=disposition,
        )
    checked_hit, checked_danger = _require_activation_conjuncts(
        hit, danger, externally_admitted=externally_admitted, suspended=suspended
    )
    _require_independent_signals(checked_hit, checked_danger)
    if disposition not in ACTIVATION_DISPOSITIONS:
        raise ValueError(
            f"activation may select only FINDING, HOLD or REFUSE; {disposition!r} is not closed"
        )
    independence_basis = (
        f"host observer {checked_danger.observer_id} reported "
        f"{checked_danger.signal_kind} with evidence "
        f"{checked_danger.evidence_digest[:23]}..., distinct from detector spec "
        f"{checked_hit.spec_id} and its finding"
    )
    return GuardActivationReceiptV1(
        profile_digest=profile_digest,
        hit_id=checked_hit.hit_id,
        danger_receipt_id=checked_danger.receipt_id,
        subject_id=checked_hit.subject_id,
        disposition=disposition,
        independence_basis=independence_basis,
    )


def _validate_activation_inputs(
    profile_digest: str,
    hit: DetectorHitRefV1 | None,
    danger: DangerSignalReceiptV1 | None,
    externally_admitted: bool,
    suspended: bool,
) -> None:
    _digest(profile_digest, "profile_digest")
    if type(externally_admitted) is not bool:
        raise ValueError("externally_admitted must be an exact boolean")
    if type(suspended) is not bool:
        raise ValueError("suspended must be an exact boolean")
    if hit is not None and type(hit) is not DetectorHitRefV1:
        raise ValueError("activation requires an exact DetectorHitRefV1")
    if danger is not None and type(danger) is not DangerSignalReceiptV1:
        raise ValueError("activation requires an exact DangerSignalReceiptV1")


def _require_activation_conjuncts(
    hit: DetectorHitRefV1 | None,
    danger: DangerSignalReceiptV1 | None,
    *,
    externally_admitted: bool,
    suspended: bool,
) -> tuple[DetectorHitRefV1, DangerSignalReceiptV1]:
    if not externally_admitted:
        raise ActivationRefusal(
            "NOT_EXTERNALLY_ADMITTED",
            "the guard has no external admission for this subject scope",
        )
    if hit is None:
        raise ActivationRefusal(
            "NO_DETECTOR_MATCH",
            "a danger signal without a detector match cannot activate a guard",
        )
    if danger is None:
        raise ActivationRefusal(
            "NO_DANGER_SIGNAL",
            "a detector match without an independent danger receipt stays a finding "
            "and does not activate the learned guard",
        )
    if danger.subject_id != hit.subject_id:
        raise ActivationRefusal(
            "SUBJECT_MISMATCH",
            "the danger signal observes a different subject than the detector",
        )
    if suspended:
        raise ActivationRefusal(
            "SUSPENDED", "the guard is suspended in this subject scope"
        )
    return hit, danger


def _require_independent_signals(
    hit: DetectorHitRefV1, danger: DangerSignalReceiptV1
) -> None:
    if danger.evidence_digest == hit.hit_id:
        raise ActivationRefusal(
            "TWO_SIGNAL_COLLAPSE",
            "the danger receipt's evidence is the detector's own finding; "
            "that is one signal counted twice",
        )
    if danger.observer_id.casefold() == hit.spec_id.casefold():
        raise ActivationRefusal(
            "TWO_SIGNAL_COLLAPSE",
            f"the danger signal was observed by '{danger.observer_id}', which is the "
            "detector spec itself; the danger bit is derived from the match",
        )
    if danger.observer_id.casefold() == hit.failure_code.casefold():
        raise ActivationRefusal(
            "TWO_SIGNAL_COLLAPSE",
            "the danger observer is the detector's own failure code",
        )


__all__ = [
    "ACTIVATION_DISPOSITIONS",
    "ActivationRefusal",
    "DANGER_PRODUCER_HOST",
    "DANGER_SIGNAL_KINDS",
    "DANGER_SIGNAL_SCHEMA_V1",
    "DangerSignalReceiptV1",
    "DetectorHitRefV1",
    "FORBIDDEN_DANGER_PRODUCERS",
    "GUARD_ACTIVATION_SCHEMA_V1",
    "GuardActivationReceiptV1",
    "REFUSAL_CODES",
    "evaluate_activation",
]
