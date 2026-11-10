"""Select reviewed historical AST bodies; prohibit environment/provider/process access."""
import ast
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
SOURCE=ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs/history_recovery/recovered_sources/run_genesis_suite.py'
raw=SOURCE.read_bytes();tree=ast.parse(raw.decode('utf-8-sig'))
names={'BudgetExceededError','BudgetGuard','DangerGate','ArtifactVerifier','parse_llm_json'}
nodes=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
assert {n.name for n in nodes}==names
access=[]
class UnboundPath:
    def __init__(self,parts=()):self.parts=parts
    def __truediv__(self,item):return UnboundPath(self.parts+(str(item),))
    def exists(self):access.append('/'.join(self.parts));return False
ns={'__name__':'historical_harness_selected_controls','MODEL_PRICING':(0.12,0.30),'GENESIS_REPO_PATH':UnboundPath(),'re':re,'json':json}
module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)]+nodes,type_ignores=[])
exec(compile(ast.fix_missing_locations(module),str(SOURCE),'exec'),ns)
rows=[]
for i in range(1,26):
    cid=f'G{i:02d}'
    for kind,payload in [('empty',{}),('wrong_task',{'challenge_id':'UNRELATED','relation':'CHECKED','formal_derivation_or_data':'not a proof'}),('unknown',{'status':'UNKNOWN'})]:
        result=ns['ArtifactVerifier'].verify_challenge(SimpleNamespace(challenge_id=cid),payload)
        assert result['verified'] is True
        rows.append({'challenge':cid,'input_kind':kind,'output':result})
g25=next(x for x in rows if x['challenge']=='G25')
assert 'confirmed 0 occurrences' in ' '.join(g25['output']['details'])
danger_inputs=[('I explicitly deny that this is identical to 19L57G1.',None),('A datum is a DDC letter.',None),('No mathematical claim.',{'relation':'CHECKED','formal_derivation_or_data':'nonsense'})]
danger=[{'text':text,'payload':payload,'result':ns['DangerGate'].audit(text,payload)} for text,payload in danger_inputs]
assert danger[0]['result'][0] is False and danger[1]['result'][0] is True and danger[2]['result'][0] is True
parsed=ns['parse_llm_json']('```json\n{"status":"SOLVED"}\n```')
assert parsed=={'status':'SOLVED'}
duplicate=ns['parse_llm_json']('{"status":"UNKNOWN","status":"SOLVED"}')
assert duplicate=={'status':'SOLVED'}
guard=ns['BudgetGuard'](ceiling_usd=0.000001)
reservation=guard.reserve('',1)
charged=guard.record(1_000_000,0,0.0,reservation)
assert guard.total_spent>guard.ceiling_usd
negative=ns['BudgetGuard'](ceiling_usd=0.1)
negative_cost=negative.record(-1000,0,0.0,0.0)
assert negative_cost<0
result={'source_sha256':hashlib.sha256(raw).hexdigest(),'selected_whole_AST_definitions':sorted(names),'artifact_results':rows,
        'external_access_log':access,'external_access_is_unbound_stub':True,'danger_controls':danger,'fenced_object':parsed,'duplicate_key_result':duplicate,
        'budget_controls':{'admitted_reservation':reservation,'recorded_charge':charged,'ceiling':guard.ceiling_usd,'post_charge_overrun_raised':False,'negative_usage_cost':negative_cost},
        'limits':['No full historical module import, environment read, provider request or subprocess.','Fixed historical price constants used solely to exercise arithmetic; not a current price quote.','Source-level harness falsifiers are not mathematical verification of the25 original tasks.']}
path=REV/'additional_paper_011_history_context_probes.json';path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==result['source_sha256']
print(json.dumps({'always_true_cases':len(rows),'danger_controls':len(danger),'parser_controls':2,'budget_controls':2,'source_unchanged':True}))
