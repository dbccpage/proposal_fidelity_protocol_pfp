"""Package re-implementation of a Demo 3 style host for PFP Paper 003.

This is not the repository's canonical Demo 3 host; paper Section 4.1 lists the
differences. It provides:

1. Phases: INTAKE -> COVERAGE -> WITNESS -> VERIFY -> TERMINAL.
2. Fuel: each attempted batch costs one unit, which a rollback does not return;
   the host enters TERMINAL with FUEL_EXHAUSTED when the last unit is spent.
3. Atomic batches: a refused batch restores the prior covered elements, witness,
   and phase.
4. A SHA-256 digest chain over the prior digest, the proposed moves, and the
   decision. The chain shows internal consistency only; it has no key and does
   not authenticate who produced a receipt.

Every nonempty route returns ``NO_NATIVE_PORT``; no witness is certified.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence


class HostPhase(str, Enum):
    INTAKE = "INTAKE"
    COVERAGE = "COVERAGE"
    WITNESS = "WITNESS"
    VERIFY = "VERIFY"
    TERMINAL = "TERMINAL"


class HostExit(str, Enum):
    FUEL_EXHAUSTED = "FUEL_EXHAUSTED"
    SCOPED_CERTIFICATE = "SCOPED_CERTIFICATE"
    REFUSED = "REFUSED"
    REJECTED = "REJECTED"


class DemoRefusal(Exception):
    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail

    def __repr__(self) -> str:
        return f"DemoRefusal(code={self.code!r}, detail={self.detail!r})"


@dataclass
class MoveProposal:
    move_type: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "move_type": self.move_type,
            "payload": copy.deepcopy(self.payload),
        }


def move_mapping(move: MoveProposal) -> dict[str, Any]:
    return move.to_dict()


@dataclass
class HostState:
    fixture_id: str
    arm: str
    current_phase: HostPhase
    remaining_fuel: int
    covered_elements: set[str] = field(default_factory=set)
    witness_candidate: dict[str, Any] | None = None
    terminal_exit: HostExit | None = None
    terminal_label: str | None = None
    state_digest: str = ""

    def copy(self) -> HostState:
        return HostState(
            fixture_id=self.fixture_id,
            arm=self.arm,
            current_phase=self.current_phase,
            remaining_fuel=self.remaining_fuel,
            covered_elements=set(self.covered_elements),
            witness_candidate=copy.deepcopy(self.witness_candidate),
            terminal_exit=self.terminal_exit,
            terminal_label=self.terminal_label,
            state_digest=self.state_digest,
        )


@dataclass
class StepReceipt:
    host_decision: str
    batch_rolled_back: bool
    prior_state_digest: str
    new_state_digest: str
    event_bytes_hex: str = ""
    detector_findings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "host_decision": self.host_decision,
            "batch_rolled_back": self.batch_rolled_back,
            "prior_state_digest": self.prior_state_digest,
            "new_state_digest": self.new_state_digest,
            "event_bytes_hex": self.event_bytes_hex,
            "detector_findings": list(self.detector_findings),
        }


def canonical_json(obj: Any) -> bytes:
    """Sorted keys, compact separators, no NaN/Infinity, UTF-8 output.

    This is a declared convention, not a full RFC 8785 implementation.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def initial_digest(fixture_id: str, arm: str) -> str:
    canonical = canonical_json({"arm": arm, "fixture_id": fixture_id})
    return hashlib.sha256(canonical).hexdigest()


def chain_digest(prior_digest: str, ev_bytes: bytes, decision: Any) -> str:
    decision_str = decision.value if hasattr(decision, "value") else str(decision)
    raw = f"{prior_digest}:{ev_bytes.hex()}:{decision_str}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def event_bytes(moves: Sequence[MoveProposal] | Sequence[dict[str, Any]]) -> bytes:
    normalized = []
    for m in moves:
        if isinstance(m, MoveProposal):
            normalized.append(m.to_dict())
        else:
            normalized.append(m)
    return canonical_json(normalized)


KNOWN_FIXTURES: dict[str, str] = {
    "gauge_even_triangle": "restricted_diagonal_sign_gauge",
    "gauge_odd_triangle": "frustrated_parity_gauge",
    "cochain_exact_cycle": "discrete_gauge_potential",
    "meron_two_pairs_survivor": "meron_cluster_involution",
    "frustrated_square_diagonal": "frustrated_diagonal_sign_gauge",
}


def verify_route(route_name: str) -> DemoRefusal:
    if not route_name:
        raise DemoRefusal("UNKNOWN_ROUTE", "")
    return DemoRefusal("NO_NATIVE_PORT", route_name)


