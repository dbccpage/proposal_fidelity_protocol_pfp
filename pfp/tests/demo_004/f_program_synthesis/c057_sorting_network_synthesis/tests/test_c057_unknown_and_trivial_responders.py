"""C057 judge corrections: UNKNOWN is accepted only on proven infeasibility.

Counterexamples retained from the 2026-09-28 audit:

- an always-UNKNOWN responder was accepted on every case that carried a prefix
  or a forbidden list, feasible or not (6 of 10 in the model matrix);
- a refuse-all (OUT_OF_SCOPE) responder must fail on every in-scope case;
- the reference solver could not be imported (``Optional`` was undefined);
- review of 2026-09-29: the judge proved infeasibility itself and ignored the
  answer's ``code``, so a constant UNKNOWN passed the 16 infeasible cases
  (refuse-all scored 16 of 64). UNKNOWN now passes only when ``code`` names a
  proof that holds on the case, and warranted refusals are reported apart.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.judge_packet import (
    exact_checker,
    independent_checker,
)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
CASES_DIR = PACKAGE_DIR / "judge_packet" / "cases"
CHECKERS = (
    ("exact", exact_checker.check),
    ("independent", independent_checker.independent_check),
)

PREFIX = "BOUND_BELOW_PREFIX_LENGTH"
INFO = "BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND"
OPT = "BOUND_BELOW_PROVEN_OPTIMAL_SIZE"
ADJ = "FORBIDDEN_ADJACENT_COMPARATOR"
PROOF_CODES = (PREFIX, INFO, OPT, ADJ)

LEDGER_PATH = PACKAGE_DIR / "judge_packet" / "case_id_ledger.json"
LEDGER: dict[str, str] = (
    json.loads(LEDGER_PATH.read_text(encoding="utf-8")) if LEDGER_PATH.exists() else {}
)

# The 16 judge cases whose infeasibility follows from a proof the checkers can
# cite, with every proof that holds: k below ceil(log2 n!) (INFO), below the
# proven optimal size (OPT), or a forbidden adjacent comparator (ADJ; every
# sorting network contains every [i, i+1]). No judge case has k below its prefix.
_RAW_HOLDING_CODES = {
    "c057_b12_n5_forbid_01": {ADJ},
    "c057_b15_n7_prefix_pairs": {ADJ},
    "c057_b25_infeas_n4_k4": {INFO, OPT},
    "c057_b26_infeas_n5_k8": {OPT},
    "c057_b27_infeas_n6_k11": {OPT},
    "c057_b28_infeas_n7_k15": {OPT},
    "c057_b29_infeas_n8_k18": {OPT},
    "c057_b30_infeas_n9_k24": {OPT},
    "c057_b31_infeas_n10_k28": {OPT},
    "c057_b32_infeas_n11_k34": {OPT},
    "c057_g04_relabel_n7_reflect_prefix": {ADJ},
    "c057_g11_infeas_reflect_n4": {INFO, OPT},
    "c057_g12_infeas_reflect_n9": {OPT},
    "c057_g13_infeas_reflect_n10": {OPT},
    "c057_p01_deceptive_opt_claim": {INFO, OPT},
    "c057_p02_deceptive_n9_opt": {OPT},
}
HOLDING_CODES = {LEDGER.get(k, k): v for k, v in _RAW_HOLDING_CODES.items()}
PROVEN_INFEASIBLE_CASE_IDS = frozenset(HOLDING_CODES)


def _load_cases() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CASES_DIR.glob("*.json"))]


CASES = _load_cases()
IN_SCOPE = [c for c in CASES if exact_checker.is_valid_case_input(c)[0]]


def _unknown(case: dict, code: object = "NO_NETWORK_FOUND_WITHIN_BOUND") -> dict:
    return {"case_id": case["case_id"], "status": "UNKNOWN", "code": code}


def test_case_inventory_matches_expected_split():
    assert len(CASES) == 64
    assert len(IN_SCOPE) == 50


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize(
    "code", ["NO_NETWORK_FOUND_WITHIN_BOUND", "INFEASIBLE", "", None, 7, *PROOF_CODES]
)
def test_constant_unknown_responder_scores_zero(name, checker, code):
    """A constant UNKNOWN, whatever its code, may pass at most the cases where that code holds."""
    accepted = {c["case_id"] for c in IN_SCOPE if checker(c, _unknown(c, code))[0]}
    expected = {cid for cid, holding in HOLDING_CODES.items() if code in holding}
    assert accepted == expected, (name, code)
    assert len(accepted) < len(PROVEN_INFEASIBLE_CASE_IDS)


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_unknown_with_a_generic_or_wrong_code_fails_and_the_holding_code_passes(name, checker):
    by_id = {c["case_id"]: c for c in IN_SCOPE}
    assert set(HOLDING_CODES) <= set(by_id)
    for cid, holding in HOLDING_CODES.items():
        case = by_id[cid]
        for code in holding:
            ok, msg = checker(case, _unknown(case, code))
            assert ok is True and msg.startswith("WARRANTED_REFUSAL"), (name, cid, code, msg)
        for code in set(PROOF_CODES) - holding:
            ok, msg = checker(case, _unknown(case, code))
            assert ok is False and msg.startswith("UNWARRANTED_REFUSAL"), (name, cid, code, msg)
        for code in (
            "NO_NETWORK_FOUND_WITHIN_BOUND",
            "UNKNOWN",
            "",
            None,
            ["BOUND_BELOW_PROVEN_OPTIMAL_SIZE"],
        ):
            assert checker(case, _unknown(case, code))[0] is False, (name, cid, code)
        missing = {"case_id": cid, "status": "UNKNOWN"}
        assert checker(case, missing)[0] is False, (name, cid)


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_prefix_length_code_passes_only_when_the_prefix_is_longer_than_k(name, checker):
    case = {"case_id": "pre", "n": 4, "k": 1, "prefix": [[0, 1], [2, 3]], "forbidden": []}
    assert checker(case, _unknown(case, PREFIX))[0] is True
    case = {"case_id": "pre2", "n": 4, "k": 4, "prefix": [[0, 1]], "forbidden": []}
    assert checker(case, _unknown(case, PREFIX))[0] is False
    assert checker(case, _unknown(case, INFO))[0] is True


def test_outcomes_report_warranted_refusals_apart_from_constructive_solutions():
    by_id = {c["case_id"]: c for c in CASES}
    infeasible = by_id[LEDGER.get("c057_b26_infeas_n5_k8", "c057_b26_infeas_n5_k8")]
    feasible = by_id[LEDGER.get("c057_b01_unconstrained_n4", "c057_b01_unconstrained_n4")]
    malformed = by_id[LEDGER.get("c057_p11_n_too_small", "c057_p11_n_too_small")]
    network = {
        "case_id": feasible["case_id"],
        "status": "SOLVED",
        "network": [[0, 2], [1, 3], [0, 1], [2, 3], [1, 2]],
    }
    oos = {
        "case_id": malformed["case_id"],
        "status": "OUT_OF_SCOPE",
        "witness": {"reason": "N_OUT_OF_BOUNDS"},
    }
    expectations = [
        (feasible, network, True, "ACCEPTED"),
        (infeasible, _unknown(infeasible, OPT), True, "WARRANTED_REFUSAL"),
        (malformed, oos, True, "WARRANTED_REFUSAL"),
        (infeasible, _unknown(infeasible), False, "UNWARRANTED_REFUSAL"),
        (feasible, _unknown(feasible, OPT), False, "UNWARRANTED_REFUSAL"),
        (feasible, {**oos, "case_id": feasible["case_id"]}, False, "UNWARRANTED_REFUSAL"),
        (feasible, {**network, "network": network["network"][:4]}, False, "REJECTED"),
    ]
    for case, answer, accepted, outcome in expectations:
        result = exact_checker.classify(case, answer)
        assert (result["accepted"], result["outcome"]) == (accepted, outcome), (
            case["case_id"],
            result,
        )
        ok, label, _ = independent_checker.independent_outcome(case, answer)
        assert (ok, label) == (accepted, outcome), (case["case_id"], label)


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_unknown_on_feasible_case_with_prefix_and_forbidden_list_is_rejected(name, checker):
    """Counterexample: matrix case m02 (n=4, k=5, prefix [[0,3]], forbidden [[0,2]]) is feasible."""
    case = {"case_id": "m02", "n": 4, "k": 5, "prefix": [[0, 3]], "forbidden": [[0, 2]]}
    ok, msg = checker(case, _unknown(case))
    assert ok is False, (name, msg)
    witness = {
        "case_id": "m02",
        "status": "SOLVED",
        "network": [[0, 3], [1, 2], [0, 1], [2, 3], [1, 2]],
    }
    assert checker(case, witness)[0] is True


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize(
    "reason",
    [
        "PREFIX_COMPARATOR_NOT_ORDERED",
        "N_OUT_OF_BOUNDS",
        "NEGATIVE_BOUND_K",
        "PREFIX_CONTAINS_FORBIDDEN_COMPARATOR",
    ],
)
def test_refuse_all_responder_fails_on_every_in_scope_case(name, checker, reason):
    for case in IN_SCOPE:
        refusal = {
            "case_id": case["case_id"],
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": reason},
        }
        assert checker(case, refusal)[0] is False, (name, case["case_id"])


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_empty_dict_and_constant_network_responders_fail(name, checker):
    constant = [[0, 2], [1, 3], [0, 1], [2, 3], [1, 2]]
    for case in CASES:
        assert checker(case, {})[0] is False, (name, case["case_id"])
        answer = {"case_id": case["case_id"], "status": "SOLVED", "network": constant}
        ok = checker(case, answer)[0]
        if ok:
            assert case["n"] == 4 and case["k"] >= 5 and not case["prefix"], case["case_id"]


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_forbidden_adjacent_comparator_is_a_proven_infeasibility(name, checker):
    case = {"case_id": "adj", "n": 5, "k": 30, "prefix": [], "forbidden": [[2, 3]]}
    assert checker(case, _unknown(case, ADJ))[0] is True
    # A non-adjacent forbidden comparator proves nothing: UNKNOWN is rejected.
    case = {"case_id": "nonadj", "n": 5, "k": 30, "prefix": [], "forbidden": [[1, 3]]}
    assert checker(case, _unknown(case, ADJ))[0] is False


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_alternative_valid_certificate_is_accepted(name, checker):
    """Semantic mutant: the mirror image of Floyd's 25-comparator network for n=9."""
    floyd = [
        (0, 3),
        (1, 7),
        (2, 5),
        (4, 8),
        (0, 7),
        (2, 4),
        (3, 8),
        (5, 6),
        (0, 2),
        (1, 3),
        (4, 5),
        (7, 8),
        (1, 4),
        (3, 6),
        (5, 7),
        (0, 1),
        (2, 4),
        (3, 5),
        (6, 8),
        (2, 3),
        (4, 5),
        (6, 7),
        (1, 2),
        (3, 4),
        (5, 6),
    ]
    mirrored = [[8 - j, 8 - i] for i, j in floyd]
    target_id = LEDGER.get("c057_g06_relabel_n9_reflect_opt", "c057_g06_relabel_n9_reflect_opt")
    case = next(c for c in CASES if c["case_id"] == target_id)
    assert mirrored[:4] == case["prefix"]
    ok, msg = checker(case, {"case_id": case["case_id"], "status": "SOLVED", "network": mirrored})
    assert ok is True, (name, msg)


