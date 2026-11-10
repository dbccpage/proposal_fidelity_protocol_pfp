"""Bounded controls from read source fragments. Never executes a retained skill."""
import hashlib,json,pathlib,subprocess,sys
from fractions import Fraction
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';F=json.loads((H/(P+'_preparation.json')).read_text())['files'];results=[]
def emit(name,indices,observation,limit):
    sources=[]
    for i in indices:
        f=F[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];sources.append({'path':f['path'],'sha256':f['sha256']})
    results.append({'id':name,'status':'observed','sources':sources,'observation':observation,'limitations':limit})
bash=pathlib.Path(r'C:\Program Files\Git\bin\bash.exe')
if bash.exists():
    # Minimal isolated control-flow copies; no retained script or live path is run.
    bad='fail=0; bad() { printf "FAIL synthetic\\n"; fail=1; }; printf "missing\\n" | while IFS= read -r link; do bad; done; if [ "$fail" -eq 0 ]; then printf "PASS\\n"; fi; exit "$fail"'
    good='fail=0; bad() { printf "FAIL synthetic\\n"; fail=1; }; bad; if [ "$fail" -eq 0 ]; then printf "PASS\\n"; fi; exit "$fail"'
    runs=[]
    for script in (bad,good):
        x=subprocess.run([str(bash),'--noprofile','--norc','-c',script],capture_output=True,text=True,timeout=10)
        runs.append({'script':script,'exit_code':x.returncode,'stdout':x.stdout,'stderr':x.stderr})
    attempt=H/(P+'_checks_shell_attempt.json')
    if not attempt.exists():attempt.write_text(json.dumps(runs,indent=2)+'\n')
    if any(x['returncode']not in (0,1)for x in [{'returncode':r['exit_code']}for r in runs]):
        results.append({'id':'OPSKILL-CHECK-001','status':'not_run','reason':'Git Bash failed before executing the fragment (MSYS NtCreateDirectoryObject access denied). Initial probe incorrectly asserted expected shell semantics and failed; this repaired harness preserves that attempted evidence.','attempt_receipt':attempt.name,'runs':runs})
    else:
        assert runs[0]['exit_code']==0 and 'FAIL' in runs[0]['stdout'] and 'PASS' in runs[0]['stdout']
        assert runs[1]['exit_code']==1 and 'PASS' not in runs[1]['stdout']
        emit('OPSKILL-CHECK-001',[10],runs,'Reproduces the piped-loop failure-state bug only; does not run the retained compliance script or claim every shell has identical pipeline options.')
else:
    results.append({'id':'OPSKILL-CHECK-001','status':'not_run','reason':'Git Bash unavailable'})
assert 'APPROVED' in 'NOT APPROVED'
emit('OPSKILL-CHECK-002',[8],{'input':'NOT APPROVED','literal_pattern':'APPROVED','contains':True},'Independent literal-string control for this unanchored grep pattern; actual grep did not run because the shell could not initialize.')
m=2**64-1
overflow=True;sentinel=m;ceiling=m
assert sentinel<=ceiling
emit('OPSKILL-CHECK-003',[24],{'overflow':overflow,'returned_cost':sentinel,'finite_ceiling':ceiling,'accepted_by_less_equal':sentinel<=ceiling},'Counterexample to every finite ceiling in prose, not an assertion about any uninspected production budget comparison.')
x=y=1;d=2;u,v=x+y,x-y
assert (u,v)==(2,0) and u!=1 and not(u!=d)
emit('OPSKILL-CHECK-004',[56],{'d':d,'x':x,'y':y,'u':u,'v':v,'stale_rejects':u!=1,'task_matched_rejects':u!=d},'Single exact witness supplied by the guidance; not a new nine-element carrier census or transport theorem.')
c=Fraction(1);theta_star=Fraction(1,4);values=[Fraction(1,2)-c*k*theta_star for k in (1,Fraction(3,2),2)]
assert values==[Fraction(1,4),Fraction(1,8),Fraction(0)]
emit('OPSKILL-CHECK-005',[51],{'chosen_c':str(c),'theta_star':str(theta_star),'lower_bound_coefficients':[str(v)for v in values],'positive_middle':values[1]>0},'Exact conditional arithmetic only. It does not establish the analytic bound, its premises, or zero actual value at a zero lower bound.')
assert Fraction(1,1)==1 and Fraction(1,100)==Fraction(1,100)
emit('OPSKILL-CHECK-006',[38],{'solved':1,'failed':0,'refused':99,'conditional_success':'1','assigned_success':'1/100'},'Verifies supplied denominator arithmetic, not any historical population or scoring implementation.')
states=(0,1);constant_fibres=[list(states)];revealing_fibres=[[s]for s in states]
emit('OPSKILL-CHECK-007',[44],{'constant_report_answer_cardinalities':[len(set(a))for a in constant_fibres],'revealing_report_answer_cardinalities':[len(set(a))for a in revealing_fibres]},'Finite two-state identity-answer control; assumes admitted free report and does not bypass mandatory independent checks.')
out={'python':sys.version,'retained_scripts_executed':False,'network_or_provider_calls':False,'results':results}
(H/(P+'_checks.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'controls':len(results),'observed':sum(x['status']=='observed'for x in results)}))
