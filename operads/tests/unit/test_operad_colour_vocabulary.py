"""Regression tests for the admitted operad colour vocabulary.

`domain/operad/colours.py` declared only eight of the ten admitted colours,
omitting `Contract` and `Diagram`. The V3 compiler then silently dropped an
unrecognised source colour -- changing the operation's arity -- and rewrote an
unrecognised target colour to `Receipt`, while still reporting success.

Sixteen admitted skills declare one of the two missing colours, including
`blackrod`, `rip-lawyers`, `nomos-law-contract-manager` and
`meta-law-contract-enforcer`, so this was corrupting real catalog entries rather
than a hypothetical.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from operads.application.operad.compiler_service import (
    OperadCompilerService,
)
from operads.domain.operad import ADMITTED_FINITE_COLOURS, Colour
from operads.infrastructure.legacy.models import ADMITTED_COLOURS

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_PACKAGE_SIGNATURE = (
    _REPO_ROOT
    / "operads"
    / "skill_operad"
    / "json"
    / "operad_signature.json"
)
_OPERATIONS_SIGNATURE = (
    _REPO_ROOT
    / "operations"
    / "skill_operad"
    / "json"
    / "operad_signature.json"
)


def _registry(path: pathlib.Path) -> dict:
    """Load one signature. A missing file fails; there is no fallback path."""

    assert path.is_file(), f"operad signature is missing: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


def _write_skill(directory: pathlib.Path, name: str, sources, target) -> pathlib.Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "SKILL.md"
    path.write_text(
        "---\n"
        f"name: {name}\n"
        f"operad_source_colours: {json.dumps(list(sources))}\n"
        f"operad_target_colour: {target}\n"
        f"operad_arity: {len(sources)}\n"
        "operad_residual: unknown\n"
        "---\n\n"
        "# body\n",
        encoding="utf-8",
    )
    return path


def test_all_ten_admitted_colours_are_declared() -> None:
    assert len(ADMITTED_FINITE_COLOURS) == 10
    assert "Contract" in ADMITTED_FINITE_COLOURS
    assert "Diagram" in ADMITTED_FINITE_COLOURS


def test_the_three_colour_vocabularies_agree() -> None:
    """Domain, legacy infrastructure, and the sole OEWAS signature agree."""
    package_colours = set(_registry(_PACKAGE_SIGNATURE)["colours"])
    assert not _OPERATIONS_SIGNATURE.exists(), "the removed operations copy must not return"
    assert set(ADMITTED_FINITE_COLOURS) == set(ADMITTED_COLOURS) == package_colours


@pytest.mark.parametrize("colour", ["Contract", "Diagram"])
def test_previously_missing_colours_are_constructible(colour: str) -> None:
    assert Colour(colour).name == colour


def test_contract_skill_keeps_its_arity_and_target(tmp_path: pathlib.Path) -> None:
    """The exact shape of the old corruption: arity 2 -> 1, target -> Receipt."""
    path = _write_skill(
        tmp_path / "nomos-law-contract-manager",
        "nomos-law-contract-manager",
        ["Contract", "State"],
        "Contract",
    )

    parsed = OperadCompilerService().parse_skill_md(path)

    assert parsed.is_ok
    signature = parsed.unwrap()
    assert [c.name for c in signature.signature.source] == ["Contract", "State"]
    assert signature.signature.target.name == "Contract"


def test_diagram_target_is_not_rewritten_to_receipt(tmp_path: pathlib.Path) -> None:
    path = _write_skill(tmp_path / "meta-dda-dag-emitter", "meta-dda-dag-emitter", ["State"], "Diagram")

    parsed = OperadCompilerService().parse_skill_md(path)

    assert parsed.is_ok
    assert parsed.unwrap().signature.target.name == "Diagram"


def test_unadmitted_target_is_refused_rather_than_defaulted(tmp_path: pathlib.Path) -> None:
    """A colour outside the vocabulary must not be quietly repaired."""
    path = _write_skill(tmp_path / "bogus", "bogus", ["State"], "Nonsense")

    service = OperadCompilerService()
    parsed = service.parse_skill_md(path)
    assert parsed.is_err
    assert parsed.error.code == "UNADMITTED_TARGET_COLOUR"
    assert any("Nonsense" in reason for reason in service.refusals)


def test_unadmitted_source_is_refused_rather_than_dropped(tmp_path: pathlib.Path) -> None:
    """Dropping a source silently changes arity, which is the worse failure."""
    path = _write_skill(tmp_path / "bogus2", "bogus2", ["State", "Nonsense"], "Receipt")

    service = OperadCompilerService()
    parsed = service.parse_skill_md(path)
    assert parsed.is_err
    assert parsed.error.code == "UNADMITTED_SOURCE_COLOUR"
    assert any("Nonsense" in reason for reason in service.refusals)


def test_every_catalog_entry_uses_only_admitted_colours() -> None:
    """The canonical OEWAS signature must use only admitted colours."""
    admitted = set(ADMITTED_FINITE_COLOURS)
    offenders = []
    registry = _registry(_PACKAGE_SIGNATURE)
    for entry in registry["identities"] + registry["operations"]:
        used = set(entry["source_colours"]) | {entry["target_colour"]}
        if not used <= admitted:
            offenders.append(
                (_PACKAGE_SIGNATURE.as_posix(), entry["skill_id"], sorted(used - admitted))
            )

    assert offenders == []
