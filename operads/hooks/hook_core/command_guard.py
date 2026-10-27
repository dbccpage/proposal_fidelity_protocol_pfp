"""Lexical shell command parser and safety gatekeeper for Git and Pytest commands.

Enforces constitutional safety fences in AGENTS.md:
1. Strict branch push directive: blocks direct push to origin/main or origin/master,
   force refspecs (+src:dst), force flags, and blanket branch pushes.
2. Strict staging/commit hygiene: blocks blanket git add (. / * / -A / --all) and blanket commit (-a / --all).
3. PowerShell stash syntax: blocks unquoted stash@{N} to prevent shell syntax errors.
4. Strict test execution directive: blocks whole-suite pytest sweeps (bare pytest, pytest -q,
   pytest .) and enforces targeted execution of 1 to 3 files maximum.
5. Ignores inert echo/view commands and prevents commit message false positives.

AuthorityEffect: None.
"""

from __future__ import annotations

import os
import re
import shlex
from typing import List, Tuple

_INERT_EXECUTABLES = {
    "echo",
    "cat",
    "grep",
    "head",
    "tail",
    "type",
    "printf",
    "echo.",
    "more",
}

_CHAIN_SEPARATORS = {"&&", "||", ";", "|", "&"}

_UNQUOTED_STASH_RE = re.compile(
    r"(?<!['\"])stash@\{[0-9]+\}(?!['\"])",
    re.IGNORECASE,
)

_GIT_GLOBAL_OPTS_WITH_ARGS = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--exec-path",
    "--config-env",
}


#: The rule each refusal enforces (operads/rules/git/rl_hook_command_and_file_fences.md).
RULE_PUSH = "RULE_GIT_NO_FORCE_OR_MAIN_PUSH_001"
RULE_STAGING = "RULE_GIT_EXPLICIT_STAGING_001"
RULE_COMMIT = "RULE_GIT_NO_COMMIT_ALL_001"
RULE_PYTEST = "RULE_PYTEST_TARGETED_RUNS_001"
RULE_QUOTED_STASH = "RULE_SHELL_QUOTED_STASH_REF_001"


def _split_into_commands(tokens: List[str]) -> List[List[str]]:
    """Split token stream on shell operators (&&, ||, ;, |, &)."""
    commands: List[List[str]] = []
    current: List[str] = []
    for token in tokens:
        if token in _CHAIN_SEPARATORS:
            if current:
                commands.append(current)
                current = []
        else:
            current.append(token)
    if current:
        commands.append(current)
    return commands


def _normalize_exe(token: str) -> str:
    """Extract lowercase base name of an executable."""
    cleaned = token.strip("\"' ")
    base = os.path.basename(cleaned).lower()
    if base.endswith(".exe"):
        base = base[:-4]
    return base


def _inspect_git_push(args: List[str]) -> Tuple[bool, str]:
    """Inspect arguments to `git push`."""
    if not args:
        return (
            False,
            "Bare `git push` without explicit destination or branch is forbidden by AGENTS.md.",
        )

    for token in args:
        # Force flags
        if token in ("--force", "-f", "--force-with-lease", "--force-if-includes", "--mirror"):
            return (
                False,
                "Force-pushing (`git push -f` / `--force` / `--force-with-lease`) is strictly forbidden by AGENTS.md.",
            )
        if token.startswith("--force-with-lease=") or token.startswith("--force-if-includes="):
            return (
                False,
                "Force-pushing (`git push -f` / `--force` / `--force-with-lease`) is strictly forbidden by AGENTS.md.",
            )
        # Blanket push
        if token in ("--all", "-all"):
            return (
                False,
                "Pushing all branches (`git push --all`) is forbidden by AGENTS.md. Push explicit feature branch.",
            )
        # Force refspec (+src:dst)
        if token.startswith("+") and len(token) > 1 and not token.startswith("++"):
            return False, f"Force-push refspec (`{token}`) is strictly forbidden by AGENTS.md."

        # Main / Master branch targets
        lower = token.lower()
        if lower in ("main", "master", "refs/heads/main", "refs/heads/master"):
            return (
                False,
                "Pushing directly to origin/main or origin/master is strictly forbidden by AGENTS.md. Create a PR instead.",
            )
        if lower.startswith("origin/main") or lower.startswith("origin/master"):
            return (
                False,
                "Pushing directly to origin/main or origin/master is strictly forbidden by AGENTS.md. Create a PR instead.",
            )
        if (
            lower.endswith(":main")
            or lower.endswith(":master")
            or lower.endswith(":refs/heads/main")
            or lower.endswith(":refs/heads/master")
        ):
            return (
                False,
                "Pushing directly to main or master branch refspecs is strictly forbidden by AGENTS.md. Create a PR instead.",
            )

    return True, ""


def _inspect_git_add(args: List[str]) -> Tuple[bool, str]:
    """Inspect arguments to `git add`."""
    i = 0
    in_pathspecs = False
    while i < len(args):
        token = args[i]
        if token == "--":
            in_pathspecs = True
            i += 1
            continue

        if not in_pathspecs and token.startswith("-"):
            if token in ("-A", "--all"):
                return (
                    False,
                    "Unbounded git staging (`git add -A` / `--all`) is forbidden. Stage explicit files.",
                )
            i += 1
            continue

        if token in (".", "*", "-A", "--all", r":\ ", ":/", ":"):
            return (
                False,
                "Unbounded git staging (`git add .`, `git add -A`, `git add *`) is forbidden. Stage explicit files.",
            )
        i += 1

    return True, ""


