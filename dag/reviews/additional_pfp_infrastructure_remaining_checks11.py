"""Offline exact source-declaration countermodels; no host/provider execution."""
import collections,fractions,hashlib,itertools,json,pathlib,re,sqlite3,sys
import yaml,jsonschema
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];pins={};out=[]
def src(i):
 f=fs[i];b=(R/f['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==f['sha256'];pins[f['path']]=f['sha256'];return b.decode('utf-8')
def rec(k,ok,detail):
 assert ok,detail
 out.append({'id':'PFPINFRA-P'+k,'status':'reproduced','detail':detail})
F=fractions.Fraction
# Execute only the reviewed fixed INSERT statement in an in-memory empty SQLite DB.
rel=yaml.safe_load(src(527));statement=next(x for x in rel['canonical_example']['prompt'].splitlines()if x.startswith('INSERT'));db=sqlite3.connect(':memory:');db.execute('CREATE TABLE prompt_spans(slot TEXT, role TEXT, text TEXT) STRICT')
try:db.execute(statement);error=None
except sqlite3.Error as e:error=str(e)
rec('059',error is not None,{'sqlite_version':sqlite3.sqlite_version,'statement':statement,'error':error,'scope':'Canonical example claims sqlite_strict_text_set_v1; PostgreSQL ::text is invalid SQLite syntax.'});db.close()
sym=yaml.safe_load(src(529));pat=sym['specification']['fields']['wire']['pattern'];wire='<<p><v1><< ><s0>>>'
rec('060',re.fullmatch(pat,wire)is not None,{'pattern':pat,'accepted_wire':wire,'scope':'Space passes declared regex despite stated strict alphabet; full boundary parser may separately reject.'})
bad=[]
for i in [522,523,524,525]:
 d=yaml.safe_load(src(i));sid=d['canonical_example']['source_id'];pattern=d['specification']['fields']['source_id']['pattern'];bad.append({'path':fs[i]['path'],'source_id':sid,'regex':pattern,'matches':re.fullmatch(pattern,sid)is not None})
rec('061',all(not x['matches']for x in bad),bad)
src(536);src(525);x=F(-3,2);y=F(21,8);z=(x*x+y*y)**2+18*(x*x+y*y)-8*(x**3-3*x*y*y)-27
rec('062',z!=0,{'claimed_cusp':[str(x),str(y)],'deltoid_polynomial_value':str(z),'negative_y_same':True,'scope':'Illustrative cusp violates related declared deltoid boundary; not a native verifier execution.'})
src(504);worlds=list(itertools.product([0,1],repeat=3));uniform={w:F(1,8)for w in worlds};correlated={w:F(int(w[0]==w[2]),4)for w in worlds}
def marginal(d,indices):
 r=collections.defaultdict(F)
 for w,p in d.items():r[tuple(w[i]for i in indices)]+=p
 return dict(r)
rec('063',uniform!=correlated and all(marginal(uniform,p)==marginal(correlated,p)for p in[(0,1),(1,2)]),{'cover':['AB','BC'],'uniform':[str(uniform[w])for w in worlds],'A_equals_C':[str(correlated[w])for w in worlds],'both_pair_marginals_uniform':True,'scope':'Acyclic consistent marginals have distinct global extensions; existence does not imply uniqueness.'})
rec('064',2*0==0,{'premises':'{Qi,Qj}=2 delta_ij H and Qi^2=0 over characteristic0','deduction':'i=j gives2 Qi^2=2 H, hence H=0','scope':'Roadmap conflates real supercharges with complex nilpotent supercharges; no nonzero Hamiltonian can satisfy both as written.'})
rec('065',2**257>2**256,{'argument':'More than2^256 admissible distinct serialized ledgers cannot inject into SHA256 outputs. Collision resistance is computational, not universal injectivity.','finite_matrix_CCR_boundary':'tr([Q,P])=0 whereas tr(i hbar I_n)=i hbar n !=0 for n>0,hbar!=0. Finite simplicial link set alone need not mean finite-dimensional operator carrier; roadmap must specify infinite-domain or truncated CCR.'})
s=yaml.safe_load(src(508));jsonschema.Draft202012Validator(s).validate({});r=yaml.safe_load(src(509));sample={'pilot_id':'p','request_id':'r','trial_status':'COMPLETED','sanitization':{'fence_stripped':False,'is_valid_json':True,'structure_leakage_debt_chars':0},'evaluation':{'checker_id':'x','expected':1,'received':1,'status':'ACCEPTED'},'receipt':{}};jsonschema.Draft202012Validator(r).validate(sample)
sample['receipt']={'provider_calls':-1,'cost_microusd':-1,'usage':{'prompt_tokens':-1,'completion_tokens':-1,'total_tokens':999}};jsonschema.Draft202012Validator(r).validate(sample)
rec('066',True,{'comparison_empty_object_valid':True,'completed_accepted_response_without_raw_reply_empty_receipt_valid':True,'negative_calls_cost_tokens_and_inconsistent_total_valid':True,'scope':'Schema boundary only; no claim actual host accepts invalid receipts.'})
s=yaml.safe_load(src(578));sample={'stage':5,'name':'evaluation','executor':'host','requires':[2,4],'version':'1','derived_under_policy':'SPK-001','authority_effect':'None','source_template':'t','system_prompt':'s','user_prompt':'u','input_contract':{'preserve_original_seed':False,'retain_stage_2_candidates':False,'candidate_source_stage':99,'independent_checker_required':False}};jsonschema.Draft202012Validator(s).validate(sample)
rec('067',True,{'schema_valid_stage5':sample,'scope':'x-slot fixed annotations do not enforce true safety flags or source stage2; runtime validation may add constraints.'})
q=json.loads(src(30));records=[]
for case in q['cases']:
 terms=case['terms'];pairs=[]
 assert all(len(t['pauli'])==case['num_qubits']and set(t['pauli'])<=set('IXYZ')and F(t['weight'])>0 and t['target_sign']in[-1,1]for t in terms)
 for a,b in itertools.combinations(terms,2):
  if sum(x!=y and x!='I'and y!='I'for x,y in zip(a['pauli'],b['pauli']))%2:pairs.append([a['pauli'],b['pauli']])
 records.append({'case_id':case['case_id'],'description':case['description'],'is_control':case['is_control'],'anticommuting_pair_count':len(pairs),'first_pair':pairs[:1]})
selected=[x for x in records if any(x['case_id'].startswith('q40_'+n+'_')for n in['07','18','23'])]
rec('068',len(selected)==3 and selected[0]['anticommuting_pair_count']>0 and selected[1]['anticommuting_pair_count']>0 and selected[2]['anticommuting_pair_count']==0,{'all40_word_lengths_alphabets_weights_signs_valid':True,'base_count':sum(not x['is_control']for x in records),'control_count':sum(x['is_control']for x in records),'contradictory_descriptions':selected,'all_case_commutation_census':records,'scope':'Exact Pauli parity calculation, not Hamiltonian eigenvalue/native test or provider measurement.'})
(H/(P+'_checks11.json')).write_text(json.dumps({'python':sys.version,'method':'Exact independent mathematical and declaration-schema probes. SQLite memory-only literal execution; JSON Schema local refs only. No production imports, providers, network, source edits or private material.','source_pins':pins,'outcomes':out},indent=2)+'\n');print(json.dumps({'controls':len(out),'reproduced':len(out),'q40':selected,'cusp_value':str(z)},indent=2))
