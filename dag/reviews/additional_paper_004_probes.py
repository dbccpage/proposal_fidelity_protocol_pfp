"""Finite public-input AST-isolated probes; no providers, native processes or source writes.

Only audited top-level stdlib imports, definitions and call-free constants load.
Bootstrap path discovery, optional imports and every __main__ block are omitted.
The only function-local ambient selection is compute_phi1's CORE graph pin;
remove that name in this child process so enumeration is selected.
"""
import ast
import dataclasses
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import sys
import types

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]; P='additional_paper_004'
BASE=ROOT/'papers/pfp/004_pfp_native_verification_and_evidence_custody/code'
os.environ.pop('CORE_FUNCTIONAL_GRAPH_BIN',None)
os.environ.pop('CORE_FUNCTIONAL_GRAPH_SHA256',None)
ALLOWED={'__future__','copy','sys','dataclasses','enum','fractions','pathlib','typing','hashlib','json','subprocess','time','collections','datetime','re'}
sources=[]
def load(name,extra=None):
    path=BASE/(name+'.py'); raw=path.read_bytes(); tree=ast.parse(raw.decode()); body=[]
    for n in tree.body:
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            modules=[n.module] if isinstance(n,ast.ImportFrom) else [x.name for x in n.names]
            assert all(x.split('.')[0] in ALLOWED for x in modules),modules
            body.append(n)
        elif isinstance(n,(ast.ClassDef,ast.FunctionDef)):
            body.append(n)
        elif isinstance(n,(ast.Assign,ast.AnnAssign)) and not any(isinstance(x,ast.Call) for x in ast.walk(n)):
            body.append(n)
    m=types.ModuleType(P+'_'+name);m.__file__=str(path);m.__dict__.update(extra or {});sys.modules[m.__name__]=m
    exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),str(path),'exec'),m.__dict__)
    sources.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'loaded_top_level_ranges':[[n.lineno,n.end_lineno] for n in body]})
    return m

results=[]
def run(name,fn):
    try:
        detail=fn();results.append({'id':name,'status':'observed','detail':detail})
    except Exception as e:
        results.append({'id':name,'status':'probe_error','exception':type(e).__name__,'detail':str(e)})

g=load('l1_symbol_game_governor')
def triangle(isolated=False):return g.ConstraintGraph(vertices=('a','b','c','z') if isolated else ('a','b','c'),edges=(g.Edge('a','b',1),g.Edge('b','c',2),g.Edge('c','a',2)))
def normalization():
    graph=triangle();edge=g.Cochain1(values={e:Fraction(1) for e in graph.edges});tup=g.Cochain1(values={e.key:Fraction(1) for e in graph.edges})
    a,_=g.compute_phi1(graph,edge);b,_=g.compute_phi1(graph,tup)
    assert a==0 and b==3
    return {'edge_keyed_phi':str(a),'tuple_keyed_phi':str(b),'independent_cycle_lower_bound':'3'}
run('edge_key_normalization',normalization)
def nan_cut():
    gov=g.L1SymbolGameGovernor(triangle()); v=gov.step_cut(proposed_section={'a':float('nan'),'b':0,'c':0})
    assert v.admitted and str(v.defect_after)=='nan'
    return {'admitted':v.admitted,'status':v.status,'defect_after':str(v.defect_after),'stored_nonfinite':str(gov.section['a'])}
run('nan_section_cut',nan_cut)
def unknown_edge():
    gov=g.L1SymbolGameGovernor(triangle());v=gov.step_verify('EDGE_MATCH:x,y')
    assert v.admitted and v.status=='Verified'
    return dataclasses.asdict(v)
run('undeclared_edge_verify',unknown_edge)

l=load('interactive_lean4_governor')
def fake_proof():
    class NeverVerifier:
        def __getattr__(self,name):raise AssertionError('Verifier accessed: '+name)
    gov=l.SymbolGameHostGovernor(verifier=NeverVerifier());v=gov.evaluate_step([l.ProofGoal(goal_id='false',target_type='False')],0,l.TacticProposal(tactic_str='exact arbitrary',goal_id='other',rule_name='unrelated'),lean_context='theorem impossible : False := by')
    assert v.accepted and v.defect_after==0
    return dataclasses.asdict(v)
run('unchecked_false_proof',fake_proof)

