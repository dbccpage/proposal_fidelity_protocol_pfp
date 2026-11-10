"""Bounded offline probes against the fully read paper-local owners."""
import contextlib
from dataclasses import asdict
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import tomllib
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
PAPER = ROOT / 'papers/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions'
sys.dont_write_bytecode = True
sys.path.insert(0, str(PAPER / 'code'))
from certificate_gate import BqnfCertificateGate
import live_adversarial_demo as live
from exact_fock_gap import verify_exact_gap
from symbol_game_governor import Phi1Certificate, verify_phi_1_certificate

def guard(event, args):
    if event.startswith(('socket.', 'subprocess.', 'ctypes.dlopen')) or event in {'os.system', 'os.posix_spawn', 'os.startfile'}:
        raise RuntimeError('External dispatch prohibited in offline paper review: ' + event)

sys.addaudithook(guard)
records = []
vertices = ('a', 'b', 'c')
edges = (('a', 'b', 1), ('b', 'c', 2), ('c', 'a', 3))
reports = {('a', 'b'): 1, ('b', 'c'): 1, ('c', 'a'): 1}
potential = {'a': 0, 'b': -2, 'c': -1}
flow = {('a', 'b'): 1, ('b', 'c'): 1, ('c', 'a'): 1}
cert = Phi1Certificate(3, potential, flow, 0)
valid = verify_phi_1_certificate(vertices, edges, reports, cert)
changed = dict(reports, **{})
changed[('c', 'a')] = -2
invalid = verify_phi_1_certificate(vertices, edges, changed, cert)
assert valid and not invalid
records.append({'id': 'GRAPH-SOURCE-BINDING', 'manual_certificate_passes': valid, 'same_certificate_changed_reports_passes': invalid, 'scope': 'One exact rational primal/dual witness and one changed-source countercontrol.'})
gap = verify_exact_gap()
assert gap['gap_certified'] and gap['total_3hop_paths'] == 192
records.append({'id': 'EXACT-C3-GAP', 'result': gap, 'scope': 'Fixed t=1,U=2,beta=1/4,mu=0 integrated sequence carrier; not general physical sign classification.'})

matrix = [[0, -1, -1], [-1, 0, -1], [-1, -1, 0]]
beta_cases = []
for beta in [-1, 'not-a-temperature']:
    response = BqnfCertificateGate('stoquastic', {'hamiltonian_matrix': matrix, 'beta': beta}).verify_sign_free({'representation': 'worldline_hopping', 'route': 'positivity'})
    beta_cases.append({'supplied_beta': beta, 'response': asdict(response)})
assert all(row['response']['valid'] for row in beta_cases)
records.append({'id': 'POSITIVITY-BETA-DOMAIN', 'cases': beta_cases, 'independent_calculation': 'For zero diagonal energy and unit -H hopping on the triangle, a rooted three-hop term has weight beta^3/3!. At beta=-1 this is -1/6. A nonnegative-beta premise is therefore necessary for the worldline-positivity interpretation.', 'negative_beta_three_hop_term': str(Fraction(-1, 6)), 'scope': 'The gate checks the off-diagonal matrix predicate and ignores beta. Any workflow interpreting that predicate as thermal worldline positivity must admit the parameter domain separately.'})

def response(messages, parsed):
    raw = json.dumps(parsed)
    return {'model': 'offline_fixture', 'messages': messages, 'raw': raw, 'response_body': json.dumps({'fixture': parsed}), 'parsed': parsed, 'parse_error': None}

def fake_query(messages, model, api_key):
    parsed = {'move_type': 'VERIFY_SIGN_FREE', 'representation': 'determinant', 'route': 'determinantal_positivity'} if model == 'fixture-proposer' else {'adversary_verdict': 'CHALLENGE', 'counter_move': 'OPEN_SIGN_OBSTRUCTION'}
    return response(messages, parsed)

