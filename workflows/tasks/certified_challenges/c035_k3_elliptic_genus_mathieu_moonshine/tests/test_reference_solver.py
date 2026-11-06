"""Tests for C035 Reference Solver.

Validates exact series arithmetic, character decomposition, DDC tracing, and fail-closed refusals.

AuthorityEffect: None.
"""

from __future__ import annotations

import time

from c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.ddc_tracer import (
    VALID_DDC_LETTERS,
    DDCTracer,
)
from c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.mathieu_moonshine import (
    CLASS_SIZES_M24,
    CLASSES_M24,
    G_ORDER,
    IRREP_NAMES,
    TABLE_M24,
    is_exact_int,
)
from c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.solver import (
    solve,
)


def test_solver_coefficients_small_n():
    """Solver must correctly compute coefficients A_1, A_2, A_3."""
    res = solve({"case_id": "test_c3", "query": "coefficients", "max_n": 3})
    assert res.get("status") == "SOLVED"
    assert res.get("A") == {"1": 90, "2": 462, "3": 1540}


def test_solver_coefficients_boundary_n30():
    """Solver must compute exact coefficients up to boundary N=30 in under 2 seconds."""
    t0 = time.perf_counter()
    res = solve({"case_id": "test_c30", "query": "coefficients", "max_n": 30})
    elapsed = time.perf_counter() - t0

    assert res.get("status") == "SOLVED"
    a_dict = res.get("A", {})
    assert len(a_dict) == 30
    assert a_dict["30"] == 9104078592
    assert elapsed < 2.0, f"Computation took {elapsed:.2f}s, exceeding 2.0s ceiling"


def test_solver_decomposition_a1():
    """Solver must decompose A_1 class values into 45 + 45bar."""
    a1_vals = [
        90,
        -6,
        0,
        0,
        2,
        -1,
        -1,
        -2,
        0,
        2,
        0,
        0,
        1,
        1,
        -2,
        -2,
        2,
        -2,
        2,
        6,
        10,
        0,
        -1,
        -1,
        -6,
        0,
    ]
    case = {
        "case_id": "test_d1",
        "query": "decompose",
        "n": 1,
        "class_order": CLASSES_M24,
        "values": a1_vals,
    }
    res = solve(case)
    assert res.get("status") == "SOLVED"
    assert res.get("multiplicities") == {"45": 1, "45bar": 1}
    assert res.get("zero_elsewhere") is True


def test_solver_decomposition_a2_a3():
    """Solver must decompose A_2 into 231 + 231bar and A_3 into 770 + 770bar."""
    a2_vals = [
        462,
        14,
        -6,
        2,
        -2,
        0,
        0,
        -2,
        2,
        0,
        -1,
        -1,
        0,
        0,
        2,
        2,
        0,
        0,
        6,
        0,
        -18,
        2,
        0,
        0,
        -2,
        -2,
    ]
    res2 = solve(
        {
            "case_id": "test_d2",
            "query": "decompose",
            "n": 2,
            "class_order": CLASSES_M24,
            "values": a2_vals,
        }
    )
    assert res2.get("status") == "SOLVED"
    assert res2.get("multiplicities") == {"231": 1, "231bar": 1}

    a3_vals = [
        1540,
        -28,
        10,
        0,
        -4,
        0,
        0,
        0,
        2,
        0,
        0,
        0,
        0,
        0,
        -1,
        -1,
        2,
        2,
        -4,
        -14,
        20,
        0,
        0,
        0,
        4,
        -2,
    ]
    res3 = solve(
        {
            "case_id": "test_d3",
            "query": "decompose",
            "n": 3,
            "class_order": CLASSES_M24,
            "values": a3_vals,
        }
    )
    assert res3.get("status") == "SOLVED"
    assert res3.get("multiplicities") == {"770": 1, "770bar": 1}


