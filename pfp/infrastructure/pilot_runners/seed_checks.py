"""Finite checks for the actual catalog problems; no model attestations.

This is the implementation behind evaluator_000, not another execution service.
Unimplemented mathematical or native obligations remain explicit refusals.
AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from typing import Any

import sympy as sp


class SeedCheckFailure(ValueError):
    pass


REVIEW_IDS = tuple(f"DEMO-N{i:02d}" for i in range(16)) + tuple(
    f"DEMO-B{i:02d}" for i in range(16, 20)
) + tuple(f"DEMO-Q{i:02d}" for i in range(20, 24))
SEED_IDS = REVIEW_IDS + tuple(f"DEMO_{i:02d}" for i in range(1, 51))


def rational(value: Any) -> Fraction:
    """The candidate is never rounded, coerced from a float, or booleanized."""
    if type(value) not in (int, str):
        raise SeedCheckFailure("NON_EXACT_RATIONAL")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise SeedCheckFailure("NON_EXACT_RATIONAL") from exc
    return result


def vector(value: Any, length: int) -> list[Fraction]:
    if type(value) is not list or len(value) != length:
        raise SeedCheckFailure("WITNESS_SHAPE")
    return [rational(v) for v in value]


def compare(value: Any, expected: Any, path: str = "candidate") -> None:
    """Require every computed field; accept equivalent exact rational spellings."""
    if isinstance(expected, Fraction):
        if rational(value) != expected:
            raise SeedCheckFailure("WRONG_VALUE: " + path)
    elif type(expected) is dict:
        if type(value) is not dict or set(value) != set(expected):
            raise SeedCheckFailure("MISSING_OR_EXTRA_FIELDS: " + path)
        for key, item in expected.items():
            compare(value[key], item, path + "." + key)
    elif type(expected) is list:
        if type(value) is not list or len(value) != len(expected):
            raise SeedCheckFailure("WITNESS_SHAPE: " + path)
        for i, item in enumerate(expected):
            compare(value[i], item, f"{path}[{i}]")
    elif type(value) is not type(expected) or value != expected:
        raise SeedCheckFailure("WRONG_VALUE_OR_TYPE: " + path)


def wire(value: Any) -> Any:
    if isinstance(value, Fraction):
        return str(value)
    if type(value) is dict:
        return {k: wire(v) for k, v in value.items()}
    if type(value) is list:
        return [wire(v) for v in value]
    return value


def boundary(simplices: list[tuple[str, ...]], lower: list[tuple[str, ...]]) -> list[list[int]]:
    index = {cell: i for i, cell in enumerate(lower)}
    matrix = [[0] * len(simplices) for _ in lower]
    for col, cell in enumerate(simplices):
        for i in range(len(cell)):
            matrix[index[cell[:i] + cell[i + 1:]]][col] += (-1) ** i
    return matrix


def de_bruijn() -> sp.Matrix:
    words = ["".join(x) for x in product("01", repeat=2)]
    return sp.Matrix([[int(right[:1] == left[1:]) for right in words] for left in words])


def cycle_incidence(n: int) -> list[list[int]]:
    return [[int(j == (i + 1) % n) - int(j == i) for j in range(n)] for i in range(n)]


def primal_dual(payload: dict, cochain: list[int], weights: list[int], d0: list[list[int]]) -> dict:
    if set(payload) != {"potential", "dual"}:
        raise SeedCheckFailure("REQUIRED_WITNESS: potential, dual")
    g = vector(payload["potential"], len(d0[0]))
    y = vector(payload["dual"], len(d0))
    residual = [Fraction(c) - sum(a * b for a, b in zip(row, g)) for c, row in zip(cochain, d0)]
    constraints = [sum(row[j] * yy for row, yy in zip(d0, y)) for j in range(len(g))]
    if any(constraints) or any(abs(a) > b for a, b in zip(y, weights)):
        raise SeedCheckFailure("DUAL_INFEASIBLE")
    primal = sum(w * abs(r) for w, r in zip(weights, residual))
    dual = sum(c * yy for c, yy in zip(cochain, y))
    if primal != dual:
        raise SeedCheckFailure("DUALITY_GAP_NONZERO")
    return dict(residual=residual, dual_constraint=constraints, primal_value=primal, dual_value=dual)


_DISPATCH_MISS = object()


def _review_b16_expected():
    candidates = []
    minima = []
    for arity in (1, 2, 3):
        tuples = list(product((0, 1), repeat=arity))
        for mask in range(1 << len(tuples)):
            table = {t for i, t in enumerate(tuples) if mask & (1 << i)}
            candidates.append(table)
            separates = any(((context[:j] + (0,) + context[j:]) in table) !=
                            ((context[:j] + (1,) + context[j:]) in table)
                            for j in range(arity) for context in product((0, 1), repeat=arity - 1))
            if separates:
                minima.append((1 + len(table), arity, sorted(table)))
    cost = min(item[0] for item in minima)
    best = [item for item in minima if item[0] == cost]
    orbits = {min(tuple(t[0]), tuple(1 - x for x in t[0])) for _, _, t in best}
    return dict(candidate_table_count=len(candidates), minimum_item_cost=cost,
                labelled_minima=[dict(arity=a, tuples=[list(t) for t in ts]) for _, a, ts in best],
                unary_minima_count=sum(a == 1 for _, a, _ in best), quotient_classes_count=len(orbits))


def _review_local_a(seed_id):
    if seed_id in {"DEMO-N00", "DEMO-N01", "DEMO-N12"}:
        from pfp.infrastructure.pilot_runners.seed_core_checks import native_expected
        return native_expected(seed_id)
    if seed_id == "DEMO-N02":
        q = [0, 0]
        tagged = [[q[i], i] for i in range(2)]
        return dict(pair_decoded=["a", "b"], edge_decoded={"source": "a", "target": "b"},
                    reports=q, tagged_reports=tagged, endpoint_support=["a", "b"],
                    occurrence_counts=[len([("a", "b")] * n) for n in (1, 2, 3)])
    if seed_id in {"DEMO-N03", "DEMO-N04"}:
        vertices = [(v,) for v in "abc"]
        edges = [("a", "b"), ("a", "c"), ("b", "c")]
        b1 = boundary(edges, vertices)
        b2 = boundary([tuple("abc")], edges)
        ranks = [len(edges) - sp.Matrix(b1).rank(),
                 len(edges) - sp.Matrix(b1).rank() - sp.Matrix(b2).rank()]
        if seed_id == "DEMO-N03":
            return dict(boundary_1=b1, boundary_2=b2, cycle=[1, -1, 1],
                        cycle_boundary=list(sp.Matrix(b1) * sp.Matrix([1, -1, 1])),
                        h1_before=int(ranks[0]), h1_after=int(ranks[1]),
                        retraction_obstruction="nonzero old cycle becomes a boundary")
        return dict(edges=[list(e) for e in edges], face_boundary=[1, -1, 1],
                    double_boundary=[0, 0, 0], reachability=[[1, 1, 1], [0, 1, 1], [0, 0, 1]],
                    h1_skeleton=int(ranks[0]), h1_filled=int(ranks[1]))
    if seed_id == "DEMO-N05":
        def gram(q):
            off = Fraction(2 - q, 2)
            return [[Fraction(1), off], [off, Fraction(1)]]
        good, bad = gram(1), gram(9)
        return dict(gram_valid=good, determinant_valid=Fraction(sp.Matrix(good).det()),
                    gram_invalid=bad, determinant_invalid=Fraction(sp.Matrix(bad).det()),
                    angle_status="CERTIFIED_ENCLOSURE_REQUIRED")
    if seed_id == "DEMO-N06":
        return dict(old_recovery={"a'": "inl(a)", "b'": "inl(b)"},
                    foreign_recovery={"z": "NON_DESCENT"}, empty_base_maps=0)
    return _DISPATCH_MISS


def _review_local_b(seed_id):
    if seed_id in {"DEMO-N07", "DEMO-N10"}:
        t = de_bruijn()
        if seed_id == "DEMO-N07":
            return dict(adjacency=t.tolist(), trace_1=int(sp.trace(t)), trace_2=int(sp.trace(t**2)),
                        primitive_period_2=(int(sp.trace(t**2)) - int(sp.trace(t))) // 2)
        return dict(adjacency=t.tolist(), characteristic_polynomial=[int(v) for v in t.charpoly().all_coeffs()],
                    evidence_scope="FINITE_MATRIX_ONLY")
    if seed_id == "DEMO-N09":
        table = [[0, 1], [1, 1]]
        dagger = [0, 1]
        return dict(composition=table, dagger=dagger,
                    involution=[dagger[dagger[i]] for i in (0, 1)],
                    reversed_composition=[[dagger[table[j][i]] for j in (0, 1)] for i in (0, 1)],
                    inverses_of_p=[i for i in (0, 1) if table[1][i] == table[i][1] == 0],
                    p_dagger_p=table[dagger[1]][1])
    if seed_id == "DEMO-N11":
        return dict(branches=[["a", "b", "d"], ["a", "c", "d"]],
                    ranks=[[2, 1, 0], [2, 1, 0]], removed_rule_normal_forms=["c", "d"],
                    complete_critical_pairs=[["b", "c", "d"]])
    if seed_id == "DEMO-N13":
        history = ["ab"[i % 2] for i in range(7)]
        return dict(history=history, current=history[-1], transitions=6, period=2,
                    carrier_change="REQUIRES_SEPARATE_LICENSE")
    return _DISPATCH_MISS


def _review_policy_and_tables(seed_id):
    if seed_id == "DEMO-N14":
        carrier = [0, 1, 2]
        # A one-comparison budget cannot finish the first existential query.
        budget, examined, terminal = 1, [], "UNKNOWN"
        for x, y in product(carrier, repeat=2):
            if len(examined) == budget:
                break
            examined.append([x, y, x < y])
        return dict(relation=[[a, b] for a in carrier for b in carrier if a < b],
                    witnesses={str(a): [b for b in carrier if a < b] for a in carrier},
                    falsifying_x=2, empty_forall=True, empty_exists=False,
                    budget=budget, examined=examined, incomplete_search=terminal)
    if seed_id == "DEMO-N15":
        raise SeedCheckFailure("POLICY_ATTACHMENT_REPLAY_UNAVAILABLE: actual permitted attachment event required")
    if seed_id == "DEMO-B16":
        return _review_b16_expected()
    return _DISPATCH_MISS


def _review_boolean_and_quantum(seed_id):
    if seed_id == "DEMO-B17":
        q, f1, f2 = [0, 0, 1], [0, 1, 0], [1, 1, 0]
        return dict(q=q, f1=f1, f2=f2, counterexample=["a", "b"], factor={"0": 1, "1": 0},
                    duplicate_reports=[[x, x] for x in q])
    if seed_id == "DEMO-B18":
        old, new = [0, 1], [0, 0, 1]
        return dict(recovery=[0, 1, "NON_DESCENT"], old_report=old, new_on_old=new[:2],
                    preservation_failures=[i for i in old if old[i] != new[i]], lift_status="REFUSED")
    if seed_id == "DEMO-B19":
        return dict(compressed_reports=[0, 0, 1], enabled=[True, False, False],
                    transition_results=["c", None, None], conflicting_fiber=["a", "b"],
                    deterministic_factor="NON_DESCENT")
    if seed_id == "DEMO-Q20":
        x, y = Fraction(3, 5), Fraction(4, 5)
        return dict(conjugate=[x, -y], squared_modulus=x*x+y*y,
                    inverse=[x, -y], product=[Fraction(1), Fraction(0)],
                    zero_inverse="REFUSED", invalid_scalar="REFUSED")
    if seed_id == "DEMO-Q21":
        return dict(squared_norms=[Fraction(2), Fraction(8), Fraction(0)],
                    weights=[[Fraction(1, 2), Fraction(1, 2)]]*2,
                    branch_rays=[[1, 0], [0, 1]], unit_norm=False, zero_ray="REFUSED")
    if seed_id == "DEMO-Q22":
        raise SeedCheckFailure("LOCAL_CHANNEL_WITNESS_REQUIRED: submit and check exact Kraus completeness and transported marginals")
    if seed_id == "DEMO-Q23":
        h = sp.Matrix([[1, 1], [1, -1]])
        c = sp.diag(sp.eye(2), h)
        return dict(h_gram=(h.T*h).tolist(), c_gram=(c.T*c).tolist(),
                    distorted_weights=[Fraction(1, 3), Fraction(2, 3)],
                    required_extension_field="Q(sqrt(2),i)")
    return _DISPATCH_MISS


def review_expected(seed_id: str) -> dict:
    """Recompute finite facts from the displayed review-seed problem."""
    result = _review_local_a(seed_id)
    if result is not _DISPATCH_MISS:
        return result
    result = _review_local_b(seed_id)
    if result is not _DISPATCH_MISS:
        return result
    result = _review_policy_and_tables(seed_id)
    if result is not _DISPATCH_MISS:
        return result
    result = _review_boolean_and_quantum(seed_id)
    if result is not _DISPATCH_MISS:
        return result
    raise SeedCheckFailure("UNKNOWN_SEED")


def _mss_local_a(number):
    if number == 1:
        return dict(raw="<>", admitted_data=[], admitted_forms=[], admitted_instances=[],
                    replay_packets=["<>"], profile="mss0_ground_boundary")
    if number == 2:
        return dict(old_language=["<>"], new_language=["<>", "<a>"],
                    inclusion={"<>": "<>"}, down_map={"<>": "<>", "<a>": "NON_DESCENT"})
    if number == 4:
        return dict(candidates=[dict(input=s, source=s[1], target=s[2], arity=2, status=status)
                                for s, status in (("<ab>", "ACCEPTED"), ("<ba>", "ACCEPTED"),
                                                  ("<aa>", "REFUSED"))] +
                    [dict(input="<abc>", source=None, target=None, arity=3, status="REFUSED")])
    if number == 5:
        sigma = dict(a="c", b="b", c="a")
        edges = [["a", "b"], ["b", "c"]]
        return dict(vertices=list("abc"), edges=edges, transported_vertices=[sigma[v] for v in "abc"],
                    transported_edges=[[sigma[a], sigma[b]] for a, b in edges],
                    path=list("abc"), transported_path=[sigma[v] for v in "abc"])
    return _DISPATCH_MISS


def _mss_local_b(number):
    if number in {6, 8}:
        b1 = boundary([tuple(e) for e in ("ab", "ac", "bc")], [(v,) for v in "abc"])
        b2 = boundary([tuple("abc")], [tuple(e) for e in ("ab", "ac", "bc")])
        return dict(boundary_1=b1, boundary_2=b2, double_boundary=(sp.Matrix(b1)*sp.Matrix(b2)).tolist(),
                    coefficient_profile="Q" if number == 8 else "Z", metric_data=None)
    if number == 9:
        return dict(inclusion={"a": "A", "b": "B"}, down_map={"A": "a", "B": "b", "C": "NON_DESCENT"},
                    old_composite={"a": "a", "b": "b"}, foreign_counterexample="C")
    if number == 10:
        source = [["s0", "task", "ab"], ["s1", "constraint", "ab"], ["s2", "task", "ba"]]
        return dict(payloads=["ab", "ba"], occurrences=[[s, r, int(t == "ba")] for s, r, t in source],
                    reconstructed=source, merged_occurrence_count=2, original_occurrence_count=3)
    if number == 12:
        cm = sp.Matrix([[0, 1, 1, 1], [1, 0, 1, 1], [1, 1, 0, 2], [1, 1, 2, 0]])
        return dict(cayley_menger=cm.tolist(), determinant=int(cm.det()),
                    area_squared=Fraction(-cm.det(), 16), exact_angle_status="SCALAR_EXTENSION_REQUIRED")
    if number == 15:
        values = [[x, y, (1-x+y) % 2] for x, y in product((0, 1), repeat=2)]
        return dict(colours={"flip": ["Bit", "Bit"], "combine": ["Bit", "Bit", "Pair"],
                            "parity": ["Pair", "Out"]}, slot=0, left=values, right=values)
    return _DISPATCH_MISS


def _mss_local_c(number):
    if number == 17:
        history = ["ab" if i % 2 == 0 else "ba" for i in range(13)]
        return dict(history=history, rule_ids=["ab_to_ba" if i % 2 == 0 else "ba_to_ab" for i in range(12)],
                    repeated_state_indices=[0, 2], terminal="BUDGET_EXHAUSTED", normal_form=None)
    if number == 18:
        return dict(current_images={"a": "a", "b": "b"}, current_policy="P1",
                    historical_replay="HISTORICAL_BYTES_UNAVAILABLE",
                    required_artifacts=["receipt_bytes", "checker_digest", "policy_P0_bytes"])
    if number == 19:
        y, bound = Fraction(1), Fraction(1)
        old, new = Fraction(1)*y, Fraction(0)*y
        return dict(historical_residual=old, current_residual=new, historical_bound=bound, current_bound=bound,
                    historical_accepted=old == 0 and abs(y) <= bound,
                    current_accepted=new == 0 and abs(y) <= bound)
    if number == 21:
        return dict(d0=cycle_incidence(4), cochain=[1]*4, cycle=[1]*4, pairing=Fraction(4),
                    closed=True, exact=False, coefficient_profile="Q")
    return _DISPATCH_MISS


def _mss_local_d(number):
    if number in {22, 34}:
        solutions = [list(x) for x in product((0, 1), repeat=3)
                     if all((x[(i+1) % 3] + x[i]) % 2 == 1 for i in range(3))]
        result = dict(d0=cycle_incidence(3), cochain=[1, 1, 1], cycle_pairing=1,
                      global_sections=solutions, coefficient_profile="F2")
        if number == 34:
            contexts = [[0,1],[1,2],[2,0]]
            tables = [[[Fraction(int(a != b),2) for b in (0,1)] for a in (0,1)] for _ in contexts]
            support = [list(x) for x in product((0,1),repeat=3)
                       if all(tables[i][x[a]][x[b]] > 0 for i,(a,b) in enumerate(contexts))]
            result.update(global_support=support, contexts=contexts, probability_tables=tables,
                          overlap_marginals=[[sum(row) for row in table] for table in tables],
                          global_distribution="NO_NONNEGATIVE_EXTENSION_EMPTY_SUPPORT",
                          model_scope="DECLARED_TABLE_SUPPORT_AND_F2_CIRCLE")
        return result
    if number == 24:
        d0 = [[-1, 1, 0], [-1, 0, 1], [0, -1, 1]]
        d1 = [[1, -1, 1]]
        return dict(d0=d0, d1=d1, cochain=[1, 0, 0], d1_cochain=[1],
                    double_differential=(sp.Matrix(d1)*sp.Matrix(d0)).tolist(),
                    classification="NONCLOSED", repair="NO_EXACT_VERTEX_REPAIR")
    if number in {25, 26}:
        result = dict(integer_obstruction={"modulus": 2, "residue": 1},
                      integer_repair="REFUSED", coefficient_profile="Z")
        if number == 26:
            result.update(rational_repair=Fraction(1, 2), f2_differential=0,
                          f2_input=1, f2_repair="REFUSED")
        return result
    if number == 29:
        u, v = [0, 1], [1, 1]
        return dict(u=u, v=v, difference=[1, 0], source_potential=1,
                    theta_u=[0, 0], theta_v=[0, 1], target_difference=[0, 1],
                    quotient_map="NOT_WELL_DEFINED")
    if number == 30:
        d0 = sp.Matrix([[1, 0], [0, 1], [1, 1], [2, -1]])
        d1 = sp.Matrix([[-1, -1, 1, 0], [-2, -2, 2, 0]])
        p = sp.zeros(4)
        for i, j in enumerate((3, 1, 2, 0)):
            p[i, j] = 1
        c = sp.Matrix([0, 0, 0, 1])
        return dict(d0=d0.tolist(), d1=d1.tolist(), input=list(c),
                    double_differential=(d1*d0).tolist(), transported_d0=(p*d0).tolist(),
                    transported_d1=(d1*p).tolist(), transported_input=list(p*c),
                    exact=False, closed=True)
    return _DISPATCH_MISS


def mss_expected(number: int) -> dict:
    """Finite components implemented here, with explicit residual for larger targets."""
    if number in {3, 11, 16}:
        from pfp.infrastructure.pilot_runners.seed_core_checks import core_expected
        return core_expected(number)
    if number in {20,27,28} or (31 <= number <= 50 and number != 34):
        from pfp.infrastructure.pilot_runners.seed_advanced_checks import (
            advanced_expected,
        )
        return advanced_expected(number)
    result = _mss_local_a(number)
    if result is not _DISPATCH_MISS:
        return result
    result = _mss_local_b(number)
    if result is not _DISPATCH_MISS:
        return result
    result = _mss_local_c(number)
    if result is not _DISPATCH_MISS:
        return result
    result = _mss_local_d(number)
    if result is not _DISPATCH_MISS:
        return result
    obligations = {
        3: "GRAMMAR_SOURCE_BOUND_THREE_PROFILE_PARSE", 11: "TETRAHEDRON_ORIENTATION_CHAIN_MAP",
        14: "WEIGHTED_HODGE_RECONSTRUCTION_ADJOINTS", 16: "POSITIONED_REWRITE_AND_RELATIONAL_DEPENDENCY",
        20: "LEAN_ELABORATION_AND_AXIOM_CENSUS", 23: "TWO_CYCLE_PRIMAL_DUAL_OPTIMUM",
        27: "TETRAHEDRAL_INCIDENCE_PAIRING", 28: "GROUP_COCYCLE_ALL_ORDERED_PAIRS",
        31: "GAUSSIAN_UNITARY_FOUR_PROBE_READOUT", 32: "EXACT_SCHMIDT_AND_MARGINALS",
        33: "LABELLED_INSTRUMENT_CHANNEL_INVERSE", 35: "PR_BOX_ALL_TABLES_GLOBAL_SUPPORT",
        36: "PAULI_SQUARE_PHASE_AND_F2_IMAGE", 37: "ALL_CODE_STATE_RECOVERY",
        38: "PERIODIC_PARALLEL_EDGE_CSS_PAIRINGS", 39: "ALL_WEIGHT_TWO_SYNDROME_STABILIZER_PAIRS",
        40: "THREE_COPY_RECONSTRUCTION_AND_LOGICAL_PAIRINGS", 41: "TRANSPORTED_SHEAR_COMPLEX_PAIRING",
        42: "TWO_SPHERE_PROTECTED_CYCLE_PAIRINGS", 43: "INTEGRAL_TORSION_AND_F2_IMAGE",
        44: "GRADED_MULTIPLICATION_PRESERVATION", 45: "SIGNED_TENSOR_COMPLEX_PAIRING",
        46: "TRANSPORTED_INTEGRAL_DIVISIBILITY", 47: "FILTERED_PAGE_DIFFERENTIAL_TRANSPORT",
        48: "SYMBOLIC_CROSS_POLYTOPE_ALL_DIMENSIONS", 49: "SYMBOLIC_BILINEAR_AND_PAULI_PHASES",
        50: "ALL_SOURCE_BOUND_COMPONENTS_AND_COMPOSITION",
    }
    raise SeedCheckFailure("CHECKER_UNAVAILABLE: " + obligations[number])


def _check_primary_special(seed_id, payload):
    if seed_id == "DEMO_20":
        from pfp.infrastructure.pilot_runners.seed_advanced_checks import (
            advanced_check,
        )
        return advanced_check(20,payload)
    if seed_id == "DEMO-N08":
        if set(payload) != {"potential", "dual", "after_face"}:
            raise SeedCheckFailure("REQUIRED_WITNESS: potential, dual, after_face")
        before = primal_dual({k:payload[k] for k in ("potential","dual")}, [1,1,1], [1,1,1], cycle_incidence(3))
        after = payload["after_face"]
        if type(after) is not dict or set(after) != {"d0","cochain","face_boundary","potential","dual"}:
            raise SeedCheckFailure("AFTER_FACE_WITNESS_REQUIRED")
        compare(after["d0"], cycle_incidence(3))
        compare(after["cochain"],[Fraction(1)]*3)
        compare(after["face_boundary"],[1,1,1])
        new = primal_dual({k:after[k] for k in ("potential","dual")}, [1,1,1], [1,1,1], cycle_incidence(3))
        if before["primal_value"] != new["primal_value"]:
            raise SeedCheckFailure("UNCHANGED_L1_PROBLEM_CHANGED")
        return wire(dict(before=before, after_face=new, phi1_unchanged=before["primal_value"]))
    if seed_id == "DEMO-N15":
        compare(payload, _native(attachment_expected()))
        return wire(attachment_expected())
    if seed_id == "DEMO-Q22":
        from pfp.infrastructure.pilot_runners.seed_core_checks import channel_check
        return channel_check(payload)
    return _DISPATCH_MISS


def _check_exact_potential(seed_id, payload):
    if seed_id in {"DEMO_07", "DEMO_08"}:
        n = 7 if seed_id == "DEMO_07" else 8
        edges = [[-1, 1, 0], [0, -1, 1]] if n == 7 else [[-1, 1, 0], [-1, 0, 1], [0, -1, 1]]
        c = [2, -3] if n == 7 else [2, 5, 3]
        if set(payload) != {"potential", "d0", "original", "residual"}:
            raise SeedCheckFailure("REQUIRED_WITNESS: potential, d0, original, residual")
        compare(payload["d0"], edges)
        compare(payload["original"], [Fraction(value) for value in c])
        g = vector(payload["potential"], 3)
        if g[0] != 0:
            raise SeedCheckFailure("GAUGE_NOT_FIXED")
        residual = [Fraction(a) - sum(x*y for x, y in zip(row, g)) for a, row in zip(c, edges)]
        compare(payload["residual"], residual)
        if any(residual):
            raise SeedCheckFailure("NONZERO_RESIDUAL")
        return wire(dict(original=c, d0=edges, potential=g, residual=residual))
    return _DISPATCH_MISS


def _check_filled_triangle(seed_id, payload):
    if seed_id == "DEMO_13":
        if set(payload) != {"potential","dual","d1_cochain","classification","repair_claim"}:
            raise SeedCheckFailure("FILLED_TRIANGLE_WITNESS_FIELDS")
        if vector(payload["potential"],3)[0] != 0:
            raise SeedCheckFailure("GAUGE_NOT_FIXED")
        compare(payload["d1_cochain"],[Fraction(-1)])
        compare(payload["classification"],"NONCLOSED_NOT_H1_CLASS")
        compare(payload["repair_claim"],"OPTIMAL_NONZERO_RESIDUAL_NOT_EXACT_REPAIR")
        return wire(primal_dual({k:payload[k] for k in ("potential","dual")}, [1, 4, 2], [1, 2, 3],
                               [[-1, 1, 0], [-1, 0, 1], [0, -1, 1]]))
    return _DISPATCH_MISS


def _check_metric_and_bouquet(seed_id, payload):
    if seed_id == "DEMO_14":
        from pfp.infrastructure.pilot_runners.seed_core_checks import hodge_check
        return hodge_check(payload)
    if seed_id == "DEMO_23":
        if set(payload) != {"potential","dual","cycles","pairings","zero_repair"}:
            raise SeedCheckFailure("BOUQUET_WITNESS_FIELDS")
        if vector(payload["potential"],5)[0] != 0:
            raise SeedCheckFailure("GAUGE_NOT_FIXED")
        compare(payload["cycles"],[[1,1,1,0,0,0],[0,0,0,1,1,1]])
        compare(payload["pairings"],[Fraction(1),Fraction(2)])
        compare(payload["zero_repair"],"IMPOSSIBLE_NONZERO_CYCLE_PAIRINGS")
        return wire(primal_dual({k:payload[k] for k in ("potential","dual")}, [1,0,0,2,0,0], [1,2,3,5,7,11],
                               [[-1,1,0,0,0],[0,-1,1,0,0],[1,0,-1,0,0],[-1,0,0,1,0],[0,0,0,-1,1],[1,0,0,0,-1]]))
    return _DISPATCH_MISS


def check(seed_id: str, payload: dict) -> dict:
    if seed_id not in SEED_IDS:
        raise SeedCheckFailure("UNKNOWN_SEED")
    if type(payload) is not dict:
        raise SeedCheckFailure("CANDIDATE_NOT_OBJECT")
    result = _check_primary_special(seed_id, payload)
    if result is not _DISPATCH_MISS:
        return result
    result = _check_exact_potential(seed_id, payload)
    if result is not _DISPATCH_MISS:
        return result
    result = _check_filled_triangle(seed_id, payload)
    if result is not _DISPATCH_MISS:
        return result
    result = _check_metric_and_bouquet(seed_id, payload)
    if result is not _DISPATCH_MISS:
        return result
    expected = review_expected(seed_id) if seed_id in REVIEW_IDS else mss_expected(int(seed_id[5:]))
    # SymPy integers are host computations, not candidate coercions.
    expected = _native(expected)
    compare(payload, expected)
    return wire(expected)


def _native(value):
    if isinstance(value, sp.Integer):
        return int(value)
    if type(value) is dict:
        return {k: _native(v) for k, v in value.items()}
    if type(value) is list:
        return [_native(v) for v in value]
    return value


def attachment_expected():
    """Replay one finite face attachment under two explicit local policies."""
    import json
    from copy import deepcopy
    from hashlib import sha256
    d1=boundary([tuple(e) for e in ("ab","ac","bc")],[(v,) for v in "abc"])
    face=[1,-1,1]
    if sp.Matrix(d1)*sp.Matrix(face) != sp.zeros(3,1):
        raise SeedCheckFailure("ATTACHMENT_BOUNDARY_INVALID")
    before=dict(vertices=list("abc"), edges=[list(e) for e in ("ab","ac","bc")], faces=[])
    event=dict(kind="attach_face", vertices=list("abc"), boundary=face)
    records=[]
    for allow in (False,True):
        state=deepcopy(before)
        if allow:
            state["faces"].append(event["vertices"])
        parent=sha256(json.dumps(before,sort_keys=True).encode()).hexdigest()
        records.append(dict(policy={"attach_face":allow}, witness_boundary=face,
                            boundary_of_boundary=[0,0,0], before=before, after=state,
                            executed_events=[event] if allow else [],
                            terminal="APPLIED" if allow else "POLICY_VIOLATION", parent_digest=parent,
                            state_digest=sha256(json.dumps(state,sort_keys=True).encode()).hexdigest()))
    return dict(denied=records[0], permitted=records[1], authority_effect="None")


def _seed_rational_schema():
    return {'oneOf': [{'type': 'integer'}, {'type': 'string', 'pattern': '^-?\\d+(?:/\\d+)?$'}]}


def _seed_value_schema(value, rational_schema):
    if isinstance(value, Fraction):
        return rational_schema
    if type(value) is dict:
        return dict(type='object', additionalProperties=False, properties={k: _seed_value_schema(v, rational_schema) for k, v in value.items()}, required=list(value))
    if type(value) is list:
        if not value:
            return dict(type='array', minItems=0, maxItems=0)
        return dict(type='array', prefixItems=[_seed_value_schema(v, rational_schema) for v in value], minItems=len(value), maxItems=len(value))
    return {'type': {int: 'integer', bool: 'boolean', str: 'string', type(None): 'null'}[type(value)]}


def _seed_vector_schema(n, rational_schema):
    return dict(type='array', items=rational_schema, minItems=n, maxItems=n)


def _seed_object_schema(properties):
    return dict(type='object', additionalProperties=False, properties=properties, required=list(properties))


def _seed_primary_candidate_schema(seed_id, rational_schema):
    if seed_id == 'DEMO-N08':
        return _seed_object_schema(dict(potential=_seed_vector_schema(3, rational_schema), dual=_seed_vector_schema(3, rational_schema), after_face=_seed_object_schema(dict(d0=_seed_value_schema(cycle_incidence(3), rational_schema), cochain=_seed_vector_schema(3, rational_schema), face_boundary=_seed_value_schema([1, 1, 1], rational_schema), potential=_seed_vector_schema(3, rational_schema), dual=_seed_vector_schema(3, rational_schema)))))
    if seed_id in {'DEMO_07', 'DEMO_08'}:
        n = 2 if seed_id == 'DEMO_07' else 3
        return _seed_object_schema(dict(potential=_seed_vector_schema(3, rational_schema), d0=_seed_value_schema([[0] * 3] * n, rational_schema), original=_seed_vector_schema(n, rational_schema), residual=_seed_vector_schema(n, rational_schema)))
    if seed_id == 'DEMO_13':
        return _seed_object_schema(dict(potential=_seed_vector_schema(3, rational_schema), dual=_seed_vector_schema(3, rational_schema), d1_cochain=_seed_vector_schema(1, rational_schema), classification={'type': 'string'}, repair_claim={'type': 'string'}))
    if seed_id == 'DEMO_14':
        return _seed_object_schema(dict(potential=_seed_vector_schema(3, rational_schema), harmonic=_seed_vector_schema(3, rational_schema), face_potential=_seed_vector_schema(1, rational_schema), d0_adjoint=_seed_value_schema([[Fraction(0)] * 3] * 3, rational_schema), d1_adjoint=_seed_value_schema([[Fraction(0)]] * 3, rational_schema), comparison={'type': 'string'}))
    if seed_id == 'DEMO_23':
        return _seed_object_schema(dict(potential=_seed_vector_schema(5, rational_schema), dual=_seed_vector_schema(6, rational_schema), cycles=_seed_value_schema([[0] * 6] * 2, rational_schema), pairings=_seed_vector_schema(2, rational_schema), zero_repair={'type': 'string'}))
    return None


def _seed_channel_matrix_schema(n, scalar):
    return dict(type='array', items=dict(type='array', items=scalar, minItems=n, maxItems=n), minItems=n, maxItems=n)


def _seed_quantum_or_lean_schema(seed_id, rational_schema):
    if seed_id == 'DEMO-Q22':
        scalar = dict(type='array', items=rational_schema, minItems=2, maxItems=2)
        return _seed_object_schema(dict(kraus=dict(type='array', items=_seed_channel_matrix_schema(2, scalar), minItems=1, maxItems=8), density=_seed_channel_matrix_schema(4, scalar), marginal_first=_seed_channel_matrix_schema(2, scalar), marginal_second=_seed_channel_matrix_schema(2, scalar), output=_seed_channel_matrix_schema(4, scalar), remote_after=_seed_channel_matrix_schema(2, scalar), branch_index={'type': 'integer'}, branch_probability=rational_schema, branch_remote={'oneOf': [_seed_channel_matrix_schema(2, scalar), {'type': 'string'}]}, factor_order=_seed_value_schema([''] * 4, rational_schema)))
    if seed_id == 'DEMO_20':
        return _seed_object_schema(dict(source={'type': 'string', 'description': 'Lean module in namespace PfpSeed20: inductive Bit with constructors zero and one; def flip : Bit -> Bit swaps the constructors; theorem double_flip : forall x : Bit, flip (flip x) = x; close with end PfpSeed20. Supply the proof and no new axioms.'}, source_sha256={'type': 'string'}, toolchain_pin={'type': 'string'}, single_flip_counterexample=_seed_object_schema(dict(input={'type': 'string'}, output={'type': 'string'}))))
    return None


def seed_candidate_schema(seed_id: str) -> dict:
    """Expose witness types without including reference answers in prompts."""
    rational_schema = _seed_rational_schema()
    primary = _seed_primary_candidate_schema(seed_id, rational_schema)
    if primary is not None:
        return primary
    if seed_id == 'DEMO-N15':
        return _seed_value_schema(attachment_expected(), rational_schema)
    special = _seed_quantum_or_lean_schema(seed_id, rational_schema)
    if special is not None:
        return special
    return _seed_value_schema(_native(review_expected(seed_id) if seed_id in REVIEW_IDS else mss_expected(int(seed_id[5:]))), rational_schema)
