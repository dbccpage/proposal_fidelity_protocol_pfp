"""End-to-end allocation controls with synthetic text and zero paid calls."""
import socket
from pathlib import Path

import pytest

import reference_runner as runner


@pytest.fixture(autouse=True)
def no_external_context(monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError('Network is forbidden in offline controls')
    monkeypatch.setattr(socket.socket, 'connect', refuse)
    original = Path.open
    def guarded(path, *args, **kwargs):
        name = str(path).replace('\\', '/').lower()
        assert not any(part in name for part in ('.benchmark_private', 'evaluator_rubric',
                       'criterion_evidence', '/grades.json', '/evaluation.md'))
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded)


def test_five_calls_preserve_seed_isolation_and_all_raw_outputs(tmp_path):
    texts = [f'SYNTHETIC independent result {i}; no mathematical claim.' for i in range(5)]
    tape = runner.OfflineTape(texts)
    result = runner.run('section_allocated_v1', tape, tmp_path/'full', 'allocation-full', max_output_tokens=16000)
    seed = (runner.HERE/'seed_prompt.txt').read_bytes()
    assert len(tape.requests) == 5
    assert sum(request['max_output_tokens'] for request in tape.requests) == 16000
    for request in tape.requests:
        assert request['messages'][1]['content'].encode('utf-8') == seed
        assert len(request['messages']) == 2
        assert not any(text in str(request) for text in texts)
        assert request['tools'] == [] and request['retries'] == 0
    assert result['status'] == 'offline_fixture_completed'
    assert result['host_checks']['all_sections_nonempty'] is True
    for text, section in zip(texts, result['host_checks']['sections'], strict=True):
        a, b = section['raw_text_character_span']
        assert result['answer_text'][a:b] == text
    assert result['accuracy_score'] is None
    assert result['host_checks']['claims'] == []
    assert result['host_checks']['consistency_certified'] is False


def test_failure_keeps_prior_sections_without_promoting_last_response(tmp_path):
    tape = runner.OfflineTape(['FIRST RAW SECTION', 'SECOND RAW SECTION'])
    result = runner.run('section_allocated_v1', tape, tmp_path/'partial', 'allocation-partial')
    assert result['status'] == 'provider_or_accounting_failure'
    assert 'FIRST RAW SECTION' in result['answer_text'] and 'SECOND RAW SECTION' in result['answer_text']
    assert result['answer_text'] != 'SECOND RAW SECTION'
    assert result['host_checks']['missing_stage_ids'] == ['part_3', 'part_4', 'part_5']
    assert result['host_checks']['all_sections_nonempty'] is False
    assert len(tape.requests) == 3  # Failure stops later dispatches.


def test_no_delivered_section_is_not_a_placeholder_answer(tmp_path):
    result = runner.run('section_allocated_v1', runner.OfflineTape([]), tmp_path/'none', 'allocation-none')
    assert result['answer_text'] is None and result['answer_sha256'] is None
    assert result['host_checks']['all_sections_nonempty'] is False


def test_smaller_global_ceiling_is_enforced_on_each_section(tmp_path):
    tape = runner.OfflineTape(['synthetic'] * 5)
    runner.run('section_allocated_v1', tape, tmp_path/'small', 'allocation-small', max_output_tokens=100)
    assert [request['max_output_tokens'] for request in tape.requests] == [100] * 5


def test_empty_returned_part_is_retained_as_delivery_failure(tmp_path):
    result = runner.run('section_allocated_v1', runner.OfflineTape(['synthetic', '', 'a', 'b', 'c']),
                        tmp_path/'empty', 'allocation-empty')
    assert result['status'] == 'section_delivery_incomplete'
    assert result['host_checks']['empty_stage_ids'] == ['part_2']
    assert result['host_checks']['artifact_errors'] == {'part_2': 'SECTION_NOT_DELIVERED'}
