"""Colimits and Adjunctions in finite categories for C049."""

from typing import Any, Dict, Optional, Tuple

from .category import FiniteCategory
from .limits import find_equalizer, find_product, find_pullback, find_terminal


def find_colimit(
    cat: FiniteCategory, shape: str, diagram: Any
) -> Optional[Tuple[str, Dict[str, str]]]:
    """Compute colimit by taking the dual limit in C^op."""
    op_cat = cat.opposite()

    if shape in ("initial", "initial_object"):
        init_obj = find_terminal(op_cat)
        if init_obj is not None:
            return init_obj, {}
        return None

    if shape in ("coproduct", "sum"):
        res = find_product(op_cat, diagram)
        if res is not None:
            apex, legs = res
            return apex, legs
        return None

    if shape in ("coequalizer",):
        f, g = diagram
        res = find_equalizer(op_cat, f, g)
        if res is not None:
            apex, legs = res
            return apex, legs
        return None

    if shape in ("pushout",):
        f, g = diagram
        res = find_pullback(op_cat, f, g)
        if res is not None:
            apex, legs = res
            return apex, legs
        return None

    return None


def check_adjunction(
    cat_C: FiniteCategory,
    cat_D: FiniteCategory,
    F_obj: Dict[str, str],
    F_mor: Dict[str, str],
    G_obj: Dict[str, str],
    G_mor: Dict[str, str],
) -> Dict[str, Any]:
    """Decide whether F ⊣ G forms an adjoint pair between C and D."""
    # 1. Hom-set cardinality bijection check: |D(Fc, d)| == |C(c, Gd)|
    for c in cat_C.objects:
        Fc = F_obj[c]
        for d in cat_D.objects:
            Gd = G_obj[d]
            hom_D = cat_D.hom_set(Fc, d)
            hom_C = cat_C.hom_set(c, Gd)
            if len(hom_D) != len(hom_C):
                return {
                    "status": "SOLVED",
                    "kind": "NOT_ADJOINT",
                    "witness": {
                        "type": "HOM_CARDINALITY",
                        "c": c,
                        "d": d,
                        "lhs": len(hom_D),
                        "rhs": len(hom_C),
                    },
                }

    # 2. Search for valid unit η: 1_C => GF and counit ε: FG => 1_D
    # η_c in Hom_C(c, G(F(c)))
    # ε_d in Hom_D(F(G(d)), d)
    import itertools

    eta_candidates = [cat_C.hom_set(c, G_obj[F_obj[c]]) for c in cat_C.objects]
    eps_candidates = [cat_D.hom_set(F_obj[G_obj[d]], d) for d in cat_D.objects]

    if any(len(cands) == 0 for cands in eta_candidates) or any(
        len(cands) == 0 for cands in eps_candidates
    ):
        return {"status": "SOLVED", "kind": "NOT_ADJOINT", "witness": {"type": "NO_UNIT_OR_COUNIT"}}

    for eta_tuple in itertools.product(*eta_candidates):
        eta = {c: m for c, m in zip(cat_C.objects, eta_tuple)}
        # Check naturality of η: for f: c -> c', η_c' ∘ f == GF(f) ∘ η_c
        eta_natural = True
        for f, (src, dst) in cat_C.morphisms.items():
            GF_f = G_mor[F_mor[f]]
            left = cat_C.compose(eta[dst], f)
            right = cat_C.compose(GF_f, eta[src])
            if left != right:
                eta_natural = False
                break
        if not eta_natural:
            continue

        for eps_tuple in itertools.product(*eps_candidates):
            eps = {d: m for d, m in zip(cat_D.objects, eps_tuple)}
            # Check naturality of ε: for g: d -> d', g ∘ ε_d == ε_d' ∘ FG(g)
            eps_natural = True
            for g, (src, dst) in cat_D.morphisms.items():
                FG_g = F_mor[G_mor[g]]
                left = cat_D.compose(g, eps[src])
                right = cat_D.compose(eps[dst], FG_g)
                if left != right:
                    eps_natural = False
                    break
            if not eps_natural:
                continue

            # Check triangle identities:
            # 1. ε_Fc ∘ F(η_c) == id_Fc for all c in C
            # 2. G(ε_d) ∘ η_Gd == id_Gd for all d in D
            triangles_ok = True
            for c in cat_C.objects:
                Fc = F_obj[c]
                id_Fc = cat_D.id_map[Fc]
                comp_val = cat_D.compose(eps[Fc], F_mor[eta[c]])
                if comp_val != id_Fc:
                    triangles_ok = False
                    break
            if not triangles_ok:
                continue

            for d in cat_D.objects:
                Gd = G_obj[d]
                id_Gd = cat_C.id_map[Gd]
                comp_val = cat_C.compose(G_mor[eps[d]], eta[Gd])
                if comp_val != id_Gd:
                    triangles_ok = False
                    break

            if triangles_ok:
                return {"status": "SOLVED", "kind": "ADJOINT", "unit": eta, "counit": eps}

    return {
        "status": "SOLVED",
        "kind": "NOT_ADJOINT",
        "witness": {"type": "TRIANGLE_IDENTITIES_FAILED"},
    }
