"""Algebraic Holonomy and Flatness Checker (Checker 1) for C017.

Self-contained (no reference-solver imports); products are read from the case's
multiplication table after the table is checked to be a group.

1. UNKNOWN: accepted only when the refusal code names a bound the case violates
   (LATTICE_SIZE_OUT_OF_BOUNDS: L or M outside [2, 12]; MALFORMED_INPUT: boundary
   not open/periodic, or group/edges of the wrong type).
2. OUT_OF_SCOPE: INVALID_GROUP when the table is not a group; INVERSE_MISMATCH or
   MISSING_REVERSE_EDGE only for the cited edge, which must have that defect.
3. NOT_FLAT: the plaquette may be given in either orientation and from any start
   vertex; the reported holonomy must be the ordered product along the given order
   and must differ from the identity.
4. PURE_GAUGE: every edge u -> v satisfies g_u * U_uv * g_v^{-1} == e.
5. FLAT_NONTRIVIAL: periodic boundary, every plaquette flat, both loops closed walks
   along existing edges from `base` whose winding vectors form a basis of Z^2
   (loops A and B generate the torus), stated holonomies match, not both
   identity, and they commute.
"""

from __future__ import annotations

from typing import Any

REFUSAL_CODES = ("LATTICE_SIZE_OUT_OF_BOUNDS", "MALFORMED_INPUT")


def _refusal_conditions(case: dict[str, Any]) -> set[str]:
    codes: set[str] = set()
    L, M = case.get("L"), case.get("M")
    if type(L) is not int or type(M) is not int or not (2 <= L <= 12 and 2 <= M <= 12):
        codes.add("LATTICE_SIZE_OUT_OF_BOUNDS")
    if case.get("boundary", "open") not in ("open", "periodic"):
        codes.add("MALFORMED_INPUT")
    group = case.get("group", {})
    if (
        not isinstance(group, dict)
        or not isinstance(group.get("elements", []), list)
        or not isinstance(group.get("table", {}), dict)
        or not isinstance(group.get("inverses", {}), dict)
    ):
        codes.add("MALFORMED_INPUT")
    edges = case.get("edges", {})
    if not isinstance(edges, dict) or any(type(k) is not str or k.count("->") != 1 for k in edges):
        codes.add("MALFORMED_INPUT")
    elif isinstance(group, dict) and isinstance(group.get("elements", []), list):
        if any(type(v) is not str or v not in group.get("elements", []) for v in edges.values()):
            codes.add("MALFORMED_INPUT")
    return codes


def _group_is_valid(
    elements: list[Any], table: dict[str, Any], inverses: dict[str, Any], identity: Any
) -> bool:
    if identity not in table or identity not in elements or len(set(elements)) != len(elements):
        return False
    for a in elements:
        row = table.get(a)
        if not isinstance(row, dict) or any(row.get(b) not in elements for b in elements):
            return False
        if row[identity] != a or table[identity][a] != a:
            return False
        if inverses.get(a) not in elements or row[inverses[a]] != identity:
            return False
    return all(
        table[table[a][b]][c] == table[a][table[b][c]]
        for a in elements
        for b in elements
        for c in elements
    )


def _canonical_plaquettes(L: int, M: int, boundary: str) -> list[list[str]]:
    rows = L if boundary == "periodic" else L - 1
    cols = M if boundary == "periodic" else M - 1
    out = []
    for r in range(rows):
        for c in range(cols):
            r1, c1 = (r + 1) % L, (c + 1) % M
            out.append([f"{r},{c}", f"{r1},{c}", f"{r1},{c1}", f"{r},{c1}"])
    return out


def _same_loop_any_orientation(candidate: list[Any], canonical: list[str]) -> bool:
    n = len(canonical)
    if len(candidate) != n:
        return False
    for seq in (canonical, canonical[::-1]):
        for shift in range(n):
            if all(candidate[i] == seq[(i + shift) % n] for i in range(n)):
                return True
    return False


def _walk_product(
    path: list[Any], edges: dict[str, Any], table: dict[str, Any], identity: str
) -> str | None:
    value = identity
    for u, v in zip(path, path[1:]):
        if type(u) is not str or type(v) is not str:
            return None
        elem = edges.get(f"{u}->{v}")
        if elem is None:
            return None
        value = table[value][elem]
    return value


def _winding(loop: list[Any], L: int, M: int) -> tuple[int, int] | None:
    """Net (row, column) windings of a closed nearest-neighbour walk on the torus."""
    dr = dc = 0
    for u, v in zip(loop, loop[1:]):
        try:
            r1, c1 = (int(x) for x in str(u).split(","))
            r2, c2 = (int(x) for x in str(v).split(","))
        except ValueError:
            return None
        if c1 == c2 and r2 == (r1 + 1) % L:
            dr += 1
        elif c1 == c2 and r2 == (r1 - 1) % L:
            dr -= 1
        elif r1 == r2 and c2 == (c1 + 1) % M:
            dc += 1
        elif r1 == r2 and c2 == (c1 - 1) % M:
            dc -= 1
        else:
            return None
    if dr % L or dc % M:
        return None
    return dr // L, dc // M


