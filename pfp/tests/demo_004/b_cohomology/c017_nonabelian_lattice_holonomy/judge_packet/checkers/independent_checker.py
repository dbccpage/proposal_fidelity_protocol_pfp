"""Independent Lattice Holonomy Checker (Checker 2) for C017.

Self-contained: imports neither the reference solver nor checker 1. Its group
arithmetic is its own: each element g becomes the permutation x -> g*x of the
element list (the left-regular representation, faithful by Cayley's theorem),
products are permutation compositions, and a product is read back as the image of
the identity. The checker recomputes every plaquette with this arithmetic, finds
its own spanning-tree gauge, and verifies every submitted certificate, including
the loops and holonomies of FLAT_NONTRIVIAL.
"""

from __future__ import annotations

from collections import deque
from typing import Any

Perm = tuple[int, ...]


class _Group:
    def __init__(
        self, elements: list[str], table: dict[str, dict[str, str]], identity: str
    ) -> None:
        self.names = list(elements)
        self.index = {name: i for i, name in enumerate(self.names)}
        self.perm = {g: tuple(self.index[table[g][x]] for x in self.names) for g in self.names}
        self.identity_perm: Perm = tuple(range(len(self.names)))
        self.identity = identity

    def compose(self, p: Perm, q: Perm) -> Perm:
        # (p * q)(x) = p(q(x)); left-regular images satisfy L_g L_h = L_{gh}.
        return tuple(p[q[i]] for i in range(len(q)))

    def inverse(self, p: Perm) -> Perm:
        out = [0] * len(p)
        for i, image in enumerate(p):
            out[image] = i
        return tuple(out)

    def name(self, p: Perm) -> str:
        return self.names[p[self.index[self.identity]]]


def _build_group(group: Any) -> _Group | None:
    if not isinstance(group, dict):
        return None
    elements, table, identity = (
        group.get("elements"),
        group.get("table"),
        group.get("identity", "e"),
    )
    if not isinstance(elements, list) or not isinstance(table, dict) or identity not in elements:
        return None
    if len(set(elements)) != len(elements) or any(type(x) is not str for x in elements):
        return None
    for g in elements:
        row = table.get(g)
        if (
            not isinstance(row, dict)
            or sorted(map(str, row.values())) != sorted(elements)
            or set(row) != set(elements)
        ):
            return None  # every row must be a permutation of the elements
    grp = _Group(elements, table, identity)
    if grp.perm[identity] != grp.identity_perm:
        return None
    for a in elements:  # associativity: L_a L_b == L_{ab}
        for b in elements:
            if grp.compose(grp.perm[a], grp.perm[b]) != grp.perm[table[a][b]]:
                return None
    inverses = group.get("inverses", {})
    if not isinstance(inverses, dict):
        return None
    for g in elements:
        inv = inverses.get(g)
        if inv not in grp.perm or grp.compose(grp.perm[g], grp.perm[inv]) != grp.identity_perm:
            return None
    return grp


def _lattice_ok(case: dict[str, Any]) -> tuple[bool, bool]:
    L, M = case.get("L"), case.get("M")
    size_ok = type(L) is int and type(M) is int and 2 <= L <= 12 and 2 <= M <= 12
    shape_ok = case.get("boundary", "open") in ("open", "periodic")
    group = case.get("group")
    edges = case.get("edges", {})
    shape_ok = shape_ok and isinstance(group, dict) and isinstance(group.get("elements", []), list)
    shape_ok = (
        shape_ok
        and isinstance(group.get("table", {}), dict)
        and isinstance(group.get("inverses", {}), dict)
    )
    shape_ok = shape_ok and isinstance(edges, dict)
    if shape_ok:
        elements = set(group.get("elements", []))
        for key, value in edges.items():
            if (
                type(key) is not str
                or key.count("->") != 1
                or type(value) is not str
                or value not in elements
            ):
                shape_ok = False
                break
    return size_ok, shape_ok


