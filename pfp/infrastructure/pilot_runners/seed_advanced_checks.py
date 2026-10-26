"""Exact deciding witnesses for the advanced, source-declared MSS seed tasks.

These checks reuse the existing seed evaluator and Pauli/Lean owners. Large
tensor and bilinear tasks use the symbolic constructions expressly permitted
by their seeds; no claimed exponential table enumeration is substituted for
those constructions. A valid obstruction certificate is not a successful
repair of the original task. AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from itertools import combinations, product
from typing import Any

import sympy as sp

from ...domain.quantum.pauli import PauliString


def _plain(value: Any) -> Any:
    if isinstance(value, sp.Integer):
        return int(value)
    if isinstance(value, sp.Rational):
        return Fraction(int(value.p), int(value.q))
    if isinstance(value, sp.MatrixBase):
        return _plain(value.tolist())
    if type(value) in (list, tuple):
        return [_plain(x) for x in value]
    if type(value) is dict:
        return {k: _plain(v) for k, v in value.items()}
    return value


def _complex(value: Any) -> list[Fraction]:
    value = sp.expand(value)
    return [Fraction(sp.re(value)), Fraction(sp.im(value))]


def _complex_matrix(matrix: sp.MatrixBase) -> list:
    return [[_complex(value) for value in row] for row in matrix.tolist()]


def _simplicial(maximal: tuple[tuple, ...]) -> tuple[list, list, list, sp.Matrix, sp.Matrix]:
    vertices = sorted({v for face in maximal for v in face})
    edges = sorted({edge for face in maximal for edge in combinations(face, 2)})
    faces = sorted({face for cell in maximal for face in combinations(cell, 3)})
    b1 = sp.zeros(len(vertices), len(edges))
    b2 = sp.zeros(len(edges), len(faces))
    vi, ei = {v: i for i, v in enumerate(vertices)}, {e: i for i, e in enumerate(edges)}
    for j, (a, b) in enumerate(edges):
        b1[vi[a], j], b1[vi[b], j] = -1, 1
    for j, face in enumerate(faces):
        for i in range(3):
            b2[ei[face[:i] + face[i + 1:]], j] = (-1) ** i
    return vertices, edges, faces, b1, b2


def _sphere() -> dict:
    vertices, edges, faces, b1, b2 = _simplicial((tuple("abcd"),))
    cycle = sp.Matrix([-1, 1, -1, 1])
    cochain = sp.Matrix([1, 0, 0, 0])
    return dict(vertices=vertices, edges=edges, faces=faces, d0=b1.T, d1=b2.T,
                cycle=list(cycle), cycle_boundary=list(b2 * cycle),
                double_differential=b2.T * b1.T,
                input=list(cochain), protected_pairing=(cochain.T * cycle)[0],
                admitted_three_cells=[], exact_repair="OBSTRUCTED")


def _group_cocycle() -> dict:
    group = list(product((0, 1), repeat=2))
    add = lambda g, h: tuple(a ^ b for a, b in zip(g, h))
    alpha = lambda g, h: g[1] * h[0]
    table = [[alpha(g, h) for h in group] for g in group]
    residuals = [alpha(h, k) ^ alpha(add(g, h), k) ^ alpha(g, add(h, k)) ^ alpha(g, h)
                 for g, h, k in product(group, repeat=3)]
    rephasings = []
    for tail in product((0, 1), repeat=3):
        lam = dict(zip(group, (0, *tail)))
        if all(alpha(g, h) ^ lam[g] ^ lam[h] ^ lam[add(g, h)] == 0
               for g, h in product(group, repeat=2)):
            rephasings.append(list(lam.values()))
    commutators = [[(-1) ** (alpha(g, h) ^ alpha(h, g)) for h in group] for g in group]
    return dict(group=group, alpha=table, cocycle_residuals=residuals,
                commutator_phases=commutators, normalized_rephasings=rephasings,
                tested_normalized_one_cochains=8, cancellation_target="ORDERED_PAIR_PHASES")


def _unitary() -> dict:
    a, b = (1 - sp.I) / 2, (1 + sp.I) / 2
    unitary = a * sp.Matrix([[1, 1], [1, -1]])
    probes = [sp.Matrix(v) for v in ([1, 0], [0, 1], [b, b], [b, -b])]
    readout = lambda v: [Fraction(sp.simplify(x * sp.conjugate(x))) for x in v]
    before, after = [readout(v) for v in probes], [readout(unitary * v) for v in probes]
    permutations = [p for p in ((0, 1), (1, 0))
                    if all([row[p[0]], row[p[1]]] == out for row, out in zip(before, after))]
    return dict(unitary=_complex_matrix(unitary), gram=_complex_matrix(unitary.H * unitary),
                probes=[_complex_matrix(v) for v in probes], original_readouts=before,
                transported_readouts=after, common_coordinate_permutations=permutations,
                scalar_profile="Q(i)")


def _bell() -> dict:
    a, b = (1 + sp.I) / 2, (1 - sp.I) / 2
    amplitudes = sp.diag(a, b)
    return dict(amplitude_matrix=_complex_matrix(amplitudes),
                determinant=_complex(amplitudes.det()), schmidt_rank=int(amplitudes.rank()),
                norm_squared=Fraction(sp.simplify(sp.trace(amplitudes * amplitudes.H))),
                marginal_A=_complex_matrix(amplitudes * amplitudes.H),
                marginal_B=_complex_matrix(amplitudes.T * amplitudes.conjugate()),
                product_factorization="OBSTRUCTED_BY_NONZERO_2X2_MINOR")


def _instrument() -> dict:
    p0, p1, rho = sp.diag(1, 0), sp.diag(0, 1), sp.diag(1, 0)
    aa, bb = [p * rho * p for p in (p0, p1)], [p * rho * p for p in (p1, p0)]
    return dict(input=rho, branches_A=aa, branches_B=bb,
                probabilities_A=[sp.trace(x) for x in aa], probabilities_B=[sp.trace(x) for x in bb],
                sum_A=aa[0] + aa[1], sum_B=bb[0] + bb[1],
                protected_label=0, inverse_without_labels="NON_DESCENT")


def _pr_box() -> dict:
    settings = list(product((0, 1), repeat=2))
    tables = [[[Fraction(1, 2) if a ^ b == x * y else Fraction(0)
                for b in (0, 1)] for a in (0, 1)] for x, y in settings]
    support = [list(bits) for bits in product((0, 1), repeat=4)
               if all(bits[x] ^ bits[2 + y] == x * y for x, y in settings)]
    incidence = [[int(v == x) ^ int(v == 2 + y) for v in range(4)] for x, y in settings]
    cochain = [x * y for x, y in settings]
    global_potentials = [list(bits) for bits in product((0, 1), repeat=4)
                         if all(sum(a * b for a, b in zip(row, bits)) % 2 == c
                                for row, c in zip(incidence, cochain))]
    return dict(settings=settings, tables=tables,
                Alice_marginals=[[sum(row) for row in table] for table in tables],
                Bob_marginals=[[sum(table[a][b] for a in (0, 1)) for b in (0, 1)] for table in tables],
                globally_supported_assignments=support, predetermined_assignment_count=16,
                d0=incidence, cochain=cochain, cycle=[1] * 4,
                cycle_pairing=sum(cochain) % 2, exact_potentials=global_potentials)


def _pauli_product(words: list[str]) -> tuple[int, str]:
    result, phase = PauliString.identity(len(words[0])), 0
    for word in words:
        part, result = result.multiply(PauliString(word))
        phase = (phase + part) % 4
    return phase, result.word


def _magic_square() -> dict:
    square = [["XI", "IX", "XX"], ["IZ", "ZI", "ZZ"], ["XZ", "ZX", "YY"]]
    contexts = square + [[square[i][j] for i in range(3)] for j in range(3)]
    products = [_pauli_product(words) for words in contexts]
    commutation = [[PauliString(a).commutes_with(PauliString(b))
                    for a, b in combinations(words, 2)] for words in contexts]
    incidence = [[int(k // 3 == i) for k in range(9)] for i in range(3)] + [
        [int(k % 3 == j) for k in range(9)] for j in range(3)]
    signs = [phase // 2 for phase, _ in products]
    solutions = [list(bits) for bits in product((0, 1), repeat=9)
                 if all(sum(x * y for x, y in zip(row, bits)) % 2 == bit
                        for row, bit in zip(incidence, signs))]
    return dict(observables=square, context_commutation=commutation, products=products,
                d0=incidence, cochain=signs, dual=[1] * 6,
                dual_constraint=[sum(row[i] for row in incidence) % 2 for i in range(9)],
                protected_pairing=sum(signs) % 2, global_value_assignments=solutions,
                tested_assignments=512)


def _three_qubit() -> dict:
    stabilizers = ["ZZI", "IZZ"]
    errors = ["III", "XII", "IXI", "IIX", "ZII"]
    syndromes = [[int(not PauliString(error).commutes_with(PauliString(s))) for s in stabilizers]
                 for error in errors]
    group = [_pauli_product(words) for words in (["III"], ["ZZI"], ["IZZ"], stabilizers)]
    # On the two basis codewords, I and Z1 share syndrome but have distinct
    # relative phases. This decides the all-code-state recovery request.
    return dict(stabilizers=stabilizers, generator_commutes=PauliString(stabilizers[0]).commutes_with(PauliString(stabilizers[1])),
                stabilizer_group=group, errors=errors, syndromes=syndromes,
                code_basis=["000", "111"], indistinguishable_errors=["III", "ZII"],
                logical_action_I=[1, 1], logical_action_Z1=[1, -1],
                recovery_for_entire_error_set="OBSTRUCTED")


def _torus(n: int) -> dict:
    vertices = list(product(range(n), repeat=2))
    edges = [(kind, i, j) for kind in ("h", "t") for i, j in vertices]
    index = {edge: k for k, edge in enumerate(edges)}
    vertex_index = {v: i for i, v in enumerate(vertices)}
    stars = [[] for _ in vertices]
    for k, (kind, i, j) in enumerate(edges):
        other = ((i + 1) % n, j) if kind == "h" else (i, (j + 1) % n)
        stars[vertex_index[(i, j)]].append(k)
        stars[vertex_index[other]].append(k)
    faces = [[index[edge] for edge in (("h", i, j), ("t", (i + 1) % n, j),
                                     ("h", i, (j + 1) % n), ("t", i, j))] for i, j in vertices]
    horizontal = [index[("h", i, 0)] for i in range(n)]
    vertical = [index[("t", 0, j)] for j in range(n)]
    dual_h = [index[("h", n - 1, j)] for j in range(n)]
    dual_v = [index[("t", i, n - 1)] for i in range(n)]
    pairing = lambda left, right: len(set(left) & set(right)) % 2
    return dict(vertices=vertices, edges=edges, vertex_stars=stars, face_boundaries=faces,
                horizontal_cycle=horizontal, vertical_cycle=vertical,
                dual_horizontal=dual_h, dual_vertical=dual_v,
                logical_pairings=[[pairing(c, q) for q in (dual_h, dual_v)] for c in (horizontal, vertical)],
                cycle_boundaries=[[pairing(c, s) for s in stars] for c in (horizontal, vertical)],
                dual_on_faces=[[pairing(q, f) for f in faces] for q in (dual_h, dual_v)],
                css_commutators=[[pairing(s, f) for f in faces] for s in stars])


def _mask(support: list[int]) -> int:
    return sum(1 << i for i in support)


def _toric_errors() -> dict:
    torus = _torus(3)
    stabilizer_span = {0}
    for face in torus["face_boundaries"]:
        word = _mask(face)
        stabilizer_span |= {existing ^ word for existing in tuple(stabilizer_span)}
    supports = [list(s) for weight in (0, 1, 2) for s in combinations(range(18), weight)]
    grouped: dict[tuple, list] = {}
    for support in supports:
        syndrome = tuple(len(set(support) & set(star)) % 2 for star in torus["vertex_stars"])
        grouped.setdefault(syndrome, []).append(support)
    ambiguous = []
    for syndrome, values in sorted(grouped.items()):
        for left, right in combinations(values, 2):
            difference = _mask(left) ^ _mask(right)
            if difference not in stabilizer_span:
                support = [i for i in range(18) if difference & (1 << i)]
                ambiguous.append(dict(left=left, right=right, syndrome=list(syndrome),
                                      difference=support, logical_pairings=[
                                          len(set(support) & set(torus[key])) % 2
                                          for key in ("dual_horizontal", "dual_vertical")]))
    return dict(carrier=torus, admitted_error_count=len(supports),
                stabilizer_subgroup_size=len(stabilizer_span),
                equal_syndrome_nonstabilizer_pair_count=len(ambiguous),
                first_obstruction=ambiguous[0], generator_phases=[0] * 18,
                all_error_recovery="OBSTRUCTED")


def _three_copies() -> dict:
    torus = _torus(3)
    cells = {copy: [f"{copy}:{kind}({i},{j})" for kind, i, j in torus["edges"]]
             for copy in "ABC"}
    return dict(carrier=torus, source_edges=cells,
                source_vertices={copy: [f"{copy}:v({i},{j})" for i, j in torus["vertices"]] for copy in "ABC"},
                source_faces={copy: [f"{copy}:f({i},{j})" for i, j in torus["vertices"]] for copy in "ABC"},
                named_vertex_stars={copy: [[cells[copy][i] for i in star] for star in torus["vertex_stars"]] for copy in "ABC"},
                named_face_boundaries={copy: [[cells[copy][i] for i in face] for face in torus["face_boundaries"]] for copy in "ABC"},
                protected_cycle_pairings={copy: torus["logical_pairings"] for copy in "ABC"},
                proposed_coarse_edge_count=len(set(edge.split(":", 1)[1] for group in cells.values() for edge in group)),
                source_edge_count=sum(map(len, cells.values())),
                first_assembler_collision=[cells["A"][0], cells["B"][0]],
                simultaneous_erasure="OBSTRUCTED_BY_THREE_NAMED_PAIRINGS")


def _shear(n: int) -> sp.Matrix:
    result = sp.eye(n)
    for i in range(n - 1):
        result[i + 1, :] += result[i, :]
    result[0, :] += result[n - 1, :]
    return result


def _sheared(integral: bool) -> dict:
    dims = (3, 6, 3) if integral else (3, 7, 3)
    d0, d1 = sp.zeros(dims[1], dims[0]), sp.zeros(dims[2], dims[1])
    for i in range(3):
        d0[i, i] = 1
    for i, value in enumerate((2, 3) if integral else (1, 1, 1)):
        d1[i, i + 3] = value
    shears = [_shear(n) for n in dims]
    inverses = [s.inv() for s in shears]
    cochain = sp.Matrix([1, 1, 1]) if integral else sp.eye(7)[:, 6]
    stored = inverses[2 if integral else 1] * cochain
    result = dict(coefficient_profile="Z" if integral else "Q", dimensions=list(dims),
                  shears=shears, inverse_shears=inverses,
                  transported_d0=inverses[1] * d0 * shears[0],
                  transported_d1=inverses[2] * d1 * shears[1],
                  original_input=list(cochain), stored_input=list(stored),
                  double_differential=d1 * d0)
    if integral:
        result.update(divisibility_moduli=[2, 3], residues=[1 % 2, 1 % 3],
                      protected_free_coordinate=1, rational_repair="STILL_OBSTRUCTED_BY_FREE_COORDINATE",
                      integral_repair="OBSTRUCTED")
    else:
        dual = sp.zeros(1, 7)
        dual[0, 6] = 1
        result.update(stored_dual=dual * shears[1], dual_on_repairs=dual * d0,
                      protected_pairing=(dual * cochain)[0], exact_repair="OBSTRUCTED")
    return result


def _wedge() -> dict:
    tetrahedra = [tuple("oabc"), tuple("odef")]
    # The declared order places o first; index labels encode that order exactly.
    ordered = [(0, 1, 2, 3), (0, 4, 5, 6)]
    vertices, edges, faces, b1, b2 = _simplicial(tuple(ordered))
    cycles = []
    for tetrahedron in ordered:
        chain = sp.zeros(len(faces), 1)
        for i in range(4):
            chain[faces.index(tetrahedron[:i] + tetrahedron[i + 1:])] = (-1) ** i
        cycles.append(chain)
    c = sp.zeros(len(faces), 1)
    c[faces.index((0, 1, 2))], c[faces.index((0, 4, 5))] = 1, 2
    pairings = [(c.T * cycle)[0] for cycle in cycles]
    return dict(vertex_labels=list("oabcdef"), tetrahedron_labels=tetrahedra,
                vertices=vertices, edges=edges, faces=faces, d0=b1.T, d1=b2.T,
                input=list(c), sphere_cycles=[list(x) for x in cycles],
                cycle_boundaries=[list(b2 * x) for x in cycles], protected_pairings=pairings,
                coarse_sum=sum(pairings), coarse_question_kernel=[1, -1],
                admitted_three_cells=[], exact_repair="OBSTRUCTED")


def _rp2() -> dict:
    from sympy.matrices.normalforms import smith_normal_form

    faces = tuple(tuple(int(x) for x in text) for text in
                  ("123", "124", "135", "146", "156", "236", "245", "256", "345", "346"))
    vertices, edges, faces, b1, b2 = _simplicial(faces)
    d1 = b2.T
    smith = smith_normal_form(d1, domain=sp.ZZ)
    c = sp.eye(len(faces))[:, 0]
    solution, parameters = d1.gauss_jordan_solve(2 * c)
    doubled_repair = solution.subs({p: 0 for p in parameters})
    mod_two_cycle = [1] * len(faces)
    return dict(vertices=vertices, edges=edges, faces=faces, integral_d0=b1.T, integral_d1=d1,
                double_differential=d1 * b1.T, input=list(c),
                smith_diagonal=[abs(smith[i, i]) for i in range(min(smith.shape))],
                doubled_input_repair=list(doubled_repair),
                doubled_input_reconstruction=list(d1 * doubled_repair),
                mod_two_cycle=mod_two_cycle,
                mod_two_cycle_boundary=[int(x) % 2 for x in b2 * sp.Matrix(mod_two_cycle)],
                mod_two_pairing=int(sum(c)) % 2,
                integral_repair="OBSTRUCTED_BY_MOD_TWO_PAIRING",
                F2_repair="OBSTRUCTED_BY_FUNDAMENTAL_CYCLE")


def _graded_algebra() -> dict:
    # Multiplication tensors on basis (1,a,b,s), retaining every basis product.
    tables = []
    for nonzero in (True, False):
        table = [[[0] * 4 for _ in range(4)] for _ in range(4)]
        for i in range(4):
            table[0][i][i], table[i][0][i] = 1, 1
        if nonzero:
            table[1][2][3], table[2][1][3] = 1, -1
        tables.append(table)
    associators = []
    for table in tables:
        residuals = []
        for i, j, k, out in product(range(4), repeat=4):
            residuals.append(sum(table[i][j][m] * table[m][k][out] -
                                 table[j][k][m] * table[i][m][out] for m in range(4)))
        associators.append(sum(x != 0 for x in residuals))
    return dict(basis=["1", "a", "b", "s"], degrees=[0, 1, 1, 2], multiplication_T=tables[0],
                multiplication_W=tables[1], nonzero_associator_counts=associators,
                positive_degree_product_ranks=[int(sp.Matrix([table[i][j] for i, j in product(range(1, 4), repeat=2)]).rank()) for table in tables],
                zero_differential=[[0, 0]],
                protected_s_pairing=1, graded_isomorphism="OBSTRUCTED_BY_PRODUCT_RANK",
                exact_s_repair="OBSTRUCTED_BY_ZERO_DIFFERENTIAL")


@lru_cache(maxsize=1)
def _tensor_circle() -> dict:
    # Expand every degree-three tensor differential. Each term is computed from
    # the factor incidence and Koszul prefix degree, rather than a page label.
    factor = [[-1, 1, 0], [0, -1, 1], [1, 0, -1]]
    bases = [[(degrees, indices) for degrees in product((0, 1), repeat=3) if sum(degrees) == k
              for indices in product(range(3), repeat=3)] for k in range(4)]
    maps = []
    for k in range(3):
        index = {cell: i for i, cell in enumerate(bases[k + 1])}
        matrix = sp.zeros(len(bases[k + 1]), len(bases[k]))
        for col, (degrees, indices) in enumerate(bases[k]):
            for axis in range(3):
                if degrees[axis]:
                    continue
                for edge in range(3):
                    next_degrees, next_indices = list(degrees), list(indices)
                    next_degrees[axis], next_indices[axis] = 1, edge
                    matrix[index[(tuple(next_degrees), tuple(next_indices))], col] += (
                        (-1) ** sum(degrees[:axis]) * factor[edge][indices[axis]])
        maps.append(matrix)
    cycle = sp.ones(len(bases[3]), 1)
    input_index = bases[3].index(((1, 1, 1), (0, 0, 0)))
    ranks = [int(matrix.rank()) for matrix in maps]
    betti = [len(basis) - (ranks[k - 1] if k else 0) - (ranks[k] if k < 3 else 0)
             for k, basis in enumerate(bases)]
    return dict(factor_d0=factor, factor_count=3, basis_order="lex(degrees,indices)",
                koszul_prefix_axes=[[], [0], [0, 1]], dimensions=[len(x) for x in bases],
                differential_ranks=ranks, cohomology_dimensions=betti,
                double_differential_nonzero_counts=[sum(x != 0 for x in maps[i + 1] * maps[i]) for i in (0, 1)],
                input_top_basis_index=input_index, protected_cycle_coefficients=[1] * 27,
                cycle_on_repair_image=list((cycle.T * maps[2]).T), protected_pairing=1,
                exact_repair="OBSTRUCTED")


def _filtered() -> dict:
    tensor = _tensor_circle()
    return dict(base_differential=[[1], [0]], filtration_indices={"x": 0, "y": 2, "z": 3},
                tensor=tensor, E1_torus_multiplicities=tensor["cohomology_dimensions"],
                d1_ranks=[0] * 4, d2_ranks=tensor["cohomology_dimensions"],
                d2_source="x", d2_target="y", d2_filtration_jump=2,
                E3_surviving_base="z", input_components=["y", "z"],
                exact_input_component="y", protected_z_pairing=1,
                all_initial_page_classes_survive="OBSTRUCTED_BY_NONZERO_D2",
                exact_repair="OBSTRUCTED_BY_Z_COMPONENT")


def _cross_polytopes() -> dict:
    certificates = []
    for n in range(2, 9):
        facet_signs = list(product((-1, 1), repeat=n + 1))
        coefficients = [sp.prod(signs) for signs in facet_signs]
        ridges: dict[tuple, int] = {}
        for signs, coefficient in zip(facet_signs, coefficients):
            facet = tuple(enumerate(signs))
            for deleted in range(n + 1):
                ridge = facet[:deleted] + facet[deleted + 1:]
                ridges[ridge] = ridges.get(ridge, 0) + coefficient * (-1) ** deleted
        certificates.append(dict(dimension=n, vertex_count=2 * (n + 1), facet_count=len(facet_signs),
                                 ridge_count=len(ridges), nonzero_boundary_ridges=sum(v != 0 for v in ridges.values()),
                                 facet_basis_order="lex(signs), with -1 before +1 and increasing axis orientation",
                                 facet_coefficients=coefficients,
                                 ridge_basis_order="lex(tuple(axis,sign)); omitted axis identifies each ridge",
                                 nonzero_ridge_boundary_terms=[dict(vertices=ridge, coefficient=value)
                                                               for ridge, value in sorted(ridges.items()) if value],
                                 input_facet_signs=[1] * (n + 1), input_coefficient=1,
                                 cycle_coefficient_recipe="product(facet_vertex_signs)",
                                 orientation_recipe="increasing_axis_index", protected_pairing=coefficients[-1]))
    return dict(dimensions=certificates, enumeration_scope="TOP_FACETS_AND_RIDGES_ONLY",
                barycentric_subdivision="REQUIRES_EXPLICIT_TRANSPORT_BEFORE_ADMISSION",
                exact_repairs="OBSTRUCTED_BY_INDIVIDUAL_FUNDAMENTAL_PAIRINGS")


def _pauli_representative(bits: list[int]) -> tuple[int, str]:
    r = len(bits) // 2
    a, b = bits[:r], bits[r:]
    word = "".join("Y" if x and z else "X" if x else "Z" if z else "I" for x, z in zip(a, b))
    return 3 * sum(x * z for x, z in zip(a, b)) % 4, word


def _pauli_cocycle_product(left: list[int], right: list[int]) -> dict:
    phase_l, word_l = _pauli_representative(left)
    phase_r, word_r = _pauli_representative(right)
    phase_product, word_product = PauliString(word_l).multiply(PauliString(word_r))
    summed = [x ^ y for x, y in zip(left, right)]
    phase_sum, word_sum = _pauli_representative(summed)
    r = len(left) // 2
    alpha = sum(left[r + i] * right[i] for i in range(r)) % 2
    return dict(left_bits=left, right_bits=right, left_phase_i=phase_l, right_phase_i=phase_r,
                left_word=word_l, right_word=word_r, product_word=word_product.word,
                product_phase_i=(phase_l + phase_r + phase_product) % 4,
                sum_bits=summed, sum_word=word_sum, sum_phase_i=phase_sum, alpha=alpha,
                phase_residual=(phase_l + phase_r + phase_product - phase_sum - 2 * alpha) % 4)


def _bilinear() -> dict:
    labels = list(product((0, 1), repeat=2))
    representatives = {bits: ((3 * bits[0] * bits[1]) % 4,
                             "Y" if bits == (1, 1) else "X" if bits[0] else "Z" if bits[1] else "I")
                       for bits in labels}
    products = []
    for left, right in product(labels, repeat=2):
        phase_l, word_l = representatives[left]
        phase_r, word_r = representatives[right]
        phase_p, word_p = PauliString(word_l).multiply(PauliString(word_r))
        total = tuple(a ^ b for a, b in zip(left, right))
        phase_total, word_total = representatives[total]
        residual = (phase_l + phase_r + phase_p - phase_total - 2 * left[1] * right[0]) % 4
        products.append(dict(left=list(left), right=list(right), product_word=word_p.word,
                             target_word=word_total, phase_residual=residual))
    dimensions = []
    for r in range(2, 9):
        alpha = [[int(i == r + j) for j in range(2 * r)] for i in range(2 * r)]
        commutator = [[alpha[i][j] ^ alpha[j][i] for j in range(2 * r)] for i in range(2 * r)]
        generators = [[int(i == j) for i in range(2 * r)] for j in range(2 * r)]
        words = [_pauli_representative(bits)[1] for bits in generators]
        actual_commutators, phase_residuals = [], []
        for i, left in enumerate(generators):
            row, residual_row = [], []
            for j, right in enumerate(generators):
                forward, reverse = _pauli_cocycle_product(left, right), _pauli_cocycle_product(right, left)
                row.append((forward["product_phase_i"] - reverse["product_phase_i"]) % 4)
                residual_row.append(forward["phase_residual"])
            actual_commutators.append(row)
            phase_residuals.append(residual_row)
        left, right = [0] * (2 * r), [0] * (2 * r)
        left[0] = left[r + 1] = right[1] = right[r] = 1
        dimensions.append(dict(r=r, group_bit_dimension=2 * r,
                               alpha_matrix=alpha, commutator_matrix=commutator,
                               generator_words=words, generator_phases_i=[0] * (2 * r),
                               actual_generator_commutators_i=actual_commutators,
                               generator_phase_law_residuals=phase_residuals,
                               source_basis_order="a_0..a_(r-1),b_0..b_(r-1)",
                               nontrivial_ordered_pair=[r, 0],
                               ordered_pair_alpha=alpha[r][0], reverse_pair_alpha=alpha[0][r],
                               commutator_phase=(-1) ** commutator[r][0],
                               cross_coordinate_product=_pauli_cocycle_product(left, right)))
    return dict(dimensions=dimensions,
                one_coordinate_representatives=[dict(bits=list(bits), phase_i=phase, word=word)
                                                for bits, (phase, word) in representatives.items()],
                one_coordinate_products=products,
                tensor_composition="SUM_COORDINATE_PHASES_MOD_4",
                cocycle_certificate="BILINEAR_EXPANSION_IN_F2",
                rephasing_obstruction="ABELIAN_ONE_COBOUNDARIES_ARE_SYMMETRIC")


def _shear_values(values: list, *, inverse: bool = False, dual: bool = False, modulus: int | None = None) -> list:
    """Execute the declared elementary shears on columns or covectors."""
    result = list(values)
    if len(result) < 2:
        raise ValueError("The declared elementary shear needs distinct first/last coordinates")
    normalize = (lambda value: value % modulus) if modulus else (lambda value: value)
    if dual:
        if inverse:
            for i in range(len(result) - 1):
                result[i] = normalize(result[i] - result[i + 1])
            result[-1] = normalize(result[-1] - result[0])
        else:
            result[-1] = normalize(result[-1] + result[0])
            for i in range(len(result) - 2, -1, -1):
                result[i] = normalize(result[i] + result[i + 1])
    elif inverse:
        result[0] = normalize(result[0] - result[-1])
        for i in range(len(result) - 2, -1, -1):
            result[i + 1] = normalize(result[i + 1] - result[i])
    else:
        for i in range(len(result) - 1):
            result[i + 1] = normalize(result[i + 1] + result[i])
        result[0] = normalize(result[0] + result[-1])
    return result


def _sparse(values: list) -> list:
    return [[i, value] for i, value in enumerate(values) if value != 0]


def _bits(values: Any, length: int) -> list[int]:
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    if type(values) is not list or len(values) != length or any(type(value) is not int or value not in (0, 1) for value in values):
        raise SeedCheckFailure("REQUIRED_EXACT_BINARY_VECTOR")
    return values


def _tensor_profiles(records: list[dict], degree: int) -> list:
    profiles, offset = [], 0
    for degrees in product(*(range(len(record["dimensions"])) for record in records)):
        if sum(degrees) != degree:
            continue
        shape = [record["dimensions"][d] for record, d in zip(records, degrees)]
        size = 1
        for n in shape:
            size *= n
        profiles.append((degrees, shape, offset, size))
        offset += size
    return profiles


def _tensor_top_differential(records: list[dict], degree: int, terms: list) -> list:
    """Apply the F2 tensor differential to actual sparse source coordinates."""
    source = _tensor_profiles(records, degree)
    target = _tensor_profiles(records, degree + 1)
    target_indices = {degrees: (shape, offset) for degrees, shape, offset, _ in target}
    result = [0] * sum(size for _, _, _, size in target)
    for flat, coefficient in terms:
        degrees, shape, offset, _ = next(profile for profile in source if profile[2] <= flat < profile[2] + profile[3])
        local, indices = flat - offset, [0] * len(shape)
        for axis in range(len(shape) - 1, -1, -1):
            local, indices[axis] = divmod(local, shape[axis])
        for axis, record in enumerate(records):
            if degrees[axis] + 1 == len(record["dimensions"]):
                continue
            differential = record["differentials"][degrees[axis]]
            next_degrees = list(degrees)
            next_degrees[axis] += 1
            next_shape, next_offset = target_indices[tuple(next_degrees)]
            for row, entries in enumerate(differential):
                value = entries[indices[axis]] * coefficient % 2
                if not value:
                    continue
                next_indices = list(indices)
                next_indices[axis] = row
                index = 0
                for n, item in zip(next_shape, next_indices):
                    index = index * n + item
                result[next_offset + index] ^= value
    return result


def _tensor_transport(records: list[dict], dimensions: list[int], potential_terms: list | None = None) -> dict:
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    degree = len(dimensions) - 1
    dimension, previous = dimensions[-1], dimensions[-2]
    terms = [[0, 1]] if potential_terms is None else potential_terms
    if (type(terms) is not list or len(terms) > 64 or
            any(type(term) is not list or len(term) != 2 or type(term[0]) is not int or
                not 0 <= term[0] < previous or type(term[1]) is not int or term[1] != 1 for term in terms) or
            [term[0] for term in terms] != sorted({term[0] for term in terms})):
        raise SeedCheckFailure("REQUIRED_SORTED_SPARSE_F2_POTENTIAL_WITH_AT_MOST_64_TERMS")
    input_values = [int(i == 0) for i in range(dimension)]
    factors = [record["top_cycle"] for record in records]
    dual = []
    for coefficients in product(*factors):
        coefficient = 1
        for value in coefficients:
            coefficient = coefficient * value % 2
        dual.append(coefficient)
    stored_input = _shear_values(input_values, inverse=True, modulus=2)
    stored_dual = _shear_values(dual, dual=True, modulus=2)
    restored_input = _shear_values(stored_input, modulus=2)
    restored_dual = _shear_values(stored_dual, dual=True, inverse=True, modulus=2)
    potential = [0] * previous
    for i, value in terms:
        potential[i] = value
    stored_potential = _shear_values(potential, inverse=True, modulus=2)
    original_differential = _tensor_top_differential(records, degree - 1, terms)
    transported_differential = _shear_values(original_differential, inverse=True, modulus=2)
    restored_potential = _shear_values(stored_potential, modulus=2)
    actual_stored_map_output = _shear_values(
        _tensor_top_differential(records, degree - 1, _sparse(restored_potential)), inverse=True, modulus=2)
    probes = sorted({0, 1, dimension // 2, dimension - 2, dimension - 1})
    return dict(dimension=dimension, potential_dimension=previous,
                tensor_basis_order="lex(degrees,indices), factor order fixed by factor_certificates",
                source_input_terms=_sparse(input_values), stored_input_terms=_sparse(stored_input),
                restored_input_terms=_sparse(restored_input), source_dual_factor_coefficients=factors,
                stored_dual_probes=[[i, stored_dual[i]] for i in probes],
                restored_dual_probes=[[i, restored_dual[i]] for i in probes],
                source_pairing=sum(x * y for x, y in zip(dual, input_values)) % 2,
                stored_pairing=sum(x * y for x, y in zip(stored_dual, stored_input)) % 2,
                nonzero_dual_roundtrip_residuals=sum(x != y for x, y in zip(restored_dual, dual)),
                source_potential_terms=terms, stored_potential_terms=_sparse(stored_potential),
                source_differential_terms=_sparse(original_differential),
                stored_differential_terms=_sparse(actual_stored_map_output),
                naturality_residual_terms=_sparse([x ^ y for x, y in zip(transported_differential, actual_stored_map_output)]),
                dual_on_source_differential=sum(x * y for x, y in zip(dual, original_differential)) % 2,
                dual_on_stored_differential=sum(x * y for x, y in zip(stored_dual, actual_stored_map_output)) % 2,
                control_scope="SPARSE_TRANSPORT_CONTROL_NOT_AN_EXACT_REPAIR")


def _css_phase_control(carrier: dict, x_selection: list[int], z_selection: list[int]) -> dict:
    n, edge_count = len(carrier["vertex_stars"]), len(carrier["edges"])
    _bits(x_selection, n)
    _bits(z_selection, n)
    x = [sum(bit * int(edge in support) for bit, support in zip(x_selection, carrier["vertex_stars"])) % 2 for edge in range(edge_count)]
    z = [sum(bit * int(edge in support) for bit, support in zip(z_selection, carrier["face_boundaries"])) % 2 for edge in range(edge_count)]
    x_word, z_word = "".join("X" if bit else "I" for bit in x), "".join("Z" if bit else "I" for bit in z)
    word_parts, phase = [], 0
    # The existing exact owner admits at most eight qubits. Tensor-block
    # multiplication preserves its phase law without introducing another owner.
    for start in range(0, edge_count, 8):
        block_phase, block_word = PauliString(x_word[start:start + 8]).multiply(PauliString(z_word[start:start + 8]))
        phase, word_parts = (phase + block_phase) % 4, word_parts + [block_word.word]
    word = "".join(word_parts)
    predicted_phase = 3 * sum(a * b for a, b in zip(x, z)) % 4
    return dict(X_selection=x_selection, Z_selection=z_selection, X_support=[i for i, value in enumerate(x) if value],
                Z_support=[i for i, value in enumerate(z) if value], product_word=word,
                product_phase_i=phase, Y_count=word.count("Y"), phase_form_residual=(phase - predicted_phase) % 4)


def _css_phase_data(carrier: dict) -> dict:
    overlaps = [[len(set(star) & set(face)) for face in carrier["face_boundaries"]] for star in carrier["vertex_stars"]]
    count = len(overlaps)
    selection_x = [int(i in (0, 1, 5)) for i in range(count)]
    selection_z = [int(i in (0, 1, 6)) for i in range(count)]
    return dict(generator_overlap_counts=overlaps,
                generator_commutator_phases_i=[[2 * overlap % 4 for overlap in row] for row in overlaps],
                generator_XZ_product_phases_i=[[3 * overlap % 4 for overlap in row] for row in overlaps],
                X_support_matrix=[[int(edge in support) for edge in range(len(carrier["edges"]))] for support in carrier["vertex_stars"]],
                Z_support_matrix=[[int(edge in support) for edge in range(len(carrier["edges"]))] for support in carrier["face_boundaries"]],
                selected_generator_product=_css_phase_control(carrier, selection_x, selection_z),
                phase_scope="ARBITRARY_BINARY_GENERATOR_SELECTION_VIA_XOR_SUPPORT_AND_ACTUAL_Y_COUNT")


def _css_transport(carrier: dict) -> dict:
    vertices, edges = len(carrier["vertices"]), len(carrier["edges"])
    boundary = sp.Matrix([[int(edge in star) for edge in range(edges)] for star in carrier["vertex_stars"]])
    faces = sp.Matrix([[int(edge in face) for face in carrier["face_boundaries"]] for edge in range(edges)])
    s_edges, s_vertices = _shear(edges), _shear(vertices)
    stored_boundary, stored_faces = s_vertices.inv() * boundary * s_edges, s_edges.inv() * faces * s_vertices
    cycles = [[int(i in carrier[key]) for i in range(edges)] for key in ("horizontal_cycle", "vertical_cycle")]
    duals = [[int(i in carrier[key]) for i in range(edges)] for key in ("dual_horizontal", "dual_vertical")]
    stored_cycles = [_shear_values(cycle, inverse=True, modulus=2) for cycle in cycles]
    stored_duals = [_shear_values(dual, dual=True, modulus=2) for dual in duals]
    return dict(stored_cycles=stored_cycles, stored_duals=stored_duals,
                stored_cycle_boundaries=[[int(x) % 2 for x in stored_boundary * sp.Matrix(cycle)] for cycle in stored_cycles],
                stored_duals_on_faces=[[int(x) % 2 for x in sp.Matrix([dual]) * stored_faces] for dual in stored_duals],
                stored_logical_pairings=[[sum(x * y for x, y in zip(cycle, dual)) % 2 for dual in stored_duals] for cycle in stored_cycles],
                consecutive_map_nonzero_count=sum(int(x) % 2 != 0 for x in stored_boundary * stored_faces),
                restored_cycles=[_shear_values(cycle, modulus=2) for cycle in stored_cycles])


def _composite() -> dict:
    sphere, rp2, css = _sphere(), _rp2(), _torus(5)
    circle_d0 = [[1, 1, 0], [0, 1, 1], [1, 0, 1]]
    records = [dict(id=f"L{i}", dimensions=[3, 3], differentials=[circle_d0],
                    top_basis=[[0, 1], [1, 2], [2, 0]], top_input=[1, 0, 0], top_cycle=[1, 1, 1])
               for i in range(5)]
    for name, value, prefix in (("sphere", sphere, ""), ("rp2", rp2, "integral_")):
        d0, d1 = value[prefix + "d0"], value[prefix + "d1"]
        count = len(value["faces"])
        records.append(dict(id=name, dimensions=[len(value["vertices"]), len(value["edges"]), count],
                            differentials=[[[int(x) % 2 for x in row] for row in d.tolist()] for d in (d0, d1)],
                            top_basis=value["faces"], top_input=[int(i == 0) for i in range(count)], top_cycle=[1] * count))
    pairings = []
    for record in records:
        last = sp.Matrix(record["differentials"][-1])
        record["cycle_boundary"] = [int(x) % 2 for x in last.T * sp.Matrix(record["top_cycle"])]
        record["protected_pairing"] = sum(x * y for x, y in zip(record["top_input"], record["top_cycle"])) % 2
        pairings.append(record["protected_pairing"])
    product_pairing = 1
    for pairing in pairings:
        product_pairing = product_pairing * pairing % 2
    dimensions = [1]
    factors = [record["dimensions"] for record in records]
    for factor in factors:
        next_dimensions = [0] * (len(dimensions) + len(factor) - 1)
        for i, a in enumerate(dimensions):
            for j, b in enumerate(factor):
                next_dimensions[i + j] += a * b
        dimensions = next_dimensions
    pairs = [list(s) for k in range(1, 5) for s in combinations(range(5), k) if 0 in s]
    state = sp.zeros(32, 1)
    state[0], state[31] = (1 + sp.I) / 2, (1 - sp.I) / 2
    density = sp.simplify(state * state.H)
    density_entries = [[i, j, _complex(density[i, j])] for i, j in product(range(32), repeat=2)
                       if density[i, j] != 0]
    state_shear = _shear(32)
    stored_state = state_shear.inv() * state
    stored_density = sp.simplify(state_shear.inv() * density * state_shear.inv().T)
    restored_state = sp.simplify(state_shear * stored_state)
    restored_density = sp.simplify(state_shear * stored_density * state_shear.T)
    quantum_transport = dict(stored_state_terms=[[i, _complex(stored_state[i])] for i in range(32) if stored_state[i] != 0],
                             stored_density_terms=[[i, j, _complex(stored_density[i, j])] for i, j in product(range(32), repeat=2) if stored_density[i, j] != 0],
                             source_norm=_complex((state.H * state)[0]),
                             stored_metric_norm=_complex((stored_state.H * state_shear.T * state_shear * stored_state)[0]),
                             nonzero_state_reconstruction_residuals=sum(x != 0 for x in restored_state - state),
                             nonzero_density_reconstruction_residuals=sum(x != 0 for x in restored_density - density),
                             metric_contract="S_transpose*S; shear coordinates do not change named tensor factors")
    bit_words = list(product((0, 1), repeat=5))
    marginals = {}
    for axis in range(5):
        marginal = sp.zeros(2)
        for i, left in enumerate(bit_words):
            for j, right in enumerate(bit_words):
                if all(left[k] == right[k] for k in range(5) if k != axis):
                    marginal[left[axis], right[axis]] += density[i, j]
        marginals[str(axis)] = [[Fraction(sp.simplify(x)) for x in row] for row in marginal.tolist()]
    schmidt_ranks = []
    for partition in pairs:
        other = [i for i in range(5) if i not in partition]
        left_basis, right_basis = list(product((0, 1), repeat=len(partition))), list(product((0, 1), repeat=len(other)))
        amplitudes = sp.zeros(len(left_basis), len(right_basis))
        for i, bits in enumerate(bit_words):
            row = left_basis.index(tuple(bits[k] for k in partition))
            col = right_basis.index(tuple(bits[k] for k in other))
            amplitudes[row, col] = state[i]
        schmidt_ranks.append(int(amplitudes.rank()))
    contextual = _pr_box()
    contextual_values = [value for table in contextual["tables"] for row in table for value in row]
    assignment_bits = list(product((0, 1), repeat=4))
    projection = sp.Matrix([[int(bits[x] == a and bits[2 + y] == b) for bits in assignment_bits]
                            for x, y in product((0, 1), repeat=2) for a, b in product((0, 1), repeat=2)])
    context_shear = _shear(16)
    stored_projection = context_shear.inv() * projection * context_shear
    contextual["basis_transport"] = dict(source_assignment_order=assignment_bits,
                                         stored_tables=_shear_values(contextual_values, inverse=True),
                                         stored_global_to_table_map=stored_projection,
                                         nonzero_map_reconstruction_residuals=sum(x != 0 for x in context_shear * stored_projection * context_shear.inv() - projection),
                                         restored_tables=_shear_values(_shear_values(contextual_values, inverse=True)),
                                         positivity_contract="nonnegative original coordinates after S recovery")
    integral = _sheared(True)
    rational_partial = sp.Matrix([0, 0, 0, sp.Rational(1, 2), sp.Rational(1, 3), 0])
    integral_d1 = sp.Matrix([[0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 3, 0], [0, 0, 0, 0, 0, 0]])
    integral["rational_bridge"] = dict(partial_potential=list(rational_partial),
                                       residual=list(sp.ones(3, 1) - integral_d1 * rational_partial),
                                       torsion_questions_retained=False, free_coordinate_retained=True)
    integral["mod_two_bridge"] = dict(d1=[[int(x) % 2 for x in row] for row in integral_d1.tolist()],
                                      input=[1, 1, 1], three_torsion_question_retained=False)
    return dict(topological=dict(coefficient_profile="F2", factor_cell_dimensions=factors,
                                 factor_certificates=records,
                                 tensor_dimensions=dimensions, input_degree=9,
                                 circle_d0=circle_d0,
                                 sphere_d0=[[int(x) % 2 for x in row] for row in sphere["d0"].tolist()],
                                 sphere_d1=[[int(x) % 2 for x in row] for row in sphere["d1"].tolist()],
                                 rp2_d0=[[int(x) % 2 for x in row] for row in rp2["integral_d0"].tolist()],
                                 rp2_d1=[[int(x) % 2 for x in row] for row in rp2["integral_d1"].tolist()],
                                 sphere_cycle_boundary=[int(x) % 2 for x in sphere["d1"].T * sp.ones(4, 1)],
                                 rp2_cycle_boundary=rp2["mod_two_cycle_boundary"],
                                 fundamental_cycle_recipe="TENSOR_OF_ALL_TOP_FACTOR_CELLS_OVER_F2",
                                 individual_factor_pairings=pairings, product_pairing=product_pairing),
                integral=integral, contextual=contextual,
                quantum=dict(basis_qubits=[0, 1, 2, 3, 4], dimension=32,
                             unlisted_amplitude=[Fraction(0), Fraction(0)],
                             unlisted_density_entry=[Fraction(0), Fraction(0)],
                             nonzero_amplitudes=[[i, _complex(state[i])] for i in range(32) if state[i] != 0],
                             nonzero_density_entries=density_entries,
                             single_factor_marginals=marginals,
                             bipartitions=pairs, schmidt_ranks=schmidt_ranks, basis_transport=quantum_transport),
                css=dict(carrier=css, X_generator_phase_i=[0] * 25, Z_generator_phase_i=[0] * 25,
                         phase_form=_css_phase_data(css), basis_transport=_css_transport(css),
                         canonical_XZ_product_recipe="i^(3*Y_count)_times_Pauli_word"),
                basis_transport=dict(forward_recipe=["for_i=0..m-2:add_i_to_i+1", "add_last_to_first"],
                                     inverse_recipe=["subtract_last_from_first", "for_i=m-2..0:subtract_i_from_i+1"],
                                     minimum_dimension=2, elementary_determinants=[1, 1], matrix_rule="S_next^-1*d*S_current",
                                     cochain_rule="S^-1*c", dual_rule="dual*S",
                                     tensor_certificate=_tensor_transport(records, dimensions)),
                composed_target="OBSTRUCTED_IN_EACH_SEPARATELY_NAMED_COMPONENT",
                evidence_scope="EXACT_FACTOR_INCIDENCE_AND_LAZY_TENSOR_TRANSPORT_NOT_FULL_DENSE_ENUMERATION")


_EXPECTED = {27: _sphere, 28: _group_cocycle, 31: _unitary, 32: _bell, 33: _instrument,
             35: _pr_box, 36: _magic_square, 37: _three_qubit, 38: lambda: _torus(2),
             39: _toric_errors, 40: _three_copies, 41: lambda: _sheared(False), 42: _wedge,
             43: _rp2, 44: _graded_algebra, 45: _tensor_circle, 46: lambda: _sheared(True),
             47: _filtered, 48: _cross_polytopes, 49: _bilinear, 50: _composite}


@lru_cache(maxsize=24)
def _computed(number: int) -> dict:
    return _plain(_EXPECTED[number]())


def advanced_expected(number: int) -> dict:
    """Recompute the deciding finite data, never fabricate a tool verdict."""
    from copy import deepcopy
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure

    if number == 20:
        raise SeedCheckFailure("LEAN_SOURCE_WITNESS_REQUIRED")
    if number not in _EXPECTED:
        raise SeedCheckFailure("UNKNOWN_ADVANCED_SEED")
    return deepcopy(_computed(number))


def advanced_check(number: int, payload: dict) -> dict:
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import compare
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import wire

    if number == 20:
        return _lean_check(payload)
    expected = advanced_expected(number)
    if number == 50 and type(payload) is dict:
        # These are actual candidate-chosen finite controls. They need not equal
        # the reference control, and cannot discharge the original obstruction.
        try:
            terms = payload["basis_transport"]["tensor_certificate"]["source_potential_terms"]
            selected = payload["css"]["phase_form"]["selected_generator_product"]
            expected["basis_transport"]["tensor_certificate"] = _tensor_transport(
                expected["topological"]["factor_certificates"], expected["topological"]["tensor_dimensions"], terms)
            expected["css"]["phase_form"]["selected_generator_product"] = _css_phase_control(
                expected["css"]["carrier"], selected["X_selection"], selected["Z_selection"])
        except (KeyError, TypeError) as error:
            raise SeedCheckFailure("REQUIRED_COMPOSITE_TRANSPORT_AND_PHASE_WITNESSES") from error
    compare(payload, expected)
    if number == 48:
        _check_cross_polytope_coefficients(payload)
    elif number == 49:
        _check_bilinear_forms(payload)
    elif number == 50:
        _check_composite_factors(payload)
    return wire(expected)


def _check_cross_polytope_coefficients(payload: dict) -> None:
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import rational
    for certificate in payload["dimensions"]:
        n = certificate["dimension"]
        boundary = {}
        facets = list(product((-1, 1), repeat=n + 1))
        coefficients = [rational(value) for value in certificate["facet_coefficients"]]
        for signs, coefficient in zip(facets, coefficients):
            vertices = tuple(enumerate(signs))
            for deleted in range(n + 1):
                ridge = vertices[:deleted] + vertices[deleted + 1:]
                boundary[ridge] = boundary.get(ridge, Fraction(0)) + (-1) ** deleted * coefficient
        if any(boundary.values()) or coefficients[facets.index(tuple(certificate["input_facet_signs"]))] != 1:
            raise SeedCheckFailure("CROSS_POLYTOPE_SUBMITTED_CYCLE_OR_INPUT_PAIRING_FAILED")


def _check_bilinear_forms(payload: dict) -> None:
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    for data in payload["dimensions"]:
        r, alpha, words = data["r"], data["alpha_matrix"], data["generator_words"]
        for i in range(2 * r):
            _bits(alpha[i], 2 * r)
            for j in range(2 * r):
                commutator = alpha[i][j] ^ alpha[j][i]
                forward, forward_word = PauliString(words[i]).multiply(PauliString(words[j]))
                reverse, reverse_word = PauliString(words[j]).multiply(PauliString(words[i]))
                if (forward_word.word != reverse_word.word or (forward - reverse) % 4 != 2 * commutator or
                        data["commutator_matrix"][i][j] != commutator):
                    raise SeedCheckFailure("SUBMITTED_BILINEAR_FORM_AND_PAULI_PHASE_DISAGREE")
        witness = data["cross_coordinate_product"]
        if _pauli_cocycle_product(witness["left_bits"], witness["right_bits"])["phase_residual"]:
            raise SeedCheckFailure("HIGHER_QUBIT_COCYCLE_MULTIPLICATION_FAILED")
        i, j = data["nontrivial_ordered_pair"]
        if alpha[i][j] ^ alpha[j][i] != 1:
            raise SeedCheckFailure("NO_NONTRIVIAL_COMMUTATOR_OBSTRUCTION")


def _check_composite_factors(payload: dict) -> None:
    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    pairings = []
    for record in payload["topological"]["factor_certificates"]:
        top_cycle = _bits(record["top_cycle"], record["dimensions"][-1])
        top_input = _bits(record["top_input"], record["dimensions"][-1])
        maps = [sp.Matrix(value) for value in record["differentials"]]
        if any(int(x) % 2 for x in maps[-1].T * sp.Matrix(top_cycle)):
            raise SeedCheckFailure("SUBMITTED_TENSOR_FACTOR_CYCLE_NOT_CLOSED")
        if any(int(x) % 2 for first, second in zip(maps, maps[1:]) for x in second * first):
            raise SeedCheckFailure("SUBMITTED_FACTOR_CONSECUTIVE_DIFFERENTIAL_FAILED")
        pairings.append(sum(x * y for x, y in zip(top_cycle, top_input)) % 2)
    actual_product = 1
    for pairing in pairings:
        actual_product = actual_product * pairing % 2
    transport = payload["basis_transport"]["tensor_certificate"]
    if (pairings != payload["topological"]["individual_factor_pairings"] or actual_product != 1 or
            transport["source_pairing"] != actual_product or transport["stored_pairing"] != actual_product or
            transport["naturality_residual_terms"] or transport["dual_on_stored_differential"]):
        raise SeedCheckFailure("COMPOSITE_PAIRING_OR_TRANSPORT_NATURALITY_FAILED")


def _lean_check(payload: dict) -> dict:
    """Check the exact fixed target with the existing sandboxed Lean owner."""
    import hashlib
    from pathlib import Path
    import re
    import tempfile

    from omega_engine_pfp.infrastructure.pilot_runners.seed_checks import SeedCheckFailure
    from ...domain.lean_bridge.models import LeanVerificationRequest
    from ..adapters.lake_sandbox_adapter import LakeSandboxAdapter

    required = {"source", "source_sha256", "toolchain_pin", "single_flip_counterexample"}
    if type(payload) is not dict or set(payload) != required:
        raise SeedCheckFailure("REQUIRED_LEAN_SOURCE_AND_TOOLCHAIN_BINDINGS")
    source, pin = payload["source"], payload["toolchain_pin"]
    prefix = ("namespace PfpSeed20\n\ninductive Bit where\n  | zero\n  | one\n\n"
              "def flip : Bit -> Bit\n  | Bit.zero => Bit.one\n  | Bit.one => Bit.zero\n\n"
              "theorem double_flip : forall x : Bit, flip (flip x) = x := ")
    if (type(source) is not str or len(source.encode("utf-8")) > 8192 or
            not source.startswith(prefix) or not source.endswith("\nend PfpSeed20\n") or type(pin) is not str or
            not re.fullmatch(r"leanprover/lean4:v[0-9]+\.[0-9]+\.[0-9]+", pin)):
        raise SeedCheckFailure("LEAN_FIXED_TARGET_OR_TOOLCHAIN_MISMATCH")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if payload["source_sha256"] != digest:
        raise SeedCheckFailure("LEAN_SOURCE_DIGEST_MISMATCH")
    if payload["single_flip_counterexample"] != {"input": "zero", "output": "one"}:
        raise SeedCheckFailure("SINGLE_FLIP_COUNTEREXAMPLE_INVALID")
    request = LeanVerificationRequest(
        package_digest=digest, toolchain_pin=pin,
        required_declarations=(("PfpSeed20.double_flip", "forall x : PfpSeed20.Bit, PfpSeed20.flip (PfpSeed20.flip x) = x"),),
    )
    with tempfile.TemporaryDirectory(prefix="pfp_seed20_") as directory:
        package = Path(directory)
        (package / "lean-toolchain").write_text(pin + "\n", encoding="utf-8")
        (package / "lakefile.toml").write_text('name = "pfp_seed20"\nversion = "0.1.0"\n\n[[lean_lib]]\nname = "Seed"\n', encoding="utf-8")
        (package / "Seed.lean").write_bytes(source.encode("utf-8"))
        try:
            result = LakeSandboxAdapter(timeout_seconds=30).verify(request, package)
        except (OSError, RuntimeError) as error:
            raise SeedCheckFailure(f"LEAN_VERIFICATION_UNAVAILABLE: {error}") from error
    if result.is_err:
        error = result.unwrap_err()
        raise SeedCheckFailure(f"LEAN_VERIFICATION_UNAVAILABLE: {error.code}: {error.message}")
    receipt = result.unwrap()
    if receipt.status != "PASS" or not receipt.build_success or not receipt.harness_elaborated:
        raise SeedCheckFailure("LEAN_VERIFICATION_FAILED: " + str(receipt.refusal_code))
    axioms = dict(receipt.axioms_by_declaration)
    if (set(axioms) != {"judge_check_1"} or receipt.forbidden_findings or
            any(axiom not in request.axiom_policy for value in axioms.values() for axiom in value) or
            receipt.authority_effect != "None"):
        raise SeedCheckFailure("LEAN_AUDIT_BINDING_OR_AXIOM_POLICY_FAILED")
    return dict(source_sha256=digest, toolchain_pin=pin, theorem="PfpSeed20.double_flip",
                axioms={name: list(axioms) for name, axioms in receipt.axioms_by_declaration},
                single_flip_counterexample=payload["single_flip_counterexample"],
                evidence_grade="KERNEL_ELABORATED_FIXED_TARGET", authority_effect="None")
