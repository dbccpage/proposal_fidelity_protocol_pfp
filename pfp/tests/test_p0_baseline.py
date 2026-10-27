"""Source-pinned baseline custody checks. AuthorityEffect: None."""

from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path

import pytest
import yaml

from pfp.infrastructure.pilot_baseline import MATRIX, build_baseline

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
BASE = "df84a59644c2a6837756273ccedd7b1233525407"


def test_frozen_register_binds_complete_source_inventories():
    matrix = yaml.safe_load((ROOT / MATRIX).read_text(encoding="utf-8"))
    baseline = build_baseline(ROOT, BASE)
    assert matrix["p0_review_baseline"] == baseline
    assert baseline["counts"] == {"numbered": 51, "catalog": 143, "results": 75}
    assert Counter(row["claim_class"] for row in baseline["numbered_entries"]) == {
        "source_only_specification": 26, "unreplayed_executable_control": 25,
    }
    assert sum(row["spec_blob"] is None for row in baseline["catalog_entries"]) == 66
    assert all(not row["efficacy_eligible"] for rows in
               (baseline["numbered_entries"], baseline["catalog_entries"], baseline["result_entries"])
               for row in rows)
    assert all(len(row["artifact_blobs"]["response.yaml"]) == 40
               for row in baseline["result_entries"])


def test_register_is_an_overlay_preserving_existing_matrix_bytes():
    original = subprocess.run(["git", "-C", str(ROOT), "show", f"{BASE}:{MATRIX}"],
                              check=True, capture_output=True).stdout
    candidate = (ROOT / MATRIX).read_bytes()
    # Git checks out text with platform newlines; compare the exact normalized prefix.
    assert candidate.replace(b"\r\n", b"\n").startswith(original.replace(b"\r\n", b"\n"))


@pytest.mark.parametrize("base", ["main", "df84a59", "../HEAD"])
def test_baseline_refuses_unpinned_source(base):
    with pytest.raises(ValueError, match="FULL_COMMIT_SHA"):
        build_baseline(ROOT, base)
