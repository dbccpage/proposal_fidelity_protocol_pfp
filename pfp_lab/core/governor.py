"""The PFP governor: four moves over an exact section and claim store.

AuthorityEffect: None.
Contract: urn:pfp-lab:core:governor:v1
Provenance: ported from ``MoveType``, ``GovernorVerdict``, ``ExecutionRecord`` and
``L1SymbolGameGovernor`` in the Paper 005 governor;
``pfp_lab/core/PROVENANCE.md`` records the digest and every change.

The proposer has no authority: every number in a verdict is recomputed here.

* ASSERT records one edge claim (optionally refused if the defect would rise).
* CUT proposes either a new section (admitted only if ``D`` does not rise) or a
  complete replacement of the claims (admitted only if ``Phi_1`` does not rise,
  then the section is projected with ``P_S``).
* VERIFY checks an obligation: ZERO_DEFECT, ZERO_OBSTRUCTION or
  ``EDGE_MATCH:u,v``. It never changes state and is not recorded in history.
* RETRACT restores the section and claims saved at an earlier recorded step.

A refused move leaves the state untouched. Step identifiers default to
``step_NNN`` from a counter that advances on every move, admitted or not.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction

from pfp_lab.core.graph import ConstraintGraph, EdgeKey
from pfp_lab.core.obstruction import DEFAULT_SEARCH_BUDGET, obstruction, project, section_defect

_ZERO = Fraction(0)


class MoveKind(StrEnum):
    ASSERT = "ASSERT"
    CUT = "CUT"
    VERIFY = "VERIFY"
    RETRACT = "RETRACT"


class Status(StrEnum):
    ASSERTED = "Asserted"
    PROVISIONAL_ASSERT = "ProvisionalAssert"
    MONOTONIC_DESCENT = "MonotonicDescent"
    EXACT_REPAIR = "ExactRepair"
    IDEMPOTENT_STATIONARY = "IdempotentStationary"
    DEFECT_INCREASE = "DefectIncrease"
    INVARIANT_VIOLATION = "InvariantViolation"
    CARRIER_VIOLATION = "CarrierViolation"
    MOVE_VIOLATION = "MoveViolation"
    INCOMPLETE_PROPOSAL = "IncompleteProposal"
    REFUSED = "Refused"
    RETRACTED = "Retracted"
    VERIFIED = "Verified"
    VERIFICATION_FAILED = "VerificationFailed"


@dataclass(frozen=True, slots=True)
class AssertMove:
    source: str
    target: str
    value: Fraction
    step_id: str | None = None
    provisional: bool = False
    enforce_monotonicity: bool = False


@dataclass(frozen=True, slots=True)
class CutMove:
    """Exactly one of ``section`` or ``claims`` must be given; the governor refuses otherwise."""

    section: tuple[tuple[str, Fraction], ...] | None = None
    claims: tuple[tuple[EdgeKey, Fraction], ...] | None = None
    step_id: str | None = None


@dataclass(frozen=True, slots=True)
class VerifyMove:
    obligation: str
    step_id: str | None = None


@dataclass(frozen=True, slots=True)
class RetractMove:
    target_step_id: str
    reason: str = ""
    step_id: str | None = None


Move = AssertMove | CutMove | VerifyMove | RetractMove


@dataclass(frozen=True, slots=True)
class Verdict:
    step_id: str
    move: MoveKind
    admitted: bool
    status: Status
    defect_before: Fraction
    defect_after: Fraction
    details: str


@dataclass(frozen=True, slots=True)
class Record:
    """An admitted, state-changing step and the state it left behind."""

    step_id: str
    parent_step_id: str | None
    move: MoveKind
    status: Status
    section: tuple[tuple[str, Fraction], ...]
    claims: tuple[tuple[EdgeKey, Fraction], ...]


class Governor:
    """Exact state machine over one declared graph."""

    def __init__(self, graph: ConstraintGraph, *, budget: int = DEFAULT_SEARCH_BUDGET) -> None:
        self.graph = graph
        self.budget = budget
        self._section: dict[str, Fraction] = {name: _ZERO for name in graph.vertices}
        self._claims: dict[EdgeKey, Fraction] = {}
        self._history: list[Record] = []
        self._counter = 0

    @property
    def section(self) -> dict[str, Fraction]:
        return dict(self._section)

    @property
    def claims(self) -> dict[EdgeKey, Fraction]:
        return dict(self._claims)

    @property
    def history(self) -> tuple[Record, ...]:
        return tuple(self._history)

    def defect(self, section: dict[str, Fraction] | None = None) -> Fraction:
        """``D(s)`` for the current section, or for a proposed one."""
        chosen = self._section if section is None else section
        return section_defect(self.graph, self._claims, chosen)

    def primary_obstruction(self) -> Fraction:
        """``Phi_1`` of the current claims."""
        value, _ = obstruction(self.graph, self._claims, budget=self.budget)
        return value

    def apply(self, move: Move) -> Verdict:
        """Run one move and return the host's verdict."""
        self._counter += 1
        step_id = move.step_id or f"step_{self._counter:03d}"
        if isinstance(move, AssertMove):
            return self._assert(move, step_id)
        if isinstance(move, CutMove):
            return self._cut(move, step_id)
        if isinstance(move, VerifyMove):
            return self._verify(move, step_id)
        return self._retract(move, step_id)

    # ASSERT -------------------------------------------------------------

    def _assert(self, move: AssertMove, step_id: str) -> Verdict:
        before = self.defect()
        problem = self._assert_problem(move)
        if problem is not None:
            status, details = problem
            return _refusal(step_id, MoveKind.ASSERT, status, before, before, details)
        key = (move.source, move.target)
        trial = dict(self._claims)
        trial[key] = move.value
        after = section_defect(self.graph, trial, self._section)
        if move.enforce_monotonicity and after > before:
            details = f"ASSERT would raise the section defect from {before} to {after}."
            return _refusal(step_id, MoveKind.ASSERT, Status.DEFECT_INCREASE, before, after, details)
        self._claims = trial
        status = Status.PROVISIONAL_ASSERT if move.provisional else Status.ASSERTED
        details = f"Asserted claim {move.source} -> {move.target} = {move.value} ({status.value})."
        return self._commit(step_id, MoveKind.ASSERT, status, before, after, details)

    def _assert_problem(self, move: AssertMove) -> tuple[Status, str] | None:
        if move.source == move.target:
            return Status.INVARIANT_VIOLATION, f"Self-cut {move.source} -> {move.target} violates irreflexivity."
        if not (self.graph.has_vertex(move.source) and self.graph.has_vertex(move.target)):
            return Status.INVARIANT_VIOLATION, f"Vertices ({move.source}, {move.target}) leave the declared carrier."
        if self.graph.edge(move.source, move.target) is None:
            return Status.MOVE_VIOLATION, f"Edge ({move.source}, {move.target}) is not declared."
        return None

    # CUT ----------------------------------------------------------------

    def _cut(self, move: CutMove, step_id: str) -> Verdict:
        if move.section is not None and move.claims is not None:
            current = self.defect()
            details = "CUT requires exactly one of a section or a claim set."
            return _refusal(step_id, MoveKind.CUT, Status.MOVE_VIOLATION, current, current, details)
        if move.section is not None:
            return self._cut_section(dict(move.section), step_id)
        if move.claims is not None:
            return self._cut_claims(dict(move.claims), step_id)
        current = self.defect()
        details = "CUT must propose a section or a claim set."
        return _refusal(step_id, MoveKind.CUT, Status.REFUSED, current, current, details)

    def _cut_section(self, proposed: dict[str, Fraction], step_id: str) -> Verdict:
        before = self.defect()
        extra = sorted(set(proposed) - set(self.graph.vertices))
        if extra:
            details = f"Section names undeclared vertices {extra}."
            return _refusal(step_id, MoveKind.CUT, Status.CARRIER_VIOLATION, before, before, details)
        after = self.defect(proposed)
        if after > before:
            details = f"Section defect would rise from {before} to {after}."
            return _refusal(step_id, MoveKind.CUT, Status.DEFECT_INCREASE, before, after, details)
        self._section = {name: proposed.get(name, _ZERO) for name in self.graph.vertices}
        status = _descent_status(before, after)
        details = f"CUT admitted with status {status.value} ({before} -> {after})."
        return self._commit(step_id, MoveKind.CUT, status, before, after, details)

    def _cut_claims(self, proposed: dict[EdgeKey, Fraction], step_id: str) -> Verdict:
        problem = self._claims_problem(proposed)
        if problem is not None:
            current = self.primary_obstruction()
            status, details = problem
            return _refusal(step_id, MoveKind.CUT, status, current, current, details)
        before = self.primary_obstruction()
        after, _ = obstruction(self.graph, proposed, budget=self.budget)
        if after > before:
            details = f"Primary obstruction would rise from {before} to {after}."
            return _refusal(step_id, MoveKind.CUT, Status.DEFECT_INCREASE, before, after, details)
        projected = project(self.graph, proposed, self._section, budget=self.budget)
        self._claims = proposed
        self._section = projected
        status = _descent_status(before, after)
        details = f"Relational CUT admitted ({before} -> {after})."
        return self._commit(step_id, MoveKind.CUT, status, before, after, details)

    def _claims_problem(self, proposed: dict[EdgeKey, Fraction]) -> tuple[Status, str] | None:
        # Each test runs over every proposed edge before the next test starts, as in Paper 005.
        tests: tuple[tuple[Callable[[str, str], bool], Status, str], ...] = (
            (lambda s, t: s == t, Status.INVARIANT_VIOLATION, "Self-cut ({}, {}) violates irreflexivity."),
            (self._off_carrier, Status.CARRIER_VIOLATION, "Vertices ({}, {}) leave the declared carrier."),
            (lambda s, t: self.graph.edge(s, t) is None, Status.MOVE_VIOLATION, "Edge ({}, {}) is not declared."),
        )
        for test, status, template in tests:
            offending = next(((s, t) for s, t in proposed if test(s, t)), None)
            if offending is not None:
                return status, template.format(*offending)
        missing = [item.key for item in self.graph.edges if item.key not in proposed]
        if missing:
            return Status.INCOMPLETE_PROPOSAL, f"A relational CUT must give every declared edge; it omits {missing}."
        return None

    def _off_carrier(self, source: str, target: str) -> bool:
        return not (self.graph.has_vertex(source) and self.graph.has_vertex(target))

    # VERIFY -------------------------------------------------------------

    def _verify(self, move: VerifyMove, step_id: str) -> Verdict:
        current = self.defect()
        passed, details = self._check_obligation(move.obligation, current)
        status = Status.VERIFIED if passed else Status.VERIFICATION_FAILED
        return Verdict(step_id, MoveKind.VERIFY, passed, status, current, current, details)

    def _check_obligation(self, obligation: str, current: Fraction) -> tuple[bool, str]:
        if obligation == "ZERO_DEFECT":
            if current == _ZERO:
                return True, "Section defect is exactly zero."
            return False, f"Section defect is {current}."
        if obligation == "ZERO_OBSTRUCTION":
            value = self.primary_obstruction()
            if value == _ZERO:
                return True, "Primary obstruction Phi_1 is zero."
            return False, f"Primary obstruction Phi_1 is {value}."
        if obligation.startswith("EDGE_MATCH:"):
            return self._edge_match(obligation)
        return False, f"Unknown obligation {obligation!r}."

    def _edge_match(self, obligation: str) -> tuple[bool, str]:
        pair = obligation.removeprefix("EDGE_MATCH:").split(",")
        if len(pair) != 2 or self.graph.edge(pair[0], pair[1]) is None:
            return False, f"EDGE_MATCH needs a declared directed edge: {obligation!r}."
        source, target = pair
        claim = self._claims.get((source, target), _ZERO)
        actual = self._section[target] - self._section[source]
        return claim == actual, f"Edge {source}->{target}: claim={claim}, actual={actual}."

    # RETRACT ------------------------------------------------------------

    def _retract(self, move: RetractMove, step_id: str) -> Verdict:
        before = self.defect()
        target = next((item for item in self._history if item.step_id == move.target_step_id), None)
        if target is None:
            details = f"Step {move.target_step_id!r} is not in the recorded history."
            return _refusal(step_id, MoveKind.RETRACT, Status.REFUSED, before, before, details)
        self._section = dict(target.section)
        self._claims = dict(target.claims)
        after = self.defect()
        details = f"State restored to step {move.target_step_id!r}. Reason: {move.reason}"
        return self._commit(step_id, MoveKind.RETRACT, Status.RETRACTED, before, after, details)

    # shared -------------------------------------------------------------

    def _commit(
        self,
        step_id: str,
        move: MoveKind,
        status: Status,
        before: Fraction,
        after: Fraction,
        details: str,
    ) -> Verdict:
        parent = self._history[-1].step_id if self._history else None
        self._history.append(
            Record(
                step_id=step_id,
                parent_step_id=parent,
                move=move,
                status=status,
                section=tuple(self._section.items()),
                claims=tuple(self._claims.items()),
            )
        )
        return Verdict(step_id, move, True, status, before, after, details)


def _refusal(
    step_id: str,
    move: MoveKind,
    status: Status,
    before: Fraction,
    after: Fraction,
    details: str,
) -> Verdict:
    return Verdict(step_id, move, False, status, before, after, details)


def _descent_status(before: Fraction, after: Fraction) -> Status:
    if after == _ZERO and before > _ZERO:
        return Status.EXACT_REPAIR
    if after < before:
        return Status.MONOTONIC_DESCENT
    return Status.IDEMPOTENT_STATIONARY


__all__ = [
    "AssertMove",
    "CutMove",
    "Governor",
    "Move",
    "MoveKind",
    "Record",
    "RetractMove",
    "Status",
    "Verdict",
    "VerifyMove",
]
