"""Exact input and scope checks shared by transport and certificate verification.

These checks validate wire shapes and witnessed scope defects; they perform no
cohomology computation. AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

from .solver import detect_challenge


def exact_fraction(value: Any) -> Fraction:
    """Accept exact rational values; JSON rational strings must be canonical."""
    if type(value) is int or type(value) is Fraction:
        return Fraction(value)
    if type(value) is not str:
        raise ValueError("Rationals must be canonical strings or exact integers, not floats/bools")
    try:
        parsed = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"Invalid rational: {value!r}") from exc
    if str(parsed) != value:
        raise ValueError(f"Noncanonical rational: {value!r}")
    return parsed


def _sequence(value: Any, label: str) -> list[Any] | tuple[Any, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be a list")
    return value


def _mapping(value: Any, label: str) -> Mapping[Any, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _identifier(value: Any) -> str:
    if type(value) not in (str, int) or not str(value) or "->" in str(value):
        raise ValueError(f"Invalid identifier: {value!r}")
    return str(value)


def _identifiers(value: Any, label: str) -> list[str]:
    result = [_identifier(item) for item in _sequence(value, label)]
    if len(set(result)) != len(result):
        raise ValueError(f"Duplicate {label}")
    return result


def exact_values(value: Any, allowed_keys: set[str], label: str) -> dict[str, Fraction]:
    """Read a sparse exact vector without ignoring unknown coordinates."""
    result: dict[str, Fraction] = {}
    for raw_key, raw_value in _mapping(value, label).items():
        if isinstance(raw_key, tuple) and len(raw_key) == 2:
            key = "->".join(_identifier(item) for item in raw_key)
        elif type(raw_key) in (str, int):
            key = str(raw_key)
        else:
            raise ValueError(f"Invalid {label} coordinate: {raw_key!r}")
        if key not in allowed_keys or key in result:
            raise ValueError(f"Unknown or duplicate {label} coordinate: {key!r}")
        result[key] = exact_fraction(raw_value)
    return result


def parse_c011_case(
    case: Mapping[str, Any],
) -> tuple[list[str], list[tuple[str, str]], dict[str, Fraction], dict[str, Fraction]]:
    """Validate C011 shapes and exact scalars, leaving scope defects observable."""
    _mapping(case, "case")
    nodes = _identifiers(case.get("nodes"), "nodes")
    edges: list[tuple[str, str]] = []
    for raw_edge in _sequence(case.get("edges"), "edges"):
        edge = _sequence(raw_edge, "edge")
        if len(edge) != 2:
            raise ValueError("Each C011 edge must have exactly two endpoints")
        edges.append((_identifier(edge[0]), _identifier(edge[1])))
    if len(set(edges)) != len(edges):
        raise ValueError("Parallel C011 edges require distinct wire coordinates")
    edge_keys = {f"{u}->{v}" for u, v in edges}
    claims = exact_values(case.get("claims", {}), edge_keys, "claims")
    weights = exact_values(case.get("weights", {}), edge_keys, "weights")
    return nodes, edges, claims, weights


def _c011_violations(case: Mapping[str, Any]) -> list[dict[str, str]]:
    nodes, edges, _claims, weights = parse_c011_case(case)
    node_set = set(nodes)
    defects: list[dict[str, str]] = []
    for u, v in edges:
        key = f"{u}->{v}"
        if u == v:
            defects.append({"edge": key, "reason": "SELF_LOOP"})
        if u not in node_set or v not in node_set:
            defects.append({"edge": key, "reason": "UNKNOWN_ENDPOINT"})
        if weights.get(key, Fraction(1)) <= 0:
            defects.append({"edge": key, "reason": "NONPOSITIVE_WEIGHT"})
    return defects


def _dimension(value: Any) -> int:
    if type(value) is int and value >= 0:
        return value
    if type(value) is str and value.isascii() and value.isdigit():
        number = int(value)
        if str(number) == value:
            return number
    raise ValueError(f"Stalk dimensions must be nonnegative exact integers: {value!r}")


def _alias(case: Mapping[str, Any], primary: str, alternate: str, default: Any) -> Any:
    if primary in case and alternate in case and case[primary] != case[alternate]:
        raise ValueError(f"Conflicting {primary}/{alternate} values")
    return case.get(primary, case.get(alternate, default))


def _c012_violations(case: Mapping[str, Any]) -> list[dict[str, str]]:
    vertices = _identifiers(case.get("vertices"), "vertices")
    vertex_set = set(vertices)
    edges: list[tuple[str, str, str]] = []
    edge_ids: set[str] = set()
    for raw in _sequence(case.get("edges"), "edges"):
        if isinstance(raw, Mapping):
            u, v = _identifier(raw.get("tail")), _identifier(raw.get("head"))
            edge_id = _identifier(raw["id"]) if "id" in raw else f"{u}->{v}"
        else:
            parts = _sequence(raw, "edge")
            if len(parts) == 2:
                u, v = _identifier(parts[0]), _identifier(parts[1])
                edge_id = f"{u}->{v}"
            elif len(parts) == 3:
                edge_id, u, v = map(_identifier, parts)
            else:
                raise ValueError("Each C012 edge must have two endpoints and an optional id")
        if edge_id in edge_ids or u not in vertex_set or v not in vertex_set:
            raise ValueError("Duplicate edge id or unknown endpoint in C012")
        edge_ids.add(edge_id)
        edges.append((edge_id, u, v))

    dims_v_raw = _mapping(_alias(case, "stalk_dims_v", "vertex_stalk_dims", {}), "vertex dimensions")
    dims_e_raw = _mapping(_alias(case, "stalk_dims_e", "edge_stalk_dims", {}), "edge dimensions")
    dims_v = {str(k): _dimension(v) for k, v in dims_v_raw.items()}
    dims_e = {str(k): _dimension(v) for k, v in dims_e_raw.items()}
    if set(dims_v) - vertex_set or set(dims_e) - edge_ids:
        raise ValueError("Stalk dimensions reference unknown vertices or edges")
    restrictions = _mapping(_alias(case, "restrictions", "restriction_maps", {}), "restrictions")
    defects: list[dict[str, str]] = []
    for edge_id, u, v in edges:
        d_e = dims_e.get(edge_id, 1)
        for vertex in (u, v):
            entries = [restrictions[key] for key in (f"{vertex}<={edge_id}", f"{vertex}<= {edge_id}", (vertex, edge_id)) if key in restrictions]
            if edge_id in restrictions:
                nested = _mapping(restrictions[edge_id], "nested restrictions")
                if vertex in nested:
                    entries.append(nested[vertex])
            if entries and any(entry != entries[0] for entry in entries[1:]):
                raise ValueError("Conflicting restriction map aliases")
            if not entries or entries[0] is None:
                defects.append({"edge": edge_id, "reason": "MISSING_RESTRICTION_MAP"})
                continue
            matrix = _sequence(entries[0], "restriction matrix")
            rows = [_sequence(row, "restriction row") for row in matrix]
            for row in rows:
                for scalar in row:
                    exact_fraction(scalar)
            if len(rows) != d_e or any(len(row) != dims_v.get(vertex, 1) for row in rows):
                defects.append({"edge": edge_id, "reason": "RESTRICTION_SHAPE_MISMATCH"})

    targets = _sequence(_alias(case, "targets", "target_cochains", []), "targets")
    dim_c1 = sum(dims_e.get(edge_id, 1) for edge_id, _, _ in edges)
    for target in targets:
        coordinates = _sequence(target, "target")
        if len(coordinates) != dim_c1:
            raise ValueError("Target cochain has the wrong dimension")
        for scalar in coordinates:
            exact_fraction(scalar)
    return defects


def scope_violations(case: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return independently witnessed C011/C012 defects, or reject malformed input."""
    _mapping(case, "case")
    cid = detect_challenge(case)
    if cid == "c011":
        return _c011_violations(case)
    if cid == "c012":
        return _c012_violations(case)
    raise ValueError(f"Scope verification unavailable for {cid}")


def scope_violation(case: Mapping[str, Any]) -> dict[str, str] | None:
    """Return the first supported defect for an adapter's refusal, if any."""
    defects = scope_violations(case)
    return defects[0] if defects else None
