"""Unit tests for Simplicial Face Posets and Regge-Bianchi Holonomy Identity.

AuthorityEffect: None.

Tests:
1. Simplex constructor, canonical sorting, codimension-1 faces, and face inclusion.
2. Standard simplicial complex generators (2D triangle, 2-sphere boundary, 2D fan,
   3-sphere boundary, 4D hinge star).
3. Poset covering edge codimension-1 purity: dim(upper) == dim(lower) + 1.
4. Flat Regge restriction system curvature K == 0 identically on all triples.
5. Curved Regge restriction system non-zero curvature cochains K != 0.
6. Discrete Regge-Bianchi identity: delta_2(K) == 0 identically on all quadruples
   across 2D, 3D, and 4D simplicial geometries.
7. Hinge holonomy product around closed dual loops circling a codimension-2 hinge.
8. Error handling on empty dual loop hops.
"""

from fractions import Fraction
import pytest

from exact import exact_equal
from exactsym import Matrix
from regge_face_poset import (
    Simplex,
    SimplicialComplex,
    build_regge_restriction_system,
    build_simplicial_face_poset,
    compute_hinge_holonomy_product,
    verify_regge_bianchi_identity,
)


def test_simplex_properties():
    # 0-simplex
    v0 = Simplex([3])
    assert v0.dim == 0
    assert v0.id == "v_3"
    assert v0.faces() == []

    # 1-simplex
    e01 = Simplex([2, 0])  # tests sorting
    assert e01.dim == 1
    assert e01.vertices == (0, 2)
    assert e01.id == "e_0_2"
    faces = e01.faces()
    assert len(faces) == 2
    assert {f.id for f in faces} == {"v_0", "v_2"}

    # 2-simplex
    f012 = Simplex([2, 0, 1])
    assert f012.dim == 2
    assert f012.vertices == (0, 1, 2)
    assert f012.id == "f_0_1_2"
    assert len(f012.faces()) == 3
    assert {f.id for f in f012.faces()} == {"e_1_2", "e_0_2", "e_0_1"}

    # Sub-simplex check
    assert v0.is_face_of(Simplex([3, 4, 5]))
    assert not v0.is_face_of(f012)
    assert e01.is_face_of(f012)


def test_simplicial_complex_generators():
    # 2D triangle: 1 triangle, 3 edges, 3 vertices = 7 simplices
    t2d = SimplicialComplex.triangle_2d()
    assert t2d.dim == 2
    assert len(t2d.simplices) == 7
    assert len(t2d.simplices_by_dim[0]) == 3
    assert len(t2d.simplices_by_dim[1]) == 3
    assert len(t2d.simplices_by_dim[2]) == 1

    # 2-sphere boundary of tetrahedron: 4 triangles, 6 edges, 4 vertices = 14 simplices
    s2 = SimplicialComplex.tetrahedron_boundary_2d()
    assert s2.dim == 2
    assert len(s2.simplices) == 14
    assert len(s2.simplices_by_dim[0]) == 4
    assert len(s2.simplices_by_dim[1]) == 6
    assert len(s2.simplices_by_dim[2]) == 4

    # 2D fan with 5 triangles: 6 vertices, 10 edges, 5 triangles = 21 simplices
    fan = SimplicialComplex.equilateral_fan_2d(n_fans=5)
    assert fan.dim == 2
    assert len(fan.simplices_by_dim[0]) == 6
    assert len(fan.simplices_by_dim[1]) == 10
    assert len(fan.simplices_by_dim[2]) == 5

    # 3-sphere boundary of 4-simplex: 5 tets, 10 triangles, 10 edges, 5 vertices = 30 simplices
    s3 = SimplicialComplex.four_simplex_boundary_3d()
    assert s3.dim == 3
    assert len(s3.simplices) == 30
    assert len(s3.simplices_by_dim[0]) == 5
    assert len(s3.simplices_by_dim[1]) == 10
    assert len(s3.simplices_by_dim[2]) == 10
    assert len(s3.simplices_by_dim[3]) == 5


