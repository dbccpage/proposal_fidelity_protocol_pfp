"""Checker 2: Coset Group Theory & Root System Checker for Challenge C040.

Completely independent mathematical foundation with ZERO shared code with Checker 1:
  - Independent Lie algebra root system engine:
      Generates positive roots for E1..E8 and compact subgroups K from Cartan matrices.
      dim(G) = rank(G) + 2 * len(positive_roots(G)).
      dim(K) = rank(K) + 2 * len(positive_roots(K)).
  - Noncompact scalar coset dimension:
      dim(p) = dim(G) - dim(K).
  - Exact equality assertion:
      Requires dim(p) == scalar field count across all k in 1..8!
  - Representation theory & Weyl dimension formulas for noncompact subspace p:
      * k = 8: Chiral spinor 128 of SO(16) = 2^(16/2 - 1) = 128.
      * k = 7: wedge4(8) of SU(8) = comb(8, 4) = 70.
      * k = 6: Antisymmetric traceless 42 of USp(8) = comb(8, 4) - comb(8, 2) = 42.
      * k = 5: Bivector (5, 5) of SO(5) x SO(5) = 5 * 5 = 25.
      * k = 4: Traceless symmetric 14 of SO(5) = 5*(5+1)//2 - 1 = 14.
      * k = 3: Traceless symmetric 5 of SO(3) + 2 of SO(2) = 7.
      * k = 2: Traceless symmetric 2 of SO(2) + R^+ singlet 1 = 3.
      * k = 1: R^+ singlet = 1.
  - Branching conservation:
      dim(Adj(K)) + dim(p) == dim(G).
  - Group-theoretic vector representation dimensions:
      k=1: 1; k=2: 3; k=3: 6; k=4: 10; k=5: 16; k=6: 27; k=7: 28; k=8: 0.

All internal identifiers strictly use namespace prefix `_c2_*`.
Zero shared imports or helper code with Checker 1.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping

# -----------------------------------------------------------------------------
# Internal Types and Utilities (_c2_*)
# -----------------------------------------------------------------------------


def _c2_is_strict_int(val: Any) -> bool:
    """Verifies that val is an int and strictly not a bool."""
    return type(val) is int


def _c2_binomial(n: int, k: int) -> int:
    """Independent factorial-based binomial coefficient."""
    if k < 0 or k > n or n < 0:
        return 0
    num = 1
    den = 1
    for i in range(1, k + 1):
        num *= n - i + 1
        den *= i
    return num // den


# -----------------------------------------------------------------------------
# Independent Root System Engine from Cartan Matrices (_c2_*)
# -----------------------------------------------------------------------------


def _c2_build_cartan_matrix(
    n: int, edges: list[tuple[int, int]], non_simply_laced: dict[tuple[int, int], int] | None = None
) -> list[list[int]]:
    """Builds Cartan matrix A where A_ii = 2, A_ij = A_ji = -1 for connected edges in simply laced graphs."""
    A = [[2 if i == j else 0 for j in range(n)] for i in range(n)]
    for u, v in edges:
        A[u][v] = -1
        A[v][u] = -1
    if non_simply_laced:
        for (u, v), val in non_simply_laced.items():
            A[u][v] = val
    return A


def _c2_generate_positive_roots(A: list[list[int]]) -> list[tuple[int, ...]]:
    """Generates all positive roots from simple roots and Cartan matrix via root string algorithm."""
    n = len(A)
    roots: list[tuple[int, ...]] = []
    roots_set: set[tuple[int, ...]] = set()

    # Step 1: Base simple roots (height 1)
    for i in range(n):
        r = tuple(1 if j == i else 0 for j in range(n))
        roots.append(r)
        roots_set.add(r)

    # Step 2: Traverse roots in increasing height, applying simple reflections
    idx = 0
    while idx < len(roots):
        alpha = roots[idx]
        idx += 1
        for j in range(n):
            # Cartan pairing <alpha, alpha_j^vee> = sum_i c_i A_ij
            pairing = sum(alpha[i] * A[i][j] for i in range(n))
            # Determine string length p: max integer such that alpha - p*alpha_j is in roots_set
            p = 0
            while True:
                cand = list(alpha)
                cand[j] -= p + 1
                if tuple(cand) in roots_set:
                    p += 1
                else:
                    break
            # Root existence condition: q = p - pairing
            q = p - pairing
            if q > 0:
                beta = list(alpha)
                beta[j] += 1
                tbeta = tuple(beta)
                if tbeta not in roots_set:
                    roots_set.add(tbeta)
                    roots.append(tbeta)
    return roots


def _c2_compute_dim_from_cartan(A: list[list[int]]) -> int:
    """Computes dimension of semi-simple Lie algebra: dim = rank + 2 * len(positive_roots)."""
    rank = len(A)
    pos_roots = _c2_generate_positive_roots(A)
    return rank + 2 * len(pos_roots)


# -----------------------------------------------------------------------------
# Pinned Lie Algebra & Compact Subgroup Data (_c2_*)
# -----------------------------------------------------------------------------


def _c2_get_group_cartan(
    name: str,
) -> tuple[int, list[tuple[int, int]], dict[tuple[int, int], int] | None]:
    """Returns (rank, edges, non_simply_laced_dict) for standard Lie algebras."""
    if name == "E8":
        # E8: 8 nodes. Nodes 0,1,2,3,4,5,6,7. Node 3 connects to 1,2,4. Node 2 connects to 0.
        edges = [(0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
        return 8, edges, None
    elif name == "E7":
        edges = [(0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (5, 6)]
        return 7, edges, None
    elif name == "E6":
        edges = [(0, 2), (1, 3), (2, 3), (3, 4), (4, 5)]
        return 6, edges, None
    elif name == "SO(5,5)":  # D5
        edges = [(0, 2), (1, 3), (2, 3), (3, 4)]
        return 5, edges, None
    elif name == "SL(5)":  # A4
        edges = [(0, 1), (1, 2), (2, 3)]
        return 4, edges, None
    elif name == "SL(3)":  # A2
        edges = [(0, 1)]
        return 2, edges, None
    elif name == "SL(2)":  # A1
        return 1, [], None
    elif name == "SU(8)":  # A7
        edges = [(i, i + 1) for i in range(6)]
        return 7, edges, None
    elif name == "SO(16)":  # D8
        edges = [(i, i + 1) for i in range(5)] + [(5, 6), (5, 7)]
        return 8, edges, None
    elif name == "USp(8)":  # C4
        edges = [(0, 1), (1, 2)]
        nsl = {(2, 3): -1, (3, 2): -2}
        return 4, edges, nsl
    elif name == "SO(5)":  # B2 / C2
        nsl = {(0, 1): -1, (1, 0): -2}
        return 2, [], nsl
    elif name == "SO(3)":  # A1
        return 1, [], None
    elif name == "SO(2)":  # U(1), abelian rank 1
        return 1, [], None
    else:
        raise ValueError(f"Unknown group: {name}")


def _c2_compute_dim_G(k: int) -> int:
    """Computes exact dimension of G = E_{k(k)} using Cartan matrix positive roots."""
    if k == 1:
        return 1  # R^+
    elif k == 2:
        # SL(2, R) x R^+: 3 + 1 = 4
        rank, edges, nsl = _c2_get_group_cartan("SL(2)")
        A = _c2_build_cartan_matrix(rank, edges, nsl)
        return _c2_compute_dim_from_cartan(A) + 1  # 3 + 1 = 4
    elif k == 3:
        # SL(3, R) x SL(2, R): 8 + 3 = 11
        r1, e1, n1 = _c2_get_group_cartan("SL(3)")
        r2, e2, n2 = _c2_get_group_cartan("SL(2)")
        d1 = _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r1, e1, n1))
        d2 = _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r2, e2, n2))
        return d1 + d2
    elif k == 4:
        # SL(5, R) = A4: 24
        r, e, n = _c2_get_group_cartan("SL(5)")
        return _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
    elif k == 5:
        # SO(5, 5) = D5: 45
        r, e, n = _c2_get_group_cartan("SO(5,5)")
        return _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
    elif k == 6:
        # E6(6): 78
        r, e, n = _c2_get_group_cartan("E6")
        return _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
    elif k == 7:
        # E7(7): 133
        r, e, n = _c2_get_group_cartan("E7")
        return _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
    elif k == 8:
        # E8(8): 248
        r, e, n = _c2_get_group_cartan("E8")
        return _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
    raise ValueError(f"k out of bounds: {k}")


def _c2_compute_dim_K(k: int) -> int:
    """Computes exact dimension of maximal compact subgroup K using Cartan matrices."""
    if k == 1:
        return 0  # trivial / O(1)
    elif k == 2:
        return 1  # SO(2) = U(1)
    elif k == 3:
        # SO(3) x SO(2): 3 + 1 = 4
        r, e, n = _c2_get_group_cartan("SO(3)")
        d_so3 = _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
        return d_so3 + 1
    elif k == 4:
        # SO(5) = B2: 10
        r, e, n = _c2_get_group_cartan("SO(5)")
        return _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
    elif k == 5:
        # SO(5) x SO(5): 10 + 10 = 20
        r, e, n = _c2_get_group_cartan("SO(5)")
        d_so5 = _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
        return 2 * d_so5
    elif k == 6:
        # USp(8) = C4: 36
        r, e, n = _c2_get_group_cartan("USp(8)")
        return _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
    elif k == 7:
        # SU(8) = A7: 63
        r, e, n = _c2_get_group_cartan("SU(8)")
        return _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
    elif k == 8:
        # SO(16) = D8: 120
        r, e, n = _c2_get_group_cartan("SO(16)")
        return _c2_compute_dim_from_cartan(_c2_build_cartan_matrix(r, e, n))
    raise ValueError(f"k out of bounds: {k}")


def _c2_canonical_group_names(k: int) -> tuple[str, str]:
    """Returns canonical names of (E_{k(k)}, K) for 1 <= k <= 8."""
    names: dict[int, tuple[str, str]] = {
        1: ("R+", "1"),
        2: ("SL(2)xR+", "SO(2)"),
        3: ("SL(3)xSL(2)", "SO(3)xSO(2)"),
        4: ("SL(5)", "SO(5)"),
        5: ("SO(5,5)", "SO(5)xSO(5)"),
        6: ("E6(6)", "USp(8)"),
        7: ("E7(7)", "SU(8)"),
        8: ("E8(8)", "SO(16)"),
    }
    return names[k]


# -----------------------------------------------------------------------------
# Representation Theory & Branching Formulas (_c2_*)
# -----------------------------------------------------------------------------


def _c2_compute_rep_dim_p(k: int) -> int:
    """Computes dimension of noncompact representation p via exact Weyl/tensor formulas."""
    if k == 1:
        return 1  # singlet
    elif k == 2:
        return 3
    elif k == 3:
        return 7
    elif k == 4:
        return 5 * 6 // 2 - 1  # 14
    elif k == 5:
        return 5 * 5  # 25
    elif k == 6:
        return _c2_binomial(8, 4) - _c2_binomial(8, 2)  # 42
    elif k == 7:
        return _c2_binomial(8, 4)  # 70
    elif k == 8:
        return 1 << (16 // 2 - 1)  # 128
    raise ValueError(f"k out of bounds: {k}")


def _c2_expected_branching(k: int) -> list[tuple[str, int]]:
    """Returns canonical branching decomposition of Adj(G) into K-representations."""
    dimK = _c2_compute_dim_K(k)
    dim_p = _c2_compute_rep_dim_p(k)
    _, K_name = _c2_canonical_group_names(k)

    if k == 8:
        return [(f"adjoint({K_name})", dimK), ("chiral_spinor(16)", dim_p)]
    elif k == 7:
        return [(f"adjoint({K_name})", dimK), ("wedge4(8)", dim_p)]
    elif k == 6:
        return [(f"adjoint({K_name})", dimK), ("antisymmetric_traceless(8)", dim_p)]
    elif k == 5:
        return [(f"adjoint({K_name})", dimK), ("bivector(5,5)", dim_p)]
    elif k == 4:
        return [(f"adjoint({K_name})", dimK), ("traceless_symmetric(5)", dim_p)]
    elif k == 3:
        return [(f"adjoint({K_name})", dimK), ("p_representation", dim_p)]
    elif k == 2:
        return [(f"adjoint({K_name})", dimK), ("p_representation", dim_p)]
    elif k == 1:
        return [(f"adjoint({K_name})", dimK), ("singlet", dim_p)]
    raise ValueError(f"k out of bounds: {k}")


def _c2_group_theoretic_vectors(k: int) -> int:
    """Computes vector count in D = 11 - k dimensions from group representations."""
    vec_table = {
        1: 1,  # 1
        2: 3,  # (2, 1) + (1, 1) of SL(2) x R+
        3: 6,  # (3, 2) of SL(3) x SL(2)
        4: 10,  # wedge2(5) of SL(5)
        5: 16,  # 16 chiral spinor of SO(5,5)
        6: 27,  # 27 fundamental of E6
        7: 28,  # 28 electric vectors of E7 (half of 56)
        8: 0,  # 0 in D=3 (all dualized to scalars)
    }
    return vec_table[k]


# -----------------------------------------------------------------------------
# Anti-Bypass Defenses & Verification Entrypoint (_c2_*)
# -----------------------------------------------------------------------------


def _c2_verify_refusal_warranted(
    case: Mapping[str, Any], answer: Mapping[str, Any]
) -> tuple[bool, str]:
    """Validates that a refusal is strictly defect-grounded (k outside [1, 8])."""
    k = case.get("k")
    if _c2_is_strict_int(k) and 1 <= k <= 8:
        return False, f"Anti-bypass: refusal unwarranted for valid k={k}"

    refusal_code = answer.get("refusal_code")
    if refusal_code != "K_OUT_OF_BOUNDS":
        return (
            False,
            f"Anti-bypass: invalid refusal_code '{refusal_code}', expected 'K_OUT_OF_BOUNDS'",
        )

    allowed_keys = {"id", "case_id", "status", "refusal_code"}
    extra_keys = set(answer.keys()) - allowed_keys
    if extra_keys:
        return False, f"Anti-bypass: phantom keys in refusal answer: {sorted(extra_keys)}"

    return True, "C2_REFUSAL_WARRANTED"


def verify_coset_group_theory_certificate(
    case: Mapping[str, Any],
    answer: Mapping[str, Any],
) -> tuple[bool, str]:
    """Checker 2 entrypoint: verifies answer against Lie algebra coset group theory."""
    if not isinstance(case, Mapping) or not isinstance(answer, Mapping):
        return False, "Malformed input: case and answer must be mappings"

    status = answer.get("status")
    if status == "UNKNOWN":
        return _c2_verify_refusal_warranted(case, answer)

    if status != "SOLVED":
        return False, f"Invalid answer status '{status}', must be 'SOLVED' or 'UNKNOWN'"

    k = case.get("k")
    if not _c2_is_strict_int(k) or k < 1 or k > 8:
        return False, f"Case k={k!r} out of bounds for SOLVED status"

    ans_k = answer.get("k")
    if not _c2_is_strict_int(ans_k) or ans_k != k:
        return False, f"Answer k={ans_k!r} must be strict int matching case k={k}"

    ans_D = answer.get("D")
    exp_D = 11 - k
    if ans_D is not None and (not _c2_is_strict_int(ans_D) or ans_D != exp_D):
        return False, f"Answer D={ans_D!r} must be strict int matching 11 - k = {exp_D}"

    query = case.get("query")
    allowed_root_keys = {"id", "case_id", "status", "k", "D", "query", "theory", query}
    extra_keys = set(answer.keys()) - allowed_root_keys
    if extra_keys:
        return False, f"Anti-bypass: phantom keys in answer: {sorted(extra_keys)}"

    # Independent computation of G and K dimensions
    dimG = _c2_compute_dim_G(k)
    dimK = _c2_compute_dim_K(k)
    dim_p = dimG - dimK
    rep_dim_p = _c2_compute_rep_dim_p(k)

    # Core assertion: coset dimension MUST equal Weyl representation dimension
    if dim_p != rep_dim_p:
        return False, f"Group theory internal inconsistency: dim_p={dim_p} != rep_dim_p={rep_dim_p}"

    if query == "coset":
        coset_data = answer.get("coset")
        if not isinstance(coset_data, Mapping):
            return False, "Query 'coset' missing valid 'coset' mapping in answer"
        allowed_coset_keys = {"G", "K", "dimG", "dimK", "difference"}
        extra = set(coset_data.keys()) - allowed_coset_keys
        if extra:
            return False, f"Anti-bypass: phantom keys in coset mapping: {sorted(extra)}"

        ans_dimG = coset_data.get("dimG")
        ans_dimK = coset_data.get("dimK")
        ans_diff = coset_data.get("difference")
        coset_data.get("G")
        ans_K = coset_data.get("K")

        if not (
            _c2_is_strict_int(ans_dimG)
            and _c2_is_strict_int(ans_dimK)
            and _c2_is_strict_int(ans_diff)
        ):
            return False, "Anti-bypass: coset dimensions must be strict integers"

        # Trap Layer 4: Wrong compact subgroup label trap
        canon_G, canon_K = _c2_canonical_group_names(k)
        if ans_K is not None:
            ans_K_clean = str(ans_K).replace(" ", "").upper()
            canon_K_clean = canon_K.replace(" ", "").upper()
            # Catch dim K=36 labeled SU(8) for E6
            if k == 6 and "SU(8)" in ans_K_clean:
                return (
                    False,
                    "Anti-bypass: wrong compact subgroup label: E6(6) has K=USp(8), not SU(8)",
                )
            if ans_K_clean != canon_K_clean and ans_K_clean not in (canon_K_clean, "SP(4)", "1"):
                return (
                    False,
                    f"Compact subgroup label mismatch: got '{ans_K}', expected '{canon_K}'",
                )

        if ans_dimG != dimG:
            return False, f"dim(G) mismatch: got {ans_dimG}, expected {dimG}"
        if ans_dimK != dimK:
            return False, f"dim(K) mismatch: got {ans_dimK}, expected {dimK}"
        if ans_diff != dim_p:
            return False, f"Difference mismatch: got {ans_diff}, expected {dim_p}"
        if ans_dimG - ans_dimK != ans_diff:
            return False, f"Inconsistent coset difference: {ans_dimG} - {ans_dimK} != {ans_diff}"

        return True, "C2_COSET_OK"

    elif query == "branching":
        branching_data = answer.get("branching")
        if not isinstance(branching_data, list):
            return False, "Query 'branching' missing valid 'branching' list in answer"

        total_branching_dim = 0

        for item in branching_data:
            if not (isinstance(item, (list, tuple)) and len(item) == 2):
                return False, f"Invalid branching element: {item!r}"
            label, d = item
            if not isinstance(label, str) or not _c2_is_strict_int(d):
                return False, "Branching element must be [str, int]"
            total_branching_dim += d
            if "adjoint" in label.lower():
                if d != dimK:
                    return (
                        False,
                        f"Branching adjoint dimension mismatch: got {d}, expected dim(K)={dimK}",
                    )
            else:
                if d != dim_p:
                    return (
                        False,
                        f"Branching p dimension mismatch: got {d}, expected dim(p)={dim_p}",
                    )

        # Adjoint conservation: dim(Adj(K)) + dim(p) == dim(G)
        if total_branching_dim != dimG:
            return False, (
                f"Branching does not conserve adjoint dimension: "
                f"sum={total_branching_dim} != dim(G)={dimG}"
            )
        return True, "C2_BRANCHING_OK"

    elif query == "scalars":
        scalars_data = answer.get("scalars")
        if not isinstance(scalars_data, Mapping):
            return False, "Query 'scalars' missing valid 'scalars' mapping in answer"

        allowed_scalar_keys = {
            "metric",
            "three_form",
            "total",
            "dual_C_mu_nu_rho",
            "dual_C_mu_nu_i",
            "dual_kk_vectors",
            "dual_C_mu_ij",
            "dual_forms",
        }
        extra = set(scalars_data.keys()) - allowed_scalar_keys
        if extra:
            return False, f"Anti-bypass: phantom keys in scalars breakdown: {sorted(extra)}"

        for key, val in scalars_data.items():
            if not _c2_is_strict_int(val):
                return (
                    False,
                    f"Anti-bypass: scalar breakdown key '{key}' has non-integer value {val!r}",
                )

        total_scalars = scalars_data.get("total")
        if not _c2_is_strict_int(total_scalars):
            return False, "Scalar total must be a strict integer"

        # Group-theoretic scalar check: total scalars MUST equal dim(p) = dim(G) - dim(K)
        if total_scalars != dim_p:
            return False, (
                f"Group theory check: scalar total {total_scalars} does not match "
                f"coset dimension dim(p) = {dim_p}"
            )

        # Trap Layer 1: Metric-plus-3-form only trap
        # In D=5, 4, 3, undualized metric + 3-form is 41, 63, 92 vs 42, 70, 128
        if (
            (k == 6 and total_scalars == 41)
            or (k == 7 and total_scalars == 63)
            or (k == 8 and total_scalars == 92)
        ):
            return False, "Anti-bypass: metric-plus-3-form only trap: omitted dualized forms"

        # Check internal sum
        component_sum = sum(v for k_name, v in scalars_data.items() if k_name != "total")
        if total_scalars != component_sum:
            return (
                False,
                f"Scalar components do not sum to total: sum={component_sum} vs total={total_scalars}",
            )

        return True, "C2_SCALARS_OK"

    elif query == "vectors":
        vectors_data = answer.get("vectors")
        if not isinstance(vectors_data, Mapping):
            return False, "Query 'vectors' missing valid 'vectors' mapping in answer"

        allowed_vector_keys = {"metric_kk", "three_form", "dual_forms", "total"}
        extra = set(vectors_data.keys()) - allowed_vector_keys
        if extra:
            return False, f"Anti-bypass: phantom keys in vectors breakdown: {sorted(extra)}"

        total_vectors = vectors_data.get("total")
        if not _c2_is_strict_int(total_vectors):
            return False, "Vector total must be a strict integer"

        exp_vecs = _c2_group_theoretic_vectors(k)
        if total_vectors != exp_vecs:
            return (
                False,
                f"Group theory vector count mismatch: got {total_vectors}, expected {exp_vecs}",
            )

        return True, "C2_VECTORS_OK"

    else:
        return False, f"Unknown query type: {query}"
