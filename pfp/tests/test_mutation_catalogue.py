"""The catalogue's anchors still match. Cheap, and it runs every suite.

Replaying the whole catalogue takes minutes; this takes milliseconds. The split
matters because of what the custody skill says about a missed anchor:

    An anchor that matches zero or many times is a **setup failure, never a
    result**.

A mutant whose anchor has drifted is not a mutant the suite killed and not one
it survived -- it is a mutation that never ran. Left to the next audit, it would
sit in the catalogue looking like coverage. Here, it fails the moment the code
moves under it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pfp.tests.mutation_catalogue import (
    DEFAULT_TESTS,
    EXCLUDE_FROM_RUNS,
    MUTANTS,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("mutant", MUTANTS, ids=lambda m: m.mutant_id)
def test_every_anchor_matches_exactly_once(mutant) -> None:
    target = REPO_ROOT / mutant.target
    assert target.is_file(), f"{mutant.mutant_id}: {mutant.target} does not exist"
    occurrences = target.read_text(encoding="utf-8").count(mutant.anchor)
    assert occurrences == 1, (
        f"{mutant.mutant_id} anchors {occurrences} times in {mutant.target}; it must "
        "anchor exactly once or the mutation is not the one the catalogue "
        f"describes.\n  intent: {mutant.intent}\n  anchor: {mutant.anchor!r}"
    )


@pytest.mark.parametrize("mutant", MUTANTS, ids=lambda m: m.mutant_id)
def test_every_mutation_actually_changes_the_file(mutant) -> None:
    # A mutant whose replacement equals its anchor is a no-op that reports as a
    # survivor and looks like a gap in the tests. It is a gap in the catalogue.
    assert mutant.applied != mutant.anchor, (
        f"{mutant.mutant_id} replaces its anchor with itself"
    )


def test_mutant_ids_are_unique() -> None:
    # Ids are quoted in commit messages as evidence. A reused id makes two
    # different claims indistinguishable in the record.
    ids = [mutant.mutant_id for mutant in MUTANTS]
    assert len(ids) == len(set(ids)), f"duplicate mutant ids in {ids}"


def test_every_mutant_states_what_it_weakens() -> None:
    # `intent` is what makes a kill judgeable: it says what would be true of the
    # system if the mutation survived. "Changed <= to ==" is the applied field
    # and tells a reader nothing.
    for mutant in MUTANTS:
        assert len(mutant.intent) > 40, (
            f"{mutant.mutant_id} has no substantive intent: {mutant.intent!r}"
        )


def test_the_default_selection_covers_every_test_file() -> None:
    """Guards against the table quietly narrowing to what it can kill.

    The selection was once the whole directory and is now enumerated, which is
    reasonable for ordering and batching and is NOT reasonable if a file can be
    added without being covered. Exactly that happened, and this test is why it
    was noticed: `test_wp6_expectation_corpus.py` -- a corpus written to be an
    INDEPENDENT check on the deciders -- was invisible to every mutant, so no
    kill rate said anything about it.

    Enumerating is allowed. Enumerating incompletely is not, because the
    omission is silent: the harness reports the same clean table over a smaller
    world, which is how a mutation table comes to describe the author's
    confidence rather than the suite's power.
    """
    directory = Path(__file__).resolve().parent
    on_disk = {
        f"pfp/tests/{path.name}"
        for path in directory.glob("test_*.py")
    }
    # EXCLUDE_FROM_RUNS is a deliberate omission, not a gap: this very file
    # asserts each mutant's anchor matches, and while that mutant is APPLIED
    # its anchor is gone, so left in it would witness every mutation.
    missing = sorted(on_disk - set(DEFAULT_TESTS) - set(EXCLUDE_FROM_RUNS))
    assert not missing, (
        "these test files exist and no mutant run will ever execute them:\n  "
        + "\n  ".join(missing)
    )


def test_rust_selections_use_the_ambient_toolchain_and_scoped_serial_library_tests() -> (
    None
):
    rust_mutants = [mutant for mutant in MUTANTS if mutant.runner == "cargo"]
    assert [mutant.mutant_id for mutant in rust_mutants] == ["M01", "M02", "M03", "M04"]
    expected = ("test", "-j", "1", "-p", "core_symbol_game_runtime", "--lib")
    for mutant in rust_mutants:
        assert mutant.tests == expected, mutant.mutant_id
