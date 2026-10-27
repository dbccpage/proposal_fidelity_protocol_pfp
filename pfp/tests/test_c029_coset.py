"""Current C029 coset checks; retained packet bytes are read-only fixtures."""

import builtins
import importlib
import json
import platform
import random
from copy import deepcopy
from pathlib import Path

import pytest

from pfp.domain.quantum.c029_coset import verify_independent_coset
from pfp.infrastructure import challenge_execution as execution

CHALLENGE = execution.ROOT / (
    "demos/certified_challenges/c029_surface_code_min_weight_decoding"
)
CURRENT_SOURCE = "pfp/domain/quantum/c029_coset.py"
CHECKER_ID = "c029:gf2_coset_optimality.v1"


def test_current_route_replaces_only_the_shared_second_checker():
    judges = execution.judges_for(CHALLENGE)
    assert [name for name, _ in judges] == ["exact_checker:verify_exact", CHECKER_ID]
    assert judges[0][1].__module__.endswith(".judge_packet.checkers.exact_checker")


def test_current_checker_is_source_bound_for_replay():
    bindings = execution.source_bindings(CHALLENGE)
    assert CURRENT_SOURCE in bindings
    assert bindings[CURRENT_SOURCE] == execution.digest((execution.ROOT / CURRENT_SOURCE).read_bytes())


def case_file(name="base_02.json"):
    return json.loads((CHALLENGE / "judge_packet/cases" / name).read_bytes())


def answer(case, correction):
    return dict(id=case["case_id"], status="SOLVED", correction=correction,
                weight=sum(case["weights"][q] for q in correction), certificate={})


def original_answer():
    result = answer(case_file(), [0])
    result["certificate"] = dict(pairs=[], boundary_matches=[0],
                                 vertex_duals=["3", "0"], odd_set_duals=[])
    return result


def source_row():
    source = CHALLENGE / "judge_packet/cases/base_02.json"
    return dict(challenge="C029", source=source.relative_to(execution.ROOT).as_posix(),
                sha256=execution.digest(source.read_bytes()), index=None)


def test_original_positive_and_strictly_suboptimal_same_syndrome():
    case = case_file()
    assert verify_independent_coset(case, original_answer())[0] is True
    result = verify_independent_coset(case, answer(case, [4, 5]))
    assert result[0] is False
    assert result[2] == dict(actual_weight=5, min_weight=3, kernel_dimension=5)


def test_tied_original_corrections_are_both_accepted():
    case = case_file()
    for correction in ([0], [3]):
        assert verify_independent_coset(case, answer(case, correction))[0] is True


def test_random_small_matrices_agree_with_full_vector_enumeration():
    rng = random.Random(29029)
    for _ in range(35):
        hz = [[rng.randrange(2) for _ in range(9)] for _ in range(4)]
        weights = [rng.randint(1, 5) for _ in range(9)]
        seed = rng.randrange(1 << 9)
        syndrome = [sum(bit * ((seed >> q) & 1) for q, bit in enumerate(row)) % 2
                    for row in hz]
        case = dict(case_id="random", code="rotated", distance=3, hz=hz,
                    weights=weights, syndrome=syndrome)
        feasible = [bits for bits in range(1 << 9) if all(
            sum(bit * ((bits >> q) & 1) for q, bit in enumerate(row)) % 2 == target
            for row, target in zip(hz, syndrome)
        )]
        weight = lambda bits: sum(w for q, w in enumerate(weights) if bits & (1 << q))
        optimum = min(map(weight, feasible))
        for bits in (min(feasible, key=weight), max(feasible, key=weight), seed):
            correction = [q for q in range(9) if bits & (1 << q)]
            accepted, _, details = verify_independent_coset(case, answer(case, correction))
            assert details["min_weight"] == optimum
            assert accepted is (weight(bits) == optimum)


@pytest.mark.parametrize("name,n,k", [("base_18.json", 49, 25), ("base_34.json", 50, 26)])
def test_original_maximum_dimensions_are_supported(name, n, k):
    case = case_file(name)
    assert len(case["weights"]) == n
    accepted, _, details = verify_independent_coset(case, answer(case, [0]))
    assert accepted is True
    assert details["kernel_dimension"] == k
    assert details["min_weight"] == case["weights"][0]


