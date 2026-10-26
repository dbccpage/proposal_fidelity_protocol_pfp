"""Differential test: the port must agree with the unmodified Paper 005 governor.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:differential:v1

The oracle is ``papers/005_pfp_practitioners_field_manual/code/l1_symbol_game_governor.py``,
loaded by path and never edited. Random graphs and move sequences run on both;
after every move the verdict (step id, admitted, status, defect before and
after) and the resulting section and claims must match exactly.
"""

from __future__ import annotations

from fractions import Fraction
from types import ModuleType
from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from pfp_lab.core.governor import AssertMove, CutMove, Governor, Move, RetractMove, VerifyMove
from pfp_lab.core.graph import ConstraintGraph
from pfp_lab.tests.strategies import graphs, small_rationals


@st.composite
def moves_for(draw: st.DrawFn, graph: ConstraintGraph) -> list[Move]:
    names = [*graph.vertices, "zz"]
    keys = [item.key for item in graph.edges]
    pairs = st.tuples(st.sampled_from(names), st.sampled_from(names))
    edge_or_pair = st.sampled_from(keys) | pairs if keys else pairs
    obligations = st.sampled_from(["ZERO_DEFECT", "ZERO_OBSTRUCTION", "EDGE_MATCH:a,b", "EDGE_MATCH:b,c", "X"])
    choices = st.one_of(
        st.builds(
            lambda k, v, m: AssertMove(k[0], k[1], v, enforce_monotonicity=m),
            edge_or_pair,
            small_rationals,
            st.booleans(),
        ),
        st.builds(
            lambda s: CutMove(section=tuple(s.items())),
            st.dictionaries(st.sampled_from(names), small_rationals, max_size=4),
        ),
        st.builds(
            lambda c: CutMove(claims=tuple(c.items())),
            st.dictionaries(edge_or_pair, small_rationals, min_size=len(keys), max_size=len(keys) + 1),
        ),
        st.builds(VerifyMove, obligations),
        st.builds(lambda n: RetractMove(f"step_{n:03d}"), st.integers(1, 10)),
    )
    return draw(st.lists(choices, max_size=10))


def apply_oracle(oracle_governor: Any, move: Move) -> Any:
    if isinstance(move, AssertMove):
        return oracle_governor.step_assert(
            move.source, move.target, move.value, enforce_monotonicity=move.enforce_monotonicity
        )
    if isinstance(move, CutMove):
        return oracle_governor.step_cut(
            proposed_section=None if move.section is None else dict(move.section),
            proposed_claims=None if move.claims is None else dict(move.claims),
        )
    if isinstance(move, VerifyMove):
        return oracle_governor.step_verify(move.obligation)
    return oracle_governor.step_retract(move.target_step_id)


def oracle_graph(oracle: ModuleType, graph: ConstraintGraph) -> Any:
    edges = tuple(oracle.Edge(item.source, item.target, item.weight) for item in graph.edges)
    return oracle.ConstraintGraph(vertices=graph.vertices, edges=edges)


@settings(max_examples=300)
@given(st.data())
def test_port_matches_paper_005_oracle(oracle: ModuleType, data: st.DataObject) -> None:
    graph = data.draw(graphs(max_vertices=4, max_edges=6))
    ours = Governor(graph)
    theirs = oracle.L1SymbolGameGovernor(oracle_graph(oracle, graph))
    for move in data.draw(moves_for(graph)):
        mine = ours.apply(move)
        reference = apply_oracle(theirs, move)
        assert (mine.step_id, mine.admitted, mine.status.value) == (
            reference.step_id,
            reference.admitted,
            reference.status,
        ), move
        assert (mine.defect_before, mine.defect_after) == (reference.defect_before, reference.defect_after)
        assert ours.section == {k: Fraction(v) for k, v in theirs.section.items()}
        assert ours.claims == dict(theirs.edge_claims)


def test_oracle_worked_session_matches_pack(oracle: ModuleType) -> None:
    from pfp_lab.core.contracts import get_pack
    from pfp_lab.core.session import run_scenario

    session = run_scenario(get_pack("paper-005-worked-session"))
    graph = oracle.ConstraintGraph(
        vertices=("a", "b", "c"),
        edges=(oracle.Edge("a", "b", 1), oracle.Edge("b", "c", 2), oracle.Edge("c", "a", 3)),
    )
    reference = oracle.L1SymbolGameGovernor(graph)
    for source, target in (("a", "b"), ("b", "c"), ("c", "a")):
        reference.step_assert(source, target, Fraction(1))
    assert str(reference.primary_obstruction()) == session.verdicts[4].defect_before == "3"
