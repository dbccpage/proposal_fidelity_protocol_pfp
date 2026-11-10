"""Offline, source-bound tests and countercontrols for the field manual."""
from pathlib import Path
import contextlib
from fractions import Fraction as Q
import hashlib
import io
import json
import os
import sys
from unittest.mock import patch

# Preload stdlib modules before the package's historical code/ name can shadow it.
import code
import pdb

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews'
PACKAGE = ROOT / 'papers/pfp/005_pfp_practitioners_field_manual'
scope = json.loads((OUT/'additional_paper_005_support_scope.json').read_text())
for row in scope['files']:
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest() == row['sha256']
os.environ.pop('CORE_FUNCTIONAL_GRAPH_BIN',None)
os.environ.pop('CORE_FUNCTIONAL_GRAPH_SHA256',None)
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
sys.dont_write_bytecode = True
sys.path.insert(0,str(PACKAGE/'code'))

if any(flag in sys.argv for flag in ('--tests','--all-tests','--pure-tests')):
    import pytest
    os.environ['OPENAI_API_KEY'] = ''  # Loopback SSE tests must never resolve a user credential.
    names = ['test_harness_exact_inputs','test_manual_contracts','test_llm_streaming_harness',
        'test_cut_completeness','test_native_refusal_propagation','test_offline_worksheet',
        'test_play_demo','test_quickstart_native']
    all_tests = '--all-tests' in sys.argv or '--pure-tests' in sys.argv
    args = [str(PACKAGE/'code/tests')] if all_tests else [str(PACKAGE/'code/tests'/f'{n}.py') for n in names]
    args += ['--import-mode=importlib','-o','addopts=','-p','no:cacheprovider','-q',
        '--basetemp',str(OUT/'paper_005_test_tmp'),
        '--junitxml',str(OUT/('additional_paper_005_pure_tests.xml' if '--pure-tests' in sys.argv else 'additional_paper_005_full_tests.xml' if all_tests else 'additional_paper_005_tests.xml'))]
    if '--pure-tests' in sys.argv:
        args += ['-k','not test_live_api_streaming_proposer']
    raise SystemExit(pytest.main(args))

import l1_symbol_game_governor as g
import llm_streaming_harness as h
import quickstart as q

def graph(weight=1):
    return g.ConstraintGraph(('a','b','c'),(g.Edge('a','b',weight),g.Edge('b','c',2),g.Edge('c','a',3)))

def governor():
    gov = g.L1SymbolGameGovernor(graph())
    for e in gov.graph.edges:
        assert gov.step_assert(*e.key,Q(1)).admitted
    return gov

def session(envelope=None, initial=None, weight=1):
    return h.SymbolGameStreamingSession(('a','b','c'),(('a','b',weight),('b','c',2),('c','a',3)),
        initial if initial is not None else {('a','b'):1,('b','c'):1,('c','a'):1},
        h.MockLLMStreamingProposer([envelope] if envelope is not None else []))

def cut(claims):
    return {'schema':'TAU_SG_V1','step_id':'probe','parent_step_id':'root','move_type':'CUT',
        'move_parameters':{'proposed_claims':claims}}

observations = []
for value in [True,0.1]:
    s = session(initial={('a','b'):value},weight=value)
    result = s.initialize()
    stored = s.governor.edge_claims[('a','b')]
    assert type(stored) is Q and stored == Q(value)
    observations.append({'id':'STREAM-INITIAL-TYPE-CONVERSION','input_type':type(value).__name__,
        'stored_claim':str(stored),'stored_weight':str(s.graph.edges[0].weight),'minimum':str(result),
        'outcome':'Float/Boolean initialization is converted before the governor exact-type guard.'})

s = session(initial={('outside','a'):9})
minimum = s.initialize()
assert minimum == 0 and not s.governor.edge_claims
assert len(s.history) == 1 and s.history[0]['action'] == 'ASSERT'
observations.append({'id':'STREAM-IGNORED-INITIAL-REFUSAL','minimum':str(minimum),
    'trace':s.history,'active_claims_empty':True,
    'outcome':'initialize discards the ASSERT verdict and records an ASSERT-shaped history row for refused undeclared input.'})

envelope = cut({'a,b':999,'a->b':-2,'b,c':1,'c,a':1})
envelope.update(schema='UNRELATED_SCHEMA',parent_step_id='nonexistent-parent',expected_defect_delta='invented')
s = session(envelope)
s.initialize()
verdict = s.run_turn('public synthetic control')
assert verdict['admitted'] and s.governor.edge_claims[('a','b')] == -2
observations.append({'id':'STREAM-EDGE-ALIAS-AND-UNBOUND-ENVELOPE','verdict':verdict,
    'accepted_normalized_claim':str(s.governor.edge_claims[('a','b')]),
    'outcome':'Conflicting aliases overwrite by insertion order; schema, parent and expected-delta fields do not gate admission.'})

parser = h.StreamingEnvelopeParser()
parser.append_chunk(h.LLMStreamChunk('{"move_type":"CUT","move_type":"VERIFY"}'))
parsed = parser.parse_envelope()
assert parsed == {'move_type':'VERIFY'}
observations.append({'id':'STREAM-DUPLICATE-JSON-KEY','parsed':parsed,'outcome':'The parser silently retains the last repeated JSON key.'})

