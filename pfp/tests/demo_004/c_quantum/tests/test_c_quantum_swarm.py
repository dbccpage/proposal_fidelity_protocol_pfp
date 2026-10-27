"""Test suite for the Adversary Quantum Swarm & C021 (Q40-R) Stabilizer Architecture.

Tests:
1. Commuting stabilizer solver ground state energies and degeneracies.
2. Anticommuting detection and lexicographically sorted witnesses.
3. Malformed and out-of-bounds cases with closed refusal codes.
4. Relabel and Clifford controls (qubit perm, term reorder, id rename, weight scale, basis change).
5. Poisoned case resistance (hidden anticommuting pair, Y-phase trap, unreduced weights, signed product).
6. 30+ Checker Mutation Suite (sign-flip, energy shift, missing minimizer, extra minimizer,
   wrong degeneracy, dependent basis, commuting witness, wrong types).
7. DDC tape trace verification via Rust host (`ddc_verify_tape`).
8. Missing the city challenge binding refuses without emitting execution artifacts.
9. Strict micro-budget ceiling enforcement (< $0.05 target, <= $0.25 ceiling).

AuthorityEffect: None.
"""

from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import pytest

_REPO_ROOT = next(p for p in Path(__file__).resolve().parents if (p / "pfp").is_dir())
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

if __package__ in (None, ""):
    __package__ = "pfp.tests.demo_004.c_quantum.tests"

from operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from pfp.domain.quantum.certificate_checker import check_certificate
from pfp.infrastructure.adapters.stabilizer_rust_adapter import (
    StabilizerRustAdapter,
)

from ..solve import solve
from ..swarm import (
    BudgetController,
    BudgetExhaustedRefusal,
    DdcTracer,
    AdversaryQuantumOverseer,
)

_STABILIZER = StabilizerRustAdapter()


@pytest.fixture
def repo_root() -> Path:
    return _REPO_ROOT


@pytest.fixture
def default_host() -> RustSymbolGameHost:
    return RustSymbolGameHost()


# =============================================================================
# 1. Commuting, Anticommuting, and Unknown Cases
# =============================================================================


