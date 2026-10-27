"""The refusals are the deliverable; the candidate list is the by-product.

Harvested the day this was written, the ledger says 6 of 115 packages have ever
been invoked. A naive 30-day cull would nominate 95% of the garden. So each
refusal is tested in isolation -- and, just as importantly, there is a positive
control: given a healthy ledger and an approved policy, candidates really are
emitted. A script that always refuses is as useless as one that never does, and
would look identical in CI.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from operads.frontend.presenters.skill_cull import render_manifest
from operads.infrastructure.skill_garden import cull_candidates as cull
from operads.infrastructure.skill_garden import usage_ledger as ledger

NOW = datetime(2026, 10, 1, tzinfo=timezone.utc)

BASE_POLICY = {
    "schema": "core.skill_garden.cull_policy.v1",
    "authority_effect": "None",
    "approved_by": "a-human",
    "approved_at": "2026-09-01",
    "window_days": 30,
    "sensor_epoch": "2026-01-01",
    "minimum_ledger_days": 30,
    "new_skill_grace_days": 45,
    "max_candidate_fraction": 0.25,
    "exempt": [{"id": "kept-forever", "reason": "infrastructure"}],
}


def _make_repo(tmp_path: Path, packages: list[str], policy: dict) -> Path:
    (tmp_path / ".git").mkdir()
    skills = tmp_path / ".agents" / "skills"
    for name in packages:
        (skills / name).mkdir(parents=True)
        (skills / name / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    destination = tmp_path / cull.POLICY_REL
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    return tmp_path


def _record(root: Path, skill_id: str, when: datetime) -> None:
    ledger.append_usage_events(root, [ledger.make_usage_event(skill_id=skill_id, invoked_at=when)])


def _healthy(tmp_path: Path, policy: dict | None = None) -> Path:
    """A repo whose ledger spans long enough and whose garden is mostly alive."""
    names = [f"alive-{index}" for index in range(9)] + ["dead-one", "kept-forever"]
    root = _make_repo(tmp_path, names, policy or BASE_POLICY)
    _record(root, "alive-0", NOW - timedelta(days=90))  # widens the span
    for index in range(9):
        _record(root, f"alive-{index}", NOW - timedelta(days=2))
    return root


def _report(root: Path, **kwargs) -> cull.CullReport:
    policy = cull.load_policy(root)
    return cull.compute_candidates(
        root, now=NOW, policy=policy, check_parity=kwargs.get("check_parity", False)
    )


# --------------------------------------------------------------------------
# Positive control
# --------------------------------------------------------------------------


def test_a_healthy_garden_does_produce_a_candidate(tmp_path: Path) -> None:
    """Without this, every refusal test below could pass on a broken script."""
    report = _report(_healthy(tmp_path))
    assert report.refusals == ()
    assert [row["skill_id"] for row in report.candidates] == ["dead-one"]


def test_a_skill_used_inside_the_window_is_not_nominated(tmp_path: Path) -> None:
    report = _report(_healthy(tmp_path))
    assert "alive-3" in {row["skill_id"] for row in report.used_recently}
    assert "alive-3" not in {row["skill_id"] for row in report.candidates}


def test_an_exempt_skill_is_never_nominated(tmp_path: Path) -> None:
    """`kept-forever` has no invocations at all and must still survive."""
    report = _report(_healthy(tmp_path))
    assert "kept-forever" in {row["skill_id"] for row in report.exempt}
    assert "kept-forever" not in {row["skill_id"] for row in report.candidates}


# --------------------------------------------------------------------------
# Refusal 1: no human approval
# --------------------------------------------------------------------------


def test_an_unapproved_policy_refuses(tmp_path: Path) -> None:
    policy = dict(BASE_POLICY, approved_by="")
    report = _report(_healthy(tmp_path, policy))
    assert any("no human approval" in reason for reason in report.refusals)
    assert report.candidates == ()


# --------------------------------------------------------------------------
# Refusal 2: the ledger is younger than the window
# --------------------------------------------------------------------------


def test_a_ledger_shorter_than_the_window_refuses(tmp_path: Path) -> None:
    """The live condition today: a 30-day window over a 20-day ledger."""
    root = _make_repo(tmp_path, ["a", "b", "c", "d"], BASE_POLICY)
    _record(root, "a", NOW - timedelta(days=10))
    _record(root, "a", NOW - timedelta(days=2))
    report = _report(root)
    assert any("measures the sensor, not the garden" in r for r in report.refusals)
    assert report.candidates == ()


# --------------------------------------------------------------------------
# Refusal 3: the sensor recorded nothing at all
# --------------------------------------------------------------------------


def test_an_empty_ledger_refuses_rather_than_nominating_everything(
    tmp_path: Path,
) -> None:
    """The catastrophe this module exists to prevent.

    Mutation: treat "no events" as "nothing is used" and the script nominates
    the entire garden the first time the sensor breaks.
    """
    root = _make_repo(tmp_path, ["a", "b", "c", "d"], BASE_POLICY)
    report = _report(root)
    assert any("sensor failure" in reason for reason in report.refusals)
    assert report.candidates == ()


# --------------------------------------------------------------------------
# Refusal 4: too much of the garden at once
# --------------------------------------------------------------------------


def test_nominating_too_large_a_share_refuses(tmp_path: Path) -> None:
    names = [f"dead-{index}" for index in range(9)] + ["alive"]
    root = _make_repo(tmp_path, names, BASE_POLICY)
    _record(root, "alive", NOW - timedelta(days=90))
    _record(root, "alive", NOW - timedelta(days=1))
    report = _report(root)
    assert any("above the" in reason and "ceiling" in reason for reason in report.refusals)
    assert report.candidates == ()


def test_the_ceiling_is_a_fraction_not_a_count(tmp_path: Path) -> None:
    """Raising the ceiling must let the same garden through.

    Mutation: hard-code a count and this fails, because the ceiling would stop
    scaling with the garden.
    """
    names = [f"dead-{index}" for index in range(9)] + ["alive"]
    root = _make_repo(tmp_path, names, dict(BASE_POLICY, max_candidate_fraction=0.95))
    _record(root, "alive", NOW - timedelta(days=90))
    _record(root, "alive", NOW - timedelta(days=1))
    report = _report(root)
    assert report.refusals == ()
    assert len(report.candidates) == 9


# --------------------------------------------------------------------------
# The grace period
# --------------------------------------------------------------------------


def test_a_package_younger_than_the_grace_period_is_not_nominated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The clock must not start before the sensor could have seen the skill.

    Mutation: drop the grace period and every skill created this week is
    nominated by the first run that reaches it.
    """
    root = _healthy(tmp_path)
    (root / ".agents" / "skills" / "brand-new").mkdir()
    (root / ".agents" / "skills" / "brand-new" / "SKILL.md").write_text(
        "---\nname: x\n---\n", encoding="utf-8"
    )
    monkeypatch.setattr(
        cull, "skill_birth_dates", lambda _root: {"brand-new": NOW - timedelta(days=3)}
    )
    report = _report(root)
    assert "brand-new" in {row["skill_id"] for row in report.in_grace}
    assert "brand-new" not in {row["skill_id"] for row in report.candidates}


