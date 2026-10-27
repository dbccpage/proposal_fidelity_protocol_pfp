"""Every new row in the episode sink must be a row `episode.py` would have written.

`episode.py` validates its *input* and refuses unknown fields. It never looks at
the sink afterwards, so a row appended by any other means is never examined
again. That is not hypothetical. It has happened twice:

  * rows 16-20 of `2026-08-27.jsonl`, hand-authored on 2026-08-28, carry
    `disposition` / `resolution` / `authority_effect` and no `schema`, and are
    filed under a day their own timestamps contradict;
  * six rows in `2026-08-31.jsonl`, appended the same way, repaired in the same
    change that added this file.

An append-only ledger nobody validates after the fact has whatever shape its
last writer felt like.

**Ratcheted, not absolute.** Twenty-one rows already deviate and rewriting them
would falsify provenance -- some predate the writer's current field set, and
authoring a `proposed_invariant` for an episode somebody else recorded would be
inventing evidence. They are recorded in `episode_sink_baseline.json`, which this
check only ever reads. A new deviation fails; a recorded one may only be
removed. The estate has settled this argument before: a gate that turns red on
arrival leaves the next person choosing between reverting it and writing
waivers, and a check that can rewrite its own expectations is not a check.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import pathlib

import pytest

HERE = pathlib.Path(__file__).resolve()
REPO_ROOT = HERE.parents[4]
EPISODES = REPO_ROOT / "runs" / "skill_compiler" / "episodes"
BASELINE = (
    HERE.parents[2] / "json" / "episode_sink_baseline.json"
    if (HERE.parents[2] / "json" / "episode_sink_baseline.json").is_file()
    else HERE.parents[1] / "episode_sink_baseline.json"
)

EPISODE_SCHEMA = "core.skill_compiler.episode.v1"
CONFIDENCE_OK = frozenset({"HIGH", "MEDIUM", "LOW"})

#: Exactly the fields `episode.make_episode` emits.
REQUIRED = frozenset(
    {
        "id",
        "ts",
        "source",
        "signal_type",
        "signal",
        "proposed_invariant",
        "locus",
        "confidence",
        "evidence",
        "schema",
    }
)
#: Emitted only when a caller supplies them.
OPTIONAL = frozenset({"extra", "session_id"})


def _load_rows() -> list[tuple[str, int, dict]]:
    found = []
    for day in sorted(EPISODES.glob("*.jsonl")):
        for number, line in enumerate(day.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                found.append((day.name, number, json.loads(line)))
    return found


def _load_baseline() -> dict[str, dict]:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in payload["entries"]}


ROWS = _load_rows()
BASELINED = _load_baseline()
NEW_ROWS = [(d, n, r) for d, n, r in ROWS if r.get("id") not in BASELINED]


def _deviations(day: str, row: dict) -> list[str]:
    problems = []
    keys = set(row)
    missing = sorted(REQUIRED - keys)
    unknown = sorted(keys - REQUIRED - OPTIONAL)
    if missing:
        problems.append("missing %s" % missing)
    if unknown:
        problems.append("carries %s, which episode.py would not write" % unknown)
    if not missing:
        if row["schema"] != EPISODE_SCHEMA:
            problems.append("declares schema %r" % row["schema"])
        if not str(row["signal"]).strip():
            problems.append("empty signal; make_episode raises on this")
        if not str(row["proposed_invariant"]).strip():
            problems.append("empty proposed_invariant; make_episode raises on this")
        if row["confidence"] not in CONFIDENCE_OK:
            problems.append("confidence %r outside %s" % (row["confidence"], sorted(CONFIDENCE_OK)))
        evidence = row["evidence"]
        if not isinstance(evidence, list) or not all(
            isinstance(item, str) and item.strip() for item in evidence
        ):
            problems.append("evidence must be a list of non-empty strings")
    if not str(row.get("ts", "")).startswith(day[:10]):
        problems.append("ts %r does not match its day file" % row.get("ts"))
    return problems


def test_the_sink_is_not_empty() -> None:
    """Negative control: every check below iterates the sink."""
    assert ROWS, "no episode rows found; the checks below would be vacuous"


def test_there_are_rows_outside_the_baseline() -> None:
    """Second negative control.

    If the baseline ever covered every row, the conformance check would pass
    over nothing while looking exactly as green as real success.
    """
    assert NEW_ROWS, (
        "every row in the sink is baselined; the conformance check is vacuous"
    )


@pytest.mark.parametrize("day,number,row", NEW_ROWS)
def test_new_row_is_one_the_writer_would_have_produced(
    day: str, number: int, row: dict
) -> None:
    """Mutation: hand-append a row to any day file and this names it."""
    problems = _deviations(day, row)
    assert not problems, (
        f"{day}:{number} was not written by episode.make_episode -- "
        + "; ".join(problems)
        + ". Append through the writer, or record the row in "
        "episode_sink_baseline.json with the reason it cannot conform."
    )


def test_ids_are_unique_across_the_whole_sink() -> None:
    """A duplicate id means one episode is overwriting another's provenance."""
    ids = [row["id"] for _, _, row in ROWS]
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    assert not duplicates, f"duplicate episode ids: {duplicates}"


def test_the_baseline_only_names_rows_that_still_deviate() -> None:
    """The ratchet's other direction.

    A baselined row that now conforms is debt already paid; leaving it recorded
    would let a future deviation with the same id pass unexamined. Mutation:
    repair a baselined row without removing its entry and this fails.
    """
    by_id = {row["id"]: (day, row) for day, _, row in ROWS}
    settled = []
    for entry_id in BASELINED:
        if entry_id not in by_id:
            continue
        day, row = by_id[entry_id]
        if not _deviations(day, row):
            settled.append(entry_id)
    assert not settled, (
        "these rows now conform but are still baselined; remove them so the "
        f"ratchet keeps tightening: {settled}"
    )


def test_the_baseline_does_not_name_rows_that_are_gone() -> None:
    """A baseline entry for a deleted row is a waiver with nothing under it."""
    present = {row["id"] for _, _, row in ROWS}
    orphaned = sorted(set(BASELINED) - present)
    assert not orphaned, f"baseline names rows no longer in the sink: {orphaned}"