def _plaquette_cycles(L: int, M: int, periodic: bool) -> list[list[tuple[int, int]]]:
    cycles = []
    for r in range(L if periodic else L - 1):
        for c in range(M if periodic else M - 1):
            cycles.append([(r, c), ((r + 1) % L, c), ((r + 1) % L, (c + 1) % M), (r, (c + 1) % M)])
    return cycles


def _label(v: tuple[int, int]) -> str:
    return f"{v[0]},{v[1]}"


def _holonomy(grp: _Group, edges: dict[str, str], walk: list[Any]) -> Perm | None:
    acc = grp.identity_perm
    for u, v in zip(walk, walk[1:]):
        if type(u) is not str or type(v) is not str or f"{u}->{v}" not in edges:
            return None
        acc = grp.compose(acc, grp.perm[edges[f"{u}->{v}"]])
    return acc


def _is_plaquette(candidate: Any, cycles: list[list[tuple[int, int]]]) -> bool:
    if not isinstance(candidate, list) or len(candidate) != 4:
        return False
    labels = [[_label(v) for v in cyc] for cyc in cycles]
    for cyc in labels:
        doubled = cyc + cyc
        rev = cyc[::-1] + cyc[::-1]
        for start in range(4):
            if candidate == doubled[start : start + 4] or candidate == rev[start : start + 4]:
                return True
    return False


def _torus_winding(loop: list[Any], L: int, M: int) -> tuple[int, int] | None:
    coords = []
    for label in loop:
        parts = label.split(",") if type(label) is str else []
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            return None
        coords.append((int(parts[0]), int(parts[1])))
    steps = {((L - 1) % L, 0): (-1, 0), (0, (M - 1) % M): (0, -1)}
    steps.update({(1 % L, 0): (1, 0), (0, 1 % M): (0, 1)})  # on a 2-cycle a step counts as +1
    total_r = total_c = 0
    for (r1, c1), (r2, c2) in zip(coords, coords[1:]):
        step = steps.get(((r2 - r1) % L, (c2 - c1) % M))
        if step is None:
            return None
        total_r += step[0]
        total_c += step[1]
    if total_r % L or total_c % M:
        return None
    return total_r // L, total_c // M


