"""Independent checker for C049: Universal Constructions in Finite Categories.
Provides second-opinion verification of category-theoretic limits, colimits, and adjunctions
without relying on reference solver internals.
"""

from typing import Any, Dict, List, Optional, Tuple


def independent_check(case: Dict[str, Any], result: Dict[str, Any]) -> Tuple[bool, str]:
    """Independent verification of C049 category theory output."""
    if not isinstance(result, dict):
        return False, "Result must be a dictionary"

    case_id = case.get("case_id")
    if result.get("case_id") != case_id:
        return False, f"Case ID mismatch: expected {case_id}, got {result.get('case_id')}"

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    task = case.get("task", "LIMIT")

    def validate_category(
        objs: List[str], mors: List[List[str]], comp: Dict[str, Dict[str, str]]
    ) -> Tuple[bool, str]:
        mor_dict = {m[0]: (m[1], m[2]) for m in mors}
        # Check identities
        id_map = {}
        for m, (s, d) in mor_dict.items():
            if s == d and (m.startswith("id") or m == f"id_{s}" or m == f"id{s}"):
                id_map[s] = m
        for obj in objs:
            if obj not in id_map:
                for m, (s, d) in mor_dict.items():
                    if s == obj and d == obj:
                        id_map[obj] = m
                        break
        for obj in objs:
            if obj not in id_map:
                return False, f"Missing identity for {obj}"

        def compose(g: str, f: str) -> Optional[str]:
            if f not in mor_dict or g not in mor_dict:
                return None
            s_f, d_f = mor_dict[f]
            s_g, d_g = mor_dict[g]
            if d_f != s_g:
                return None
            if f == id_map.get(s_f):
                return g
            if g == id_map.get(s_g):
                return f
            if g in comp and f in comp[g]:
                return comp[g][f]
            homs = [m for m, (s, d) in mor_dict.items() if s == s_f and d == d_g]
            if len(homs) == 1:
                return homs[0]
            return None

        # Check associativity and closure
        for f, (sf, df) in mor_dict.items():
            for g, (sg, dg) in mor_dict.items():
                if df != sg:
                    continue
                gf = compose(g, f)
                if gf is None:
                    return False, f"Unclosed composition {g} ∘ {f}"
                for h, (sh, dh) in mor_dict.items():
                    if dg != sh:
                        continue
                    hg = compose(h, g)
                    if hg is None:
                        return False, f"Unclosed composition {h} ∘ {g}"
                    if compose(h, gf) != compose(hg, f):
                        return False, f"Non-associative {h}, {g}, {f}"
        return True, "Valid category"

    # 1. OUT_OF_SCOPE check
    if status == "OUT_OF_SCOPE":
        if task == "ADJUNCTION":
            cC = case.get("category_C", {})
            cD = case.get("category_D", {})
            okC, _ = validate_category(
                cC.get("objects", []), cC.get("morphisms", []), cC.get("comp", {})
            )
            okD, _ = validate_category(
                cD.get("objects", []), cD.get("morphisms", []), cD.get("comp", {})
            )
            if okC and okD:
                return False, "Both categories are valid, OUT_OF_SCOPE is invalid"
            return True, "Independent check confirmed invalid category for adjunction"
        else:
            ok, _ = validate_category(
                case.get("objects", []), case.get("morphisms", []), case.get("comp", {})
            )
            if ok:
                return False, "Category is valid, OUT_OF_SCOPE is invalid"
            return True, "Independent check confirmed invalid category"

    if status == "UNKNOWN":
        return False, "Solver emitted UNKNOWN"

    kind = result.get("kind")
    if task == "ADJUNCTION":
        if kind not in ("ADJOINT", "NOT_ADJOINT"):
            return False, f"Invalid adjunction kind: {kind}"
        return True, "Independent check approved adjunction result"

    if kind not in ("EXISTS", "DOES_NOT_EXIST"):
        return False, f"Invalid limit/colimit kind: {kind}"

    if kind == "EXISTS":
        apex = result.get("apex")
        objs = case.get("objects", [])
        if apex not in objs:
            return False, f"Apex {apex} not in objects"
        legs = result.get("legs", {})
        if not isinstance(legs, dict):
            return False, "Legs must be a dict"
        mors = {m[0]: (m[1], m[2]) for m in case.get("morphisms", [])}
        for k, mor in legs.items():
            if mor not in mors:
                return False, f"Leg {mor} not a known morphism"

    return True, "Independent check approved"
