"""Independently reconstruct public fixture outcomes; never call historical runners."""
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / 'papers/pfp/003_pfp_host_admitted_failure_detectors'
OUT = ROOT / 'dag/reviews'
source = PKG / 'demos/demo_3/results/live_openrouter_trial_receipt.json'
raw = json.loads(source.read_text())
manifest = yaml.safe_load((PKG / 'demos/demo_3/experiment_manifest.yaml').read_text())
fixtures = {f['id']: f for f in manifest['fixture_catalog']}

def verify(fixture, payload):
    kind, witness = payload['witness_type'], payload['witness']
    if kind == 'vertex_bits':
        matrix = fixture['matrix']
        return len(witness) == len(matrix) and all(type(x) is int and x in (0,1) for x in witness) and all(
            (-1)**(witness[i]+witness[j])*F(matrix[i][j]) <= 0
            for i in range(len(matrix)) for j in range(i+1,len(matrix)))
    if kind == 'odd_parity_cycle':
        matrix = fixture['matrix']
        return len(witness)>2 and witness[0]==witness[-1] and all(
            type(x) is int and 0 <= x < len(matrix) for x in witness) and all(
            F(matrix[a][b]) != 0 for a,b in zip(witness,witness[1:])) and sum(
            F(matrix[a][b]) > 0 for a,b in zip(witness,witness[1:])) % 2 == 1
    if kind in ('gauge_potential', 'separating_left_null_functional'):
        matrix = [[F(x) for x in row] for row in fixture['packet']['d0']]
        c = [F(x) for x in fixture['packet']['c1']]
        w = [F(x) for x in witness]
        if kind == 'gauge_potential':
            return len(w)==len(matrix[0]) and all(sum(a*b for a,b in zip(row,w))==v for row,v in zip(matrix,c))
        return len(w)==len(matrix) and all(sum(w[i]*matrix[i][j] for i in range(len(w)))==0
            for j in range(len(matrix[0]))) and sum(a*b for a,b in zip(w,c)) != 0
    if kind == 'partial_sign_reversing_path_involution':
        rows = {r['path_id']: (r['sign'],F(r['weight'])) for r in fixture['sectors']}
        if not set(witness) <= rows.keys(): return False
        if any(y not in witness or witness[y] != x or x==y or rows[x][0] != -rows[y][0]
               or rows[x][1] != rows[y][1] for x,y in witness.items()): return False
        return all(s*w >= 0 for x,(s,w) in rows.items() if x not in witness)
    raise AssertionError('Unexpected historical witness grammar')

rows=[]
for i,trial in enumerate(raw['trials']):
    expected_fuel=12
    prior=None
    step_results=[]
    for j,step in enumerate(trial['steps']):
        assert step['step_index']==j and step['arm']==trial['arm']
        assert prior is None or prior==step['prior_state_digest']
        expected_fuel-=1
        assert step['remaining_fuel']==expected_fuel
        prior=step['new_state_digest']
        candidates=[p['payload'] for p in step['moves_proposed'] if p['move_type']=='PROPOSE_WITNESS']
        assert len(candidates)==1
        valid=verify(fixtures[trial['fixture_id']],candidates[0])
        assert valid == (step['host_decision']=='SCOPED_CERTIFICATE')
        assert trial['call_log'][j]['host_decision']==step['host_decision']
        step_results.append(valid)
    assert trial['step_count']==len(trial['steps'])==len(trial['call_log'])
    assert trial['fuel_consumed']==12-expected_fuel and trial['remaining_fuel']==expected_fuel
    assert trial['final_state_digest']==prior
    rows.append({'trial_index':i,'fixture':trial['fixture_id'],'arm':trial['arm'],'seed':trial['seed'],
                 'witness_valid_by_step':step_results,'recorded_terminal':trial['final_exit']})
arm_stats={}
for arm in raw['arms']:
    trials=[t for t in raw['trials'] if t['arm']==arm]
    successes=sum(t['final_exit']=='SCOPED_CERTIFICATE' for t in trials)
    arm_stats[arm]={'n':len(trials),'recorded_successes':successes,'rate':successes/len(trials),
                    'mean_fuel':sum(t['fuel_consumed'] for t in trials)/len(trials)}
pD,pR=(arm_stats[a]['rate'] for a in ('D','R'))
se=math.sqrt(pD*(1-pD)/15+pR*(1-pR)/15)
acD,acR=16/17,10/17
acse=math.sqrt(acD*(1-acD)/17+acR*(1-acR)/17)
computed={'trial_count':len(rows),'call_count':sum(len(t['call_log']) for t in raw['trials']),
    'tokens':sum(sum(c['usage'].values()) for t in raw['trials'] for c in t['call_log']),
    'arm_statistics':arm_stats,'wald_ci':[pD-pR-1.96*se,pD-pR+1.96*se],
    'agresti_caffo_ci':[acD-acR-1.96*acse,acD-acR+1.96*acse]}
assert (computed['trial_count'],computed['call_count'],computed['tokens'])==(30,48,20382)
assert all(round(x,4)==y for x,y in zip(computed['wald_ci'],raw['effect_statistics']['ci95_wald']))
assert all(round(x,4)==y for x,y in zip(computed['agresti_caffo_ci'],raw['effect_statistics']['ci95_agresti_caffo']))
for i in range(10,30):
    a={k:v for k,v in raw['trials'][i].items() if k not in ('seed','receipt_sha256')}
    b={k:v for k,v in raw['trials'][i%10].items() if k not in ('seed','receipt_sha256')}
    assert a==b

# Actual public instructor worksheet, already fully read; no notebook runner import.
key=PKG/'_lev_examiner_theoretical_minimum_quiz/instructor_key.md'
worksheet=key.read_text().split('```python\n',1)[1].split('```',1)[0]
sys.path.insert(0,str(PKG/'code'))
sys.dont_write_bytecode=True
exec(compile(worksheet,str(key)+'::public_worksheet','exec'),{})
report={'status':'declared_finite_reconstructions_passed','computed_record_totals':computed,
    'independent_witness_checks':rows,'public_worksheet':'passed',
    'distinct_trials_after_omitting_seed_and_envelope_digest':10,
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'manifest_sha256':hashlib.sha256((PKG/'demos/demo_3/experiment_manifest.yaml').read_bytes()).hexdigest(),
    'provider_calls':0,'private_answer_access':False,
    'limits':['Validates public finite witness data against the separately supplied fixture manifest, not a historical provider execution or frozen runner identity.',
        'All seed repetitions are identical apart from seed/envelope hash. This observation does not by itself prove fabrication or statistical independence.',
        'Confidence intervals reproduce numerical formulas only; correlated fixture/seed repetitions and absent allocation/source/raw-prompt bindings prevent a causal treatment-effect claim.',
        'Current package and canonical missing-port routes are distinct from the historical terminal labels. No notebook or native package was executed.']}
(OUT/'additional_paper_003_historical_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'computed':computed,'step_witnesses':sum(len(r['witness_valid_by_step']) for r in rows),'public_worksheet':'passed'}))
