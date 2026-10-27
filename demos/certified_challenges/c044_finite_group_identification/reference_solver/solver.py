# AuthorityEffect: None.
"""
Reference Solver for C044 Finite Group Identification.
Frozen module exposing `def solve(case: dict) -> dict`.
Uses standard library Python only and reads the local SmallGroups catalog.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from c044_finite_group_identification.reference_solver.algebraic_engine import (
    parse_presentation,
)
from c044_finite_group_identification.reference_solver.ddc_tracer import (
    DDCTracer,
)
from c044_finite_group_identification.reference_solver.invariants import (
    compute_all_invariants,
)
from c044_finite_group_identification.reference_solver.isomorphism_search import (
    find_isomorphism,
)

_CATALOG_CACHE: Optional[List[Dict[str, Any]]] = None


def get_catalog() -> List[Dict[str, Any]]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        cat_path = Path(__file__).resolve().parent.parent / "catalog" / "small_groups_catalog.json"
        with open(cat_path, "r", encoding="utf-8") as f:
            _CATALOG_CACHE = json.load(f)
    return _CATALOG_CACHE


def solve(case: dict) -> dict:
    case_id = case.get("case_id", "c044_unknown")
    task = case.get("task", "IDENTIFY")
    tracer = DDCTracer(case_id)
    tracer.record_step("C", f"Initialized {task} task")

    if task == "IDENTIFY":
        tracer.record_step("Lambda", "Parsing presentation and computing closure")
        ok, res = parse_presentation(case)
        if not ok:
            tracer.record_step("M", f"Out of scope: {res}")
            tracer.record_step("T", "Terminal out of scope return")
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": res,
                "ddc_trace": tracer.get_summary(),
            }

        table, gens = res
        order_g = len(table)
        tracer.record_step("I", f"Group order {order_g}, {len(gens)} generators")

        catalog = get_catalog()
        cands = [rep for rep in catalog if rep["order"] == order_g]
        if not cands:
            tracer.record_step("M", f"No catalog representatives for order {order_g}")
            tracer.record_step("T", "Terminal unknown return")
            return {
                "case_id": case_id,
                "status": "UNKNOWN",
                "code": "ORDER_NOT_IN_CATALOG",
                "ddc_trace": tracer.get_summary(),
            }

        tracer.record_step("R", f"{len(cands)} candidates of order {order_g}")
        g_invariants = compute_all_invariants(table)

        # Invariant filtering
        menu = [
            "element_order_histogram",
            "centre_order",
            "derived_subgroup_order",
            "abelianization_factors",
            "conjugacy_class_sizes",
            "solutions_xk_eq_e",
        ]
        surviving = list(cands)
        for inv_key in menu:
            val_g = g_invariants[inv_key]
            filtered = [r for r in surviving if r["invariants"].get(inv_key) == val_g]
            if len(filtered) < len(surviving):
                tracer.record_step("D", f"Pruned by {inv_key}: {len(surviving)} -> {len(filtered)}")
                surviving = filtered
            if len(surviving) <= 1:
                break

        # Search isomorphism among surviving candidates
        for rep in surviving:
            ok_iso, images, _ = find_isomorphism(table, gens, rep["table"])
            if ok_iso and images is not None:
                tracer.record_step("E", f"Isomorphism confirmed to {rep['name']} {rep['id']}")
                tracer.record_step("T", "Terminal solved return")
                return {
                    "case_id": case_id,
                    "status": "SOLVED",
                    "kind": "IDENTIFIED",
                    "rep_id": rep["id"],
                    "images": images,
                    "ddc_trace": tracer.get_summary(),
                }

        tracer.record_step("M", "No isomorphism found among surviving candidates")
        tracer.record_step("T", "Terminal search limit")
        return {
            "case_id": case_id,
            "status": "UNKNOWN",
            "code": "SEARCH_LIMIT",
            "ddc_trace": tracer.get_summary(),
        }

    elif task == "COMPARE":
        g_pres = case.get("G", {})
        h_pres = case.get("H", {})

        ok_g, res_g = parse_presentation(g_pres)
        if not ok_g:
            tracer.record_step("M", f"G out of scope: {res_g}")
            tracer.record_step("T", "Terminal out of scope return")
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": res_g,
                "ddc_trace": tracer.get_summary(),
            }

        ok_h, res_h = parse_presentation(h_pres)
        if not ok_h:
            tracer.record_step("M", f"H out of scope: {res_h}")
            tracer.record_step("T", "Terminal out of scope return")
            return {
                "case_id": case_id,
                "status": "OUT_OF_SCOPE",
                "witness": res_h,
                "ddc_trace": tracer.get_summary(),
            }

        t_g, gens_g = res_g
        t_h, gens_h = res_h

        if len(t_g) != len(t_h):
            tracer.record_step("D", "Separated by order")
            tracer.record_step("T", "Terminal not isomorphic return")
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "NOT_ISOMORPHIC",
                "invariant": "order",
                "G_value": len(t_g),
                "H_value": len(t_h),
                "ddc_trace": tracer.get_summary(),
            }

        # Check invariant menu
        inv_g = compute_all_invariants(t_g)
        inv_h = compute_all_invariants(t_h)

        menu = [
            "element_order_histogram",
            "centre_order",
            "derived_subgroup_order",
            "abelianization_factors",
            "conjugacy_class_sizes",
            "solutions_xk_eq_e",
        ]
        for inv_key in menu:
            if inv_g[inv_key] != inv_h[inv_key]:
                tracer.record_step("D", f"Separated by invariant {inv_key}")
                tracer.record_step("T", "Terminal not isomorphic return")
                return {
                    "case_id": case_id,
                    "status": "SOLVED",
                    "kind": "NOT_ISOMORPHIC",
                    "invariant": inv_key,
                    "G_value": inv_g[inv_key],
                    "H_value": inv_h[inv_key],
                    "ddc_trace": tracer.get_summary(),
                }

        # Invariants match: search for isomorphism
        tracer.record_step("I", "Invariants agree; searching isomorphism")
        ok_iso, images, _ = find_isomorphism(t_g, gens_g, t_h)
        if ok_iso and images is not None:
            tracer.record_step("E", "Bijective homomorphism certified")
            tracer.record_step("T", "Terminal isomorphic return")
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "ISOMORPHIC",
                "images": images,
                "ddc_trace": tracer.get_summary(),
            }
        else:
            tracer.record_step("D", "Exhaustive search found no isomorphism")
            tracer.record_step("T", "Terminal not isomorphic return")
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "NOT_ISOMORPHIC",
                "invariant": "conjugacy_class_sizes",
                "G_value": inv_g["conjugacy_class_sizes"],
                "H_value": inv_h["conjugacy_class_sizes"],
                "ddc_trace": tracer.get_summary(),
            }

    return {
        "case_id": case_id,
        "status": "UNKNOWN",
        "code": "INVALID_TASK",
        "ddc_trace": tracer.get_summary(),
    }