@pytest.mark.parametrize("name,correction,k", [
    ("base_24.json", [35, 0, 1, 19, 23, 44, 12, 37], 25),
    ("base_36.json", [6, 5, 47, 15], 26),
])
def test_original_maximum_weighted_cases_reject_nonminimal_generated_errors(name, correction, k):
    case = case_file(name)
    accepted, reason, details = verify_independent_coset(case, answer(case, correction))
    assert accepted is False and reason == "Correction is suboptimal"
    assert details["min_weight"] < details["actual_weight"]
    assert details["kernel_dimension"] == k


def test_no_matching_or_primary_checker_dependency_even_when_poisoned(monkeypatch):
    historical = importlib.import_module(
        "c029_surface_code_min_weight_decoding"
        ".judge_packet.checkers.independent_checker"
    )
    case = case_file()
    bad = answer(case, [4, 5])
    monkeypatch.setattr(historical, "solve_min_weight_decoding",
                        lambda *args: (True, {"weight": 5}, {}))
    assert historical.verify_independent(case, bad)[0] is True

    original_import = builtins.__import__

    def guarded(name, *args, **kwargs):
        if any(part in name for part in ("reference_solver", "exact_checker", "matching_solver")):
            raise AssertionError("Shared matching implementation must not be used")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded)
    module = importlib.reload(importlib.import_module("pfp.domain.quantum.c029_coset"))
    assert module.verify_independent_coset(case, original_answer())[0] is True
    assert module.verify_independent_coset(case, bad)[0] is False


@pytest.mark.parametrize("field,value", [
    ("hz", []), ("hz", [[0] * 9] * 3), ("weights", [1] * 8),
    ("weights", [True] + [1] * 8), ("weights", [0] + [1] * 8),
    ("weights", [6] + [1] * 8), ("syndrome", [0, 1, True, 0]),
    ("syndrome", [0, 1]), ("distance", True), ("code", None),
])
def test_malformed_case_cannot_be_admitted(field, value):
    case = case_file()
    case[field] = value
    assert verify_independent_coset(case, original_answer())[0] is False


@pytest.mark.parametrize("field,value", [
    ("correction", [0, 0]), ("correction", [-1]), ("correction", [9]),
    ("correction", [True]), ("correction", []), ("weight", 3.0),
    ("weight", True), ("weight", 2), ("certificate", []), ("status", []),
    ("id", "wrong-case"),
])
def test_malformed_or_wrong_correction_cannot_be_admitted(field, value):
    result = original_answer()
    result[field] = value
    assert verify_independent_coset(case_file(), result)[0] is False


def test_nonbinary_matrix_and_excess_kernel_reject_without_search():
    case = case_file()
    case["hz"][0][0] = True
    assert verify_independent_coset(case, original_answer())[0] is False
    case = case_file("base_34.json")
    case["hz"] = [[0] * 50 for _ in range(25)]
    case["syndrome"] = [0] * 25
    checked = verify_independent_coset(case, answer(case, []))
    assert checked[0] is False and "Kernel dimension" in checked[1]


def test_refusal_predicates_are_independently_checked():
    case = case_file("poison_02.json")
    refusal = dict(id=case["case_id"], status="OUT_OF_SCOPE",
                   witness={"kind": "odd_parity_on_torus", "rows": "all"})
    assert verify_independent_coset(case, refusal)[0] is True
    case["hz"][0][0] ^= 1  # Odd syndrome alone does not establish a dependency.
    assert verify_independent_coset(case, refusal)[0] is False
    case = case_file("poison_04.json")  # Retained distance 6 fixture has 72 qubits.
    refusal = dict(id=case["case_id"], status="UNKNOWN", refusal_code="DISTANCE_OUT_OF_BOUNDS")
    assert verify_independent_coset(case, refusal)[0] is True
    case["distance"] = 5
    assert verify_independent_coset(case, refusal)[0] is False
    case = dict(case_id="unknown", code="other", distance=3)
    refusal = dict(id="unknown", status="OUT_OF_SCOPE",
                   witness={"kind": "unknown_code_type", "code": "other"})
    assert verify_independent_coset(case, refusal)[0] is True
    refusal["witness"]["code"] = "rotated"
    assert verify_independent_coset(case, refusal)[0] is False


