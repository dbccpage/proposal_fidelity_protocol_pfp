from hashlib import sha256

import pytest

from eis.domain.guard_activation import DetectorHitRefV1
from eis.use_cases.regulate_guard import BenignCheckResult, RegulatedGuardState


class Admitted:
    def is_externally_admitted(self, spec_id, scope):
        return True
    def is_suspended(self, spec_id, scope):
        return False


class Checker:
    def __init__(self, verdict):
        self.verdict = verdict
    def check_benign(self, content):
        return BenignCheckResult(sha256(content.encode()).hexdigest(), 'host-benign-check',
            sha256(('check:' + content).encode()).hexdigest(), self.verdict)


def hit(content, spec='learned'):
    return DetectorHitRefV1(hit_id='sha256:' + 'a' * 64, spec_id=spec,
        failure_code='MATCH', subject_id='sha256:' + sha256(content.encode()).hexdigest())


def state():
    return RegulatedGuardState(Admitted(), scope='task', optional_learned_ids=frozenset({'learned'}),
        protected_ids=frozenset({'budget', 'provenance', 'authorization', 'original_task'}))


def test_independent_benign_controls_suspend_only_target_and_scope():
    subject = state()
    for index in range(3):
        text = 'benign-' + str(index)
        result = subject.observe(hit(text), text, checker=Checker('BENIGN'))
    assert result.target_operation == 'learned'
    assert subject.is_suspended('learned', 'task')
    assert not subject.is_suspended('learned', 'another-task')
    assert not subject.is_suspended('budget', 'task')
    assert subject.is_externally_admitted('learned', 'task')


@pytest.mark.parametrize('verdict', ['HARMFUL', 'UNAVAILABLE'])
def test_harmful_or_unavailable_is_not_false_positive(verdict):
    subject = state()
    for index in range(6):
        text = str(index)
        assert subject.observe(hit(text), text, checker=Checker(verdict)) is None
    assert not subject.is_suspended('learned', 'task')


def test_protected_gate_rejects_before_checker():
    subject = state()
    with pytest.raises(ValueError, match='PROTECTED_GATE'):
        subject.observe(hit('budget', 'budget'), 'budget', checker=None)


def test_executed_detector_and_independent_json_control():
    import json
    class JsonControl:
        def check_benign(self, content):
            payload = json.loads(content)
            # This finite contract permits quoted text but forbids executing it.
            verdict = 'BENIGN' if payload.get('mode') == 'quote' else 'HARMFUL'
            return BenignCheckResult(sha256(content.encode()).hexdigest(),
                'json-mode-control-v1', sha256((verdict + content).encode()).hexdigest(), verdict)
    def overbroad_detector(content):
        return hit(content) if 'execute' in content else None
    subject = state()
    for index in range(3):
        content = json.dumps({'mode': 'quote', 'text': f'execute example {index}'})
        observed = overbroad_detector(content)
        assert observed is not None
        subject.observe(observed, content, checker=JsonControl())
    assert subject.is_suspended('learned', 'task')
    harmful = state()
    for index in range(3):
        content = json.dumps({'mode': 'execute', 'text': str(index)})
        assert harmful.observe(overbroad_detector(content), content, checker=JsonControl()) is None
    assert not harmful.is_suspended('learned', 'task')


def test_checker_exception_does_not_count_as_false_positive():
    class Missing:
        def check_benign(self, content):
            raise TimeoutError('offline check unavailable')
    subject = state()
    for index in range(3):
        content = str(index)
        assert subject.observe(hit(content), content, checker=Missing()) is None
    assert not subject.is_suspended('learned', 'task')
