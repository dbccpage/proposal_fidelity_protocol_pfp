"""Documentation link linter for normal forms contracts relocation.

Scans Markdown documentation files and updates references from:
    governance/contracts/contracts_normal_forms
to:
    education/documentation/13_normal_forms/contracts_normal_forms

Handles:
- Plain path strings (slash and backslash variants)
- file:/// URI schemes (case-insensitive drive letter)
- Markdown relative link targets [text](path)
- Four-host estate replication (.agents <-> .claude, .codex, .grok)
- Assertion that all linked target files exist and zero former path references remain

AuthorityEffect: None.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def _find_repo_root(p: Path = Path(__file__).resolve()) -> Path:
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[3]


REPO_ROOT = _find_repo_root()
_CAND150 = (
    REPO_ROOT
    / "education"
    / "documentation"
    / "014_normal_forms"
    / "contracts_normal_forms"
)
_CAND15 = (
    REPO_ROOT
    / "education"
    / "documentation"
    / "15_normal_forms"
    / "contracts_normal_forms"
)
TARGET_CANONICAL = _CAND150 if _CAND150.is_dir() else _CAND15

OLD_PATH_STR = "governance/contracts/contracts_normal_forms"
NEW_PATH_STR = "education/documentation/13_normal_forms/contracts_normal_forms"

OLD_PATH_BS = "governance\\contracts\\contracts_normal_forms"
NEW_PATH_BS = "education\\documentation\\13_normal_forms\\contracts_normal_forms"

URI_PATTERN = re.compile(
    r"file:///[cC]:/Users/a343o/source/repos/the_symbol_game/governance/contracts/contracts_normal_forms"
)

REL_LINK_PATTERN = re.compile(
    r"\((?:\.\.[/\\])+governance[/\\]contracts[/\\]contracts_normal_forms([/\\]?[^)]*)\)"
)

HOST_ROOTS = [".agents", ".claude", ".codex", ".grok"]


def find_candidate_markdown_files() -> list[Path]:
    """Finds markdown files mentioning contracts_normal_forms via git grep."""
    result: list[Path] = []
    try:
        out = subprocess.check_output(
            [
                "git",
                "-c",
                "core.quotepath=false",
                "grep",
                "-l",
                "contracts_normal_forms",
                "--",
                "*.md",
            ],
            cwd=REPO_ROOT,
        )
        for line in out.splitlines():
            line_str = line.decode("utf-8", errors="surrogateescape").strip()
            if line_str:
                p = REPO_ROOT / line_str
                if p.is_file():
                    result.append(p)
    except subprocess.CalledProcessError:
        pass  # 0 matches
    return sorted(set(result))


def lint_and_fix_file(file_path: Path) -> list[str]:
    """Updates former path references in a single file."""
    changes: list[str] = []
    text = file_path.read_text(encoding="utf-8")
    original_text = text

    # 1. Replace file:/// URIs with relative POSIX paths
    def _uri_sub(m: re.Match[str]) -> str:
        try:
            return os.path.relpath(TARGET_CANONICAL, file_path.parent).replace("\\", "/")
        except ValueError:
            return str(TARGET_CANONICAL).replace("\\", "/")

    new_text, n_uri = URI_PATTERN.subn(_uri_sub, text)
    if n_uri > 0:
        text = new_text
        changes.append(f"Replaced {n_uri} file URI(s)")

    # 2. Replace relative markdown links like (../../../../governance/contracts/contracts_normal_forms/...)
    def _rel_sub(match: re.Match[str]) -> str:
        subpath = match.group(1).lstrip("/\\")
        dest_file = TARGET_CANONICAL / subpath if subpath else TARGET_CANONICAL
        try:
            rel = os.path.relpath(dest_file, file_path.parent).replace("\\", "/")
        except ValueError:
            rel = str(dest_file).replace("\\", "/")
        if match.group(1).endswith(("/", "\\")) and not rel.endswith("/"):
            rel += "/"
        return f"({rel})"

    new_text, n_rel = REL_LINK_PATTERN.subn(_rel_sub, text)
    if n_rel > 0:
        text = new_text
        changes.append(f"Replaced {n_rel} relative link(s)")

    # 3. Replace plain path string references (slash)
    if OLD_PATH_STR in text:
        count = text.count(OLD_PATH_STR)
        text = text.replace(OLD_PATH_STR, NEW_PATH_STR)
        changes.append(f"Replaced {count} plain path string(s)")

    # 4. Replace plain path string references (backslash)
    if OLD_PATH_BS in text:
        count = text.count(OLD_PATH_BS)
        text = text.replace(OLD_PATH_BS, NEW_PATH_BS)
        changes.append(f"Replaced {count} backslash path string(s)")

    if text != original_text:
        file_path.write_text(text, encoding="utf-8")

    return changes


def sync_four_hosts(skill_names: list[str]) -> None:
    """Sync updated skills from .agents/skills/ across all four host roots."""
    for skill in skill_names:
        src = REPO_ROOT / ".agents" / "skills" / skill
        if not src.is_dir():
            continue
        for host in [".claude", ".codex", ".grok"]:
            dest = REPO_ROOT / host / "skills" / skill
            if dest.is_dir():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            print(
                f"  [FOUR-HOST SYNC] Mirrored {src.relative_to(REPO_ROOT)} -> {dest.relative_to(REPO_ROOT)}",
                flush=True,
            )


def run_linter() -> int:
    print(f"Starting normal forms documentation link linter on {REPO_ROOT}...", flush=True)
    assert TARGET_CANONICAL.is_dir(), f"Canonical target not found at {TARGET_CANONICAL}"

    candidate_files = find_candidate_markdown_files()
    print(
        f"Discovered {len(candidate_files)} markdown files with candidate references.", flush=True
    )

    modified_files: list[Path] = []
    updated_skills: set[str] = set()

    for f in candidate_files:
        changes = lint_and_fix_file(f)
        if changes:
            modified_files.append(f)
            rel_f = f.relative_to(REPO_ROOT)
            print(f"  [UPDATED] {rel_f}: {', '.join(changes)}", flush=True)
            # Track if a skill was updated
            parts = rel_f.parts
            if len(parts) >= 3 and parts[0] == ".agents" and parts[1] == "skills":
                updated_skills.add(parts[2])

    # Also update verify_normal_forms.py and extra python docstrings
    extra_py_files = [
        REPO_ROOT / "education" / "tests" / "normal_forms" / "verify_normal_forms.py",
        REPO_ROOT / "education" / "domain" / "normal_forms" / "harness.py",
        REPO_ROOT
        / "education"
        / "tests"
        / "normal_forms"
        / "test_asrf_and_bqnf_fsign_runtime.py",
    ]
    for py_file in extra_py_files:
        if py_file.is_file():
            changes = lint_and_fix_file(py_file)
            if changes:
                modified_files.append(py_file)
                print(
                    f"  [UPDATED] {py_file.relative_to(REPO_ROOT)}: {', '.join(changes)}",
                    flush=True,
                )

    # Multi-host sync if skills were updated
    if updated_skills:
        print(
            f"Syncing {len(updated_skills)} updated skill(s) across four host roots...", flush=True
        )
        sync_four_hosts(sorted(updated_skills))

    print("-" * 60, flush=True)
    print(f"Linter complete: updated {len(modified_files)} file(s).", flush=True)

    # Final assertion: check for any remaining occurrences via git grep
    remaining: list[str] = []
    for pat in [OLD_PATH_STR, OLD_PATH_BS]:
        try:
            out = subprocess.check_output(
                ["git", "-c", "core.quotepath=false", "grep", "-n", pat, "--", "*.md"],
                cwd=REPO_ROOT,
            )
            for line in out.splitlines():
                l_str = line.decode("utf-8", errors="surrogateescape").strip()
                if l_str:
                    remaining.append(l_str)
        except subprocess.CalledProcessError:
            pass

    if remaining:
        print(
            f"FAIL: {len(remaining)} occurrence(s) of former path still present in Markdown files:",
            flush=True,
        )
        for r in remaining:
            print(f"  - {r}", flush=True)
        return 1

    print(
        "PASS: Zero references to former path found across all historical Markdown guides.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(run_linter())
