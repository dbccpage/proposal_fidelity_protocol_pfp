"""N13: an inheritance edge requires a seal that names that parent and child.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from pciv.domain.causal_witness import (
    PLACEHOLDER_WITNESS,
    seal_causal_witness,
)
from operating_system.adapters.prompt_civ.genealogy import (
    LineageGraphV1 as AdapterGraph,
)
from operating_system.adapters.prompt_civ.genealogy import (
    RelationshipType as AdapterRelationship,
)
from pciv.use_cases.genealogy import (
    LineageGraphV1 as UseCaseGraph,
)
from pciv.use_cases.genealogy import (
    RelationshipType as UseCaseRelationship,
)


GRAPH_CASES = (
    pytest.param(UseCaseGraph, UseCaseRelationship, id="use_case"),
    pytest.param(AdapterGraph, AdapterRelationship, id="adapter"),
)


@pytest.mark.parametrize(("graph_cls", "relationship"), GRAPH_CASES)
def test_unbound_seal_is_not_an_edge_for_arbitrary_endpoints(graph_cls, relationship) -> None:
    graph = graph_cls()
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        graph.add_edge(
            "A",
            "B",
            relationship.DIRECT_MUTATION,
            witness_receipt=seal_causal_witness({"n": 1}),
        )
    assert graph.has_inheritance_edge("A", "B") is False


@pytest.mark.parametrize(("graph_cls", "relationship"), GRAPH_CASES)
def test_placeholder_dict_stays_refused(graph_cls, relationship) -> None:
    graph = graph_cls()
    placeholder = {
        "receipt_sha256": PLACEHOLDER_WITNESS,
        "authority_effect": "None",
    }
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        graph.add_edge(
            "A",
            "B",
            relationship.DIRECT_MUTATION,
            witness_receipt=placeholder,
        )
    assert graph.has_inheritance_edge("A", "B") is False


@pytest.mark.parametrize(("graph_cls", "relationship"), GRAPH_CASES)
def test_seal_must_name_this_parent_and_child(graph_cls, relationship) -> None:
    graph = graph_cls()
    named = seal_causal_witness({"parent_id": "A", "child_id": "B", "n": 1})
    graph.add_edge(
        "A",
        "B",
        relationship.DIRECT_MUTATION,
        witness_receipt=named,
    )
    assert graph.has_inheritance_edge("A", "B") is True
    with pytest.raises(ValueError, match="CAUSAL_WITNESS_REQUIRED"):
        graph.add_edge(
            "C",
            "D",
            relationship.DIRECT_MUTATION,
            witness_receipt=named,
        )
    assert graph.has_inheritance_edge("C", "D") is False
