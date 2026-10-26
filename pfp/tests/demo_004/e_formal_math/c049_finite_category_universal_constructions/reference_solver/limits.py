"""Limit computations in finite categories for C049.
Finds products, equalizers, pullbacks, and terminal objects, or proves absence.
"""

from typing import Dict, List, Optional, Tuple

from .category import FiniteCategory


def find_terminal(cat: FiniteCategory) -> Optional[str]:
    """Find a terminal object T in cat, where |Hom(X, T)| = 1 for all X."""
    for T in cat.objects:
        is_term = True
        for X in cat.objects:
            if len(cat.hom_set(X, T)) != 1:
                is_term = False
                break
        if is_term:
            return T
    return None


def find_product(
    cat: FiniteCategory, diagram_objs: List[str]
) -> Optional[Tuple[str, Dict[str, str]]]:
    """Find product of diagram_objs: apex P and projection legs {c_i: p_i}.
    Verifies existence of unique mediating arrow for every competing cone.
    """
    for P in cat.objects:
        # Enumerate candidate projection tuples
        # For each target obj c in diagram_objs, pick p_c in Hom(P, c)
        hom_lists = [cat.hom_set(P, c) for c in diagram_objs]
        if any(len(h) == 0 for h in hom_lists):
            continue

        # Try combinations of legs
        import itertools

        for leg_tuple in itertools.product(*hom_lists):
            legs = {c: m for c, m in zip(diagram_objs, leg_tuple)}
            # Test universality
            is_universal = True
            for A in cat.objects:
                # Find all competing cones from A to diagram_objs
                a_homs = [cat.hom_set(A, c) for c in diagram_objs]
                if any(len(h) == 0 for h in a_homs):
                    continue
                for q_tuple in itertools.product(*a_homs):
                    # Find mediating m in Hom(A, P) such that legs[c] ∘ m = q_tuple[idx] for all c
                    mediating = []
                    for m in cat.hom_set(A, P):
                        factored = True
                        for idx, c in enumerate(diagram_objs):
                            if cat.compose(legs[c], m) != q_tuple[idx]:
                                factored = False
                                break
                        if factored:
                            mediating.append(m)
                    if len(mediating) != 1:
                        is_universal = False
                        break
                if not is_universal:
                    break

            if is_universal:
                return P, legs

    return None


def find_equalizer(cat: FiniteCategory, f: str, g: str) -> Optional[Tuple[str, Dict[str, str]]]:
    """Find equalizer of parallel pair f, g: X -> Y.
    Returns (apex E, legs {X: e}).
    """
    src_f, dst_f = cat.morphisms[f]
    X = src_f

    for E in cat.objects:
        for e in cat.hom_set(E, X):
            # Check cone commutativity: f ∘ e == g ∘ e
            fe = cat.compose(f, e)
            ge = cat.compose(g, e)
            if fe != ge:
                continue

            # Check universality: for any A and h: A -> X with f ∘ h == g ∘ h,
            # there exists unique m: A -> E with e ∘ m == h.
            is_universal = True
            for A in cat.objects:
                for h in cat.hom_set(A, X):
                    if cat.compose(f, h) != cat.compose(g, h):
                        continue
                    mediating = [m for m in cat.hom_set(A, E) if cat.compose(e, m) == h]
                    if len(mediating) != 1:
                        is_universal = False
                        break
                if not is_universal:
                    break

            if is_universal:
                return E, {X: e}

    return None


def find_pullback(cat: FiniteCategory, f: str, g: str) -> Optional[Tuple[str, Dict[str, str]]]:
    """Find pullback of cospan f: X -> Z, g: Y -> Z.
    Returns (apex P, legs {X: p1, Y: p2}) such that f ∘ p1 == g ∘ p2.
    """
    X, Z = cat.morphisms[f]
    Y, _ = cat.morphisms[g]

    for P in cat.objects:
        for p1 in cat.hom_set(P, X):
            for p2 in cat.hom_set(P, Y):
                if cat.compose(f, p1) != cat.compose(g, p2):
                    continue

                # Check universality: for any A and q1: A -> X, q2: A -> Y with f ∘ q1 == g ∘ q2,
                # there exists unique m: A -> P with p1 ∘ m == q1 and p2 ∘ m == q2.
                is_universal = True
                for A in cat.objects:
                    for q1 in cat.hom_set(A, X):
                        for q2 in cat.hom_set(A, Y):
                            if cat.compose(f, q1) != cat.compose(g, q2):
                                continue
                            mediating = [
                                m
                                for m in cat.hom_set(A, P)
                                if cat.compose(p1, m) == q1 and cat.compose(p2, m) == q2
                            ]
                            if len(mediating) != 1:
                                is_universal = False
                                break
                        if not is_universal:
                            break
                    if not is_universal:
                        break

                if is_universal:
                    return P, {X: p1, Y: p2}

    return None