class Demo3HostEngine:
    def __init__(self, fixture_id: str, arm: str, initial_fuel: int = 11) -> None:
        if isinstance(initial_fuel, bool) or not isinstance(initial_fuel, int) or initial_fuel < 0:
            raise DemoRefusal("INVALID_FUEL", str(initial_fuel))

        if fixture_id not in KNOWN_FIXTURES:
            raise DemoRefusal("UNKNOWN_FIXTURE", fixture_id)

        self.fixture_id = fixture_id
        self.arm = arm
        self.fixture = {
            "fixture_id": fixture_id,
            "route": KNOWN_FIXTURES[fixture_id],
        }
        init_dig = initial_digest(fixture_id, arm)
        self.state = HostState(
            fixture_id=fixture_id,
            arm=arm,
            current_phase=HostPhase.INTAKE,
            remaining_fuel=initial_fuel,
            covered_elements=set(),
            witness_candidate=None,
            terminal_exit=None,
            terminal_label=None,
            state_digest=init_dig,
        )
        self.route_refusal: DemoRefusal | None = None

    def execute_batch(self, proposals: Sequence[MoveProposal]) -> StepReceipt:
        prior_digest = self.state.state_digest
        ev_bytes = event_bytes(proposals)

        # 1. Terminal state check
        if self.state.current_phase == HostPhase.TERMINAL:
            decision = "REJECT_TERMINAL_STATE"
            new_digest = chain_digest(prior_digest, ev_bytes, decision)
            self.state.state_digest = new_digest
            return StepReceipt(
                host_decision=decision,
                batch_rolled_back=True,
                prior_state_digest=prior_digest,
                new_state_digest=new_digest,
                event_bytes_hex=ev_bytes.hex(),
                detector_findings=(),
            )

        # 2. Fuel exhaustion check
        if self.state.remaining_fuel == 0:
            self.state.current_phase = HostPhase.TERMINAL
            self.state.terminal_exit = HostExit.FUEL_EXHAUSTED
            decision = HostExit.FUEL_EXHAUSTED.value
            new_digest = chain_digest(prior_digest, ev_bytes, decision)
            self.state.state_digest = new_digest
            return StepReceipt(
                host_decision=decision,
                batch_rolled_back=True,
                prior_state_digest=prior_digest,
                new_state_digest=new_digest,
                event_bytes_hex=ev_bytes.hex(),
                detector_findings=(),
            )

        # Attempting a batch costs 1 unit of fuel outside semantic rollback
        attempt_fuel = self.state.remaining_fuel - 1

        # 3. Empty batch check
        if not proposals:
            decision = "REJECT_EMPTY_BATCH"
            new_digest = chain_digest(prior_digest, ev_bytes, decision)
            self.state.remaining_fuel = attempt_fuel
            self.state.state_digest = new_digest
            if attempt_fuel == 0:
                self.state.current_phase = HostPhase.TERMINAL
                self.state.terminal_exit = HostExit.FUEL_EXHAUSTED
            return StepReceipt(
                host_decision=decision,
                batch_rolled_back=True,
                prior_state_digest=prior_digest,
                new_state_digest=new_digest,
                event_bytes_hex=ev_bytes.hex(),
                detector_findings=(),
            )

        # 4. Upfront check for invalid batch structure: move after VERIFY
        verify_indices = [i for i, p in enumerate(proposals) if p.move_type == "VERIFY"]
        if verify_indices and verify_indices[0] < len(proposals) - 1:
            decision = "REJECT_MOVE_AFTER_VERIFY"
            new_digest = chain_digest(prior_digest, ev_bytes, decision)
            self.state.remaining_fuel = attempt_fuel
            self.state.state_digest = new_digest
            if attempt_fuel == 0:
                self.state.current_phase = HostPhase.TERMINAL
                self.state.terminal_exit = HostExit.FUEL_EXHAUSTED
            return StepReceipt(
                host_decision=decision,
                batch_rolled_back=True,
                prior_state_digest=prior_digest,
                new_state_digest=new_digest,
                event_bytes_hex=ev_bytes.hex(),
                detector_findings=(),
            )

        snapshot = self.state.copy()
        snapshot.remaining_fuel = attempt_fuel
        temp_state = self.state.copy()
        temp_state.remaining_fuel = attempt_fuel
        saw_verify = False
        decision = "ACCEPTED"
        rollback = False

        for prop in proposals:
            if saw_verify:
                decision = "REJECT_MOVE_AFTER_VERIFY"
                rollback = True
                break

            if prop.move_type == "COVER_ELEMENT":
                elem_id = prop.payload.get("element_id")
                if not isinstance(elem_id, str) or isinstance(elem_id, bool) or not elem_id:
                    decision = "REJECT_MALFORMED_PAYLOAD"
                    rollback = True
                    break
                temp_state.covered_elements.add(elem_id)
                if temp_state.current_phase == HostPhase.INTAKE:
                    temp_state.current_phase = HostPhase.COVERAGE

            elif prop.move_type == "PROPOSE_WITNESS":
                temp_state.witness_candidate = copy.deepcopy(prop.payload)
                temp_state.current_phase = HostPhase.WITNESS

            elif prop.move_type == "HOLD_DETECTOR_FEEDBACK":
                decision = "HOLD_DETECTOR_FEEDBACK"

            elif prop.move_type == "VERIFY":
                saw_verify = True
                if not temp_state.covered_elements:
                    decision = "REJECT_INCOMPLETE_COVERAGE"
                    rollback = True
                    break
                temp_state.current_phase = HostPhase.VERIFY
                route = self.fixture["route"]
                refusal = verify_route(route)
                if isinstance(refusal, DemoRefusal):
                    decision = refusal.code
                    self.route_refusal = refusal
                    rollback = True
                    break
            else:
                decision = f"REJECT_UNKNOWN_MOVE:{prop.move_type}"
                rollback = True
                break

        new_digest = chain_digest(prior_digest, ev_bytes, decision)

        if rollback:
            self.state = snapshot
            self.state.remaining_fuel = attempt_fuel
            if attempt_fuel == 0:
                self.state.current_phase = HostPhase.TERMINAL
                self.state.terminal_exit = HostExit.FUEL_EXHAUSTED
            self.state.state_digest = new_digest
            return StepReceipt(
                host_decision=decision,
                batch_rolled_back=True,
                prior_state_digest=prior_digest,
                new_state_digest=new_digest,
                event_bytes_hex=ev_bytes.hex(),
                detector_findings=(),
            )

        temp_state.remaining_fuel = attempt_fuel
        if attempt_fuel == 0 and temp_state.current_phase != HostPhase.TERMINAL:
            temp_state.current_phase = HostPhase.TERMINAL
            temp_state.terminal_exit = HostExit.FUEL_EXHAUSTED
        temp_state.state_digest = new_digest
        self.state = temp_state
        return StepReceipt(
            host_decision=decision,
            batch_rolled_back=False,
            prior_state_digest=prior_digest,
            new_state_digest=new_digest,
            event_bytes_hex=ev_bytes.hex(),
            detector_findings=(),
        )


