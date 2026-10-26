"""A throwaway git repository with a governance policy, for the tool tests.

AuthorityEffect: None.
Contract: urn:pfp-governance:tests:conftest:v1
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from governance.tools.tests.helpers import git

REAL_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repo holding the real policy, an empty baseline and one governed source."""
    (tmp_path / "governance").mkdir()
    shutil.copy(REAL_ROOT / "governance" / "policy.json", tmp_path / "governance" / "policy.json")
    (tmp_path / "governance" / "baseline.json").write_text(
        json.dumps(
            {
                "schema_version": "pfp.governance-baseline.v1",
                "AuthorityEffect": "None",
                "rule": "r",
                "entries": {},
            }
        ),
        encoding="utf-8",
    )
    source = tmp_path / "pfp_lab" / "mod.py"
    source.parent.mkdir()
    source.write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "pfp_lab" / "tests").mkdir()
    (tmp_path / "pfp_lab" / "tests" / "test_mod.py").write_text("def test_x() -> None:\n    pass\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("not governed\n", encoding="utf-8")
    git(tmp_path, "init", "-q")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "start")
    return tmp_path