for weight in [True,0.1]:
    gov = g.L1SymbolGameGovernor(graph(weight))
    asserted = gov.step_assert('a','b',Q(1))
    moved = gov.step_cut(proposed_section={'a':Q(0),'b':Q(1),'c':Q(0)})
    try:
        gov.primary_obstruction()
    except TypeError:
        norm_rejected = True
    else:
        norm_rejected = False
    assert asserted.admitted and norm_rejected
    observations.append({'id':'GOVERNOR-WEIGHT-GUARD-PATH','input_type':type(weight).__name__,
        'assert_admitted':asserted.admitted,'section_cut_status':moved.status,'minimum_call_refuses':norm_rejected,
        'outcome':'Construction and section-score path accept a weight that the quotient scorer rejects.'})

gov = g.L1SymbolGameGovernor(graph())
assert gov.step_assert('a','b',Q(1),step_id='same').admitted
assert gov.step_assert('a','b',Q(2),step_id='same').admitted
restored = gov.step_retract('same')
assert restored.admitted and gov.edge_claims[('a','b')] == 1
observations.append({'id':'GOVERNOR-DUPLICATE-SNAPSHOT-ID','matching_snapshot_ids':2,
    'restored_claim':'1','outcome':'Caller-supplied duplicate step IDs are admitted; RETRACT selects the first matching snapshot.'})

baseline_receipt = h.run_and_generate_receipt()
assert baseline_receipt['summary']['status'] == 'PASS_ALL_INVARIANTS'
failed = {'status':'VerificationFailed','admitted':False,'defect_before':'3','defect_after':'3'}
with patch.object(h.SymbolGameStreamingSession,'run_turn',return_value=failed):
    refused_receipt = h.run_and_generate_receipt()
assert refused_receipt['summary']['status'] == 'PASS_ALL_INVARIANTS'
assert all(not step['admitted'] for sc in refused_receipt['scenarios'] for step in sc['steps'] if 'admitted' in step)
observations.append({'id':'RECEIPT-HARDCODED-PASS','baseline_status':baseline_receipt['summary']['status'],
    'injected_all_refused_summary':refused_receipt['summary'],
    'outcome':'With in-memory refused turn results, summary and terminal success labels remain hard-coded. This tests receipt derivation, not native or provider behavior.'})

meeting = q.build_default_meeting_conflict()
qgraph, qclaims = meeting.to_graph_and_cochain()
potential = {'Alice':Q(0),'Bob':Q(1),'Charlie':Q(2)}
projected = q.compute_coboundary(potential,qgraph.edges)
wrong = q.Cochain1({edge.key:Q(0) for edge in qgraph.edges})
stdout = io.StringIO()
with patch.object(q,'compute_discrete_l1_projection',side_effect=[(Q(3),potential,projected),(Q(0),potential,wrong)]):
    with contextlib.redirect_stdout(stdout):
        exit_code = q.run_quickstart(interactive=False)
assert exit_code == 0 and 'VIOLATED' in stdout.getvalue() and 'CERTIFIED_EXACT_RATIONAL' in stdout.getvalue()
observations.append({'id':'QUICKSTART-FAILED-INVARIANT-SUCCESS','exit_code':exit_code,
    'idempotence':'VIOLATED','audit_status':'CERTIFIED_EXACT_RATIONAL',
    'outcome':'Mocked inconsistent second projection reports failed idempotence but returns success and prints certification. No native executable was called.'})

received_requests = []
class Response:
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def __iter__(self):
        return iter([b'data: {"choices":[{"delta":{"content":"{}"},"finish_reason":null}]}\n',
            b'data: {"choices":[{"delta":{},"finish_reason":"length"}],"usage":{"prompt_tokens":10,"completion_tokens":5}}\n'])
def transport(request,**kwargs):
    received_requests.append(json.loads(request.data))
    return Response()
with patch.object(h.urllib.request,'urlopen',side_effect=transport):
    chunks = list(h.LiveAPIStreamingProposer('https://invalid.example/not-called',api_key='synthetic-local-only').stream_proposal('public synthetic prompt'))
assert not any(c.is_terminal for c in chunks)
assert 'max_tokens' not in received_requests[0] and 'max_completion_tokens' not in received_requests[0]
observations.append({'id':'LIVE-LIMIT-USAGE-AND-FINISH','request_keys':sorted(received_requests[0]),
    'chunks':[vars(c) for c in chunks],
    'outcome':'No completion cap/reservation, usage discarded, and empty-delta finish_reason=length lost. Transport was an in-memory stub, no external request.'})

result = {'status':'all_declared_observations_reproduced','source_commit':scope['source_commit'],
    'source_pins':[r for r in scope['files'] if '/code/' in r['path'] and r['path'].endswith('.py')],
    'observations':observations,'provider_calls':0,'native_executions':0,'private_answer_access':False,
    'limits':'Public synthetic controls. Mocked dependency failure observations concern composition and report logic, not proof that a real native solver/provider emits those failures.'}
(OUT/'additional_paper_005_probes.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'observations':len(observations),'ids':sorted({x['id'] for x in observations}),'status':result['status']}))
