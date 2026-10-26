"""Checker 2: Independent Primal-Dual & Coboundary Certifier for C011.

Total parsing: returns (False, reason: str) on any malformed or incorrect inputs,
never raises an unhandled exception.
Verifies:
1. Strict wire schema and canonical rational formatting (no floats, no '1/1', no unreduced fractions).
2. Refusal verification for UNKNOWN (closed list, checks refusal is warranted).
3. Structured witness verification for OUT_OF_SCOPE.
4. Bound compliance: |V| <= 60, |E| <= 200.
5. Exact coboundary relation: r_e == c_e - (phi(head) - phi(tail)) on all edges.
6. Primal cost: sum_{e} w_e * |r_e| == phi1.
7. Dual capacity: |y_e| <= w_e on all edges.
8. Flow conservation: sum_{head=v} y_e - sum_{tail=v} y_e == 0 at every vertex.
9. Complementary slackness:
   - if r_e > 0 => y_e == w_e
   - if r_e < 0 => y_e == -w_e
   - if |y_e| < w_e => r_e == 0
10. Dual objective equality: sum_{e} c_e * y_e == phi1.
11. Cycle holonomy annihilation: c - r has zero circulation on all fundamental cycles.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

try:
    from ...reference_solver.graph_cohomology import (
        Edge,
        Graph,
        extract_components,
        find_spanning_tree_and_cycles,
    )
except (ImportError, ValueError):
    try:
        from reference_solver.graph_cohomology import (
            Edge,
            Graph,
            extract_components,
            find_spanning_tree_and_cycles,
        )
    except (ImportError, ValueError):
        from omega_engine_pfp.tests.demo_004.b_cohomology.c011_cycle_rank_ladder_coboundary_repair.reference_solver.graph_cohomology import (
            Edge,
            Graph,
            extract_components,
            find_spanning_tree_and_cycles,
        )

CLOSED_REFUSAL_CODES = frozenset(
    {
        "VERTEX_COUNT_OUT_OF_BOUNDS",
        "EDGE_COUNT_OUT_OF_BOUNDS",
        "INVALID_CAPACITY",
        "NEGATIVE_WEIGHT",
        "DISCONNECTED_GRAPH",
        "MALFORMED_EDGE_SPEC",
        "INVALID_TARGET_DEFECT",
        "MALFORMED_CASE_STRUCTURE",
    }
)

VALID_OOS_REASONS = frozenset(
    {
        "NONPOSITIVE_WEIGHT",
        "SELF_LOOP",
        "UNKNOWN_ENDPOINT",
    }
)


def _is_canonical_rational_str(s: Any) -> bool:
    """True if s is a strictly formatted canonical rational string.

    Enforces RFC 8785 canonical string format:
    - No leading/trailing/internal whitespace.
    - No floats, decimals, exponents, or underscores.
    - Integers: plain decimal string without leading zeros or plus sign ('0', '1', '-3', never '+17', '017', '-0').
    - Fractions: 'p/q' where p, q are integers, q > 1, gcd(|p|, q) == 1, p != 0,
      with no leading zeros or plus signs on either p or q (never '+5/6', '05/6', '5/06', '5/1').
    """
    if not isinstance(s, str):
        return False
    if any(c.isspace() for c in s) or "." in s or "e" in s.lower() or "_" in s:
        return False
    if "/" in s:
        parts = s.split("/")
        if len(parts) != 2:
            return False
        num_str, den_str = parts[0], parts[1]
        try:
            num = int(num_str)
            den = int(den_str)
            if str(num) != num_str or str(den) != den_str:
                return False
            if den <= 1 or num == 0:
                return False
            f = Fraction(num, den)
            return f.numerator == num and f.denominator == den
        except Exception:
            return False
    else:
        try:
            val = int(s)
            return str(val) == s
        except Exception:
            return False


def _parse_canonical(s: Any) -> tuple[bool, Fraction | None]:
    if not _is_canonical_rational_str(s):
        return False, None
    try:
        return True, Fraction(s)
    except Exception:
        return False, None


def _compute_components_and_b1(
    raw_verts: list[str], raw_edges: list[Mapping[str, Any]]
) -> tuple[int, int]:
    """Computes number of connected components and cycle rank b1 safely on raw inputs."""
    adj: dict[str, list[str]] = {v: [] for v in raw_verts if isinstance(v, str)}
    valid_edge_count = 0
    for e in raw_edges:
        if isinstance(e, Mapping):
            u = e.get("u") or e.get("tail")
            v = e.get("v") or e.get("head")
            if isinstance(u, str) and isinstance(v, str) and u in adj and v in adj:
                adj[u].append(v)
                adj[v].append(u)
                valid_edge_count += 1
    visited: set[str] = set()
    num_components = 0
    for v in adj:
        if v not in visited:
            num_components += 1
            visited.add(v)
            q = [v]
            for curr in q:
                for nxt in adj[curr]:
                    if nxt not in visited:
                        visited.add(nxt)
                        q.append(nxt)
    b1 = valid_edge_count - len(adj) + num_components
    return num_components, b1


def _verify_refusal_warranted(case: Mapping[str, Any], refusal: str) -> tuple[bool, str]:
    """Verifies that an UNKNOWN refusal code is actually warranted by the input case."""
    if not isinstance(case, Mapping):
        if refusal == "MALFORMED_CASE_STRUCTURE":
            return True, f"VALID_REFUSAL_{refusal}"
        return False, "FAIL: case is not a mapping"

    raw_verts = case.get("vertices")
    raw_edges = case.get("edges")

    # 1. VERTEX_COUNT_OUT_OF_BOUNDS
    if refusal == "VERTEX_COUNT_OUT_OF_BOUNDS":
        if isinstance(raw_verts, list) and 1 <= len(raw_verts) <= 60:
            return (
                False,
                f"FAIL: refused VERTEX_COUNT_OUT_OF_BOUNDS on valid vertex count {len(raw_verts)}",
            )
        return True, f"VALID_REFUSAL_{refusal}"

    # 2. EDGE_COUNT_OUT_OF_BOUNDS
    if refusal == "EDGE_COUNT_OUT_OF_BOUNDS":
        if isinstance(raw_edges, list):
            if len(raw_edges) > 200:
                return True, f"VALID_REFUSAL_{refusal}"
            if isinstance(raw_verts, list):
                num_comps, b1 = _compute_components_and_b1(raw_verts, raw_edges)
                if b1 > 16:
                    return True, f"VALID_REFUSAL_{refusal}"
                return (
                    False,
                    f"FAIL: refused EDGE_COUNT_OUT_OF_BOUNDS on case with |E|={len(raw_edges)} <= 200 and b1={b1} <= 16",
                )
        return True, f"VALID_REFUSAL_{refusal}"

    # 3. NEGATIVE_WEIGHT
    if refusal == "NEGATIVE_WEIGHT":
        if not isinstance(raw_edges, list):
            return False, "FAIL: refused NEGATIVE_WEIGHT but edges is not a list"
        has_nonpositive = False
        for e in raw_edges:
            if isinstance(e, Mapping):
                w_raw = e.get("weight")
                ok, w_val = _parse_canonical(str(w_raw))
                if ok and w_val is not None and w_val <= 0:
                    has_nonpositive = True
                    break
        if not has_nonpositive:
            return False, "FAIL: refused NEGATIVE_WEIGHT on case with strictly positive weights"
        return True, f"VALID_REFUSAL_{refusal}"

    # 4. INVALID_CAPACITY
    if refusal == "INVALID_CAPACITY":
        if not isinstance(raw_edges, list):
            return False, "FAIL: refused INVALID_CAPACITY but edges is not a list"
        enforce_den = case.get("enforce_denominator_bounds", False)
        has_invalid = False
        for e in raw_edges:
            if not isinstance(e, Mapping):
                has_invalid = True
                break
            w_raw = e.get("weight")
            if w_raw is None:
                has_invalid = True
                break
            ok, w_val = _parse_canonical(str(w_raw))
            if not ok or w_val is None or w_val <= 0:
                has_invalid = True
                break
            if enforce_den and w_val.denominator > 12:
                has_invalid = True
                break
        if not has_invalid:
            return (
                False,
                "FAIL: refused INVALID_CAPACITY on case where all edge capacities are valid positive rationals",
            )
        return True, f"VALID_REFUSAL_{refusal}"

    # 5. DISCONNECTED_GRAPH
    if refusal == "DISCONNECTED_GRAPH":
        if not case.get("require_connected", False):
            return (
                False,
                "FAIL: refused DISCONNECTED_GRAPH but require_connected is not enabled for this case",
            )
        if not isinstance(raw_verts, list) or not isinstance(raw_edges, list):
            return True, f"VALID_REFUSAL_{refusal}"
        num_comps, _ = _compute_components_and_b1(raw_verts, raw_edges)
        if num_comps <= 1:
            return False, "FAIL: refused DISCONNECTED_GRAPH on a connected graph"
        return True, f"VALID_REFUSAL_{refusal}"

    # 6. INVALID_TARGET_DEFECT
    if refusal == "INVALID_TARGET_DEFECT":
        if "target_defect" not in case and "target_phi1" not in case:
            return False, "FAIL: refused INVALID_TARGET_DEFECT on case without target defect"
        raw_td = case.get("target_defect") if "target_defect" in case else case.get("target_phi1")
        ok, td_val = _parse_canonical(str(raw_td))
        if ok and td_val is not None and td_val >= 0:
            return False, f"FAIL: refused INVALID_TARGET_DEFECT on valid target defect {raw_td!r}"
        return True, f"VALID_REFUSAL_{refusal}"

    # 7. MALFORMED_EDGE_SPEC
    if refusal == "MALFORMED_EDGE_SPEC":
        if not isinstance(raw_edges, list):
            return True, f"VALID_REFUSAL_{refusal}"
        has_malformed = False
        seen_ids: set[str] = set()
        for idx, e in enumerate(raw_edges):
            if not isinstance(e, Mapping):
                has_malformed = True
                break
            u = e.get("u") or e.get("tail")
            v = e.get("v") or e.get("head")
            if not isinstance(u, str) or not isinstance(v, str):
                has_malformed = True
                break
            eid = e.get("id") or f"{u}->{v}"
            if eid in seen_ids:
                has_malformed = True
                break
            seen_ids.add(eid)
            c_raw = e.get("claim")
            if c_raw is None or not _is_canonical_rational_str(str(c_raw)):
                has_malformed = True
                break
        if not has_malformed:
            return False, "FAIL: refused MALFORMED_EDGE_SPEC on case with valid edge specifications"
        return True, f"VALID_REFUSAL_{refusal}"

    # 8. MALFORMED_CASE_STRUCTURE
    if refusal == "MALFORMED_CASE_STRUCTURE":
        case_id = case.get("id") or case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            return True, f"VALID_REFUSAL_{refusal}"
        if (
            not isinstance(raw_verts, list)
            or any(not isinstance(v, str) or not v for v in raw_verts)
            or len(set(raw_verts)) != len(raw_verts)
        ):
            return True, f"VALID_REFUSAL_{refusal}"
        if not isinstance(raw_edges, list) or any(not isinstance(e, Mapping) for e in raw_edges):
            return True, f"VALID_REFUSAL_{refusal}"
        return False, "FAIL: refused MALFORMED_CASE_STRUCTURE on structurally valid case"

    return False, f"FAIL: unhandled refusal code {refusal!r}"


def verify_potential_certificate(case: Any, result: Any) -> tuple[bool, str]:
    """Verifies a case result using independent primal-dual and coboundary criteria."""
    if not isinstance(case, Mapping):
        return False, "FAIL: case is not a mapping"
    if not isinstance(result, Mapping):
        return False, "FAIL: result is not a mapping"

    status = result.get("status")
    if not isinstance(status, str):
        return False, "FAIL: missing or invalid status in result"

    raw_verts = case.get("vertices")
    raw_edges = case.get("edges")

    # Branch 1: UNKNOWN refusal
    if status == "UNKNOWN":
        refusal = result.get("refusal") or result.get("refusal_code")
        if not isinstance(refusal, str) or refusal not in CLOSED_REFUSAL_CODES:
            return False, f"FAIL: invalid refusal code {refusal!r}"

        # Verify that refusal is actually warranted
        return _verify_refusal_warranted(case, refusal)

    # Branch 2: OUT_OF_SCOPE
    if status == "OUT_OF_SCOPE":
        witness = result.get("witness")
        if not isinstance(witness, Mapping):
            return False, "FAIL: OUT_OF_SCOPE requires witness dictionary"
        edge_id = witness.get("edge")
        reason = witness.get("reason")
        if not isinstance(edge_id, str) or not isinstance(reason, str):
            return False, "FAIL: malformed witness fields"
        if reason not in VALID_OOS_REASONS:
            return False, f"FAIL: unknown out-of-scope reason {reason!r}"

        if not isinstance(raw_edges, list):
            return True, "VALID_OUT_OF_SCOPE"

        verts_set = set(raw_verts or [])
        found_edge = None
        for idx, e in enumerate(raw_edges):
            if isinstance(e, Mapping):
                eid = e.get("id") or f"{e.get('u')}->{e.get('v')}"
                if eid == edge_id:
                    found_edge = e
                    break

        if found_edge is None:
            return False, f"FAIL: witness edge {edge_id!r} not found in case"

        u = found_edge.get("u") or found_edge.get("tail")
        v = found_edge.get("v") or found_edge.get("head")

        if reason == "SELF_LOOP":
            if u != v:
                return False, f"FAIL: witness claimed SELF_LOOP but u={u!r} != v={v!r}"
        elif reason == "UNKNOWN_ENDPOINT":
            if u in verts_set and v in verts_set:
                return (
                    False,
                    "FAIL: witness claimed UNKNOWN_ENDPOINT but both endpoints in vertices",
                )
        elif reason == "NONPOSITIVE_WEIGHT":
            w_raw = found_edge.get("weight")
            try:
                ok, w_frac = _parse_canonical(str(w_raw))
                if not ok or w_frac is None or w_frac > 0:
                    return False, "FAIL: witness claimed NONPOSITIVE_WEIGHT but weight is positive"
            except Exception:
                pass

        return True, "VALID_OUT_OF_SCOPE"

    # Branch 3: SOLVED
    if status != "SOLVED":
        return False, f"FAIL: unrecognized status {status!r}"

    # Bounds check on case
    if not isinstance(raw_verts, list) or not (1 <= len(raw_verts) <= 60):
        return (
            False,
            f"FAIL: SOLVED returned on out-of-bounds vertex count {len(raw_verts) if isinstance(raw_verts, list) else 'invalid'}",
        )

    if not isinstance(raw_edges, list) or len(raw_edges) > 200:
        return False, "FAIL: SOLVED returned on out-of-bounds edge count"

    # Parse phi1
    phi1_raw = result.get("phi1")
    ok, phi1 = _parse_canonical(phi1_raw)
    if not ok or phi1 is None or phi1 < 0:
        return False, f"FAIL: invalid phi1 canonical rational {phi1_raw!r}"

    # Parse potential
    potential_raw = result.get("potential")
    if not isinstance(potential_raw, Mapping):
        return False, "FAIL: potential must be a mapping"

    potential: dict[str, Fraction] = {}
    for v in raw_verts:
        if v not in potential_raw:
            return False, f"FAIL: vertex {v!r} missing from potential"
        pot_v_raw = potential_raw[v]
        ok_pot, pot_v = _parse_canonical(pot_v_raw)
        if not ok_pot or pot_v is None:
            return False, f"FAIL: invalid potential rational for vertex {v!r}: {pot_v_raw!r}"
        potential[v] = pot_v

    for k in potential_raw:
        if k not in potential:
            return False, f"FAIL: extra vertex {k!r} in potential not in graph"

    # Parse repair and dual mappings
    repair_raw = result.get("repair", {})
    if not isinstance(repair_raw, Mapping):
        return False, "FAIL: repair must be a mapping"

    dual_raw = result.get("dual", {})
    if not isinstance(dual_raw, Mapping):
        return False, "FAIL: dual must be a mapping"

    parsed_edges: list[Edge] = []
    edges_info: list[dict[str, Any]] = []
    seen_eids: set[str] = set()
    primal_cost = Fraction(0)

    for idx, e in enumerate(raw_edges):
        if not isinstance(e, Mapping):
            return False, "FAIL: malformed edge in case"
        u = e.get("u") or e.get("tail")
        v = e.get("v") or e.get("head")
        eid = e.get("id") or f"{u}->{v}"
        if eid in seen_eids:
            eid = f"{u}->{v}#{idx}"
        seen_eids.add(eid)

        # Endpoint validity guard: fails closed if endpoints are not valid declared vertices
        if (
            not isinstance(u, str)
            or not isinstance(v, str)
            or u not in potential
            or v not in potential
        ):
            return False, f"FAIL: edge {eid} references unknown endpoint: u={u!r}, v={v!r}"

        ok_c, claim = _parse_canonical(str(e.get("claim")))
        if not ok_c or claim is None:
            return False, f"FAIL: malformed claim in edge {eid}"

        ok_w, weight = _parse_canonical(str(e.get("weight")))
        if not ok_w or weight is None or weight <= 0:
            return False, f"FAIL: nonpositive or malformed weight in edge {eid}"

        # Parse repair
        r_raw = repair_raw.get(eid, "0")
        ok_r, r_val = _parse_canonical(str(r_raw))
        if not ok_r or r_val is None:
            return False, f"FAIL: malformed repair rational for edge {eid}: {r_raw!r}"

        # Check coboundary relation: r_e == c_e - (phi(head) - phi(tail))
        delta_phi = potential[v] - potential[u]
        expected_r = claim - delta_phi
        if r_val != expected_r:
            return False, (
                f"FAIL: coboundary relation broken on edge {eid}: "
                f"r_e={r_val} != c_e - delta_phi = {claim} - ({potential[v]} - {potential[u]}) = {expected_r}"
            )

        primal_cost += weight * abs(r_val)
        parsed_edges.append(Edge(id=eid, u=u, v=v, claim=claim, weight=weight))

        # Parse dual
        y_raw = dual_raw.get(eid, "0")
        ok_y, y_val = _parse_canonical(str(y_raw))
        if not ok_y or y_val is None:
            return False, f"FAIL: malformed dual rational for edge {eid}: {y_raw!r}"

        # Check dual capacity bound |y_e| <= w_e
        if abs(y_val) > weight:
            return False, f"FAIL: dual capacity exceeded on edge {eid}: |{y_val}| > {weight}"

        # Complementary slackness
        if r_val > 0 and y_val != weight:
            return (
                False,
                f"FAIL: complementary slackness violated on edge {eid}: r_e={r_val} > 0 but y_e={y_val} != w_e={weight}",
            )
        if r_val < 0 and y_val != -weight:
            return (
                False,
                f"FAIL: complementary slackness violated on edge {eid}: r_e={r_val} < 0 but y_e={y_val} != -w_e={-weight}",
            )
        if abs(y_val) < weight and r_val != 0:
            return (
                False,
                f"FAIL: complementary slackness violated on edge {eid}: |y_e|={abs(y_val)} < w_e={weight} but r_e={r_val} != 0",
            )

        edges_info.append({"u": u, "v": v, "dual": y_val, "claim": claim})

    # Extra edge validation on repair and dual mappings
    for eid in repair_raw:
        if eid not in seen_eids:
            return False, f"FAIL: extra edge {eid!r} in repair not in graph"

    for eid in dual_raw:
        if eid not in seen_eids:
            return False, f"FAIL: extra edge {eid!r} in dual not in graph"

    # Flow conservation at every vertex
    net_flow: dict[str, Fraction] = {v: Fraction(0) for v in raw_verts}
    for e in edges_info:
        net_flow[e["v"]] += e["dual"]
        net_flow[e["u"]] -= e["dual"]

    for v, flow in net_flow.items():
        if flow != 0:
            return (
                False,
                f"FAIL: circulation flow conservation violated at vertex {v!r}: net flow = {flow} != 0",
            )

    # Check primal cost equals phi1
    if primal_cost != phi1:
        return (
            False,
            f"FAIL: primal cost sum(w_e * |r_e|) = {primal_cost} does not match phi1 = {phi1}",
        )

    # Check dual objective equals phi1
    dual_objective = sum(e["claim"] * e["dual"] for e in edges_info)
    if dual_objective != phi1:
        return (
            False,
            f"FAIL: dual objective sum(c_e * y_e) = {dual_objective} does not match phi1 = {phi1}",
        )

    # Annihilation check: repaired claims c' = c - r must have zero circulation on all fundamental cycles
    graph = Graph(vertices=raw_verts, edges=parsed_edges)
    components = extract_components(graph)
    for comp in components:
        _, _, cycles = find_spanning_tree_and_cycles(comp)
        edge_map = {edge.id: edge for edge in comp.edges}
        for j, cycle in enumerate(cycles):
            cycle_holonomy = Fraction(0)
            for eid, orient in cycle.items():
                r_val = Fraction(repair_raw.get(eid, "0"))
                rep_c = edge_map[eid].claim - r_val
                cycle_holonomy += rep_c * Fraction(orient)
            if cycle_holonomy != 0:
                return (
                    False,
                    f"FAIL: cycle holonomy not annihilated on cycle {j}: residual = {cycle_holonomy} != 0",
                )

    return True, "VALID_POTENTIAL_CERTIFICATE"
