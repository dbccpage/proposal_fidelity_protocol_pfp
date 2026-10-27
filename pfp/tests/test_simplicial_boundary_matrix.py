"""Targeted tests for higher-dimensional simplicial boundary matrix verification (d_{k-1} ∘ d_k = 0).

Verifies sovereign delegation to core_homology via ExactHomologyPort and RustExactEngineAdapter.
Governing Invariant: Zero Python Math Re-invention.
AuthorityEffect: None.
"""

import pytest

from pfp.domain.solvers.kinds import (
    ConstOracle,
    Regime,
    RegimeOracle,
    SimplicialBoundaryLawSatisfied,
    kind_of,
    refutation,
    rename_req,
    req_json,
    satisfies,
)
from pfp.infrastructure.adapters.exact_rust_adapter import (
    ExactError,
    RustExactEngineAdapter,
)


@pytest.fixture(scope="module")
def adapter() -> RustExactEngineAdapter:
    return RustExactEngineAdapter()


def test_standard_2_simplex_triangle_boundary_composition(adapter: RustExactEngineAdapter):
    """Triangle (2-simplex) boundary law d_1 ∘ d_2 = 0."""
    simplices = [[0, 1, 2]]
    report = adapter.verify_simplicial_boundary_law(simplices)

    assert report["max_dimension"] == 2
    # Vertices: 3, Edges: 3, Faces: 1
    assert report["simplex_counts_by_dim"] == [3, 3, 1]
    assert report["euler_characteristic"] == 1
    assert report["boundary_law_verified"] is True

    # Check composition record for degree 2 (d_1 ∘ d_2)
    compositions = report["compositions"]
    assert len(compositions) == 1
    c2 = compositions[0]
    assert c2["degree"] == 2
    assert c2["rows"] == 3  # C_0 dimension
    assert c2["cols"] == 1  # C_2 dimension
    assert c2["is_zero"] is True


def test_standard_3_simplex_tetrahedron_boundary_composition(adapter: RustExactEngineAdapter):
    """Tetrahedron (3-simplex) boundary law d_{k-1} ∘ d_k = 0 for k=2,3."""
    simplices = [[0, 1, 2, 3]]
    report = adapter.verify_simplicial_boundary_law(simplices)

    assert report["max_dimension"] == 3
    # Vertices: 4, Edges: 6, Triangles: 4, Tetrahedra: 1
    assert report["simplex_counts_by_dim"] == [4, 6, 4, 1]
    assert report["euler_characteristic"] == 1
    assert report["boundary_law_verified"] is True

    compositions = report["compositions"]
    assert len(compositions) == 2

    # d_1 ∘ d_2: C_2 (4) -> C_0 (4)
    assert compositions[0]["degree"] == 2
    assert compositions[0]["rows"] == 4
    assert compositions[0]["cols"] == 4
    assert compositions[0]["is_zero"] is True

    # d_2 ∘ d_3: C_3 (1) -> C_1 (6)
    assert compositions[1]["degree"] == 3
    assert compositions[1]["rows"] == 6
    assert compositions[1]["cols"] == 1
    assert compositions[1]["is_zero"] is True


def test_standard_4_simplex_5cell_boundary_composition(adapter: RustExactEngineAdapter):
    """4-simplex (5-cell on 5 vertices) boundary law across degrees 2, 3, 4."""
    simplices = [[0, 1, 2, 3, 4]]
    report = adapter.verify_simplicial_boundary_law(simplices)

    assert report["max_dimension"] == 4
    # c_0=5, c_1=10, c_2=10, c_3=5, c_4=1
    assert report["simplex_counts_by_dim"] == [5, 10, 10, 5, 1]
    assert report["euler_characteristic"] == 1
    assert report["boundary_law_verified"] is True

    compositions = report["compositions"]
    assert len(compositions) == 3

    # d_1 ∘ d_2: rows=5, cols=10
    assert compositions[0]["degree"] == 2
    assert compositions[0]["rows"] == 5
    assert compositions[0]["cols"] == 10
    assert compositions[0]["is_zero"] is True

    # d_2 ∘ d_3: rows=10, cols=5
    assert compositions[1]["degree"] == 3
    assert compositions[1]["rows"] == 10
    assert compositions[1]["cols"] == 5
    assert compositions[1]["is_zero"] is True

    # d_3 ∘ d_4: rows=10, cols=1
    assert compositions[2]["degree"] == 4
    assert compositions[2]["rows"] == 10
    assert compositions[2]["cols"] == 1
    assert compositions[2]["is_zero"] is True