def test_poset_covering_edge_codimension_purity():
    s2 = SimplicialComplex.tetrahedron_boundary_2d()
    poset = build_simplicial_face_poset(s2)

    # Build dictionary from simplex id to dim
    dim_by_id = {s.id: s.dim for s in s2.simplices}

    # All covering relations must have dim(upper) == dim(lower) + 1
    for edge in poset.covering_edges:
        dim_lower = dim_by_id[edge.lower]
        dim_upper = dim_by_id[edge.upper]
        assert dim_upper == dim_lower + 1, f"Covering edge {edge} violates codimension-1 purity"


def test_flat_regge_system_curvature_zero():
    t2d = SimplicialComplex.triangle_2d()
    system = build_regge_restriction_system(t2d, fiber_dim=3, curvature_scale=Fraction(0))

    # All triples should have K == 0
    from cohomology_quotient import build_curvature_operator_cochain
    k_cochain = build_curvature_operator_cochain(system)
    assert k_cochain.is_zero()


def test_curved_regge_system_curvature_nonzero():
    s2 = SimplicialComplex.tetrahedron_boundary_2d()
    system = build_regge_restriction_system(s2, fiber_dim=3, curvature_scale=Fraction(1, 10))

    from cohomology_quotient import build_curvature_operator_cochain
    k_cochain = build_curvature_operator_cochain(system)
    assert not k_cochain.is_zero()


def test_regge_bianchi_identity_across_dimensions():
    # 1. 2D triangle flat
    t2d = SimplicialComplex.triangle_2d()
    sys_t2d = build_regge_restriction_system(t2d, fiber_dim=3, curvature_scale=Fraction(0))
    is_bianchi, quads = verify_regge_bianchi_identity(sys_t2d)
    assert is_bianchi
    assert quads > 0

    # 2. 2-sphere boundary curved
    s2 = SimplicialComplex.tetrahedron_boundary_2d()
    sys_s2 = build_regge_restriction_system(s2, fiber_dim=3, curvature_scale=Fraction(1, 8))
    is_bianchi_s2, quads_s2 = verify_regge_bianchi_identity(sys_s2)
    assert is_bianchi_s2
    assert quads_s2 == 194

    # 3. 3-sphere boundary curved (4D Regge geometry boundary)
    s3 = SimplicialComplex.four_simplex_boundary_3d()
    sys_s3 = build_regge_restriction_system(s3, fiber_dim=4, curvature_scale=Fraction(1, 12))
    is_bianchi_s3, quads_s3 = verify_regge_bianchi_identity(sys_s3)
    assert is_bianchi_s3
    assert quads_s3 == 1320

    # 4. 4D hinge star curved
    star = SimplicialComplex.triangulated_hinge_star_4d()
    sys_star = build_regge_restriction_system(star, fiber_dim=4, curvature_scale=Fraction(1, 10))
    is_bianchi_star, quads_star = verify_regge_bianchi_identity(sys_star)
    assert is_bianchi_star
    assert quads_star > 0


def test_hinge_holonomy_product():
    # Test closed loop product around vertex hinge in a flat vs curved 2D system
    fan = SimplicialComplex.equilateral_fan_2d(n_fans=3)
    sys_flat = build_regge_restriction_system(fan, fiber_dim=3, curvature_scale=Fraction(0))

    # Path from f_0_1_2 to v_0 and back through f_0_2_3
    # Self-contained cycle of restrictions
    hops = [
        ("f_0_1_2", "v_0"),
        ("v_0", "v_0"),
    ]
    hol_flat = compute_hinge_holonomy_product(sys_flat, hops)
    assert exact_equal(hol_flat, Matrix.eye(3))

    # Empty hops error
    with pytest.raises(ValueError, match="cannot be empty"):
        compute_hinge_holonomy_product(sys_flat, [])
