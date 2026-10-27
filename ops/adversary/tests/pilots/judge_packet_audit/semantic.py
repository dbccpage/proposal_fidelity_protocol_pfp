"""Semantic mutants for three packages.

Each mutant is built from a case and the package's reference answer for it,
with a declared expected verdict:

- C017 (lattice holonomy): a NOT_FLAT certificate reported from another
  start vertex or in the opposite orientation of the same plaquette, with the
  holonomy recomputed from the case's group table along the new order, and a
  PURE_GAUGE certificate with every gauge value left-multiplied by one fixed
  group element. Both are valid certificates: expected ACCEPT.
- C022 (stabilizer code distance): the reference logical operator multiplied
  by stabilizer generators. A product of the same weight d is another valid
  minimum-weight logical (expected ACCEPT); a product of larger weight w with
  the distance claimed as w is self-consistent but not minimal (expected
  REJECT). The ``lower_bound`` field is copied from the reference answer.
- W10 (evaluation preorders): the zero potential with every derived field
  recomputed from it (Phi_1 as the L1 norm of the cochain, the class,
  removability and r_cl). Where the zero potential is not optimal this is a
  consistent but non-minimal answer: expected REJECT.

A builder returns None for a case where the mutant does not apply.
"""

from __future__ import annotations

import copy
from fractions import Fraction
from itertools import combinations
from typing import Any, Callable

ACCEPT = "ACCEPT"
REJECT = "REJECT"


def _frac_text(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _parse(value: Any) -> Fraction | None:
    if type(value) is int:
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError):
            return None
    return None


def _walk(
    path: list[str], edges: dict[str, Any], table: dict[str, Any], identity: str
) -> str | None:
    value = identity
    for u, v in zip(path, path[1:]):
        elem = edges.get(f"{u}->{v}")
        row = table.get(value) if isinstance(table, dict) else None
        if elem is None or not isinstance(row, dict) or elem not in row:
            return None
        value = row[elem]
    return value


def c017_rotated_plaquette(case: Any, ref: Any) -> Any:
    return _c017_plaquette(case, ref, reverse=False)


def c017_reversed_plaquette(case: Any, ref: Any) -> Any:
    return _c017_plaquette(case, ref, reverse=True)


def _c017_plaquette(case: Any, ref: Any, *, reverse: bool) -> Any:
    if not (isinstance(ref, dict) and ref.get("verdict") == "NOT_FLAT" and isinstance(case, dict)):
        return None
    plaq = ref.get("plaquette")
    group = case.get("group")
    edges = case.get("edges")
    if not (
        isinstance(plaq, list)
        and len(plaq) == 4
        and isinstance(group, dict)
        and isinstance(edges, dict)
    ):
        return None
    order = plaq[::-1] if reverse else plaq[1:] + plaq[:1]
    identity = group.get("identity", "e")
    holonomy = _walk(order + [order[0]], edges, group.get("table", {}), identity)
    if holonomy is None or holonomy == identity:
        return None
    answer = copy.deepcopy(ref)
    answer["plaquette"] = order
    answer["holonomy"] = holonomy
    return answer


def c017_translated_gauge(case: Any, ref: Any) -> Any:
    if not (
        isinstance(ref, dict) and ref.get("verdict") == "PURE_GAUGE" and isinstance(case, dict)
    ):
        return None
    gauge = ref.get("gauge")
    group = case.get("group")
    if not (isinstance(gauge, dict) and isinstance(group, dict)):
        return None
    identity = group.get("identity", "e")
    table = group.get("table", {})
    elements = [e for e in group.get("elements", []) if e != identity]
    if not elements or not isinstance(table, dict) or not isinstance(table.get(elements[0]), dict):
        return None
    shift = elements[0]
    answer = copy.deepcopy(ref)
    try:
        answer["gauge"] = {vertex: table[shift][value] for vertex, value in gauge.items()}
    except (KeyError, TypeError):
        return None
    return answer


_PAULI = {"I": (0, 0), "X": (1, 0), "Z": (0, 1), "Y": (1, 1)}
_WORD = {v: k for k, v in _PAULI.items()}


def _masks(word: str) -> list[tuple[int, int]] | None:
    body = word[1:] if word[:1] in ("+", "-") else word
    if any(ch not in _PAULI for ch in body):
        return None
    return [_PAULI[ch] for ch in body]


