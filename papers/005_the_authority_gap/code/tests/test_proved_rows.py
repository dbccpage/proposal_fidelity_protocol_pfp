"""The proved-row replay must call the shipped checkers."""

from fractions import Fraction

from proved_rows import replay_proved_rows


def test_proved_rows_call_shipped_checkers():
    report = replay_proved_rows()
    assert report["ok"] is True
    assert report["CLM-005-007"]["hidden_bit_ngd"] == str(Fraction(1, 2))
    assert report["CLM-005-007"]["unconditional_red_ngd"] == str(Fraction(1, 1))
    assert report["CLM-005-007"]["hidden_bit_cases"] == 4
    assert report["CLM-005-010"]["backlog_50_10_12"] == "480"
    assert report["CLM-005-010"]["backlog_10_3_1"] == "7"
    assert report["CLM-005-010"]["verified_share_10_3"] == str(Fraction(3, 10))
    assert report["CLM-005-011"]["missing_descent_admitted"] is False
    assert "Counterfeit descent" in report["CLM-005-011"]["missing_descent_reason"]
    assert report["CLM-005-011"]["nonzero_residual_admitted"] is False
    assert "Exactness fraud violation" in report["CLM-005-011"]["nonzero_residual_reason"]
