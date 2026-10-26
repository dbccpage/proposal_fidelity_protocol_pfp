"""Unit contract for finite-gauge request value objects."""

import pytest

from omega_engine_pfp.domain.finite_gauge import RunConfig


def test_custom_graph_rejects_undeclared_edge_endpoint() -> None:
    with pytest.raises(ValueError, match="declared endpoints"):
        RunConfig(
            fixture_id="custom_graph",
            vertices=("a",),
            edges=(("a", "b", 1),),
        )
