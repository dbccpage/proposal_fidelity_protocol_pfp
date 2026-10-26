# AuthorityEffect: None.
"""
Reference Solver for C045: Knot Polynomials from Planar Diagrams.
Pure Python standard library with DDC operational tracing and zero external dependencies.
"""

from typing import Any, Dict

from .alexander_poly import compute_alexander_poly
from .ddc_tracer import DDCTracer
from .kauffman_bracket import compute_kauffman_and_jones
from .knots_catalog import match_knot_in_catalog
from .pd_validator import validate_and_parse_pd


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = case.get("case_id", "unknown_case")
    task = case.get("task", "COMPUTE_POLYNOMIALS")
    tracer = DDCTracer(case_id)

    tracer.record_step("E", f"Received task {task} for case {case_id}")

    if task in {"COMPUTE_POLYNOMIALS", "IDENTIFY"}:
        pd = case.get("pd")
        if pd is None:
            tracer.record_step("R", "Missing pd parameter in input case")
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": "MALFORMED_INPUT",
                "witness": {"detail": "Missing pd field"},
                "ddc_trace": tracer.get_summary(),
            }

        # Handle unknot
        if len(pd) == 0:
            tracer.record_step("R", "Validated trivial unknot (0 crossings)")
            tracer.record_step("C", "Writhe is 0")
            tracer.record_step("Lambda", "Trivial Kauffman bracket <K> = 1")
            tracer.record_step("I", "Trivial Jones V(t) = 1")
            tracer.record_step("D", "Trivial Alexander Delta(t) = 1")
            tracer.record_step("M", "Matched unknot 0_1")
            tracer.record_step("T", "Emitted unknot result")
            if task == "IDENTIFY":
                return {
                    "case_id": case_id,
                    "status": "SOLVED",
                    "task": "IDENTIFY",
                    "identified_knot": "0_1",
                    "chirality": "ACHIRAL",
                    "invariants": {
                        "writhe": 0,
                        "jones_polynomial": {"0": 1},
                        "alexander_polynomial": {"0": 1},
                    },
                    "ddc_trace": tracer.get_summary(),
                }
            else:
                return {
                    "case_id": case_id,
                    "status": "SOLVED",
                    "task": "COMPUTE_POLYNOMIALS",
                    "identified_knot": "0_1",
                    "chirality": "ACHIRAL",
                    "writhe": 0,
                    "kauffman_bracket": {"0": 1},
                    "jones_polynomial": {"0": 1},
                    "alexander_polynomial": {"0": 1},
                    "ddc_trace": tracer.get_summary(),
                }

        ok, parse_res = validate_and_parse_pd(pd)
        if not ok:
            tracer.record_step("R", f"PD validation failed: {parse_res['reason']}", parse_res)
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": parse_res["reason"],
                "witness": parse_res,
                "ddc_trace": tracer.get_summary(),
            }

        writhe = parse_res["writhe"]
        signs = parse_res["signs"]
        tracer.record_step(
            "R", f"Planar rotation system verified (faces = {parse_res['crossings_count'] + 2})"
        )
        tracer.record_step("C", f"Computed crossing signs and total writhe = {writhe}")

        # Kauffman bracket and Jones polynomial
        tracer.record_step("Lambda", f"Executing state-sum over 2^{len(pd)} smoothings")
        bracket, jones = compute_kauffman_and_jones(pd, writhe)
        tracer.record_step("I", "Normalized Kauffman bracket to Jones polynomial V(t)")

        # Alexander polynomial
        tracer.record_step(
            "D", f"Evaluating and interpolating Alexander matrix minor of size {len(pd) - 1}"
        )
        alexander = compute_alexander_poly(pd, signs)

        # Catalog identification
        knot_id, chirality = match_knot_in_catalog(jones, alexander)
        tracer.record_step("M", f"Catalog match: {knot_id} (chirality: {chirality})")
        tracer.record_step("T", "Emitted final polynomial invariants")

        if task == "IDENTIFY":
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "task": "IDENTIFY",
                "identified_knot": knot_id,
                "chirality": chirality,
                "invariants": {
                    "writhe": writhe,
                    "jones_polynomial": jones,
                    "alexander_polynomial": alexander,
                },
                "ddc_trace": tracer.get_summary(),
            }
        else:
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "task": "COMPUTE_POLYNOMIALS",
                "writhe": writhe,
                "kauffman_bracket": bracket,
                "jones_polynomial": jones,
                "alexander_polynomial": alexander,
                "identified_knot": knot_id,
                "chirality": chirality,
                "ddc_trace": tracer.get_summary(),
            }

    elif task == "COMPARE":
        pd_1 = case.get("pd_1")
        pd_2 = case.get("pd_2")
        if pd_1 is None or pd_2 is None:
            tracer.record_step("R", "Missing pd_1 or pd_2 in COMPARE task")
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": "MALFORMED_INPUT",
                "witness": {"detail": "Missing pd_1 or pd_2"},
                "ddc_trace": tracer.get_summary(),
            }

        # Solve pd_1
        c1 = {"case_id": f"{case_id}_1", "task": "COMPUTE_POLYNOMIALS", "pd": pd_1}
        r1 = solve(c1)
        if r1["status"] != "SOLVED":
            tracer.record_step("R", f"Validation failed on pd_1: {r1['reason']}")
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": f"PD_1_{r1['reason']}",
                "witness": r1["witness"],
                "ddc_trace": tracer.get_summary(),
            }

        # Solve pd_2
        c2 = {"case_id": f"{case_id}_2", "task": "COMPUTE_POLYNOMIALS", "pd": pd_2}
        r2 = solve(c2)
        if r2["status"] != "SOLVED":
            tracer.record_step("R", f"Validation failed on pd_2: {r2['reason']}")
            return {
                "case_id": case_id,
                "status": "REFUSED",
                "reason": f"PD_2_{r2['reason']}",
                "witness": r2["witness"],
                "ddc_trace": tracer.get_summary(),
            }

        # Compare invariants
        same_jones = r1["jones_polynomial"] == r2["jones_polynomial"]
        same_alex = r1["alexander_polynomial"] == r2["alexander_polynomial"]

        if same_jones and same_alex:
            tracer.record_step("M", "Knots share identical Jones and Alexander polynomials")
            tracer.record_step("T", "Emitted SAME_INVARIANTS verdict")
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "task": "COMPARE",
                "kind": "SAME_INVARIANTS",
                "invariants": {
                    "jones_polynomial": r1["jones_polynomial"],
                    "alexander_polynomial": r1["alexander_polynomial"],
                },
                "ddc_trace": tracer.get_summary(),
            }
        else:
            sep_inv = "jones_polynomial" if not same_jones else "alexander_polynomial"
            tracer.record_step("M", f"Knots separated by invariant {sep_inv}")
            tracer.record_step("T", "Emitted DIFFERENT_INVARIANTS verdict")
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "task": "COMPARE",
                "kind": "DIFFERENT_INVARIANTS",
                "separating_invariant": sep_inv,
                "val_1": r1[sep_inv],
                "val_2": r2[sep_inv],
                "ddc_trace": tracer.get_summary(),
            }

    else:
        tracer.record_step("R", f"Unknown task: {task}")
        return {
            "case_id": case_id,
            "status": "REFUSED",
            "reason": "UNKNOWN_TASK",
            "witness": {"task": task},
            "ddc_trace": tracer.get_summary(),
        }