def run_cell(fixture_id: str, arm: str) -> dict[str, Any]:
    if arm == "D":
        raise DemoRefusal("ARM_D_IN_WORKFLOWS", "Arm D runs in workflows")

    engine = Demo3HostEngine(fixture_id, arm)
    proposals = [
        MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
        MoveProposal("PROPOSE_WITNESS", {"witness_type": "standard", "witness": [0, 1, 0]}),
        MoveProposal("VERIFY", {}),
    ]
    receipt = engine.execute_batch(proposals)
    return {
        "fixture_id": fixture_id,
        "arm": arm,
        "steps": [receipt.to_dict()],
        "terminal_exit": engine.state.terminal_exit.value if engine.state.terminal_exit else None,
        "host_decision": receipt.host_decision,
    }


def assemble_receipt() -> dict[str, Any]:
    """Run one scripted batch in each of the 30 cells (5 package fixtures x 6 arms).

    The assembled receipt is unverified until passed to ``verify_receipt_bytes``.
    """
    fixtures = list(KNOWN_FIXTURES.keys())[:5]
    arms = ["P", "T", "C", "R", "D", "A"]
    cells = []

    for f_id in fixtures:
        for arm in arms:
            engine = Demo3HostEngine(f_id, arm, initial_fuel=11)
            if arm == "D":
                receipt = engine.execute_batch([MoveProposal("HOLD_DETECTOR_FEEDBACK", {})])
            else:
                receipt = engine.execute_batch([
                    MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
                    MoveProposal("PROPOSE_WITNESS", {"witness_type": "standard", "witness": [0, 1, 0]}),
                    MoveProposal("VERIFY", {}),
                ])
            cell = {
                "fixture_id": f_id,
                "arm": arm,
                "steps": [receipt.to_dict()],
                "terminal_exit": engine.state.terminal_exit.value if engine.state.terminal_exit else None,
            }
            cells.append(cell)

    return {
        "status": "ASSEMBLED",
        "route": "NO_NATIVE_PORT",
        "cell_count": len(cells),
        "cells": cells,
    }


