"""Judge-side case model for C014 (no reference-solver imports).

Parses a judge case into exact rational matrices, decides which refusal codes
the case genuinely admits under TASK.md section 2, and parses candidate
rationals strictly (canonical strings or plain ints; floats and booleans are
rejected).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

CLOSED_REFUSAL_ENUM = frozenset(
    {
        "VERTEX_COUNT_OUT_OF_BOUNDS",
        "EDGE_COUNT_OUT_OF_BOUNDS",
        "FACE_COUNT_OUT_OF_BOUNDS",
        "COEFFICIENT_BOUND_EXCEEDED",
        "WEIGHT_DENOMINATOR_EXCEEDED",
        "WEIGHT_NON_POSITIVE",
        "MALFORMED_INPUT",
        "MALFORMED_CASE_STRUCTURE",
        "BUDGET_EXHAUSTED",
    }
)

MAX_VERTICES = 80
MAX_EDGES = 200
MAX_FACES = 150
MAX_FLOW_PART = 999
MAX_WEIGHT_DENOMINATOR = 12

_CASE_RATIONAL = re.compile(r"-?[0-9]+(/[0-9]+)?")
_CANONICAL_RATIONAL = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?")
_CANONICAL_NATURAL = re.compile(r"0|[1-9][0-9]*")


class CaseParseError(ValueError):
    """The judge case does not describe a well-formed complex."""


def parse_case_rational(value: Any) -> Fraction:
    """Parse a rational from judge case data (int or 'p' / 'p/q' string)."""
    if type(value) is int:
        return Fraction(value, 1)
    if type(value) is str and _CASE_RATIONAL.fullmatch(value):
        num, _, den = value.partition("/")
        if den and int(den) == 0:
            raise CaseParseError(f"zero denominator in {value!r}")
        return Fraction(int(num), int(den) if den else 1)
    raise CaseParseError(f"not an exact rational: {value!r}")


def parse_answer_rational(value: Any) -> Fraction:
    """Parse a candidate rational: a plain int or a canonical 'p' / 'p/q' string."""
    if type(value) is int:
        return Fraction(value, 1)
    if type(value) is str and _CANONICAL_RATIONAL.fullmatch(value) and value != "-0":
        num, _, den = value.partition("/")
        frac = Fraction(int(num), int(den) if den else 1)
        if den and (frac.denominator != int(den) or frac.denominator == 1):
            raise ValueError(f"rational {value!r} is not in lowest terms")
        return frac
    raise ValueError(f"not a canonical exact rational: {value!r}")


def parse_answer_natural(value: Any) -> int:
    """Parse a non-negative integer given as a plain int or canonical string."""
    if type(value) is int and value >= 0:
        return value
    if type(value) is str and _CANONICAL_NATURAL.fullmatch(value):
        return int(value)
    raise ValueError(f"not a canonical non-negative integer: {value!r}")


def mat_mul(
    a: Sequence[Sequence[Fraction]], b: Sequence[Sequence[Fraction]], inner: int, cols: int
) -> list[list[Fraction]]:
    out = [[Fraction(0) for _ in range(cols)] for _ in range(len(a))]
    for i, row in enumerate(a):
        for k in range(inner):
            if row[k]:
                brow = b[k]
                for j in range(cols):
                    if brow[j]:
                        out[i][j] += row[k] * brow[j]
    return out


def mat_vec(a: Sequence[Sequence[Fraction]], x: Sequence[Fraction]) -> list[Fraction]:
    return [
        sum((row[j] * x[j] for j in range(len(x)) if row[j] and x[j]), Fraction(0)) for row in a
    ]


def transpose(a: Sequence[Sequence[Fraction]], cols: int) -> list[list[Fraction]]:
    return [[a[r][c] for r in range(len(a))] for c in range(cols)]


def rank(rows: Sequence[Sequence[Fraction]], cols: int) -> int:
    work = [list(r) for r in rows]
    rk = 0
    for c in range(cols):
        pivot = next((i for i in range(rk, len(work)) if work[i][c] != 0), None)
        if pivot is None:
            continue
        work[rk], work[pivot] = work[pivot], work[rk]
        pv = work[rk][c]
        for i in range(len(work)):
            if i != rk and work[i][c] != 0:
                f = work[i][c] / pv
                work[i] = [work[i][j] - f * work[rk][j] for j in range(cols)]
        rk += 1
        if rk == len(work):
            break
    return rk


def _edge_rows(
    case: Mapping[str, Any], raw_edges: list[Any], vert_idx: dict[str, int]
) -> tuple[list[str], list[list[Fraction]]]:
    n_v = len(vert_idx)
    explicit = case.get("d0") if case.get("d0") is not None else case.get("delta0")
    if explicit is not None:
        if isinstance(explicit, list):
            edges = [e if type(e) is str else f"e{i}" for i, e in enumerate(raw_edges)]
            if len(explicit) != len(edges):
                raise CaseParseError("delta0 row count differs from |E|")
            rows = []
            for row in explicit:
                if not isinstance(row, list) or len(row) != n_v:
                    raise CaseParseError("delta0 row length differs from |V|")
                rows.append([parse_case_rational(x) for x in row])
            return edges, rows
        if isinstance(explicit, dict):
            edges = [str(e) for e in raw_edges]
            rows = [[Fraction(0) for _ in range(n_v)] for _ in edges]
            for i, e in enumerate(edges):
                entry = explicit.get(e, {})
                if not isinstance(entry, dict):
                    raise CaseParseError(f"delta0 entry for {e} is not an object")
                for v, val in entry.items():
                    if v not in vert_idx:
                        raise CaseParseError(f"delta0 cites unknown vertex {v!r}")
                    rows[i][vert_idx[v]] = parse_case_rational(val)
            return edges, rows
        raise CaseParseError("delta0 must be a list or an object")
    endpoints_map = case.get("edge_endpoints", {})
    if not isinstance(endpoints_map, dict):
        raise CaseParseError("edge_endpoints must be an object")
    edges: list[str] = []
    rows: list[list[Fraction]] = []
    for idx, e in enumerate(raw_edges):
        if isinstance(e, dict):
            e_id = str(e.get("id", f"e{idx}"))
            u, v = e.get("u", e.get("tail")), e.get("v", e.get("head"))
        elif isinstance(e, list) and len(e) == 2:
            u, v = e[0], e[1]
            e_id = f"e_{u}_{v}"
        elif isinstance(e, list) and len(e) == 3:
            e_id, u, v = str(e[0]), e[1], e[2]
        elif type(e) is str:
            ends = endpoints_map.get(e)
            if not isinstance(ends, list) or len(ends) != 2:
                raise CaseParseError(f"missing endpoints for edge {e!r}")
            e_id, (u, v) = e, ends
        else:
            raise CaseParseError(f"invalid edge entry {e!r}")
        u, v = str(u), str(v)
        if u not in vert_idx or v not in vert_idx:
            raise CaseParseError(f"edge {e_id} cites unknown vertex {u!r} or {v!r}")
        row = [Fraction(0) for _ in range(n_v)]
        row[vert_idx[u]] -= 1
        row[vert_idx[v]] += 1
        edges.append(e_id)
        rows.append(row)
    return edges, rows


def _face_rows(
    case: Mapping[str, Any], raw_faces: list[Any], faces: list[str], edge_idx: dict[str, int]
) -> list[list[Fraction]]:
    n_e = len(edge_idx)
    explicit = case.get("d1") if case.get("d1") is not None else case.get("delta1")
    rows = [[Fraction(0) for _ in range(n_e)] for _ in faces]

    def put(f_pos: int, e_id: Any, val: Any) -> None:
        key = str(e_id)
        if key not in edge_idx:
            raise CaseParseError(f"face boundary cites unknown edge {key!r}")
        rows[f_pos][edge_idx[key]] = parse_case_rational(val)

    if explicit is not None:
        if isinstance(explicit, list):
            if len(explicit) != len(faces):
                raise CaseParseError("delta1 row count differs from |F|")
            out = []
            for row in explicit:
                if not isinstance(row, list) or len(row) != n_e:
                    raise CaseParseError("delta1 row length differs from |E|")
                out.append([parse_case_rational(x) for x in row])
            return out
        if isinstance(explicit, dict):
            for i, f in enumerate(faces):
                entry = explicit.get(f, {})
                if not isinstance(entry, dict):
                    raise CaseParseError(f"delta1 entry for {f} is not an object")
                for e_id, val in entry.items():
                    put(i, e_id, val)
            return rows
        raise CaseParseError("delta1 must be a list or an object")
    boundaries = case.get("face_boundaries", {})
    if not isinstance(boundaries, dict):
        raise CaseParseError("face_boundaries must be an object")
    for i, f_raw in enumerate(raw_faces):
        if isinstance(f_raw, dict):
            bnd = f_raw.get("edges", f_raw.get("boundary", {}))
        else:
            bnd = boundaries.get(str(f_raw), {})
        if isinstance(bnd, dict):
            for e_id, val in bnd.items():
                put(i, e_id, val)
        elif isinstance(bnd, list):
            for item in bnd:
                if isinstance(item, list) and len(item) == 2:
                    put(i, item[0], item[1])
                elif type(item) is str:
                    put(i, item, 1)
                else:
                    raise CaseParseError(f"invalid face boundary item {item!r}")
        else:
            raise CaseParseError(f"invalid boundary for face {f_raw!r}")
    return rows


def parse_complex(case: Any) -> dict[str, Any]:
    """Return the exact complex; raise CaseParseError when the case is malformed."""
    if not isinstance(case, Mapping):
        raise CaseParseError("case is not an object")
    raw_verts, raw_edges, raw_faces = case.get("vertices"), case.get("edges"), case.get("faces", [])
    if (
        not isinstance(raw_verts, list)
        or not isinstance(raw_edges, list)
        or not isinstance(raw_faces, list)
    ):
        raise CaseParseError("vertices, edges and faces must be lists")
    vertices = [str(v) for v in raw_verts]
    faces = [
        str(f.get("id", f"f{i}")) if isinstance(f, dict) else str(f)
        for i, f in enumerate(raw_faces)
    ]
    if len(set(vertices)) != len(vertices) or len(set(faces)) != len(faces):
        raise CaseParseError("duplicate vertex or face identifiers")
    vert_idx = {v: i for i, v in enumerate(vertices)}
    edges, delta0 = _edge_rows(case, raw_edges, vert_idx)
    if len(set(edges)) != len(edges):
        raise CaseParseError("duplicate edge identifiers")
    edge_idx = {e: i for i, e in enumerate(edges)}
    delta1 = _face_rows(case, raw_faces, faces, edge_idx)

    def vector(key: str, default: Fraction) -> list[Fraction]:
        raw = case.get(key, {})
        if isinstance(raw, dict):
            unknown = set(raw) - set(edges)
            if unknown:
                raise CaseParseError(f"{key} cites unknown edges {sorted(unknown)}")
            return [parse_case_rational(raw[e]) if e in raw else default for e in edges]
        if isinstance(raw, list):
            if len(raw) != len(edges):
                raise CaseParseError(f"{key} list length differs from |E|")
            return [parse_case_rational(x) for x in raw]
        raise CaseParseError(f"{key} must be an object or a list")

    return {
        "vertices": vertices,
        "edges": edges,
        "faces": faces,
        "delta0": delta0,
        "delta1": delta1,
        "flow": vector("flow", Fraction(0)),
        "weights": vector("weights", Fraction(1)),
    }


def admissible_refusals(case: Any) -> frozenset[str]:
    """Refusal codes whose TASK.md condition genuinely holds on this case.

    BUDGET_EXHAUSTED is never admissible: every case within the declared bounds
    is decidable, and budget exhaustion carries no witness a judge can check.
    """
    if not isinstance(case, Mapping):
        return frozenset({"MALFORMED_CASE_STRUCTURE"})
    codes: set[str] = set()
    raw_verts, raw_edges, raw_faces = case.get("vertices"), case.get("edges"), case.get("faces", [])
    for raw, limit, code in (
        (raw_verts, MAX_VERTICES, "VERTEX_COUNT_OUT_OF_BOUNDS"),
        (raw_edges, MAX_EDGES, "EDGE_COUNT_OUT_OF_BOUNDS"),
        (raw_faces, MAX_FACES, "FACE_COUNT_OUT_OF_BOUNDS"),
    ):
        if not isinstance(raw, list):
            codes.add("MALFORMED_INPUT")
        elif len(raw) > limit:
            codes.add(code)
    try:
        comp = parse_complex(case)
    except CaseParseError:
        codes.add("MALFORMED_INPUT")
        return frozenset(codes)
    for f in comp["flow"]:
        if abs(f.numerator) > MAX_FLOW_PART or f.denominator > MAX_FLOW_PART:
            codes.add("COEFFICIENT_BOUND_EXCEEDED")
    for w in comp["weights"]:
        if w <= 0:
            codes.add("WEIGHT_NON_POSITIVE")
        elif w.denominator > MAX_WEIGHT_DENOMINATOR:
            codes.add("WEIGHT_DENOMINATOR_EXCEEDED")
    return frozenset(codes)


def check_refusal(case: Any, result: Mapping[str, Any]) -> tuple[bool, str]:
    """An UNKNOWN passes only with a closed-enum code whose condition holds on the case."""
    codes = [result[k] for k in ("refusal", "refusal_code") if k in result]
    if not codes:
        return False, "FAIL: UNKNOWN without a refusal code"
    if any(type(c) is not str for c in codes) or len(set(codes)) != 1:
        return False, f"FAIL: refusal fields disagree or are not strings: {codes!r}"
    code = codes[0]
    if code not in CLOSED_REFUSAL_ENUM:
        return False, f"FAIL: refusal {code!r} not in closed refusal enum"
    admissible = admissible_refusals(case)
    if code not in admissible:
        return False, (
            f"FAIL: refusal {code!r} is not supported by the case "
            f"(conditions that hold: {sorted(admissible) or 'none; the case is in scope'})"
        )
    return True, "VALID_REFUSAL"
