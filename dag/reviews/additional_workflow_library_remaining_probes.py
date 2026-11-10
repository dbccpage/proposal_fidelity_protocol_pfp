"""Synthetic public-fixture controls; deny network/process/private-file access."""
import ast,copy,hashlib,json,sys,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
P=ROOT/'dag/reviews/additional_workflow_library_remaining'
def barrier(event,args):
    if event.startswith('socket.connect') or event in ('subprocess.Popen','os.system'):
        raise RuntimeError('AUDIT_EXTERNAL_EXECUTION_DENIED:'+event)
    if event=='open' and isinstance(args[0],(str,bytes)):
        s=str(args[0]).replace('\\','/').lower()
        if '.benchmark_private' in s or 'dag/benchmark/seed_prompt.txt' in s or s.endswith('/.env'):
            raise RuntimeError('AUDIT_PRIVATE_READ_DENIED')
sys.addaudithook(barrier)
from pfp.workflows.wf0003 import workflow,runner
from pfp.workflows.wf0003.tests import test_wf0003 as fixtures
from jsonschema import Draft202012Validator
import yaml
spec=json.loads(workflow.resource_text('examples/integer_sum.task.json'))
results={'mode':'synthetic_offline_public_fixtures','provider_calls':0,'native_builds':0,'probes':[]}
answer=fixtures.mining_answer();answer['operad_candidates'][0]['operation']='Output the result thirty eight.'
for row in answer['l2_guidance']:row['guidance']='Return thirty eight as the total.'
turn=workflow.MiningContract.prepare_task(spec)
raw=fixtures.reply(turn,answer);checked=workflow.MiningContract.check_reply(spec,raw)
screen=workflow.screen_mining(spec,raw,checked)
results['probes'].append({'id':'word_encoded_answer','schema_valid':checked['schema_valid'],'screen_accepted':screen['accepted'],'errors':screen['errors'],'answer':answer})
assert checked['schema_valid'] and screen['accepted']
digit=copy.deepcopy(answer);digit['operad_candidates'][0]['operation']='Output the result 38.'
dr=fixtures.reply(turn,digit);dc=workflow.MiningContract.check_reply(spec,dr);ds=workflow.screen_mining(spec,dr,dc)
results['probes'].append({'id':'decimal_answer_negative_control','screen_accepted':ds['accepted'],'errors':ds['errors']})
assert not ds['accepted']
# Compile only the already fully read fixture factory, changing its local synthetic
# billed observation and ledger filename. No production byte is changed.
tree=ast.parse(Path(fixtures.__file__).read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='factory_for')
class Alter(ast.NodeTransformer):
    def __init__(self,split=True):self.split=split
    def visit_Dict(self,n):
        if [getattr(k,'value',None) for k in n.keys]==['prompt','completion']:
            n.values=[ast.Constant('0'),ast.Constant('0.00000003')]
            return n
        return self.generic_visit(n)
    def visit_Constant(self,n):
        if type(n.value) is float and n.value==0.000001:return ast.copy_location(ast.Constant(0.000051),n)
        if self.split and n.value=='accounting.sqlite3':return ast.copy_location(ast.JoinedStr([ast.Constant('phase-'),ast.FormattedValue(ast.Name('tokens',ast.Load()),-1),ast.Constant('.sqlite3')]),n)
        return n
ns=dict(vars(fixtures));exec(compile(ast.fix_missing_locations(ast.Module(body=[Alter().visit(copy.deepcopy(fn))],type_ignores=[])),'<audit-modified-fixture-factory>','exec'),ns)
base=Path(str(P)+'_inspection');base.mkdir(exist_ok=True)
runroot=base/('split_ledger_'+uuid.uuid4().hex[:10]);calls=[]
summary=runner.run(spec,runroot,'fixture/model',ns['factory_for'](calls),budget_microusd=100)
results['probes'].append({'id':'split_phase_ledgers','run_path':str(runroot.relative_to(ROOT)).replace('\\','/'),'calls':len(calls),'status':summary.get('status'),'cost_usd':summary.get('cost_usd'),'declared_cap_microusd':100,'ledger_files':[x.name for x in runroot.glob('*.sqlite3')],'summary':summary})
Path(str(P)+'_probe_results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
assert len(calls)==2 and summary['status']=='HOST_ACCEPTED' and summary['cost_usd']>0.0001
ns2=dict(vars(fixtures));exec(compile(ast.fix_missing_locations(ast.Module(body=[Alter(False).visit(copy.deepcopy(fn))],type_ignores=[])),'<audit-shared-ledger-control>','exec'),ns2)
controlroot=base/('shared_ledger_'+uuid.uuid4().hex[:10]);controlcalls=[]
control=runner.run(spec,controlroot,'fixture/model',ns2['factory_for'](controlcalls),budget_microusd=100)
results['probes'].append({'id':'shared_ledger_negative_control','run_path':str(controlroot.relative_to(ROOT)).replace('\\','/'),'calls':len(controlcalls),'status':control.get('status'),'failure_class':control.get('failure_class')})
assert len(controlcalls)==1 and control['status']=='INFRASTRUCTURE_ERROR'
# Keep the schema's descriptive constraints separate from Python model validation.
schema=yaml.safe_load((ROOT/'workflows/library/pilot_estate/matrix/pilot_models.yaml').read_text())
controls=[('ParameterAxis',{'name':'x','values':[1.5]}),('TargetSelector',{'glob':'../../outside'}),('TokenUsage',{'prompt_tokens':2,'completion_tokens':3,'total_tokens':999})]
for name,value in controls:
    sub={'$ref':'#/$defs/'+name,'$defs':schema['$defs']};errors=list(Draft202012Validator(sub).iter_errors(value))
    results['probes'].append({'id':'generated_schema_'+name,'value':value,'accepted':not errors})
    assert not errors
# Independent public arithmetic and protected-bracket checks, no historical code.
task=json.loads((ROOT/'workflows/library/pilot_estate/evidence/pfp_app_integration_20261012/ide_handoff/task.json').read_text())
v=task['input']['vector'];actual=[sum(a*b for a,b in zip(row,v)) for row in task['input']['matrix']]
results['probes'].append({'id':'public_ide_dot_products','computed':actual,'expected_public_reply':[219,-89,-28],'matches':actual==[219,-89,-28]})
for i in range(5):
    p=ROOT/f'workflows/library/pilot_estate/results/pilot_{i:07d}/seed.yaml';x=yaml.safe_load(p.read_text());s=x['seed_prompt'];depth=0;minimum=0
    for ch in s:
        depth+=(ch=='<')-(ch=='>');minimum=min(minimum,depth)
    results['probes'].append({'id':f'historical_bracket_balance_{i}','final_depth':depth,'minimum_depth':minimum,'balanced':depth==0 and minimum>=0})
Path(str(P)+'_probe_results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({**results,'probes':[{k:v for k,v in r.items() if k not in ('answer','summary')} for r in results['probes']]},indent=2))