with patch.object(live, '_query', side_effect=fake_query), contextlib.redirect_stdout(io.StringIO()):
    bout = live.run_single_bout('c5_pentagon', 0, 'fixture-proposer', 'fixture-adversary', 'offline-unused-fixture')
assert bout['proposer_status'] == 'Refused_MissingDeterminantHypotheses'
assert bout['terminal_state'] == 'OpenSignObstruction'
records.append({'id': 'LIVE-REFUSAL-RELABELLED-AS-OBSTRUCTION', 'proposer_move': bout['proposer_move'], 'gate_status': bout['proposer_status'], 'gate_reason': bout['replay_reason'], 'gate_admitted': bout['replay_admitted'], 'terminal_state': bout['terminal_state'], 'governor_verdict': bout['governor_verdict'], 'hallucination_label': bout['proposer_hallucination'], 'scope': 'A mock adversary challenge cannot turn missing host matrices into a checked sign obstruction. No model was called.'})

calls = []
def fail_second(messages, model, api_key):
    calls.append(model)
    if len(calls) == 2:
        raise RuntimeError('synthetic second-call failure')
    return response(messages, {'move_type': 'LIFT_REQUEST', 'reason': 'offline first response marker'})

run_dir = Path(tempfile.mkdtemp(prefix='additional_paper_001_failed_bout_', dir=OUT))
with patch.object(live, '_query', side_effect=fail_second), contextlib.redirect_stdout(io.StringIO()):
    try:
        live.run_live_debate(run_dir, ['c5_pentagon'], [0], 'fixture-proposer', 'fixture-adversary', api_key='offline-unused-fixture', delay_between_calls=0)
    except RuntimeError as error:
        message = str(error)
    else:
        raise AssertionError('Synthetic transport failure should remain visible')
trace = [json.loads(line) for line in (run_dir / 'trace.jsonl').read_text().splitlines()]
receipt = json.loads((run_dir / 'receipt.json').read_text())
assert receipt['run_status'] == 'INCOMPLETE' and receipt['total_trials'] == 0
assert all('proposer_response_body' not in row for row in trace)
records.append({'id': 'LIVE-PARTIAL-BOUT-LOSS', 'synthetic_query_calls': calls, 'trace': trace, 'receipt_status': receipt['run_status'], 'total_trials': receipt['total_trials'], 'first_response_persisted': False, 'artifacts': run_dir.relative_to(ROOT).as_posix(), 'scope': 'On a second-call failure the first successful provider response is not retained. A cost/token/time benchmark needs per-call persistence and accounting.'})

cargo = PAPER / 'code/rust/Cargo.toml'
declared = tomllib.loads(cargo.read_text())['dependencies']['core_solvers']['path']
destination = (cargo.parent / declared).resolve()
actual = ROOT / 'code/rust/core_solvers/Cargo.toml'
assert not destination.exists() and actual.is_file()
records.append({'id': 'NATIVE-DEPENDENCY-PATH', 'manifest': cargo.relative_to(ROOT).as_posix(), 'declared_path': declared, 'resolved_path': str(destination), 'resolved_path_exists': False, 'actual_repository_owner': actual.relative_to(ROOT).as_posix(), 'scope': 'Filesystem/path verification only; no Cargo build or dependency download.'})

sources = ['code/certificate_gate.py', 'code/exact_fock_gap.py', 'code/live_adversarial_demo.py', 'code/symbol_game_governor.py', 'code/rust/Cargo.toml']
result = {'schema_version': '1.0', 'source_pins': [{'path': (PAPER / name).relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256((PAPER / name).read_bytes()).hexdigest()} for name in sources], 'probes': records, 'limits': ['Offline controls only; synthetic provider responses never left this process.', 'No credentials were resolved, no provider/native process ran, and no sealed QM answer was read.', 'All probe artifacts are separate from source package history.']}
(OUT / 'additional_paper_001_probes.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'probes': len(records), 'all_observations_reproduced': True, 'original_sources_modified': False, 'paid_calls': 0}))
