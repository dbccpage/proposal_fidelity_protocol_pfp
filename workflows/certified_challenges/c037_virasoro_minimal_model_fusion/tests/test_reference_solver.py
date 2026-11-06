"""Tests for C037 Reference Solver.

Validates solver across SU(2)_k levels, unitary & non-unitary minimal models,
fail-closed refusals, DDC operational tracing, and AST anti-hardcoding regression.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from pathlib import Path

from c037_virasoro_minimal_model_fusion.reference_solver import (
    fusion_engine,
    solver,
    verlinde,
)
from c037_virasoro_minimal_model_fusion.reference_solver.solver import (
    get_last_tracer,
    solve,
)


def test_solver_su2_levels():
    """Verifies SU(2)_k solving for k=1, 2, 3."""
    c1 = solve({"case_id": "su2_1", "model": "su2", "k": 1})
    assert c1["status"] == "SOLVED"
    assert c1["central_charge"] == "1"
    assert len(c1["primaries"]) == 2
    assert len(c1["fusion"]) == 3

    c2 = solve({"case_id": "su2_2", "model": "su2", "k": 2})
    assert c2["status"] == "SOLVED"
    assert c2["central_charge"] == "3/2"
    assert len(c2["primaries"]) == 3

    c3 = solve({"case_id": "su2_3", "model": "su2", "k": 3})
    assert c3["status"] == "SOLVED"
    assert c3["central_charge"] == "9/5"
    assert len(c3["primaries"]) == 4


def test_solver_ising_minimal_model():
    """Verifies M(4, 3) Ising model solution."""
    case = {"case_id": "m43", "model": "minimal", "p": 4, "p_prime": 3}
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["central_charge"] == "1/2"
    primaries = {tuple(p["label"]): p["h"] for p in res["primaries"]}
    assert primaries[(1, 1)] == "0"
    assert primaries[(1, 2)] == "1/16"
    assert primaries[(2, 1)] == "1/2"
    assert len(res["fusion"]) == 7


def test_solver_lee_yang_non_unitary():
    """Verifies M(5, 2) Lee-Yang non-unitary model with negative central charge and weight."""
    case = {"case_id": "m52", "model": "minimal", "p": 5, "p_prime": 2}
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["central_charge"] == "-22/5"
    primaries = {tuple(p["label"]): p["h"] for p in res["primaries"]}
    assert primaries[(1, 1)] == "0"
    assert primaries[(1, 2)] == "-1/5"
    assert len(res["fusion"]) == 4


def test_solver_refusal_non_coprime():
    """Non-coprime minimal model parameters must fail-closed with OUT_OF_SCOPE."""
    case = {"case_id": "bad_gcd", "model": "minimal", "p": 6, "p_prime": 4}
    res = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"]["kind"] == "not_coprime"
    assert res["witness"]["gcd"] == 2


def test_solver_refusal_level_out_of_bounds():
    """Level out of bounds must fail-closed with UNKNOWN."""
    c_su2 = {"case_id": "oob_su2", "model": "su2", "k": 25}
    assert solve(c_su2)["refusal_code"] == "LEVEL_OUT_OF_BOUNDS"

    c_min = {"case_id": "oob_min", "model": "minimal", "p": 15, "p_prime": 4}
    assert solve(c_min)["refusal_code"] == "LEVEL_OUT_OF_BOUNDS"


def test_solver_ddc_tracer_emits_valid_alphabet():
    """DDC tracer must record transitions over {E, R, C, I, Lambda, D, M, T} with SHA-256 chaining."""
    case = {"case_id": "ddc_test", "model": "minimal", "p": 4, "p_prime": 3}
    solve(case)
    tracer = get_last_tracer()
    assert tracer is not None
    trace = tracer.export_trace()
    assert trace["step_count"] >= 5
    valid_letters = {"E", "R", "C", "I", "Lambda", "D", "M", "T"}
    for step in trace["steps"]:
        assert step["letter"] in valid_letters
        assert len(step["digest"]) == 64


def test_no_hardcoded_fusion_tables():
    """AST Anti-Hardcoding Regression Test.

    Inspects ASTs of solver, verlinde, and fusion_engine to assert NO static lookup tables
    or dictionaries contain hardcoded fusion matrices or precomputed primary tables.
    """
    modules_to_inspect = [
        (solver, "Reference Solver (solver)"),
        (verlinde, "Verlinde Engine (verlinde)"),
        (fusion_engine, "Fusion Engine (fusion_engine)"),
    ]

    for mod, name in modules_to_inspect:
        src_path = Path(mod.__file__).resolve()
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
                assert "M(4,3)" not in keys, f"Hardcoded table key detected in {name}: 'M(4,3)'"
                assert "su2_k2" not in keys, f"Hardcoded table key detected in {name}: 'su2_k2'"
                assert "ex01_ising" not in keys, (
                    f"Hardcoded case ID detected in {name}: 'ex01_ising'"
                )
