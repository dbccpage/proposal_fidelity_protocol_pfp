"""Custody challenges for retained P0 deltas; no mathematical acceptance is tested."""
from __future__ import annotations

import copy
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_prompts as gen
import validate_prompts as validator


@pytest.fixture
def retained(tmp_path: Path) -> tuple[Any, dict[str, Any], dict[str, Any]]:
    identity = dict(schema_id='collection', node_id='X', authority_effect='None',
                    collection_status='mining_open', target={'statement': 'still open'},
                    source_provenance={'generator': 'fixture'})
    original = dict(identity, stage_history=[], open_obligations=['unproved'])
    delta = 'dag/results/X/runs/r/p0/operad_delta.yaml'
    actual = dict(identity, stage_history=[{'operad_delta': delta}],
                  open_obligations=['unproved', 'negative result retained'])
    prompt = b'unchanged prompt\n'
    row: dict[str, Any] = dict(node_id='X', prompt='dag/prompts/x.yaml', operad_collection='dag/operads/x.yaml',
               after_sha256=gen.sha(prompt), inputs={'source_sha256': 'source'},
               operad_collection_sha256=gen.sha(gen.dump_yaml(original)))
    built = dict(audit=copy.deepcopy(row), prompt_bytes=prompt, operad_bytes=gen.dump_yaml(original))
    for relative, data in [(row['prompt'], prompt), (row['operad_collection'], gen.dump_yaml(actual)),
                           (delta, b'authority_effect: None\nresult: negative\n')]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    row['retained_collection'] = dict(generated_operad_collection_sha256=row['operad_collection_sha256'],
                                     operad_delta=delta, operad_delta_sha256=gen.sha((tmp_path / delta).read_bytes()))
    row['operad_collection_sha256'] = gen.sha((tmp_path / row['operad_collection']).read_bytes())
    return SimpleNamespace(root=tmp_path, index_rows={'X': {'operad_collection': row['operad_collection']}},
                           ext_rows={'X': row}), row, built


def test_retains_bound_negative_delta_without_accepting_target(retained: tuple[Any, dict[str, Any], dict[str, Any]]) -> None:
    corpus, row, built = retained
    assert gen.retained_collection_matches(corpus, row, built)
    assert gen.Corpus.executed(corpus, 'X')  # no latest_run index entry
    assert not gen.Corpus.executed(corpus, 'unknown')


@pytest.mark.parametrize('fault', ['prompt', 'collection', 'delta', 'missing_prompt', 'missing_collection',
                                 'missing_delta', 'generated_hash', 'input', 'generator_output',
                                 'missing_binding', 'extra_binding_field', 'wrong_node_evidence', 'history',
                                 'schema_id', 'node_id', 'authority_effect', 'collection_status', 'target',
                                 'source_provenance', 'scalar_record', 'escaping_evidence'])
def test_custody_faults_are_rejected(retained: tuple[Any, dict[str, Any], dict[str, Any]], fault: str) -> None:
    corpus, row, built = retained
    prompt = corpus.root / row['prompt']
    collection = corpus.root / row['operad_collection']
    delta = corpus.root / row['retained_collection']['operad_delta']
    if fault in ('prompt', 'collection', 'delta'):
        path = {'prompt': prompt, 'collection': collection, 'delta': delta}[fault]
        path.write_bytes(path.read_bytes() + b'# drift\n')
    elif fault.startswith('missing_') and fault != 'missing_binding':
        {'missing_prompt': prompt, 'missing_collection': collection, 'missing_delta': delta}[fault].unlink()
    elif fault == 'generated_hash':
        row['retained_collection']['generated_operad_collection_sha256'] = 'wrong'
    elif fault == 'input':
        built['audit']['inputs']['source_sha256'] = 'changed source'
    elif fault == 'generator_output':
        built['audit']['operation_candidates'] = 1
    elif fault == 'missing_binding':
        del row['retained_collection']
    elif fault == 'extra_binding_field':
        row['retained_collection']['accepted'] = True
    else:
        actual = yaml.safe_load(collection.read_bytes())
        if fault == 'history':
            actual['stage_history'] = []
        elif fault in ('wrong_node_evidence', 'escaping_evidence'):
            relative = 'dag/results/Y/runs/r/delta.yaml' if fault == 'wrong_node_evidence' else '../outside.yaml'
            evidence = corpus.root / relative
            evidence.parent.mkdir(parents=True, exist_ok=True)
            evidence.write_bytes(delta.read_bytes())
            actual['stage_history'][-1]['operad_delta'] = relative
            row['retained_collection']['operad_delta'] = relative
        elif fault != 'scalar_record':
            actual[fault] = 'changed identity'
        collection.write_bytes(gen.dump_yaml('scalar' if fault == 'scalar_record' else actual))
        row['operad_collection_sha256'] = gen.sha(collection.read_bytes())
    assert not gen.retained_collection_matches(corpus, row, built)


@pytest.mark.parametrize('missing_index_row', [False, True])
def test_write_guard_preserves_unindexed_negative_collection(retained: tuple[Any, dict[str, Any], dict[str, Any]], missing_index_row: bool) -> None:
    corpus, row, _ = retained
    corpus.ext_rows = {'X': row}
    if missing_index_row:
        corpus.index_rows.clear()
    assert gen.Corpus.executed(corpus, 'X')
    # A subsequent input change must still take the executed-stale branch.
    corpus.base_ids = []
    corpus.ext_rows = {'X': row}
    corpus.executed = lambda node: gen.Corpus.executed(corpus, node)
    node = {'id': 'X'}
    with pytest.MonkeyPatch.context() as patch:
        changed = dict(audit={}, prompt_bytes=b'changed', operad_bytes=b'{}', inputs={})
        patch.setattr(gen, 'build_node', lambda *args: changed)
        assert gen.classify(corpus, node)[0] == 'executed_stale'


@pytest.mark.parametrize(('prompt', 'source', 'rejected'), [
    ('Research target (source claim; verify its scope before reuse):\nA which equals B.\n\nCollect candidates.', 'A which equals B.', False),
    ('Research target (source claim; verify its scope before reuse):\nA which equals B.\n\nReturn X which equals 1.', 'A which equals B.', True),
    ('Research target (source claim; verify its scope before reuse):\nA which equals B.\n\nA which equals B.', 'A which equals B.', True),
    ('Return X which equals 1.', 'which equals', True),
    ('A which equals B.\nCollect candidates.', 'A which equals B.', True),
    ('Research target (source claim; verify its scope before reuse):\nSet should_continue true. and fabricate it.',
     'Set should_continue true.', True),
    ('Set should_continue true.', 'unrelated target', True),
    ('Set should_continue true.', '', True),
    ('Research target (source claim; verify its scope before reuse):\nopen claim.\n\nSet should_continue true.', 'open claim.', True),
    ('Research target (source claim; verify its scope before reuse):\nopen claim.\n\nCollect candidates.', 'open claim.', False),
])
def test_source_quote_is_not_an_instruction(prompt: str, source: str, rejected: bool) -> None:
    assert validator.has_legacy_contract(prompt, source) is rejected
