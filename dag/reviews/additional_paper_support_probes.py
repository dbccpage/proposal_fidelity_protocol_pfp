"""Offline audit probes; write only the audit result alongside this file."""
import ast
import dataclasses
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from fractions import Fraction

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name('additional_paper_support_probe_results.json')
results = {'source_commit': '8050c66900899771766f33e8f5fdd200b7dd9120', 'provider_calls': 0, 'private_benchmark_access': False, 'probes': [], 'validation': []}

def module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

auth = module('audit_finite_auth', 'papers/non_pfp/014_finite_authority_and_non_terminal_computation/code/mod_finite_authority_core.py')
trace = auth.ProposalTrace('fabricated', '2+2', '5', Fraction(1))
gates = auth.GateStack(*([True] * 8))
witness = auth.TerminalWitness('invented-terminal', 'this is not a proof', '5')
results['probes'].append({'id': 'unverified-string-authority', 'result': auth.evaluate_halted_trace(trace, gates, witness).status.value, 'counterfeit_route': auth.detect_counterfeit_descent(trace, Fraction(0), gates, witness)[1].status.value, 'interpretation': 'Both functions label supplied claims AUTHORITY without checking arithmetic or the proof string. This is a gate-record simulator, not operational proof validation.'})
epk = auth.EvaluatedPathKernel(0, 0)
results['probes'].append({'id':'zero-penalty-discount', 'large_cost_kernel': str(epk.compute_kernel([dataclasses.replace(trace, cost=Fraction(10**12), residual_risk=Fraction(10**12))], lambda _: True))})
boundary = module('audit_boundary', 'papers/non_pfp/016_the_anomalon_boundary/code/mod_anomalon_boundary_core.py')
zero = boundary.CochainDefect('zero', Fraction(0), True, False, Fraction(0))
results['probes'].append({'id': 'zero-mass-nonexact', 'classification': zero.classify().value, 'interpretation': 'Direct constructor accepts a zero-norm nonexact cochain, impossible for the rational L1 model; matrix-derived analyze_defect does not make this error.'})
b = boundary.AnomalonBoundary('unrelated', Fraction(1), 1)
results['probes'].append({'id':'supplied-lift-witness', 'result': b.authorize_lift(boundary.LiftPreservationWitness('made-up-contract', 1, Fraction(1)))['status'], 'interpretation':'No carrier map or preservation equation is present to verify.'})
replay = module('audit_pfp017', 'papers/pfp/017_pfp_proposal_channels_and_internal_interventions/code/replay.py')
grafted = replay._operad_graft((('A',), 'B', (None,)), 0, ((), 'A', ()))
results['probes'].append({'id':'graft-arity', 'input_arity':1, 'nullary_child_arity':0, 'returned_profile_arity':len(grafted[0]), 'expected_operadic_substitution_arity':0})
l1 = module('audit_l1', 'papers/non_pfp/002_l1_obstruction_framework/code/mod_004_l1_obstruction_framework_core.py')
g = l1.DirectedGraph.cycle(3)
results['probes'].append({'id':'exact-kkt-controls', 'valid_concentrated_residual':l1.LocalPrimalDualIterator.is_kkt_fixed_point(g,[3,0,0],[0,0,0],[1,1,1]), 'invalid_dual_refused':not l1.LocalPrimalDualIterator.is_kkt_fixed_point(g,[3,0,0],[0,0,0],[0,0,0]), 'alternative_dominance':l1.LocalPrimalDualIterator.certificate_dominates(g,[3,0,0],[0,0,0],[1,1,1],[0,3,3])})
# Exercise only the receipt dataclasses; do not import the provider-capable tournament module.
rel = 'papers/pfp/020_pfp_frontier_research/code/adaptive_braid_tournament_demo.py'
tree = ast.parse((ROOT/rel).read_text(encoding='utf-8'))
chosen={'TournamentRoundResult','ProposerLeaderboardEntry','TournamentRunReceipt'}
nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in chosen]
ns={'dataclass':dataclasses.dataclass,'Fraction':Fraction,'Tuple':tuple,'hashlib':hashlib,'json':json}
exec(compile(ast.Module(body=nodes,type_ignores=[]),rel,'exec'),ns)
r=ns['TournamentRoundResult']('R',2,'hadamard_q1',Fraction(1),Fraction(2),'P','M',True,'accepted',1,Fraction(0),'source-digest')
t=ns['TournamentRunReceipt']('T',2,1,(Fraction(1),),('M',),(),(r,),'')
changed=dataclasses.replace(r,target_operation='unrelated-target',tolerance_epsilon=Fraction(999),gate_count=999,status_reason='fabricated')
t2=dataclasses.replace(t,round_results=(changed,))
results['probes'].append({'id':'receipt-omits-round-fields','digest_unchanged':t.canonical_digest()==t2.canonical_digest(),'changed_fields':['target_operation','tolerance_epsilon','gate_count','status_reason'],'interpretation':'The receipt digest does not bind all public round fields.'})
env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
test_python = str(ROOT / '.venv/Scripts/python.exe')
commands=[
 ['finite-authority-tests',[test_python,'-X','utf8','-B','-m','pytest','-q','-p','no:cacheprovider','--confcutdir=papers/non_pfp/014_finite_authority_and_non_terminal_computation/code/tests','papers/non_pfp/014_finite_authority_and_non_terminal_computation/code/tests/test_finite_authority.py']],
 ['boundary-tests',[test_python,'-X','utf8','-B','-m','pytest','-q','-p','no:cacheprovider','--confcutdir=papers/non_pfp/016_the_anomalon_boundary/code/tests','papers/non_pfp/016_the_anomalon_boundary/code/tests/test_anomalon_boundary.py']],
 ['operator-incidence-tests',[test_python,'-X','utf8','-B','-m','pytest','-q','-p','no:cacheprovider','--confcutdir=papers/non_pfp/004_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects/code/tests','papers/non_pfp/004_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects/code/tests/test_operator_incidence_dga.py']],
 ['pfp017-finite-only',[sys.executable,'-B','papers/pfp/017_pfp_proposal_channels_and_internal_interventions/code/replay.py','--finite-only']],
]
for name,cmd in commands:
    p=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
    results['validation'].append({'name':name,'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    OUT.write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'probes':results['probes'],'validation':[{k:v[k] for k in ['name','exit_code','stdout','stderr']} for v in results['validation']]},indent=2))

