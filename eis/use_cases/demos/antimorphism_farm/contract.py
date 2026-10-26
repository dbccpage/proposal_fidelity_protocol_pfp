"""Admitted farm inputs and a quarantine record that cannot promote.

No classifier, pharmacy, or screen runs in this module. AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from omega_engine_pfp.domain.demos import DemoRefusal, refuse_model_functionals

DEMO_ID = "antimorphism_farm"
AUTHORITY_EFFECT = "None"
NATIVE_PORT_CODE = "NO_NATIVE_PORT"
PINNED_SCOPE = (
    "Bounded failure-class controls and traced OEWAS immune-port probes; "
    "no learning, model efficacy or promotion claim."
)
FIXTURE_KEYS = frozenset({"kind", "farm_probes", "replies", "immune_replies", "scope"})
PHARMACY_CONTROL_COUNT = 24
FARM_PROBE_COUNT = 6


@dataclass(frozen=True, slots=True)
class FarmFixture:
    kind: str
    farm_probes: bool
    replies: tuple[str, ...]
    immune_replies: tuple[str, ...]
    scope: str


def _strings(value: object, field: str) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise DemoRefusal("INVALID_FIXTURE", field)
    return tuple(value)


def admit_farm_fixture(value: object) -> FarmFixture:
    """Admit the front-end object. Reply text is not classified."""
    if type(value) is not dict:
        raise DemoRefusal("INVALID_FIXTURE", "object")
    refuse_model_functionals(value)
    if set(value) != FIXTURE_KEYS:
        raise DemoRefusal("INVALID_FIXTURE", "keys")
    kind = value["kind"]
    if type(kind) is not str or kind != "immune":
        raise DemoRefusal("INVALID_FIXTURE", "kind")
    flag = value["farm_probes"]
    if type(flag) is not bool:
        raise DemoRefusal("INVALID_FIXTURE", "farm_probes")
    scope = value["scope"]
    if type(scope) is not str or scope != PINNED_SCOPE:
        raise DemoRefusal("INVALID_FIXTURE", "scope")
    return FarmFixture(
        kind=kind,
        farm_probes=flag,
        replies=_strings(value["replies"], "replies"),
        immune_replies=_strings(value["immune_replies"], "immune_replies"),
        scope=scope,
    )


def refusal_evidence_body() -> dict[str, object]:
    """Preimage of the quarantine digest. The probe flag is not a gate."""
    return {
        "AuthorityEffect": AUTHORITY_EFFECT,
        "code": NATIVE_PORT_CODE,
        "demo_id": DEMO_ID,
        "farm_probe_count": FARM_PROBE_COUNT,
        "farm_probes_are_a_gate": False,
        "pharmacy_controls": PHARMACY_CONTROL_COUNT,
    }


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    rule_id: str
    epitope: str
    matched: str
    evidence_digest: str
    disposition: str
    AuthorityEffect: str
    permanent: bool
    can_promote_to_core: bool

    def __post_init__(self) -> None:
        if self.rule_id != DEMO_ID or self.epitope != NATIVE_PORT_CODE:
            raise DemoRefusal("PROMOTION_REFUSED", "identity")
        if self.matched != NATIVE_PORT_CODE or self.disposition != "QUARANTINED":
            raise DemoRefusal("PROMOTION_REFUSED", "disposition")
        if self.AuthorityEffect != AUTHORITY_EFFECT:
            raise DemoRefusal("PROMOTION_REFUSED", "AuthorityEffect")
        if type(self.permanent) is not bool or self.permanent is not True:
            raise DemoRefusal("PROMOTION_REFUSED", "permanent")
        if type(self.can_promote_to_core) is not bool or self.can_promote_to_core is not False:
            raise DemoRefusal("PROMOTION_REFUSED", "can_promote_to_core")
        if (
            type(self.evidence_digest) is not str
            or len(self.evidence_digest) != 64
            or any(char not in "0123456789abcdef" for char in self.evidence_digest)
        ):
            raise DemoRefusal("PROMOTION_REFUSED", "evidence_digest")

    def as_dict(self) -> dict[str, object]:
        return {
            "AuthorityEffect": self.AuthorityEffect,
            "can_promote_to_core": self.can_promote_to_core,
            "disposition": self.disposition,
            "epitope": self.epitope,
            "evidence_digest": self.evidence_digest,
            "matched": self.matched,
            "permanent": self.permanent,
            "rule_id": self.rule_id,
        }


def refusal_quarantine(evidence_digest: str) -> dict[str, object]:
    return QuarantineRecord(
        rule_id=DEMO_ID,
        epitope=NATIVE_PORT_CODE,
        matched=NATIVE_PORT_CODE,
        evidence_digest=evidence_digest,
        disposition="QUARANTINED",
        AuthorityEffect=AUTHORITY_EFFECT,
        permanent=True,
        can_promote_to_core=False,
    ).as_dict()
