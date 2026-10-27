"""Frozen reference solver for C049: Universal Constructions in Finite Categories.
Computes limits, colimits, and decides functor adjunctions with universal witnesses.
"""

from typing import Any, Dict

from .category import FiniteCategory
from .colimits import check_adjunction, find_colimit
from .limits import find_equalizer, find_product, find_pullback, find_terminal


def solve(case: Dict[str, Any]) -> Dict[str, Any]:
    """Solve a C049 category theory challenge case."""
    case_id = case.get("case_id", "cat_unknown")
    task = case.get("task", "LIMIT")

    trace = ["C", "R"]

    # 1. Handle Adjunction Task
    if task == "ADJUNCTION":
        cat_C_data = case.get("category_C", {})
        cat_D_data = case.get("category_D", {})
        C = FiniteCategory(
            cat_C_data.get("objects", []),
            cat_C_data.get("morphisms", []),
            cat_C_data.get("comp", {}),
        )
        D = FiniteCategory(
            cat_D_data.get("objects", []),
            cat_D_data.get("morphisms", []),
            cat_D_data.get("comp", {}),
        )

        ok_C, err_C = C.validate()
        if not ok_C:
            trace.append("M")
            return {"case_id": case_id, "status": "OUT_OF_SCOPE", "witness": err_C, "trace": trace}

        ok_D, err_D = D.validate()
        if not ok_D:
            trace.append("M")
            return {"case_id": case_id, "status": "OUT_OF_SCOPE", "witness": err_D, "trace": trace}

        F_data = case.get("F", {})
        G_data = case.get("G", {})
        F_obj = F_data.get("objects", {})
        F_mor = F_data.get("morphisms", {})
        G_obj = G_data.get("objects", {})
        G_mor = G_data.get("morphisms", {})

        trace.append("I")
        res = check_adjunction(C, D, F_obj, F_mor, G_obj, G_mor)
        res["case_id"] = case_id
        trace.extend(["E", "T"])
        res["trace"] = trace
        return res

    # 2. Handle Limit / Colimit Tasks
    objects = case.get("objects", [])
    morphisms = case.get("morphisms", [])
    comp = case.get("comp", {})
    shape = case.get("shape", "product").lower()
    diagram = case.get("diagram", [])

    cat = FiniteCategory(objects, morphisms, comp)
    ok, err = cat.validate()
    if not ok:
        trace.append("M")
        return {"case_id": case_id, "status": "OUT_OF_SCOPE", "witness": err, "trace": trace}

    trace.append("I")

    if task == "LIMIT":
        if shape in ("terminal", "terminal_object"):
            term = find_terminal(cat)
            trace.extend(["E", "T"])
            if term is not None:
                return {
                    "case_id": case_id,
                    "status": "SOLVED",
                    "kind": "EXISTS",
                    "apex": term,
                    "legs": {},
                    "trace": trace,
                }
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "DOES_NOT_EXIST",
                "trace": trace,
            }

        if shape in ("product", "pair"):
            res = find_product(cat, diagram)
            trace.extend(["E", "T"])
            if res is not None:
                apex, legs = res
                return {
                    "case_id": case_id,
                    "status": "SOLVED",
                    "kind": "EXISTS",
                    "apex": apex,
                    "legs": legs,
                    "trace": trace,
                }
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "DOES_NOT_EXIST",
                "trace": trace,
            }

        if shape in ("equalizer",):
            f, g = diagram
            res = find_equalizer(cat, f, g)
            trace.extend(["E", "T"])
            if res is not None:
                apex, legs = res
                return {
                    "case_id": case_id,
                    "status": "SOLVED",
                    "kind": "EXISTS",
                    "apex": apex,
                    "legs": legs,
                    "trace": trace,
                }
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "DOES_NOT_EXIST",
                "trace": trace,
            }

        if shape in ("pullback",):
            f, g = diagram
            res = find_pullback(cat, f, g)
            trace.extend(["E", "T"])
            if res is not None:
                apex, legs = res
                return {
                    "case_id": case_id,
                    "status": "SOLVED",
                    "kind": "EXISTS",
                    "apex": apex,
                    "legs": legs,
                    "trace": trace,
                }
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "DOES_NOT_EXIST",
                "trace": trace,
            }

    if task == "COLIMIT":
        res = find_colimit(cat, shape, diagram)
        trace.extend(["E", "T"])
        if res is not None:
            apex, legs = res
            return {
                "case_id": case_id,
                "status": "SOLVED",
                "kind": "EXISTS",
                "apex": apex,
                "legs": legs,
                "trace": trace,
            }
        return {"case_id": case_id, "status": "SOLVED", "kind": "DOES_NOT_EXIST", "trace": trace}

    trace.append("T")
    return {"case_id": case_id, "status": "UNKNOWN", "code": "ENUMERATION_LIMIT", "trace": trace}