def test_information_theoretic_bound_is_computed_exactly():
    for n in range(4, 13):
        exact = (math.factorial(n) - 1).bit_length()
        assert 2 ** (exact - 1) < math.factorial(n) <= 2**exact
        assert exact_checker.information_theoretic_lower_bound(n) == exact
        assert independent_checker.info_bound(n) == exact


def test_proven_optimal_table_is_disclosed_with_its_sources():
    source = exact_checker.PROVEN_OPTIMAL_SIZE_SOURCE
    for needle in ("Floyd", "Knuth", "Codish", "Harder", "not verified by this checker"):
        assert needle in source
    assert exact_checker.PROVEN_OPTIMAL_SIZE == {
        4: 5,
        5: 9,
        6: 12,
        7: 16,
        8: 19,
        9: 25,
        10: 29,
        11: 35,
        12: 39,
    }
    assert independent_checker.PROVEN_OPT == exact_checker.PROVEN_OPTIMAL_SIZE


def test_reference_solver_imports_and_passes_both_checkers_on_every_case():
    """Old code: ``reference_solver.solver`` raised NameError (``Optional``) at import."""
    from pfp.tests.demo_004.f_program_synthesis.c057_sorting_network_synthesis.reference_solver.solver import (
        solve,
    )

    for case in CASES:
        answer = solve(case)
        for name, checker in CHECKERS:
            ok, msg = checker(case, answer)
            assert ok is True, (name, case["case_id"], answer.get("status"), msg)