s=load('l1_sparsity_bullshit_benchmark')
def landing_only():
    task=s.build_heldout_dataset()[0]; altered=task.sparse_response.replace('17 mod 5 = 2','17 mod 5 = 999'); v=s.deterministic_host_replay(task,altered,True)
    assert v[0]
    return {'accepted_wrong_intermediate':v,'original_expected':task.expected_result,'changed_arithmetic':altered!=task.sparse_response}
run('stored_answer_replay',landing_only)
def s3():
    def compose(a,b):return tuple(a[b[i]] for i in range(3))
    a=(1,0,2);b=(0,2,1);left=compose(compose(a,b),a);right=compose(b,a)
    assert left!=right
    return {'s1_s2_s1':left,'s2_s1':right,'conclusion':'different permutations; not a convention-sensitive equality'}
run('s3_fixture_arithmetic',s3)

p=load('packet_firewall_host')
def output_carrier():
    initial='a';out='\U0001f47e';h=lambda v:hashlib.sha256(v.encode()).hexdigest()
    step=p.DerivationStep(op='CUT',position=0,rule_id='R',substitution={},pre_state_hash=h(initial),post_state_hash=h(out),content='CUT a')
    host=p.PacketFirewallHost();v=host.evaluate_pipeline(initial,step,{'R':{}},lambda *args:out)
    assert v.admitted and not host.check_fw_payload_carrier(out).admitted
    return {'admitted':v.admitted,'rule_has_price':False,'output_separate_carrier_check':False}
run('firewall_output_and_price',output_carrier)

d=load('conversational_repair_dag')
def hidden_event():
    dag=d.ConversationalRepairDAG();dag.events['fake']=d.Event('fake',d.EventType.PROMPT,'unhashed',{},());v=dag.verify_integrity()
    assert v.ok and not dag.events['fake'].is_consistent()
    return dataclasses.asdict(v)
run('dag_index_omission',hidden_event)

r=load('arity_rewrite_engine')
def orbit_normal():
    system=r.RewriteSystem([r.Rule('b_to_c','b','c')],[{'a':'b','b':'a','c':'c'}]);normal,steps,done=system.reduce_to_normal_form('a',modulo_group=True);reachable,complete=system.reach('a',modulo_group=True)
    assert done and normal=='a' and 'c' in reachable
    return {'reported_normal':normal,'terminated':done,'reachable':sorted(reachable),'reach_complete':complete}
run('quotient_normal_form',orbit_normal)

landing=load('l1_sparse_landing',{'ConstraintGraph':g.ConstraintGraph,'Edge':g.Edge,'Cochain1':g.Cochain1,'solve_phi1_lp_exact_basis':g.compute_phi1})
def isolated_vertex():
    target={e.key:Fraction(1) for e in triangle().edges};base=landing.certify_unique_landing(triangle(),target);iso=landing.certify_unique_landing(triangle(True),target)
    assert base.unique and not iso.unique
    return {'connected':dataclasses.asdict(base),'isolated_vertex':dataclasses.asdict(iso),'independent_reason':'Isolated vertex adds a free potential coordinate and no residual coordinate; residual uniqueness is unchanged.'}
run('isolated_vertex_uniqueness',isolated_vertex)

def finite_witness():
    edges=[(0,1),(1,2),(2,0),(1,3),(3,0)];c=[3,2,2,1,1];f=[0,-2,-2,-1];y=[1,1,1,0,0]
    df=[f[v]-f[u] for u,v in edges];res=[a-b for a,b in zip(c,df)];div=[sum(y[j]*((v==i)-(u==i)) for j,(u,v) in enumerate(edges)) for i in range(4)]
    assert div==[0]*4 and sum(abs(x) for x in res)==sum(a*b for a,b in zip(y,c))==7
    assert [sum(c[j] for j in face) for face in [(0,1,2),(0,3,4)]]==[7,5]
    return {'potential':f,'coboundary':df,'residual':res,'dual':y,'divergence':div,'matching_primal_dual':7,'face_sums':[7,5],'gamma2':12,'zero_not_gauge_equivalent':True}
run('four_vertex_exact_witness',finite_witness)

report={'source_receipts':sources,'method':'AST-isolated audited definitions and stdlib imports; source module bootstrap omitted, native graph pin removed in child process. Finite synthetic public inputs only. No full module import or end-to-end equivalence claim.','results':results,'provider_calls':0,'native_processes':0,'production_writes':0}
(HERE/(P+'_probe_results.json')).write_text(json.dumps(report,indent=2,default=str,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps(results,default=str,ensure_ascii=False,indent=2))
