"""The usage ledger must under-report loudly, never over-report quietly.

This ledger is the only number any cull policy will have. Two failure modes
matter and they are not symmetric. Over-reporting invents a skill's liveness and
keeps dead weight; under-reporting archives something in use. Both are checked,
but the tests that matter most are the ones that stop a name being minted:
`normalize_skill_id` is the single point where a plugin skill, a built-in slash
command, or a package renamed away could enter the garden's own statistics.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from omega_engine_operads.infrastructure.skill_garden import (
    transcript_harvester as harvester,
)
from omega_engine_operads.infrastructure.skill_garden import usage_ledger as ledger

ROSTER = frozenset({"auto-oe-autop", "techne-run-tests", "blackrod"})


# --------------------------------------------------------------------------
# normalize_skill_id: the gate that stops a foreign name being minted
# --------------------------------------------------------------------------


def test_a_bare_roster_name_is_accepted() -> None:
    assert ledger.normalize_skill_id("auto-oe-autop", ROSTER) == "auto-oe-autop"


def test_a_directory_scoped_name_is_reduced_to_the_package() -> None:
    """Observed shape: `.claude/worktrees/bg-session-worktree:auto-oe-autop`."""
    scoped = ".claude/worktrees/bg-session-worktree:auto-oe-autop"
    assert ledger.normalize_skill_id(scoped, ROSTER) == "auto-oe-autop"


def test_a_plugin_skill_is_refused() -> None:
    """`mattpocock-skills:grilling` is real, and is not ours.

    Mutation: return the suffix unconditionally and this fails -- the plugin's
    skill would be counted as a garden package that does not exist.
    """
    assert ledger.normalize_skill_id("mattpocock-skills:grilling", ROSTER) is None


def test_a_builtin_command_is_refused() -> None:
    """`/clear`, `/plan`, `/compact` are recorded the same way as a skill."""
    for builtin in ("clear", "plan", "compact", "model", "init"):
        assert ledger.normalize_skill_id(builtin, ROSTER) is None


def test_a_package_renamed_away_is_refused() -> None:
    """`github` was renamed to `techne-github`.

    Its invocations are real history, but the call failed when it was made and
    the name must not resurrect as a phantom roster entry.
    """
    assert ledger.normalize_skill_id("github", ROSTER) is None


@pytest.mark.parametrize("value", ["", "   ", None, 17, ["auto-oe-autop"]])
def test_junk_is_refused_rather_than_raising(value: object) -> None:
    assert ledger.normalize_skill_id(value, ROSTER) is None  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Content addressing
# --------------------------------------------------------------------------


def _event(**overrides: object) -> dict:
    base = dict(
        skill_id="auto-oe-autop",
        invoked_at="2026-08-31T06:30:00+00:00",
        host="claude",
        channel="tool_use",
        caller="direct",
        session_id="abc",
    )
    base.update(overrides)
    return ledger.make_usage_event(**base)  # type: ignore[arg-type]


def test_the_same_invocation_yields_the_same_entry_id() -> None:
    assert _event()["entry_id"] == _event()["entry_id"]


def test_entry_id_excludes_observation_time() -> None:
    """Re-harvesting the same transcript must not duplicate the row.

    Mutation: fold `observed_at` into the identity and this fails, because two
    harvests of one unchanged transcript would then disagree.
    """
    first, second = _event(), _event()
    assert first["observed_at"] != second["observed_at"] or True
    assert first["entry_id"] == second["entry_id"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("skill_id", "blackrod"),
        ("invoked_at", "2026-08-31T06:31:00+00:00"),
        ("channel", "slash"),
        ("caller", "slash"),
        ("session_id", "def"),
        ("host", "codex"),
    ],
)
def test_each_identity_field_changes_the_entry_id(field: str, value: str) -> None:
    """Mutation: drop any of these from the identity and this names it."""
    assert _event()["entry_id"] != _event(**{field: value})["entry_id"]


def test_an_event_never_claims_authority() -> None:
    event = _event()
    assert event["authority_effect"] == "None"
    assert event["classification"] == "RecordedResidualObservation"
    assert event["schema"] == ledger.USAGE_SCHEMA


def test_an_empty_skill_id_is_refused() -> None:
    with pytest.raises(ledger.UsageLedgerError):
        ledger.make_usage_event(skill_id="  ", invoked_at="2026-08-31T00:00:00+00:00")


# --------------------------------------------------------------------------
# Append, read back, summarise
# --------------------------------------------------------------------------


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    (tmp_path / ".git").mkdir()
    skills = tmp_path / ".agents" / "skills"
    for name in ("auto-oe-autop", "blackrod", "_shared"):
        (skills / name).mkdir(parents=True)
        (skills / name / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    return tmp_path


def test_roster_excludes_libraries(fake_repo: Path) -> None:
    """`_shared` and `_templates` are libraries, not skills.

    Counting them would put two packages in the denominator that can never be
    invoked, and the cull would nominate them every time.
    """
    assert ledger.garden_roster(fake_repo) == frozenset({"auto-oe-autop", "blackrod"})


def test_appending_twice_writes_once(fake_repo: Path) -> None:
    events = [_event(), _event()]
    first = ledger.append_usage_events(fake_repo, events)
    second = ledger.append_usage_events(fake_repo, events)
    assert first["written"] == 1, "identical events collapse within one call"
    assert second["written"] == 0 and second["skipped"] == 2


def test_rows_land_in_the_day_their_timestamp_names(fake_repo: Path) -> None:
    ledger.append_usage_events(fake_repo, [_event(invoked_at="2026-07-04T12:00:00+00:00")])
    assert (ledger.usage_dir(fake_repo) / "2026-07-04.jsonl").is_file()


def test_reading_back_recovers_what_was_written(fake_repo: Path) -> None:
    ledger.append_usage_events(fake_repo, [_event(), _event(skill_id="blackrod")])
    rows = ledger.load_usage_events(fake_repo)
    assert sorted(row["skill_id"] for row in rows) == ["auto-oe-autop", "blackrod"]


def test_since_and_until_bound_the_read(fake_repo: Path) -> None:
    old = _event(invoked_at="2026-01-01T00:00:00+00:00")
    new = _event(invoked_at="2026-08-31T00:00:00+00:00")
    ledger.append_usage_events(fake_repo, [old, new])
    cutoff = datetime(2026, 6, 1, tzinfo=timezone.utc)
    assert len(ledger.load_usage_events(fake_repo, since=cutoff)) == 1
    assert len(ledger.load_usage_events(fake_repo, until=cutoff)) == 1


def test_last_used_index_keeps_the_most_recent(fake_repo: Path) -> None:
    ledger.append_usage_events(
        fake_repo,
        [
            _event(invoked_at="2026-08-01T00:00:00+00:00"),
            _event(invoked_at="2026-08-20T00:00:00+00:00"),
        ],
    )
    index = ledger.last_used_index(fake_repo)
    assert index["auto-oe-autop"] == datetime(2026, 8, 20, tzinfo=timezone.utc)


def test_span_is_empty_when_nothing_was_recorded(fake_repo: Path) -> None:
    """The refusal a cull policy reads before nominating anything."""
    assert ledger.ledger_span(fake_repo) == (None, None)


def test_span_measures_first_to_last(fake_repo: Path) -> None:
    ledger.append_usage_events(
        fake_repo,
        [
            _event(invoked_at="2026-08-01T00:00:00+00:00"),
            _event(invoked_at="2026-08-21T00:00:00+00:00"),
        ],
    )
    first, last = ledger.ledger_span(fake_repo)
    assert last - first == timedelta(days=20)


def test_summary_counts_the_unseen(fake_repo: Path) -> None:
    ledger.append_usage_events(fake_repo, [_event()])
    report = ledger.summarize(fake_repo)
    assert report["roster"] == 2 and report["seen"] == 1 and report["never_seen"] == 1


def test_a_malformed_row_is_reported_not_swallowed(fake_repo: Path) -> None:
    """A ledger that silently drops rows it cannot parse under-counts.

    Mutation: catch and continue instead of raising, and a corrupted ledger
    would read as a quiet garden.
    """
    day = ledger.usage_dir(fake_repo) / "2026-08-31.jsonl"
    day.parent.mkdir(parents=True, exist_ok=True)
    day.write_text("{not json}\n", encoding="utf-8")
    with pytest.raises(ledger.UsageLedgerError):
        ledger.load_usage_events(fake_repo)


def test_repo_root_detection_does_not_key_on_a_path_that_cannot_exist(
    fake_repo: Path,
) -> None:
    """`check_skill_usage.py` keys its own root walk on `omega_engine_py/`.

    CLAUDE.md's stale-path table states that directory does not exist, so that
    loop never matches and always falls through to the cwd. This one keys on
    `.git` plus `.agents`, both of which do.
    """
    nested = fake_repo / "a" / "b"
    nested.mkdir(parents=True)
    assert ledger.repo_root_from(nested) == fake_repo


# --------------------------------------------------------------------------
# Transcript harvesting
# --------------------------------------------------------------------------


def test_mangle_matches_the_observed_project_directory_names() -> None:
    """Pinned against real directory names, not against the implementation."""
    assert (
        harvester.mangle(Path(r"C:\Users\a343o\source\repos\anomalonpy"))
        == "C--Users-a343o-source-repos-anomalonpy"
    )
    assert (
        harvester.mangle(
            Path(r"C:\Users\a343o\source\repos\anomalonpy\.claude\worktrees\bg-session-worktree")
        )
        == "C--Users-a343o-source-repos-anomalonpy--claude-worktrees-bg-session-worktree"
    )


def test_a_worktree_root_resolves_to_its_main_checkout() -> None:
    """Worktrees each mangle to their own directory.

    Harvesting only the current one would scatter a repository's invocations
    across directories nobody reads. Mutation: return the path unchanged and the
    harvest silently loses every session run from the main checkout.
    """
    worktree = Path(r"C:\repos\anomalonpy\.claude\worktrees\bg-session-worktree")
    assert harvester.main_checkout(worktree) == Path(r"C:\repos\anomalonpy")
    plain = Path(r"C:\repos\anomalonpy")
    assert harvester.main_checkout(plain) == plain


def _transcript(path: Path, records: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def test_both_recorded_shapes_are_harvested(tmp_path: Path) -> None:
    """A tool_use block and a slash command.

    Mutation: harvest only `tool_use` and `auto-oe-autop` under-counts by the
    slash invocations, which are the majority of its real use.
    """
    transcript = tmp_path / "session.jsonl"
    _transcript(
        transcript,
        [
            {
                "timestamp": "2026-08-31T06:30:00.000Z",
                "sessionId": "s1",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Skill",
                            "input": {"skill": "auto-oe-autop"},
                            "caller": {"type": "direct"},
                        }
                    ]
                },
            },
            {
                "timestamp": "2026-08-31T07:00:00.000Z",
                "sessionId": "s1",
                "message": {
                    "content": [{"type": "text", "text": "<command-name>/blackrod</command-name>"}]
                },
            },
        ],
    )
    found = list(harvester.iter_skill_invocations(transcript))
    assert [record["raw"] for record in found] == ["auto-oe-autop", "blackrod"]
    assert [record["channel"] for record in found] == ["tool_use", "slash"]


def test_a_non_skill_tool_use_is_ignored(tmp_path: Path) -> None:
    transcript = tmp_path / "session.jsonl"
    _transcript(
        transcript,
        [
            {
                "timestamp": "2026-08-31T06:30:00.000Z",
                "message": {
                    "content": [{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}]
                },
            }
        ],
    )
    assert list(harvester.iter_skill_invocations(transcript)) == []


def test_a_truncated_line_does_not_cost_the_whole_transcript(tmp_path: Path) -> None:
    """Transcripts are a foreign format this repository does not own."""
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        "{ this is not json\n"
        + json.dumps(
            {
                "timestamp": "2026-08-31T06:30:00.000Z",
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Skill",
                            "input": {"skill": "blackrod"},
                        }
                    ]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    assert [r["raw"] for r in harvester.iter_skill_invocations(transcript)] == ["blackrod"]


def test_a_record_without_a_timestamp_is_not_written(fake_repo: Path, tmp_path: Path) -> None:
    """An undated invocation cannot inform a 30-day window."""
    home = tmp_path / "home"
    project = home / ".claude" / "projects" / harvester.mangle(fake_repo)
    project.mkdir(parents=True)
    _transcript(
        project / "s.jsonl",
        [
            {
                "message": {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Skill",
                            "input": {"skill": "blackrod"},
                        }
                    ]
                }
            }
        ],
    )
    report = harvester.harvest(fake_repo, home=home, apply=True)
    assert report["invocations_found"] == 0
    assert ledger.load_usage_events(fake_repo) == []
