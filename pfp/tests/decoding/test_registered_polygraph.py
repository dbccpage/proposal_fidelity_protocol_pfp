"""Ground-step registration controls; no system-wide confluence claim."""

from dataclasses import replace

import pytest

from omega_engine_pfp.domain.decoding.errors import DecodingError, DecodingRefusalCode
from omega_engine_pfp.domain.decoding.polygraph import (
    Confluence2Cell,
    RewriteStep,
    TarskiPolygraph,
)


def cell(step: RewriteStep) -> Confluence2Cell:
    return Confluence2Cell("peak", step.source_term, step.result_term,
        (step,), (), step.result_term)


def test_empty_registry_refuses_invented_join_step() -> None:
    result = TarskiPolygraph(()).validate_confluence_result(cell(RewriteStep("fake", "0", "x", "y")))
    assert result.is_failure
    assert result.error.code == DecodingRefusalCode.UNREGISTERED_REWRITE_RULE


def test_registered_rule_name_is_not_enough() -> None:
    registered = RewriteStep("r", "0", "x", "y")
    result = TarskiPolygraph((registered,)).validate_confluence_result(
        cell(RewriteStep("forged-r", "0", "x", "y")))
    assert result.error.code == DecodingRefusalCode.UNREGISTERED_REWRITE_RULE


@pytest.mark.parametrize("field,value", [
    ("source_term", "foreign"), ("result_term", "foreign"), ("redex_loc", "1"),
])
def test_registered_name_with_changed_ground_step_refuses(field: str, value: str) -> None:
    registered = RewriteStep("r", "0", "x", "y")
    result = TarskiPolygraph((registered,)).validate_confluence_result(
        cell(replace(registered, **{field: value})))
    assert result.error.code == DecodingRefusalCode.REGISTERED_REWRITE_MISMATCH


def test_independently_created_exact_registered_step_passes() -> None:
    registered = RewriteStep("r", "0", "x", "y")
    assert TarskiPolygraph((registered,)).validate_confluence(cell(RewriteStep("r", "0", "x", "y")))


def test_both_branches_are_checked_for_registration() -> None:
    registered = RewriteStep("r", "0", "x", "z")
    forged = RewriteStep("fake", "0", "y", "z")
    result = TarskiPolygraph((registered,)).validate_confluence_result(
        Confluence2Cell("peak", "x", "y", (registered,), (forged,), "z"))
    assert result.error.code == DecodingRefusalCode.UNREGISTERED_REWRITE_RULE


def test_multiple_registered_ground_steps_with_same_name_pass() -> None:
    first, second = RewriteStep("r", "0", "x", "y"), RewriteStep("r", "1", "y", "z")
    assert TarskiPolygraph((first, second)).validate_confluence(
        Confluence2Cell("peak", "x", "z", (first, second), (), "z"))


def test_discontinuous_chain_keeps_original_refusal() -> None:
    first, second = RewriteStep("r1", "0", "x", "y"), RewriteStep("r2", "0", "wrong", "z")
    result = TarskiPolygraph((first, second)).validate_confluence_result(
        Confluence2Cell("peak", "x", "z", (first, second), (), "z"))
    assert result.error.code == DecodingRefusalCode.DISCONTINUOUS_REWRITE_CHAIN


def test_divergent_endpoints_keep_original_refusal() -> None:
    registered = RewriteStep("r", "0", "x", "y")
    result = TarskiPolygraph((registered,)).validate_confluence_result(
        Confluence2Cell("peak", "x", "z", (registered,), (), "z"))
    assert result.error.code == DecodingRefusalCode.DIVERGENT_JOIN_MISMATCH


def test_reflexive_paths_remain_valid_without_rules() -> None:
    assert TarskiPolygraph(()).validate_confluence(Confluence2Cell("x", "x", "x", (), (), "x"))


def test_step_subclass_cannot_override_registration_equality() -> None:
    class ForgedStep(RewriteStep):
        def __eq__(self, _other):
            return True
    registered = RewriteStep("r", "0", "x", "y")
    forged = ForgedStep("r", "wrong", "x", "forged")
    result = TarskiPolygraph((registered,)).validate_confluence_result(cell(forged))
    assert result.error.code == DecodingRefusalCode.REGISTERED_REWRITE_MISMATCH


def test_registry_step_subclass_is_refused() -> None:
    class ForgedStep(RewriteStep):
        def __eq__(self, _other):
            return True
    with pytest.raises(DecodingError) as caught:
        TarskiPolygraph((ForgedStep("r", "0", "x", "y"),))
    assert caught.value.code == DecodingRefusalCode.REGISTERED_REWRITE_MISMATCH


def test_string_subclasses_cannot_forge_ground_step_fields() -> None:
    class ForgedString(str):
        def __eq__(self, _other):
            return True
    with pytest.raises(TypeError, match="Terms must be strings"):
        RewriteStep("r", "0", "x", ForgedString("forged"))
    registered = RewriteStep("r", "0", "x", "y")
    forged = RewriteStep("r", "0", "x", "forged")
    object.__setattr__(forged, "result_term", ForgedString("forged"))
    result = TarskiPolygraph((registered,)).validate_confluence_result(cell(forged))
    assert result.error.code == DecodingRefusalCode.REGISTERED_REWRITE_MISMATCH


def test_string_subclasses_cannot_forge_join_equality() -> None:
    class ForgedString(str):
        def __eq__(self, _other):
            return True
    registered = RewriteStep("r", "0", "x", "y")
    forged_cell = Confluence2Cell("peak", "x", "z", (registered,), (), ForgedString("not-a-join"))
    result = TarskiPolygraph((registered,)).validate_confluence_result(forged_cell)
    assert result.error.code == DecodingRefusalCode.REGISTERED_REWRITE_MISMATCH
