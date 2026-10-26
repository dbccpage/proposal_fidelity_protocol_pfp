"""Three-role provenance gate: fail-closed check of ``(proposer, evaluator, authorizer)``.

AuthorityEffect: None.

The packet is the WDP authority packet read on its provenance fields
(``WDP-CH15-D01``): a claim, a scope, three role bindings, the declared
observer under which the claim was evaluated (``WDP-CH10-D01``: kernel,
admissibility, norm, terminal rule, layer) and the authority root the
authorizer appeals to. The role policy of a high-assurance regime requires
``PairwiseDistinct(proposer, evaluator, authorizer)``; the WDP note on
authority adds that distinct identifiers do not ensure independent actors,
so each binding also names its principal (the actor or process behind the
identifier) and two bindings on one principal are not distinct.

What the gate does not do: it does not evaluate the claim, does not compute
a defect, and does not promote anything. ``ADMITTED_FOR_AUTHORIZATION`` means
the packet is well formed and separated, so the authorizer may act under the
root it named; the certificate, if any, is issued outside this module.

Fail-closed discipline: a missing field, an empty identifier, a non-boolean
flag or an unknown policy is a typed refusal, never a default. The sentence
"I verified this and certify it", read as a packet, binds all three roles to
one principal and is rejected on three counts; that is the unadmitted
self-bridge the mission names, recorded here as the gate's standing example.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

AUTHORITY_EFFECT = "None"

OBSERVER_COMPONENTS = ("kernel", "admissibility", "norm", "terminal", "layer")
PACKET_FIELDS = (
    "claim_id",
    "scope",
    "proposer",
    "evaluator",
    "authorizer",
    "observer",
    "authority_root",
    "policy",
)
BINDING_FIELDS = ("identifier", "principal")


class Role(str, Enum):
    PROPOSER = "proposer"
    EVALUATOR = "evaluator"
    AUTHORIZER = "authorizer"


class RolePolicy(str, Enum):
    """Declared by the regime, not derived from the evidence."""

    PAIRWISE_DISTINCT = "pairwise_distinct"
    SELF_ATTESTED_PERMITTED = "self_attested_permitted"


class VerdictCode(str, Enum):
    ADMITTED_FOR_AUTHORIZATION = "ADMITTED_FOR_AUTHORIZATION"
    SELF_ATTESTED = "SELF_ATTESTED"
    REJECTED = "REJECTED"


class RefusalReason(str, Enum):
    MALFORMED_PACKET = "MALFORMED_PACKET"
    MISSING_FIELD = "MISSING_FIELD"
    UNKNOWN_FIELD = "UNKNOWN_FIELD"
    EMPTY_IDENTIFIER = "EMPTY_IDENTIFIER"
    UNKNOWN_POLICY = "UNKNOWN_POLICY"
    UNDECLARED_OBSERVER = "UNDECLARED_OBSERVER"
    SELF_AUTHORIZATION = "SELF_AUTHORIZATION"
    EVALUATOR_IS_PROPOSER = "EVALUATOR_IS_PROPOSER"
    EVALUATOR_IS_AUTHORIZER = "EVALUATOR_IS_AUTHORIZER"
    SHARED_PRINCIPAL = "SHARED_PRINCIPAL"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    UNADMITTED_ROOT = "UNADMITTED_ROOT"


class PacketShapeError(ValueError):
    """A packet that cannot be read as a provenance packet."""

    def __init__(self, reason: RefusalReason, detail: str) -> None:
        super().__init__(f"{reason.value}: {detail}")
        self.reason = reason
        self.detail = detail


def _require_str(payload: Mapping[str, Any], field: str, where: str) -> str:
    if field not in payload:
        raise PacketShapeError(RefusalReason.MISSING_FIELD, f"{where}.{field}")
    value = payload[field]
    if type(value) is not str:
        raise PacketShapeError(RefusalReason.MALFORMED_PACKET, f"{where}.{field} is not a string")
    if not value.strip():
        raise PacketShapeError(RefusalReason.EMPTY_IDENTIFIER, f"{where}.{field}")
    return value


def _require_mapping(payload: Mapping[str, Any], field: str, where: str) -> Mapping[str, Any]:
    if field not in payload:
        raise PacketShapeError(RefusalReason.MISSING_FIELD, f"{where}.{field}")
    value = payload[field]
    if not isinstance(value, Mapping):
        raise PacketShapeError(RefusalReason.MALFORMED_PACKET, f"{where}.{field} is not a mapping")
    return value


def _reject_unknown(payload: Mapping[str, Any], allowed: tuple[str, ...], where: str) -> None:
    # Keys are checked for type before any set arithmetic or formatting: a
    # non-string key must become a typed refusal, never a TypeError escaping
    # the gate, and it is never coerced to a string to be named.
    if any(type(key) is not str for key in payload):
        raise PacketShapeError(RefusalReason.MALFORMED_PACKET, f"{where}: a key is not a string")
    unknown = sorted(set(payload) - set(allowed))
    if unknown:
        raise PacketShapeError(RefusalReason.UNKNOWN_FIELD, f"{where}: {', '.join(unknown)}")


@dataclass(frozen=True)
class RoleBinding:
    """A role, the identifier that signed, and the principal behind it."""

    role: Role
    identifier: str
    principal: str

    def __post_init__(self) -> None:
        if type(self.role) is not Role:
            raise PacketShapeError(RefusalReason.MALFORMED_PACKET, "role is not a Role")
        for field in BINDING_FIELDS:
            value = getattr(self, field)
            if type(value) is not str:
                raise PacketShapeError(RefusalReason.MALFORMED_PACKET, f"{self.role.value}.{field}")
            if not value.strip():
                raise PacketShapeError(RefusalReason.EMPTY_IDENTIFIER, f"{self.role.value}.{field}")

    @classmethod
    def from_mapping(cls, role: Role, payload: Mapping[str, Any]) -> RoleBinding:
        _reject_unknown(payload, BINDING_FIELDS, role.value)
        return cls(
            role=role,
            identifier=_require_str(payload, "identifier", role.value),
            principal=_require_str(payload, "principal", role.value),
        )


@dataclass(frozen=True)
class ObserverDeclaration:
    """The five observer components of ``WDP-CH10-D01``, all declared."""

    kernel: str
    admissibility: str
    norm: str
    terminal: str
    layer: str

    def __post_init__(self) -> None:
        for component in OBSERVER_COMPONENTS:
            value = getattr(self, component)
            if type(value) is not str or not value.strip():
                raise PacketShapeError(RefusalReason.UNDECLARED_OBSERVER, component)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ObserverDeclaration:
        _reject_unknown(payload, OBSERVER_COMPONENTS, "observer")
        missing = [c for c in OBSERVER_COMPONENTS if c not in payload]
        if missing:
            raise PacketShapeError(RefusalReason.UNDECLARED_OBSERVER, missing[0])
        return cls(**{c: _observer_component(payload, c) for c in OBSERVER_COMPONENTS})


def _observer_component(payload: Mapping[str, Any], component: str) -> str:
    value = payload[component]
    if type(value) is not str or not value.strip():
        raise PacketShapeError(RefusalReason.UNDECLARED_OBSERVER, component)
    return value


@dataclass(frozen=True)
class ProvenancePacket:
    """The provenance fields of an authority packet."""

    claim_id: str
    scope: str
    proposer: RoleBinding
    evaluator: RoleBinding
    authorizer: RoleBinding
    observer: ObserverDeclaration
    authority_root: str
    policy: RolePolicy

    def __post_init__(self) -> None:
        for name, role in (
            ("proposer", Role.PROPOSER),
            ("evaluator", Role.EVALUATOR),
            ("authorizer", Role.AUTHORIZER),
        ):
            binding = getattr(self, name)
            if type(binding) is not RoleBinding or binding.role is not role:
                raise PacketShapeError(RefusalReason.MALFORMED_PACKET, f"{name} binding")
        if type(self.observer) is not ObserverDeclaration:
            raise PacketShapeError(RefusalReason.UNDECLARED_OBSERVER, "observer")
        if type(self.policy) is not RolePolicy:
            raise PacketShapeError(RefusalReason.UNKNOWN_POLICY, str(self.policy))
        for field in ("claim_id", "scope", "authority_root"):
            value = getattr(self, field)
            if type(value) is not str or not value.strip():
                raise PacketShapeError(RefusalReason.EMPTY_IDENTIFIER, field)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> ProvenancePacket:
        """Strict reading: every field present, typed, and nonempty."""

        if not isinstance(payload, Mapping):
            raise PacketShapeError(RefusalReason.MALFORMED_PACKET, "packet is not a mapping")
        _reject_unknown(payload, PACKET_FIELDS, "packet")
        policy_text = _require_str(payload, "policy", "packet")
        try:
            policy = RolePolicy(policy_text)
        except ValueError as error:
            raise PacketShapeError(RefusalReason.UNKNOWN_POLICY, policy_text) from error
        return cls(
            claim_id=_require_str(payload, "claim_id", "packet"),
            scope=_require_str(payload, "scope", "packet"),
            proposer=RoleBinding.from_mapping(
                Role.PROPOSER, _require_mapping(payload, "proposer", "packet")
            ),
            evaluator=RoleBinding.from_mapping(
                Role.EVALUATOR, _require_mapping(payload, "evaluator", "packet")
            ),
            authorizer=RoleBinding.from_mapping(
                Role.AUTHORIZER, _require_mapping(payload, "authorizer", "packet")
            ),
            observer=ObserverDeclaration.from_mapping(
                _require_mapping(payload, "observer", "packet")
            ),
            authority_root=_require_str(payload, "authority_root", "packet"),
            policy=policy,
        )

    def bindings(self) -> tuple[RoleBinding, RoleBinding, RoleBinding]:
        return (self.proposer, self.evaluator, self.authorizer)


@dataclass(frozen=True)
class GateVerdict:
    """The gate's answer. ``authority_effect`` is always ``"None"``."""

    code: VerdictCode
    reasons: tuple[RefusalReason, ...]
    detail: str
    authority_effect: str = AUTHORITY_EFFECT

    def __post_init__(self) -> None:
        if self.authority_effect != AUTHORITY_EFFECT:
            raise ValueError("a gate verdict carries no authority effect")
        if self.code is VerdictCode.REJECTED and not self.reasons:
            raise ValueError("a rejection names at least one reason")
        if self.code is not VerdictCode.REJECTED and self.reasons:
            raise ValueError("an admitted or self-attested verdict names no refusal")

    @property
    def admitted(self) -> bool:
        return self.code is VerdictCode.ADMITTED_FOR_AUTHORIZATION


