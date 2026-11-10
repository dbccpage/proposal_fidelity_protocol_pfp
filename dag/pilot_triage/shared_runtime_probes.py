"""Offline source probes on invented public inputs; never load stored cases or run a CLI."""
from __future__ import annotations
import ast,copy,hashlib,importlib,importlib.util,json,math,socket,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; BASE=ROOT/'pilots/anomalon_woland'
sys.dont_write_bytecode=True
def denied(*a,**kw):raise RuntimeError('NETWORK_FORBIDDEN_IN_TRIAGE')
socket.create_connection=socket.getaddrinfo=denied
socket.socket.connect=socket.socket.connect_ex=socket.socket.sendto=denied
inventory=json.loads(Path(__file__).with_name('shared_runtime_inventory.json').read_text())
sources={s['path']:s['sha256'] for r in inventory for s in r['sources']}
def load(name,path):
    path=Path(path);rel=path.relative_to(ROOT).as_posix()
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sources[rel]
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def judges(root):
    name='_triage_'+root[:4]; p=types.ModuleType(name);p.__path__=[str(BASE/root)];sys.modules[name]=p
    p2=types.ModuleType(name+'.judge_packet');p2.__path__=[str(BASE/root/'judge_packet')];sys.modules[p2.__name__]=p2
    return [load(name+'.judge_packet.'+leaf,BASE/root/'judge_packet'/f'{leaf}.py') for leaf in ('exact_checker','independent_checker')]
rows=[]
def record(owner,probe,observed,expected,ceiling='pure_function_on_invented_public_input'):
    rows.append(dict(owner=owner,probe=probe,observed=observed,expected=expected,assertion_passed=observed==expected,ceiling=ceiling))
roots=[r['id'] for r in inventory]
checks={r:judges(r) for r in roots[:6]}
for i in range(5):
    root=roots[i];a,b=checks[root]
    fn='check_solution' if i<3 else 'check_exact';gn='check_solution' if i<3 else 'independent_check'
    if i==0:
        case=dict(case_id='public-triage',A=[['1']],b=['2'],c=['1']);answer=dict(case_id=case['case_id'],status='SOLVED',kind='OPTIMAL',x=['2'],y=['1'],value='2')
        bad=dict(answer,value='3')
    elif i==1:
        case=dict(case_id='public-triage',n=2,s=0,t=1,arcs=[[0,1,1]]);answer=dict(case_id=case['case_id'],status='SOLVED',value='1',flow=['1'],cut_S=[0]);bad=dict(answer,value='2')
    elif i==2:
        case=dict(case_id='public-triage',matrix=[['1','0'],['0','1']]);answer=dict(case_id=case['case_id'],status='SOLVED',kind='INVERTIBLE',det='1',adjugate=[['1','0'],['0','1']],inverse=[['1','0'],['0','1']]);bad=dict(answer,det='5',adjugate=[['5','0'],['0','5']])
    elif i==3:
        case=dict(case_id='public-triage',A=[['1','0'],['0','0']],b=['4','0']);answer=dict(case_id=case['case_id'],status='SOLVED',kind='CONSISTENT',x=['4','0'],rank=1,rank_rows=[0],rank_cols=[0],null_basis=[['0','1']],null_rows=[1]);bad=dict(answer,rank_rows=[True])
    else:
        case=dict(case_id='public-triage',cost=[['1','5'],['5','1']],sense='min');answer=dict(case_id=case['case_id'],status='SOLVED',kind='OPTIMAL',sigma=[0,1],u=['1','1'],v=['0','0'],value='2');bad=dict(answer,sigma=[False,True])
    f,g=getattr(a,fn),getattr(b,gn)
    record(root,'valid_certificate',[f(case,answer)[0],g(case,answer)[0]],[True,True])
    record(root,'targeted_invalid_certificate',[f(case,bad)[0],g(case,bad)[0]],[False,False])
    if i in (3,4):
        unknown=dict(answer,status='UNKNOWN')
        record(root,'unknown_status_with_valid_witness_first_vs_second',[f(case,unknown)[0],g(case,unknown)[0]],[True,False])
    if i==1:
        malformed=dict(case,arcs=[[0,1,1.9]])
        record(root,'nonintegral_capacity_is_truncated_by_both',[f(malformed,answer)[0],g(malformed,answer)[0]],[True,True])

root=roots[5];a,b=checks[root]
case=dict(case_id='public-null',schema={'t':{'id':'INTEGER'}},spec={'op':'select','from':'t','where':{'not':{'coalesce':['id',{'val':None}]}}},protected=[],test_databases=[{'t':[{'id':None}]}])
answer=dict(case_id='public-null',status='SOLVED',sql='SELECT id FROM t WHERE NOT COALESCE(id,NULL)',preflight_sql='SELECT 1 WHERE 0',null_ledger=[])
for label,c,r,expected in [
    ('null_boundary_valid',case,answer,[True,True]),
    ('empty_database_suite',dict(case,test_databases=[]),answer,[False,False]),
    ('read_boundary_delete',case,dict(answer,sql='DELETE FROM t'),[False,False]),
    ('wrong_empty_result_heading',case,dict(answer,sql='SELECT id AS wrong FROM t WHERE 0'),[False,False])]:
    record(root,label,[a.verify_candidate(c,r)[0],b.independent_check(c,r)[0]],expected)
