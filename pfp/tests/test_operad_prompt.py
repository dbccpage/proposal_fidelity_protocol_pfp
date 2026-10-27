r"""Tests for Categorical Coloured Operad Prompt in pfp.

Covers Milestone 3 requirements:
- Colours C
- Immutable leaf text spans with source offsets [i, j]
- Operators O^+ with input/output colours
- Slot grafting (\circ_i) fail-closed validation of boundary colour matching and arity
- Congruence Ideal fences (I -> NullTree)
- Annihilator decoy refutation witness checks (O^-)

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from pfp.domain.operad import (
    AnnihilatorDecoy,
    ColouredOperadPrompt,
    CongruenceIdeal,
    LeafTextSpan,
    NullTree,
    OperadTreeNode,
    PromptColour,
    PromptOperator,
)


def test_prompt_colour_enumeration():
    assert PromptColour.RawTextSpan.value == "RawTextSpan"
    assert PromptColour.Equation.value == "Equation"
    assert PromptColour.IsolatedVariable.value == "IsolatedVariable"
    assert PromptColour.SubstitutionStep.value == "SubstitutionStep"
    assert PromptColour.RationalValue.value == "RationalValue"
    assert PromptColour.InvariantWitness.value == "InvariantWitness"
    assert PromptColour.TargetResult.value == "TargetResult"


def test_immutable_text_span_boundary_checks():
    source_doc = "x + 2*y = 5\n2*x - y = 0\nx + y"

    # 1. Valid span: "x + 2*y = 5" at offsets [0, 11]
    span = LeafTextSpan(
        id="span_1",
        colour=PromptColour.RawTextSpan,
        content="x + 2*y = 5",
        source_offsets=(0, 11),
    )
    span.verify_against_document(source_doc)

    # 2. Inverted bounds: start > end raises ValueError
    with pytest.raises(ValueError, match="Start offset 10 exceeds end offset 5"):
        LeafTextSpan(
            id="span_inv",
            colour=PromptColour.RawTextSpan,
            content="bad",
            source_offsets=(10, 5),
        )

    # 3. Out of bounds offset
    oob_span = LeafTextSpan(
        id="span_oob",
        colour=PromptColour.RawTextSpan,
        content="target",
        source_offsets=(0, 1000),
    )
    with pytest.raises(ValueError, match="exceeds document length"):
        oob_span.verify_against_document(source_doc)

    # 4. Content mutation at specified offsets
    mut_span = LeafTextSpan(
        id="span_mut",
        colour=PromptColour.RawTextSpan,
        content="x + 2*y = 6",
        source_offsets=(0, 11),
    )
    with pytest.raises(ValueError, match="Span content mismatch"):
        mut_span.verify_against_document(source_doc)


def test_operator_arity_enforcement():
    # Mismatched arity on declaration
    with pytest.raises(ValueError, match="arity mismatch"):
        PromptOperator(
            id="op_bad",
            source_colours=(PromptColour.Equation,),
            target_colour=PromptColour.IsolatedVariable,
            arity=2,
        )

    # Valid operator
    op_valid = PromptOperator(
        id="op_good",
        source_colours=(PromptColour.Equation,),
        target_colour=PromptColour.IsolatedVariable,
        arity=1,
    )
    assert op_valid.arity == 1


def test_slot_grafting_colour_mismatch_rejection():
    isolate_op = PromptOperator(
        id="isolate_var",
        source_colours=(PromptColour.Equation,),
        target_colour=PromptColour.IsolatedVariable,
        arity=1,
    )
    tree = OperadTreeNode(operator=isolate_op, children=())

    # RawTextSpan is not an Equation -> graft must raise TypeError
    raw_span = LeafTextSpan(
        id="raw_1",
        colour=PromptColour.RawTextSpan,
        content="x + 2*y = 5",
        source_offsets=(0, 11),
    )
    with pytest.raises(TypeError, match="Boundary colour mismatch at slot 0"):
        tree.graft(0, raw_span)


def test_slot_grafting_out_of_bounds_rejection():
    isolate_op = PromptOperator(
        id="isolate_var",
        source_colours=(PromptColour.Equation,),
        target_colour=PromptColour.IsolatedVariable,
        arity=1,
    )
    tree = OperadTreeNode(operator=isolate_op, children=())
    eq_span = LeafTextSpan(
        id="eq_1",
        colour=PromptColour.Equation,
        content="x = 1",
        source_offsets=(0, 5),
    )

    with pytest.raises(IndexError, match="Slot 1 out of bounds"):
        tree.graft(1, eq_span)


def test_successful_slot_grafting():
    parse_op = PromptOperator(
        id="parse_equation",
        source_colours=(PromptColour.RawTextSpan,),
        target_colour=PromptColour.Equation,
        arity=1,
    )
    isolate_op = PromptOperator(
        id="isolate_var",
        source_colours=(PromptColour.Equation,),
        target_colour=PromptColour.IsolatedVariable,
        arity=1,
    )

    raw_leaf = LeafTextSpan(
        id="raw_1",
        colour=PromptColour.RawTextSpan,
        content="x + 2*y = 5",
        source_offsets=(0, 11),
    )

    parse_tree = OperadTreeNode(operator=parse_op, children=()).graft(0, raw_leaf)
    assert parse_tree.output_colour == PromptColour.Equation

    isolated_tree = OperadTreeNode(operator=isolate_op, children=()).graft(0, parse_tree)
    assert isolated_tree.output_colour == PromptColour.IsolatedVariable


def test_congruence_ideal_null_tree_projection():
    ideal_rational = CongruenceIdeal(
        id="IDEAL_EXACT_RATIONAL_DOMAIN",
        target_colour=PromptColour.RationalValue,
        assertion="isinstance(val, Fraction) and not isinstance(val, (float, complex))",
    )

    # 1. Float strings trigger NullTree
    for float_val in (3.1415, 0.0, 1e-4, "2.5", "0.001", "1e-5"):
        proj = ideal_rational.evaluate_rational_domain(float_val)
        assert proj is not None, f"Float {float_val!r} must project to NullTree"
        assert proj.is_null
        assert proj.ideal_id == "IDEAL_EXACT_RATIONAL_DOMAIN"
        assert "float/decimal" in proj.reason

    # 2. Exact rationals are admitted
    for exact_val in ("1", "-5", "3/4", "-7/11", Fraction(3, 4), 42):
        assert ideal_rational.evaluate_rational_domain(exact_val) is None


def test_congruence_ideal_absorption_in_grafting():
    op = PromptOperator(
        id="add",
        source_colours=(PromptColour.RationalValue, PromptColour.RationalValue),
        target_colour=PromptColour.RationalValue,
        arity=2,
    )
    tree = OperadTreeNode(operator=op, children=())

    null_child = NullTree(
        ideal_id="IDEAL_EXACT_RATIONAL_DOMAIN",
        reason="float approximation detected",
        target_colour=PromptColour.RationalValue,
    )

    # Grafting a null child absorbs parent to NullTree
    grafted = tree.graft(0, null_child)
    assert grafted.is_null
    assert isinstance(grafted, NullTree)
    assert "grafted child is null tree" in grafted.reason


def test_annihilator_decoy_refutation_witness_checks():
    decoy = AnnihilatorDecoy(
        id="AB_FALSE_CERTAINTY_DECOY",
        description="Catches false decoy candidate",
        decoy_candidate_bindings={"x": "3", "y": "0"},
        refutation_witness={
            "equation": "x + 2*y = 5",
            "evaluation": "3 + 2*(0) = 3 != 5",
            "action": "annihilate_tree",
        },
    )

    # 1. Non-matching candidate is irrelevant
    irr = decoy.evaluate({"x": "1", "y": "2"}, None)
    assert irr["disposition"] == "Irrelevant"

    # 2. Matching candidate without refutation witness raises ValueError
    with pytest.raises(ValueError, match="DECOY_TRAP_UNREFUTED.*without refutation"):
        decoy.evaluate({"x": "3", "y": "0"}, None)

    # 3. Matching candidate with bad refutation witness (no inequality) raises ValueError
    bad_witness = {"equation": "x + 2*y = 5", "evaluation": "looks fine"}
    with pytest.raises(ValueError, match="must demonstrate inequality"):
        decoy.evaluate({"x": "3", "y": "0"}, bad_witness)

    # 4. Matching candidate with genuine refutation witness -> Neutralized
    good_witness = {
        "equation": "x + 2*y = 5",
        "evaluation": "3 + 2*(0) = 3 != 5",
        "action": "annihilate_tree",
    }
    neut = decoy.evaluate({"x": "3", "y": "0"}, good_witness)
    assert neut["disposition"] == "Neutralized"
    assert neut["decoy_id"] == "AB_FALSE_CERTAINTY_DECOY"
    assert neut["witness_evaluation"] == "3 + 2*(0) = 3 != 5"


def test_coloured_operad_prompt_envelope_validation():
    prompt = ColouredOperadPrompt(
        schema_id="core.coda.categorical-operad-prompt.v2",
        family_name="test_family",
        prompt_id="P_TEST",
        colours=(
            PromptColour.RawTextSpan,
            PromptColour.Equation,
            PromptColour.IsolatedVariable,
            PromptColour.RationalValue,
        ),
        operands=(
            LeafTextSpan(
                id="span_1",
                colour=PromptColour.RawTextSpan,
                content="x + 2*y = 5",
                source_offsets=(0, 11),
            ),
        ),
        operators=(
            PromptOperator(
                id="parse_eq",
                source_colours=(PromptColour.RawTextSpan,),
                target_colour=PromptColour.Equation,
                arity=1,
            ),
        ),
    )
    assert prompt.validate() is True

    # Bad schema id raises ValueError
    bad_prompt = ColouredOperadPrompt(
        schema_id="unsupported.v0",
        family_name="test_family",
        prompt_id="P_TEST",
        colours=prompt.colours,
        operands=prompt.operands,
        operators=prompt.operators,
    )
    with pytest.raises(ValueError, match="Unsupported schema_id"):
        bad_prompt.validate()
