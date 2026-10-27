"""Archiving must be reversible, refused without authorisation, and all-four-hosts.

The estate's parity gate exists because "adding a skill and forgetting three
mirrors is the single most common way this estate breaks itself". Removing one
has the same shape, and `sync_cross_host_skills` never deletes -- so an archive
that touches canon alone leaves `--check` red with no way to satisfy it except
undoing the move.

AuthorityEffect: None.

Two of these tests shell out to `git`. They build a throwaway repository in
`tmp_path` rather than touching the checkout.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from operads.infrastructure.skill_garden import archive_lane as lane
from operads.infrastructure.skill_garden.usage_ledger import (
    repo_root_from,
)

SKILL_BODY = """---
name: {name}
description: "A disposable package used to prove the archive lane round-trips."
operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# {name}

## When to use

Never.
"""

MANIFEST = """# Planned archive

approved_by: a-human
approved_at: 2026-08-31

## Nominated

| skill | last used | created |
| --- | --- | --- |
| `{name}` | never | 2026-01-01 |
"""


_HOOK_GIT_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
)


def _clean_git_env(root: Path) -> dict[str, str]:
    """Drop repository coordinates exported to Git hooks."""
    env = {key: value for key, value in os.environ.items() if key not in _HOOK_GIT_VARS}
    env["GIT_CONFIG_GLOBAL"] = str(root / ".gitconfig-none")
    return env


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git against the throwaway repo, and only against it.

    `-c` supplies identity per invocation instead of `git config`, which writes
    a file. An earlier version of this fixture called
    `git config user.email ...`; that write escaped `tmp_path` and landed in the
    real repository's shared `.git/config`. A test may not mutate the checkout
    it is run from.

    `--git-dir` and `--work-tree` are pinned explicitly so no discovery walk can
    reach a repository above `tmp_path` even if `git init` here fails.
    """
    return subprocess.run(
        [
            "git",
            "--git-dir",
            str(root / ".git"),
            "--work-tree",
            str(root),
            "-c",
            "user.email=t@example.invalid",
            "-c",
            "user.name=test",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        env=_clean_git_env(root),
    )


@pytest.fixture()
def garden(tmp_path: Path) -> Path:
    """A four-host garden in a real git repository."""
    root = tmp_path
    subprocess.run(
        ["git", "init", "-q", str(root)],
        capture_output=True,
        text=True,
        check=True,
        env=_clean_git_env(root),
    )
    (root / ".agents").mkdir()

    for host in (".agents", *lane.MIRRORS):
        for name in ("keeper", "goner"):
            package = root / host / "skills" / name
            package.mkdir(parents=True)
            (package / "SKILL.md").write_text(
                SKILL_BODY.format(name=name), encoding="utf-8", newline="\n"
            )
    (root / "planned_archive.md").write_text(
        MANIFEST.format(name="goner"), encoding="utf-8", newline="\n"
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "seed")
    return root


def _present(root: Path, name: str) -> dict[str, bool]:
    return {
        "canon": (root / lane.CANON / name).is_dir(),
        "archive": (root / lane.ARCHIVE / name).is_dir(),
        **{host: (root / host / "skills" / name).is_dir() for host in lane.MIRRORS},
    }


# --------------------------------------------------------------------------
# Authorisation
# --------------------------------------------------------------------------


def test_no_manifest_refuses(garden: Path) -> None:
    with pytest.raises(lane.ArchiveRefusal, match="no manifest"):
        lane.archive_skills(garden, ["goner"], manifest_path=garden / "absent.md", apply=True)


def test_an_unsigned_manifest_refuses(garden: Path) -> None:
    """A proposal is not an authorisation.

    Mutation: accept a manifest without `approved_by` and the human is out of
    the loop entirely.
    """
    unsigned = garden / "unsigned.md"
    unsigned.write_text(
        MANIFEST.format(name="goner").replace("approved_by: a-human", "approved_by:"),
        encoding="utf-8",
    )
    with pytest.raises(lane.ArchiveRefusal, match="approved_by"):
        lane.archive_skills(garden, ["goner"], manifest_path=unsigned, apply=True)


def test_a_package_outside_the_manifest_refuses(garden: Path) -> None:
    """The manifest is the authorisation; anything else has none."""
    with pytest.raises(lane.ArchiveRefusal, match="not in the approved manifest"):
        lane.archive_skills(
            garden, ["keeper"], manifest_path=garden / "planned_archive.md", apply=True
        )


def test_an_absent_package_refuses(garden: Path) -> None:
    manifest = garden / "ghost.md"
    manifest.write_text(MANIFEST.format(name="ghost"), encoding="utf-8")
    with pytest.raises(lane.ArchiveRefusal, match="not present in the garden"):
        lane.archive_skills(garden, ["ghost"], manifest_path=manifest, apply=True)


def test_a_dry_run_moves_nothing(garden: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lane, "parity_is_green", lambda _root: True)
    result = lane.archive_skills(
        garden, ["goner"], manifest_path=garden / "planned_archive.md", apply=False
    )
    assert result["applied"] is False
    assert _present(garden, "goner")["canon"] is True


# --------------------------------------------------------------------------
# The round trip
# --------------------------------------------------------------------------


@pytest.fixture()
def archived(garden: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(lane, "parity_is_green", lambda _root: True)
    monkeypatch.setattr(lane, "regenerate_derived_surfaces", lambda _root: ["skipped"])
    lane.archive_skills(garden, ["goner"], manifest_path=garden / "planned_archive.md", apply=True)
    return garden


def test_archiving_leaves_the_package_in_exactly_one_place(archived: Path) -> None:
    """Canon keeps the bytes; every mirror loses the package.

    Mutation: skip the mirror removal and `find_destination_only_packages`
    fails `--check` -- a mirror may not hold a package canon has never declared.
    """
    where = _present(archived, "goner")
    assert where["archive"] is True
    assert where["canon"] is False
    assert not any(where[host] for host in lane.MIRRORS)


def test_the_untouched_package_is_untouched(archived: Path) -> None:
    where = _present(archived, "keeper")
    assert where["canon"] is True
    assert all(where[host] for host in lane.MIRRORS)


def test_an_archived_package_is_invisible_to_the_garden_glob(archived: Path) -> None:
    """The property the whole lane exists for.

    `.agents/archive/` sits structurally outside `<host>/skills`, so no scanner
    that walks the garden can reach it.
    """
    found = {path.parent.name for path in (archived / lane.CANON).glob("*/SKILL.md")}
    assert found == {"keeper"}


def test_the_receipt_records_what_a_restore_needs(archived: Path) -> None:
    receipt = json.loads(
        (archived / lane.ARCHIVE / "goner" / lane.RECEIPT_NAME).read_text(encoding="utf-8")
    )
    assert receipt["skill_id"] == "goner"
    assert receipt["approved_by"] == "a-human"
    assert receipt["authority_effect"] == "None"
    assert len(receipt["package_sha256"]) == 64
    assert "restore" in receipt["restore_command"]


def test_restoring_puts_it_back(archived: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lane, "regenerate_derived_surfaces", lambda _root: ["skipped"])
    monkeypatch.setattr(lane, "parity_is_green", lambda _root: True)
    lane.restore_skills(archived, ["goner"], apply=True)
    where = _present(archived, "goner")
    assert where["canon"] is True and where["archive"] is False
    assert (archived / lane.CANON / "goner" / "SKILL.md").is_file()
    assert not (archived / lane.CANON / "goner" / lane.RECEIPT_NAME).exists()


def test_restoring_something_that_is_not_archived_refuses(garden: Path) -> None:
    with pytest.raises(lane.ArchiveRefusal, match="not in the archive"):
        lane.restore_skills(garden, ["keeper"], apply=True)


def test_restoring_over_a_live_package_refuses(archived: Path) -> None:
    """Two copies of one package is worse than none."""
    (archived / lane.CANON / "goner").mkdir(parents=True)
    with pytest.raises(lane.ArchiveRefusal, match="already exists"):
        lane.restore_skills(archived, ["goner"], apply=True)


# --------------------------------------------------------------------------
# Dormant tampering
# --------------------------------------------------------------------------


def test_verify_notices_bytes_edited_while_archived(archived: Path) -> None:
    """The reason the receipt records a tree hash at all.

    Mutation: drop `package_sha256` and an archived package could be edited for
    months and restored as though it were the original.
    """
    assert lane.verify_archive(archived) == []
    target = archived / lane.ARCHIVE / "goner" / "SKILL.md"
    target.write_text(target.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
    findings = lane.verify_archive(archived)
    assert findings and "changed while archived" in findings[0]


def test_verify_reports_a_package_with_no_receipt(archived: Path) -> None:
    (archived / lane.ARCHIVE / "goner" / lane.RECEIPT_NAME).unlink()
    findings = lane.verify_archive(archived)
    assert findings and "no ARCHIVE_RECEIPT.json" in findings[0]


# --------------------------------------------------------------------------
# The live repository
# --------------------------------------------------------------------------



def test_the_live_archive_verifies() -> None:
    root = repo_root_from(Path(__file__).resolve())
    assert lane.verify_archive(root) == []


def test_the_fixture_does_not_write_to_the_real_repository_config(
    tmp_path: Path,
) -> None:
    """A test may not mutate the checkout it is run from.

    An earlier version of `_git` called `git config user.email ...` inside
    `tmp_path`. That write escaped and landed in the real repository's shared
    `.git/config`, adding a `[user]` section naming a fake author. Nothing
    caught it; it was found by hand afterwards, when `git status` began
    refusing.

    Mutation: drop the `-c` / `--git-dir` pinning from `_git` and this fails.
    """
    import hashlib

    root = repo_root_from(Path(__file__).resolve())
    shared_config = root / ".git"
    if shared_config.is_file():  # linked worktree: follow the gitdir pointer
        pointer = shared_config.read_text(encoding="utf-8").strip()
        shared_config = Path(pointer.split("gitdir:", 1)[-1].strip())
    common = shared_config / "commondir"
    if common.is_file():
        shared_config = (shared_config / common.read_text(encoding="utf-8").strip()).resolve()
    config_file = shared_config / "config"
    if not config_file.is_file():  # pragma: no cover - unusual layout
        pytest.skip("cannot locate the shared git config")

    before = hashlib.sha256(config_file.read_bytes()).hexdigest()

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    subprocess.run(
        ["git", "init", "-q", str(scratch)],
        capture_output=True,
        text=True,
        check=True,
        env=_clean_git_env(scratch),
    )
    (scratch / "f.txt").write_text("x", encoding="utf-8")
    _git(scratch, "add", "-A")
    _git(scratch, "commit", "-q", "-m", "scratch")

    after = hashlib.sha256(config_file.read_bytes()).hexdigest()
    assert before == after, (
        f"a test git invocation modified the real repository's shared config at {config_file}"
    )


def test_throwaway_init_refuses_hook_parent_coordinates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hook-exported GIT_DIR may not capture a throwaway repository init."""
    parent = tmp_path / "parent"
    child = tmp_path / "child"
    subprocess.run(
        ["git", "init", "-q", str(parent)],
        capture_output=True,
        text=True,
        check=True,
        env=_clean_git_env(parent),
    )
    parent_config = parent / ".git" / "config"
    before = parent_config.read_bytes()

    monkeypatch.setenv("GIT_DIR", str(parent / ".git"))
    monkeypatch.delenv("GIT_WORK_TREE", raising=False)
    subprocess.run(
        ["git", "init", "-q", str(child)],
        capture_output=True,
        text=True,
        check=True,
        env=_clean_git_env(child),
    )

    assert (child / ".git").is_dir()
    assert parent_config.read_bytes() == before
