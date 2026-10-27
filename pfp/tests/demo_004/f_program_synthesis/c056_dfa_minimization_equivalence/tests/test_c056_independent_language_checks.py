"""C056 judge corrections: exact language checks and no reference imports.

Counterexamples from the 2026-09-28 audit:

- a 1-state accept-everything DFA for the regex '%' (the empty word) passed the
  independent checker, which never compared L(DFA) with L(regex);
- EQUAL was checked by sampling words of length at most 4, so two regexes that
  differ only on a longer word were accepted as equal;
- both checkers imported the reference solver.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

import pytest
from pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.judge_packet import (
    exact_checker,
    independent_checker,
)

PACKAGE_DIR = Path(__file__).resolve().parents[1]
JUDGE_DIR = PACKAGE_DIR / "judge_packet"
CHECKERS = (
    ("exact", exact_checker.check_exact),
    ("independent", independent_checker.independent_check),
)
CASES = [
    json.loads(p.read_text(encoding="utf-8")) for p in sorted((JUDGE_DIR / "cases").glob("*.json"))
]
ONE_STATE_ACCEPT_ALL = {
    "states": 1,
    "accept": [0],
    "delta": [[0, 0]],
    "access": [""],
    "separators": {},
}


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_one_state_accept_everything_dfa_for_empty_word_fails(name, checker):
    case = {"case_id": "eps", "task": "MINIMIZE", "alphabet": ["a", "b"], "regex": "%"}
    ok, msg = checker(case, {"case_id": "eps", "status": "SOLVED", **ONE_STATE_ACCEPT_ALL})
    assert ok is False, (name, msg)


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_equal_claim_on_languages_differing_only_beyond_length_four_fails(name, checker):
    case = {"case_id": "long", "task": "EQUIV", "alphabet": ["a", "b"], "r1": "aaaaa|b", "r2": "b"}
    dfa_b = {"states": 3, "accept": [1], "delta": [[2, 1], [2, 2], [2, 2]]}
    answer = {
        "case_id": "long",
        "status": "SOLVED",
        "kind": "EQUAL",
        "dfa1": dfa_b,
        "dfa2": dfa_b,
        "bijection": {"0": 0, "1": 1, "2": 2},
    }
    ok, msg = checker(case, answer)
    assert ok is False, (name, msg)
    different = {"case_id": "long", "status": "SOLVED", "kind": "DIFFERENT", "word": "aaaaa"}
    assert checker(case, different)[0] is True


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_equal_answer_must_carry_its_own_automata(name, checker):
    """The old exact checker let a missing dfa1/dfa2 default to the reference's automata."""
    case = {"case_id": "comm", "task": "EQUIV", "alphabet": ["a", "b"], "r1": "a|b", "r2": "b|a"}
    ok, msg = checker(
        case,
        {
            "case_id": "comm",
            "status": "SOLVED",
            "kind": "EQUAL",
            "bijection": {"0": 0, "1": 1, "2": 2},
        },
    )
    assert ok is False, (name, msg)


@pytest.mark.parametrize("path", sorted(JUDGE_DIR.glob("*_checker.py")), ids=lambda p: p.name)
def test_checkers_import_neither_the_reference_nor_each_other(path):
    source = path.read_text(encoding="utf-8")
    imports = [line for line in source.splitlines() if re.match(r"\s*(from|import)\s", line)]
    assert not [line for line in imports if "reference_solver" in line or "checker" in line], (
        imports
    )


@pytest.mark.parametrize("name,checker", CHECKERS)
def test_trivial_responders_fail_on_every_in_scope_case(name, checker):
    in_scope = [c for c in CASES if exact_checker._validate_case(c)[0] is not None]
    assert len(in_scope) == 50
    for case in in_scope:
        cid = case["case_id"]
        for answer in (
            {},
            [],
            {"case_id": cid, "status": "OUT_OF_SCOPE", "witness": {"reason": "PARSE_ERROR"}},
            {"case_id": cid, "status": "UNKNOWN"},
            {"case_id": cid, "status": "SOLVED", **ONE_STATE_ACCEPT_ALL},
        ):
            ok, _ = checker(case, answer)
            if ok:
                # The accept-everything DFA is right exactly when the language is universal.
                assert answer.get("states") == 1 and case["task"] == "MINIMIZE", cid
                assert all(
                    exact_checker.matches(exact_checker.parse(case["regex"], case["alphabet"]), w)
                    for w in ("", "ab", "ba", "bb")
                )


def test_reference_solver_passes_and_every_hostile_mutation_fails_both_checkers():
    from pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.reference_solver import (
        solve,
    )

    for case in CASES:
        answer = solve(case)
        for name, checker in CHECKERS:
            assert checker(case, answer)[0] is True, (name, case["case_id"])
    mutations = sorted((JUDGE_DIR / "hostile_mutations").glob("*.json"))
    assert mutations
    for path in mutations:
        mutation = json.loads(path.read_text(encoding="utf-8"))
        for name, checker in CHECKERS:
            assert checker(mutation["case"], mutation["mutated_result"])[0] is False, (
                name,
                path.name,
            )


def test_both_parsers_agree_with_the_reference_grammar_on_random_strings():
    """Scope decisions must not change: same accepted strings, same languages."""
    from pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.reference_solver.dfa_engine import (
        compile_minimal_dfa,
    )
    from pfp.tests.demo_004.f_program_synthesis.c056_dfa_minimization_equivalence.reference_solver.regex_parser import (
        parse_regex,
    )

    rng = random.Random(56)
    alphabet = ["a", "b"]
    symbols = "ab%#()*| "
    for _ in range(4000):
        text = "".join(rng.choice(symbols) for _ in range(rng.randint(0, 7)))
        try:
            ref = compile_minimal_dfa(parse_regex(text, alphabet), alphabet)
        except Exception:  # noqa: BLE001 - any reference parse failure means out of scope
            ref = None
        for name, parse in (
            ("exact", exact_checker.parse),
            ("independent", independent_checker.parse_expression),
        ):
            try:
                parse(text, alphabet)
                parsed = True
            except (exact_checker.RegexSyntaxError, independent_checker.NotARegex):
                parsed = False
            assert parsed is (ref is not None), (name, text)
        if ref is None:
            continue
        case = {"case_id": "fuzz", "task": "MINIMIZE", "alphabet": alphabet, "regex": text}
        answer = {"case_id": "fuzz", "status": "SOLVED", **ref}
        for name, checker in CHECKERS:
            assert checker(case, answer)[0] is True, (name, text)


def test_runner_prompt_defines_empty_set_and_empty_word():
    source = (PACKAGE_DIR / "run_c056_matrix.py").read_text(encoding="utf-8")
    assert "dotenv" not in source, "runner must not read .env files"
    import importlib

    runner = importlib.import_module(
        "pfp.tests.demo_004.f_program_synthesis."
        "c056_dfa_minimization_equivalence.run_c056_matrix"
    )
    prompt = runner.SYSTEM_PROMPT
    assert "`#` denotes the empty language" in prompt and "`%` denotes the empty word" in prompt
    assert "RFC 8785" not in prompt
    for case, token, user_prompt in runner.SPEC.prompts():
        assert case["case_id"] not in user_prompt and token in user_prompt
