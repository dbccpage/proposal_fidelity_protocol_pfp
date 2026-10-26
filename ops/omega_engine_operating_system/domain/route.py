"""Route planning and skill-use evidence models for OEOS governed tasks.

RoutePlanV1 binds the task envelope, capability snapshot, and candidate routes.
SkillUseEventV1 enforces monotonic progression across observed phases:
SELECTED -> CONTEXT_BOUND -> INVOKED -> OUTPUT_USED.
No later state is inferred from an earlier one.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from .task import (
    GENESIS_EVENT_DIGEST,
    TaskInvariantError,
    _ExactTypeValue,
    _require_digest,
    _require_exact_int,
    _require_exact_str,
    _require_timestamp,
    _IDENTIFIER,
    _SCOPED_IDENTIFIER,
    digest_payload,
)

SCHEMA_ROUTE_PLAN = "omega.oeos.route-plan.v1"
SCHEMA_SKILL_USE_EVENT = "omega.oeos.skill-use-event.v1"


@dataclass(frozen=True, slots=True, eq=False)
class RoutePlanV1(_ExactTypeValue):
    """Governed route plan bound to task envelope and capability snapshot."""

    route_plan_id: str
    task_id: str
    envelope_digest: str
    capability_snapshot_digest: str
    selected_route: str
    candidate_routes: tuple[str, ...]
    policy_digest: str
    created_at_utc: str
    schema: str = SCHEMA_ROUTE_PLAN
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_ROUTE_PLAN:
            raise TaskInvariantError("SCHEMA_MISMATCH", "route plan schema differs")
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN", "route plans grant no authority"
            )
        _require_exact_str(self.route_plan_id, "route_plan_id", _IDENTIFIER)
        _require_exact_str(self.task_id, "task_id", _IDENTIFIER)
        _require_digest(self.envelope_digest, "envelope_digest")
        _require_digest(self.capability_snapshot_digest, "capability_snapshot_digest")
        _require_exact_str(self.selected_route, "selected_route", _SCOPED_IDENTIFIER)
        _require_digest(self.policy_digest, "policy_digest")
        _require_timestamp(self.created_at_utc, "created_at_utc")

        if type(self.candidate_routes) is not tuple or any(
            type(route) is not str or _SCOPED_IDENTIFIER.fullmatch(route) is None
            for route in self.candidate_routes
        ):
            raise TaskInvariantError(
                "INVALID_CANDIDATE_ROUTES",
                "candidate_routes must be a tuple of scoped identifiers",
            )
        if tuple(sorted(set(self.candidate_routes))) != self.candidate_routes:
            raise TaskInvariantError(
                "INVALID_CANDIDATE_ROUTES",
                "candidate_routes must be sorted and unique",
            )
        if self.selected_route not in self.candidate_routes:
            raise TaskInvariantError(
                "SELECTED_ROUTE_NOT_CANDIDATE",
                "selected_route must be present in candidate_routes",
            )

    def to_canonical(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "candidate_routes": list(self.candidate_routes),
            "capability_snapshot_digest": self.capability_snapshot_digest,
            "created_at_utc": self.created_at_utc,
            "envelope_digest": self.envelope_digest,
            "policy_digest": self.policy_digest,
            "route_plan_id": self.route_plan_id,
            "schema": self.schema,
            "selected_route": self.selected_route,
            "task_id": self.task_id,
        }

    @property
    def canonical_digest(self) -> str:
        return digest_payload(self.schema, self.to_canonical())

    @classmethod
    def create(
        cls,
        *,
        route_plan_id: str,
        task_id: str,
        envelope_digest: str,
        capability_snapshot_digest: str,
        selected_route: str,
        candidate_routes: tuple[str, ...],
        policy_digest: str,
        created_at_utc: str,
    ) -> RoutePlanV1:
        return cls(
            route_plan_id=route_plan_id,
            task_id=task_id,
            envelope_digest=envelope_digest,
            capability_snapshot_digest=capability_snapshot_digest,
            selected_route=selected_route,
            candidate_routes=candidate_routes,
            policy_digest=policy_digest,
            created_at_utc=created_at_utc,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> RoutePlanV1:
        expected = {
            "authority_effect",
            "candidate_routes",
            "capability_snapshot_digest",
            "created_at_utc",
            "envelope_digest",
            "policy_digest",
            "route_plan_id",
            "schema",
            "selected_route",
            "task_id",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_ROUTE_PLAN", "route plan fields differ"
            )
        raw_routes = value["candidate_routes"]
        if type(raw_routes) is not list:
            raise TaskInvariantError(
                "INVALID_ROUTE_PLAN", "candidate_routes must be a list"
            )
        return cls(
            route_plan_id=value["route_plan_id"],  # type: ignore[arg-type]
            task_id=value["task_id"],  # type: ignore[arg-type]
            envelope_digest=value["envelope_digest"],  # type: ignore[arg-type]
            capability_snapshot_digest=value["capability_snapshot_digest"],  # type: ignore[arg-type]
            selected_route=value["selected_route"],  # type: ignore[arg-type]
            candidate_routes=tuple(raw_routes),
            policy_digest=value["policy_digest"],  # type: ignore[arg-type]
            created_at_utc=value["created_at_utc"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


class SkillUsePhaseV1(str, Enum):
    """Discrete phases of governed skill use.

    No later phase may be inferred from an earlier one without an explicit
    evidence digest recorded for each step.
    """

    SELECTED = "SELECTED"
    CONTEXT_BOUND = "CONTEXT_BOUND"
    INVOKED = "INVOKED"
    OUTPUT_USED = "OUTPUT_USED"


ALLOWED_SKILL_PHASE_TRANSITIONS: Mapping[
    SkillUsePhaseV1 | None, frozenset[SkillUsePhaseV1]
] = {
    None: frozenset({SkillUsePhaseV1.SELECTED}),
    SkillUsePhaseV1.SELECTED: frozenset({SkillUsePhaseV1.CONTEXT_BOUND}),
    SkillUsePhaseV1.CONTEXT_BOUND: frozenset({SkillUsePhaseV1.INVOKED}),
    SkillUsePhaseV1.INVOKED: frozenset({SkillUsePhaseV1.OUTPUT_USED}),
    SkillUsePhaseV1.OUTPUT_USED: frozenset(),
}


@dataclass(frozen=True, slots=True, eq=False)
class SkillUseEventV1(_ExactTypeValue):
    """Monotonic observed evidence event in a skill's lifecycle."""

    event_id: str
    task_id: str
    skill_id: str
    sequence: int
    from_phase: SkillUsePhaseV1 | None
    to_phase: SkillUsePhaseV1
    evidence_digest: str
    occurred_at_utc: str
    previous_event_digest: str
    event_digest: str
    schema: str = SCHEMA_SKILL_USE_EVENT
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.schema != SCHEMA_SKILL_USE_EVENT:
            raise TaskInvariantError(
                "SCHEMA_MISMATCH", "skill use event schema differs"
            )
        if self.authority_effect != "None":
            raise TaskInvariantError(
                "AUTHORITY_EFFECT_FORBIDDEN", "skill use events grant no authority"
            )
        _require_exact_str(self.event_id, "event_id", _IDENTIFIER)
        _require_exact_str(self.task_id, "task_id", _IDENTIFIER)
        _require_exact_str(self.skill_id, "skill_id", _SCOPED_IDENTIFIER)
        _require_exact_int(self.sequence, "sequence", 1, 10**9)
        if self.from_phase is not None and type(self.from_phase) is not SkillUsePhaseV1:
            raise TaskInvariantError(
                "INVALID_PHASE", "from_phase type differs"
            )
        if type(self.to_phase) is not SkillUsePhaseV1:
            raise TaskInvariantError(
                "INVALID_PHASE", "to_phase type differs"
            )
        if self.to_phase not in ALLOWED_SKILL_PHASE_TRANSITIONS[self.from_phase]:
            raise TaskInvariantError(
                "ILLEGAL_SKILL_PHASE_TRANSITION",
                f"{self.from_phase} cannot transition directly to {self.to_phase.value}",
            )
        _require_digest(self.evidence_digest, "evidence_digest")
        _require_timestamp(self.occurred_at_utc, "occurred_at_utc")
        _require_digest(self.previous_event_digest, "previous_event_digest")
        _require_digest(self.event_digest, "event_digest")
        if self.event_digest != self.recomputed_digest:
            raise TaskInvariantError(
                "EVENT_DIGEST_MISMATCH", "skill use event digest does not replay"
            )

    def _digest_fields(self) -> dict[str, object]:
        return {
            "authority_effect": self.authority_effect,
            "evidence_digest": self.evidence_digest,
            "from_phase": self.from_phase.value if self.from_phase else None,
            "occurred_at_utc": self.occurred_at_utc,
            "previous_event_digest": self.previous_event_digest,
            "schema": self.schema,
            "sequence": self.sequence,
            "skill_id": self.skill_id,
            "task_id": self.task_id,
            "to_phase": self.to_phase.value,
        }

    @property
    def recomputed_digest(self) -> str:
        return digest_payload(self.schema, self._digest_fields())

    def to_canonical(self) -> dict[str, object]:
        return {
            **self._digest_fields(),
            "event_digest": self.event_digest,
            "event_id": self.event_id,
        }

    @classmethod
    def create(
        cls,
        *,
        event_id: str,
        task_id: str,
        skill_id: str,
        sequence: int,
        from_phase: SkillUsePhaseV1 | None,
        to_phase: SkillUsePhaseV1,
        evidence_digest: str,
        occurred_at_utc: str,
        previous_event_digest: str,
    ) -> SkillUseEventV1:
        fields = {
            "authority_effect": "None",
            "evidence_digest": evidence_digest,
            "from_phase": from_phase.value if from_phase else None,
            "occurred_at_utc": occurred_at_utc,
            "previous_event_digest": previous_event_digest,
            "schema": SCHEMA_SKILL_USE_EVENT,
            "sequence": sequence,
            "skill_id": skill_id,
            "task_id": task_id,
            "to_phase": to_phase.value,
        }
        computed = digest_payload(SCHEMA_SKILL_USE_EVENT, fields)
        return cls(
            event_id=event_id,
            task_id=task_id,
            skill_id=skill_id,
            sequence=sequence,
            from_phase=from_phase,
            to_phase=to_phase,
            evidence_digest=evidence_digest,
            occurred_at_utc=occurred_at_utc,
            previous_event_digest=previous_event_digest,
            event_digest=computed,
        )

    @property
    def canonical_digest(self) -> str:
        return self.event_digest

    @classmethod
    def create_genesis(
        cls,
        *,
        event_id: str,
        task_id: str,
        skill_id: str,
        phase: SkillUsePhaseV1 = SkillUsePhaseV1.SELECTED,
        evidence_digest: str,
        created_at_utc: str,
    ) -> SkillUseEventV1:
        return cls.create(
            event_id=event_id,
            task_id=task_id,
            skill_id=skill_id,
            sequence=1,
            from_phase=None,
            to_phase=phase,
            evidence_digest=evidence_digest,
            occurred_at_utc=created_at_utc,
            previous_event_digest=GENESIS_EVENT_DIGEST,
        )

    @classmethod
    def create_child(
        cls,
        *,
        parent: SkillUseEventV1,
        event_id: str,
        phase: SkillUsePhaseV1,
        evidence_digest: str,
        created_at_utc: str,
    ) -> SkillUseEventV1:
        return cls.create(
            event_id=event_id,
            task_id=parent.task_id,
            skill_id=parent.skill_id,
            sequence=parent.sequence + 1,
            from_phase=parent.to_phase,
            to_phase=phase,
            evidence_digest=evidence_digest,
            occurred_at_utc=created_at_utc,
            previous_event_digest=parent.canonical_digest,
        )

    @classmethod
    def from_canonical(cls, value: Mapping[str, object]) -> SkillUseEventV1:
        expected = {
            "authority_effect",
            "event_digest",
            "event_id",
            "evidence_digest",
            "from_phase",
            "occurred_at_utc",
            "previous_event_digest",
            "schema",
            "sequence",
            "skill_id",
            "task_id",
            "to_phase",
        }
        if type(value) is not dict or set(value) != expected:
            raise TaskInvariantError(
                "INVALID_SKILL_USE_EVENT", "skill use event fields differ"
            )
        from_phase = (
            None
            if value["from_phase"] is None
            else SkillUsePhaseV1(value["from_phase"])
        )
        to_phase = SkillUsePhaseV1(value["to_phase"])
        return cls(
            event_id=value["event_id"],  # type: ignore[arg-type]
            task_id=value["task_id"],  # type: ignore[arg-type]
            skill_id=value["skill_id"],  # type: ignore[arg-type]
            sequence=value["sequence"],  # type: ignore[arg-type]
            from_phase=from_phase,
            to_phase=to_phase,
            evidence_digest=value["evidence_digest"],  # type: ignore[arg-type]
            occurred_at_utc=value["occurred_at_utc"],  # type: ignore[arg-type]
            previous_event_digest=value["previous_event_digest"],  # type: ignore[arg-type]
            event_digest=value["event_digest"],  # type: ignore[arg-type]
            schema=value["schema"],  # type: ignore[arg-type]
            authority_effect=value["authority_effect"],  # type: ignore[arg-type]
        )


