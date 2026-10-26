"""The Python toxicity denominator is not the native TP/FP denominator."""

from fractions import Fraction

from omega_engine_epistemic_immune_system.domain.treg import TregSupervisor


def test_denominator_policies_are_not_silently_merged():
    # One uncorroborated match, nine corroborated matches, ten nonmatches.
    # Python counts all twenty supplied trigger pairs, so toxicity is 1/20.
    # The native TP/FP policy counts ten positive classifications, giving 1/10.
    triggers = [(True, False)] + [(True, True)] * 9 + [(False, False)] * 10
    report = TregSupervisor().evaluate_toxicity("rule", triggers=triggers)
    assert report.signal1_only_count == 1
    assert report.total_triggers == 20
    assert report.toxicity_index == Fraction(1, 20)
    assert report.toxicity_index != Fraction(1, 10)
    assert TregSupervisor().synthesize_treg(report) is None
