"""Unreadable, frontmatter-less and malformed skills are typed refusals.

`OperadCompilerService.parse_skill_md` returned `None` without a record for an
unreadable file, a missing frontmatter block and a YAML error. The skill then
left the operad while `compile_skills_garden` still reported PASSED, because the
receipt only failed on refusals it had been told about. Each case below is a
garden with one good skill and one broken one: the old service passed it.

AuthorityEffect: None.
"""

from __future__ import annotations

import pathlib

import pytest

from omega_engine_operads.application.operad.compiler_service import (
    OperadCompilerService,
)
from omega_engine_operads.domain.operad import SkillSignatureRefusal

_GOOD = (
    "---\nname: good\noperad_source_colours: [State]\n"
    "operad_target_colour: Receipt\n---\n\n# body\n"
)


def _garden(tmp_path: pathlib.Path, broken: bytes) -> pathlib.Path:
    (tmp_path / "good").mkdir()
    (tmp_path / "good" / "SKILL.md").write_text(_GOOD, encoding="utf-8")
    (tmp_path / "broken").mkdir()
    (tmp_path / "broken" / "SKILL.md").write_bytes(broken)
    return tmp_path


@pytest.mark.parametrize(
    ("broken", "code"),
    [
        (b"# a skill with no frontmatter block\n", "MISSING_FRONTMATTER"),
        (b"---\nname: [unclosed\n---\n\n# body\n", "FRONTMATTER_YAML_ERROR"),
        (b"\xff\xfe not utf-8 \x80\n", "UNREADABLE_SKILL_FILE"),
        (b"---\n- a\n- list\n---\n\n# body\n", "FRONTMATTER_NOT_A_MAPPING"),
        (
            b"---\nname: s\noperad_source_colours: State\noperad_target_colour: Receipt\n---\n",
            "SOURCE_COLOURS_NOT_A_LIST",
        ),
    ],
)
def test_a_broken_skill_is_a_typed_refusal_and_fails_the_receipt(
    tmp_path: pathlib.Path, broken: bytes, code: str
) -> None:
    root = _garden(tmp_path, broken)
    service = OperadCompilerService()

    parsed = service.parse_skill_md(root / "broken" / "SKILL.md")
    assert parsed.is_err
    assert isinstance(parsed.error, SkillSignatureRefusal)
    assert parsed.error.code == code
    assert parsed.error.locus.endswith("SKILL.md")

    receipt = OperadCompilerService().compile_skills_garden(root)
    observations = {o.key: o.value for o in receipt.observations}
    assert receipt.passed is False, "a dropped skill must not leave the compile PASSED"
    assert observations["total_skills_refused"] == 1
    assert observations["total_skills_compiled"] == 1
    assert code in observations["refusal_0"]
    assert "broken" in observations["refusal_0"]


def test_a_directory_named_skill_md_is_unreadable_not_silently_skipped(
    tmp_path: pathlib.Path,
) -> None:
    (tmp_path / "good").mkdir()
    (tmp_path / "good" / "SKILL.md").write_text(_GOOD, encoding="utf-8")
    (tmp_path / "odd" / "SKILL.md").mkdir(parents=True)

    receipt = OperadCompilerService().compile_skills_garden(tmp_path)

    assert receipt.passed is False
    refusals = [str(o.value) for o in receipt.observations if o.key.startswith("refusal_")]
    assert any("UNREADABLE_SKILL_FILE" in reason for reason in refusals)


def test_two_skills_declaring_one_name_are_refused_not_overwritten(
    tmp_path: pathlib.Path,
) -> None:
    """The operad stores operations by id; the second used to replace the first."""
    for folder, target in (("a", "Receipt"), ("b", "Audit")):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "SKILL.md").write_text(
            f"---\nname: same\noperad_source_colours: [State]\n"
            f"operad_target_colour: {target}\n---\n",
            encoding="utf-8",
        )

    service = OperadCompilerService()
    receipt = service.compile_skills_garden(tmp_path)

    assert receipt.passed is False
    assert service.operad.operations["same"].target_colour == "Receipt"
    assert any("DUPLICATE_OPERATION_ID" in reason for reason in service.refusals)


def test_an_unknown_refusal_code_cannot_be_constructed() -> None:
    with pytest.raises(ValueError):
        SkillSignatureRefusal("MADE_UP", "x/SKILL.md", "detail")