textcase=dict(case,schema={'t':{'id':'TEXT'}},spec={'op':'select','from':'t','where':{'coalesce':['id',{'val':None}]}},test_databases=[{'t':[{'id':'abc'}]}])
textanswer=dict(answer,sql='SELECT id FROM t WHERE COALESCE(id,NULL)')
record(root,'text_coalesce_sqlite_vs_python_truth',[a.verify_candidate(textcase,textanswer)[0],b.independent_check(textcase,textanswer)[0]],[True,False])

kit=load('_triage_kit',BASE/'pilot_reply_kit.py')
r1=kit.Request('r','first instruction',{'public':'input'});r2=kit.Request('r','changed instruction',{'public':'input'})
record('pilot_reply_kit.py','source_hash_does_not_bind_instruction',r1.sha==r2.sha,True)
record('pilot_reply_kit.py','parse_accepts_nonfinite_constant',math.isnan(kit.parse('NaN')),True)
try:kit.parse('{"x":1,"x":2}'); duplicate=False
except ValueError:duplicate=True
record('pilot_reply_kit.py','duplicate_keys_rejected',duplicate,True)
pilot=kit.Pilot('public',0,'triage',(r1,),lambda request,x:x,lambda request,x:{'status':'CHECKED'},('CHECKED',))
record('pilot_reply_kit.py','missing_reply_not_run',pilot.evaluate([])['rows'][0]['status'],'NOT_RUN')

store=load('_triage_store',BASE/'sqlite_pilot_store.py')
dummy=store.SqlitePilotStore.__new__(store.SqlitePilotStore)
dummy.get_run=lambda _:types.SimpleNamespace(input_data={},output_data={},challenge_id='public',harness='PFP',outcome='UNTESTED')
record('sqlite_pilot_store.py','empty_checker_sequence_vacuously_passes',dummy.replay_run('synthetic',[])['all_passed'],True,'method_on_mock_record_no_database_created_or_opened')
record('sqlite_pilot_store.py','truthy_nonboolean_checker_accepted',dummy.replay_run('synthetic',[('bad',lambda c,a:('false','not boolean'))])['all_passed'],True,'method_on_mock_record_no_database_created_or_opened')

worker=load('_triage_worker',BASE/'judge_packet_audit/worker.py')
record('judge_packet_audit','contradictory_verdict_dictionary_priority',worker.normalize({'verdict':'ACCEPT','accepted':False})[0],'ACCEPT')
record('judge_packet_audit','integer_one_is_not_boolean_acceptance',worker.normalize(1)[0],'UNINTERPRETABLE')
leak=load('_triage_leak',BASE/'judge_packet_audit/leakage.py')
record('judge_packet_audit','id_token_leak_detected',leak.case_id_leak('trial-infeasible',{'x':1},['infeasible'])['names_own_answer'],['infeasible'])

# Extract exactly the pure functions/method under review, without running legacy
# imports, construction, configuration reads, or the receipt-writing self-test.
class Verdict:
    @staticmethod
    def create(*args):return dict(status=args[3],details=args[4])
env={'HypothesisVerdict':Verdict,'P0ItemResult':type('Sentinel',(),{})}
path=BASE/'certified_ladder/hypothesis_evaluator.py';tree=ast.parse(path.read_text())
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='CertifiedLadderEvaluator')
node=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_h0_gate_controls')
module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),node],type_ignores=[]);ast.fix_missing_locations(module);exec(compile(module,str(path),'exec'),env)
record('certified_ladder','incomplete_h0_record_retained',env[node.name](types.SimpleNamespace(hypotheses={}),[{}])['status'],'RETAINED','exact_AST_extracted_method_with_verdict_recorder_no_constructor_or_storage')
domain=ROOT/'pfp/domain/pilots/certified_ladder.py';tree=ast.parse(domain.read_text())
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='evaluate_h2')
module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),node],type_ignores=[]);ast.fix_missing_locations(module);exec(compile(module,str(domain),'exec'),env)
record('certified_ladder','nonmonotone_h2_curve_retained',env[node.name](None,{1:.9,3:.1,5:.2})['status'],'RETAINED','exact_AST_extracted_canonical_owner_function_with_verdict_recorder')
out={'schema':'pfp.shared-runtime-public-probes.v1','provider_calls':0,'stored_cases_or_observations_read':False,'checks':rows,'all_assertions_passed':all(r['assertion_passed'] for r in rows),'interpretation':'Assertions verify observed behavior, including known weaknesses; they do not certify the checkers.'}
Path(__file__).with_name('shared_runtime_probe_results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