def test_actual_route_keeps_required_certificate_and_typed_refusal():
    good = execution.worker(dict(kind="CHECK_ANSWER", row=source_row(), answer=original_answer()))
    assert good["status"] == "HOST_ACCEPTED", good
    assert [j["judge"] for j in good["judges"]] == ["exact_checker:verify_exact", CHECKER_ID]
    wrong = original_answer()
    wrong["certificate"]["vertex_duals"] = ["0", "0"]
    bad = execution.worker(dict(kind="CHECK_ANSWER", row=source_row(), answer=wrong))
    assert bad["status"] == "CHECKER_DEFECT" and bad["failure_class"] == "DISAGREEMENT"
    assert [j["accepted"] for j in bad["judges"]] == [False, True]
    case = case_file("poison_02.json")
    source = CHALLENGE / "judge_packet/cases/poison_02.json"
    row = dict(source_row(), source=source.relative_to(execution.ROOT).as_posix(),
               sha256=execution.digest(source.read_bytes()))
    refusal = dict(id=case["case_id"], status="OUT_OF_SCOPE",
                   witness={"kind": "odd_parity_on_torus", "rows": "all"})
    checked = execution.worker(dict(kind="CHECK_ANSWER", row=row, answer=refusal))
    assert checked["status"] == "TYPED_REFUSAL", checked


def test_real_toric_geometry_exposes_historical_dual_defect_independently():
    case = case_file("base_29.json")
    case["case_id"] = "toric_l4_adversarial_dual"
    case["weights"] = [1] * 32
    defects = {0, 1, 2, 4, 5, 6}
    case["syndrome"] = [int(row in defects) for row in range(16)]

    def edge(a, b):
        return next(q for q in range(32) if {
            r for r in range(16) if case["hz"][r][q]
        } == {a, b})

    case["weights"][edge(0, 1)] = 2
    wrong = answer(case, [edge(0, 1), edge(2, 6), edge(5, 4)])
    better = answer(case, [edge(1, 2), edge(6, 5), edge(4, 0)])
    assert wrong["weight"] == 4 and better["weight"] == 3
    wrong["certificate"] = dict(pairs=[], boundary_matches=[], vertex_duals=["0"] * 6,
                                odd_set_duals=[[[0, 2, 4], "2"], [[1, 3, 5], "2"]])
    primary, independent = execution.judges_for(CHALLENGE)
    assert primary[1](case, wrong)[0] is True  # Retained primary defect, not corrected here.
    accepted, _, details = independent[1](case, wrong)
    assert accepted is False and details["min_weight"] == 3
    assert independent[1](case, better)[0] is True
    result = execution.CheckProposalUseCase().check_answer(
        case, wrong, execution.judges_for(CHALLENGE)
    )
    assert result.status == "CHECKER_DEFECT" and result.failure_class == "DISAGREEMENT"


def test_current_source_mutation_blocks_replay_before_any_worker(tmp_path, monkeypatch):
    receipt = dict(python=platform.python_version(), sources=execution.source_bindings(CHALLENGE),
                   row=source_row(), result={})
    raw = execution.canonical(receipt)
    (tmp_path / "control.json").write_bytes(raw)
    (tmp_path / "manifest.json").write_bytes(execution.canonical({"rows": [dict(
        path="control.json", sha256=execution.digest(raw)
    )]}))
    original_read = Path.read_bytes

    def changed_read(path):
        content = original_read(path)
        return content + b"\n# changed checker" if path == execution.ROOT / CURRENT_SOURCE else content

    def unexpected_worker(*args, **kwargs):
        pytest.fail("Replay must detect current source drift before executing any worker")

    monkeypatch.setattr(Path, "read_bytes", changed_read)
    monkeypatch.setattr(execution, "isolated", unexpected_worker)
    with pytest.raises(ValueError, match="CHECKER_SOURCE_DRIFT"):
        execution.replay_host(tmp_path)


def test_checker_never_mutates_case_or_candidate():
    case, result = case_file(), original_answer()
    before = deepcopy((case, result))
    verify_independent_coset(case, result)
    assert (case, result) == before
