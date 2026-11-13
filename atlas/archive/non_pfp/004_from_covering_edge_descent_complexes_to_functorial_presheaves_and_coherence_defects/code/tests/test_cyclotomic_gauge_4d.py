"""Targeted verification and mutation tests for exact rational non-abelian gauge group holonomies on 4D simplicial complexes.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from pathlib import Path
from fractions import Fraction
import pytest

# Ensure code directory is on sys.path
CODE_DIR = Path(__file__).resolve().parent.parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from cyclotomic_gauge import (
    Cyclotomic,
    CyclotomicMatrix,
    NonAbelianGaugeGroup,
    Simplex4D,
    FourSimplexHingeStar,
    NonAbelianSimplicialGaugeSystem,
    FourSimplexGaugeSystem,
    TetrahedronBianchiVerification,
    FourSimplexBianchiVerification,
)


# ---------------------------------------------------------------------------
# 1. Cyclotomic Number Field Arithmetic
# ---------------------------------------------------------------------------

def test_cyclotomic_algebraic_identities() -> None:
    """Verify exact algebraic identities in Q(zeta_8)."""
    zeta8 = Cyclotomic.zeta(8)
    one = Cyclotomic.one(8)
    zero = Cyclotomic.zero(8)

    # zeta_8^4 == -1
    zeta8_4 = zeta8 * zeta8 * zeta8 * zeta8
    assert zeta8_4 == -one

    # zeta_8^2 == i
    i_unit = Cyclotomic.i(8)
    assert zeta8 * zeta8 == i_unit
    assert i_unit * i_unit == -one

    # Exact sqrt(2) identity: (zeta_8 - zeta_8^3)^2 == 2
    sqrt2 = Cyclotomic.sqrt2(8)
    assert sqrt2 * sqrt2 == Cyclotomic.rational(2, 8)

    # 1/sqrt(2) * sqrt(2) == 1
    inv_sqrt2 = Cyclotomic.inv_sqrt2(8)
    assert inv_sqrt2 * sqrt2 == one

    # Field arithmetic: (1 + i) * (1 - i) == 2
    z = one + i_unit
    z_bar = z.conjugate()
    assert z_bar == one - i_unit
    assert z * z_bar == Cyclotomic.rational(2, 8)
    assert z.norm_squared() == Fraction(2, 1)

    # Invertibility
    z_inv = z.inverse()
    assert z * z_inv == one


# ---------------------------------------------------------------------------
# 2. CyclotomicMatrix Linear Algebra
# ---------------------------------------------------------------------------

def test_cyclotomic_matrix_algebra() -> None:
    """Verify matrix operations, trace, and adjoint over Q(zeta_8)."""
    i_unit = Cyclotomic.i(8)
    one = Cyclotomic.one(8)
    zero = Cyclotomic.zero(8)

    # Pauli matrices
    sigma_x = CyclotomicMatrix([[zero, one], [one, zero]], 8)
    sigma_y = CyclotomicMatrix([[zero, -i_unit], [i_unit, zero]], 8)
    sigma_z = CyclotomicMatrix([[one, zero], [zero, -one]], 8)

    assert sigma_x.is_unitary()
    assert sigma_y.is_unitary()
    assert sigma_z.is_unitary()

    # Pauli algebra: sigma_x * sigma_y == i * sigma_z
    prod_xy = sigma_x * sigma_y
    expected_xy = sigma_z * i_unit
    assert prod_xy == expected_xy

    # Trace is zero
    assert sigma_x.trace().is_zero()
    assert sigma_y.trace().is_zero()
    assert sigma_z.trace().is_zero()

    # Non-abelian commutator: [sigma_x, sigma_y] == 2i * sigma_z
    comm = sigma_x.commutator(sigma_y)
    expected_comm = sigma_z * (i_unit * Fraction(2, 1))
    assert comm == expected_comm
    assert not comm.is_zero()


# ---------------------------------------------------------------------------
# 3. Exact Discrete Non-Abelian Gauge Groups
# ---------------------------------------------------------------------------

def test_quaternion_group_q8_su2() -> None:
    """Verify quaternion group Q_8 relations and non-abelian properties in SU(2)."""
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)
    mat_1 = q8["1"]
    mat_neg_1 = q8["-1"]
    mat_i = q8["i"]
    mat_j = q8["j"]
    mat_k = q8["k"]

    # All 8 elements must be unitary
    for name, mat in q8.items():
        assert mat.is_unitary(), f"Q_8 element {name} is not unitary"

    # i^2 = j^2 = k^2 = ijk = -1
    assert mat_i * mat_i == mat_neg_1
    assert mat_j * mat_j == mat_neg_1
    assert mat_k * mat_k == mat_neg_1
    assert mat_i * mat_j * mat_k == mat_neg_1

    # Non-abelian multiplication: i * j == k, j * i == -k
    assert mat_i * mat_j == mat_k
    assert mat_j * mat_i == -mat_k
    assert mat_i * mat_j != mat_j * mat_i

    # Commutator [i, j] == 2k
    comm_ij = mat_i.commutator(mat_j)
    assert comm_ij == mat_k * Fraction(2, 1)


def test_binary_tetrahedral_group_2t() -> None:
    """Verify binary tetrahedral group 2T order and group closure."""
    elements = NonAbelianGaugeGroup.binary_tetrahedral_group_2t(8)
    assert len(elements) == 24

    for mat in elements:
        assert mat.is_unitary()

    # Test closure on subset of products
    for i in range(5):
        for j in range(5):
            prod = elements[i] * elements[j]
            assert any(prod == existing for existing in elements), "Group closure failed for 2T"


def test_clifford_plus_t_group() -> None:
    """Verify universal quantum gauge generators <H, T> in SU(2)."""
    gen = NonAbelianGaugeGroup.clifford_plus_t(8)
    H = gen["H"]
    T = gen["T"]
    S = gen["S"]
    X = gen["X"]
    Z = gen["Z"]

    assert H.is_unitary()
    assert T.is_unitary()
    assert S.is_unitary()

    # H^2 == I
    assert H * H == CyclotomicMatrix.eye(2, 8)

    # T^2 == S, S^2 == Z, Z^2 == I
    assert T * T == S
    assert S * S == Z
    assert Z * Z == CyclotomicMatrix.eye(2, 8)

    # H X H == Z, H Z H == X
    assert H * X * H == Z
    assert H * Z * H == X

    # Non-commutativity: [H, T] != 0
    assert not H.commutator(T).is_zero()


def test_su2_to_so4_spin_cover() -> None:
    """Verify spin double cover mapping Spin(4) = SU(2) x SU(2) -> SO(4)."""
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)
    i_mat = q8["i"]
    j_mat = q8["j"]
    one_mat = q8["1"]

    rot_i_1 = NonAbelianGaugeGroup.su2_to_so4(i_mat, one_mat)
    rot_1_j = NonAbelianGaugeGroup.su2_to_so4(one_mat, j_mat)

    assert (rot_i_1.rows, rot_i_1.cols) == (4, 4)
    assert rot_i_1.is_unitary()
    assert rot_1_j.is_unitary()

    # In SO(4), elements with real entries satisfy transpose == adjoint
    # Verify homomorphism property: R(U1, 1) * R(U2, 1) == R(U1 * U2, 1)
    rot_j_1 = NonAbelianGaugeGroup.su2_to_so4(j_mat, one_mat)
    rot_k_1 = NonAbelianGaugeGroup.su2_to_so4(q8["k"], one_mat)
    assert rot_i_1 * rot_j_1 == rot_k_1


# ---------------------------------------------------------------------------
# 4. 4D Simplicial Complex Triangulation & Dual Hinge Star
# ---------------------------------------------------------------------------

def test_four_simplex_properties() -> None:
    """Verify 4-simplex vertices, facets (tetrahedra), and hinges (triangles)."""
    s4 = Simplex4D((0, 1, 2, 3, 4))
    assert s4.vertices == (0, 1, 2, 3, 4)
    assert len(s4.tetrahedra()) == 5
    assert len(s4.triangle_hinges()) == 10


def test_four_simplex_hinge_star() -> None:
    """Verify 4D simplicial hinge star with closed dual loop."""
    # 4 pentachora meeting around triangle hinge (0, 1, 2)
    star = FourSimplexHingeStar(
        hinge_vertices=(0, 1, 2),
        perimeter_vertices=[3, 4, 5, 6],
    )
    assert len(star.simplices) == 4
    assert len(star.shared_tetrahedra) == 4
    assert len(star.dual_loop()) == 4

    # Each simplex must contain the hinge
    for s in star.simplices:
        assert set(star.hinge).issubset(set(s.vertices))


# ---------------------------------------------------------------------------
# 5. Non-Abelian Wilson Loop Holonomies & Curvature
# ---------------------------------------------------------------------------

def test_flat_gauge_connection_holonomy() -> None:
    """Verify that a flat connection yields identity holonomy and zero curvature."""
    star = FourSimplexHingeStar((0, 1, 2), [3, 4, 5, 6])
    system = NonAbelianSimplicialGaugeSystem(star, default_identity_group="SU2", conductor=8)

    w = system.compute_hinge_holonomy()
    eye = CyclotomicMatrix.eye(2, 8)
    assert w == eye

    k = system.compute_curvature_defect()
    assert k.is_zero()

    trace = system.wilson_loop_trace()
    assert trace.is_one()


def test_nonabelian_q8_curvature_defect() -> None:
    """Verify that non-abelian link transports around a 4D hinge produce exact non-zero curvature."""
    star = FourSimplexHingeStar((0, 1, 2), [3, 4, 5, 6])
    system = NonAbelianSimplicialGaugeSystem(star, default_identity_group="SU2", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)

    # Assign non-commuting transports along the 4 dual hops:
    # Hop 0: s0 -> s1 with transport i
    # Hop 1: s1 -> s2 with transport j
    # Hop 2: s2 -> s3 with transport -i
    # Hop 3: s3 -> s0 with transport -j
    loop = star.dual_loop()
    system.set_link_gauge_element(loop[0][0], loop[0][1], q8["i"])
    system.set_link_gauge_element(loop[1][0], loop[1][1], q8["j"])
    system.set_link_gauge_element(loop[2][0], loop[2][1], q8["-i"])
    system.set_link_gauge_element(loop[3][0], loop[3][1], q8["-j"])

    # Holonomy W = (-j) * (-i) * j * i = (j * i) * (j * i) = (-k) * (-k) = k^2 = -1
    w = system.compute_hinge_holonomy()
    assert w == q8["-1"]
    assert not w.is_zero()

    # Curvature defect K = W - I = -1 - 1 = -2 * I
    k = system.compute_curvature_defect()
    assert not k.is_zero()
    expected_k = CyclotomicMatrix.eye(2, 8) * Fraction(-2, 1)
    assert k == expected_k

    # Exact entry norm certificate: ||K||_F^2 = (-2)^2 + (-2)^2 = 8
    assert k.l1_entry_norm() == Fraction(8, 1)

    # Wilson loop trace is -1
    trace = system.wilson_loop_trace()
    assert trace == Cyclotomic.rational(-1, 8)


def test_nonabelian_path_reversal() -> None:
    """Verify that reversing orientation inverts the Wilson loop: W(h^{-1}) == W(h)^dagger."""
    star = FourSimplexHingeStar((0, 1, 2), [3, 4, 5])
    system = NonAbelianSimplicialGaugeSystem(star, default_identity_group="SU2", conductor=8)
    gen = NonAbelianGaugeGroup.clifford_plus_t(8)

    loop = star.dual_loop()
    system.set_link_gauge_element(loop[0][0], loop[0][1], gen["H"])
    system.set_link_gauge_element(loop[1][0], loop[1][1], gen["T"])
    system.set_link_gauge_element(loop[2][0], loop[2][1], gen["S"])

    w_forward = system.compute_hinge_holonomy(reverse=False)
    w_reverse = system.compute_hinge_holonomy(reverse=True)

    assert w_forward.is_unitary()
    assert w_reverse.is_unitary()
    assert w_reverse == w_forward.adjoint()
    assert w_forward * w_reverse == CyclotomicMatrix.eye(2, 8)


def test_gauge_transformation_covariance_and_trace_invariance() -> None:
    """Verify that local gauge transformations preserve the Wilson loop trace."""
    star = FourSimplexHingeStar((0, 1, 2), [3, 4, 5, 6])
    system = NonAbelianSimplicialGaugeSystem(star, default_identity_group="SU2", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)

    loop = star.dual_loop()
    system.set_link_gauge_element(loop[0][0], loop[0][1], q8["i"])
    system.set_link_gauge_element(loop[1][0], loop[1][1], q8["j"])

    trace_before = system.wilson_loop_trace()

    # Apply local gauge transformations g(sigma)
    gauge_trans = {
        star.simplices[0].id: q8["j"],
        star.simplices[1].id: q8["k"],
        star.simplices[2].id: q8["i"],
        star.simplices[3].id: q8["1"],
    }
    system.apply_gauge_transformation(gauge_trans)

    trace_after = system.wilson_loop_trace()

    # Gauge invariance of trace: Tr(W') == Tr(W)
    assert trace_before == trace_after


def test_so4_spacetime_curvature_holonomy() -> None:
    """Verify exact 4x4 SO(4) non-abelian curvature holonomy on a 4D hinge star."""
    star = FourSimplexHingeStar((0, 1, 2), [3, 4, 5, 6])
    system = NonAbelianSimplicialGaugeSystem(star, default_identity_group="SO4", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)

    rot_i = NonAbelianGaugeGroup.su2_to_so4(q8["i"], q8["1"])
    rot_j = NonAbelianGaugeGroup.su2_to_so4(q8["j"], q8["1"])

    loop = star.dual_loop()
    system.set_link_gauge_element(loop[0][0], loop[0][1], rot_i)
    system.set_link_gauge_element(loop[1][0], loop[1][1], rot_j)

    w = system.compute_hinge_holonomy()
    assert (w.rows, w.cols) == (4, 4)
    assert w.is_unitary()

    # Curvature defect is non-zero
    k = system.compute_curvature_defect()
    assert not k.is_zero()
    assert k.l1_entry_norm() > Fraction(0)


# ---------------------------------------------------------------------------
# 6. Adversarial Mutation Tests (Refutation Probes)
# ---------------------------------------------------------------------------

def test_falsify_mutated_link_breaks_unitarity() -> None:
    """Adversarial probe: A corrupted non-unitary link matrix must be rejected."""
    corrupted_data = [
        [Cyclotomic.one(8), Cyclotomic.one(8)],
        [Cyclotomic.zero(8), Cyclotomic.one(8)],
    ]
    corrupted_mat = CyclotomicMatrix(corrupted_data, 8)
    assert not corrupted_mat.is_unitary()

    star = FourSimplexHingeStar((0, 1, 2), [3, 4, 5])
    system = NonAbelianSimplicialGaugeSystem(star, default_identity_group="SU2", conductor=8)
    loop = star.dual_loop()

    with pytest.raises(AssertionError):
        system.set_link_gauge_element(loop[0][0], loop[0][1], corrupted_mat)


def test_falsify_swapped_path_ordering_detects_non_abelian_defect() -> None:
    """Adversarial probe: Swapping multiplication order of non-commuting links must produce different holonomies."""
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)
    u1 = q8["i"]
    u2 = q8["j"]

    order_12 = u1 * u2
    order_21 = u2 * u1
    assert order_12 != order_21
    assert order_12 == -order_21


def test_falsify_gauge_transformation_without_conjugation() -> None:
    """Adversarial probe: One-sided gauge transformation breaks trace invariance."""
    star = FourSimplexHingeStar((0, 1, 2), [3, 4, 5, 6])
    system = NonAbelianSimplicialGaugeSystem(star, default_identity_group="SU2", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)

    # Flat connection has Wilson loop trace 1
    trace_orig = system.wilson_loop_trace()
    assert trace_orig.is_one()

    # Corrupt a link with an un-conjugated one-sided transformation g = i
    link = star.dual_loop()[0]
    u = system.connection[link]
    g = q8["i"]
    corrupted_u = g * u  # Missing g_target^\dagger
    system.connection[link] = corrupted_u

    trace_corrupted = system.wilson_loop_trace()
    # Trace of i is 0, so 1 != 0
    assert trace_orig != trace_corrupted
    assert trace_corrupted.is_zero()


# ---------------------------------------------------------------------------
# 7. Discrete Bianchi Identity on 3-Cells (Tetrahedra) and 4-Simplices
# ---------------------------------------------------------------------------

def test_tetrahedron_discrete_bianchi_identity_flat_and_curved() -> None:
    """Verify discrete Bianchi identity on a single tetrahedron for flat and curved connections."""
    fs = FourSimplexGaugeSystem(vertices=(0, 1, 2, 3, 4), default_identity_group="SU2", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)
    one = q8["1"]
    eye = CyclotomicMatrix.eye(2, 8)

    # 1. Flat connection
    ver_flat = fs.verify_tetrahedron_bianchi((0, 1, 2, 3), basepoint=0)
    assert ver_flat.is_bianchi_satisfied
    assert ver_flat.curvature_defect.is_zero()
    assert ver_flat.linear_residual.is_zero()

    # 2. Genuinely curved non-abelian connection (non-pure-gauge)
    fs.set_link(0, 1, one)
    fs.set_link(0, 2, one)
    fs.set_link(0, 3, one)
    fs.set_link(3, 1, q8["i"])
    fs.set_link(2, 3, q8["j"])
    fs.set_link(1, 2, q8["k"])

    ver_curved = fs.verify_tetrahedron_bianchi((0, 1, 2, 3), basepoint=0)
    # Individual faces carry non-trivial curvature (w != eye)
    for w in ver_curved.based_face_holonomies:
        assert w != eye, "Individual faces must carry non-trivial curvature"

    # Despite non-trivial curvature on all faces, discrete Bianchi product must equal identity exactly
    assert ver_curved.is_bianchi_satisfied
    assert ver_curved.curvature_defect.is_zero()


def test_four_simplex_discrete_bianchi_across_all_five_tetrahedra() -> None:
    """Verify discrete Bianchi identity across all 5 bounding tetrahedra of a 4-simplex with Q_8 links."""
    fs = FourSimplexGaugeSystem(vertices=(0, 1, 2, 3, 4), default_identity_group="SU2", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)

    # Assign distinct non-abelian unitary link variables to all 10 edges of the 4-simplex
    links_data = [
        (0, 1, q8["i"]),
        (0, 2, q8["j"]),
        (0, 3, q8["k"]),
        (0, 4, q8["-1"]),
        (1, 2, q8["k"]),
        (1, 3, q8["i"]),
        (1, 4, q8["j"]),
        (2, 3, q8["j"]),
        (2, 4, q8["k"]),
        (3, 4, q8["i"]),
    ]
    for u, v, mat in links_data:
        fs.set_link(u, v, mat)

    # Verify all 5 tetrahedra bounding the 4-simplex
    res = fs.verify_four_simplex_bianchi(universal_basepoint=0)
    assert res.is_all_tetrahedra_satisfied
    assert res.boundary_curvature_defect.is_zero()
    assert len(res.tetrahedra_verifications) == 5

    for t_ver in res.tetrahedra_verifications:
        assert t_ver.is_bianchi_satisfied
        assert t_ver.curvature_defect.is_zero()


def test_four_simplex_bianchi_with_binary_tetrahedral_2t() -> None:
    """Verify discrete Bianchi identity on a 4-simplex with binary tetrahedral group 2T links."""
    fs = FourSimplexGaugeSystem(vertices=(0, 1, 2, 3, 4), default_identity_group="SU2", conductor=8)
    g_2t = NonAbelianGaugeGroup.binary_tetrahedral_group_2t(8)

    # Use elements involving 1/2 (+/- 1 +/- i +/- j +/- k)
    fs.set_link(0, 1, g_2t[8])
    fs.set_link(0, 2, g_2t[10])
    fs.set_link(0, 3, g_2t[14])
    fs.set_link(0, 4, g_2t[16])
    fs.set_link(1, 2, g_2t[18])
    fs.set_link(2, 3, g_2t[20])
    fs.set_link(3, 4, g_2t[22])

    res = fs.verify_four_simplex_bianchi(universal_basepoint=0)
    assert res.is_all_tetrahedra_satisfied
    assert res.boundary_curvature_defect.is_zero()


def test_four_simplex_bianchi_with_so4_spacetime_rotations() -> None:
    """Verify discrete Bianchi identity on a 4-simplex with 4D SO(4) spacetime rotation links."""
    fs = FourSimplexGaugeSystem(vertices=(0, 1, 2, 3, 4), default_identity_group="SO4", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)

    # Embed SU(2) x SU(2) into SO(4)
    r_i = NonAbelianGaugeGroup.su2_to_so4(q8["i"], q8["1"])
    r_j = NonAbelianGaugeGroup.su2_to_so4(q8["j"], q8["1"])
    r_k = NonAbelianGaugeGroup.su2_to_so4(q8["k"], q8["1"])
    r_ij = NonAbelianGaugeGroup.su2_to_so4(q8["i"], q8["j"])

    fs.set_link(0, 1, r_i)
    fs.set_link(0, 2, r_j)
    fs.set_link(1, 2, r_k)
    fs.set_link(2, 3, r_ij)
    fs.set_link(3, 4, r_i)

    res = fs.verify_four_simplex_bianchi(universal_basepoint=0)
    assert res.is_all_tetrahedra_satisfied
    assert res.boundary_curvature_defect.is_zero()


def test_four_simplex_bianchi_gauge_invariance() -> None:
    """Verify that local gauge transformations at vertices preserve discrete Bianchi identity."""
    fs = FourSimplexGaugeSystem(vertices=(0, 1, 2, 3, 4), default_identity_group="SU2", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)

    # Initial curved links
    fs.set_link(0, 1, q8["i"])
    fs.set_link(0, 2, q8["j"])
    fs.set_link(1, 2, q8["k"])
    fs.set_link(2, 3, q8["i"])
    fs.set_link(3, 4, q8["j"])

    # Local discrete gauge transformations at each vertex
    omega = {
        0: q8["j"],
        1: q8["k"],
        2: q8["i"],
        3: q8["-1"],
        4: q8["-j"],
    }
    fs.apply_gauge_transformation(omega)

    res = fs.verify_four_simplex_bianchi(universal_basepoint=0)
    assert res.is_all_tetrahedra_satisfied
    assert res.boundary_curvature_defect.is_zero()


def test_falsify_bianchi_with_reversed_face_orientation() -> None:
    """Adversarial probe: Reversing orientation of one face in Bianchi product breaks identity."""
    fs = FourSimplexGaugeSystem(vertices=(0, 1, 2, 3, 4), default_identity_group="SU2", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)
    one = q8["1"]

    fs.set_link(0, 1, one)
    fs.set_link(0, 2, one)
    fs.set_link(0, 3, one)
    fs.set_link(3, 1, q8["i"])
    fs.set_link(2, 3, q8["j"])
    fs.set_link(1, 2, q8["k"])

    ver = fs.verify_tetrahedron_bianchi((0, 1, 2, 3), basepoint=0)
    w1, w2, w3, w_opp = ver.based_face_holonomies

    # Correct Bianchi product
    b_correct = w1 * w2 * w3 * w_opp.adjoint()
    eye = CyclotomicMatrix.eye(2, 8)
    assert b_correct == eye

    # Corrupted Bianchi product with reversed orientation on Face 3 (w3 -> w3^\dagger = -k != k)
    b_corrupted = w1 * w2 * w3.adjoint() * w_opp.adjoint()
    assert b_corrupted != eye
    assert not (b_corrupted - eye).is_zero()


def test_falsify_bianchi_with_corrupted_internal_link() -> None:
    """Adversarial probe: Corrupting an internal link between faces breaks Bianchi cancellation."""
    fs = FourSimplexGaugeSystem(vertices=(0, 1, 2, 3, 4), default_identity_group="SU2", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)
    one = q8["1"]

    fs.set_link(0, 1, one)
    fs.set_link(0, 2, one)
    fs.set_link(0, 3, one)
    fs.set_link(3, 1, q8["i"])
    fs.set_link(2, 3, q8["j"])
    fs.set_link(1, 2, q8["k"])

    ver = fs.verify_tetrahedron_bianchi((0, 1, 2, 3), basepoint=0)
    w1, w2, w3, w_opp = ver.based_face_holonomies
    eye = CyclotomicMatrix.eye(2, 8)

    # Mutate the opposite face holonomy by a non-trivial factor
    w_opp_corrupted = q8["i"] * w_opp
    b_tampered = w1 * w2 * w3 * w_opp_corrupted.adjoint()
    assert b_tampered != eye
    assert not (b_tampered - eye).is_zero()


def test_falsify_bianchi_with_permuted_face_order() -> None:
    """Adversarial probe: Permuting non-abelian face multiplication order breaks cancellation."""
    fs = FourSimplexGaugeSystem(vertices=(0, 1, 2, 3, 4), default_identity_group="SU2", conductor=8)
    q8 = NonAbelianGaugeGroup.quaternion_group_q8(8)
    one = q8["1"]

    fs.set_link(0, 1, one)
    fs.set_link(0, 2, one)
    fs.set_link(0, 3, one)
    fs.set_link(3, 1, q8["i"])
    fs.set_link(2, 3, q8["j"])
    fs.set_link(1, 2, q8["k"])

    ver = fs.verify_tetrahedron_bianchi((0, 1, 2, 3), basepoint=0)
    w1, w2, w3, w_opp = ver.based_face_holonomies
    eye = CyclotomicMatrix.eye(2, 8)

    # Permuted order: w2 * w1 * w3 * w_opp^\dagger (swapping w1 and w2)
    b_permuted = w2 * w1 * w3 * w_opp.adjoint()
    # In non-abelian SU(2), w1=i and w2=j do not commute (ij = k, ji = -k)
    assert w1 * w2 != w2 * w1
    assert b_permuted != eye
    assert not (b_permuted - eye).is_zero()

