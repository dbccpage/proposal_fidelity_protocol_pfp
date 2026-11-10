"""Bounded local SNF, chain and self-application countercontrols."""
import sys
sys.dont_write_bytecode=True
import ast,copy,hashlib,json
from dataclasses import dataclass
from enum import Enum,auto
from typing import Any,Dict,List,Sequence,Tuple
import additional_pfp_tests_remaining_audit as a
b='pfp/tests/normal_forms/'
p15=b+'test_tranche15_exact_homology_and_rust_seams.py';p16=b+'test_tranche16_mssn_reach_grammar_and_clean_arch.py'
selection={p15:['exact_bareiss_det','exact_smith_normal_form_with_multipliers','matrix_mult'],p16:['GodelOutcome','SimplicialCarrier','probe_self_application','verify_chain']}
nodes=[];bindings=[]
for p,names in selection.items():
    t=ast.parse('\n'.join(a.source(p)))
    for name in names:
        found=[x for x in ast.walk(t) if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name];assert len(found)==1
        nodes+=found;bindings.append({'path':p,'sha256':a.row(p)['sha256'],'name':name,'lines':[found[0].lineno,found[0].end_lineno]})
ns={'dataclass':dataclass,'Enum':Enum,'auto':auto,'Any':Any,'Dict':Dict,'List':List,'Sequence':Sequence,'Tuple':Tuple,'__name__':__name__}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<read-vetted exact local helpers>','exec'),ns)
M=[[2,0],[0,3]]
diags,P,Q=ns['exact_smith_normal_form_with_multipliers'](M)
PAQ=ns['matrix_mult'](ns['matrix_mult'](P,M),Q)
assert diags==[2,3] and diags[1]%diags[0]!=0 and PAQ==M
assert abs(ns['exact_bareiss_det'](P))==abs(ns['exact_bareiss_det'](Q))==1
assert ns['exact_bareiss_det']([[0,1],[1,0]])==-1
records=[];prev='sha256:'+'0'*64
for i in range(5):
    body={'seq':i,'carrier':'synthetic','prev':prev}
    d='sha256:'+hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
    records.append({'body':body,'digest':d,'prev':prev});prev=d
verify=ns['verify_chain'];assert verify(records) and not verify(records[1:])
tail=verify(records[:-1]);tampered=copy.deepcopy(records);tampered[-1]['body']['carrier']='changed-without-rehash'
body_accept=verify(tampered);assert tail and body_accept
carrier=ns['SimplicialCarrier'](['v0','v1'],[('v0','v1')])
calls=[]
def false_zero_oracle(c,h):calls.append(1);return {'harmonic_mass':0.0,'harmonic':{('v0','v1'):999.0}}
outcome,details=ns['probe_self_application'](carrier,{'v0':1.0,'v1':2.0},{('v0','v1'):999.0},false_zero_oracle,max_iterations=0)
assert outcome.name=='STABLE_FIXPOINT' and len(calls)==1 and details['trace']==[]
a.write('_probe11.json',{'runtime':sys.version,'bindings':bindings,'smith':{'input':M,'returned_diagonal':diags,'divisibility_holds':False,'P_det_abs':1,'Q_det_abs':1,'P_A_Q':PAQ,'correct_invariant_factors_by_gcd_and_determinant':[1,6],'new_bareiss_swap_control_correct':True},'chain':{'baseline_accepted':True,'head_cut_rejected':True,'tail_cut_accepted':tail,'last_body_changed_without_rehash_accepted':body_accept},'self_application':{'max_iterations':0,'oracle_calls':len(calls),'reported_mass':0,'supplied_harmonic_value':999,'outcome':outcome.name,'trace':details['trace']},'limits':['Only fully read test-local AST bodies; no pfp.ffi/native/production imports, ledger file reads or external services.','SNF input is fixed diagonal2x2, avoiding exploratory unbounded elimination.','Self-application control tests report binding, not any metamathematical theorem.']})
print('SNF divisibility, chain custody and self-application controls confirmed')
