"""Exact Lie algebra kernel for C033.

Implements Cartan data, simple roots, Weyl groups, Weyl dimension formula,
dominant chamber reflection, Freudenthal weight multiplicity recursion,
and Brauer-Klimyk tensor product decomposition for simple Lie algebras
of rank <= 4:
  A1, A2, A3, A4
  B2, B3, B4
  C3, C4
  D4
  G2
  F4

Bourbaki conventions throughout:
  - An: standard chain 1 - 2 - ... - n
  - Bn: node n is short (vector 2n+1 is [1, 0, ..., 0], spinor 2^n is [0, ..., 1])
  - Cn: node n is long (fundamental 2n is [1, 0, ..., 0])
  - D4: node 2 is central: 1 - 2(-4) - 3; triality permutes 1, 3, 4
  - G2: node 1 is short (dim 7 is [1, 0]), node 2 is long (adjoint 14 is [0, 1])
  - F4: nodes 1, 2 long, nodes 3, 4 short (dim 26 is [0, 0, 0, 1], adjoint 52 is [1, 0, 0, 0])

Pure Python standard library. Exact rational and integer arithmetic.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections import deque
from fractions import Fraction
from functools import lru_cache
from itertools import product

# Cartan matrices A_ij = 2(alpha_i, alpha_j) / (alpha_j, alpha_j)
# The j-th simple reflection on Dynkin labels w is:
# (s_j(w))_k = w_k - w_j * A_jk
CARTAN_MATRICES: dict[str, list[list[int]]] = {
    "A1": [[2]],
    "A2": [
        [2, -1],
        [-1, 2],
    ],
    "A3": [
        [2, -1, 0],
        [-1, 2, -1],
        [0, -1, 2],
    ],
    "A4": [
        [2, -1, 0, 0],
        [-1, 2, -1, 0],
        [0, -1, 2, -1],
        [0, 0, -1, 2],
    ],
    "B2": [
        [2, -2],
        [-1, 2],
    ],
    "B3": [
        [2, -1, 0],
        [-1, 2, -2],
        [0, -1, 2],
    ],
    "B4": [
        [2, -1, 0, 0],
        [-1, 2, -1, 0],
        [0, -1, 2, -2],
        [0, 0, -1, 2],
    ],
    "C3": [
        [2, -1, 0],
        [-1, 2, -1],
        [0, -2, 2],
    ],
    "C4": [
        [2, -1, 0, 0],
        [-1, 2, -1, 0],
        [0, -1, 2, -1],
        [0, 0, -2, 2],
    ],
    "D4": [
        [2, -1, 0, 0],
        [-1, 2, -1, -1],
        [0, -1, 2, 0],
        [0, -1, 0, 2],
    ],
    "G2": [
        [2, -1],
        [-3, 2],
    ],
    "F4": [
        [2, -1, 0, 0],
        [-1, 2, -2, 0],
        [0, -1, 2, -1],
        [0, 0, -1, 2],
    ],
}

# Symmetrizers d_i such that d_j * A_ij = d_i * A_ji = (alpha_i, alpha_j)
# Root length squared (alpha_i, alpha_i) = 2 * d_i (up to overall scale)
SYMMETRIZERS: dict[str, list[int]] = {
    "A1": [1],
    "A2": [1, 1],
    "A3": [1, 1, 1],
    "A4": [1, 1, 1, 1],
    "B2": [2, 1],
    "B3": [2, 2, 1],
    "B4": [2, 2, 2, 1],
    "C3": [1, 1, 2],
    "C4": [1, 1, 1, 2],
    "D4": [1, 1, 1, 1],
    "G2": [1, 3],
    "F4": [2, 2, 1, 1],
}

WEYL_GROUP_ORDERS: dict[str, int] = {
    "A1": 2,
    "A2": 6,
    "A3": 24,
    "A4": 120,
    "B2": 8,
    "B3": 48,
    "B4": 384,
    "C3": 48,
    "C4": 384,
    "D4": 192,
    "G2": 12,
    "F4": 1152,
}

SUPPORTED_ALGEBRAS = frozenset(CARTAN_MATRICES.keys())


def is_algebra_supported(algebra: str) -> bool:
    """Returns True if the algebra is a supported simple Lie algebra of rank <= 4."""
    return algebra in SUPPORTED_ALGEBRAS


def get_rank(algebra: str) -> int:
    """Returns the rank of the Lie algebra."""
    if algebra not in CARTAN_MATRICES:
        raise ValueError(f"Unsupported Lie algebra: {algebra}")
    return len(CARTAN_MATRICES[algebra])


def get_cartan_matrix(algebra: str) -> list[list[int]]:
    """Returns the Cartan matrix for the Lie algebra."""
    if algebra not in CARTAN_MATRICES:
        raise ValueError(f"Unsupported Lie algebra: {algebra}")
    return CARTAN_MATRICES[algebra]


def get_symmetrizer(algebra: str) -> list[int]:
    """Returns the symmetrizer vector d for the Lie algebra."""
    if algebra not in SYMMETRIZERS:
        raise ValueError(f"Unsupported Lie algebra: {algebra}")
    return SYMMETRIZERS[algebra]


@lru_cache(maxsize=32)
def get_positive_roots(algebra: str) -> tuple[tuple[int, ...], ...]:
    """Generates all positive roots expressed in simple root basis."""
    cartan = get_cartan_matrix(algebra)
    rank = len(cartan)
    simple = [tuple(1 if i == j else 0 for j in range(rank)) for i in range(rank)]
    roots: set[tuple[int, ...]] = set(simple)
    queue: list[tuple[int, ...]] = list(simple)

    while queue:
        r = queue.pop(0)
        for i in range(rank):
            inner = sum(r[j] * cartan[j][i] for j in range(rank))
            new_r = list(r)
            new_r[i] -= inner
            new_tuple = tuple(new_r)
            if all(x >= 0 for x in new_tuple) and any(x > 0 for x in new_tuple):
                if new_tuple not in roots:
                    roots.add(new_tuple)
                    queue.append(new_tuple)

    return tuple(sorted(roots, key=lambda r: (sum(r), r)))


@lru_cache(maxsize=32)
def get_positive_roots_dynkin(algebra: str) -> tuple[tuple[int, ...], ...]:
    """Returns positive roots expressed in the Dynkin basis (column combinations of Cartan matrix)."""
    cartan = get_cartan_matrix(algebra)
    rank = len(cartan)
    roots = get_positive_roots(algebra)
    dynk_roots = []
    for r in roots:
        # dynk[i] = sum_j A[j][i] * r[j]
        dynk = tuple(sum(cartan[j][i] * r[j] for j in range(rank)) for i in range(rank))
        dynk_roots.append(dynk)
    return tuple(dynk_roots)


def scalar_product_roots(algebra: str, r1: tuple[int, ...], r2: tuple[int, ...]) -> int:
    """Exact invariant scalar product (r1, r2) between two roots in simple root basis."""
    cartan = get_cartan_matrix(algebra)
    d = get_symmetrizer(algebra)
    rank = len(cartan)
    return sum(r1[i] * r2[j] * d[j] * cartan[i][j] for i in range(rank) for j in range(rank))


def inner_product_weight_root(algebra: str, weight: tuple[int, ...], root: tuple[int, ...]) -> int:
    """Computes exact scalar product (weight, root) where weight is Dynkin and root is simple basis."""
    d = get_symmetrizer(algebra)
    rank = len(weight)
    return sum(root[j] * d[j] * weight[j] for j in range(rank))


def simple_reflect(algebra: str, weight: tuple[int, ...], index: int) -> tuple[int, ...]:
    """Reflects a weight across simple root index in Dynkin basis."""
    cartan = get_cartan_matrix(algebra)
    val = weight[index]
    rank = len(weight)
    return tuple(weight[j] - val * cartan[index][j] for j in range(rank))


def reflect_to_dominant(algebra: str, weight: tuple[int, ...] | list[int]) -> tuple[int, ...]:
    """Reflects an integral weight into the dominant chamber (all Dynkin labels >= 0)."""
    cartan = get_cartan_matrix(algebra)
    rank = len(cartan)
    curr = list(weight)

    # Finite loop bounded by maximum Coxeter element length
    for _ in range(100):
        neg_idx = -1
        for i in range(rank):
            if curr[i] < 0:
                neg_idx = i
                break
        if neg_idx == -1:
            return tuple(curr)

        val = curr[neg_idx]
        for j in range(rank):
            curr[j] -= val * cartan[neg_idx][j]

    return tuple(curr)


def weyl_orbit_size(algebra: str, weight: tuple[int, ...] | list[int]) -> int:
    """Computes the exact size of the Weyl orbit W * weight."""
    cartan = get_cartan_matrix(algebra)
    rank = len(cartan)
    start = tuple(weight)
    visited: set[tuple[int, ...]] = {start}
    queue = deque([start])

    while queue:
        curr = queue.popleft()
        for i in range(rank):
            val = curr[i]
            if val != 0:
                new_w = tuple(curr[j] - val * cartan[i][j] for j in range(rank))
                if new_w not in visited:
                    visited.add(new_w)
                    queue.append(new_w)

    return len(visited)


def weyl_dimension(algebra: str, weight: tuple[int, ...] | list[int]) -> int:
    """Computes the dimension of the irreducible representation V(weight) via the Weyl dimension formula."""
    dom = reflect_to_dominant(algebra, weight)
    roots = get_positive_roots(algebra)
    d = get_symmetrizer(algebra)
    rank = len(dom)

    num = 1
    den = 1
    for r in roots:
        # (lambda + rho, alpha)
        v_l = sum(r[j] * d[j] * (dom[j] + 1) for j in range(rank))
        # (rho, alpha)
        v_r = sum(r[j] * d[j] * 1 for j in range(rank))
        num *= v_l
        den *= v_r

    return num // den


@lru_cache(maxsize=32)
def _get_cartan_inverse(algebra: str) -> tuple[tuple[Fraction, ...], ...]:
    """Computes exact rational inverse of the Cartan matrix."""
    cart = CARTAN_MATRICES[algebra]
    r = len(cart)
    aug = [
        [Fraction(cart[i][j]) for j in range(r)] + [Fraction(1 if i == j else 0) for j in range(r)]
        for i in range(r)
    ]
    for i in range(r):
        pivot = aug[i][i]
        for c in range(2 * r):
            aug[i][c] /= pivot
        for row in range(r):
            if row != i:
                factor = aug[row][i]
                for c in range(2 * r):
                    aug[row][c] -= factor * aug[i][c]
    return tuple(tuple(aug[i][r + j] for j in range(r)) for i in range(r))


def freudenthal_multiplicities(
    algebra: str,
    highest_weight: tuple[int, ...] | list[int],
    max_dimension: int = 1_000_000,
) -> dict[tuple[int, ...], int]:
    """Computes exact dominant weight multiplicities via Freudenthal recursion."""
    lam = reflect_to_dominant(algebra, highest_weight)
    dim = weyl_dimension(algebra, lam)
    if dim > max_dimension:
        raise ValueError(f"Dimension {dim} exceeds max limit {max_dimension}")

    cartan = get_cartan_matrix(algebra)
    d = get_symmetrizer(algebra)
    roots = get_positive_roots(algebra)
    roots_dynk = get_positive_roots_dynkin(algebra)
    root_norms = [scalar_product_roots(algebra, r, r) for r in roots]
    rank = len(lam)

    # Base case
    mults: dict[tuple[int, ...], int] = {lam: 1}
    if all(x == 0 for x in lam):
        return mults

    # Generate all candidate dominant weights mu <= lambda via bounded box on k
    # Since mu = lambda - k * A >= 0 and (A^-1)_ij > 0 for all i, j:
    # k_j = sum_i (lambda_i - mu_i) (A^-1)_ij <= sum_i lambda_i (A^-1)_ij
    inv_cartan = _get_cartan_inverse(algebra)
    k_max = [sum(lam[i] * inv_cartan[i][j] for i in range(rank)) for j in range(rank)]
    ranges = [range(int(k_max[j]) + 1) for j in range(rank)]

    dominant_candidates: dict[tuple[int, ...], tuple[int, ...]] = {}
    for k in product(*ranges):
        mu = tuple(lam[i] - sum(cartan[j][i] * k[j] for j in range(rank)) for i in range(rank))
        if all(x >= 0 for x in mu):
            dominant_candidates[mu] = k

    # Sort dominant candidates by height (sum(k)) ascending
    sorted_candidates = sorted(
        dominant_candidates.items(), key=lambda item: (sum(item[1]), item[0])
    )

    # Now solve Freudenthal recursion in increasing order of height
    for mu, k in sorted_candidates:
        if mu == lam:
            continue

        # Denominator: (lambda + mu + 2*rho, lambda - mu)
        # = sum_j k_j * d_j * (lambda_j + mu_j + 2)
        denom = sum(k[j] * d[j] * (lam[j] + mu[j] + 2) for j in range(rank))
        if denom <= 0:
            continue

        # Numerator: 2 * sum_{alpha > 0} sum_{n >= 1} (mu + n*alpha, alpha) * m(mu + n*alpha)
        num = 0
        for r_idx, r in enumerate(roots):
            r_dynk = roots_dynk[r_idx]
            norm_r = root_norms[r_idx]
            n = 1
            while True:
                target = tuple(mu[j] + n * r_dynk[j] for j in range(rank))
                dom_target = reflect_to_dominant(algebra, target)

                # If dom_target > lam, m = 0
                m = mults.get(dom_target, 0)
                if m > 0:
                    val = inner_product_weight_root(algebra, mu, r) + n * norm_r
                    num += 2 * val * m

                # Stop climbing if target exceeds highest weight height
                if any(dom_target[j] > lam[j] + 10 for j in range(rank)) or n > 25:
                    break
                n += 1

        m_mu = num // denom
        if m_mu > 0:
            mults[mu] = m_mu

    return mults


def klimyk_weyl_action(algebra: str, gamma: tuple[int, ...]) -> tuple[int, tuple[int, ...] | None]:
    """Reflects gamma into the strictly dominant chamber (all labels > 0).

    Returns (sign, w_gamma) where sign is (-1)^length(w).
    If gamma lies on a chamber wall (any label == 0 at any step), returns (0, None).
    """
    cartan = get_cartan_matrix(algebra)
    rank = len(cartan)
    curr = list(gamma)
    sign = 1

    for _ in range(100):
        if any(x == 0 for x in curr):
            return 0, None
        if all(x > 0 for x in curr):
            return sign, tuple(curr)

        # Reflect across first negative index
        for i in range(rank):
            if curr[i] < 0:
                val = curr[i]
                for j in range(rank):
                    curr[j] -= val * cartan[i][j]
                sign = -sign
                break

    return 0, None


def get_all_weights_with_multiplicities(
    algebra: str,
    highest_weight: tuple[int, ...] | list[int],
) -> dict[tuple[int, ...], int]:
    """Generates ALL weights of the irreducible representation with their multiplicities."""
    dom_mults = freudenthal_multiplicities(algebra, highest_weight)
    all_weights: dict[tuple[int, ...], int] = {}

    cartan = get_cartan_matrix(algebra)
    rank = len(cartan)

    for dom_w, mult in dom_mults.items():
        # Generate Weyl orbit of dom_w
        visited: set[tuple[int, ...]] = {dom_w}
        queue = deque([dom_w])
        while queue:
            curr = queue.popleft()
            all_weights[curr] = mult
            for i in range(rank):
                val = curr[i]
                if val != 0:
                    new_w = tuple(curr[j] - val * cartan[i][j] for j in range(rank))
                    if new_w not in visited:
                        visited.add(new_w)
                        queue.append(new_w)

    return all_weights


def tensor_product_decomposition(
    algebra: str,
    left_weight: tuple[int, ...] | list[int],
    right_weight: tuple[int, ...] | list[int],
    max_product_dimension: int = 1_000_000,
) -> dict[tuple[int, ...], int]:
    """Decomposes V(left) (x) V(right) into irreducible components via the Brauer-Klimyk rule."""
    lam1 = reflect_to_dominant(algebra, left_weight)
    lam2 = reflect_to_dominant(algebra, right_weight)

    dim1 = weyl_dimension(algebra, lam1)
    dim2 = weyl_dimension(algebra, lam2)

    if dim1 * dim2 > max_product_dimension:
        raise ValueError(
            f"Product dimension {dim1} * {dim2} = {dim1 * dim2} exceeds max limit {max_product_dimension}"
        )

    # Use smaller representation for weight expansion
    if dim1 >= dim2:
        big_lam, small_lam = lam1, lam2
    else:
        big_lam, small_lam = lam2, lam1

    small_weights = get_all_weights_with_multiplicities(algebra, small_lam)
    rank = len(big_lam)
    decomp: dict[tuple[int, ...], int] = {}

    # Brauer-Klimyk formula:
    # V(big) (x) V(small) = sum_{nu in wt(small)} m(nu) * (-1)^l(w) * V(w(big + nu + rho) - rho)
    for nu, mult in small_weights.items():
        gamma = tuple(big_lam[i] + nu[i] + 1 for i in range(rank))
        sign, w_gamma = klimyk_weyl_action(algebra, gamma)
        if sign != 0 and w_gamma is not None:
            target = tuple(w_gamma[i] - 1 for i in range(rank))
            decomp[target] = decomp.get(target, 0) + sign * mult

    # Remove zero or negative multiplicities (should be non-negative)
    return {k: v for k, v in decomp.items() if v > 0}
