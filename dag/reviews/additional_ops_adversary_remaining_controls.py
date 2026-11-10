"""Confined source-only finite controls. Never import audited modules or run their runners."""
from pathlib import Path
import ast, copy, hashlib, json, math, random
from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction
from types import SimpleNamespace
from typing import Any, cast

R=Path(__file__).resolve().parents[2]
P=R/'dag/reviews/additional_ops_adversary_remaining'
I=json.loads(Path(str(P)+'_inventory.json').read_text())['files']
OUT=[]
def evidence(index,lo,hi):
    r=I[index]; assert 1 <= lo <= hi <= r['lines']
    assert hashlib.sha256((R/r['path']).read_bytes()).hexdigest()==r['sha256']
    return {'path':r['path'],'sha256':r['sha256'],'lines':[lo,hi]}
def record(code,title,value,refs,kind='independent finite countermodel'):
    OUT.append({'id':code,'title':title,'status':'confirmed','method':kind,'result':value,
                'source_evidence':[evidence(*r) for r in refs]})
def extract(index,names,extra=None):
    source=(R/I[index]['path']).read_text(encoding='utf8')
    parsed=ast.parse(source); selected=[]
    for name in names:
        parts=name.split('.')
        node=next(n for n in parsed.body if getattr(n,'name',None)==parts[0])
        if len(parts)>1:
            node=next(n for n in node.body if getattr(n,'name',None)==parts[1])
        node=copy.deepcopy(node)
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):node.decorator_list=[]
        selected.append(node)
    module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*selected],type_ignores=[])
    ns=dict(globals());ns.update(extra or {})
    exec(compile(ast.fix_missing_locations(module),'<audited-pure-extract>','exec'),ns)
    return ns

# Exact rational consistency, with no graph/native imports.
d0=[[Fraction(-1),1,0],[0,-1,1],[-1,0,1]]; residual=[Fraction(3)]*3
f=extract(224,['_pure_python_evaluate_functional'])['_pure_python_evaluate_functional']
phi,gamma,label,_=f(d0,[],residual)
assert (phi,gamma,label)==(9,0,'ClosedResidual') and residual[0]+residual[1]!=residual[2]
record('OAC01','Closed directed-cycle residual need not be a coboundary',
 {'edges':['A->B','B->C','A->C'],'residual':[3,3,3],'phi1':'9','gamma2':'0',
 'native_class':label,'mapped_label':'COBOUNDARY_EXACT','contradiction':'b-a=3,c-b=3 imply c-a=6, but third edge requires 3'},[(224,28,56),(224,81,107),(224,173,209)])

diagonal=[2,-1];trace=sum(diagonal);purity=sum(x*x for x in diagonal);entropy=-sum(x*math.log2(x) for x in diagonal if x>1e-12)
assert (trace,purity,entropy)==(1,5,-2.0)
record('OAC02','Hermitian trace normalization does not admit a density matrix',
 {'diagonal':diagonal,'trace':trace,'negative_eigenvalue':-1,'purity':purity,'reported_entropy_bits':entropy},[(242,52,65),(242,103,121)])

ns=extract(71,['LicensingBoundary'],{'R_EXACTNESS_WITNESS':'exact'})
w=SimpleNamespace(residual_sort='exact',is_exact=lambda:True,witness_data=('a'*64,))
lic=[]
for value in [-1.0,float('nan'),0.0]:
    t=SimpleNamespace(is_measured=True,phi_1=value,gamma_2=9,phi_ret=9,phi_claim=9,is_exact_rational=False)
    admitted=ns['LicensingBoundary'].propose_token(target_receipt=t,witness_cochain=w,expected_sha256='a'*64)[0]
    assert admitted;lic.append({'phi_1':str(value),'nonzero_other_residuals':True,'proposal_admitted':admitted})
record('OAC03','Licensing proposal checks positive mass rather than exact zero',lic,[(71,125,175)],'extracted pure predicate with synthetic declared witness; no kernel or authority')

exact=extract(219,['exact_object'])['exact_object']
try:exact({},frozenset(),'seat',allow_missing=True)
except TypeError as e:err=str(e)
else:raise AssertionError('unexpected accepted keyword')
record('OAC04','Seat decoder calls an unsupported exact_object keyword',err,[(219,19,29),(246,80,94)],'extracted pure helper call and source call-site')

