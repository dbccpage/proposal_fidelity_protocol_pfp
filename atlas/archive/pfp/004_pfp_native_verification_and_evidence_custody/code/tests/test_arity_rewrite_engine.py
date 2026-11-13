"""
Tests for Arity Rewrite Engine and S(n) Tower Distinction Stages.
Reference: Paper 032 (PO-032).
"""


from arity_rewrite_engine import (
    RewriteSystem,
    Rule,
    StageKind,
    Step,
    create_stage_object,
)


def test_stage_hierarchy_and_diagonal_excision():
    """Verifies stages 0 to 5 and refusal of self-loop ARA (diagonal excision)."""
    # Stage 0: Void
    s0 = create_stage_object(StageKind.STAGE_0_VOID, ())
    assert s0.stage == StageKind.STAGE_0_VOID
    assert s0.is_admissible_primitive is True

    # Stage 1: Point
    s1 = create_stage_object(StageKind.STAGE_1_POINT, ("a",))
    assert s1.stage == StageKind.STAGE_1_POINT
    assert s1.automorphism_group == "1"

    # Stage 2: Pair
    s2 = create_stage_object(StageKind.STAGE_2_PAIR, ("a", "b"))
    assert s2.stage == StageKind.STAGE_2_PAIR
    assert s2.automorphism_group == "S_2"

    # Stage 3: Cut D2
    s3 = create_stage_object(StageKind.STAGE_3_CUT_D2, ("a", "b"))
    assert s3.stage == StageKind.STAGE_3_CUT_D2
    assert s3.edges == (("a", "b"),)

    # Stage 4: Refused Loop ARA (self-loop)
    s4 = create_stage_object(StageKind.STAGE_4_LOOP_ARA, ("a",))
    assert s4.stage == StageKind.STAGE_4_LOOP_ARA
    assert s4.is_admissible_primitive is False
    assert s4.refusal_reason is not None
    assert "refused" in s4.refusal_reason.lower() or "violates" in s4.refusal_reason.lower()

    # Stage 5: Symmetric Link S2
    s5 = create_stage_object(StageKind.STAGE_5_LINK_S2, ("a", "b"))
    assert s5.stage == StageKind.STAGE_5_LINK_S2
    assert len(s5.edges) == 2


def test_redex_keyed_rewriting():
    """Derivation steps are keyed by (position, rule) rather than name alone."""
    r1 = Rule(name="r1", lhs="ba", rhs="ab", weight=1)
    srs = RewriteSystem(rules=[r1])

    text = "bba"
    # Redex at position 1: 'ba' -> 'ab' produces 'bab'
    res, err = srs.apply_step(text, Step(rule_name="r1", pos=1))
    assert err is None
    assert res == "bab"

    # Mismatched position returns error
    res_bad, err_bad = srs.apply_step(text, Step(rule_name="r1", pos=0))
    assert res_bad is None
    assert err_bad is not None
