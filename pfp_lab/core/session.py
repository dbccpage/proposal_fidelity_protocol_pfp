"""Run an admitted scenario, seal it into a receipt, and verify receipts by replay.

AuthorityEffect: None.
Contract: urn:pfp-lab:core:session:v1

This is the one use case every front end calls. ``run_scenario`` applies the
scenario's moves in order to a fresh ``Governor``; nothing here reads files,
the network or the clock, so the same scenario always yields the same session.

A receipt holds the scenario, the verdicts, the final state, the core version
and a SHA-256 digest over the canonical JSON of all of that. Canonical JSON is
``json.dumps`` with sorted keys, no insignificant whitespace and UTF-8 output.
Every value in a receipt is a string, an integer, a boolean, ``null``, a list
or an object (there are no floats), and over that domain this encoding agrees
with RFC 8785.

Verification never trusts the receipt's own numbers: it checks the digest,
then replays the scenario on this core and compares every verdict and the
final state.
"""

from __future__ import annotations

import hashlib
import json
from typing import Final, Literal

from pydantic import Field

from pfp_lab.core.admission import format_rational
from pfp_lab.core.contracts import (
    CORE_VERSION,
    ClaimIn,
    ScenarioIn,
    StateOut,
    Strict,
    VerdictOut,
    to_graph,
    to_move,
    verdict_out,
)
from pfp_lab.core.governor import Governor
from pfp_lab.core.obstruction import DEFAULT_SEARCH_BUDGET

RECEIPT_SCHEMA: Final = "pfp-lab.receipt.v1"
_DIGEST = r"^[0-9a-f]{64}$"


class SessionOut(Strict):
    scenario: ScenarioIn
    verdicts: tuple[VerdictOut, ...]
    final: StateOut


class ReceiptOut(Strict):
    schema_id: Literal["pfp-lab.receipt.v1"] = Field(alias="schema")
    core_version: str = Field(max_length=32)
    scenario: ScenarioIn
    verdicts: tuple[VerdictOut, ...]
    final: StateOut
    digest: str = Field(pattern=_DIGEST)


class VerifyReport(Strict):
    valid: bool
    digest: str
    problems: tuple[str, ...]


def run_scenario(scenario: ScenarioIn, *, budget: int = DEFAULT_SEARCH_BUDGET) -> SessionOut:
    """Apply every move of ``scenario`` in order; ``BudgetExceededError`` if a search runs out."""
    governor = Governor(to_graph(scenario), budget=budget)
    verdicts = tuple(verdict_out(governor.apply(to_move(item))) for item in scenario.moves)
    return SessionOut(scenario=scenario, verdicts=verdicts, final=state_out(governor))


def state_out(governor: Governor) -> StateOut:
    """The governor's current section, claims, defect and obstruction in wire form."""
    claims = tuple(
        ClaimIn(source=source, target=target, value=format_rational(value))
        for (source, target), value in governor.claims.items()
    )
    return StateOut(
        section={name: format_rational(value) for name, value in governor.section.items()},
        claims=claims,
        defect=format_rational(governor.defect()),
        obstruction=format_rational(governor.primary_obstruction()),
    )


def canonical_json(value: object) -> str:
    """Sorted keys, compact separators, UTF-8; see the module note on RFC 8785."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def receipt_digest(receipt: ReceiptOut) -> str:
    """SHA-256 of the canonical JSON of every receipt field except ``digest``."""
    body = receipt.model_dump(mode="json", by_alias=True, exclude={"digest"})
    return hashlib.sha256(canonical_json(body).encode("utf-8")).hexdigest()


def build_receipt(session: SessionOut) -> ReceiptOut:
    """Seal a session into a receipt whose digest binds every field."""
    draft = ReceiptOut(
        schema=RECEIPT_SCHEMA,
        core_version=CORE_VERSION,
        scenario=session.scenario,
        verdicts=session.verdicts,
        final=session.final,
        digest="0" * 64,
    )
    return draft.model_copy(update={"digest": receipt_digest(draft)})


def verify_receipt(receipt: ReceiptOut) -> VerifyReport:
    """Check the digest, then replay the scenario and compare what the core returns now."""
    problems: list[str] = []
    expected = receipt_digest(receipt)
    if expected != receipt.digest:
        problems.append(f"digest mismatch: receipt says {receipt.digest}, content hashes to {expected}")
    replay = run_scenario(receipt.scenario)
    problems.extend(_verdict_problems(receipt.verdicts, replay.verdicts))
    if replay.final != receipt.final:
        problems.append("final state differs from the replayed final state")
    return VerifyReport(valid=not problems, digest=expected, problems=tuple(problems))


def _verdict_problems(
    recorded: tuple[VerdictOut, ...],
    replayed: tuple[VerdictOut, ...],
) -> list[str]:
    if len(recorded) != len(replayed):
        return [f"receipt has {len(recorded)} verdicts; replay produced {len(replayed)}"]
    return [
        f"verdict {index} ({now.step_id}) differs from the replay"
        for index, (then, now) in enumerate(zip(recorded, replayed, strict=True))
        if then != now
    ]


__all__ = [
    "RECEIPT_SCHEMA",
    "ReceiptOut",
    "SessionOut",
    "VerifyReport",
    "build_receipt",
    "canonical_json",
    "receipt_digest",
    "run_scenario",
    "state_out",
    "verify_receipt",
]