def check_algebraic_holonomy_certificate(
    case: dict[str, Any], result: dict[str, Any]
) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"

    status = result.get("status")
    refusable = _refusal_conditions(case)
    if status == "UNKNOWN":
        codes = [result[k] for k in ("refusal", "refusal_code") if k in result]
        if not codes or len(set(codes)) != 1 or codes[0] not in REFUSAL_CODES:
            return False, f"UNKNOWN needs one refusal code from {REFUSAL_CODES}, got {codes!r}"
        if codes[0] not in refusable:
            return (
                False,
                f"Refusal {codes[0]} does not hold for this case (conditions: {sorted(refusable) or 'none'})",
            )
        return True, "Valid refusal for an out-of-bounds case"
    if refusable:
        return False, f"Case violates declared bounds {sorted(refusable)}; UNKNOWN expected"

    edges = case.get("edges", {})
    group = case.get("group", {})
    table = group.get("table", {})
    inverses = group.get("inverses", {})
    elements = group.get("elements", [])
    identity = group.get("identity", "e")
    L, M = case["L"], case["M"]
    boundary = case.get("boundary", "open")

    if not _group_is_valid(elements, table, inverses, identity):
        if status != "OUT_OF_SCOPE":
            return False, "Expected OUT_OF_SCOPE due to invalid group"
        witness = result.get("witness") if isinstance(result.get("witness"), dict) else {}
        if witness.get("reason") != "INVALID_GROUP":
            return False, "Witness missing INVALID_GROUP reason"
        return True, "Valid OUT_OF_SCOPE witness verified for invalid group"

    defects: dict[str, str] = {}
    for key, elem in edges.items():
        u, v = key.split("->", 1)
        rev = f"{v}->{u}"
        if rev not in edges:
            defects[key] = "MISSING_REVERSE_EDGE"
        elif edges[rev] != inverses.get(elem):
            defects[key] = "INVERSE_MISMATCH"

    if defects:
        if status != "OUT_OF_SCOPE":
            return False, "Expected OUT_OF_SCOPE due to inverse mismatch"
        witness = result.get("witness") if isinstance(result.get("witness"), dict) else {}
        cited = witness.get("edge")
        if type(cited) is not str or defects.get(cited) != witness.get("reason"):
            return False, f"Witness {witness!r} does not cite an edge with the stated defect"
        return True, "Valid OUT_OF_SCOPE witness verified"

    if status != "SOLVED":
        return False, f"Unexpected result status: {status}"

    verdict = result.get("verdict")
    plaquettes = _canonical_plaquettes(L, M, boundary)

    if verdict == "NOT_FLAT":
        plaq = result.get("plaquette")
        claimed = result.get("holonomy")
        if not isinstance(plaq, list) or len(plaq) != 4:
            return False, "plaquette must be a 4-element list of vertex strings"
        if not any(_same_loop_any_orientation(plaq, p) for p in plaquettes):
            return (
                False,
                f"Reported plaquette {plaq} is not an elementary plaquette in any orientation",
            )
        actual = _walk_product(plaq + [plaq[0]], edges, table, identity)
        if actual is None or actual != claimed:
            return False, f"Plaquette holonomy mismatch: reported {claimed}, computed {actual}"
        if actual == identity:
            return False, "Reported plaquette is actually flat (holonomy == e)"
        return True, "NOT_FLAT certificate verified"

    if verdict == "PURE_GAUGE":
        gauge = result.get("gauge")
        if not isinstance(gauge, dict):
            return False, "gauge must be a dict mapping vertex -> group element"
        for key, elem in edges.items():
            u, v = key.split("->", 1)
            g_u, g_v = gauge.get(u), gauge.get(v)
            if g_u not in elements or g_v not in elements:
                return False, f"Gauge value missing or not a group element at {u} or {v}"
            if table[table[g_u][elem]][inverses[g_v]] != identity:
                return False, f"Edge {key} not trivialized by gauge"
        return True, "PURE_GAUGE certificate verified"

    if verdict == "FLAT_NONTRIVIAL":
        if boundary != "periodic":
            return False, "FLAT_NONTRIVIAL is only possible on periodic boundaries"
        for p in plaquettes:
            if _walk_product(p + [p[0]], edges, table, identity) != identity:
                return False, f"FLAT_NONTRIVIAL claimed but plaquette {p} is not flat"
        base = result.get("base")
        holonomies = []
        windings: list[tuple[int, int] | None] = []
        for name in ("a", "b"):
            loop = result.get(f"loop_{name}")
            if not isinstance(loop, list) or len(loop) < 2 or loop[0] != loop[-1]:
                return False, f"loop_{name} must be a closed vertex walk"
            if base is not None and loop[0] != base:
                return False, f"loop_{name} does not start at base {base!r}"
            actual = _walk_product(loop, edges, table, identity)
            if actual is None or actual != result.get(f"hol_{name}"):
                return False, f"Loop {name.upper()} holonomy mismatch: computed {actual}"
            holonomies.append(actual)
            windings.append(_winding(loop, L, M))
        if (
            None in windings
            or abs(windings[0][0] * windings[1][1] - windings[0][1] * windings[1][0]) != 1
        ):
            return (
                False,
                f"loops A and B must be noncontractible generators of the torus (windings {windings})",
            )
        hol_a, hol_b = holonomies
        if hol_a == identity and hol_b == identity:
            return False, "Both global holonomies are trivial (connection is pure gauge)"
        if table[hol_a][hol_b] != table[hol_b][hol_a]:
            return False, "Global holonomies do not commute on torus"
        return True, "FLAT_NONTRIVIAL certificate verified"

    return False, f"Unknown verdict: {verdict}"
