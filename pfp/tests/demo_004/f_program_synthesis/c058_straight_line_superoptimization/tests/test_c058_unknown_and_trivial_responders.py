"""C058 judge verification: UNKNOWN is accepted only on genuine irreducibility.

Theoretical minimum and trivial-responder matrix test per §3.2 and §7 (UOW-3.1):
- Invariant: for every in-scope solvable case, no trivial responder is accepted by both checkers,
  and the reference answer is.
- Break: C058 accepts UNKNOWN whenever its heuristic finds nothing.
- Witness: this test rejects UNKNOWN on all 45 solvable cases across both checkers.
- Mutation: if exact_checker restores unconditional `return True, "UNKNOWN_ACCEPTED"` on solvable cases,
  `test_constant_unknown_responder_fails_on_all_solvable_cases` fails.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from omega_engine_pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.judge_packet import (
    exact_checker,
    independent_checker,
)
from omega_engine_pfp.tests.demo_004.f_program_synthesis.c058_straight_line_superoptimization.reference_solver import (
    solve,
)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
CASES_DIR = PACKAGE_DIR / "judge_packet" / "cases"
CHECKERS = (
    ("exact", exact_checker.verify_candidate),
    ("independent", independent_checker.check_candidate_indep),
)

GENUINE_UNKNOWN_IDS = frozenset(
    {
        "c058_b27_unknown_add_target0",
        "c058_b28_unknown_mul_target0",
        "c058_b29_unknown_xor_target0_w32",
        "c058_b30_unknown_sub_target0_w32",
        "c058_g16_unknown_renamed",
    }
)


def _load_cases() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CASES_DIR.glob("*.json"))]


CASES = _load_cases()
IN_SCOPE = [c for c in CASES if exact_checker.validate_ir(c)[0]]
SOLVABLE = [c for c in IN_SCOPE if c["case_id"] not in GENUINE_UNKNOWN_IDS]


def _unknown(case: dict, code: object = "NO_SHORTER_FOUND") -> dict:
    res = {"case_id": case["case_id"], "status": "UNKNOWN"}
    if code is not None:
        res["code"] = code
    return res


def test_case_inventory_and_split():
    assert len(CASES) == 64
    assert len(IN_SCOPE) == 50
    assert len(SOLVABLE) == 45
    assert len(GENUINE_UNKNOWN_IDS) == 5


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_reference_solver_answers_accepted_on_all_cases(name, checker):
    for case in CASES:
        ans = solve(case)
        ok, msg = checker(case, ans)
        assert ok is True, f"{name} failed on reference answer for {case['case_id']}: {msg}"


@pytest.mark.parametrize("name,checker", CHECKERS)
@pytest.mark.parametrize("code", ["NO_SHORTER_FOUND", "UNKNOWN", "INFEASIBLE", "", None, 123])
def test_constant_unknown_responder_fails_on_all_solvable_cases(name, checker, code):
    """Witness to the invariant: UNKNOWN must be rejected on every solvable case."""
    for case in SOLVABLE:
        ok, msg = checker(case, _unknown(case, code))
        assert ok is False, (
            f"{name} incorrectly accepted UNKNOWN with code={code!r} on solvable case {case['case_id']}: {msg}"
        )


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_unknown_accepted_only_on_genuine_irreducible_cases(name, checker):
    for case in IN_SCOPE:
        cid = case["case_id"]
        ans = _unknown(case, "NO_SHORTER_FOUND")
        ok, msg = checker(case, ans)
        if cid in GENUINE_UNKNOWN_IDS:
            assert ok is True, f"{name} rejected genuine UNKNOWN on {cid}: {msg}"
        else:
            assert ok is False, f"{name} accepted false UNKNOWN on {cid}: {msg}"


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_refuse_all_responder_fails_on_every_in_scope_case(name, checker):
    for case in IN_SCOPE:
        refusal = {
            "case_id": case["case_id"],
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_OPS"},
        }
        ok, msg = checker(case, refusal)
        assert ok is False, f"{name} accepted refuse-all on in-scope case {case['case_id']}: {msg}"


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_empty_dict_and_malformed_candidates_fail(name, checker):
    for case in CASES:
        assert checker(case, {})[0] is False, f"{name} accepted empty dict on {case['case_id']}"
        assert checker(case, {"case_id": case["case_id"]})[0] is False, (
            f"{name} accepted missing status on {case['case_id']}"
        )
        assert (
            checker(case, {"case_id": "wrong_id", "status": "SOLVED", "ops": [], "out": "x"})[0]
            is False
        ), f"{name} accepted wrong case_id"