def test_standard_5_simplex_higher_dimension(adapter: RustExactEngineAdapter):
    """5-simplex on 6 vertices: boundary law verified for degrees 2, 3, 4, 5."""
    simplices = [[0, 1, 2, 3, 4, 5]]
    report = adapter.verify_simplicial_boundary_law(simplices)

    assert report["max_dimension"] == 5
    # c_0=6, c_1=15, c_2=20, c_3=15, c_4=6, c_5=1
    assert report["simplex_counts_by_dim"] == [6, 15, 20, 15, 6, 1]
    assert report["euler_characteristic"] == 1
    assert report["boundary_law_verified"] is True
    assert len(report["compositions"]) == 4

    for rec in report["compositions"]:
        assert rec["is_zero"] is True

    # verify_boundary_law protocol method
    assert adapter.verify_boundary_law(simplices) is True


def test_octahedron_sphere_boundary_verification(adapter: RustExactEngineAdapter):
    """Octahedron boundary: 8 triangles forming a topological 2-sphere S^2."""
    simplices = [
        [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1],
        [5, 1, 2], [5, 2, 3], [5, 3, 4], [5, 4, 1],
    ]
    report = adapter.verify_simplicial_boundary_law(simplices)

    assert report["max_dimension"] == 2
    # 6 vertices, 12 edges, 8 triangles
    assert report["simplex_counts_by_dim"] == [6, 12, 8]
    # Euler characteristic of S^2 is V - E + F = 6 - 12 + 8 = 2
    assert report["euler_characteristic"] == 2
    assert report["boundary_law_verified"] is True
    assert report["compositions"][0]["is_zero"] is True


def test_empty_complex_boundary_law(adapter: RustExactEngineAdapter):
    """Empty complex vacously satisfies boundary law."""
    report = adapter.verify_simplicial_boundary_law([])
    assert report["boundary_law_verified"] is True
    assert report["compositions"] == []


def test_rejects_duplicate_vertices_in_simplex(adapter: RustExactEngineAdapter):
    """Rust host rejects degenerate simplex with duplicate vertices."""
    with pytest.raises(ExactError) as exc_info:
        adapter.verify_simplicial_boundary_law([[0, 1, 1]])
    assert "NATIVE_HOMOLOGY_REFUSAL" in str(exc_info.value) or "invalid simplex" in str(exc_info.value)


def test_simplicial_boundary_law_satisfied_requirement():
    """Verify SimplicialBoundaryLawSatisfied behaves as a first-class requirement kind."""
    from pfp import initialize_exact_ports

    initialize_exact_ports()
    tetrahedron = ((0, 1, 2, 3),)
    req = SimplicialBoundaryLawSatisfied("req_tetra", tetrahedron)

    assert kind_of(req) == "simplicial_boundary_law_satisfied"
    json_rep = req_json(req)
    assert json_rep["id"] == "req_tetra"
    assert json_rep["kind"] == "simplicial_boundary_law_satisfied"
    assert json_rep["simplices"] == [[0, 1, 2, 3]]

    # Value Object Exact-Type Equality Invariant
    req_same = SimplicialBoundaryLawSatisfied("req_tetra", tetrahedron)
    assert req == req_same
    assert req != ("req_tetra", tetrahedron)

    # Oracle satisfaction
    regime = Regime((), (), frozenset(), frozenset(), frozenset())
    oracle = RegimeOracle(regime)
    assert satisfies(oracle, req) is True
    assert refutation(oracle, req) == ()

    # ConstOracle
    const_o = ConstOracle(regime, True)
    assert satisfies(const_o, req) is True

    # Rename req
    pi = (3, 2, 1, 0)
    renamed = rename_req(req, pi, (0,))
    assert isinstance(renamed, SimplicialBoundaryLawSatisfied)
    assert renamed.rid == "req_tetra"
    assert renamed.simplices == ((0, 1, 2, 3),)