def test_the_grace_period_exceeds_the_window(tmp_path: Path) -> None:
    """Structural guard, asserted on the live policy rather than a fixture.

    If grace ever drops to or below the window, a skill created the day the
    window opens becomes nominable by the very next run.
    """
    root = ledger.repo_root_from(Path(__file__).resolve())
    policy = cull.load_policy(root)
    assert policy.new_skill_grace_days > policy.window_days


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------


def test_a_refused_manifest_lists_no_candidates(tmp_path: Path) -> None:
    root = _make_repo(tmp_path, ["a", "b"], BASE_POLICY)
    text = render_manifest(_report(root), now=NOW)
    assert "## Refused" in text and "## Nominated" not in text


def test_an_approved_manifest_has_somewhere_to_record_approval(tmp_path: Path) -> None:
    text = render_manifest(_report(_healthy(tmp_path)), now=NOW)
    assert "approved_by:" in text and "## Nominated" in text and "`dead-one`" in text


# --------------------------------------------------------------------------
# The live policy
# --------------------------------------------------------------------------


def test_the_live_policy_parses() -> None:
    policy = cull.load_policy(ledger.repo_root_from(Path(__file__).resolve()))
    assert policy.window_days > 0 and policy.max_candidate_fraction <= 1.0


def test_the_live_policy_is_not_yet_approved() -> None:
    """Pins the current state honestly.

    Nothing may be archived until a human fills this in. When that happens this
    test is the one that must be consciously changed, which is the point.
    """
    policy = cull.load_policy(ledger.repo_root_from(Path(__file__).resolve()))
    assert policy.approved_by == "", (
        "the cull policy now records a human approval; update this test "
        "deliberately, and note that the archive lane will begin to act"
    )


def test_skill_birth_dates_reads_real_history() -> None:
    """Negative control on the git parse.

    Mutation: return an empty dict and every package looks ageless, which
    silently disables the grace period.
    """
    root = ledger.repo_root_from(Path(__file__).resolve())
    if not (root / ".git").exists():  # pragma: no cover
        pytest.skip("not a git checkout")
    births = cull.skill_birth_dates(root)
    assert births, "no birth dates parsed; the grace period would be inert"
    assert "auto-oe-autop" in births
