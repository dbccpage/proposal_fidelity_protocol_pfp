"""Face boundaries must belong to the declared one-skeleton."""
from fractions import Fraction

import pytest

from pfp.domain.ddc import (
    Cochain0, Edge, Face, SimplicialComplex, audit_nilpotency_all_basis, d0, d1,
)


def test_complete_graph_faces_have_nilpotent_coboundary():
    carrier = SimplicialComplex.complete_graph(4, with_faces=True)
    assert carrier.num_faces == 4
    assert audit_nilpotency_all_basis(carrier).is_nilpotent


def test_reversed_boundary_edges_remain_admissible():
    carrier = SimplicialComplex(
        vertices=("a", "b", "c"),
        edges=(Edge("b", "a"), Edge("c", "b"), Edge("a", "c")),
        faces=(Face("a", "b", "c"),),
    )
    potential = Cochain0({"a": Fraction(1, 2), "b": Fraction(7, 3), "c": Fraction(-2)})
    assert d1(carrier, d0(carrier, potential)).get("a", "b", "c") == Fraction(0)
    assert audit_nilpotency_all_basis(carrier).is_nilpotent
    assert audit_nilpotency_all_basis(SimplicialComplex.cycle_graph(3, with_faces=True)).is_nilpotent


@pytest.mark.parametrize("missing", [0, 1, 2])
def test_face_with_any_missing_boundary_edge_is_refused(missing):
    edges = (Edge("a", "b"), Edge("b", "c"), Edge("a", "c"))
    with pytest.raises(ValueError, match="boundary edge .* absent in both orientations"):
        SimplicialComplex(
            vertices=("a", "b", "c"),
            edges=tuple(edge for index, edge in enumerate(edges) if index != missing),
            faces=(Face("a", "b", "c"),),
        )