def verify_skill_lifecycle_chain(
    events: tuple[SkillUseEventV1, ...]
) -> SkillUsePhaseV1:
    """Verify hash-chaining and phase progression for a single skill stream."""
    if type(events) is not tuple or not events:
        raise TaskInvariantError(
            "EMPTY_SKILL_CHAIN", "at least one skill use event is required"
        )
    expected_previous = GENESIS_EVENT_DIGEST
    expected_phase: SkillUsePhaseV1 | None = None
    skill_id = events[0].skill_id
    task_id = events[0].task_id

    for expected_sequence, event in enumerate(events, start=1):
        if type(event) is not SkillUseEventV1:
            raise TaskInvariantError("INVALID_EVENT", "event type differs")
        if event.task_id != task_id or event.skill_id != skill_id:
            raise TaskInvariantError(
                "SKILL_IDENTITY_MISMATCH", "event stream identity differs"
            )
        if event.sequence != expected_sequence:
            raise TaskInvariantError(
                "SEQUENCE_GAP", f"expected sequence {expected_sequence}, got {event.sequence}"
            )
        if event.previous_event_digest != expected_previous:
            raise TaskInvariantError(
                "CHAIN_BROKEN", "previous event digest mismatch"
            )
        if event.from_phase is not expected_phase:
            raise TaskInvariantError(
                "PHASE_CHAIN_BROKEN",
                f"expected from_phase {expected_phase}, got {event.from_phase}",
            )
        expected_phase = event.to_phase
        expected_previous = event.event_digest

    if expected_phase is None:
        raise TaskInvariantError(
            "INVALID_SKILL_STREAM", "skill stream reached no valid phase"
        )
    return expected_phase


__all__ = [
    "ALLOWED_SKILL_PHASE_TRANSITIONS",
    "RoutePlanV1",
    "SCHEMA_ROUTE_PLAN",
    "SCHEMA_SKILL_USE_EVENT",
    "SkillUseEventV1",
    "SkillUsePhaseV1",
    "verify_skill_lifecycle_chain",
]