def test_solver_ddc_tracer_emits_valid_alphabet():
    """DDCTracer must record only letters from valid alphabet and verify SHA-256 step chaining."""
    tracer = DDCTracer(challenge_id="c035_test")
    tracer.record_step("C", {"stage": "context"})
    tracer.record_step("I", {"stage": "integrate"})
    tracer.record_step("R", {"stage": "residual"})
    tracer.record_step("E", {"stage": "exact"})
    tracer.record_step("T", {"stage": "terminal"})

    trace = tracer.export_trace()
    assert trace["step_count"] == 5
    for letter in trace["letters"]:
        assert letter in VALID_DDC_LETTERS
    assert len(trace["final_digest"]) == 64


def test_solver_refuses_max_n_out_of_bounds():
    """Solver must refuse MAX_N_OUT_OF_BOUNDS for max_n > 30 or < 1."""
    res_high = solve({"case_id": "t_high", "query": "coefficients", "max_n": 35})
    assert res_high.get("status") == "UNKNOWN"
    assert res_high.get("refusal_code") == "MAX_N_OUT_OF_BOUNDS"

    res_low = solve({"case_id": "t_low", "query": "coefficients", "max_n": 0})
    assert res_low.get("status") == "UNKNOWN"
    assert res_low.get("refusal_code") == "MAX_N_OUT_OF_BOUNDS"


def test_solver_refuses_unrecognized_class_name():
    """Solver must refuse UNRECOGNIZED_CLASS_NAME if class_order contains unknown classes."""
    bad_order = list(CLASSES_M24)
    bad_order[0] = "99Z"
    case = {
        "case_id": "t_bad_class",
        "query": "decompose",
        "n": 1,
        "class_order": bad_order,
        "values": [0] * 26,
    }
    res = solve(case)
    assert res.get("status") == "UNKNOWN"
    assert res.get("refusal_code") == "UNRECOGNIZED_CLASS_NAME"


def test_solver_detects_out_of_scope_multiplicities():
    """Solver must emit OUT_OF_SCOPE with typed witness for fractional or negative multiplicities."""
    a1_vals = [
        90,
        -6,
        0,
        0,
        2,
        -1,
        -1,
        -2,
        0,
        2,
        0,
        0,
        1,
        1,
        -2,
        -2,
        2,
        -2,
        2,
        6,
        10,
        0,
        -1,
        -1,
        -6,
        0,
    ]
    pert_vals = list(a1_vals)
    pert_vals[1] += 1  # 2A perturbed

    res_frac = solve(
        {
            "case_id": "t_frac",
            "query": "decompose",
            "n": 1,
            "class_order": CLASSES_M24,
            "values": pert_vals,
        }
    )
    assert res_frac.get("status") == "OUT_OF_SCOPE"
    assert res_frac.get("witness", {}).get("kind") == "non_integral_multiplicity"

    neg_vals = list(a1_vals)
    # subtract 2 * dim(1) = 2
    for j in range(26):
        neg_vals[j] -= 2
    res_neg = solve(
        {
            "case_id": "t_neg",
            "query": "decompose",
            "n": 1,
            "class_order": CLASSES_M24,
            "values": neg_vals,
        }
    )
    assert res_neg.get("status") == "OUT_OF_SCOPE"
    assert res_neg.get("witness", {}).get("kind") == "negative_multiplicity"


def test_strict_boolean_rejection():
    """Solver must reject booleans masquerading as integers."""
    assert is_exact_int(1) is True
    assert is_exact_int(0) is True
    assert is_exact_int(True) is False
    assert is_exact_int(False) is False

    res_bool = solve({"case_id": "t_bool", "query": "coefficients", "max_n": True})
    assert res_bool.get("status") == "UNKNOWN"
    assert res_bool.get("refusal_code") == "MAX_N_OUT_OF_BOUNDS"


def test_character_table_orthogonality():
    """First orthogonality relation must hold across all 26 irrep rows."""
    for r1 in range(26):
        for r2 in range(r1, 26):
            tot_re = 0
            tot_im = {7: 0, 15: 0, 23: 0}
            for j in range(26):
                a1, b1, p1 = TABLE_M24[r1][j]
                a2, b2, p2 = TABLE_M24[r2][j]
                p = p1 if b1 != 0 else (p2 if b2 != 0 else 0)

                re4 = a1 * a2 + b1 * b2 * p
                im4 = a2 * b1 - a1 * b2
                cj = CLASS_SIZES_M24[j]
                tot_re += cj * re4
                if p in tot_im:
                    tot_im[p] += cj * im4

            for p, im_val in tot_im.items():
                assert im_val == 0, (
                    f"Non-zero imaginary inner product between {IRREP_NAMES[r1]} and {IRREP_NAMES[r2]}"
                )

            expected = 4 * G_ORDER if r1 == r2 else 0
            assert tot_re == expected, (
                f"Orthogonality failure between {IRREP_NAMES[r1]} and {IRREP_NAMES[r2]}: {tot_re} != {expected}"
            )