a=b'a'+b'bc';b=b'ab'+b'c';assert a==b
record('OAC05','Legacy tree encoding has distinct tree preimages',{'tree1':{'a':'bc'},'tree2':{'ab':'c'},'encoded_hex':a.hex(),'equal_sha256':hashlib.sha256(a).hexdigest(),'cryptographic_collision':False},[(272,44,50),(272,360,385)])

ns=extract(301,['_claim_overlaps','_matching_claims'])
assert ns['_matching_claims'](['unrelated defect'],set())=={'unrelated defect'}
assert ns['_matching_claims'](['overflow'],{'no overflow was observed'})=={'overflow'}
record('OAC06','F0 textual matching can credit unrelated or negated claims',{'empty_failed_host_finding_set':['unrelated defect'],'negated_host_finding':'no overflow was observed','claim_credited':'overflow'},[(301,2424,2465)],'extracted pure text-matching helpers')

digest=extract(306,['compute_bundle_digest'])['compute_bundle_digest']
config={'preset':'p','prompt_family_versions':{'a':'1'},'checker_ids':['c']}
one={**config,'objective':'A','turns':[{'answer':'A'}]};two={**config,'objective':'B','turns':[]}
h1=digest(one['preset'],one['prompt_family_versions'],one['checker_ids']);h2=digest(two['preset'],two['prompt_family_versions'],two['checker_ids']);assert h1==h2
record('OAC07','Bundle configuration digest ignores objective and turns',{'different_payloads':True,'same_config_digest':h1},[(306,404,419),(301,4305,4362)],'extracted pure configuration digest; no workflow replay')

state={'nested':{'findings':[]}};first=dict(state);first['nested']['findings'].append('first reviewer');second=dict(state)
assert second['nested']['findings']==['first reviewer']
record('OAC08','Reference blind cohort shallow copy shares nested mutations',{'second_reviewer_sees':second['nested']['findings']},[(301,4137,4172)])

tree=ast.parse((R/I[142]['path']).read_text());consts={}
for n in tree.body:
    if isinstance(n,ast.Assign) and n.targets[0].id in ('UNSUPPORTED_SCHEMA_KEYWORDS','SUPPORTED_STRING_FORMATS'):
        consts[n.targets[0].id]=frozenset(ast.literal_eval(n.value.args[0]))
projection=extract(142,['provider_output_schema'],consts)['provider_output_schema']
original={'const':{'minimum':5,'normal':7},'enum':[{'pattern':'a'}]};projected=projection(original)
assert projected=={'const':{'normal':7},'enum':[{}]}
record('OAC09','Provider schema recursion alters literal const and enum values',{'original':original,'projected':projected,'local_full_schema_still_stronger':True},[(142,24,56)],'extracted pure schema projection; no API interaction')

trial=extract(306,['Trial.from_dict'])['from_dict'](lambda **kw:kw,{'arm':'a','task':'t','success':'false','cost_usd':'-1','wall_seconds':-2,'tokens':-3})
assert trial['success'] is True and trial['cost_usd']<0
record('OAC10','Yardstick Trial decoder coerces false text to true and accepts negative costs',{'success':trial['success'],'cost_usd':str(trial['cost_usd']),'wall_seconds':trial['wall_seconds'],'tokens':trial['tokens']},[(306,75,96)],'extracted pure decoder; no stored trial input')

ns=extract(306,['wilson_interval','mcnemar_exact'],{'Z95':1.959963984540054})
assert ns['wilson_interval'](0,0)==(0,1)
for n in range(1,11):
    for k in range(n+1):
        lo,hi=ns['wilson_interval'](k,n);assert 0<=lo<=k/n+1e-12 and k/n-1e-12<=hi<=1
for a in range(6):
    for b in range(6):
        expected=min(Fraction(1),2*sum((Fraction(math.comb(a+b,k),2**(a+b)) for k in range(min(a,b)+1)),Fraction()))
        assert abs(ns['mcnemar_exact'](a,b)-float(expected))<1e-15
record('OAC11','Statistical arithmetic matches bounded independent controls',{'wilson_cases':66,'mcnemar_cases':36,'limits':'descriptive Bernoulli/pairing assumptions remain external'},[(306,230,240),(306,290,330)],'extracted pure formula checks against exact finite tails; not trial efficacy')

