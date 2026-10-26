"""Finite Controlled Experiment Adapter for Symbol Game Demo 3.

Implements:
1. 6 Protocol Treatment Arms:
   - P (Plain Prompt Baseline)
   - T (Typed Packet Control)
   - C (Phase Cue Control after confirmed coverage)
   - R (Reflection / Rejection Feedback Baseline)
   - D (Primary Treatment: Frozen Admitted Detector Decisions + Bounded Hints)
   - A (Assisted Upper-Bound Control with solution-bearing hint)
2. 3 Finite Host Routes:
   - Restricted diagonal sign gauge (even/odd triangles)
   - Exact rational cochains (exact/nonexact cycles)
   - Finite signed-path pairing (meron involution with survivor)
3. Cryptographic State Hash-Chaining:
   - digest_i = SHA256(digest_{i-1} || event_bytes || host_decision)
4. Atomic Batch Transactions:
   - Any invalid proposal rolls back entire batch with zero state mutation.
5. Independent Host Oracle Evaluation:
   - Never trusts model-supplied 'verified': true or self-certified claims.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, Optional, Sequence

from omega_engine_pfp.infrastructure.adapters.mssn_research.bqnf_zero import (
    check_alpha_witness,
    check_cochain_packet,
    check_left_null_witness,
)
from omega_engine_pfp.infrastructure.adapters.mssn_research.meron_witness import (
    verify_meron_witness,
)
from omega_engine_pfp.infrastructure.adapters.mssn_research.sign_switching import (
    verify_cycle,
    verify_gauge,
)


def _canonical_json(data: Any) -> str:
    """RFC 8785 canonical JSON serialization (sorted keys, compact)."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ----------------------------------------------------------------------
# Data Models and Invariants
# ----------------------------------------------------------------------


class HostPhase:
    INTAKE = "INTAKE"
    COVERAGE = "COVERAGE"
    WITNESS = "WITNESS"
    VERIFY = "VERIFY"
    TERMINAL = "TERMINAL"


class HostExit:
    SCOPED_CERTIFICATE = "SCOPED_CERTIFICATE"
    REJECT_LOCAL = "REJECT_LOCAL"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    UNKNOWN_NOT_CERTIFIED = "UNKNOWN_NOT_CERTIFIED"
    FUEL_EXHAUSTED = "FUEL_EXHAUSTED"


@dataclass(frozen=True)
class MoveProposal:
    move_type: str
    payload: dict[str, Any]
    self_reported_verified: Optional[bool] = None


@dataclass(frozen=True)
class StepReceipt:
    step_index: int
    arm: str
    phase_before: str
    phase_after: str
    moves_proposed: tuple[dict[str, Any], ...]
    detector_findings: tuple[str, ...]
    host_decision: str
    prior_state_digest: str
    new_state_digest: str
    remaining_fuel: int
    batch_rolled_back: bool = False


@dataclass
class HostState:
    fixture_id: str
    route: str
    current_phase: str = HostPhase.INTAKE
    covered_elements: set[str] = field(default_factory=set)
    witness_candidate: Optional[dict[str, Any]] = None
    terminal_exit: Optional[str] = None
    terminal_label: Optional[str] = None
    remaining_fuel: int = 12
    state_digest: str = ""
    history: list[StepReceipt] = field(default_factory=list)

    def compute_next_digest(self, event_bytes: str, decision: str) -> str:
        payload = f"{self.state_digest}:{event_bytes}:{decision}"
        return _sha256(payload)


# ----------------------------------------------------------------------
# Fixture Catalog
# ----------------------------------------------------------------------

