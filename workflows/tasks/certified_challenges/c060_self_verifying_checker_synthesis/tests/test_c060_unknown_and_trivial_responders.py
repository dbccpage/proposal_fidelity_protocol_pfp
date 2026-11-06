"""C060 judge tests: Trivial responders fail, checkers are import-independent, and reference solver passes.

Verifies:
- Checkers have zero import dependence on reference_solver.
- Constant ACCEPT responder fails on all 48 corrupt/invalid cases.
- Constant REJECT responder fails on all 16 valid self-certificate cases.
- Malformed and trivial responders (empty dict, UNKNOWN, OUT_OF_SCOPE) fail on all cases.
- Reference solver passes both checkers on all 64 judge cases.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c060_self_verifying_checker_synthesis.judge_packet import (
    exact_checker,
    independent_checker,
)
from c060_self_verifying_checker_synthesis.reference_solver.checker import (
    check as ref_check,
)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
CASES_DIR = PACKAGE_DIR / "judge_packet" / "cases"
CHECKERS = (
    ("exact", exact_checker.verify_candidate),
    ("independent", independent_checker.independent_check),
)


def _load_cases() -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(CASES_DIR.glob("*.json"))]


CASES = _load_cases()
ACCEPT_CASES = [c for c in CASES if c.get("expected_verdict") == "ACCEPT"]
REJECT_CASES = [c for c in CASES if c.get("expected_verdict") == "REJECT"]


def test_case_inventory():
    assert len(CASES) == 64
    assert len(ACCEPT_CASES) == 32
    assert len(REJECT_CASES) == 32


def test_checkers_have_zero_import_dependence_on_reference_solver():
    """Exact checker and independent checker must not import from reference_solver."""
    import inspect

    exact_src = inspect.getsource(exact_checker)
    indep_src = inspect.getsource(independent_checker)
    assert "reference_solver" not in exact_src
    assert "reference_solver" not in indep_src


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_reference_solver_passes_both_checkers_on_all_cases(name, checker):
    for case in CASES:
        c_case = case.get("case")
        c_cert = case.get("cert")
        ans = ref_check(c_case, c_cert)
        ok, msg = checker(case, ans)
        assert ok is True, f"Reference solver failed on {case['case_id']} under {name}: {msg}"


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_constant_accept_responder_fails_on_all_reject_cases(name, checker):
    cand = {"verdict": "ACCEPT", "code": None, "reason": "All good."}
    for case in REJECT_CASES:
        ok, msg = checker(case, cand)
        assert ok is False, (
            f"Constant ACCEPT unexpectedly passed reject case {case['case_id']} under {name}"
        )


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_constant_reject_responder_fails_on_all_accept_cases(name, checker):
    cand = {"verdict": "REJECT", "code": "SCHEMA", "reason": "Refused."}
    for case in ACCEPT_CASES:
        ok, msg = checker(case, cand)
        assert ok is False, (
            f"Constant REJECT unexpectedly passed accept case {case['case_id']} under {name}"
        )


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_empty_dict_and_malformed_responders_fail_on_all_cases(name, checker):
    for case in CASES:
        assert checker(case, {})[0] is False, f"Empty dict passed on {case['case_id']} under {name}"
        assert checker(case, {"verdict": "UNKNOWN"})[0] is False, (
            f"UNKNOWN passed on {case['case_id']} under {name}"
        )
        assert checker(case, {"status": "OUT_OF_SCOPE"})[0] is False, (
            f"OUT_OF_SCOPE passed on {case['case_id']} under {name}"
        )
        assert checker(case, None)[0] is False, f"None passed on {case['case_id']} under {name}"
