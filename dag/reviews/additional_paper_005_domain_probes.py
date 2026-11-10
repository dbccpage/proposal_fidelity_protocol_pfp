"""Actual offline graph bouts and independent receipt consistency controls."""
from pathlib import Path
from fractions import Fraction as Q
import contextlib
import hashlib
import io
import json
import os
import sys
from unittest.mock import patch
import code
import pdb

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'dag/reviews'
PACKAGE = ROOT/'papers/pfp/005_pfp_practitioners_field_manual'
scope = json.loads((OUT/'additional_paper_005_support_scope.json').read_text())
for row in scope['files']:
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest() == row['sha256']
os.environ.pop('CORE_FUNCTIONAL_GRAPH_BIN',None)
os.environ.pop('CORE_FUNCTIONAL_GRAPH_SHA256',None)
sys.dont_write_bytecode = True
sys.path.insert(0,str(PACKAGE/'code'))
import multi_domain_symbol_game_bouts as multi
import symbol_game_matolcsi_conjecture2 as mat
import symbol_game_r4_playground as r4
import symbol_game_toolkit as toolkit

observations = []
for trace in [[],[{'move':'invented'}]]:
    valid = multi.validate_bout_trace('invented-domain',trace)
    assert valid
    observations.append({'id':'VACUOUS-TRACE-VALIDATION','trace':trace,'accepted':valid,
        'outcome':'No required phase, domain, move vocabulary or completeness is established by this predicate.'})

stdout = io.StringIO()
mat_cemetery = mat.CemeteryDAGSink()
with contextlib.redirect_stdout(stdout), patch.object(mat,'CemeteryDAGSink',return_value=mat_cemetery):
    result = mat.run_symbol_game_matolcsi_conjecture2_bout()
log = stdout.getvalue()
verdict_lines = [line for line in log.splitlines() if 'Host Verdict on Bogus Zeroing' in line]
assert len(verdict_lines) == 1 and 'Admitted=True' in verdict_lines[0]
assert mat_cemetery.entries[0]['disposition'] == 'REFUSED_OBSTRUCTION_TAO_WITNESS'
assert result['final_phi1'] == '0'
observations.append({'id':'MATOLCSI-ACCEPTED-CUT-RECORDED-AS-REFUSED',
    'actual_host_line':verdict_lines[0],'cemetery_record':mat_cemetery.entries[0],
    'result':result,'outcome':'The actual graph accepts zeroing the edge, reducing obstruction nine to zero, while the script records a refusal and prints a pre-call antibody. No polynomial or antibody execution occurs.'})

stdout = io.StringIO()
r4_cemetery = r4.CemeteryDAGSink()
with contextlib.redirect_stdout(stdout), patch.object(r4,'CemeteryDAGSink',return_value=r4_cemetery):
    r4.run_symbol_game_r4_bout()
log = stdout.getvalue()
final_lines = [line for line in log.splitlines() if 'FINAL VERIFY:' in line or 'New Primary Obstruction' in line]
assert any('Admitted=False' in line for line in final_lines)
assert any('= 4' in line for line in final_lines)
assert r4_cemetery.entries[-1]['disposition'] == 'ACCEPTED_TERMINAL'
assert r4_cemetery.entries[-1]['defect_mass'] == '0'
observations.append({'id':'R4-FAILED-VERIFY-RECORDED-AS-ZERO-TERMINAL',
    'actual_host_lines':final_lines,'cemetery_terminal':r4_cemetery.entries[-1],
    'outcome':'Actual residual obstruction is four and VERIFY refuses, yet the stored terminal says accepted with zero danger. Setting one claim to zero does not remove its edge or close the cycle.'})

vertices = ['a','b','c']
edges = [('a','b',1),('b','c',1),('c','a',1)]
unadmitted = toolkit.run_to_terminal(vertices,edges,{('outside','a'):1})
assert unadmitted['terminal'] == 'ACCEPTED_ZERO_DEFECT'
assert unadmitted['trace'][0]['status'] != 'Asserted'
observations.append({'id':'TOOLKIT-REFUSED-ASSERT-ZERO-TERMINAL','result':unadmitted,
    'outcome':'An undeclared assertion is refused, but the empty admitted state is returned as accepted zero defect. Terminal must be interpreted relative to admitted state, not all requested claims.'})
claims = {('a','b'):1,('b','c'):1,('c','a'):1}
stopped = toolkit.run_to_terminal(vertices,edges,claims,max_cuts=0)
repaired = toolkit.run_to_terminal(vertices,edges,claims,max_cuts=1)
assert stopped['terminal'] == 'SURVIVOR_OBSTRUCTION' and stopped['final_phi1'] == '3'
assert repaired['final_phi1'] == '0'
observations.append({'id':'TOOLKIT-FUEL-IS-NOT-IRREDUCIBILITY','no_cuts':stopped,'one_cut':repaired,
    'outcome':'A configured zero-cut budget produces the survivor label even though one permitted replacement reaches zero.'})

stdout = io.StringIO()
with contextlib.redirect_stdout(stdout):
    metric, trace = multi.run_domain_2_distributed_deadlock(multi.UniversalCemeteryDAG())
assert metric.initial_phi == '4' and metric.intermediate_phi == '1' and metric.final_phi == '0'
observations.append({'id':'DEADLOCK-METRIC-NOT-EXECUTED-STATE','metrics':vars(metric),'trace':trace,
    'independent_replacement_distance':str(abs(Q(-3)-Q(1))*Q(1)),
    'outcome':'Declared intermediate one is not a measured state transition. Changing the weight-one claim from one to minus three has weighted L1 distance four, not candidate label one.'})

receipt = {'status':'all_declared_observations_reproduced','observations':observations,
    'source_commit':scope['source_commit'],'source_pins':[x for x in scope['files'] if x['path'].endswith(('symbol_game_matolcsi_conjecture2.py','symbol_game_r4_playground.py','multi_domain_symbol_game_bouts.py','symbol_game_toolkit.py','l1_symbol_game_governor.py'))],
    'provider_calls':0,'native_executions':0,'private_answer_access':False,
    'limits':'Actual Python fallback graph execution. In-memory constructor interception only exposes the unchanged cemetery instance; no solver or verdict was replaced. No external domain claims tested.'}
(OUT/'additional_paper_005_domain_probes.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'observations':len(observations),'status':receipt['status']}))
