"""Offline selected tests and boundary probes; original package is not modified."""
import code as stdlib_code  # Preload before pytest inserts the repository's code/ package.
import pdb as stdlib_pdb  # importlib-mode conftest naming can later replace sys.modules['code'].
import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews'
PACKAGE = ROOT / 'papers/pfp/003_pfp_host_admitted_failure_detectors'
CODE = PACKAGE / 'code'
assert hasattr(stdlib_code, 'InteractiveConsole')
os.environ['PFP003_HOST_DETECTOR_BIN'] = str(OUT / 'paper003-no-native-selected.exe')
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.dont_write_bytecode = True
sys.path.insert(0, str(CODE))

if '--tests' in sys.argv:
    import pytest
    result = pytest.main([str(CODE / 'tests'), '-q', '-p', 'no:cacheprovider',
        '--basetemp=' + str(OUT / 'additional_paper_003_pytest_tmp'),
        '--junitxml=' + str(OUT / 'additional_paper_003_tests.xml')])
    raise SystemExit(result)

import live_proposer_demo as live
import host_engine as host
import native_host_detector as native

records = []
with patch('socket.socket', side_effect=AssertionError('network prohibited')):
    with patch.object(live, 'resolve_api_key', return_value=''), contextlib.redirect_stdout(io.StringIO()):
        result = live.run_demo(live=True)
    assert result['status'] == 'PASSED' and result['live_acquisition']['result'] == 'NO_API_KEY'
    records.append({'id': 'missing_key_still_overall_passed', 'result': result})
    with patch.object(live, 'resolve_api_key', return_value='public-test-placeholder'), \
         patch.object(live, 'query_openrouter', return_value=None) as query, \
         contextlib.redirect_stdout(io.StringIO()):
        result = live.run_demo(live=True)
    assert query.call_count == 1 and result['status'] == 'PASSED'
    assert result['live_acquisition']['result'] == 'FAILED_QUERY'
    records.append({'id': 'failed_mock_acquisition_still_overall_passed', 'result': result,
                    'actual_network_calls': 0})

    candidate = '{"moves":[{"move_type":"PROPOSE_WITNESS","payload":{"x":NaN}}]}'
    moves, error = live._parse_moves(candidate)
    assert error is None and len(moves) == 1
    try:
        live.process_candidate_response(candidate)
    except ValueError as exc:
        records.append({'id': 'nonfinite_payload_escapes_structural_gate', 'candidate': candidate,
                        'parser_error': error, 'raised': type(exc).__name__, 'message': str(exc)})
    else:
        raise AssertionError('Expected canonical serialization refusal to escape wrapper')

    captured = {}
    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return json.dumps({'choices': [{'message': {'content': 'public-fixture-response'}}],
                'usage': {'prompt_tokens': 10, 'completion_tokens': 20, 'cost': 0.0001}}).encode()
    def fake_urlopen(request, **kwargs):
        captured['body'] = json.loads(request.data)
        captured['transport_options'] = kwargs
        return FakeResponse()
    with patch.object(live.urllib.request, 'urlopen', side_effect=fake_urlopen):
        answer = live.query_openrouter('public control only', 'public-test-placeholder', 'mock/model')
    assert 'max_tokens' not in captured['body'] and answer == 'public-fixture-response'
    records.append({'id': 'no_output_limit_and_usage_discarded', **captured,
                    'returned_value': answer, 'actual_network_calls': 0})

    one = host.Demo3HostEngine('gauge_even_triangle', 'T', initial_fuel=1)
    many = host.Demo3HostEngine('gauge_even_triangle', 'T', initial_fuel=12)
    moves = [host.MoveProposal('COVER_ELEMENT', {'element_id': 'public-control'})]
    a, b = one.execute_batch(moves), many.execute_batch(moves)
    assert a.new_state_digest == b.new_state_digest
    assert one.state.current_phase != many.state.current_phase
    records.append({'id': 'declared_digest_not_full_state', 'digest': a.new_state_digest,
        'fuels': [one.state.remaining_fuel, many.state.remaining_fuel],
        'phases': [one.state.current_phase.value, many.state.current_phase.value],
        'interpretation': 'Confirms an explicitly documented scope limit, not an undisclosed certificate forgery.'})

    bad = {'decision': 'TOLERATED', 'is_refusal': 'false', 'disposition': 'fixture',
           'signal1_count': -10, 'signal2_severity': None, 'is_suppressed': False, 'rationale': 'fixture'}
    with patch.object(native, '_call_native', return_value=bad):
        admitted = native.native_evaluate_two_signal_gate([])
    assert admitted.is_refusal == 'false' and admitted.signal1_count == -10
    records.append({'id': 'native_adapter_shape_trust_boundary', 'admitted_mock_payload': bad,
        'interpretation': 'Malformed mocked backend output; no claim that the bundled Rust implementation produces it.'})

cli = CODE / 'rust/src/bin/solve_host_detector.rs'
source = cli.read_text()
start = source.index('fn hex_to_bytes(')
end = source.index('\nfn main()', start)
function = source[start:end]
probe_dir = OUT / 'additional_paper_003_native_probe'
probe_dir.mkdir(exist_ok=True)
probe = probe_dir / 'hex_probe.rs'
probe.write_text(function + '''
fn main() {
    std::panic::set_hook(Box::new(|_| {}));
    assert_eq!(hex_to_bytes("0a"), Ok(vec![10]));
    assert!(hex_to_bytes("zz").is_err());
    assert!(hex_to_bytes("a").is_err());
    let panicked = std::panic::catch_unwind(|| hex_to_bytes("aéa")).is_err();
    assert!(panicked);
    println!("ascii_valid_pass; ascii_invalid_refused; odd_length_refused; utf8_even_length_panics");
}
''', encoding='utf-8')
exe = probe_dir / 'hex_probe.exe'
rustc = Path.home() / '.cargo/bin/rustc.exe'
compile_result = subprocess.run([str(rustc), '--edition=2021', str(probe), '-o', str(exe)],
    capture_output=True, text=True, timeout=60)
assert compile_result.returncode == 0, compile_result.stderr
run_result = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10)
assert run_result.returncode == 0, run_result.stderr
records.append({'id': 'native_hex_unicode_boundary_panic', 'source_path': cli.relative_to(ROOT).as_posix(),
    'source_sha256': hashlib.sha256(cli.read_bytes()).hexdigest(),
    'extracted_function_sha256': hashlib.sha256(function.encode()).hexdigest(),
    'compile_exit': compile_result.returncode, 'run_exit': run_result.returncode,
    'stdout': run_result.stdout, 'limit': 'Exact dependency-free source function compiled in isolation; not a full native crate build or CLI integration test.'})

report = {'status': 'all_expected_observations_reproduced', 'probes': records,
    'provider_calls': 0, 'private_answer_access': False,
    'source_hashes': {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [CODE / 'live_proposer_demo.py', CODE / 'host_engine.py', CODE / 'native_host_detector.py', cli]},
    'test_launch_setup': {'initial_attempts': 4, 'collection_or_tests_executed': False,
        'error': 'Repository code/ shadows stdlib code during pytest configuration; pdb requires InteractiveConsole.',
        'resolution': 'Isolated interpreter preloads stdlib pdb and code before importlib-mode conftest loading; original source untouched.'}}
(OUT / 'additional_paper_003_probes.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'probes': len(records), 'status': report['status'], 'provider_calls': 0}))
