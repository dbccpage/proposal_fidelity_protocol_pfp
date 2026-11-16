"""Host rerun of the cited Paper 020 braid-tournament tests.

AuthorityEffect: None.

The frozen modules import majorana_multiqubit_noise at load time. This test
runs that import path. It does not rebuild a braid matrix.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PAPER = _REPO / "atlas" / "archive" / "pfp" / "020_pfp_frontier_research"
_TESTS = (
    _PAPER / "code" / "tests" / "test_adaptive_braid_tournament_demo.py",
    _PAPER / "code" / "tests" / "test_l8_n4_cross_validation.py",
)
_ZIP = _PAPER / "022_pfp_frontier_research_2026-10-03.zip"
_MISSING = _REPO / "projects" / "ms_majorana" / "code" / "majorana_multiqubit_noise.py"
_REVIEW = _REPO / "dag" / "reviews" / "additional_p020_braid_host.json"
_IDS = tuple(f"ATL-P020-{index:03d}" for index in range(1, 13))
_HEADINGS = (
    "## 1. What this record supports",
    "## 2. What it does not support",
    "## 3. Narrowest claim",
    "## 4. Negative or null controls",
)


def _matches() -> dict[str, dict]:
    rows = json.loads((_REPO / "atlas" / "atlas_claim_matches.json").read_text(encoding="utf-8"))
    return {row["atlas_id"]: row for row in rows["results"]}


def test_cited_braid_modules_fail_collection_without_the_referee() -> None:
    assert not _MISSING.is_file()
    with zipfile.ZipFile(_ZIP) as archive:
        names = archive.namelist()
    assert names
    assert not any("majorana" in name.lower() for name in names)
    command = [sys.executable, "-B", "-X", "utf8", "-m", "pytest", "-q", "--tb=line", "-p", "no:cacheprovider"]
    command.extend(str(path) for path in _TESTS)
    res = subprocess.run(
        command,
        cwd=_REPO,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    combined = res.stdout + res.stderr
    assert res.returncode == 2, combined
    assert "ModuleNotFoundError" in combined
    assert "majorana_multiqubit_noise" in combined
    assert "2 errors during collection" in combined


def test_p020_rows_narrow_to_the_failed_collection() -> None:
    review = json.loads(_REVIEW.read_text(encoding="utf-8"))
    assert review["AuthorityEffect"] == "None"
    assert {row["id"] for row in review["claims"]} == {atlas_id.replace("ATL-", "AUDIT-") for atlas_id in _IDS}
    rows = _matches()
    for atlas_id in _IDS:
        row = rows[atlas_id]
        audit_id = atlas_id.replace("ATL-", "AUDIT-")
        assert row["verdict"] == "partial"
        assert row["relation"] == "narrows"
        assert row["nodes"] == [audit_id]
        assert row["proposed_derivation"] is not None
        assert "majorana_multiqubit_noise" in row["note"]
        text = (_REPO / "dag" / "derivations" / f"{audit_id.lower().replace('-', '_')}.md").read_text(encoding="utf-8")
        for heading in _HEADINGS:
            assert heading in text
        assert "ModuleNotFoundError" in text