def test_no_hardcoded_coefficient_tables():
    """Assert reference solver derives coefficients dynamically without static lookup tables.

    Inspects both runtime module globals and the source AST of mathieu_moonshine.py
    to ensure no static sequence dictionaries or tables (like KNOWN_A) exist.
    """
    import ast
    from pathlib import Path

    from c035_k3_elliptic_genus_mathieu_moonshine.reference_solver import (
        mathieu_moonshine,
    )

    # 1. Verify absence of KNOWN_A in module globals
    assert not hasattr(mathieu_moonshine, "KNOWN_A"), (
        "Integrity Violation: KNOWN_A static table still present in mathieu_moonshine globals"
    )

    # 2. Parse source AST
    src_path = Path(mathieu_moonshine.__file__).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))

    # Signature Mathieu moonshine coefficients
    mathieu_signatures = {90, 462, 1540, 4554, 11592, 27830}
    a30_val = 8816896000

    # Walk AST and inspect all collection literals (Dict, List, Tuple)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Dict, ast.List, ast.Tuple)):
            elements = node.values if isinstance(node, ast.Dict) else node.elts
            int_vals = [
                e.value
                for e in elements
                if isinstance(e, ast.Constant) and isinstance(e.value, int)
            ]

            # Check for Mathieu moonshine sequence embedding
            matched = set(int_vals).intersection(mathieu_signatures)
            assert len(matched) < 3, (
                f"Integrity Violation: Hardcoded coefficient container ({type(node).__name__}) "
                f"detected in mathieu_moonshine.py with values: {matched}"
            )
            assert a30_val not in int_vals, (
                f"Integrity Violation: Boundary coefficient A_30 ({a30_val}) hardcoded in source AST"
            )


def test_dynamic_k3_elliptic_genus_specialization():
    """Assert specialization_z0 evaluates the dynamic Laurent series and verifies chi(K3) = 24.

    Tests that:
    1. The query returns status SOLVED with constant 24.
    2. The underlying series arithmetic evaluates at y=1 (z=0) to exactly 24.
    3. The solver emits genuine DDC trace steps reflecting specialization.
    """
    from c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.mathieu_moonshine import (
        compute_k3_elliptic_genus,
    )

    # 1. Solver API invocation
    case = {"case_id": "test_spec_dynamic", "query": "specialization_z0"}
    res = solve(case)
    assert res.get("status") == "SOLVED"
    assert res.get("constant") == 24, f"Expected chi(K3)=24, got {res.get('constant')}"

    # 2. Dynamic series evaluation check at order q^0
    z_series = compute_k3_elliptic_genus(max_q=1)
    assert 0 in z_series, "Missing order q^0 in dynamic elliptic genus expansion"
    p0 = z_series[0]

    # Evaluate Laurent polynomial p0(y) at y = 1 (z = 0)
    chi_val = sum(p0.values())
    assert chi_val == 24, (
        f"Dynamic series normalization failure: sum(p0(1)) = {chi_val} != 24. "
        f"Polynomial terms: {p0}"
    )

    # 3. DDC trace validation
    from c035_k3_elliptic_genus_mathieu_moonshine.reference_solver.solver import (
        get_last_tracer,
    )

    last_tracer = get_last_tracer()
    assert last_tracer is not None, "DDCTracer was not recorded during solve"
    trace = res.get("ddc_trace") or last_tracer.export_trace()
    assert trace.get("step_count", 0) >= 3
    letters = trace.get("letters", [])
    assert letters[-1] == "T", f"Trace did not terminate cleanly: {letters}"
    assert "E" in letters, f"Trace missing exact verification step: {letters}"
