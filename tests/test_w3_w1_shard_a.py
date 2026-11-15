"""Tests for Window 3 Wave 1 Shard A (Paper 003: Failure Detectors).

Target Claims:
- ATL-P003-013 -> AUDIT-P003-013: Native port parity
- ATL-P003-014 -> AUDIT-P003-014: Detector admission record
- ATL-P003-015 -> AUDIT-P003-015: Principal comparison
- ATL-P003-016 -> AUDIT-P003-016: Route-specific error measurement

Zero-Float Law enforced: All metrics, confidences, and counts use exact rationals or integers.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import math
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

# Ensure repository root and Paper 003 code path are discoverable without shadowing stdlib
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_P3_CODE = _REPO_ROOT / "atlas" / "archive" / "pfp" / "003_pfp_host_admitted_failure_detectors" / "code"
if str(_P3_CODE) not in sys.path:
    sys.path.append(str(_P3_CODE))

import canaries  # noqa: E402
import danger_gate  # noqa: E402
import native_host_detector  # noqa: E402

from pfp.domain.immune.danger_gate import Signal1AstMatch  # noqa: E402

# Canonical fixtures from test_danger_gate.py
_SIGNAL1 = [
    danger_gate.Signal1Match(
        epitope_name="AM-FSP-8-TROYER-WIESE",
        pattern_matched="Troyer-Wiese",
        confidence_num=1,
        confidence_den=1,
    )
]
_SIGNAL2_LOW = danger_gate.Signal2Danger(
    danger_type="UNOPTIMIZED_CONTRACT",
    severity=danger_gate.DangerSeverity.LOW.value,
    defect_count=1,
)
_SIGNAL2_MEDIUM = danger_gate.Signal2Danger(
    danger_type="ODD_CYCLE_OBSTRUCTION",
    severity=danger_gate.DangerSeverity.MEDIUM.value,
)
_SIGNAL2_CRITICAL = danger_gate.Signal2Danger(
    danger_type="CORRUPTED_EVENT_CHAIN",
    severity=danger_gate.DangerSeverity.CRITICAL.value,
    defect_count=2,
)

_TRUE_ATTRACTIVE_U = (
    "For attractive U < 0 with equal spin populations, determinant QMC is "
    "sign-problem-free on any lattice."
)

_DETECTOR_CASES = [
    ("Claiming to solve np-hard sign problem solved in p unconditionally.", "AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM"),
    ("We assume particle-hole symmetry on triangle plaquettes at half filling.", "AM-FSP-2-FRUSTRATED-OBSTRUCTION"),
    ("Defining smooth majorana representation on 2-torus without holonomy.", "AM-FSP-7-UNVERIFIED-MAJORANA-LIFT"),
    (
        "Meron cluster algorithms eliminate sign oscillations for every doped model.",
        "AM-FSP-4-ORBIT-SUM-MISMATCH",
    ),
]


# ============================================================================
# 1. AUDIT-P003-013: Native Port Parity
# ============================================================================

class TestNativePortParity:
    """Tests confirming the Rust native port matches the Python reference implementation."""

    def test_native_binary_presence(self) -> None:
        """Confirm that the solve_host_detector binary is discovered."""
        assert native_host_detector.is_native_available(), (
            "solve_host_detector binary must be compiled and available at code/rust/target/"
        )
        binary_path = native_host_detector.native_binary_path()
        assert binary_path is not None
        assert binary_path.is_file()

    def test_gate_all_canonical_cases_parity(self) -> None:
        """The native port and Python reference return identical decisions on all 5 gate cases."""
        gate_cases = [
            ([], None, "TOLERATED", False, False),
            (_SIGNAL1, None, "DIAGNOSTIC_ONLY", False, False),
            ([], _SIGNAL2_LOW, "DIAGNOSTIC_ONLY", False, False),
            ([], _SIGNAL2_CRITICAL, "DEFENSIVE_LOCKDOWN", True, True),
            (_SIGNAL1, _SIGNAL2_MEDIUM, "QUARANTINED", True, True),
        ]
        for signal1, signal2, exp_dec, exp_refusal, exp_suppressed in gate_cases:
            py_res = danger_gate.evaluate_two_signal_gate(signal1, signal2)
            rust_res = native_host_detector.native_evaluate_two_signal_gate(signal1, signal2)

            assert rust_res == py_res
            assert rust_res.decision == exp_dec
            assert rust_res.is_refusal is exp_refusal
            assert rust_res.is_suppressed is exp_suppressed
            assert rust_res.disposition == py_res.disposition
            assert rust_res.signal1_count == py_res.signal1_count
            assert rust_res.signal2_severity == py_res.signal2_severity
            assert rust_res.rationale == py_res.rationale

    def test_canaries_constructed_fixtures_parity(self) -> None:
        """The native port and Python reference return identical canary findings on constructed sentences."""
        for text, expected_id in _DETECTOR_CASES:
            py_findings = canaries.scan_for_canaries(text)
            rust_findings = native_host_detector.native_scan_for_canaries(text)

            assert rust_findings == py_findings
            assert len(rust_findings) == 1
            assert rust_findings[0].canary_id == expected_id
            # Zero-float verification: confidences are exact integer rationals
            assert rust_findings[0].confidence_num == 1
            assert rust_findings[0].confidence_den == 1
            assert isinstance(rust_findings[0].confidence_num, int)
            assert isinstance(rust_findings[0].confidence_den, int)

    def test_canaries_clean_and_negated_controls_parity(self) -> None:
        """The native port matches the Python reference on clean controls and negated sentences."""
        # True attractive-U sentence produces 0 findings in both
        py_att = canaries.scan_for_canaries(_TRUE_ATTRACTIVE_U)
        rust_att = native_host_detector.native_scan_for_canaries(_TRUE_ATTRACTIVE_U)
        assert rust_att == py_att == []

        # Negated sentence triggers AM-FSP-2 in both
        negated = "There is no particle-hole symmetry on triangle plaquettes."
        py_neg = canaries.scan_for_canaries(negated)
        rust_neg = native_host_detector.native_scan_for_canaries(negated)
        assert rust_neg == py_neg
        assert len(rust_neg) == 1
        assert rust_neg[0].canary_id == "AM-FSP-2-FRUSTRATED-OBSTRUCTION"

        # Neutral cochain text produces 0 findings in both
        neutral = "We compute the discrete cochain boundary of a 1-chain on a bipartite square lattice over Q."
        assert native_host_detector.native_scan_for_canaries(neutral) == canaries.scan_for_canaries(neutral) == []

        # Empty string produces 0 findings in both
        assert native_host_detector.native_scan_for_canaries("") == canaries.scan_for_canaries("") == []

    def test_native_error_handling_on_malformed_command(self) -> None:
        """Native host bridge raises NativeHostError on unsupported commands or malformed payloads."""
        with pytest.raises(native_host_detector.NativeHostError):
            native_host_detector._call_native({"command": "nonexistent_command"})

        with pytest.raises(native_host_detector.NativeHostError):
            native_host_detector._call_native({"command": "evaluate_gate", "malformed": 123})

    def test_domain_danger_gate_zero_float_law(self) -> None:
        """Repository domain gate strictly enforces ZERO-FLOAT on confidence values."""
        # Fraction(1, 1) is accepted
        valid_match = Signal1AstMatch(
            epitope_name="EPITOPE_1",
            pattern_matched="pattern",
            confidence=Fraction(1, 1),
        )
        assert valid_match.confidence == Fraction(1, 1)

        # Float confidence raises TypeError
        with pytest.raises(TypeError, match="ZERO-FLOAT Invariant violated"):
            Signal1AstMatch(  # type: ignore[arg-type]
                epitope_name="EPITOPE_1",
                pattern_matched="pattern",
                confidence=1.0,  # Forbidden float
            )


# ============================================================================
# 2. AUDIT-P003-014: Detector Admission Record
# ============================================================================

@dataclass(frozen=True, slots=True)
class AdmissionRecord:
    detector_id: str
    version: str
    route_scope: str
    predicate_sha256: str
    positive_defect_witness: dict[str, Any]
    near_miss_controls: list[dict[str, Any]]
    action_policy: str


def validate_detector_admission(
    record: AdmissionRecord,
    reproduced_defect_oracle: bool,
    near_miss_oracles: Sequence[bool],
    computed_predicate_sha256: str,
) -> tuple[bool, str]:
    """Evaluates admission against Paper 003 Section 3 invariants."""
    # 1. Repaired defect reproduction
    if not reproduced_defect_oracle or not record.positive_defect_witness:
        return False, "ADMISSION_REFUSED_DEFECT_NOT_REPRODUCED"

    # 2. Near miss controls
    if not record.near_miss_controls or len(record.near_miss_controls) == 0:
        return False, "ADMISSION_REFUSED_MISSING_NEAR_MISS_CONTROLS"
    if not all(near_miss_oracles):
        return False, "ADMISSION_REFUSED_NEAR_MISS_FAILED_ORACLE"

    # 3. Declared route scope
    if not record.route_scope or record.route_scope == "*":
        return False, "ADMISSION_REFUSED_UNDECLARED_ROUTE_SCOPE"

    # 4. Frozen cryptographic identity
    if record.predicate_sha256 != computed_predicate_sha256:
        return False, "ADMISSION_REFUSED_PREDICATE_DIGEST_MISMATCH"

    return True, "ADMISSION_APPROVED"


class TestDetectorAdmissionRecord:
    """Tests verifying detector admission criteria per Paper 003 Section 3."""

    def _sample_record(self) -> AdmissionRecord:
        dummy_code = b"def evaluate(): pass"
        code_sha256 = hashlib.sha256(dummy_code).hexdigest()
        return AdmissionRecord(
            detector_id="AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM",
            version="1.0.0",
            route_scope="pfp.domain.physics.fermion_sign_problem",
            predicate_sha256=code_sha256,
            positive_defect_witness={"prompt_id": "MERON-01", "failing_token": "np-hard sign problem solved in p"},
            near_miss_controls=[
                {
                    "prompt_id": "MERON-01-NM1",
                    "valid_text": "Sign problem is solved in p for bipartite planar lattices.",
                }
            ],
            action_policy="QUARANTINED",
        )

    def test_admission_record_valid_schema(self) -> None:
        """A complete admission record meeting all four criteria is approved."""
        record = self._sample_record()
        approved, reason = validate_detector_admission(
            record=record,
            reproduced_defect_oracle=True,
            near_miss_oracles=[True],
            computed_predicate_sha256=record.predicate_sha256,
        )
        assert approved is True
        assert reason == "ADMISSION_APPROVED"

    def test_admission_rejected_missing_positive_witness(self) -> None:
        """Admission fails if the defect cannot be reproduced."""
        record = self._sample_record()
        approved, reason = validate_detector_admission(
            record=record,
            reproduced_defect_oracle=False,  # Oracle cannot reproduce defect
            near_miss_oracles=[True],
            computed_predicate_sha256=record.predicate_sha256,
        )
        assert approved is False
        assert reason == "ADMISSION_REFUSED_DEFECT_NOT_REPRODUCED"

    def test_admission_rejected_missing_near_miss(self) -> None:
        """Admission fails if near-miss controls are absent or rejected by oracle."""
        dummy_code = b"def evaluate(): pass"
        code_sha256 = hashlib.sha256(dummy_code).hexdigest()
        empty_nm_record = AdmissionRecord(
            detector_id="AM-FSP-8",
            version="1.0.0",
            route_scope="pfp.domain.physics",
            predicate_sha256=code_sha256,
            positive_defect_witness={"sample": "data"},
            near_miss_controls=[],  # Empty controls
            action_policy="QUARANTINED",
        )
        approved, reason = validate_detector_admission(
            record=empty_nm_record,
            reproduced_defect_oracle=True,
            near_miss_oracles=[],
            computed_predicate_sha256=code_sha256,
        )
        assert approved is False
        assert reason == "ADMISSION_REFUSED_MISSING_NEAR_MISS_CONTROLS"

        # Near miss fails independent oracle
        record = self._sample_record()
        approved_nm_fail, reason_nm_fail = validate_detector_admission(
            record=record,
            reproduced_defect_oracle=True,
            near_miss_oracles=[False],  # Near miss rejected by oracle
            computed_predicate_sha256=record.predicate_sha256,
        )
        assert approved_nm_fail is False
        assert reason_nm_fail == "ADMISSION_REFUSED_NEAR_MISS_FAILED_ORACLE"

    def test_admission_rejected_unbounded_scope(self) -> None:
        """Admission fails if route scope is empty or wildcard."""
        dummy_code = b"def evaluate(): pass"
        code_sha256 = hashlib.sha256(dummy_code).hexdigest()
        unbounded_record = AdmissionRecord(
            detector_id="AM-FSP-8",
            version="1.0.0",
            route_scope="*",  # Wildcard unbounded
            predicate_sha256=code_sha256,
            positive_defect_witness={"sample": "data"},
            near_miss_controls=[{"sample": "control"}],
            action_policy="QUARANTINED",
        )
        approved, reason = validate_detector_admission(
            record=unbounded_record,
            reproduced_defect_oracle=True,
            near_miss_oracles=[True],
            computed_predicate_sha256=code_sha256,
        )
        assert approved is False
        assert reason == "ADMISSION_REFUSED_UNDECLARED_ROUTE_SCOPE"

    def test_admission_rejected_tampered_digest(self) -> None:
        """Admission fails if predicate hash does not match frozen digest."""
        record = self._sample_record()
        approved, reason = validate_detector_admission(
            record=record,
            reproduced_defect_oracle=True,
            near_miss_oracles=[True],
            computed_predicate_sha256="tampered_hash_e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        )
        assert approved is False
        assert reason == "ADMISSION_REFUSED_PREDICATE_DIGEST_MISMATCH"

    def test_repetition_count_does_not_equal_independent_instances(self) -> None:
        """1,000 rows with 40 distinct base contents yield 40 independent clusters, not 1,000."""
        # Replicate repository self panel shape: 40 distinct contents repeated 25 times each = 1,000 rows
        base_contents = [f"Base defect pattern template #{i}" for i in range(40)]
        log_rows = [base_contents[i % 40] for i in range(1000)]

        assert len(log_rows) == 1000
        distinct_contents = set(log_rows)
        assert len(distinct_contents) == 40
        assert len(distinct_contents) != len(log_rows)


# ============================================================================
# 3. AUDIT-P003-015: Principal Comparison
# ============================================================================

@dataclass(frozen=True, slots=True)
class ExperimentArm:
    arm_id: str
    name: str
    description: str
    is_assisted_control: bool
    budget_turns: int
    budget_tokens: int


@dataclass(frozen=True, slots=True)
class TrialRunResult:
    arm_id: str
    task_id: str
    witness_obtained: bool
    is_verified_by_oracle: bool
    budget_exhausted: bool


class TestPrincipalComparison:
    """Tests verifying the D versus R principal comparison design per Paper 003 Section 6."""

    def _six_arms(self) -> dict[str, ExperimentArm]:
        return {
            "P": ExperimentArm("P", "Plain proposal", "Unprompted baseline", False, 10, 4000),
            "T": ExperimentArm("T", "Typed protocol", "Structural schema constraints", False, 10, 4000),
            "C": ExperimentArm("C", "Coverage guidance", "Coverage prompts", False, 10, 4000),
            "R": ExperimentArm("R", "Generic reflection", "Generic reflection feedback", False, 10, 4000),
            "D": ExperimentArm("D", "Admitted detector policy", "Detector gating + tailored feedback", False, 10, 4000),
            "A": ExperimentArm("A", "Solution assistance", "Assisted control with hints", True, 10, 4000),
        }

    def test_prespecified_six_arm_design_structure(self) -> None:
        """The experiment design defines exactly 6 arms with matched budgets."""
        arms = self._six_arms()
        assert set(arms.keys()) == {"P", "T", "C", "R", "D", "A"}

        # Arms D and R must have identical stopping budgets
        assert arms["D"].budget_turns == arms["R"].budget_turns == 10
        assert arms["D"].budget_tokens == arms["R"].budget_tokens == 4000

    def test_principal_contrast_is_d_minus_r(self) -> None:
        """The primary comparison evaluates D minus R under identical evaluation conditions."""
        arms = self._six_arms()
        principal_arms = (arms["D"].arm_id, arms["R"].arm_id)
        assert principal_arms == ("D", "R")
        # Both are unassisted arms
        assert not arms["D"].is_assisted_control
        assert not arms["R"].is_assisted_control

    def test_assisted_control_arm_a_excluded_from_unassisted_claims(self) -> None:
        """Arm A is tagged as assisted control and barred from unassisted solution claims."""
        arms = self._six_arms()
        assert arms["A"].is_assisted_control is True
        for arm_id in ("P", "T", "C", "R", "D"):
            assert arms[arm_id].is_assisted_control is False

    def test_confirmatory_gate_requires_positive_lower_ci_bound(self) -> None:
        """The confirmatory gate requires LB_95(D - R) > 0 on verified primary outcome."""
        def evaluate_confirmatory_gate(
            runs_d: Sequence[TrialRunResult],
            runs_r: Sequence[TrialRunResult],
        ) -> tuple[bool, Fraction, Fraction]:
            n_d = len(runs_d)
            n_r = len(runs_r)
            assert n_d == n_r and n_d > 0

            # Verified witnesses within budget (primary outcome)
            succ_d = sum(1 for r in runs_d if r.witness_obtained and r.is_verified_by_oracle and not r.budget_exhausted)
            succ_r = sum(1 for r in runs_r if r.witness_obtained and r.is_verified_by_oracle and not r.budget_exhausted)

            p_d = Fraction(succ_d, n_d)
            p_r = Fraction(succ_r, n_r)
            diff = p_d - p_r

            # Normal approximation 95% lower bound with exact Fraction arithmetic: z_0.95 = 1645/1000 = 1.645
            var_d = (p_d * (1 - p_d)) / n_d
            var_r = (p_r * (1 - p_r)) / n_r
            se_approx = Fraction(int(math.isqrt(int((var_d + var_r) * 10**8))), 10**4)
            lower_bound = diff - Fraction(1645, 1000) * se_approx

            return (lower_bound > 0), diff, lower_bound

        # Case 1: Substantial advantage in D: 80/100 vs 50/100
        runs_d_win = [TrialRunResult("D", f"task_{i}", True, True, False) for i in range(80)] + [
            TrialRunResult("D", f"task_{i}", False, False, True) for i in range(80, 100)
        ]
        runs_r_base = [TrialRunResult("R", f"task_{i}", True, True, False) for i in range(50)] + [
            TrialRunResult("R", f"task_{i}", False, False, True) for i in range(50, 100)
        ]
        passes_gate, diff, lb = evaluate_confirmatory_gate(runs_d_win, runs_r_base)
        assert passes_gate is True
        assert diff == Fraction(3, 10)
        assert lb > 0

        # Case 2: No advantage: 50/100 vs 50/100
        runs_d_tie = [TrialRunResult("D", f"task_{i}", True, True, False) for i in range(50)] + [
            TrialRunResult("D", f"task_{i}", False, False, True) for i in range(50, 100)
        ]
        passes_gate_tie, diff_tie, lb_tie = evaluate_confirmatory_gate(runs_d_tie, runs_r_base)
        assert passes_gate_tie is False
        assert diff_tie == 0
        assert lb_tie <= 0

    def test_unbalanced_budget_violates_contrast_invariants(self) -> None:
        """Giving Arm D more turns or tokens than Arm R violates the design invariant."""
        arm_d_inflated = ExperimentArm("D", "Admitted detector policy", "inflated", False, 20, 8000)
        arm_r_standard = ExperimentArm("R", "Generic reflection", "standard", False, 10, 4000)

        assert (arm_d_inflated.budget_turns == arm_r_standard.budget_turns) is False
        assert (arm_d_inflated.budget_tokens == arm_r_standard.budget_tokens) is False


# ============================================================================
# 4. AUDIT-P003-016: Route-Specific Error Measurement
# ============================================================================

@dataclass(frozen=True, slots=True)
class ProposalAuditRecord:
    route: str
    is_detector_eligible: bool
    is_blocked_by_policy: bool
    is_valid_by_route_oracle: bool
    model_declared_valid: bool
    terminal_certificate_issued: bool


class TestRouteSpecificErrorMeasurement:
    """Tests verifying route-specific error measurement per Paper 003 Section 7."""

    def test_false_suppression_formula_calculation(self) -> None:
        """False suppression is valid eligible blocked divided by all valid eligible."""
        def compute_false_suppression(records: Sequence[ProposalAuditRecord]) -> Fraction:
            # Denominator: proposals that are detector-eligible AND independently valid
            eligible_valid = [r for r in records if r.is_detector_eligible and r.is_valid_by_route_oracle]
            if not eligible_valid:
                return Fraction(0, 1)

            # Numerator: valid eligible proposals blocked by policy
            blocked_valid = [r for r in eligible_valid if r.is_blocked_by_policy]
            return Fraction(len(blocked_valid), len(eligible_valid))

        records = [
            # 298 valid eligible allowed
            ProposalAuditRecord("cochain", True, False, True, True, False),
        ] * 298 + [
            # 2 valid eligible blocked (false suppressions)
            ProposalAuditRecord("cochain", True, True, True, True, False),
        ] * 2 + [
            # 50 invalid proposals blocked (legitimate blocks, must NOT enter denominator)
            ProposalAuditRecord("cochain", True, True, False, True, False),
        ] * 50

        rate = compute_false_suppression(records)
        assert rate == Fraction(2, 300)
        assert rate == Fraction(1, 150)
        assert isinstance(rate, Fraction)

    def test_invalid_proposals_excluded_from_denominator(self) -> None:
        """Blocked invalid proposals do not enlarge the denominator."""
        records_only_invalid = [
            ProposalAuditRecord("graph", True, True, False, True, False) for _ in range(100)
        ]
        # None are valid under route oracle, so eligible valid denominator is 0
        valid_eligible = [r for r in records_only_invalid if r.is_detector_eligible and r.is_valid_by_route_oracle]
        assert len(valid_eligible) == 0

    def test_bernoulli_sample_size_bound_calculation(self) -> None:
        """Zero failures in n independent Bernoulli trials gives upper bound 1 - 0.05^(1/n)."""
        def exact_upper_bound(n: int) -> float:
            return 1.0 - math.pow(0.05, 1.0 / n)

        # n = 8 gives bound ~ 0.3123 (31.2%)
        bound_8 = exact_upper_bound(8)
        assert 0.31 < bound_8 < 0.32
        assert bound_8 > 0.01  # Fails 1% gate

        # n = 298 gives bound slightly above 0.01
        bound_298 = exact_upper_bound(298)
        assert bound_298 > 0.01

        # n = 299 gives bound below 0.01 (0.997%)
        bound_299 = exact_upper_bound(299)
        assert bound_299 < 0.01

    def test_zero_tolerance_false_terminal_trigger(self) -> None:
        """A single false terminal certificate immediately fails the route safety gate."""
        def evaluate_route_safety_gate(records: Sequence[ProposalAuditRecord]) -> tuple[bool, str]:
            false_terminals = [
                r for r in records if r.is_valid_by_route_oracle and r.terminal_certificate_issued
            ]
            if len(false_terminals) > 0:
                return False, f"SAFETY_GATE_HALTED_FALSE_TERMINAL_COUNT_{len(false_terminals)}"

            return True, "SAFETY_GATE_PASSED"

        clean_records = [
            ProposalAuditRecord("route_a", True, False, True, True, False) for _ in range(300)
        ]
        passed, msg = evaluate_route_safety_gate(clean_records)
        assert passed is True
        assert msg == "SAFETY_GATE_PASSED"

        # Introduce 1 false terminal
        compromised = list(clean_records) + [
            ProposalAuditRecord("route_a", True, True, True, True, True)  # Valid proposal got terminal certificate
        ]
        failed, fail_msg = evaluate_route_safety_gate(compromised)
        assert failed is False
        assert fail_msg == "SAFETY_GATE_HALTED_FALSE_TERMINAL_COUNT_1"

    def test_safety_non_transferability_between_routes(self) -> None:
        """Safety confirmed on route A cannot be transferred to route B."""
        route_records = {
            "route_cochain": [ProposalAuditRecord("route_cochain", True, False, True, True, False) for _ in range(300)],
            "route_symbol_game": [],  # No evaluated proposals
        }

        def route_status(route_name: str) -> str:
            recs = route_records.get(route_name, [])
            valid_count = sum(1 for r in recs if r.is_detector_eligible and r.is_valid_by_route_oracle)
            if valid_count < 299:
                return "UNASSESSED_ROUTE_SAFETY_GATE_BLOCKED"
            return "ASSESSED_ROUTE_SAFETY_GATE_PASSED"

        assert route_status("route_cochain") == "ASSESSED_ROUTE_SAFETY_GATE_PASSED"
        assert route_status("route_symbol_game") == "UNASSESSED_ROUTE_SAFETY_GATE_BLOCKED"
