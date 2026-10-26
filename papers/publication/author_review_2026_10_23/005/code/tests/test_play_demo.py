"""
Checks that the worked session (`play_demo.py`, guide Section 4) reproduces the
table in the guide, on both calculation paths of the vendored governor.
"""

from fractions import Fraction

from play_demo import run_session


def _assert_session_table(r):
    assert r["weights"] == (1, 2, 3)
    assert r["phi_after_assert"] == Fraction(3)      # holonomy 1+1+1
    assert r["bad_status"] == "DefectIncrease"        # defect-increasing CUT refused
    assert r["bad_admitted"] is False
    assert r["repair_status"] == "ExactRepair"        # consistent replacement admitted
    assert r["repair_before"] == Fraction(3)
    assert r["repair_after"] == Fraction(0)
    assert r["verify_admitted"] is True               # host confirms zero obstruction
    assert r["phi_after_retract"] == Fraction(3)      # RETRACT restores pre-repair state


def test_worked_session_matches_manual(native_functional):
    """Through the pinned native calculator (skips without pins)."""
    result = run_session(verbose=False)
    assert result["calculation_path"] == "native"
    _assert_session_table(result)


def test_worked_session_offline_enumeration(monkeypatch):
    """Without pins the governor's exact Python enumeration gives the same table.

    These are Python enumeration results, not native results.
    """
    monkeypatch.delenv("OMEGA_FUNCTIONAL_GRAPH_BIN", raising=False)
    monkeypatch.delenv("OMEGA_FUNCTIONAL_GRAPH_SHA256", raising=False)
    result = run_session(verbose=False)
    assert result["calculation_path"] == "python-enumeration"
    _assert_session_table(result)