def test_c021_commuting_2q_solution():
    case = {
        "id": "test_comm_2q",
        "n": 2,
        "terms": [
            {"id": "t1", "P": "ZI", "w": [1, 1], "target": 1},
            {"id": "t2", "P": "IZ", "w": [1, 1], "target": 1},
        ],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["energy"] == [0, 1]
    assert res["degeneracy"] == 1
    assert set(res["basis"]) == {"t1", "t2"}
    assert res["minimizers"] == [0]

    verdict = check_certificate(case, res, port=_STABILIZER)
    assert verdict["verdict"] == "PASS"


def test_c021_spec_example_h07():
    case = {
        "id": "h_07",
        "n": 3,
        "terms": [
            {"id": "t_a", "P": "XYZ", "w": [3, 2], "target": 1},
            {"id": "t_b", "P": "ZZI", "w": [1, 1], "target": -1},
        ],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["energy"] == [0, 1]
    assert res["degeneracy"] == 2
    assert res["basis"] == ["t_a", "t_b"]
    assert res["minimizers"] == [2]

    verdict = check_certificate(case, res, port=_STABILIZER)
    assert verdict["verdict"] == "PASS"


def test_c021_anticommuting_witness():
    case = {
        "id": "test_anti_1q",
        "n": 1,
        "terms": [
            {"id": "t_z", "P": "Z", "w": [1, 1], "target": 1},
            {"id": "t_x", "P": "X", "w": [1, 1], "target": 1},
        ],
    }
    res = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"] == ["t_x", "t_z"]  # Lexicographically sorted

    verdict = check_certificate(case, res, port=_STABILIZER)
    assert verdict["verdict"] == "PASS"


def test_c021_unknown_refusal_codes():
    # 1. Qubits out of bounds
    case_n9 = {
        "id": "bad_n",
        "n": 9,
        "terms": [{"id": "t1", "P": "IIIIIIIII", "w": [1, 1], "target": 1}],
    }
    res_n9 = solve(case_n9)
    assert res_n9["status"] == "UNKNOWN"
    assert res_n9["refusal_code"] == "QUBIT_BOUND_EXCEEDED"
    assert check_certificate(case_n9, res_n9, port=_STABILIZER)["verdict"] == "PASS"

    # 2. Duplicate term ID
    case_dup = {
        "id": "bad_dup",
        "n": 2,
        "terms": [
            {"id": "t_dup", "P": "ZI", "w": [1, 1], "target": 1},
            {"id": "t_dup", "P": "IZ", "w": [1, 1], "target": 1},
        ],
    }
    res_dup = solve(case_dup)
    assert res_dup["status"] == "UNKNOWN"
    assert res_dup["refusal_code"] == "DUPLICATE_TERM_ID"
    assert check_certificate(case_dup, res_dup, port=_STABILIZER)["verdict"] == "PASS"


# =============================================================================
# 2. Relabel and Clifford Controls
# =============================================================================


def test_c021_relabel_controls_invariance():
    judge_dir = Path(__file__).resolve().parents[1] / "judge"
    with open(judge_dir / "relabel_controls.json", "r", encoding="utf-8") as f:
        controls = json.load(f)

    for case in controls:
        res = solve(case)
        assert res["status"] == "SOLVED"
        verdict = check_certificate(case, res, port=_STABILIZER)
        assert verdict["verdict"] == "PASS", f"Failed on {case['id']}: {verdict}"


# =============================================================================
# 3. Poisoned Cases
# =============================================================================


def test_c021_poisoned_cases():
    judge_dir = Path(__file__).resolve().parents[1] / "judge"
    with open(judge_dir / "poisoned_cases.json", "r", encoding="utf-8") as f:
        poisoned = json.load(f)

    for case in poisoned:
        res = solve(case)
        verdict = check_certificate(case, res, port=_STABILIZER)
        assert verdict["verdict"] == "PASS", f"Failed on {case['id']}: {verdict}"


# =============================================================================
# 4. Mutation Suite (30+ Corrupted Outputs Rejected by Checker)
# =============================================================================


def test_c021_checker_mutation_suite():
    base_case = {
        "id": "mut_base_case",
        "n": 3,
        "terms": [
            {"id": "t_a", "P": "XYZ", "w": [3, 2], "target": 1},
            {"id": "t_b", "P": "ZZI", "w": [1, 1], "target": -1},
        ],
    }
    correct_solution = solve(base_case)
    assert check_certificate(base_case, correct_solution, port=_STABILIZER)["verdict"] == "PASS"

    mutations: list[tuple[str, dict]] = []

    # 1. Flip phase/sign of term decomposition
    m = copy.deepcopy(correct_solution)
    m["decomposition"][0]["phase"] = -m["decomposition"][0]["phase"]
    mutations.append(("sign_flipped_phase", m))

    # 2. Non-integer phase
    m = copy.deepcopy(correct_solution)
    m["decomposition"][0]["phase"] = 2
    mutations.append(("invalid_phase_value", m))

    # 3. Wrong ground energy (shift by 1)
    m = copy.deepcopy(correct_solution)
    m["energy"] = [m["energy"][0] + 1, m["energy"][1]]
    mutations.append(("energy_shifted_by_one", m))

    # 4. Negative energy on PSD Hamiltonian
    m = copy.deepcopy(correct_solution)
    m["energy"] = [-1, 1]
    mutations.append(("negative_energy", m))

    # 5. Zero denominator in energy
    m = copy.deepcopy(correct_solution)
    m["energy"] = [1, 0]
    mutations.append(("zero_denominator_energy", m))

    # 6. Float energy instead of rational pair
    m = copy.deepcopy(correct_solution)
    m["energy"] = 0.5  # type: ignore
    mutations.append(("float_energy", m))

    # 7. Energy pair with non-integer elements
    m = copy.deepcopy(correct_solution)
    m["energy"] = ["0", "1"]
    mutations.append(("string_elements_energy", m))

    # 8. Missing minimizer
    m = copy.deepcopy(correct_solution)
    m["minimizers"] = []
    mutations.append(("missing_minimizers", m))

    # 9. Extra non-minimizer added
    m = copy.deepcopy(correct_solution)
    m["minimizers"] = [m["minimizers"][0], 0 if m["minimizers"][0] != 0 else 1]
    mutations.append(("extra_non_minimizer", m))

    # 10. Minimizer out of bounds (>= 2^k)
    m = copy.deepcopy(correct_solution)
    m["minimizers"] = [999]
    mutations.append(("minimizer_out_of_bounds", m))

    # 11. Duplicate minimizer
    m = copy.deepcopy(correct_solution)
    m["minimizers"] = [m["minimizers"][0], m["minimizers"][0]]
    mutations.append(("duplicate_minimizer", m))

    # 12. Non-integer minimizer (float)
    m = copy.deepcopy(correct_solution)
    m["minimizers"] = [2.0]
    mutations.append(("float_minimizer", m))

    # 13. Wrong degeneracy (missing 2^{n-k} factor, e.g. 1 instead of 2)
    m = copy.deepcopy(correct_solution)
    m["degeneracy"] = 1
    mutations.append(("wrong_degeneracy_missing_factor", m))

    # 14. Non-integer degeneracy
    m = copy.deepcopy(correct_solution)
    m["degeneracy"] = 2.5
    mutations.append(("float_degeneracy", m))

    # 15. Negative degeneracy
    m = copy.deepcopy(correct_solution)
    m["degeneracy"] = -2
    mutations.append(("negative_degeneracy", m))

    # 16. Basis with non-existent term ID
    m = copy.deepcopy(correct_solution)
    m["basis"] = ["t_a", "non_existent_id"]
    mutations.append(("non_existent_basis_term", m))

    # 17. Dependent basis (repeat a generator)
    m = copy.deepcopy(correct_solution)
    m["basis"] = ["t_a", "t_a"]
    mutations.append(("dependent_basis", m))

    # 18. Decomposition missing a term
    m = copy.deepcopy(correct_solution)
    m["decomposition"] = [m["decomposition"][0]]
    mutations.append(("missing_decomposition_row", m))

    # 19. Decomposition with extra unknown term
    m = copy.deepcopy(correct_solution)
    m["decomposition"].append({"id": "extra_term", "mask": 0, "phase": 1})
    mutations.append(("extra_decomposition_row", m))

    # 20. Decomposition wrong mask
    m = copy.deepcopy(correct_solution)
    m["decomposition"][0]["mask"] = 3  # Wrong mask
    mutations.append(("wrong_decomposition_mask", m))

    # 21. Decomposition mask out of bounds (>= 2^k)
    m = copy.deepcopy(correct_solution)
    m["decomposition"][0]["mask"] = 16
    mutations.append(("mask_out_of_bounds", m))

    # 22. Status OUT_OF_SCOPE on commuting Hamiltonian
    m = {"id": "mut_base_case", "status": "OUT_OF_SCOPE", "witness": ["t_a", "t_b"]}
    mutations.append(("false_out_of_scope_commuting", m))

    # 23. OUT_OF_SCOPE with identical witness terms ["t_a", "t_a"]
    m = {"id": "mut_base_case", "status": "OUT_OF_SCOPE", "witness": ["t_a", "t_a"]}
    mutations.append(("identical_witness_terms", m))

    # 24. OUT_OF_SCOPE with missing witness
    m = {"id": "mut_base_case", "status": "OUT_OF_SCOPE"}
    mutations.append(("missing_witness", m))

    # 25. OUT_OF_SCOPE with 3 witness terms instead of 2
    m = {"id": "mut_base_case", "status": "OUT_OF_SCOPE", "witness": ["t_a", "t_b", "t_c"]}
    mutations.append(("three_witness_terms", m))

    # 26. Status UNKNOWN on well-formed case
    m = {"id": "mut_base_case", "status": "UNKNOWN", "refusal_code": "NUM_QUBITS_OUT_OF_BOUNDS"}
    mutations.append(("false_unknown_on_valid_case", m))

    # 27. UNKNOWN missing refusal code
    m = {"id": "mut_base_case", "status": "UNKNOWN"}
    mutations.append(("unknown_missing_refusal_code", m))

    # 28. Status invalid string
    m = {"id": "mut_base_case", "status": "PARTIALLY_SOLVED"}
    mutations.append(("invalid_status_string", m))

    # 29. Result is not a dict
    m = ["not", "a", "dict"]  # type: ignore
    mutations.append(("non_dict_result", m))

    # 30. Basis is not a list
    m = copy.deepcopy(correct_solution)
    m["basis"] = "t_a, t_b"
    mutations.append(("non_list_basis", m))

    # 31. Minimizers is not a list
    m = copy.deepcopy(correct_solution)
    m["minimizers"] = 2
    mutations.append(("non_list_minimizers", m))

    # 32. Decomposition is not a list
    m = copy.deepcopy(correct_solution)
    m["decomposition"] = {"id": "t_a", "mask": 1, "phase": 1}
    mutations.append(("non_list_decomposition", m))

    assert len(mutations) >= 30, f"Expected at least 30 mutations, got {len(mutations)}"

    for label, mutated_result in mutations:
        verdict = check_certificate(base_case, mutated_result, port=_STABILIZER)
        assert verdict["verdict"] == "FAIL", (
            f"Checker unexpectedly accepted mutation '{label}': {verdict}"
        )


# =============================================================================
# 5. DDC Operational Trace & Tape Verification
# =============================================================================


def test_c021_ddc_tape_verification(default_host: RustSymbolGameHost):
    tracer = DdcTracer(task_id="test_ddc_q40", initial_carrier="carrier_q40", host=default_host)
    tracer.set_initial_state(
        carrier="carrier_q40",
        residual=[Fraction(0, 1)],
        phi=Fraction(0, 1),
        gamma=Fraction(0, 1),
        adequate=True,
    )
    tracer.record_step(
        "C", "carrier_q40_exposed", [Fraction(0, 1)], Fraction(0, 1), Fraction(0, 1), True
    )
    tracer.record_step(
        "I",
        "carrier_q40_exposed",
        [Fraction(0, 1)],
        Fraction(0, 1),
        Fraction(0, 1),
        True,
        receipt=True,
    )
    tracer.record_step(
        "R", "carrier_q40_exposed", [Fraction(0, 1)], Fraction(0, 1), Fraction(0, 1), True
    )
    tracer.record_step(
        "D",
        "carrier_q40_repaired",
        [Fraction(0, 1)],
        Fraction(0, 1),
        Fraction(0, 1),
        True,
        loss_ledger=True,
    )
    tracer.record_step(
        "E", "carrier_q40_repaired", [Fraction(0, 1)], Fraction(0, 1), Fraction(0, 1), True
    )
    tracer.record_step(
        "T",
        "carrier_q40_repaired",
        [Fraction(0, 1)],
        Fraction(0, 1),
        Fraction(0, 1),
        True,
        receipt=True,
    )

    outcome = tracer.verify_tape_with_rust_host()
    assert outcome.get("lawful") is True, f"Rust host rejected DDC tape: {outcome}"


# =============================================================================
# 6. Refusal without a the city execution binding
# =============================================================================


def test_c021_adversary_swarm_requires_adversary_binding(tmp_path):
    overseer = AdversaryQuantumOverseer(repo_root=tmp_path, budget_ceiling=Decimal("0.25"))
    case = {
        "id": "h_07",
        "n": 3,
        "terms": [
            {"id": "t_a", "P": "XYZ", "w": [3, 2], "target": 1},
            {"id": "t_b", "P": "ZZI", "w": [1, 1], "target": -1},
        ],
    }
    res = overseer.execute_challenge("C021", case, task_key="c021_h07_test")
    assert res.verdict == "REFUSE"
    assert res.refusal_code == "ADVERSARY_EXECUTION_UNAVAILABLE"
    assert res.certificate.status == "UNKNOWN"
    assert res.receipt_sha256 == ""
    assert not res.output_directory.exists()
    assert list(tmp_path.iterdir()) == []


# =============================================================================
# 7. Budget Controller Ceiling Enforcement
# =============================================================================


def test_c021_budget_controller_hard_ceiling():
    controller = BudgetController(
        hard_ceiling_usd=Decimal("0.001"), target_budget_usd=Decimal("0.0005")
    )

    # Initial charge under target
    controller.charge("op1", "test_solver", inp_tokens=1000, outp_tokens=1000)
    assert controller.is_within_target

    # Charge exceeding ceiling must raise BudgetExhaustedRefusal
    with pytest.raises(BudgetExhaustedRefusal):
        controller.charge(
            "op2",
            "expensive_solver",
            inp_tokens=100000,
            outp_tokens=50000,
            rate_per_1k_input=Decimal("0.01"),
            rate_per_1k_output=Decimal("0.02"),
        )
