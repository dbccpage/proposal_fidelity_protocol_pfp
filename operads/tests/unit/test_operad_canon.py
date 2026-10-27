"""The Python canon is the Rust canon's rendering, and the old copies now read it."""

import json
import typing

from operads import canon
from operads.skill_operad.skill_compiler.operad_type_registry import CANON_JSON, repo_root


def test_the_generated_module_and_json_hold_the_same_types():
    document = json.loads((repo_root() / CANON_JSON).read_text(encoding="utf-8"))
    assert [entry["id"] for entry in document["types"]] == list(canon.TYPES)
    for entry in document["types"]:
        assert canon.values_of(entry["id"]) == tuple(entry["values"])
        assert canon.TYPES[entry["id"]]["status"] == entry["status"]
    assert document["colour_meanings"] == canon.COLOUR_MEANINGS


def test_the_generated_enums_are_the_canon_values():
    assert tuple(member.value for member in canon.OperadColour) == canon.OPERAD_COLOUR
    assert tuple(member.value for member in canon.DdcLetter) == canon.DDC_LETTER
    assert canon.DdcLetter.LAMBDA == "Λ"
    assert tuple(member.value for member in canon.HitDisposition) == canon.HIT_DISPOSITION


def test_former_copies_are_the_canon():
    from operads.contracts import typed_capabilities_v1
    from operads.domain.anti_skills.anti_skill_v2 import HIT_DISPOSITIONS
    from operads.domain.ddc_execution import ddc_step, enums
    from operads.domain.ddc_execution.constants import ADMITTED_FINITE_COLOURS as ddc_colours
    from operads.domain.operad.colours import ADMITTED_FINITE_COLOURS
    from operads.domain.planar_substitution import OPERAD_COLOURS
    from operads.infrastructure.legacy.models import ADMITTED_COLOURS
    from operads.skill_operad import ddc_trace_logger
    from operads.skill_operad.domain import colours as skill_colours

    colours = set(canon.OPERAD_COLOUR)
    for copy in (ADMITTED_FINITE_COLOURS, OPERAD_COLOURS, ADMITTED_COLOURS, ddc_colours,
                 skill_colours.ADMITTED_FINITE_COLOURS, typing.get_args(typed_capabilities_v1.Colour)):
        assert set(copy) == colours
    assert enums.OperadColour is canon.OperadColour
    assert ddc_trace_logger.DdcLetter is canon.DdcLetter
    assert ddc_step.CANONICAL_RUNES == canon.DDC_LETTER
    assert not hasattr(ddc_step, "DdcRune")
    assert HIT_DISPOSITIONS == frozenset(canon.HIT_DISPOSITION)
