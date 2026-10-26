"""Strict unified-diff parsing for host-derived code-change path sets."""

from __future__ import annotations

import re
import shlex
from typing import Any, NamedTuple, cast

from .exceptions import SecurityPathViolationError
from omega_engine_pfp.domain.shared_kernel.path import validate_path_security

_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$")
_RENAME_FROM = re.compile(r"^rename from (?P<path>.+)$")
_RENAME_TO = re.compile(r"^rename to (?P<path>.+)$")
_COPY_FROM = re.compile(r"^copy from (?P<path>.+)$")
_COPY_TO = re.compile(r"^copy to (?P<path>.+)$")
_BINARY_DIFF = re.compile(r"^Binary files (?P<left>\S+) and (?P<right>\S+) differ$")


class DiffParseResult(NamedTuple):
    touched_paths: tuple[str, ...]
    is_valid: bool
    error_message: str | None


def _invalid(message: str) -> DiffParseResult:
    return DiffParseResult((), False, message)


def _clean_diff_path(raw_path: str) -> str | None:
    """Normalize a single Git path while preserving fail-closed path rules."""
    p = raw_path.strip()
    if len(p) >= 2 and p[0] == p[-1] and p[0] in {'"', "'"}:
        parsed = shlex.split(p, posix=True)
        if len(parsed) != 1:
            raise SecurityPathViolationError("quoted diff path is malformed")
        p = parsed[0]
    if p in ("dev/null", "/dev/null", ""):
        return None
    if p.startswith(("a/", "b/")):
        p = p[2:]
    validate_path_security(p)
    return p


def _diff_git_paths(line: str) -> tuple[str | None, str | None] | None:
    try:
        parts = shlex.split(line, posix=True)
    except ValueError:
        return None
    if len(parts) != 4 or parts[:2] != ["diff", "--git"]:
        return None
    return _clean_diff_path(parts[2]), _clean_diff_path(parts[3])