def _inspect_git_commit(args: List[str]) -> Tuple[bool, str]:
    """Inspect arguments to `git commit`."""
    i = 0
    while i < len(args):
        token = args[i]
        if token == "--all":
            return (
                False,
                "Unbounded commit (`git commit --all`) is forbidden. Stage explicit files.",
            )

        if token in ("-m", "-F", "-C", "-c"):
            # Next token is message/file; skip it so its content isn't mistaken for flags
            i += 2
            continue

        if token.startswith("-") and not token.startswith("--"):
            # Check for flag clustering containing 'a', e.g. -a, -am, -ma, -vam, etc.
            if token in ("-ma", "-am") or set(token[1:]).issubset(
                {"a", "m", "v", "q", "s", "e", "n"}
            ):
                if "a" in token[1:]:
                    return (
                        False,
                        "Unbounded commit (`git commit -a` / `-am`) is forbidden. Stage explicit files.",
                    )
                if "m" in token[1:]:
                    # Clustered flag ending with m takes next argument as message
                    i += 2
                    continue
            elif "a" in token[1:]:
                # If 'a' appears before 'm', it's definitely a flag
                m_pos = token.find("m")
                a_pos = token.find("a")
                if m_pos == -1 or a_pos < m_pos:
                    return (
                        False,
                        "Unbounded commit (`git commit -a` / `-am`) is forbidden. Stage explicit files.",
                    )

        i += 1

    return True, ""


def _inspect_pytest(args: List[str]) -> Tuple[bool, str]:
    """Inspect arguments to `pytest`."""
    opts_with_arg = {
        "-k",
        "-m",
        "-o",
        "-c",
        "-p",
        "--override-ini",
        "--rootdir",
        "--import-mode",
        "--basetemp",
        "--log-level",
    }
    targets: List[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in opts_with_arg:
            i += 2
            continue
        if token.startswith("-"):
            i += 1
            continue
        targets.append(token)
        i += 1

    if not targets:
        return (
            False,
            "Whole-suite pytest sweeps across repo root are forbidden by AGENTS.md. Run targeted test files (1-3 files max).",
        )

    # Normalize targets
    normalized_targets: List[str] = []
    for target in targets:
        norm = target.replace("\\", "/")
        while norm.startswith("./"):
            norm = norm[2:]
        if norm in (".", "", "/"):
            return (
                False,
                "Whole-suite pytest sweeps across repo root are forbidden by AGENTS.md. Run targeted test files (1-3 files max).",
            )
        normalized_targets.append(norm)

    if len(normalized_targets) > 3:
        return (
            False,
            f"Too many test targets ({len(normalized_targets)} > 3). AGENTS.md mandates 1-3 targeted test files maximum.",
        )

    return True, ""


def evaluate_command(command: str) -> Tuple[bool, str]:
    """Check command against repository safety fences."""
    cmd_text = command.strip()
    if not cmd_text:
        return True, ""

    # Check unquoted PowerShell stash syntax first across the raw command string
    if _UNQUOTED_STASH_RE.search(cmd_text):
        return (
            False,
            f"[{RULE_QUOTED_STASH}] "
            "Unquoted PowerShell stash syntax (`stash@{N}`) causes shell evaluation errors. Enclose in quotes, e.g. 'stash@{0}'.",
        )

    # Parse tokens using shlex
    try:
        tokens = shlex.split(cmd_text, posix=True)
    except ValueError:
        tokens = cmd_text.split()

    if not tokens:
        return True, ""

    sub_commands = _split_into_commands(tokens)

    for sub_cmd in sub_commands:
        if not sub_cmd:
            continue

        exe = _normalize_exe(sub_cmd[0])

        # Ignore inert viewing / echo commands
        if exe in _INERT_EXECUTABLES:
            continue

        # 1. Git command evaluation
        if exe == "git":
            args = sub_cmd[1:]
            i = 0
            while i < len(args):
                token = args[i]
                if token in _GIT_GLOBAL_OPTS_WITH_ARGS:
                    i += 2
                    continue
                if any(token.startswith(f"{opt}=") for opt in _GIT_GLOBAL_OPTS_WITH_ARGS):
                    i += 1
                    continue
                if token.startswith("-"):
                    i += 1
                    continue
                subcommand = token.lower()
                git_args = args[i + 1 :]
                if subcommand == "push":
                    allowed, reason = _inspect_git_push(git_args)
                    if not allowed:
                        return False, f"[{RULE_PUSH}] {reason}"
                elif subcommand == "add":
                    allowed, reason = _inspect_git_add(git_args)
                    if not allowed:
                        return False, f"[{RULE_STAGING}] {reason}"
                elif subcommand == "commit":
                    allowed, reason = _inspect_git_commit(git_args)
                    if not allowed:
                        return False, f"[{RULE_COMMIT}] {reason}"
                break
            continue

        # 2. Pytest command evaluation (pytest / python -m pytest / py -3.12 -m pytest)
        if exe == "pytest":
            allowed, reason = _inspect_pytest(sub_cmd[1:])
            if not allowed:
                return False, f"[{RULE_PYTEST}] {reason}"
            continue

        if exe in ("python", "python3", "py"):
            args = sub_cmd[1:]
            for idx, token in enumerate(args):
                if token == "-m" and idx + 1 < len(args) and args[idx + 1].lower() == "pytest":
                    allowed, reason = _inspect_pytest(args[idx + 2 :])
                    if not allowed:
                        return False, f"[{RULE_PYTEST}] {reason}"
                    break

    return True, ""