FIXTURES: dict[str, dict[str, Any]] = {
    "gauge_even_triangle": {
        "id": "gauge_even_triangle",
        "route": "restricted_diagonal_sign_gauge",
        "basis": ["v0", "v1", "v2"],
        "matrix": [
            ["0", "1", "-1"],
            ["1", "0", "1"],
            ["-1", "1", "0"],
        ],
        "expected_witness_type": "vertex_bits",
        "valid_witness": [0, 1, 0],
        "terminal": "RestrictedSignGaugeRepair",
    },
    "gauge_odd_triangle": {
        "id": "gauge_odd_triangle",
        "route": "restricted_diagonal_sign_gauge",
        "basis": ["v0", "v1", "v2"],
        "matrix": [
            ["0", "1", "1"],
            ["1", "0", "1"],
            ["1", "1", "0"],
        ],
        "expected_witness_type": "odd_parity_cycle",
        "valid_witness": [0, 1, 2, 0],
        "terminal": "RestrictedSignGaugeObstruction",
    },
    "cochain_exact_cycle": {
        "id": "cochain_exact_cycle",
        "route": "exact_rational_cochain_packet",
        "d0": [["1", "0"], ["-1", "1"], ["0", "-1"]],
        "d1": [["1", "1", "1"]],
        "c1": ["1/2", "0", "-1/2"],
        "expected_witness_type": "gauge_potential",
        "valid_witness": ["1/2", "1/2"],
        "terminal": "ExactCochainRepair",
    },
    "cochain_nonexact_cycle": {
        "id": "cochain_nonexact_cycle",
        "route": "exact_rational_cochain_packet",
        # Mathematical characterization:
        # Complex: C^0 (Q^2) -> d0 -> C^1 (Q^3) -> d1 -> C^2 (Q^1)
        # rank(d0) = 2, rank(d1) = 1 => dim(ker(d1)) = 2 = dim(im(d0)) => H^1 = ker(d1)/im(d0) = 0.
        # d1 * c1 = [1, 1, 1] * [1, 0, 0]^T = 1 != 0, so c1 is not a cocycle.
        # Left-null functional lambda = [1, 1, 1] satisfies lambda * d0 = 0 and lambda * c1 = 1 != 0,
        # certifying non-exactness (c1 not in im(d0)) in cokernel quotient Q_1 = C^1 / im(d0).
        "d0": [["1", "0"], ["-1", "1"], ["0", "-1"]],
        "d1": [["1", "1", "1"]],
        "c1": ["1", "0", "0"],
        "expected_witness_type": "separating_left_null_functional",
        "valid_witness": ["1", "1", "1"],
        "terminal": "ExactCochainObstruction",
    },
    "meron_two_pairs_survivor": {
        "id": "meron_two_pairs_survivor",
        "route": "finite_signed_path_pairing",
        "sectors": [
            {"path_id": "p0", "sign": -1, "weight": "1/2"},
            {"path_id": "p1", "sign": 1, "weight": "2/3"},
            {"path_id": "p2", "sign": -1, "weight": "2/3"},
            {"path_id": "p3", "sign": 1, "weight": "1/2"},
            {"path_id": "p4", "sign": 1, "weight": "3/7"},
        ],
        "expected_witness_type": "partial_sign_reversing_path_involution",
        "cancellation_ids": ["p0", "p1", "p2", "p3"],
        "valid_witness": {"p0": "p3", "p3": "p0", "p1": "p2", "p2": "p1"},
        "expected_survivors": ["p4"],
        "expected_signed_sum": "3/7",
        "terminal": "MeronPartialCancellation",
    },
}


# ----------------------------------------------------------------------
# Detectors & Safety Rules
# ----------------------------------------------------------------------


def run_detectors(
    moves: Sequence[MoveProposal], state: HostState, fixture: dict[str, Any]
) -> list[str]:
    from omega_engine_epistemic_immune_system.domain.value_objects import DetectorRule
    from omega_engine_epistemic_immune_system.infrastructure.mssn_ports import (
        DEMO3_MATCHER_ID,
        ProtocolMatcher,
    )

    codes = (
        "AM-3-PRECONDITION-INCOMPLETE",
        "AM-FSP-6-WRONG-ROUTE",
        "UNGROUNDED_SELF_CERTIFICATION",
    )
    # The protocol matcher runs host checks, not regexes: each rule binds to it
    # and names, as its pattern, the exact finding code it selects.
    rules = tuple(DetectorRule(code, code, code, matcher_id=DEMO3_MATCHER_ID) for code in codes)
    matcher = ProtocolMatcher(state, fixture)
    content = json.dumps([asdict(move) for move in moves])
    return [match.epitope_name for match in matcher.match_antigen(content, rules)]


# ----------------------------------------------------------------------
# Atomic Batch Executor & Host Oracle
# ----------------------------------------------------------------------


