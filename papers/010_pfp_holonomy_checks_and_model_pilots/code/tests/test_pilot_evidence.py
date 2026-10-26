"""Published counts must follow the retained case flags and source bytes."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import recount_pilots  # noqa: E402


def test_historical_sources_and_c017_extraction_match_original_bytes() -> None:
    assert recount_pilots.verify_source_bytes() == 15
    assert recount_pilots.verify_c017_extraction() == 25


def test_table3_counts_follow_per_case_acceptance_flags() -> None:
    assert recount_pilots.table3() == {
        "c045": (2, 8, 3), "c046": (4, 7, 8), "c047": (4, 2, 0), "c048": (10, 8, 5),
        "c049_panel_a": (5, 6, 4), "c049_panel_b": (9, 6, 6),
        "c050_run_1": (7, 4, 1), "c050_run_2": (6, 3, 1),
    }


def test_table4_recounts_author_categories_and_prior_baseline_record() -> None:
    rows = recount_pilots.table4()
    assert rows == {"C045": (7, 3, 0, 10), "C046": (5, 3, 2, 10), "C047": (4, 6, 0, 0),
                    "C048": (10, 0, 0, 3), "C049": (5, 5, 0, 2), "C050": (5, 5, 0, 1)}
    assert sum(row[0] for row in rows.values()) == 36
    assert sum(sum(row[:3]) for row in rows.values()) == 60


def test_recount_rejects_summary_or_panel_mismatch() -> None:
    model = recount_pilots.load("c050_run_1.json")["models"]["Space Bunny Alpha"]
    wrong_total = copy.deepcopy(model)
    wrong_total["passed"] += 1
    with pytest.raises(ValueError, match="summary passed"):
        recount_pilots.count_model(wrong_total)
    wrong_panel = copy.deepcopy(model)
    wrong_panel["records"][1]["case_id"] = wrong_panel["records"][0]["case_id"]
    with pytest.raises(ValueError, match="ten distinct"):
        recount_pilots.count_model(wrong_panel)