class ThreeRoleGate:
    """Checks packets against a scope and a set of admitted authority roots."""

    def __init__(self, scope: str, admitted_roots: frozenset[str]) -> None:
        if type(scope) is not str or not scope.strip():
            raise ValueError("the gate's scope must be a nonempty string")
        if type(admitted_roots) is not frozenset or not admitted_roots:
            raise ValueError("the gate needs a nonempty frozenset of admitted roots")
        if any(type(root) is not str or not root.strip() for root in admitted_roots):
            raise ValueError("every admitted root is a nonempty string")
        self._scope = scope
        self._admitted_roots = admitted_roots

    @property
    def scope(self) -> str:
        return self._scope

    @property
    def admitted_roots(self) -> frozenset[str]:
        return self._admitted_roots

    @staticmethod
    def separation_failures(packet: ProvenancePacket) -> tuple[RefusalReason, ...]:
        """The pairwise-distinctness failures of the three bindings, in a fixed order."""

        proposer, evaluator, authorizer = packet.bindings()
        failures: list[RefusalReason] = []
        if proposer.identifier == authorizer.identifier:
            failures.append(RefusalReason.SELF_AUTHORIZATION)
        if evaluator.identifier == proposer.identifier:
            failures.append(RefusalReason.EVALUATOR_IS_PROPOSER)
        if evaluator.identifier == authorizer.identifier:
            failures.append(RefusalReason.EVALUATOR_IS_AUTHORIZER)
        bindings = packet.bindings()
        pairs = ((bindings[i], bindings[j]) for i in range(3) for j in range(i + 1, 3))
        if any(a.identifier != b.identifier and a.principal == b.principal for a, b in pairs):
            failures.append(RefusalReason.SHARED_PRINCIPAL)
        return tuple(failures)

    def evaluate(self, packet: ProvenancePacket) -> GateVerdict:
        if type(packet) is not ProvenancePacket:
            return GateVerdict(
                VerdictCode.REJECTED,
                (RefusalReason.MALFORMED_PACKET,),
                "not a ProvenancePacket",
            )
        reasons: list[RefusalReason] = []
        if packet.scope != self._scope:
            reasons.append(RefusalReason.SCOPE_MISMATCH)
        if packet.authority_root not in self._admitted_roots:
            reasons.append(RefusalReason.UNADMITTED_ROOT)
        separation = self.separation_failures(packet)
        if separation and packet.policy is RolePolicy.PAIRWISE_DISTINCT:
            reasons.extend(separation)
        if reasons:
            return GateVerdict(VerdictCode.REJECTED, tuple(reasons), packet.claim_id)
        if separation:
            return GateVerdict(
                VerdictCode.SELF_ATTESTED,
                (),
                f"{packet.claim_id}: separation not required by {packet.policy.value}; "
                "valid only under that regime and scope",
            )
        return GateVerdict(VerdictCode.ADMITTED_FOR_AUTHORIZATION, (), packet.claim_id)

    def evaluate_mapping(self, payload: Mapping[str, Any]) -> GateVerdict:
        """Read and evaluate; a packet that cannot be read is a rejection."""

        try:
            packet = ProvenancePacket.from_mapping(payload)
        except PacketShapeError as error:
            return GateVerdict(VerdictCode.REJECTED, (error.reason,), error.detail)
        return self.evaluate(packet)