class Demo3HostEngine:
    """Deterministic host engine executing the 6-arm protocol with atomic batches."""

    def __init__(self, fixture_id: str, arm: str, initial_fuel: int = 12) -> None:
        if fixture_id not in FIXTURES:
            raise ValueError(f"Unknown fixture ID: {fixture_id}")
        self.fixture = FIXTURES[fixture_id]
        self.arm = arm.upper()
        init_digest = _sha256(f"DEMO3_INIT:{fixture_id}:{self.arm}")
        self.state = HostState(
            fixture_id=fixture_id,
            route=self.fixture["route"],
            remaining_fuel=initial_fuel,
            state_digest=init_digest,
        )

    def execute_batch(self, moves: Sequence[MoveProposal]) -> StepReceipt:
        """Process an atomic batch of moves. Any validation failure rolls back all moves."""
        if self.state.terminal_exit is not None:
            prior = self.state.state_digest
            new_digest = self.state.compute_next_digest(
                _canonical_json([asdict(m) for m in moves]), "REJECT_TERMINAL_STATE"
            )
            self.state.state_digest = new_digest
            receipt = StepReceipt(
                step_index=len(self.state.history),
                arm=self.arm,
                phase_before=self.state.current_phase,
                phase_after=self.state.current_phase,
                moves_proposed=tuple(asdict(m) for m in moves),
                detector_findings=(),
                host_decision="REJECT_TERMINAL_STATE",
                prior_state_digest=prior,
                new_state_digest=new_digest,
                remaining_fuel=self.state.remaining_fuel,
                batch_rolled_back=True,
            )
            self.state.history.append(receipt)
            return receipt
        if self.state.remaining_fuel <= 0:
            self.state.terminal_exit = HostExit.FUEL_EXHAUSTED
            receipt = StepReceipt(
                step_index=len(self.state.history),
                arm=self.arm,
                phase_before=self.state.current_phase,
                phase_after=HostPhase.TERMINAL,
                moves_proposed=tuple(asdict(m) for m in moves),
                detector_findings=("FUEL_EXHAUSTED",),
                host_decision=HostExit.FUEL_EXHAUSTED,
                prior_state_digest=self.state.state_digest,
                new_state_digest=self.state.state_digest,
                remaining_fuel=0,
                batch_rolled_back=False,
            )
            self.state.history.append(receipt)
            return receipt

        self.state.remaining_fuel -= 1
        prior_digest = self.state.state_digest
        phase_before = self.state.current_phase

        # Run detector checks
        malformed_payload = any(
            not isinstance(move.payload, dict)
            or (
                move.move_type == "COVER_ELEMENT"
                and (
                    type(move.payload.get("element_id")) is not str
                    or not move.payload["element_id"]
                )
            )
            for move in moves
        )
        findings = [] if malformed_payload else run_detectors(moves, self.state, self.fixture)

        # In arm D, detector findings trigger diagnostic HOLD or REFUSE
        if self.arm == "D" and findings:
            new_digest = self.state.compute_next_digest(
                _canonical_json([asdict(m) for m in moves]), "HOLD_DETECTOR"
            )
            self.state.state_digest = new_digest
            receipt = StepReceipt(
                step_index=len(self.state.history),
                arm=self.arm,
                phase_before=phase_before,
                phase_after=self.state.current_phase,
                moves_proposed=tuple(asdict(m) for m in moves),
                detector_findings=tuple(findings),
                host_decision="HOLD_DETECTOR_FEEDBACK",
                prior_state_digest=prior_digest,
                new_state_digest=new_digest,
                remaining_fuel=self.state.remaining_fuel,
                batch_rolled_back=True,
            )
            self.state.history.append(receipt)
            return receipt

        # Atomic transaction execution: snapshot state
        snap_phase = self.state.current_phase
        snap_covered = set(self.state.covered_elements)
        snap_witness = self.state.witness_candidate

        batch_ok = True
        host_decision = "ACCEPTED"

        for idx, move in enumerate(moves):
            if malformed_payload:
                batch_ok = False
                host_decision = "REJECT_MALFORMED_PAYLOAD"
                break
            if move.move_type == "COVER_ELEMENT":
                elem = move.payload.get("element_id")
                if not elem:
                    batch_ok = False
                    host_decision = "REJECT_MALFORMED_ELEMENT"
                    break
                self.state.covered_elements.add(elem)
                self.state.current_phase = HostPhase.COVERAGE

            elif move.move_type == "PROPOSE_WITNESS":
                self.state.witness_candidate = deepcopy(move.payload)
                self.state.current_phase = HostPhase.WITNESS

            elif move.move_type == "VERIFY":
                # Blocker 2: VERIFY must strictly be the terminal move in any batch
                if idx != len(moves) - 1:
                    batch_ok = False
                    host_decision = "REJECT_MOVE_AFTER_VERIFY"
                    break

                # Blocker 1: Incomplete coverage check for ALL arms
                if not (
                    "elem_all" in self.state.covered_elements
                    or "elem_complete" in self.state.covered_elements
                ):
                    batch_ok = False
                    host_decision = "REJECT_INCOMPLETE_COVERAGE"
                    break

                # Verify requires witness
                if not self.state.witness_candidate:
                    batch_ok = False
                    host_decision = "REJECT_MISSING_WITNESS"
                    break

                # Execute route oracle check
                verified, outcome_label = self._evaluate_oracle(self.state.witness_candidate)
                if verified:
                    self.state.current_phase = HostPhase.TERMINAL
                    self.state.terminal_exit = HostExit.SCOPED_CERTIFICATE
                    self.state.terminal_label = outcome_label
                    host_decision = HostExit.SCOPED_CERTIFICATE
                else:
                    batch_ok = False
                    host_decision = HostExit.REJECT_LOCAL
                break
            else:
                batch_ok = False
                host_decision = f"REJECT_UNKNOWN_MOVE:{move.move_type}"
                break

        # Rollback on failure
        if not batch_ok:
            self.state.current_phase = snap_phase
            self.state.covered_elements = snap_covered
            self.state.witness_candidate = snap_witness

        new_digest = self.state.compute_next_digest(
            _canonical_json([asdict(m) for m in moves]), host_decision
        )
        self.state.state_digest = new_digest

        receipt = StepReceipt(
            step_index=len(self.state.history),
            arm=self.arm,
            phase_before=phase_before,
            phase_after=self.state.current_phase,
            moves_proposed=tuple(asdict(m) for m in moves),
            detector_findings=tuple(findings),
            host_decision=host_decision,
            prior_state_digest=prior_digest,
            new_state_digest=new_digest,
            remaining_fuel=self.state.remaining_fuel,
            batch_rolled_back=not batch_ok,
        )
        self.state.history.append(receipt)
        return receipt

    def _evaluate_oracle(self, witness_payload: dict[str, Any]) -> tuple[bool, str]:
        """Independent host oracle verifying the proposed witness against exact mathematics."""
        route = self.fixture["route"]
        witness = witness_payload.get("witness")

        try:
            if route == "restricted_diagonal_sign_gauge":
                matrix = self.fixture["matrix"]
                w_type = witness_payload.get("witness_type")
                if w_type == "vertex_bits":
                    if verify_gauge(matrix, witness):
                        return True, "RestrictedSignGaugeRepair"
                elif w_type == "odd_parity_cycle":
                    if verify_cycle(matrix, witness):
                        return True, "RestrictedSignGaugeObstruction"
                return False, "INVALID_GAUGE_OR_CYCLE"

            elif route == "exact_rational_cochain_packet":
                d0 = self.fixture["d0"]
                d1 = self.fixture["d1"]
                c1 = self.fixture["c1"]
                packet = check_cochain_packet(d0, d1, c1)
                w_type = witness_payload.get("witness_type")
                if w_type == "gauge_potential":
                    check_alpha_witness(packet, witness)
                    return True, "ExactCochainRepair"
                elif w_type == "separating_left_null_functional":
                    check_left_null_witness(packet, witness)
                    return True, "ExactCochainObstruction"
                return False, "INVALID_COCHAIN_WITNESS"

            elif route == "finite_signed_path_pairing":
                sectors = self.fixture["sectors"]
                cancellation_ids = self.fixture["cancellation_ids"]
                # Convert string keys in witness map
                verify_meron_witness(sectors, cancellation_ids, witness)
                return True, "MeronPartialCancellation"

            return False, "UNKNOWN_ROUTE"
        except Exception:
            return False, "ORACLE_EXCEPTION"


