"""Non-force disposal: ancestor OR typed cherry receipt (STORY-031-003).

Arbitrary nonempty text is not patch-equivalence. Patch-eq requires a typed
subprocess receipt (exit, argv, stdout, candidate/main SHAs) with git-cherry
line grammar.
AuthorityEffect: None.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

from .cherry_receipt import CherryReceipt
from .disposal_decision import DisposalDecision

_CHERRY_LINE = re.compile(r"^[+-] [0-9a-fA-F]{7,40}(?:\s|$)")

_GIT_GLOBAL_VALUE = frozenset(
    {
        "-C",
        "-c",
        "--git-dir",
        "--work-tree",
        "--namespace",
        "--config-env",
        "--super-prefix",
        "--list-cmds",
    }
)
_GIT_GLOBAL_FLAGS = frozenset(
    {
        "--no-pager",
        "--paginate",
        "--no-replace-objects",
        "--bare",
        "--literal-pathspecs",
        "--glob-pathspecs",
        "--noglob-pathspecs",
        "--icase-pathspecs",
        "--no-optional-locks",
        "-p",
        "-P",
    }
)


def _core_after_globals(argv: Sequence[str]) -> list[str] | None:
    if not argv:
        return None
    tokens = list(argv)
    head = tokens[0].lower().replace("\\", "/")
    if not (head == "git" or head.endswith(("/git", "git.exe"))):
        return None
    i = 1
    n = len(tokens)
    while i < n:
        t = tokens[i]
        if t in _GIT_GLOBAL_FLAGS:
            i += 1
            continue
        if t in _GIT_GLOBAL_VALUE:
            i += 2
            continue
        if t.startswith(("--git-dir=", "--work-tree=", "--namespace=")):
            i += 1
            continue
        if t.startswith("-c") and "=" in t and t != "-c":
            i += 1
            continue
        break
    return tokens[i:]


def validate_cherry_receipt(receipt: CherryReceipt) -> str | None:
    """Return residual code if receipt is not valid measured cherry evidence."""
    if receipt.exit_status != 0:
        return "CHERRY_NONZERO_EXIT"
    if not receipt.candidate_sha or not receipt.main_sha:
        return "CHERRY_MISSING_SHA"
    if len(receipt.candidate_sha) < 7 or len(receipt.main_sha) < 7:
        return "CHERRY_SHA_TOO_SHORT"

    core = _core_after_globals(receipt.argv)
    if core is None:
        return "CHERRY_ARGV_NOT_GIT"
    if not core or core[0] != "cherry":
        return "CHERRY_ARGV_NOT_CHERRY"
    rest = core[1:]
    if rest and rest[0] in ("-v", "--verbose"):
        rest = rest[1:]
    if len(rest) < 2:
        return "CHERRY_ARGV_MISSING_SHAS"
    upstream, head = rest[0], rest[1]
    if upstream != receipt.main_sha or head != receipt.candidate_sha:
        return "CHERRY_ARGV_SHA_MISMATCH"

    lines = [ln for ln in receipt.stdout_lines if ln.strip() != ""]
    if not lines:
        return "CHERRY_EMPTY_STDOUT"
    for ln in lines:
        if not _CHERRY_LINE.match(ln):
            return "CHERRY_MALFORMED_LINE"
    return None


def can_dispose(
    *,
    is_ancestor_of_main: bool,
    cherry_receipt: CherryReceipt | None = None,
    force: bool = False,
    cherry_lines: Sequence[str] | None = None,
) -> DisposalDecision:
    """Default path never uses force."""
    if cherry_lines is not None and cherry_receipt is None:
        if force:
            return DisposalDecision(
                may_dispose=True,
                residual="FORCE_USED_HUMAN_ONLY",
                used_force=True,
                proof=None,
            )
        return DisposalDecision(
            may_dispose=False,
            residual="DISPOSAL_BLOCKED_UNTYPED_LINES",
            used_force=False,
            proof=None,
        )

    if is_ancestor_of_main:
        return DisposalDecision(
            may_dispose=True, residual=None, used_force=False, proof="ancestor"
        )

    if cherry_receipt is None:
        if force:
            return DisposalDecision(
                may_dispose=True,
                residual="FORCE_USED_HUMAN_ONLY",
                used_force=True,
                proof=None,
            )
        return DisposalDecision(
            may_dispose=False,
            residual="DISPOSAL_BLOCKED_NO_EVIDENCE",
            used_force=False,
            proof=None,
        )

    residual = validate_cherry_receipt(cherry_receipt)
    if residual is not None:
        if force:
            return DisposalDecision(
                may_dispose=True,
                residual="FORCE_USED_HUMAN_ONLY",
                used_force=True,
                proof=None,
            )
        return DisposalDecision(
            may_dispose=False,
            residual=residual,
            used_force=False,
            proof=None,
        )

    lines = [ln for ln in cherry_receipt.stdout_lines if ln.strip() != ""]
    has_unique = any(ln.startswith("+") for ln in lines)
    if has_unique:
        if force:
            return DisposalDecision(
                may_dispose=True,
                residual="FORCE_USED_HUMAN_ONLY",
                used_force=True,
                proof=None,
            )
        return DisposalDecision(
            may_dispose=False,
            residual="DISPOSAL_BLOCKED",
            used_force=False,
            proof=None,
        )
    return DisposalDecision(
        may_dispose=True,
        residual=None,
        used_force=False,
        proof="patch_equivalence",
    )
