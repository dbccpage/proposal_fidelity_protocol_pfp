"""Unit tests for finite poset and covering relations (PO-001).

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from covering_edge_poset import ComparablePair, CoverEdge, FinitePoset


def test_poset_diamond_construction():
    # Elementary diamond: 0 < 1 < 3 and 0 < 2 < 3
    poset = FinitePoset(
        elements=["0", "1", "2", "3"],
        relations=[("0", "1"), ("1", "3"), ("0", "2"), ("2", "3")],
    )

    assert poset.is_le("0", "3")
    assert poset.is_lt("0", "3")
    assert poset.is_covering("0", "1")
    assert poset.is_covering("1", "3")
    assert poset.is_covering("0", "2")
    assert poset.is_covering("2", "3")
    assert not poset.is_covering("0", "3")  # 0 < 3 is not a covering edge because of 1 and 2

    assert poset.is_diamond("0", "1", "2", "3")
    assert poset.is_diamond("0", "2", "1", "3")

    chains = poset.saturated_chains("0", "3")
    assert len(chains) == 2
    assert ("0", "1", "3") in chains
    assert ("0", "2", "3") in chains


def test_poset_cycle_rejection():
    # Relation with cycle violates antisymmetry
    with pytest.raises(ValueError, match="not antisymmetric"):
        FinitePoset(
            elements=["A", "B"],
            relations=[("A", "B"), ("B", "A")],
        )


def test_value_object_exact_type_equality():
    edge = CoverEdge(lower="0", upper="1")
    pair = ComparablePair(lower="0", upper="1")

    assert edge != pair
    assert type(edge) is not type(pair)
    assert not (edge == pair)