def check_independent_holonomy(case: dict[str, Any], result: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a dict"
    status = result.get("status")
    size_ok, shape_ok = _lattice_ok(case)
    violations = set()
    if not size_ok:
        violations.add("LATTICE_SIZE_OUT_OF_BOUNDS")
    if not shape_ok:
        violations.add("MALFORMED_INPUT")
    if status == "UNKNOWN":
        code = result.get("refusal_code", result.get("refusal"))
        if result.get("refusal", code) != code or code not in violations:
            return False, f"Independent checker: refusal {code!r} is not supported by the case"
        return True, "Independent checker confirms the refusal"
    if violations:
        return False, "Independent checker: case is out of bounds; UNKNOWN expected"

    edges: dict[str, str] = case["edges"]
    grp = _build_group(case["group"])
    if grp is None:
        reason = (
            result.get("witness", {}).get("reason")
            if isinstance(result.get("witness"), dict)
            else None
        )
        if status == "OUT_OF_SCOPE" and reason == "INVALID_GROUP":
            return True, "Independent checker confirms INVALID_GROUP"
        return False, "Independent checker: invalid group table requires OUT_OF_SCOPE INVALID_GROUP"

    bad_edges = {}
    for key, value in edges.items():
        u, v = key.split("->")
        reverse = edges.get(f"{v}->{u}")
        if reverse is None:
            bad_edges[key] = "MISSING_REVERSE_EDGE"
        elif grp.compose(grp.perm[value], grp.perm[reverse]) != grp.identity_perm:
            bad_edges[key] = "INVERSE_MISMATCH"
    if bad_edges:
        w = result.get("witness") if isinstance(result.get("witness"), dict) else {}
        if status == "OUT_OF_SCOPE" and bad_edges.get(w.get("edge")) == w.get("reason"):
            return True, "Independent checker confirms the cited edge defect"
        return (
            False,
            "Independent checker: OUT_OF_SCOPE with a witness citing a defective edge expected",
        )
    if status != "SOLVED":
        return False, f"Expected SOLVED, got {status}"

    L, M, periodic = case["L"], case["M"], case.get("boundary", "open") == "periodic"
    cycles = _plaquette_cycles(L, M, periodic)
    curved = [
        cyc
        for cyc in cycles
        if _holonomy(grp, edges, [_label(v) for v in cyc + cyc[:1]]) != grp.identity_perm
    ]
    verdict = result.get("verdict")

    if curved:
        if verdict != "NOT_FLAT":
            return False, f"Expected NOT_FLAT, got {verdict}"
        plaq = result.get("plaquette")
        if not _is_plaquette(plaq, cycles):
            return (
                False,
                f"Reported plaquette {plaq} is not an elementary plaquette in any orientation",
            )
        hol = _holonomy(grp, edges, plaq + plaq[:1])
        if hol is None or hol == grp.identity_perm or grp.name(hol) != result.get("holonomy"):
            return False, "Independent checker: reported plaquette holonomy mismatch"
        return True, "Independent checker confirms NOT_FLAT"

    # Flat: build a BFS spanning-tree gauge g_v with U_uv = g_u^{-1} g_v on tree edges.
    vertices = [(r, c) for r in range(L) for c in range(M)]
    gauge: dict[str, Perm] = {_label(vertices[0]): grp.identity_perm}
    queue = deque([_label(vertices[0])])
    while queue:
        u = queue.popleft()
        for key, value in edges.items():
            a, b = key.split("->")
            if a == u and b not in gauge:
                gauge[b] = grp.compose(gauge[u], grp.perm[value])
                queue.append(b)
    pure = len(gauge) == len(vertices) and all(
        grp.compose(grp.compose(gauge[a], grp.perm[value]), grp.inverse(gauge[b]))
        == grp.identity_perm
        for key, value in edges.items()
        for a, b in [key.split("->")]
        if a in gauge and b in gauge
    )

    if verdict == "PURE_GAUGE":
        if not pure:
            return False, "Independent checker: connection is not pure gauge"
        submitted = result.get("gauge")
        if not isinstance(submitted, dict) or any(
            submitted.get(_label(v)) not in grp.perm for v in vertices
        ):
            return False, "Independent checker: gauge must assign a group element to every vertex"
        for key, value in edges.items():
            a, b = key.split("->")
            if a not in submitted or b not in submitted:
                return False, "Independent checker: gauge misses an edge endpoint"
            left = grp.compose(grp.perm[submitted[a]], grp.perm[value])
            if grp.compose(left, grp.inverse(grp.perm[submitted[b]])) != grp.identity_perm:
                return False, f"Independent checker: edge {key} not trivialized by submitted gauge"
        return True, "Independent checker confirms PURE_GAUGE"

    if verdict == "FLAT_NONTRIVIAL":
        if pure or not periodic:
            return (
                False,
                "Independent checker: flat connection is pure gauge; FLAT_NONTRIVIAL is false",
            )
        base = result.get("base")
        found = []
        winds: list[tuple[int, int] | None] = []
        for name in ("a", "b"):
            loop = result.get(f"loop_{name}")
            if (
                not isinstance(loop, list)
                or len(loop) < 2
                or loop[0] != loop[-1]
                or (base is not None and loop[0] != base)
            ):
                return False, f"Independent checker: loop_{name} is not a closed walk from base"
            hol = _holonomy(grp, edges, loop)
            if hol is None or grp.name(hol) != result.get(f"hol_{name}"):
                return False, f"Independent checker: loop_{name} holonomy mismatch"
            found.append(hol)
            winds.append(_torus_winding(loop, L, M))
        if None in winds or abs(winds[0][0] * winds[1][1] - winds[0][1] * winds[1][0]) != 1:
            return False, "Independent checker: loops do not generate the torus"
        if all(h == grp.identity_perm for h in found):
            return False, "Independent checker: both loop holonomies are trivial"
        if grp.compose(found[0], found[1]) != grp.compose(found[1], found[0]):
            return False, "Independent checker: loop holonomies do not commute"
        return True, "Independent checker confirms FLAT_NONTRIVIAL"

    return False, f"Independent checker: unexpected verdict {verdict!r}"