# ----------------------------------------------------------------------
# Scripted Multi-Arm Proposer Simulation
# ----------------------------------------------------------------------


def run_scripted_arm_protocol(fixture_id: str, arm: str) -> dict[str, Any]:
    """Execute a complete scripted simulation of treatment arm on fixture."""
    engine = Demo3HostEngine(fixture_id=fixture_id, arm=arm, initial_fuel=12)
    fixture = FIXTURES[fixture_id]

    # Arm A: Assisted upper bound (direct delivery of certified witness)
    if arm == "A":
        # Step 1: Complete coverage
        engine.execute_batch(
            [
                MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
            ]
        )
        # Step 2: Propose certified witness directly
        engine.execute_batch(
            [
                MoveProposal(
                    "PROPOSE_WITNESS",
                    {
                        "witness_type": fixture["expected_witness_type"],
                        "witness": fixture["valid_witness"],
                        "assisted": True,
                    },
                ),
                MoveProposal("VERIFY", {}),
            ]
        )

    # Arm D: Primary treatment with admitted detector feedback
    elif arm == "D":
        # Step 1: Initial move (partial coverage)
        engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_0"})])
        # Step 2: Premature verify attempt (caught by detector AM-3)
        receipt2 = engine.execute_batch([MoveProposal("VERIFY", {})])
        if "AM-3-PRECONDITION-INCOMPLETE" not in receipt2.detector_findings:
            raise ValueError("scenario invariant failed")
        # Step 3: Complete coverage
        engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_complete"})])
        # Step 4: Propose correct witness and verify
        engine.execute_batch(
            [
                MoveProposal(
                    "PROPOSE_WITNESS",
                    {
                        "witness_type": fixture["expected_witness_type"],
                        "witness": fixture["valid_witness"],
                    },
                ),
                MoveProposal("VERIFY", {}),
            ]
        )

    # Arm R: Reflection baseline (attempts invalid proposal, receives generic failure, recovers)
    elif arm == "R":
        engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
        # Try wrong witness
        engine.execute_batch(
            [
                MoveProposal(
                    "PROPOSE_WITNESS",
                    {
                        "witness_type": fixture["expected_witness_type"],
                        "witness": "invalid_syntax",
                    },
                ),
                MoveProposal("VERIFY", {}),
            ]
        )
        # Reflect and retry with valid witness
        engine.execute_batch(
            [
                MoveProposal(
                    "PROPOSE_WITNESS",
                    {
                        "witness_type": fixture["expected_witness_type"],
                        "witness": fixture["valid_witness"],
                    },
                ),
                MoveProposal("VERIFY", {}),
            ]
        )

    # Arm C: Phase cue control (cue arrives only after complete coverage)
    elif arm == "C":
        engine.execute_batch([MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"})])
        engine.execute_batch(
            [
                MoveProposal(
                    "PROPOSE_WITNESS",
                    {
                        "witness_type": fixture["expected_witness_type"],
                        "witness": fixture["valid_witness"],
                    },
                ),
                MoveProposal("VERIFY", {}),
            ]
        )

    # Arm T: Typed packet control
    elif arm == "T":
        engine.execute_batch(
            [
                MoveProposal("COVER_ELEMENT", {"element_id": "elem_all"}),
                MoveProposal(
                    "PROPOSE_WITNESS",
                    {
                        "witness_type": fixture["expected_witness_type"],
                        "witness": fixture["valid_witness"],
                    },
                ),
                MoveProposal("VERIFY", {}),
            ]
        )

    # Arm P: Plain prompt baseline (stalls on premature verify)
    elif arm == "P":
        # Proposes premature verify without complete coverage
        engine.execute_batch([MoveProposal("VERIFY", {})])

    # Build canonical receipt
    history_records = [asdict(r) for r in engine.state.history]
    receipt: dict[str, Any] = {
        "schema": "symbol-game-demo3-experiment/run-receipt-v1",
        "fixture_id": fixture_id,
        "arm": arm,
        "route": fixture["route"],
        "final_exit": engine.state.terminal_exit or HostExit.REJECT_LOCAL,
        "terminal_label": engine.state.terminal_label,
        "fuel_consumed": 12 - engine.state.remaining_fuel,
        "remaining_fuel": engine.state.remaining_fuel,
        "step_count": len(history_records),
        "steps": history_records,
        "final_state_digest": engine.state.state_digest,
    }
    receipt_bytes = _canonical_json(receipt)
    receipt["receipt_sha256"] = _sha256(receipt_bytes)
    return receipt


def run_all_protocol_matrix() -> dict[str, Any]:
    """Execute all 6 arms across all 5 canonical fixtures."""
    matrix_results: dict[str, Any] = {
        "schema": "symbol-game-demo3-experiment/matrix-receipt-v1",
        "arms": ["P", "T", "C", "R", "D", "A"],
        "fixtures": list(FIXTURES.keys()),
        "runs": {},
    }

    for f_id in FIXTURES:
        matrix_results["runs"][f_id] = {}
        for arm in ["P", "T", "C", "R", "D", "A"]:
            run_res = run_scripted_arm_protocol(f_id, arm)
            matrix_results["runs"][f_id][arm] = {
                "final_exit": run_res["final_exit"],
                "terminal_label": run_res.get("terminal_label"),
                "fuel_consumed": run_res["fuel_consumed"],
                "step_count": run_res["step_count"],
                "receipt_sha256": run_res["receipt_sha256"],
            }

    receipt_bytes = _canonical_json(matrix_results)
    matrix_results["matrix_sha256"] = _sha256(receipt_bytes)
    return matrix_results


# ----------------------------------------------------------------------
# OpenRouter Live Proposer & Trial Runner
# ----------------------------------------------------------------------


def parse_model_moves(raw: str) -> list[MoveProposal]:
    """Parse JSON move array or objects from model text output."""
    cleaned = raw.strip()
    if "```" in cleaned:
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()

    parsed = None
    try:
        parsed = json.loads(cleaned)
    except Exception:
        start_arr = cleaned.find("[")
        end_arr = cleaned.rfind("]")
        if start_arr != -1 and end_arr > start_arr:
            try:
                parsed = json.loads(cleaned[start_arr : end_arr + 1])
            except Exception:
                pass
        if parsed is None:
            start_obj = cleaned.find("{")
            end_obj = cleaned.rfind("}")
            if start_obj != -1 and end_obj > start_obj:
                try:
                    parsed = json.loads(cleaned[start_obj : end_obj + 1])
                except Exception:
                    pass

    if parsed is None:
        return []

    moves_raw: list[Any] = []
    if isinstance(parsed, list):
        moves_raw = parsed
    elif isinstance(parsed, dict):
        if "moves" in parsed and isinstance(parsed["moves"], list):
            moves_raw = parsed["moves"]
        elif "move_type" in parsed:
            moves_raw = [parsed]
        else:
            return []
    else:
        return []

    proposals: list[MoveProposal] = []
    for item in moves_raw:
        if isinstance(item, dict) and "move_type" in item:
            m_type = str(item["move_type"])
            payload = item.get("payload", {})
            if not isinstance(payload, dict):
                payload = {}
            for k, v in item.items():
                if k not in ("move_type", "payload", "self_reported_verified", "verified"):
                    if k not in payload:
                        payload[k] = v
            self_ver = item.get("self_reported_verified") or item.get("verified")
            proposals.append(
                MoveProposal(move_type=m_type, payload=payload, self_reported_verified=self_ver)
            )
        else:
            proposals.append(
                MoveProposal(move_type="INVALID_MALFORMED", payload={"raw": str(item)})
            )

    return proposals


def render_live_prompt(
    fixture: dict[str, Any], arm: str, turn: int, host_feedback: Optional[str] = None
) -> str:
    """Render prompt for live model according to treatment arm specification."""
    f_id = fixture["id"]
    route = fixture["route"]
    lines = [
        "You are the candidate proposer in Symbol Game Demo 3.",
        f"Task Fixture: {f_id}",
        f"Mathematical Route: {route}",
        "",
        "Problem Specification:",
    ]
    if route == "restricted_diagonal_sign_gauge":
        lines.append(f"Vertices: {fixture['basis']}")
        lines.append(f"Adjacency/Sign Matrix: {fixture['matrix']}")
        lines.append(
            "A diagonal sign gauge assigns binary bits s_i in {0, 1} to vertices such that for each non-zero edge (i, j):"
        )
        lines.append("  If matrix[i][j] == '1', then s_i ^ s_j == 1.")
        lines.append("  If matrix[i][j] == '-1', then s_i ^ s_j == 0.")
        lines.append(
            "If such a gauge exists, the witness is type 'vertex_bits' with a list of bits, e.g. [b_0, b_1, b_2]."
        )
        lines.append(
            "If no such gauge exists (odd-parity frustration cycle), the witness is type 'odd_parity_cycle' with a cycle vertex sequence, e.g. [v_0, v_1, v_2, v_0]."
        )

    elif route == "exact_rational_cochain_packet":
        lines.append(f"d0 matrix: {fixture['d0']}")
        lines.append(f"d1 matrix: {fixture['d1']}")
        lines.append(f"c1 1-cochain: {fixture['c1']}")
        lines.append(
            "If c1 is exact (c1 in im(d0)), the witness is type 'gauge_potential' with rational potentials, e.g. ['s_0', 's_1']."
        )
        lines.append(
            "If c1 is obstructed (c1 not in im(d0)), the witness is type 'separating_left_null_functional' with a rational functional separating non-exactness in cokernel Q_1 = C^1 / im(d0), e.g. ['lambda_0', 'lambda_1', 'lambda_2']."
        )

    elif route == "finite_signed_path_pairing":
        lines.append(f"Sectors: {fixture['sectors']}")
        lines.append("Pair opposite-sign paths with identical weights into an involution mapping.")
        lines.append(
            "The witness is type 'partial_sign_reversing_path_involution' with mapping dict, e.g. {'path_a': 'path_b', 'path_b': 'path_a'}."
        )

    lines.append("")
    lines.append("Complete Verification Protocol:")
    lines.append("To achieve verification, you should submit a complete batch of 3 moves:")
    lines.append('1. {"move_type": "COVER_ELEMENT", "payload": {"element_id": "elem_all"}}')
    lines.append(
        '2. {"move_type": "PROPOSE_WITNESS", "payload": {"witness_type": "<type>", "witness": <value>}}'
    )
    lines.append('3. {"move_type": "VERIFY", "payload": {}}')
    lines.append("You can and should output all 3 moves together in a single JSON array.")

    if arm == "P":
        lines.append("\nSolve this problem by outputting valid moves.")
    elif arm == "T":
        lines.append(
            "\nStrict requirement: Output a JSON array with complete element coverage, typed witness payload, and verify."
        )
    elif arm == "C":
        lines.append(
            "\nPhase Guidance: Complete coverage ('elem_all') must be established before witness verification."
        )
    elif arm == "A":
        lines.append(
            f"\nAssisted Solution Hint: The verified witness is type '{fixture['expected_witness_type']}' with witness: {json.dumps(fixture['valid_witness'])}."
        )

    if host_feedback and turn > 1:
        lines.append("")
        lines.append("=== PREVIOUS TURN HOST DISPOSITION ===")
        if arm == "D":
            lines.append("Host Detector Feedback: " + host_feedback)
            lines.append(
                "Directive: Correct your proposal to resolve the specific detector finding reported above."
            )
        elif arm == "R":
            lines.append(
                "Host Oracle Feedback: REJECT_LOCAL. Your previous proposal was rejected by the host oracle."
            )
            lines.append(
                "Directive: Reflect carefully on the rejection, diagnose what went wrong, and submit a corrected proposal."
            )
        else:
            lines.append("Host Feedback: " + host_feedback)

    lines.append("\nReturn ONLY the JSON array:")
    return "\n".join(lines)


def run_live_arm(fixture_id: str, arm: str, propose, *, max_turns: int = 2) -> dict[str, Any]:
    """Drive one demo-3 arm from proposer text. The host does not invent moves."""
    engine = Demo3HostEngine(fixture_id=fixture_id, arm=arm, initial_fuel=12)
    turns: list[dict[str, Any]] = []
    feedback: Optional[str] = None
    for turn in range(1, max_turns + 1):
        if engine.state.terminal_exit is not None:
            break
        raw = propose(render_live_prompt(engine.fixture, arm, turn, feedback))
        text = raw if isinstance(raw, str) else ""
        if not text.strip():
            turns.append(
                {
                    "turn": turn,
                    "provider_called": True,
                    "parsed_moves": 0,
                    "host_decision": "EMPTY_PROVIDER_RESPONSE",
                }
            )
            break
        moves = parse_model_moves(text)
        if not moves:
            turns.append(
                {
                    "turn": turn,
                    "provider_called": True,
                    "parsed_moves": 0,
                    "host_decision": "UNPARSED_MODEL_MOVES",
                    "response_chars": len(text),
                }
            )
            break
        receipt = engine.execute_batch(moves)
        findings = ",".join(receipt.detector_findings)
        feedback = (
            receipt.host_decision
            if not findings
            else f"{receipt.host_decision}; detectors={findings}"
        )
        turns.append(
            {
                "turn": turn,
                "provider_called": True,
                "parsed_moves": len(moves),
                "host_decision": receipt.host_decision,
                "response_chars": len(text),
            }
        )
    return {
        "fixture_id": fixture_id,
        "arm": arm,
        "final_exit": engine.state.terminal_exit,
        "terminal_label": engine.state.terminal_label,
        "step_count": len(engine.state.history),
        "provider_calls": len(turns),
        "turns": turns,
    }


def run_live_protocol_matrix(propose, *, max_turns: int = 2) -> dict[str, Any]:
    """One live proposer pass for every fixture and arm. No scripted move substitution."""
    runs: dict[str, Any] = {}
    calls = 0
    for fixture_id in FIXTURES:
        runs[fixture_id] = {}
        for arm in ("P", "T", "C", "R", "D", "A"):
            row = run_live_arm(fixture_id, arm, propose, max_turns=max_turns)
            calls += int(row["provider_calls"])
            runs[fixture_id][arm] = row
    return {
        "schema": "symbol-game-demo3-experiment/live-matrix-receipt-v1",
        "arms": ["P", "T", "C", "R", "D", "A"],
        "fixtures": list(FIXTURES.keys()),
        "provider_calls": calls,
        "runs": runs,
    }


def compute_empirical_effect_size(
    runs_d: Sequence[dict[str, Any]],
    runs_r: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Compute empirical treatment effect size Delta_{D-R} and confidence intervals."""
    n_d = len(runs_d)
    n_r = len(runs_r)
    if n_d == 0 or n_r == 0:
        return {"error": "Insufficient sample size for comparison"}

    k_d = sum(1 for r in runs_d if r.get("final_exit") == HostExit.SCOPED_CERTIFICATE)
    k_r = sum(1 for r in runs_r if r.get("final_exit") == HostExit.SCOPED_CERTIFICATE)

    p_d = k_d / n_d
    p_r = k_r / n_r
    delta = p_d - p_r

    # Agresti-Caffo adjusted interval
    n_d_tilde = n_d + 2
    n_r_tilde = n_r + 2
    p_d_tilde = (k_d + 1) / n_d_tilde
    p_r_tilde = (k_r + 1) / n_r_tilde
    delta_tilde = p_d_tilde - p_r_tilde
    se_ac = math.sqrt(
        (p_d_tilde * (1.0 - p_d_tilde) / n_d_tilde) + (p_r_tilde * (1.0 - p_r_tilde) / n_r_tilde)
    )
    ci95_ac = (round(delta_tilde - 1.96 * se_ac, 4), round(delta_tilde + 1.96 * se_ac, 4))

    # Standard Wald SE
    var_wald = (p_d * (1.0 - p_d) / n_d) + (p_r * (1.0 - p_r) / n_r)
    se_wald = math.sqrt(var_wald) if var_wald > 0 else 0.0
    ci95_wald = (round(delta - 1.96 * se_wald, 4), round(delta + 1.96 * se_wald, 4))

    mean_fuel_d = sum(r.get("fuel_consumed", 0) for r in runs_d) / n_d
    mean_fuel_r = sum(r.get("fuel_consumed", 0) for r in runs_r) / n_r
    mean_steps_d = sum(r.get("step_count", 0) for r in runs_d) / n_d
    mean_steps_r = sum(r.get("step_count", 0) for r in runs_r) / n_r

    return {
        "n_d": n_d,
        "n_r": n_r,
        "success_d": k_d,
        "success_r": k_r,
        "rate_d": round(p_d, 4),
        "rate_r": round(p_r, 4),
        "delta_d_minus_r": round(delta, 4),
        "se_agresti_caffo": round(se_ac, 4),
        "ci95_agresti_caffo": ci95_ac,
        "se_wald": round(se_wald, 4),
        "ci95_wald": ci95_wald,
        "mean_fuel_d": round(mean_fuel_d, 2),
        "mean_fuel_r": round(mean_fuel_r, 2),
        "mean_steps_d": round(mean_steps_d, 2),
        "mean_steps_r": round(mean_steps_r, 2),
    }
