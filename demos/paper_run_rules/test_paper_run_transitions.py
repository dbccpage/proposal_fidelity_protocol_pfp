"""PaperRunGraph planning and fail-closed, role-gated transitions.

Ported from an internal test suite. The command-line planner test was not ported.
AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from paperrun.paper_run_graph import (
    PaperRunGraph,
    PaperRunGraphError,
    TransitionEvent,
    validate_transition,
    validate_transition_or_raise,
)
from paperrun.paper_plan import freeze_carrier, plan_paper


@pytest.fixture()
def mini_paper(tmp_path: Path) -> Path:
    root = tmp_path / "pkg"
    root.mkdir()
    (root / "docs").mkdir()
    (root / "README.md").write_text("# mini\n", encoding="utf-8")
    (root / "docs" / "claim_ir.yaml").write_text(
        """
schema_version: claim_ir/v1
claims:
  - claim_id: A1
    mechanization_class: SCOPE_FENCE
    lean_na_reason: fence
  - claim_id: D2
    mechanization_class: LEAN_THEOREM
  - claim_id: E4
    mechanization_class: PYTHON_NUMERICAL_REPLAY
    lean_na_reason: prose only
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (root / "paper.md").write_text("# Paper\n\nBody.\n", encoding="utf-8")
    return root


def test_freeze_and_plan_read_only(mini_paper: Path):
    g = freeze_carrier(mini_paper)
    assert g.authority_effect == "None"
    assert len(g.carrier_hash) == 64
    assert {c.claim_id for c in g.claims} >= {"A1", "D2", "E4"}
    # D2 LEAN_THEOREM -> lean_kernel obligation active
    d2_lean = [o for o in g.obligations if o.claim_id == "D2" and o.kind == "lean_kernel"]
    assert d2_lean and d2_lean[0].disposition == "unchecked"
    # E4 is computational only: no universal Lean obligation forced
    e4_lean = [o for o in g.obligations if o.claim_id == "E4" and "lean" in o.kind]
    assert e4_lean == []

    plan = plan_paper(mini_paper)
    assert plan.read_only is True
    assert plan.authority_effect == "None"
    assert "stage_0_redteam" in plan.required_stage_ids
    assert "stage_final_red_team" in plan.required_stage_ids
    d = plan.to_dict()
    assert "finite typed" in d["precise_claim"].lower()
    assert d["graph"]["claim_count"] >= 3

    # YAML roundtrip
    yaml_text = g.to_yaml()
    assert "carrier_hash" in yaml_text
    reloaded = PaperRunGraph.from_yaml(yaml_text)
    assert reloaded.carrier_hash == g.carrier_hash
    assert len(reloaded.claims) == len(g.claims)


def test_carrier_hash_changes_when_a_file_changes(mini_paper: Path):
    before = freeze_carrier(mini_paper).carrier_hash
    assert freeze_carrier(mini_paper).carrier_hash == before
    (mini_paper / "paper.md").write_text("# Paper\n\nEdited body.\n", encoding="utf-8")
    assert freeze_carrier(mini_paper).carrier_hash != before


def test_refuse_proposer_pass():
    ev = TransitionEvent(
        role="proposer",
        event_type="candidate_patch",
        carrier_hash="abc",
        claims_pass=True,
    )
    res = validate_transition(ev)
    assert res.is_err
    assert "proposer cannot emit" in res.unwrap_err().message

    with pytest.raises(PaperRunGraphError, match="proposer cannot emit"):
        validate_transition_or_raise(ev)


def test_refuse_evaluator_patch():
    ev = TransitionEvent(
        role="evaluator",
        event_type="candidate_patch",
        carrier_hash="abc",
    )
    res = validate_transition(ev)
    assert res.is_err
    assert "evaluator cannot mutate" in res.unwrap_err().message

    with pytest.raises(PaperRunGraphError, match="evaluator cannot mutate"):
        validate_transition_or_raise(ev)


def test_refuse_post_build_mutate():
    ev = TransitionEvent(
        role="proposer",
        event_type="candidate_patch",
        carrier_hash="abc",
        post_build=True,
        source_mutated_after_build=True,
    )
    res = validate_transition(ev)
    assert res.is_err
    assert "post-build" in res.unwrap_err().message

    with pytest.raises(PaperRunGraphError, match="post-build"):
        validate_transition_or_raise(ev)


def test_refuse_global_green():
    ev = TransitionEvent(
        role="evaluator",
        event_type="global_green",
        carrier_hash="abc",
    )
    res = validate_transition(ev)
    assert res.is_err
    assert "forbidden" in res.unwrap_err().message

    with pytest.raises(PaperRunGraphError, match="forbidden"):
        validate_transition_or_raise(ev)


def test_refuse_non_authorizer_accept():
    ev = TransitionEvent(
        role="evaluator",
        event_type="human_accept",
        carrier_hash="abc",
    )
    res = validate_transition(ev)
    assert res.is_err
    assert "only authorizer" in res.unwrap_err().message

    with pytest.raises(PaperRunGraphError, match="only authorizer"):
        validate_transition_or_raise(ev)


def test_legal_evaluator_finding():
    ev = TransitionEvent(
        role="evaluator",
        event_type="finding",
        carrier_hash="deadbeef",
    )
    res = validate_transition(ev)
    assert res.is_ok
    validate_transition_or_raise(ev)


def test_legal_authorizer_accept():
    ev = TransitionEvent(
        role="authorizer",
        event_type="human_accept",
        carrier_hash="deadbeef",
    )
    res = validate_transition(ev)
    assert res.is_ok
    validate_transition_or_raise(ev)


def test_dev_only_skips_stage_5_and_final(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "claim_ir.yaml").write_text(
        "claims:\n  - claim_id: C1\n    mechanization_class: PROSE\n", encoding="utf-8"
    )
    plan = plan_paper(tmp_path, dev_only=True)
    assert "stage_5_build_public_object" not in plan.required_stage_ids
    assert "stage_final_red_team" not in plan.required_stage_ids
    assert "stage_5_build_public_object" in plan.skipped_stage_ids
    assert "stage_final_red_team" in plan.skipped_stage_ids
    assert any("dev-only" in n for n in plan.uncovered_notes)