def parse_unified_diff(patch_text: object) -> DiffParseResult:
    """Parse a Git unified diff and reject malformed or truncated hunks."""
    wrapped_value = getattr(patch_text, "value", None)
    if type(patch_text) is str:
        text = patch_text
    elif type(wrapped_value) is str:
        text = cast(str, wrapped_value)
    else:
        return _invalid("Patch text must be an exact string or PatchText value")
    if not text.strip():
        return _invalid("Patch text is empty or whitespace-only")

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()

    touched_paths: set[str] = set()
    found_diff = False
    current_left: str | None = None
    current_right: str | None = None
    section_open = False
    section_has_change = False
    old_header_seen = False
    new_header_seen = False
    old_remaining = 0
    new_remaining = 0
    in_hunk = False
    allow_no_newline_marker = False

    def finish_section() -> DiffParseResult | None:
        if section_open and not section_has_change:
            return _invalid(
                "Diff section contains no patch, rename, copy, mode, or binary change"
            )
        return None

    try:
        for line in lines:
            if in_hunk:
                if line == r"\ No newline at end of file":
                    if not allow_no_newline_marker:
                        return _invalid("Misplaced no-newline marker in hunk")
                    allow_no_newline_marker = False
                    continue
                if not line:
                    return _invalid(
                        "Truncated hunk before declared line counts were satisfied"
                    )
                prefix = line[0]
                old_delta = 1 if prefix in (" ", "-") else 0
                new_delta = 1 if prefix in (" ", "+") else 0
                if prefix not in (" ", "-", "+"):
                    return _invalid(f"Invalid hunk line prefix in diff: {line!r}")
                if old_delta > old_remaining or new_delta > new_remaining:
                    return _invalid("Hunk body exceeds its declared line counts")
                old_remaining -= old_delta
                new_remaining -= new_delta
                allow_no_newline_marker = True
                section_has_change = True
                if old_remaining == 0 and new_remaining == 0:
                    in_hunk = False
                continue

            if line == r"\ No newline at end of file":
                if not allow_no_newline_marker:
                    return _invalid("Misplaced no-newline marker outside a hunk")
                allow_no_newline_marker = False
                continue
            allow_no_newline_marker = False

            if line.startswith("diff --git "):
                unfinished = finish_section()
                if unfinished is not None:
                    return unfinished
                parsed_paths = _diff_git_paths(line)
                if parsed_paths is None:
                    return _invalid(f"Malformed diff --git line: {line!r}")
                current_left, current_right = parsed_paths
                for path in parsed_paths:
                    if path is not None:
                        touched_paths.add(path)
                found_diff = True
                section_open = True
                section_has_change = False
                old_header_seen = False
                new_header_seen = False
                continue

            if line.startswith("--- "):
                # A complete header pair already stands open, so this `--- `
                # opens the *next* file of a plain unified diff. `diff --git` is
                # the only other place a section begins and it finishes the
                # previous one itself; this branch did not, so the outgoing
                # section was never checked for a change and its
                # `section_has_change` survived into the incoming one. One
                # patched file followed by a header-only file was therefore
                # accepted on the strength of the first file's hunk, and both
                # paths were reported as touched.
                if section_open and old_header_seen and new_header_seen:
                    unfinished = finish_section()
                    if unfinished is not None:
                        return unfinished
                    section_has_change = False
                    current_left = None
                    current_right = None
                    old_header_seen = False
                    new_header_seen = False
                if old_header_seen and not new_header_seen:
                    return _invalid(
                        "Repeated old-file header without a new-file header"
                    )
                raw = line[4:].strip().split("\t", 1)[0]
                old_path = _clean_diff_path(raw)
                # `current_left` is set only by the `diff --git` branch, so it is
                # None throughout a plain unified diff -- the kind `diff -u`
                # produces and git accepts. Without the None guard the second
                # `--- ` of such a patch compared a real path against None and
                # refused, naming `diff --git` as the thing it disagreed with
                # when no such line was in the input. The first file escaped only
                # because `section_open` was still False.
                #
                # The `+++ ` branch below has always had this guard. The
                # asymmetry was the whole defect.
                if (
                    section_open
                    and current_left is not None
                    and old_path is not None
                    and old_path != current_left
                ):
                    return _invalid("Old-file header disagrees with diff --git path")
                if old_path is not None:
                    touched_paths.add(old_path)
                found_diff = True
                section_open = True
                old_header_seen = True
                new_header_seen = False
                continue

            if line.startswith("+++ "):
                if not old_header_seen or new_header_seen:
                    return _invalid(
                        "New-file header is missing or repeats its old-file header"
                    )
                raw = line[4:].strip().split("\t", 1)[0]
                new_path = _clean_diff_path(raw)
                if (
                    current_right is not None
                    and new_path is not None
                    and new_path != current_right
                ):
                    return _invalid("New-file header disagrees with diff --git path")
                if new_path is not None:
                    touched_paths.add(new_path)
                new_header_seen = True
                continue

            hunk_match = _HUNK_HEADER.fullmatch(line)
            if hunk_match is not None:
                if not old_header_seen or not new_header_seen:
                    return _invalid(
                        "Hunk appears before a complete old/new file header pair"
                    )
                old_remaining = int(hunk_match.group(2) or "1")
                new_remaining = int(hunk_match.group(4) or "1")
                if old_remaining == 0 and new_remaining == 0:
                    return _invalid("Hunk declares no old or new lines")
                in_hunk = True
                section_has_change = True
                continue
            if line.startswith("@@"):
                return _invalid(f"Malformed hunk header: {line!r}")

            rename_from = _RENAME_FROM.fullmatch(line)
            rename_to = _RENAME_TO.fullmatch(line)
            copy_from = _COPY_FROM.fullmatch(line)
            copy_to = _COPY_TO.fullmatch(line)
            path_match = rename_from or rename_to or copy_from or copy_to
            if path_match is not None:
                if not section_open:
                    return _invalid(
                        "Rename or copy metadata appears outside a diff section"
                    )
                path = _clean_diff_path(path_match.group("path"))
                if path is not None:
                    touched_paths.add(path)
                if rename_to is not None or copy_to is not None:
                    section_has_change = True
                continue

            binary_match = _BINARY_DIFF.fullmatch(line)
            if binary_match is not None:
                if not section_open:
                    return _invalid("Binary metadata appears outside a diff section")
                for name in ("left", "right"):
                    path = _clean_diff_path(binary_match.group(name))
                    if path is not None:
                        touched_paths.add(path)
                section_has_change = True
                continue

            if line == "GIT binary patch":
                return _invalid("GIT binary patch bodies are unsupported")
            if line.startswith(("new file mode ", "deleted file mode ", "new mode ")):
                if not section_open:
                    return _invalid("Mode metadata appears outside a diff section")
                section_has_change = True
                continue
            if line.startswith(
                ("index ", "old mode ", "similarity index ", "dissimilarity index ")
            ):
                if not section_open:
                    return _invalid("Diff metadata appears outside a diff section")
                continue
            return _invalid(f"Unrecognized line outside a hunk: {line!r}")
    except SecurityPathViolationError as exc:
        return _invalid(f"Unsafe diff path: {exc}")

    if in_hunk:
        return _invalid("Truncated hunk before declared line counts were satisfied")
    unfinished = finish_section()
    if unfinished is not None:
        return unfinished
    if not found_diff:
        return _invalid("No valid diff headers found in patch text")
    if not touched_paths:
        return _invalid("Patch text yielded zero touched paths")
    return DiffParseResult(tuple(sorted(touched_paths)), True, None)


def is_path_contained_in_root(path: str | Any, root: str | Any) -> bool:
    """Return whether a normalized path is within a normalized root boundary."""
    p = str(path).strip("/")
    r = str(root).strip("/")
    if not r:
        return True
    return p == r or p.startswith(r + "/")