def verify_receipt_bytes(data: bytes) -> dict[str, Any]:
    """Check a 30-cell receipt by recomputing each cell's SHA-256 digest chain.

    Refuses empty or blank input, malformed JSON, an incomplete or duplicated
    matrix, chain discontinuities, digest mismatches, and any certificate label
    (the route port is missing). It does not check fuel or the scripted arm
    sequences, and anyone can recompute the digests of an edited receipt.
    """
    if not data or data == b"{}" or data.strip() == b"{}":
        raise DemoRefusal("INVALID_RECEIPT", "Receipt data is empty or blank JSON object")

    try:
        parsed = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise DemoRefusal("MALFORMED_JSON", str(e)) from e

    if not isinstance(parsed, dict):
        raise DemoRefusal("INVALID_RECEIPT", "Receipt must be a JSON dictionary")

    cells = parsed.get("cells")
    if not isinstance(cells, list) or len(cells) != 30:
        raise DemoRefusal(
            "INCOMPLETE_MATRIX",
            f"Expected 30 cells, found {len(cells) if isinstance(cells, list) else 0}",
        )

    expected_fixtures = set(list(KNOWN_FIXTURES.keys())[:5])
    expected_arms = {"P", "T", "C", "R", "D", "A"}
    seen_cells: set[tuple[str, str]] = set()

    for cell in cells:
        if not isinstance(cell, dict):
            raise DemoRefusal("MALFORMED_CELL", "Cell must be a dictionary")
        f_id = cell.get("fixture_id", "")
        arm = cell.get("arm", "")
        if (
            not isinstance(f_id, str)
            or not isinstance(arm, str)
            or f_id not in expected_fixtures
            or arm not in expected_arms
        ):
            raise DemoRefusal("UNKNOWN_CELL_COORDINATES", f"{f_id}:{arm}")
        if (f_id, arm) in seen_cells:
            raise DemoRefusal("DUPLICATE_CELL", f"Duplicate cell {f_id}:{arm}")
        seen_cells.add((f_id, arm))

        # A certificate label is impossible while the route port is missing.
        term_exit = cell.get("terminal_exit")
        if term_exit in ("SCOPED_CERTIFICATE", HostExit.SCOPED_CERTIFICATE):
            raise DemoRefusal(
                "FORGED_CERTIFICATE",
                f"Cell {f_id}:{arm} claims SCOPED_CERTIFICATE under missing route ports",
            )

        steps = cell.get("steps")
        if not isinstance(steps, list) or not steps:
            raise DemoRefusal("MISSING_STEPS", f"Cell {f_id}:{arm} has no execution steps")

        # Recompute the digest chain for this cell from its initial digest.
        expected_digest = initial_digest(f_id, arm)
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                raise DemoRefusal("MALFORMED_STEP", f"Cell {f_id}:{arm} step {idx} is malformed")

            h_decision = step.get("host_decision")
            if h_decision in ("ACCEPTED_CERTIFICATE", "SCOPED_CERTIFICATE"):
                raise DemoRefusal(
                    "FORGED_CERTIFICATE",
                    f"Step {idx} in {f_id}:{arm} claims {h_decision} under missing route ports",
                )

            prior_d = step.get("prior_state_digest")
            new_d = step.get("new_state_digest")
            ev_hex = step.get("event_bytes_hex", "")
            if not isinstance(h_decision, str) or not isinstance(ev_hex, str):
                raise DemoRefusal("MALFORMED_STEP", f"Cell {f_id}:{arm} step {idx} has non-string fields")
            try:
                ev_bytes = bytes.fromhex(ev_hex)
            except ValueError as e:
                raise DemoRefusal("MALFORMED_STEP", f"Cell {f_id}:{arm} step {idx} event bytes are not hex") from e

            if prior_d != expected_digest:
                raise DemoRefusal("CHAIN_DISCONTINUITY", f"Cell {f_id}:{arm} step {idx} prior digest mismatch")

            computed_new = chain_digest(expected_digest, ev_bytes, h_decision)
            if new_d != computed_new:
                raise DemoRefusal("HASH_CHAIN_MISMATCH", f"Cell {f_id}:{arm} step {idx} hash verification failed")

            expected_digest = computed_new

    return {
        "status": "VERIFIED",
        "route": "NO_NATIVE_PORT",
        "cells_verified": len(cells),
    }