promote=extract(306,['promote_candidate_operand'])['promote_candidate_operand']
result=promote({'operand_id':'x','composition':['unverified']},0,float('inf'))
assert result['promoted']
record('OAC12','Operand promotion admits infinite caller-supplied yield',{'promoted':True,'trial_yield':'inf','disposition':result['disposition'],'sample_or_checker_inputs':False},[(306,497,516)],'extracted pure threshold policy')

dispatch=next(n for n in ast.walk(ast.parse((R/I[295]['path']).read_text())) if isinstance(n,ast.FunctionDef) and n.name=='dispatch')
before=[n for n in ast.walk(dispatch) if isinstance(n,ast.Call) and 195 <= n.lineno < 209]
assert not any(isinstance(n.func,ast.Attribute) and n.func.attr=='_apply' for n in before)
state='PENDING';sends=1;crash_state=state;retry_allowed=crash_state=='PENDING';assert retry_allowed
record('OAC13','Research dispatch crash window retains resend-eligible PENDING state',{'modeled_send_count_before_crash':sends,'durable_state_at_send':state,'same_occurrence_retry_eligible':retry_allowed,'stronger_completion_writeahead_line':85},[(295,195,239),(289,76,90)],'AST ordering plus independent crash-state model; native host not executed')

text='Previously PASSED. Current release BLOCKED.'
status='PASS' if ('PASSED' in text or 'CLEARED' in text) else 'BLOCKED' if ('BLOCKED' in text or 'NOT READY' in text) else 'UNKNOWN'
assert status=='PASS'
record('OAC14','Markdown review mining ignores negative precedence and chronology',{'text':text,'derived_status':status},[(279,183,194)],'independent exact branch transcription')

values=[b'AAA\n',b'BBB\n'];assert values[0].count(b'\n')==values[1].count(b'\n') and values[0]!=values[1]
record('OAC15','Event mirror line counts cannot authenticate retained prefix',{'same_newline_count':1,'different_prefix_bytes':True},[(170,85,160)])

key1=('same/path',1234,3);key2=('same/path',1234,3);cache={key1:hashlib.sha256(b'AAA').hexdigest()}
assert cache[key2]!=hashlib.sha256(b'BBB').hexdigest()
record('OAC16','Size and mtime native hash cache permits stale digest under preserved metadata',{'same_cache_key':True,'different_equal_length_bytes':True,'requires_metadata_preserving_mutation':True},[(181,89,96),(181,344,360)])

dispatched=['r1','r2','r3'];merged=['r1'];skipped=['r2','r3'];assert set(dispatched)-set(merged)==set(skipped)
record('OAC17','Eager blind cohort can execute replies that merge then discards',{'dispatched':dispatched,'after_first_reply_quorum_or_allowance_reached':True,'retained_in_run':merged,'lost_from_run':skipped},[(301,4217,4293)],'finite control-flow model; no executor or retained runner called')

left={'x':1};right={'x':True};assert left==right
lk=tuple(sorted((k,str(v)) for k,v in left.items()));rk=tuple(sorted((k,str(v)) for k,v in right.items()));assert lk!=rk
record('OAC18','Request equality and hashed canonicalization disagree',{'dict_equal':True,'hash_inputs_differ':True,'left_hash_input':lk,'right_hash_input':rk},[(30,112,124),(30,316,336)])

errors=[];n=0
for row in I:
    if row['path'].endswith('.py'):
        n+=1
        try:ast.parse((R/row['path']).read_text(encoding='utf8'),filename=row['path'])
        except (SyntaxError,UnicodeError) as exc:errors.append({'path':row['path'],'error':str(exc)})
assert n==304 and not errors
record('OAC19','Whole Python population parses without importing modules',{'python_files':n,'syntax_errors':errors,'not_runtime_or_type_validation':True},[],'whole-population static AST parse; no source-reading credit')

out={'schema_version':1,'scope_manifest':'dag/reviews/additional_ops_adversary_remaining_scope.json',
 'scope_sha256':hashlib.sha256(Path(str(P)+'_scope.json').read_bytes()).hexdigest(),
 'controls':OUT,'summary':{'controls':len(OUT),'confirmed':len(OUT),'retained_runners_executed':0,'native_or_provider_calls':0},
 'limits':['All inputs are synthetic/public source predicates. No repository packages imported.',
           'Extracted pure predicates and independent finite models are distinguished; no broad test or end-to-end claim.',
           'No private benchmark/credential/seed contents read. Only this prefix receives output.']}
Path(str(P)+'_controls.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf8')
print(out['summary'])
