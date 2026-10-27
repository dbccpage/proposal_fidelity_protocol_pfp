"""C006 host scratch projection consumed by the shared PFP task-turn adapter.

This prepares one full-CUT proposal, not the complete C006 session experiment.
The host supplies independently computed facts; this module neither computes a
repair nor certifies Phi1. Mathematical admission, session fuel, provider budgets
and OEEIS detector admission remain with their existing owners. AM-4 here is a
factual repeat observation, not an automatically activated antibody.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from pfp.domain.shared_kernel.canonical import domain_digest
from pfp.infrastructure.task_turn import PreparedTaskTurn, prepare_task_turn


def _integer(value: int) -> int:
    if type(value) is not int:
        raise ValueError("EXACT_INTEGER_REQUIRED")
    return value


def _pairs(values: dict[str, int]) -> tuple[tuple[str, int], ...]:
    if type(values) is not dict or not values:
        raise ValueError("NONEMPTY_HOST_FACTS_REQUIRED")
    if any(type(key) is not str or not key for key in values):
        raise ValueError("HOST_FACT_IDENTIFIER_REQUIRED")
    return tuple(sorted((key, _integer(value)) for key, value in values.items()))


def _identifiers(values, *, allowed=None) -> tuple[str, ...]:
    if type(values) not in (tuple, list):
        raise ValueError("HOST_IDENTIFIER_SEQUENCE_REQUIRED")
    if any(type(value) is not str or not value for value in values):
        raise ValueError("HOST_FACT_IDENTIFIER_REQUIRED")
    if len(set(values)) != len(values) or (allowed is not None and not set(values) <= allowed):
        raise ValueError("INVALID_HOST_IDENTIFIER_SET")
    return tuple(sorted(values))


@dataclass(frozen=True, slots=True)
class HostScratchLedger:
    """Copied host observations, with history/diagnostics outside state identity.

    ``board_bytes`` at construction must be the original host-frozen public
    board. The hash is provenance, not authentication or mathematical evidence.
    Only current facts appear; no optimal cochain, target chord or solver hint
    is accepted by this API. Caller-controlled recent turns retain their text.
    """

    board_sha256: str
    claims: tuple[tuple[str, int], ...]
    asserted_edges: tuple[str, ...]
    phi1: int
    cycle_residuals: tuple[tuple[str, int], ...]
    closed_chords: tuple[str, ...]
    last_move_sha256: str | None
    stationary_counter: int
    last_two_turns: tuple[str, ...]

    @classmethod
    def from_host(cls, *, board_bytes: bytes, claims: dict[str, int],
                  asserted_edges, phi1: int, cycle_residuals: dict[str, int],
                  closed_chords=(), last_move_sha256=None, stationary_counter=0,
                  last_two_turns=()) -> HostScratchLedger:
        if type(board_bytes) is not bytes or not board_bytes:
            raise ValueError("HOST_BOARD_BYTES_REQUIRED")
        if _integer(phi1) < 0 or _integer(stationary_counter) < 0:
            raise ValueError("NEGATIVE_HOST_COUNTER")
        if last_move_sha256 is not None and (
            type(last_move_sha256) is not str or len(last_move_sha256) != 64
            or any(char not in "0123456789abcdef" for char in last_move_sha256)
        ):
            raise ValueError("LAST_MOVE_DIGEST_REQUIRED")
        if type(last_two_turns) not in (tuple, list) or any(
            type(turn) is not str for turn in last_two_turns
        ):
            raise ValueError("TURN_TEXT_REQUIRED")
        claim_pairs = _pairs(claims)
        edges = set(claims)
        return cls(sha256(board_bytes).hexdigest(), claim_pairs,
                   _identifiers(asserted_edges, allowed=edges), phi1,
                   _pairs(cycle_residuals), _identifiers(closed_chords, allowed=edges),
                   last_move_sha256, stationary_counter, tuple(last_two_turns[-2:]))

    @property
    def state_sha256(self) -> str:
        # A diagnostic counter/history update cannot manufacture a changed board
        # and let an otherwise identical stationary CUT evade the observation.
        return domain_digest("pfp.c006.host-state.v1", {
            "board_sha256": self.board_sha256, "claims": dict(self.claims),
            "asserted_edges": list(self.asserted_edges), "phi1": self.phi1,
            "cycle_residuals": dict(self.cycle_residuals),
            "closed_chords": list(self.closed_chords),
        })

    def public_context(self) -> dict:
        return {"current_claims": dict(self.claims), "asserted_edges": list(self.asserted_edges),
                "phi1": self.phi1, "cycle_residuals": dict(self.cycle_residuals),
                "closed_chords": list(self.closed_chords),
                "last_move_sha256": self.last_move_sha256,
                "stationary_counter": self.stationary_counter,
                "last_two_turns": list(self.last_two_turns)}


def _cut_digest(ledger: HostScratchLedger, claims: dict[str, int]) -> str:
    pairs = _pairs(claims)
    if {edge for edge, _ in pairs} != {edge for edge, _ in ledger.claims}:
        raise ValueError("FULL_CUT_REQUIRED")
    return domain_digest("pfp.c006.full-cut.v1", dict(pairs))


@dataclass(frozen=True, slots=True)
class StationaryCutBinding:
    host_state_sha256: str
    cut_sha256: str


def stationary_cut_binding(ledger: HostScratchLedger, claims: dict[str, int],
                           *, observed_phi1: int) -> StationaryCutBinding:
    """Record an actual host-evaluated stationary result, never model Phi1."""
    if _integer(observed_phi1) != ledger.phi1 or ledger.phi1 == 0:
        raise ValueError("NOT_STATIONARY")
    return StationaryCutBinding(ledger.state_sha256, _cut_digest(ledger, claims))


def stationary_repeat(ledger: HostScratchLedger, claims: dict[str, int],
                      previous: StationaryCutBinding | None) -> bool:
    """AM-4 observation only; callers own admission, suspension and turn fuel."""
    digest = _cut_digest(ledger, claims)
    return (ledger.phi1 > 0 and previous is not None
            and previous == StationaryCutBinding(ledger.state_sha256, digest))


def prepare_scratch_cut_turn(ledger: HostScratchLedger, *, protocol_path: Path,
                             protocol_sha256: str, task_id: str,
                             attempt_id: str) -> PreparedTaskTurn:
    """Prepare an actual current-IDE/provider brief through canonical PFP.

    The explicit host source pin binds the retained original C006 specification.
    Its worked answers are deliberately not copied into the participant brief.
    Submit actual bytes with ``turn.check(raw, judges=..., require_checker=True)``
    when a host admission checker is available. Shape-only checks stay UNVERIFIED.
    Provider dispatch and reservation use the existing caller gateway/ledger.
    """
    if sha256(protocol_path.read_bytes()).hexdigest() != protocol_sha256:
        raise ValueError("C006_PROTOCOL_SOURCE_MISMATCH")
    claim_schema = {"type": "object", "properties": {
        edge: {"type": "integer"} for edge, _ in ledger.claims},
        "required": [edge for edge, _ in ledger.claims], "additionalProperties": False}
    return prepare_task_turn(
        system="Propose a full integer-cochain CUT using only the supplied public host observations.",
        user="Return one CUT covering every current edge. The host admits a CUT only if its "
             "independently checked Phi1 strictly decreases or reaches zero. This step does not "
             "perform ASSERT, LIFT_REQUEST or VERIFY and cannot certify session completion.",
        task_id=task_id, attempt_id=attempt_id, checker_id="c006-host-cut-v1",
        context={"protocol": "C006", "protocol_sha256": protocol_sha256,
                 "board_sha256": ledger.board_sha256, "host_state_sha256": ledger.state_sha256,
                 "host_scratch": ledger.public_context()},
        answer_schema={"type": "object", "properties": {
            "move": {"const": "CUT"}, "claims": claim_schema},
            "required": ["move", "claims"], "additionalProperties": False},
    )


def check_scratch_cut_turn(turn: PreparedTaskTurn, ledger: HostScratchLedger,
                           raw_reply: bytes, *, previous: StationaryCutBinding | None = None,
                           judges=()) -> dict:
    """Consume the real reply through PFP, then observe a source-bound AM-4 repeat.

    A repeat adds an observation and an answer-free suggested action. It does not
    replace the independently configured checker result or spend another turn.
    A host wanting mathematical admission must supply its actual admission judge;
    without one the result remains UNVERIFIED. No provider calls occur here.
    """
    context = turn.task.case.get("context", {})
    if (context.get("host_state_sha256") != ledger.state_sha256
            or context.get("board_sha256") != ledger.board_sha256
            or context.get("host_scratch") != ledger.public_context()):
        raise ValueError("SCRATCH_TURN_STATE_MISMATCH")
    checked = turn.check(raw_reply, judges=judges)
    observation = None
    if checked["schema_valid"] and stationary_repeat(ledger, checked["answer"]["claims"], previous):
        observation = {
            "code": "AM-4-STATIONARY-REPEAT",
            "suggested_action": "REQUEST_DIFFERENT_CANDIDATE_OR_LIFT",
            "host_state_sha256": ledger.state_sha256,
            "cut_sha256": _cut_digest(ledger, checked["answer"]["claims"]),
        }
    return {**checked, "scratch_observation": observation}
