"""The compile receipt must report refused skills.

Changing the V3 compiler from "repair an unadmitted colour" to "refuse the
skill" removes a silent corruption, but only if the refusal is visible. Without
these tests the change would merely trade a silent repair for a silent drop: the
skill leaves the operad while the receipt still reports PASSED, so
`frontend/cli/operad_cli.py` prints PASSED and exits 0 and the loss is invisible.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import pathlib

from operads.application.operad.compiler_service import (
    OperadCompilerService,
)


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


def _observations(receipt) -> dict:
    return {observation.key: observation.value for observation in receipt.observations}


def test_a_refused_skill_fails_the_compile_receipt(tmp_path: pathlib.Path) -> None:
    _write_skill(tmp_path / "good", "good", ["State"], "Receipt")
    _write_skill(tmp_path / "bad", "bad", ["State"], "Nonsense")

    receipt = OperadCompilerService().compile_skills_garden(tmp_path)

    assert receipt.passed is False
    observations = _observations(receipt)
    assert observations["total_skills_refused"] == 1
    assert any("Nonsense" in str(value) for value in observations.values())


def test_the_refusal_reason_names_the_offending_file(tmp_path: pathlib.Path) -> None:
    _write_skill(tmp_path / "bad", "bad", ["State"], "Nonsense")

    receipt = OperadCompilerService().compile_skills_garden(tmp_path)

    reasons = [
        str(value)
        for key, value in _observations(receipt).items()
        if key.startswith("refusal_")
    ]
    assert reasons, "a refusal must be recorded, not merely counted"
    assert any("bad" in reason for reason in reasons)


def test_a_clean_garden_still_passes(tmp_path: pathlib.Path) -> None:
    _write_skill(tmp_path / "good", "good", ["State"], "Receipt")

    receipt = OperadCompilerService().compile_skills_garden(tmp_path)

    assert receipt.passed is True
    assert _observations(receipt)["total_skills_refused"] == 0


def test_refusals_do_not_leak_between_runs(tmp_path: pathlib.Path) -> None:
    """One service instance reused across roots must not report stale refusals.

    `compile_skills_garden` rebuilds the operad each call; leaving `refusals`
    intact would attribute the first root's problems to the second, with no way
    for a caller to tell them apart.
    """
    _write_skill(tmp_path / "dirty" / "bad", "bad", ["State"], "Nonsense")
    _write_skill(tmp_path / "clean" / "good", "good", ["State"], "Receipt")

    service = OperadCompilerService()

    first = service.compile_skills_garden(tmp_path / "dirty")
    assert first.passed is False

    second = service.compile_skills_garden(tmp_path / "clean")
    assert second.passed is True, "the previous run's refusals leaked into this one"
    assert service.refusals == []


def test_an_empty_garden_does_not_pass(tmp_path: pathlib.Path) -> None:
    """Nothing compiled is not success."""
    receipt = OperadCompilerService().compile_skills_garden(tmp_path)
    assert receipt.passed is False
