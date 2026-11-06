"""Counterexamples to the retired two-condition equivalence in Lemma 7.1."""
from fractions import Fraction

from mod_authority_gap_core import calculate_ngd


def test_zero_ngd_does_not_require_boundary_information_factorization():
    trials = [{"hidden": h, "boundary": "constant", "continuation": "fixed",
               "local_green": h == 0, "global_red": h != 0} for h in (0, 1)]
    assert calculate_ngd(trials) == Fraction(0)
    assert len({(row["boundary"], row["continuation"]) for row in trials}) == 1
    assert len({row["global_red"] for row in trials}) == 2


def test_information_factorization_does_not_imply_zero_ngd():
    trials = [{"local_green": True, "global_red": True} for _ in (0, 1)]
    assert calculate_ngd(trials) == Fraction(1)
