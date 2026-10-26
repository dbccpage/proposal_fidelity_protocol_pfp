"""Comprehensive unit tests for Workflows, Agents, Skills (WAS) & Operads (Levels 00–09).

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest
from was_operad_core import (
    AntiSkillRegistry,
    Colour,
    ColouredOperad,
    DDCContractivityEngine,
    DeliberationReceiptEmitter,
    DialecticWorkflow,
    FourHostParityManager,
    OperadOp,
    OperadTregSupervisor,
    PlanarTree,
    SkillPackage,
    SwarmWing,
)


def test_level_00_coloured_operad_architecture():
    operad = ColouredOperad()
    op_code_gen = OperadOp(id=1, name="code_gen", inputs=(Colour.CODE,), output=Colour.CODE)
    op_test = OperadOp(id=2, name="run_test", inputs=(Colour.CODE,), output=Colour.TEST_RECEIPT)

    # Compose op_test o_0 op_code_gen
    composed = operad.partial_compose(op_test, op_code_gen, slot_i=0)
    assert composed.inputs == (Colour.CODE,)
    assert composed.output == Colour.TEST_RECEIPT
    assert composed.arity == 1

    # Incompatible composition raises TypeError
    op_invalid = OperadOp(
        id=3, name="invalid", inputs=(Colour.DELIBERATION,), output=Colour.DELIBERATION
    )
    with pytest.raises(TypeError, match="Colour mismatch"):
        operad.partial_compose(op_test, op_invalid, slot_i=0)


def test_level_01_skill_packaging_discipline():
    # Compliant skill package
    valid_pkg = SkillPackage(
        name="governance-clean-arch",
        description="Clean architecture invariants",
        instruction_lines=180,
        size_bytes=12000,
        has_frontmatter=True,
        reference_dispatch_matrix=True,
    )
    ok, violations = valid_pkg.check_packaging_compliance()
    assert ok is True
    assert len(violations) == 0

    # Non-compliant skill package breaching budget ceilings
    bloated_pkg = SkillPackage(
        name="bloated-skill",
        description="Too large",
        instruction_lines=450,
        size_bytes=35000,
        has_frontmatter=False,
        reference_dispatch_matrix=False,
    )
    ok_b, violations_b = bloated_pkg.check_packaging_compliance()
    assert ok_b is False
    assert len(violations_b) == 4


def test_level_02_planar_trees_and_associativity():
    leaf1 = PlanarTree(colour=Colour.CODE)
    leaf2 = PlanarTree(colour=Colour.CODE)
    assert leaf1.is_leaf is True
    assert leaf1.height() == 0

    merge_op = OperadOp(id=10, name="merge", inputs=(Colour.CODE, Colour.CODE), output=Colour.CODE)
    tree = PlanarTree(op=merge_op, subtrees=(leaf1, leaf2))
    assert tree.is_leaf is False
    assert tree.height() == 1
    assert tree.root_output() == Colour.CODE
    assert tree.leaf_colours() == [Colour.CODE, Colour.CODE]


def test_level_03_capability_slices_and_swarm_wings():
    wing = SwarmWing(name="WolandWing", allowed_capabilities={"lint", "format", "parse"})

    assert wing.can_execute("lint") is True
    assert wing.can_execute("deploy_production") is False

    ok, msg = wing.execute_bounded("lint", "check module 090")
    assert ok is True

    ok_refused, msg_refused = wing.execute_bounded("deploy_production", "push to prod")
    assert ok_refused is False
    assert "refuses" in msg_refused


def test_level_04_epistemic_anti_skills():
    registry = AntiSkillRegistry()
    anti_id = registry.mint_anti_skill(
        defect_type="UNCHECKED_MUTATION",
        incident_receipt={"trigger": "silent_eval_pass", "date": "2026-10-05"},
    )
    assert anti_id == "anti_unchecked_mutation"

    # Blocks candidate containing the trigger
    assert registry.check_candidate(anti_id, "Candidate with silent_eval_pass pattern") is False
    # Allows benign candidate
    assert registry.check_candidate(anti_id, "Clean verified implementation") is True


def test_level_05_regulatory_treg_supervision():
    treg = OperadTregSupervisor(rate_limit_per_second=2.0)

    # First two calls pass
    assert treg.check_rate_compliance(current_time=1.0) is True
    assert treg.check_rate_compliance(current_time=1.1) is True
    # Third call within the same second is rate-limited
    assert treg.check_rate_compliance(current_time=1.2) is False
    # Next call after 1 second window passes
    assert treg.check_rate_compliance(current_time=2.5) is True


def test_level_06_residual_geometry_and_ddc():
    ddc = DDCContractivityEngine(contraction_factor=0.5)

    r0 = 1.0
    r1 = ddc.scale_descent_step(r0)
    r2 = ddc.scale_descent_step(r1)
    r3 = ddc.scale_descent_step(r2)

    seq = [r0, r1, r2, r3]
    assert ddc.verify_contractivity(seq) is True
    assert r3 == 0.125


def test_level_07_workflow_graphs_and_dialectic_pipelines():
    pipeline = DialecticWorkflow()

    def thesis(x: str) -> str:
        return f"Proposal({x})"

    def antithesis(x: str) -> str:
        return f"Challenge({x})"

    def synthesis(t: str, a: str) -> str:
        return f"Synthesized({t} resolved with {a})"

    res = pipeline.run_pipeline(thesis, antithesis, synthesis, "DraftSpec")
    assert "DraftSpec" in res["thesis"]
    assert "Challenge" in res["antithesis"]
    assert "Synthesized" in res["synthesis"]
    assert res["authority_effect"] == "None"


def test_level_08_four_host_mirror_parity():
    manager = FourHostParityManager()
    rel = "skills/demo-skill/SKILL.md"
    content = "---\nname: demo-skill\n---\n# Demo"

    manager.sync_file(rel, content)
    assert manager.verify_mirror_parity(rel) is True

    # Tamper with one seat breaks parity
    manager.store[".grok"][rel] = "drifted content"
    assert manager.verify_mirror_parity(rel) is False


def test_level_09_sovereign_non_authority_and_deliberation_receipts():
    emitter = DeliberationReceiptEmitter()
    receipt = emitter.emit_receipt(
        proposal_id=42,
        proposer="agent_proposer",
        reviewer="agent_reviewer",
        verifier="agent_verifier",
        accepted=True,
    )

    assert receipt["receipt_id"] == 1
    assert receipt["proposal_id"] == 42
    assert receipt["authority_effect"] == "None"
    assert "digest" in receipt
    assert len(receipt["digest"]) == 64
