"""Finite original-board controls, using the native and independent judges."""
import json
from copy import deepcopy

import pytest

from omega_engine_woland.tests.pilots.challenge_suite.mechanism_panels import (
    ROUND5,
    VERSION,
    build_compaction_panels,
    build_panels,
    generate_board,
)
from omega_engine_pfp.infrastructure.mechanism_sessions import (
    _structure,
    prepare_session_turn,
    replay_session,
    start_session,
    submit_session_turn,
)

SHA = "e1cf2e0fd816ad060c534f3aad8facc16e7c6d5d8cf5c7bd9bffa2ffd33635fb"


def test_versioned_public_hidden_relabel_panels_are_seeded_and_original_round5_is_exact():
    panel = build_panels(version=VERSION)
    assert panel == build_panels(version=VERSION)
    assert [len(panel[key]) for key in ("public", "hidden", "relabel", "poison")] == [12, 60, 20, 12]
    assert [sum(row["metadata"]["cycle_rank"] == rank for row in panel["public"]) for rank in range(3, 8)] == [2, 2, 2, 2, 4]
    assert [sum(row["metadata"]["cycle_rank"] == rank for row in panel["hidden"]) for rank in range(3, 9)] == [10] * 6
    assert panel["hidden"][0]["board"] == ROUND5
    assert panel["observation"] == "TASK_DATA_NOT_MODEL_TRIALS"
    with pytest.raises(ValueError, match="EXPLICIT_PANEL_VERSION"):
        build_panels(version="original")


def test_all_generated_families_have_real_shared_tree_edges_and_nontrivial_cycles():
    panel = build_panels(version=VERSION)
    assert {row["metadata"]["graph_family"] for row in panel["public"]} == {
        "K4", "K3,3", "cube-Q3", "K5", "Petersen", "wheel-7-rim"}
    for row in panel["public"] + panel["hidden"][1:] + panel["relabel"]:
        board = row["board"]
        facts = _structure(board, board["claims"])
        counts = [sum(any([u, v] == edge for u, v, _ in cycle) for cycle in facts["cycles"])
                  for edge in facts["tree_edges"]]
        assert max(counts) >= 3
        if row["metadata"]["control"] is None:
            assert all(facts["cycle_residuals"].values())
        if row["metadata"]["control"] == "correct_zero_chord":
            assert any(board["claims"][f"{u}->{v}"] == 0 for u, v in facts["chords"])
        p = {key: int(value) for key, value in row["reference_potential"].items()}
        assert all(p[v] - p[u] == board["claims"][f"{u}->{v}"] for u, v in facts["tree_edges"])


@pytest.mark.parametrize("rank", range(3, 9))
def test_original_nontrivial_boards_require_separate_cut_verify_and_replay(rank):
    row = generate_board(rank, seed=31000 + rank, variant=1)
    board, potential = row["board"], row["reference_potential"]
    state = start_session(board, run_id=f"v2-r{rank}", protocol_sha256=SHA)
    assert state["schema_version"] == "c006.session.v2"
    assert int(state["measurement"]["phi1"]) > 0
    context = prepare_session_turn(state).task.case["context"]
    assert "reference_potential" not in json.dumps(context)
    claims = {f"{u}->{v}": str(int(potential[v]) - int(potential[u])) for u, v in board["edges"]}
    for answer in (dict(move="CUT", claims=claims), dict(move="VERIFY", potential=potential)):
        turn = prepare_session_turn(state)
        raw = json.dumps({key: turn.binding[key] for key in ("task_id", "attempt_id", "input_sha256")} | {"answer": answer}).encode()
        state = submit_session_turn(state, raw)
    assert state["terminal"] == "ACCEPTED_ZERO_DEFECT"
    assert replay_session(json.loads(json.dumps(state)))["provider_calls"] == 0


@pytest.mark.parametrize("fault", ["missing", "duplicate", "unknown", "disconnected"])
def test_invalid_explicit_tree_refuses_before_native(fault):
    class NeverNative:
        def solve(self, _case):
            raise AssertionError("must not call native")
    board = generate_board(3, seed=78)["board"]
    if fault == "missing":
        board["spanning_tree"].pop()
    elif fault == "duplicate":
        board["spanning_tree"][1] = board["spanning_tree"][0]
    elif fault == "unknown":
        board["spanning_tree"][0] = ["a", "unknown"]
    else:
        board["spanning_tree"] = [["a", "b"], ["a", "c"], ["b", "c"]]
    with pytest.raises(ValueError):
        start_session(board, run_id="bad-tree", protocol_sha256=SHA, native=NeverNative())


def test_original_default_board_keeps_v1_bfs_behavior():
    assert start_session(deepcopy(ROUND5), run_id="historical", protocol_sha256=SHA)["schema_version"] == "c006.session.v1"


def test_original_compaction_panel_sizes_union_witnesses_and_late_constraint_controls():
    from omega_engine_pfp.infrastructure.context_compaction_sessions import _schedule
    panel = build_compaction_panels(version="c007.panels.v1")
    assert [len(panel[key]) for key in ("hidden", "relabel", "poison")] == [40, 12, 16]
    assert panel == build_compaction_panels(version="c007.panels.v1")
    for row in panel["hidden"] + panel["relabel"] + panel["poison"]:
        assert _schedule(row["schedule"]) == row["schedule"]
        witness = {node: int(value) for node, value in row["reference_potential"].items()}
        for event in row["schedule"]:
            for record in event.get("constraints", []):
                if not record["repairable"]:
                    assert witness[record["v"]] - witness[record["u"]] == record["claim"]
    assert all(row["metadata"]["control"] == "typo" for row in panel["poison"][:10])
    assert all(row["schedule"][30]["constraints"][-1]["u"] == "n0" for row in panel["poison"][10:])


@pytest.mark.parametrize("index", [0, 6])
def test_poisoned_stale_cut_and_zero_chord_edit_are_remeasured_not_trusted(index):
    row = build_panels(version=VERSION)["poison"][index]
    state = start_session(row["board"], run_id=f"poison-{index}", protocol_sha256=SHA)
    for candidate in (row["current_claims"], row["proposed_claims"]):
        turn = prepare_session_turn(state)
        raw = json.dumps({key: turn.binding[key] for key in ("task_id", "attempt_id", "input_sha256")} |
            {"answer": dict(move="CUT", claims={key: str(value) for key, value in candidate.items()})}).encode()
        state = submit_session_turn(state, raw)
    assert state["transcript"][-1]["outcome"]["reason"] == "NO_STRICT_DESCENT"
    assert state["claims"] == row["current_claims"] and state["measurement"]["phi1"] == "0"
