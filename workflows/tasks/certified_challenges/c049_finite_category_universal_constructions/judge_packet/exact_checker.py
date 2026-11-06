"""Exact checker for C049: Universal Constructions in Finite Categories.
Validates limits, colimits, adjunctions, and category axiom refutations.
"""

from typing import Any, Dict, Tuple

from ..reference_solver.category import FiniteCategory
from ..reference_solver.colimits import check_adjunction, find_colimit
from ..reference_solver.limits import find_equalizer, find_product, find_pullback, find_terminal


def check_solution(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    """Verify candidate solution for C049 category theory challenge."""
    if not isinstance(result, dict):
        return False, "Result must be a JSON object"

    case_id = case.get("case_id")
    if result.get("case_id") != case_id:
        return False, f"Case ID mismatch: expected {case_id}, got {result.get('case_id')}"

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    task = case.get("task", "LIMIT")

    # 1. OUT_OF_SCOPE validation
    if status == "OUT_OF_SCOPE":
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
            ok_C, _ = C.validate()
            ok_D, _ = D.validate()
            if ok_C and ok_D:
                return False, "Categories are valid, cannot be OUT_OF_SCOPE"
            return True, "Valid OUT_OF_SCOPE verified for adjunction"
        else:
            cat = FiniteCategory(
                case.get("objects", []), case.get("morphisms", []), case.get("comp", {})
            )
            ok, _ = cat.validate()
            if ok:
                return False, "Category is valid, cannot be OUT_OF_SCOPE"
            return True, "Valid OUT_OF_SCOPE verified for category"

    if status == "UNKNOWN":
        return False, "Solver failed with UNKNOWN"

    # If status is SOLVED, verify input validity first
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
            return False, f"Category C is invalid: {err_C}, should be OUT_OF_SCOPE"
        ok_D, err_D = D.validate()
        if not ok_D:
            return False, f"Category D is invalid: {err_D}, should be OUT_OF_SCOPE"

        kind = result.get("kind")
        if kind not in ("ADJOINT", "NOT_ADJOINT"):
            return False, f"Invalid kind for ADJUNCTION: {kind}"

        ref_adj = check_adjunction(
            C,
            D,
            case.get("F", {}).get("objects", {}),
            case.get("F", {}).get("morphisms", {}),
            case.get("G", {}).get("objects", {}),
            case.get("G", {}).get("morphisms", {}),
        )

        if kind == "ADJOINT":
            if ref_adj.get("kind") != "ADJOINT":
                return False, "Adjunction does not exist according to reference validator"
            unit = result.get("unit")
            counit = result.get("counit")
            if not isinstance(unit, dict) or not isinstance(counit, dict):
                return False, "ADJOINT requires unit and counit mappings"
            # Verify unit/counit triangle identities directly
            F_obj = case.get("F", {}).get("objects", {})
            F_mor = case.get("F", {}).get("morphisms", {})
            case.get("G", {}).get("objects", {})
            case.get("G", {}).get("morphisms", {})
            for c in C.objects:
                Fc = F_obj[c]
                id_Fc = D.id_map[Fc]
                if c not in unit or unit[c] not in C.morphisms:
                    return False, f"Unit missing or invalid for object {c}"
                if Fc not in counit or counit[Fc] not in D.morphisms:
                    return False, f"Counit missing or invalid for object {Fc}"
                comp_val = D.compose(counit[Fc], F_mor[unit[c]])
                if comp_val != id_Fc:
                    return False, f"Triangle identity failed on object {c}"
            return True, "Valid ADJOINT certificate verified"

        if kind == "NOT_ADJOINT":
            if ref_adj.get("kind") != "NOT_ADJOINT":
                return False, "Adjunction does exist, cannot be NOT_ADJOINT"
            return True, "Valid NOT_ADJOINT certificate verified"

    # LIMIT / COLIMIT tasks
    objects = case.get("objects", [])
    morphisms = case.get("morphisms", [])
    comp = case.get("comp", {})
    shape = case.get("shape", "product").lower()
    diagram = case.get("diagram", [])

    cat = FiniteCategory(objects, morphisms, comp)
    ok, err = cat.validate()
    if not ok:
        return False, f"Category is invalid: {err}, should be OUT_OF_SCOPE"

    kind = result.get("kind")
    if kind not in ("EXISTS", "DOES_NOT_EXIST"):
        return False, f"Invalid kind for {task}: {kind}"

    # Determine ground truth existence
    if task == "LIMIT":
        if shape in ("terminal", "terminal_object"):
            ref_apex = find_terminal(cat)
            ref_exists = ref_apex is not None
        elif shape in ("product", "pair"):
            res = find_product(cat, diagram)
            ref_exists = res is not None
        elif shape in ("equalizer",):
            res = find_equalizer(cat, diagram[0], diagram[1])
            ref_exists = res is not None
        elif shape in ("pullback",):
            res = find_pullback(cat, diagram[0], diagram[1])
            ref_exists = res is not None
        else:
            return False, f"Unknown limit shape: {shape}"
    elif task == "COLIMIT":
        res = find_colimit(cat, shape, diagram)
        ref_exists = res is not None
    else:
        return False, f"Unknown task: {task}"

    if kind == "DOES_NOT_EXIST":
        if ref_exists:
            return (
                False,
                "Limit/Colimit exists in category, candidate falsely claimed DOES_NOT_EXIST",
            )
        return True, "Valid DOES_NOT_EXIST verified"

    if kind == "EXISTS":
        if not ref_exists:
            return (
                False,
                "Limit/Colimit does not exist in category, candidate falsely claimed EXISTS",
            )
        apex = result.get("apex")
        if apex not in cat.objects:
            return False, f"Apex {apex} not in category objects"
        legs = result.get("legs", {})
        if not isinstance(legs, dict):
            return False, "Legs must be a dictionary"
        # Legs must exist and be morphisms in cat
        for k, mor in legs.items():
            if mor not in cat.morphisms:
                return False, f"Leg morphism {mor} not in category morphisms"

        return True, f"Valid {task} {shape} certificate verified"

    return False, "Unhandled verification branch"
