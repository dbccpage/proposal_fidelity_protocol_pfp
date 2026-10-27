"""Memory must be bounded on write and granted on evidence, or not at all.

The Context Protection rule exists because loading many files at once is what
breaks these sessions. A `MEMORY.md` in every package would be that failure
wearing a friendlier name. So the tests that matter here are the ones that stop
memory spreading: the cap, and the refusals.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from operads.infrastructure.skill_garden import skill_memory as memory
from operads.infrastructure.skill_garden import usage_ledger as ledger

NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)


def _repo(tmp_path: Path, packages: list[str]) -> Path:
    (tmp_path / ".git").mkdir()
    skills = tmp_path / ".agents" / "skills"
    for name in packages:
        (skills / name).mkdir(parents=True)
        (skills / name / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    return tmp_path


def _record(root: Path, skill_id: str, times: int, *, days_ago: int = 1) -> None:
    events = [
        ledger.make_usage_event(
            skill_id=skill_id,
            invoked_at=NOW - timedelta(days=days_ago, minutes=index),
            session_id=f"s{index}",
        )
        for index in range(times)
    ]
    ledger.append_usage_events(root, events)


@pytest.fixture()
def healthy(tmp_path: Path) -> Path:
    """A ledger long enough and broad enough to select on."""
    names = ["busy-a", "busy-b", "busy-c", "quiet-a", "quiet-b", "silent"]
    root = _repo(tmp_path, names)
    _record(root, "busy-a", 1, days_ago=90)  # widens the span
    for name in ("busy-a", "busy-b", "busy-c"):
        _record(root, name, 4)
    for name in ("quiet-a", "quiet-b"):
        _record(root, name, 1)
    return root


# --------------------------------------------------------------------------
# Positive control
# --------------------------------------------------------------------------


def test_a_healthy_ledger_grants_a_cohort(healthy: Path) -> None:
    """Without this, every refusal test could pass on a selector that never grants."""
    selection = memory.select(healthy)
    assert selection.refusals == ()
    assert set(selection.granted) == {"busy-a", "busy-b", "busy-c"}


def test_the_control_is_the_near_miss_set(healthy: Path) -> None:
    """Chosen before any outcome is known.

    Mutation: pick the control after observing which granted skills improved and
    the comparison proves nothing, because the groups would differ by outcome
    rather than by treatment.
    """
    selection = memory.select(healthy)
    assert set(selection.control) <= {"quiet-a", "quiet-b"}
    assert set(selection.control) & set(selection.granted) == set()


def test_a_skill_never_invoked_is_in_neither_group(healthy: Path) -> None:
    selection = memory.select(healthy)
    assert "silent" not in selection.granted
    assert "silent" not in selection.control


# --------------------------------------------------------------------------
# Refusals
# --------------------------------------------------------------------------


def test_a_short_ledger_refuses(tmp_path: Path) -> None:
    """The live condition: 20 days against a 30-day minimum."""
    root = _repo(tmp_path, ["a", "b", "c"])
    for name in ("a", "b", "c"):
        _record(root, name, 5)
    selection = memory.select(root)
    assert any("measures the sensor" in reason for reason in selection.refusals)
    assert selection.granted == ()


def test_too_small_a_cohort_refuses(healthy: Path) -> None:
    """One busy skill is not evidence that memory helps skills.

    This is the live condition too: `auto-oe-autop` has 13 invocations and
    nothing else has three.
    """
    selection = memory.select(healthy, min_cohort=4)
    assert any("cannot distinguish" in reason for reason in selection.refusals)
    assert selection.granted == ()


def test_an_empty_ledger_refuses(tmp_path: Path) -> None:
    root = _repo(tmp_path, ["a", "b", "c"])
    selection = memory.select(root)
    assert any("sensor failure" in reason for reason in selection.refusals)
    assert selection.granted == ()


def test_an_unreachable_floor_refuses(healthy: Path) -> None:
    selection = memory.select(healthy, floor=99)
    assert any("no skill reaches" in reason for reason in selection.refusals)


# --------------------------------------------------------------------------
# The cap, enforced on write
# --------------------------------------------------------------------------


def test_memory_is_capped_by_lines(healthy: Path) -> None:
    """Mutation: check the cap on read instead and the file grows unbounded.

    A cap checked on read is not a cap; the bytes are already on disk and
    already in someone's context.
    """
    for index in range(200):
        memory.append_memory(healthy, "busy-a", f"observation {index}")
    text = memory.read_memory(healthy, "busy-a")
    assert len(text.split("\n")) <= memory.MAX_LINES + 1
    assert len(text.encode("utf-8")) <= memory.MAX_BYTES


def test_an_empty_observation_is_refused(healthy: Path) -> None:
    with pytest.raises(memory.MemoryRefusal):
        memory.append_memory(healthy, "busy-a", "   ")


def test_memory_for_a_package_that_does_not_exist_is_refused(healthy: Path) -> None:
    with pytest.raises(memory.MemoryRefusal, match="not a package"):
        memory.append_memory(healthy, "no-such-skill", "hello")


def test_a_written_memory_reads_back(healthy: Path) -> None:
    memory.append_memory(healthy, "busy-a", "the harvester under-counts codex")
    assert "under-counts codex" in memory.read_memory(healthy, "busy-a")


def test_memory_declares_no_authority(healthy: Path) -> None:
    memory.append_memory(healthy, "busy-a", "anything")
    assert "authority_effect: None" in memory.read_memory(healthy, "busy-a")


def test_memory_lives_inside_the_package_it_belongs_to(healthy: Path) -> None:
    """So archiving the skill archives its memory, on the same 30-day clock."""
    memory.append_memory(healthy, "busy-a", "x")
    assert memory.memory_path(healthy, "busy-a").parent.name == "busy-a"


# --------------------------------------------------------------------------
# The cohort record
# --------------------------------------------------------------------------


def test_the_cohort_record_freezes_both_groups(healthy: Path) -> None:
    selection = memory.select(healthy)
    path = memory.record_cohort(healthy, selection)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["authority_effect"] == "None"
    assert set(payload["granted"]) == set(selection.granted)
    assert set(payload["control"]) == set(selection.control)
    assert payload["measurement"], "a cohort with no stated measurement proves nothing"


# --------------------------------------------------------------------------
# The live state, pinned honestly
# --------------------------------------------------------------------------


def test_the_live_selection_currently_refuses() -> None:
    """Pins the truth as of this change.

    Six skills have ever been invoked; one reaches three. Granting memory on
    that would be selecting on noise. When the ledger matures this test is the
    one that must be consciously changed, which is the point of pinning it.
    """
    root = ledger.repo_root_from(Path(__file__).resolve())
    selection = memory.select(root)
    assert selection.refused, (
        "the ledger now supports a memory cohort; update this test deliberately "
        "and record the cohort with --record-cohort"
    )
    assert selection.granted == ()


def test_no_package_carries_memory_yet() -> None:
    """Nothing was granted, so nothing should have been written."""
    root = ledger.repo_root_from(Path(__file__).resolve())
    carrying = sorted(path.parent.name for path in (root / memory.SKILLS_REL).glob("*/MEMORY.md"))
    assert carrying == []