def _product(a: list[tuple[int, int]], b: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return [(x1 ^ x2, z1 ^ z2) for (x1, z1), (x2, z2) in zip(a, b)]


def _weight(masks: list[tuple[int, int]]) -> int:
    return sum(1 for m in masks if m != (0, 0))


def _c022_products(case: Any, ref: Any) -> list[tuple[int, str]]:
    if not (isinstance(ref, dict) and ref.get("status") == "SOLVED" and isinstance(case, dict)):
        return []
    logical = _masks(ref.get("logical", "")) if isinstance(ref.get("logical"), str) else None
    gens = [_masks(g) for g in case.get("generators", []) if isinstance(g, str)]
    if logical is None or not gens or any(g is None or len(g) != len(logical) for g in gens):
        return []
    out = []
    for size in (1, 2):
        for combo in combinations(range(len(gens)), size):
            masks = logical
            for i in combo:
                masks = _product(masks, gens[i])
            out.append((_weight(masks), "".join(_WORD[m] for m in masks)))
    return out


def c022_alternative_logical(case: Any, ref: Any) -> Any:
    distance = ref.get("distance") if isinstance(ref, dict) else None
    if type(distance) is not int:
        return None
    for weight, word in _c022_products(case, ref):
        if weight == distance and word != ref.get("logical"):
            answer = copy.deepcopy(ref)
            answer["logical"] = word
            return answer
    return None


def c022_overstated_distance(case: Any, ref: Any) -> Any:
    distance = ref.get("distance") if isinstance(ref, dict) else None
    if type(distance) is not int:
        return None
    heavier = sorted((w, word) for w, word in _c022_products(case, ref) if w > distance)
    if not heavier:
        return None
    weight, word = heavier[0]
    answer = copy.deepcopy(ref)
    answer["logical"] = word
    answer["distance"] = weight
    return answer


def w10_zero_potential(case: Any, ref: Any) -> Any:
    if not (isinstance(ref, dict) and ref.get("status") == "SOLVED" and isinstance(case, dict)):
        return None
    true_phi = _parse(ref.get("phi_1"))
    gamma = _parse(ref.get("gamma_2"))
    cochain = case.get("cochain")
    vertices = case.get("vertices")
    if (
        true_phi is None
        or gamma is None
        or not isinstance(cochain, list)
        or not isinstance(vertices, list)
    ):
        return None
    names, values = [], []
    for index, item in enumerate(cochain):
        raw = item[1] if isinstance(item, list) and len(item) == 2 else item
        value = _parse(raw)
        if value is None:
            return None
        names.append(item[0] if isinstance(item, list) and len(item) == 2 else f"e{index}")
        values.append(value)
    phi = sum((abs(v) for v in values), Fraction(0))
    if phi == true_phi:
        return None
    answer = copy.deepcopy(ref)
    answer["optimal_potential"] = [[v, "0/1"] for v in vertices]
    answer["phi_1"] = _frac_text(phi)
    if "residual_quotient_vector" in answer:
        answer["residual_quotient_vector"] = [[n, _frac_text(v)] for n, v in zip(names, values)]
    answer["is_gauge_removable"] = phi == 0
    if phi == 0 and gamma == 0:
        answer["three_way_class"] = "REMOVABLE_GAUGE"
    elif gamma == 0:
        answer["three_way_class"] = "CLOSED_OBSTRUCTION"
    else:
        answer["three_way_class"] = "NON_CLOSED_RUPTURE"
    if "r_cl" in answer:
        if phi > 0:
            answer["r_cl"] = _frac_text(gamma / phi)
        elif gamma == 0:
            answer["r_cl"] = "0/1"
        else:
            answer["r_cl"] = "INFINITY"
    return answer


Builder = Callable[[Any, Any], Any]
MUTANTS: dict[str, list[tuple[str, str, Builder]]] = {
    "C017": [
        ("semantic:rotated_plaquette", ACCEPT, c017_rotated_plaquette),
        ("semantic:reversed_plaquette", ACCEPT, c017_reversed_plaquette),
        ("semantic:left_translated_gauge", ACCEPT, c017_translated_gauge),
    ],
    "C022": [
        ("semantic:alternative_min_weight_logical", ACCEPT, c022_alternative_logical),
        ("semantic:overstated_distance", REJECT, c022_overstated_distance),
    ],
    "W10": [("semantic:zero_potential_non_minimal", REJECT, w10_zero_potential)],
}


def semantic_strategies(
    package_id: str, cases: list[Any], references: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Per-case semantic mutants; a strategy with no applicable case is omitted."""
    out = []
    for sid, expected, build in MUTANTS.get(package_id, []):
        per_case = []
        for case, ref in zip(cases, references):
            answer = build(case, ref.get("json")) if ref.get("exact_json") else None
            per_case.append(answer)
        if any(a is not None for a in per_case):
            out.append(
                {
                    "id": sid,
                    "family": "semantic",
                    "expected": expected,
                    "template": None,
                    "per_case": per_case,
                }
            )
    return out
