from fractions import Fraction

import pytest

from omega_engine_operads.domain.operad.treg import OperadTregSupervisor


def test_missing_danger_is_not_a_false_positive():
    supervisor = OperadTregSupervisor()
    for _ in range(5):
        assert supervisor.record_operation_step('learned', True, False) is None
    assert not supervisor.is_downgraded('learned')


def test_checked_false_positives_target_only_optional_learned_detector():
    from omega_engine_operads.domain.operad.treg import CheckedFalsePositive
    supervisor = OperadTregSupervisor()
    results = []
    for index in range(3):
        evidence = CheckedFalsePositive('learned', str(index) * 64, 'host-checker', 'e' * 64)
        results.append(supervisor.record_operation_step('learned', True, False,
            false_positive=evidence, learned_detector=True))
    assert results[-1].toxicity_index == Fraction(1)
    assert supervisor.is_downgraded('learned')
    assert not supervisor.is_downgraded('another')


def test_mandatory_gate_and_conflicting_witness_cannot_be_downgraded():
    from omega_engine_operads.domain.operad.treg import CheckedFalsePositive
    evidence = CheckedFalsePositive('budget', 'a' * 64, 'host-checker', 'e' * 64)
    supervisor = OperadTregSupervisor(min_suppressions=1)
    with pytest.raises(ValueError, match='PROTECTED_GATE'):
        supervisor.record_operation_step('budget', True, False, false_positive=evidence,
            learned_detector=True, protected=True)
    with pytest.raises(ValueError, match='CONTRADICTORY'):
        supervisor.record_operation_step('budget', True, True, false_positive=evidence,
            learned_detector=True)


def test_replayed_false_positive_does_not_inflate_count():
    from omega_engine_operads.domain.operad.treg import CheckedFalsePositive
    evidence = CheckedFalsePositive('learned', 'a' * 64, 'host-checker', 'e' * 64)
    supervisor = OperadTregSupervisor()
    for _ in range(5):
        assert supervisor.record_operation_step('learned', True, False,
            false_positive=evidence, learned_detector=True) is None
