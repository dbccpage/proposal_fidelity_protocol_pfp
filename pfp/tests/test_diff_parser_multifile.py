"""A refusal may not name a construct the input does not contain.

`parse_unified_diff` rejected every plain multi-file unified diff -- the kind
`diff -u` emits and git accepts -- with:

    Old-file header disagrees with diff --git path

on input containing no `diff --git` line at all. `current_left` is set only by
the `diff --git` branch, so it stays `None` throughout such a patch, and the
`--- ` branch compared a real path against `None`. The first file escaped only
because `section_open` was still `False`; every file after it refused.

The `+++ ` branch has always guarded `current_right is not None`. The asymmetry
between the two branches was the entire defect.

It survived because **no test asserted the content of an error message.** The
one parser test in the suite passes a single-file `diff --git` patch and checks
`is_valid is True`. A parser is a producer of refusals, and a refusal nobody
reads is a refusal nobody can find wrong.

AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from omega_engine_pfp.domain.diff_parser import parse_unified_diff

HUNK = "@@ -1 +1 @@\n-old\n+new\n"


def _plain(*paths: str) -> str:
    """A unified diff with no `diff --git` lines, as `diff -u` emits."""
    return "".join(f"--- a/{p}\n+++ b/{p}\n{HUNK}" for p in paths)


def _git(*paths: str) -> str:
    return "".join(
        f"diff --git a/{p} b/{p}\n--- a/{p}\n+++ b/{p}\n{HUNK}" for p in paths
    )


# --------------------------------------------------------------------------
# The defect
# --------------------------------------------------------------------------


def test_a_plain_two_file_diff_parses() -> None:
    """The reported defect, at its smallest.

    Mutation: drop the `current_left is not None` guard and this fails with
    `Old-file header disagrees with diff --git path`.
    """
    result = parse_unified_diff(_plain("src/x.py", "src/y.py"))
    assert result.is_valid is True, result.error_message
    assert set(result.touched_paths) == {"src/x.py", "src/y.py"}


def test_a_plain_single_file_diff_still_parses() -> None:
    """This one always worked -- by accident, not by design.

    The first `--- ` escapes the comparison because `section_open` is still
    False. Pinned so a future guard change cannot break the case that happened
    to be safe.
    """
    result = parse_unified_diff(_plain("src/only.py"))
    assert result.is_valid is True, result.error_message
    assert set(result.touched_paths) == {"src/only.py"}


@pytest.mark.parametrize("count", [2, 3, 5])
def test_a_plain_diff_parses_at_any_file_count(count: int) -> None:
    """The failure was per-file after the first, so it scales with the patch."""
    paths = [f"src/f{index}.py" for index in range(count)]
    result = parse_unified_diff(_plain(*paths))
    assert result.is_valid is True, result.error_message
    assert set(result.touched_paths) == set(paths)


# --------------------------------------------------------------------------
# The guard must not have weakened the check it guards
# --------------------------------------------------------------------------


def test_an_old_header_disagreeing_with_its_diff_git_line_is_still_refused() -> None:
    """The check the guard protects. Adding a None test must not disable it.

    Mutation: guard on `old_path is None` instead, or drop the comparison, and
    a patch whose `--- ` names a different file than its `diff --git` is
    admitted -- which is the forgery the check exists to stop.
    """
    patch = (
        "diff --git a/src/declared.py b/src/declared.py\n"
        "--- a/src/actually_other.py\n"
        "+++ b/src/declared.py\n" + HUNK
    )
    result = parse_unified_diff(patch)
    assert result.is_valid is False
    assert result.error_message == "Old-file header disagrees with diff --git path"


def test_a_new_header_disagreeing_with_its_diff_git_line_is_still_refused() -> None:
    """The sibling branch, which was already correct."""
    patch = (
        "diff --git a/src/declared.py b/src/declared.py\n"
        "--- a/src/declared.py\n"
        "+++ b/src/actually_other.py\n" + HUNK
    )
    result = parse_unified_diff(patch)
    assert result.is_valid is False
    assert result.error_message == "New-file header disagrees with diff --git path"


def test_a_well_formed_git_multi_file_diff_still_parses() -> None:
    result = parse_unified_diff(_git("src/a.py", "src/b.py"))
    assert result.is_valid is True, result.error_message
    assert set(result.touched_paths) == {"src/a.py", "src/b.py"}


# --------------------------------------------------------------------------
# The general property, which is what would have caught this
# --------------------------------------------------------------------------

#: Inputs that must be refused, none of which contains `diff --git`.
MALFORMED_WITHOUT_GIT_HEADER = [
    pytest.param("--- a/x.py\n--- a/y.py\n", id="repeated-old-header"),
    pytest.param("+++ b/x.py\n" + HUNK, id="new-header-without-old"),
    pytest.param("--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n?bad\n", id="bad-hunk-prefix"),
    pytest.param("--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n", id="truncated-hunk"),
    pytest.param("not a diff at all\n", id="not-a-diff"),
]


@pytest.mark.parametrize("patch", MALFORMED_WITHOUT_GIT_HEADER)
def test_a_refusal_never_names_a_construct_absent_from_the_input(patch: str) -> None:
    """The invariant the reported defect violated, stated generally.

    An error naming `diff --git` for input containing no such line sends the
    reader looking for something that was never there. This is the check that
    generalises past the one branch that was wrong, and it is the check whose
    absence let the defect ship: nothing asserted message content at all.
    """
    result = parse_unified_diff(patch)
    assert result.is_valid is False, "fixture must be invalid for this to mean anything"
    message = result.error_message or ""
    assert "diff --git" not in message, (
        f"refusal names `diff --git` but the input has none: {message!r}"
    )


def test_the_property_check_is_not_vacuous() -> None:
    """Negative control on the check above.

    If every fixture happened to be valid, or the parser stopped producing
    messages, the parametrised check would pass while testing nothing.
    """
    for param in MALFORMED_WITHOUT_GIT_HEADER:
        patch = param.values[0]
        assert "diff --git" not in patch
        result = parse_unified_diff(patch)
        assert result.is_valid is False
        assert result.error_message, "a refusal must say why"


# --------------------------------------------------------------------------
# What widening the plain-diff path let through
# --------------------------------------------------------------------------
#
# Admitting plain multi-file diffs widened what the parser accepts, and the
# `--- ` branch that opens each of those sections never finished the previous
# one. Only `diff --git` did. So `section_has_change` -- the flag that makes a
# section prove it carries a change -- leaked across the boundary between two
# plain files, and a header-only section rode in on its neighbour's hunk. Both
# paths were then reported as touched, so a patch could claim a file it never
# altered.

HEADER_ONLY_SECTION = [
    pytest.param(
        f"--- a/x.py\n+++ b/x.py\n{HUNK}--- a/y.py\n+++ b/y.py\n",
        "y.py",
        id="trailing-section-has-no-hunk",
    ),
    pytest.param(
        f"--- a/x.py\n+++ b/x.py\n--- a/y.py\n+++ b/y.py\n{HUNK}",
        "x.py",
        id="leading-section-has-no-hunk",
    ),
]


@pytest.mark.parametrize("patch,unchanged_path", HEADER_ONLY_SECTION)
def test_a_plain_section_without_a_hunk_is_refused(
    patch: str, unchanged_path: str
) -> None:
    """Every plain section must carry its own change, not borrow a neighbour's.

    Mutation: delete the `finish_section()` call from the `--- ` branch and
    both cases are accepted, because `section_has_change` stays `True` from the
    file that did have a hunk.
    """
    result = parse_unified_diff(patch)
    assert result.is_valid is False, (
        f"a section with no hunk was accepted; {unchanged_path} is unchanged"
    )
    assert "no patch" in (result.error_message or "")


@pytest.mark.parametrize("patch,unchanged_path", HEADER_ONLY_SECTION)
def test_a_refused_patch_claims_no_paths(patch: str, unchanged_path: str) -> None:
    """A refusal must not leave a path claimed.

    `touched_paths` feeds path-ownership checks. A patch that never changed
    `unchanged_path` must not put it -- or anything else -- on that list.
    """
    result = parse_unified_diff(patch)
    assert result.is_valid is False
    assert unchanged_path not in set(result.touched_paths)
    assert not set(result.touched_paths)


def test_the_hunk_bearing_twin_of_those_fixtures_still_parses() -> None:
    """Negative control: the refusal above is about the missing hunk, nothing else.

    Same two files, same plain shape, both sections carrying a hunk. If this
    went red, the fix would be refusing valid plain multi-file diffs rather
    than header-only sections.
    """
    result = parse_unified_diff(_plain("x.py", "y.py"))
    assert result.is_valid is True, result.error_message
    assert set(result.touched_paths) == {"x.py", "y.py"}
