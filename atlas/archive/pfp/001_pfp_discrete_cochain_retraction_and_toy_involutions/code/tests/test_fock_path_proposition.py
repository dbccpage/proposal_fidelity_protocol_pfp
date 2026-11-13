"""
Unit Test: Verification of the Restricted Fock Path Proposition.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fock_path_enumerator import verify_fock_path_proposition


def test_fock_path_proposition_192_paths_and_gap():
    res = verify_fock_path_proposition()
    assert res["total_paths"] == 192
    assert res["neg_paths"] == 96
    assert res["pos_paths"] == 96
    assert res["max_positive_path_energy"] <= 2.0
    assert res["abs_target_weight"] > res["four_hop_upper_bound"]
    assert res["abs_target_weight"] < res["min_positive_3hop_weight"]
    assert res["gap_certified"] is True
