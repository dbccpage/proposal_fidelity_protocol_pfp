"""Public empirical command admission; never contact a model provider."""

import json
from hashlib import sha256

from omega_engine_pfp.entrypoints import empirical_gates as cli


def token_inputs(tmp_path):
    source = tmp_path / 'tasks.json'
    source.write_text(json.dumps({'tasks': [
        {'id': f't{i}', 'prompt': f'Return the sum of {i} and 1.'} for i in range(10)
    ]}), encoding='utf-8')
    return source


def test_plan_counts_matched_four_model_unit_marginals(tmp_path, capsys):
    source = token_inputs(tmp_path)
    assert cli.main(['--suite', 'tokens', '--input', str(source), '--models',
                     'a', 'b', 'c', 'd', '--plan']) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan['planned_provider_calls'] == 32
    assert plan['provider_calls'] == 0
    assert plan['batch_sizes'] == [1, 2, 9, 10]
    assert plan['authority_effect'] == 'None'


def test_rewrite_plan_requires_no_model_and_is_zero_send(capsys):
    assert cli.main(['--suite', 'rewrites', '--plan']) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan['planned_provider_calls'] == plan['provider_calls'] == 0
    assert plan['rewrite_cases'] == 50


def test_live_requires_explicit_shared_allowance_before_creating_output(tmp_path, capsys):
    source = token_inputs(tmp_path)
    output = tmp_path / 'measurements.json'
    assert cli.main(['--suite', 'tokens', '--input', str(source), '--models', 'a',
                     '--output', str(output)]) == 2
    assert 'EXPLICIT_PROVIDER_ALLOWANCE_REQUIRED' in capsys.readouterr().err
    assert not output.exists()
    assert not list(tmp_path.glob('*.sqlite3'))


def test_rejects_ambiguous_input_before_provider_admission(tmp_path, capsys):
    source = tmp_path / 'duplicate.json'
    source.write_text('{"tasks":[],"tasks":[]}', encoding='utf-8')
    assert cli.main(['--suite', 'tokens', '--input', str(source), '--models', 'a', '--plan']) == 2
    assert capsys.readouterr().err
    assert not list(tmp_path.glob('*.sqlite3'))


def test_existing_output_is_preserved_before_any_dispatch(tmp_path, capsys):
    source = token_inputs(tmp_path)
    output = tmp_path / 'measurements.json'
    output.write_bytes(b'historical measurements\r\n')
    assert cli.main(['--suite', 'tokens', '--input', str(source), '--models', 'a',
                     '--max-provider-calls', '8', '--max-estimated-cost-microusd', '1000',
                     '--output', str(output)]) == 2
    assert 'OUTPUT_EXISTS' in capsys.readouterr().err
    assert output.read_bytes() == b'historical measurements\r\n'
    assert not list(tmp_path.glob('*.sqlite3'))


def test_woland_uses_same_empirical_entrypoint(monkeypatch):
    from omega_engine_woland.entrypoints.cli import main as woland_main

    received = []
    monkeypatch.setattr(cli, 'main', lambda args: received.append(args) or 0)
    assert woland_main(['empirical', '--suite', 'rewrites', '--plan']) == 0
    assert received == [['--suite', 'rewrites', '--plan']]


def test_anthropic_plan_binds_explicit_rate_snapshot_without_provider_calls(tmp_path, capsys):
    source = token_inputs(tmp_path)
    snapshot = dict(source_url='https://platform.claude.com/docs/en/about-claude/pricing',
                    observed_at_utc='2026-10-14T22:00:00+00:00',
                    rows=[dict(id='synthetic-anthropic-model',
                               pricing=dict(prompt='0.000001', completion='0.000005'))])
    snapshot['catalog_sha256'] = sha256(cli._canonical(snapshot).encode()).hexdigest()
    pricing = tmp_path / 'prices.json'
    pricing.write_text(json.dumps(snapshot), encoding='utf-8')
    assert cli.main(['--suite', 'tokens', '--input', str(source), '--models',
                     'synthetic-anthropic-model', '--provider', 'anthropic',
                     '--pricing-snapshot', str(pricing), '--plan']) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan['provider'] == 'anthropic'
    assert plan['pricing_snapshot'] == snapshot
    assert plan['planned_provider_calls'] == 8
    assert plan['provider_calls'] == 0
    assert not list(tmp_path.glob('*.sqlite3'))
    snapshot['rows'][0]['pricing']['completion'] = '0.0000001'
    pricing.write_text(json.dumps(snapshot), encoding='utf-8')
    assert cli.main(['--suite', 'tokens', '--input', str(source), '--models',
                     'synthetic-anthropic-model', '--provider', 'anthropic',
                     '--pricing-snapshot', str(pricing), '--plan']) == 2
    assert capsys.readouterr().err


def test_anthropic_never_silently_uses_openrouter_rates(tmp_path, capsys):
    source = token_inputs(tmp_path)
    assert cli.main(['--suite', 'tokens', '--input', str(source), '--models',
                     'synthetic-anthropic-model', '--provider', 'anthropic', '--plan']) == 2
    assert 'ANTHROPIC_PRICING_SNAPSHOT_REQUIRED' in capsys.readouterr().err
