"""Additional small independent stage controls; no retained fixtures consumed."""
import sys,json,hashlib
sys.dont_write_bytecode=True
import additional_pfp_adapters_audit as a
D=a.ROOT/'pfp/infrastructure/adapters/mssn_research/checkers'
def stage(n):
    ns={'__name__':'audit_stage_'+str(n)}
    for p in (D/'preamble.py',D/f'stage_{n:03}.py'):exec(compile(p.read_text(encoding='utf8'),str(p),'exec'),ns)
    return ns
def digest(obj):return 'sha256:'+hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()
rows=[]
def run(n,name,p,expected,assessment):
    got=stage(n)['check'](p);assert got[0]==expected,(name,got)
    rows.append({'stage':n,'rule':name,'status':'observed','payload':p,'observed':list(got),'assessment':assessment})
src=[['x','2/1',digest({'id':'x','value':'2/1'})],['y','2/1',digest({'id':'y','value':'2/1'})]]
derived_digest=digest({'id':'z','value':'4/1'})
for op in ('sum','product'):
    run(83,'lineage_digest_omits_operation_'+op,{'sources':src,'derived':[['z',op,[[s[0],s[2]] for s in src],'4/1',derived_digest]]},'PASS','Different valid lineage operations share the identical derived record digest because only id/value are hashed; this digest does not bind the derivation.')
run(85,'principal_self_handoff_does_not_narrow',{'principal':'p','principal_scope':['read','write'],'handoffs':[['p','p',['read']]],'tasks':[['p','write']]},'PASS','Source prose allows self-handoff narrowing, but principal is specially exempted from updates and retains write. Other agents use last received scope.')
p={'bound':1,'source_symbols':{'R':1},'target_symbols':{'S':1,'R':1},'map':{'R':'S'},'source':{'prefix':'Ax','matrix':['rel','R','x']},'target':{'prefix':'Ax','matrix':['rel','R','x']}}
run(91,'unmapped_target_symbol_aliases_source_name',p,'PASS','Target R is outside the image of the declared map R->S. Fallback rename.get reads source R anyway. A target model with S true,R false and source R true refutes the resulting unqualified translation equivalence; target-only symbols have no explicit interpretation in the implementation.')
run(92,'initial_empty_clause_has_no_zero_step_refutation',{'claims':[{'cnf':[[]],'answer':'UNSAT','proof':[],'model':None}]},'REFUSED','CNF already contains the empty clause and is unsatisfiable, but kernel requires at least one resolution step. This is incompleteness of the allowed certificate format, not false SAT acceptance.')
corpus=[['case','synthetic']]
run(96,'chebyshev_condition_not_necessary',{'corpus':corpus,'corpus_digest':digest(corpus),'trials':[['case','success']],'estimate':{'successes':1,'count':1,'point':'1/1','half_width':'1/1','alpha':'1/10','interval':['0/1','1/1']}},'REFUSED','For n1 and half-width1 the clipped interval is always[0,1], so coverage is1 for every Bernoulli parameter. Condition1/(4*n*h*h)<=alpha fails and checker refuses. The Chebyshev inequality is a sufficient bound, not the claimed exact necessity.')
run(100,'open_tested_claim_absent_from_frontier',{'claims':['c'],'tests':['t'],'evidence':[['c','t']],'open':[['c','OPEN','unsolved obligation']],'frontier':[],'self_certification':'none','authority_effect':'None'},'PASS','An explicitly OPEN claim with a declared test is removed from the computed frontier; links are not evidence of proof. This contradicts prose that an open obligation cannot coexist with a complete frontier.')
a.write('_stage_probes2.json',{'method':'Unchanged fully read stage and preamble source executed directly; independent tiny payloads; no native/provider/private data access.','checks':rows,'source_hashes':{str(p.relative_to(a.ROOT)).replace('\\','/'):a.sha(p) for p in [D/'preamble.py']+[D/f'stage_{n:03}.py' for n in (83,85,91,92,96,100)]}})
print(json.dumps([{k:r[k] for k in ('stage','rule','observed')} for r in rows]))
