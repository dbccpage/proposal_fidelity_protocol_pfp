"""Swarm automation git hygiene policy (STORY-031-004).

Structural argv parse: consume legal global Git options before evaluating the
subcommand so `git --no-pager add -A` cannot bypass.
AuthorityEffect: None.
"""

from __future__ import annotations

import shlex
from collections.abc import Sequence
from dataclasses import dataclass

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


@dataclass(frozen=True)
class PolicyResult:
    ok: bool
    residual: str | None


def _tokenize(cmd: str | Sequence[str]) -> list[str]:
    if isinstance(cmd, (list, tuple)):
        return [str(x) for x in cmd]
    try:
        return shlex.split(str(cmd), posix=True)
    except ValueError:
        return str(cmd).split()


def _is_git_head(token: str) -> bool:
    t = token.lower().replace("\\", "/")
    return t == "git" or t.endswith(("/git", "git.exe"))


def _core_after_globals(tokens: list[str]) -> list[str] | None:
    if not tokens or not _is_git_head(tokens[0]):
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


def check_command(cmd: str | Sequence[str]) -> PolicyResult:
    tokens = _tokenize(cmd)
    core = _core_after_globals(tokens)
    if core is None:
        # Not a git command â€” out of scope for this policy
        return PolicyResult(ok=True, residual=None)
    if not core:
        return PolicyResult(ok=True, residual=None)

    sub = core[0]
    rest = core[1:]

    if sub == "worktree" and rest and rest[0] == "remove":
        if "--force" in rest or "-f" in rest:
            return PolicyResult(
                ok=False, residual="FORCE_WORKTREE_REMOVE_FORBIDDEN_DEFAULT"
            )
        return PolicyResult(ok=True, residual=None)

    if sub == "add":
        if "--" in rest:
            idx = rest.index("--")
            opts = rest[:idx]
            paths = rest[idx + 1 :]
            broad_opts = {"-A", "--all", "-u", "."}
            if any(o in broad_opts for o in opts):
                return PolicyResult(ok=False, residual="BROAD_STAGING_FORBIDDEN")
            if not paths:
                return PolicyResult(ok=False, residual="BROAD_STAGING_FORBIDDEN")
            return PolicyResult(ok=True, residual=None)
        # No pathspec delimiter â†’ fail closed (includes add -A / add . / add -u)
        return PolicyResult(ok=False, residual="BROAD_STAGING_FORBIDDEN")

    return PolicyResult(ok=True, residual=None)
