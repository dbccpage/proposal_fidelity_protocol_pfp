"""Executable verification suite for Window 2 Wave 2 Shard D (Note 004).

Derivations verified:
- AUDIT-N004-001: Functorial Banach presheaf (ATL-N004-001)
- AUDIT-N004-002: Strict completion from covering edges (ATL-N004-002)
- AUDIT-N004-003: Diamond path-independence (ATL-N004-003)
- AUDIT-N004-010: Payload-curvature factorization boundary (ATL-N004-010)

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Mapping, Sequence, Set, Tuple
import pytest

# ---------------------------------------------------------------------------
# Exact Rational Linear Algebra Helpers
# ---------------------------------------------------------------------------

Matrix = List[List[Fraction]]
Vector = Tuple[Fraction, ...]


def mat_zeros(rows: int, cols: int) -> Matrix:
    """Return zero matrix of dimension rows x cols."""
    return [[Fraction(0) for _ in range(cols)] for _ in range(rows)]


def mat_eye(n: int) -> Matrix:
    """Return identity matrix of dimension n x n."""
    res = mat_zeros(n, n)
    for i in range(n):
        res[i][i] = Fraction(1)
    return res


def mat_mul_vec(m: Matrix, v: Sequence[Fraction]) -> Vector:
    """Multiply rational matrix m by rational vector v."""
    return tuple(
        sum((m[r][c] * v[c] for c in range(len(v))), Fraction(0))
        for r in range(len(m))
    )


def mat_mul_mat(a: Matrix, b: Matrix) -> Matrix:
    """Multiply rational matrix a by rational matrix b."""
    rows_a = len(a)
    cols_a = len(a[0])
    rows_b = len(b)
    cols_b = len(b[0])
    if cols_a != rows_b:
        raise ValueError(f"Incompatible matrix multiplication dimensions: ({rows_a}, {cols_a}) x ({rows_b}, {cols_b})")
    res: Matrix = []
    for r in range(rows_a):
        row: List[Fraction] = []
        for c in range(cols_b):
            val = sum((a[r][k] * b[k][c] for k in range(cols_a)), Fraction(0))
            row.append(val)
        res.append(row)
    return res


def mat_sub(a: Matrix, b: Matrix) -> Matrix:
    """Subtract rational matrix b from a."""
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        raise ValueError("Matrix dimensions must agree for subtraction")
    return [
        [a[r][c] - b[r][c] for c in range(len(a[0]))]
        for r in range(len(a))
    ]


def mat_equal(a: Matrix, b: Matrix) -> bool:
    """Check exact equality of rational matrices."""
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        return False
    return all(a[r][c] == b[r][c] for r in range(len(a)) for c in range(len(a[0])))


def mat_is_zero(m: Matrix) -> bool:
    """Check if rational matrix is identically zero."""
    return all(m[r][c] == Fraction(0) for r in range(len(m)) for c in range(len(m[0])))


def mat_l1_op_norm(m: Matrix) -> Fraction:
    """Operator norm induced by l1 vector norm: maximum absolute column sum."""
    cols = len(m[0])
    rows = len(m)
    return max(
        sum(abs(m[r][c]) for r in range(rows))
        for c in range(cols)
    )


def is_contractive(m: Matrix) -> bool:
    """Check if matrix is contractive under the induced l1 operator norm."""
    return mat_l1_op_norm(m) <= Fraction(1)


# ---------------------------------------------------------------------------
# Finite Poset & Banach Presheaf Models
# ---------------------------------------------------------------------------

class PosetCarrier:
    """Finite partially ordered set defined by elements and relation pairs."""

    def __init__(
        self,
        elements: Sequence[str],
        relations: Sequence[Tuple[str, str]],
    ) -> None:
        self.elements = sorted(set(elements))
        # Compute reflexive-transitive closure
        self._leq: Set[Tuple[str, str]] = {(x, x) for x in self.elements}
        for a, b in relations:
            self._leq.add((a, b))

        # Floyd-Warshall transitive closure
        n = len(self.elements)
        elem_list = list(self.elements)
        for k in elem_list:
            for i in elem_list:
                for j in elem_list:
                    if (i, k) in self._leq and (k, j) in self._leq:
                        self._leq.add((i, j))

    def is_le(self, a: str, b: str) -> bool:
        """True if a <= b."""
        return (a, b) in self._leq

    def covering_edges(self) -> List[Tuple[str, str]]:
        """Covering relations a -< b (a < b with no intermediate x)."""
        cov: List[Tuple[str, str]] = []
        for a in self.elements:
            for b in self.elements:
                if a != b and self.is_le(a, b):
                    # Check if there exists intermediate x
                    has_mid = any(
                        x != a and x != b and self.is_le(a, x) and self.is_le(x, b)
                        for x in self.elements
                    )
                    if not has_mid:
                        cov.append((a, b))
        return sorted(cov)

    def saturated_chains(self, a: str, b: str) -> List[List[str]]:
        """All maximal / saturated chains of covering edges from a to b."""
        if not self.is_le(a, b):
            return []
        if a == b:
            return [[a]]
        chains: List[List[str]] = []
        cov_edges = self.covering_edges()
        for lower, upper in cov_edges:
            if lower == a and self.is_le(upper, b):
                sub_chains = self.saturated_chains(upper, b)
                for sc in sub_chains:
                    chains.append([a] + sc)
        return chains


class BanachPresheaf:
    """Contravariant functor F: P^op -> Ban on a finite poset."""

    def __init__(
        self,
        poset: PosetCarrier,
        fiber_dims: Mapping[str, int],
        restrictions: Mapping[Tuple[str, str], Matrix],
    ) -> None:
        self.poset = poset
        self.fiber_dims = dict(fiber_dims)
        self.restrictions = dict(restrictions)

    def validate_presheaf_laws(self) -> Tuple[bool, str]:
        """Validate identity, composition, and contractivity laws."""
        # 1. Identity law
        for x in self.poset.elements:
            pair = (x, x)
            expected = mat_eye(self.fiber_dims[x])
            actual = self.restrictions.get(pair)
            if actual is None:
                return False, f"Missing identity restriction for {x}"
            if not mat_equal(actual, expected):
                return False, f"Identity law violated at {x}"

        # 2. Composition law and Contractivity
        for x in self.poset.elements:
            for y in self.poset.elements:
                if not self.poset.is_le(x, y):
                    continue
                r_yx = self.restrictions.get((x, y))
                if r_yx is None:
                    return False, f"Missing restriction for comparable pair ({x}, {y})"
                if not is_contractive(r_yx):
                    return False, f"Restriction ({x}, {y}) is not contractive (norm = {mat_l1_op_norm(r_yx)})"

                for z in self.poset.elements:
                    if not self.poset.is_le(y, z):
                        continue
                    r_zy = self.restrictions.get((y, z))
                    r_zx = self.restrictions.get((x, z))
                    if r_zy is None or r_zx is None:
                        return False, f"Missing restriction in composition triple ({x}, {y}, {z})"
                    comp = mat_mul_mat(r_yx, r_zy)
                    if not mat_equal(comp, r_zx):
                        return False, f"Composition defect at triple ({x}, {y}, {z})"

        return True, "Valid functorial Banach presheaf"


def strict_completion_from_covering(
    poset: PosetCarrier,
    fiber_dims: Mapping[str, int],
    covering_restrictions: Mapping[Tuple[str, str], Matrix],
) -> BanachPresheaf:
    """Construct unique functorial presheaf extension from covering-edge maps."""
    cov_edges = set(poset.covering_edges())

    # Verify covering restrictions provided and contractive
    for edge in cov_edges:
        if edge not in covering_restrictions:
            raise ValueError(f"Missing covering restriction for {edge}")
        if not is_contractive(covering_restrictions[edge]):
            raise ValueError(f"Covering restriction {edge} is not contractive")

    completed: Dict[Tuple[str, str], Matrix] = {}

    for x in poset.elements:
        completed[(x, x)] = mat_eye(fiber_dims[x])

    for a in poset.elements:
        for b in poset.elements:
            if a == b or not poset.is_le(a, b):
                continue
            chains = poset.saturated_chains(a, b)
            if not chains:
                raise ValueError(f"Poset transitivity obstruction: no saturated chain for {a} <= {b}")

            # Compute composite along first chain
            first_chain = chains[0]
            curr = mat_eye(fiber_dims[b])
            for i in range(len(first_chain) - 1, 0, -1):
                upper = first_chain[i]
                lower = first_chain[i - 1]
                edge_mat = covering_restrictions[(lower, upper)]
                curr = mat_mul_mat(edge_mat, curr)
            first_comp = curr

            # Path A requirement: check all alternative chains agree
            for alt in chains[1:]:
                alt_curr = mat_eye(fiber_dims[b])
                for i in range(len(alt) - 1, 0, -1):
                    upper = alt[i]
                    lower = alt[i - 1]
                    edge_mat = covering_restrictions[(lower, upper)]
                    alt_curr = mat_mul_mat(edge_mat, alt_curr)
                if not mat_equal(first_comp, alt_curr):
                    raise ValueError(f"Path A hypothesis violated: chains {first_chain} and {alt} yield different composites")

            completed[(a, b)] = first_comp

    sheaf = BanachPresheaf(poset, fiber_dims, completed)
    valid, msg = sheaf.validate_presheaf_laws()
    if not valid:
        raise ValueError(f"Strict completion failed presheaf validation: {msg}")
    return sheaf


# ---------------------------------------------------------------------------
# Curvature Packet and Quotient Model
# ---------------------------------------------------------------------------

class DiscreteCurvaturePacket:
    """Packet carrying a local payload vector and a global curvature defect vector."""

    def __init__(self, payload: Sequence[Fraction], curvature: Sequence[Fraction]) -> None:
        self.payload = tuple(payload)
        self.curvature = tuple(curvature)

    def __repr__(self) -> str:
        return f"Packet(payload={self.payload}, curvature={self.curvature})"


class DiscretePayloadQuotient:
    """Payload quotient classifier and congruence verification."""

    @staticmethod
    def payload_equiv(p1: DiscreteCurvaturePacket, p2: DiscreteCurvaturePacket) -> bool:
        """True if packets share identical local payloads."""
        return p1.payload == p2.payload

    @staticmethod
    def joint_equiv(p1: DiscreteCurvaturePacket, p2: DiscreteCurvaturePacket) -> bool:
        """True if packets share both identical payloads and curvatures."""
        return p1.payload == p2.payload and p1.curvature == p2.curvature

    @classmethod
    def payload_factors_through_quotient(cls, packets: Sequence[DiscreteCurvaturePacket]) -> bool:
        """Verify local payload observation is invariant-congruent under payload equivalence."""
        for i, p1 in enumerate(packets):
            for p2 in packets[i + 1:]:
                if cls.payload_equiv(p1, p2):
                    if p1.payload != p2.payload:
                        return False
        return True

    @classmethod
    def curvature_factors_through_payload_quotient(cls, packets: Sequence[DiscreteCurvaturePacket]) -> bool:
        """Check whether curvature observable factors through the payload-only quotient."""
        for i, p1 in enumerate(packets):
            for p2 in packets[i + 1:]:
                if cls.payload_equiv(p1, p2):
                    if p1.curvature != p2.curvature:
                        return False
        return True

    @classmethod
    def curvature_factors_through_joint_quotient(cls, packets: Sequence[DiscreteCurvaturePacket]) -> bool:
        """Check whether curvature observable factors through joint equivalence."""
        for i, p1 in enumerate(packets):
            for p2 in packets[i + 1:]:
                if cls.joint_equiv(p1, p2):
                    if p1.curvature != p2.curvature:
                        return False
        return True


# ===========================================================================
# Target 1: AUDIT-N004-001 (Functorial Banach presheaf)
# ===========================================================================

def test_audit_n004_001_functorial_presheaf_positive() -> None:
    """Validates identity law and chain composition on a 3-element chain with 2D fibers."""
    poset = PosetCarrier(elements=["0", "1", "2"], relations=[("0", "1"), ("1", "2")])
    fiber_dims = {"0": 2, "1": 2, "2": 2}

    # Contractive restriction maps
    r_21: Matrix = [
        [Fraction(1, 2), Fraction(1, 4)],
        [Fraction(0), Fraction(1, 2)],
    ]
    r_10: Matrix = [
        [Fraction(2, 3), Fraction(0)],
        [Fraction(1, 6), Fraction(1, 3)],
    ]
    # Functorial composite r_20 = r_10 * r_21
    r_20 = mat_mul_mat(r_10, r_21)

    restrictions: Dict[Tuple[str, str], Matrix] = {
        ("0", "0"): mat_eye(2),
        ("1", "1"): mat_eye(2),
        ("2", "2"): mat_eye(2),
        ("0", "1"): r_10,
        ("1", "2"): r_21,
        ("0", "2"): r_20,
    }

    presheaf = BanachPresheaf(poset, fiber_dims, restrictions)
    valid, msg = presheaf.validate_presheaf_laws()
    assert valid, f"Expected valid Banach presheaf, got: {msg}"
    assert is_contractive(r_20), "Composite of contractive maps must be contractive"


def test_audit_n004_001_functorial_presheaf_negative_composition_defect() -> None:
    """Introduces an off-diagonal perturbation into r_{c,a}; asserts composition defect detection."""
    poset = PosetCarrier(elements=["0", "1", "2"], relations=[("0", "1"), ("1", "2")])
    fiber_dims = {"0": 2, "1": 2, "2": 2}

    r_21: Matrix = [
        [Fraction(1, 2), Fraction(1, 4)],
        [Fraction(0), Fraction(1, 2)],
    ]
    r_10: Matrix = [
        [Fraction(2, 3), Fraction(0)],
        [Fraction(1, 6), Fraction(1, 3)],
    ]
    r_20 = mat_mul_mat(r_10, r_21)
    # Perturb r_20
    r_20_perturbed = [
        [r_20[0][0] + Fraction(1, 10), r_20[0][1]],
        [r_20[1][0], r_20[1][1]],
    ]

    restrictions: Dict[Tuple[str, str], Matrix] = {
        ("0", "0"): mat_eye(2),
        ("1", "1"): mat_eye(2),
        ("2", "2"): mat_eye(2),
        ("0", "1"): r_10,
        ("1", "2"): r_21,
        ("0", "2"): r_20_perturbed,
    }

    presheaf = BanachPresheaf(poset, fiber_dims, restrictions)
    valid, msg = presheaf.validate_presheaf_laws()
    assert not valid, "Perturbed composite must fail functorial composition law"
    assert "Composition defect" in msg


def test_audit_n004_001_functorial_presheaf_negative_non_contractive() -> None:
    """Evaluates a matrix with operator norm > 1; asserts violation of contractivity requirement."""
    poset = PosetCarrier(elements=["0", "1"], relations=[("0", "1")])
    fiber_dims = {"0": 2, "1": 2}

    # Matrix with column sum = 3/2 > 1
    r_non_contractive: Matrix = [
        [Fraction(3, 4), Fraction(1, 2)],
        [Fraction(3, 4), Fraction(1, 4)],
    ]
    assert mat_l1_op_norm(r_non_contractive) == Fraction(3, 2)
    assert not is_contractive(r_non_contractive)

    restrictions: Dict[Tuple[str, str], Matrix] = {
        ("0", "0"): mat_eye(2),
        ("1", "1"): mat_eye(2),
        ("0", "1"): r_non_contractive,
    }

    presheaf = BanachPresheaf(poset, fiber_dims, restrictions)
    valid, msg = presheaf.validate_presheaf_laws()
    assert not valid, "Presheaf with norm > 1 must fail contractivity requirement"
    assert "not contractive" in msg


# ===========================================================================
# Target 2: AUDIT-N004-002 (Strict completion from covering edges)
# ===========================================================================

def test_audit_n004_002_strict_completion_positive() -> None:
    """Validates unique direct extension from path-independent covering-edge maps on a diamond."""
    poset = PosetCarrier(
        elements=["0", "1", "2", "3"],
        relations=[("0", "1"), ("0", "2"), ("1", "3"), ("2", "3")],
    )
    fiber_dims = {"0": 2, "1": 2, "2": 2, "3": 2}

    # Covering edges: (0, 1), (0, 2), (1, 3), (2, 3)
    # Left path: 3 -> 1 -> 0
    # Right path: 3 -> 2 -> 0
    r_31: Matrix = [
        [Fraction(1, 2), Fraction(0)],
        [Fraction(0), Fraction(1, 3)],
    ]
    r_10: Matrix = [
        [Fraction(1, 2), Fraction(0)],
        [Fraction(0), Fraction(1, 2)],
    ]
    # Left composite: r_10 * r_31 = diag(1/4, 1/6)
    left_comp = mat_mul_mat(r_10, r_31)

    r_32: Matrix = [
        [Fraction(1, 4), Fraction(0)],
        [Fraction(0), Fraction(1, 6)],
    ]
    r_20: Matrix = [
        [Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(1)],
    ]
    # Right composite: r_20 * r_32 = diag(1/4, 1/6)
    right_comp = mat_mul_mat(r_20, r_32)
    assert mat_equal(left_comp, right_comp), "Covering edges must commute along diamond"

    covering_restrictions: Dict[Tuple[str, str], Matrix] = {
        ("0", "1"): r_10,
        ("0", "2"): r_20,
        ("1", "3"): r_31,
        ("2", "3"): r_32,
    }

    presheaf = strict_completion_from_covering(poset, fiber_dims, covering_restrictions)
    assert mat_equal(presheaf.restrictions[("0", "3")], left_comp)
    assert is_contractive(presheaf.restrictions[("0", "3")])


def test_audit_n004_002_strict_completion_negative_path_dependent_diamond() -> None:
    """Perturbs one branch of diamond; asserts rejection of unique completion."""
    poset = PosetCarrier(
        elements=["0", "1", "2", "3"],
        relations=[("0", "1"), ("0", "2"), ("1", "3"), ("2", "3")],
    )
    fiber_dims = {"0": 2, "1": 2, "2": 2, "3": 2}

    r_31: Matrix = [
        [Fraction(1, 2), Fraction(0)],
        [Fraction(0), Fraction(1, 3)],
    ]
    r_10: Matrix = [
        [Fraction(1, 2), Fraction(0)],
        [Fraction(0), Fraction(1, 2)],
    ]
    # Perturbed right branch: diag(1/3, 1/6) != diag(1/4, 1/6)
    r_32_perturbed: Matrix = [
        [Fraction(1, 3), Fraction(0)],
        [Fraction(0), Fraction(1, 6)],
    ]
    r_20: Matrix = [
        [Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(1)],
    ]

    covering_restrictions: Dict[Tuple[str, str], Matrix] = {
        ("0", "1"): r_10,
        ("0", "2"): r_20,
        ("1", "3"): r_31,
        ("2", "3"): r_32_perturbed,
    }

    with pytest.raises(ValueError, match="Path A hypothesis violated"):
        strict_completion_from_covering(poset, fiber_dims, covering_restrictions)


def test_audit_n004_002_strict_completion_negative_non_transitive_obstruction() -> None:
    """Asserts that missing covering restriction or non-contractive map obstructs extension."""
    poset = PosetCarrier(
        elements=["0", "1", "2"],
        relations=[("0", "1"), ("1", "2")],
    )
    fiber_dims = {"0": 2, "1": 2, "2": 2}

    # Only supply restriction for (0, 1), omitting (1, 2)
    incomplete_covering: Dict[Tuple[str, str], Matrix] = {
        ("0", "1"): mat_eye(2),
    }

    with pytest.raises(ValueError, match="Missing covering restriction"):
        strict_completion_from_covering(poset, fiber_dims, incomplete_covering)


# ===========================================================================
# Target 3: AUDIT-N004-003 (Diamond path-independence)
# ===========================================================================

def test_audit_n004_003_diamond_path_independence_positive() -> None:
    """Evaluates composite restrictions around an elementary diamond with 3D stalk spaces."""
    # Elementary diamond: bottom=0, left=1, right=2, top=3
    poset = PosetCarrier(
        elements=["0", "1", "2", "3"],
        relations=[("0", "1"), ("0", "2"), ("1", "3"), ("2", "3")],
    )
    dim = 3
    # Non-trivial contractive matrices for left branch (3 -> 1 -> 0)
    r_31: Matrix = [
        [Fraction(1, 3), Fraction(1, 6), Fraction(0)],
        [Fraction(0), Fraction(1, 3), Fraction(1, 6)],
        [Fraction(0), Fraction(0), Fraction(1, 2)],
    ]
    r_10: Matrix = [
        [Fraction(1, 2), Fraction(0), Fraction(1, 4)],
        [Fraction(0), Fraction(1, 2), Fraction(0)],
        [Fraction(1, 4), Fraction(0), Fraction(1, 2)],
    ]
    left_comp = mat_mul_mat(r_10, r_31)

    # In a strict presheaf, direct restriction r_30 equals left_comp
    r_30 = left_comp

    # Right branch factors r_30 as r_20 * r_32
    # Let r_20 = identity, r_32 = left_comp
    r_20 = mat_eye(dim)
    r_32 = left_comp
    right_comp = mat_mul_mat(r_20, r_32)

    # Defect matrix around diamond
    defect = mat_sub(left_comp, right_comp)
    assert mat_is_zero(defect), "Diamond defect matrix must be identically zero in strict presheaf"

    # Verify action on sections
    section_c = (Fraction(3), Fraction(-2), Fraction(5))
    val_left = mat_mul_vec(left_comp, section_c)
    val_right = mat_mul_vec(right_comp, section_c)
    val_direct = mat_mul_vec(r_30, section_c)
    assert val_left == val_right == val_direct


def test_audit_n004_003_diamond_path_independence_negative_gauge_defect() -> None:
    """Introduces a gauge/curvature defect into one branch; asserts non-zero defect is detected."""
    dim = 2
    r_31: Matrix = [
        [Fraction(1, 2), Fraction(0)],
        [Fraction(0), Fraction(1, 2)],
    ]
    r_10: Matrix = [
        [Fraction(1, 2), Fraction(0)],
        [Fraction(0), Fraction(1, 2)],
    ]
    left_comp = mat_mul_mat(r_10, r_31)  # diag(1/4, 1/4)

    # Gauge defect: non-zero off-diagonal perturbation theta
    theta = Fraction(1, 8)
    r_32: Matrix = [
        [Fraction(1, 4), theta],
        [Fraction(0), Fraction(1, 4)],
    ]
    r_20: Matrix = mat_eye(dim)
    right_comp = mat_mul_mat(r_20, r_32)

    defect = mat_sub(left_comp, right_comp)
    assert not mat_is_zero(defect), "Perturbed diamond must yield non-zero defect matrix"
    assert defect[0][1] == -theta


def test_audit_n004_003_diamond_path_independence_negative_dimension_mismatch() -> None:
    """Asserts failure during composition if fiber dimensions are incompatible."""
    # Stalk 3 has dim 3, stalk 1 has dim 2, stalk 0 has dim 2
    r_31 = mat_zeros(2, 3)
    # Attempting to multiply incompatible matrix shape (2, 2) by (4, 4) raises ValueError
    r_invalid = mat_zeros(4, 4)
    with pytest.raises(ValueError, match="Incompatible matrix multiplication dimensions"):
        mat_mul_mat(r_31, r_invalid)


# ===========================================================================
# Target 4: AUDIT-N004-010 (Payload-curvature factorization boundary)
# ===========================================================================

def test_audit_n004_010_payload_curvature_factorization_positive_lggr() -> None:
    """Constructs packets with identical payloads and differing curvatures; asserts Local Green, Global Red."""
    # Common local payload
    payload = (Fraction(1), Fraction(2), Fraction(3))
    # Distinct curvature defect observables
    curvature_k = (Fraction(0),)
    curvature_l = (Fraction(5),)

    p1 = DiscreteCurvaturePacket(payload=payload, curvature=curvature_k)
    p2 = DiscreteCurvaturePacket(payload=payload, curvature=curvature_l)
    packets = [p1, p2]

    # Under payload primitive difference, p1 ~ p2
    assert DiscretePayloadQuotient.payload_equiv(p1, p2)

    # Local payload observation factors through payload quotient (Local Green)
    assert DiscretePayloadQuotient.payload_factors_through_quotient(packets)

    # Global curvature observation FAILS to factor through payload quotient (Global Red)
    assert not DiscretePayloadQuotient.curvature_factors_through_payload_quotient(packets)


def test_audit_n004_010_payload_curvature_factorization_negative_quotient_refutation() -> None:
    """Shows that projecting curvature through payload-only quotient equates distinct curvatures, refuting descent."""
    payload = (Fraction(10), Fraction(20))
    curvature_a = (Fraction(1, 2),)
    curvature_b = (Fraction(3, 4),)
    assert curvature_a != curvature_b

    p1 = DiscreteCurvaturePacket(payload=payload, curvature=curvature_a)
    p2 = DiscreteCurvaturePacket(payload=payload, curvature=curvature_b)

    # If curvature were constant on the payload fiber, p1.curvature would equal p2.curvature
    fibers_constant = (p1.curvature == p2.curvature)
    assert not fibers_constant, "Curvature is not fiber-constant across payload-equivalent states"

    # Attempting to assign a single quotient representative value leads to contradiction
    # Representative chosen from p1 yields curvature_a, but evaluating on p2 yields curvature_b
    quotient_rep_error = tuple(p1.curvature[i] - p2.curvature[i] for i in range(len(curvature_a)))
    assert quotient_rep_error == (Fraction(-1, 4),)


def test_audit_n004_010_payload_curvature_factorization_positive_joint_quotient() -> None:
    """Evaluates joint equivalence preserving both payload and curvature; asserts faithful descent of both."""
    payload_1 = (Fraction(1), Fraction(0))
    payload_2 = (Fraction(1), Fraction(0))
    curv_1 = (Fraction(7),)
    curv_2 = (Fraction(7),)

    p1 = DiscreteCurvaturePacket(payload=payload_1, curvature=curv_1)
    p2 = DiscreteCurvaturePacket(payload=payload_2, curvature=curv_2)
    packets = [p1, p2]

    # Under joint equivalence, both payload and curvature factor
    assert DiscretePayloadQuotient.joint_equiv(p1, p2)
    assert DiscretePayloadQuotient.payload_factors_through_quotient(packets)
    assert DiscretePayloadQuotient.curvature_factors_through_joint_quotient(packets)
