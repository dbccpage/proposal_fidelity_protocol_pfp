"""Shared fixtures for autopoiesis learning loop tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from omega_engine_operads.infrastructure.autopoiesis.git_learning import command
from omega_engine_operads.infrastructure.autopoiesis.learning_store import (
    LearningStore,
)


@pytest.fixture
def store(tmp_path: Path) -> LearningStore:
    return LearningStore(tmp_path / "store")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    remote = tmp_path / "remote.git"
    remote.mkdir()
    command(remote, "git", "init", "--bare", "-b", "main")
    root = tmp_path / "source"
    root.mkdir()
    command(root, "git", "init", "-b", "main")
    command(root, "git", "config", "user.email", "test@example.invalid")
    command(root, "git", "config", "user.name", "Test")
    (root / "gate.py").write_text(
        "import sys\nprint('PASS' if sys.argv[1] != 'missing' else 'PASS')\n", encoding="utf-8"
    )
    for host in ("omega_engine_operads", ".agents", ".claude", ".codex", ".grok"):
        path = root / host / "skills" / "fixture"
        path.mkdir(parents=True)
        (path / "SKILL.md").write_text("---\nname: fixture\n---\nFixture", encoding="utf-8")
    command(
        root,
        "git",
        "add",
        "--",
        "gate.py",
        "omega_engine_operads/skills/fixture/SKILL.md",
        ".agents/skills/fixture/SKILL.md",
        ".claude/skills/fixture/SKILL.md",
        ".codex/skills/fixture/SKILL.md",
        ".grok/skills/fixture/SKILL.md",
    )
    command(root, "git", "commit", "-m", "baseline")
    command(root, "git", "remote", "add", "origin", str(remote))
    command(root, "git", "push", "-u", "origin", "main")
    return root
