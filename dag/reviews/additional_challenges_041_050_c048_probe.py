import sys,itertools,subprocess
sys.dont_write_bytecode=True
from additional_challenges_041_050_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c048_ternary_quadratic_forms.reference_solver.solver import solve
from c048_ternary_quadratic_forms.reference_solver.factorization import is_prime
from c048_ternary_quadratic_forms.reference_solver.hilbert_symbol import hilbert_symbol
from c048_ternary_quadratic_forms.judge_packet.exact_checker import check_solution
from c048_ternary_quadratic_forms.judge_packet.independent_checker import independent_check,independent_hilbert
def main():
    rows=[]
    def run(name,c,a=None):
        if a is None:a=solve(c)
        out=[]
        for f in(check_solution,independent_check):
            try:out.append(f(c,a))
            except Exception as e:out.append({'exception':type(e).__name__,'message':str(e)})
        rows.append({'name':name,'case':c,'answer':a,'results':out})
    c={'case_id':'probe','a':'1','b':'1','c':str(-2001**2)}
    run('small-axis-search misses obvious scaled point',c)
    run('independent supplied exact point',c,{'case_id':'probe','status':'SOLVED','kind':'RATIONAL_POINT','x':'2001','y':'0','z':'1'})
    run('bare OOS with malformed coefficient',{**c,'a':'bad'},{'case_id':'probe','status':'OUT_OF_SCOPE'})
    run('noncanonical decimal coordinates',c,{'case_id':'probe','status':'SOLVED','kind':'RATIONAL_POINT','x':'02001','y':'-0','z':'1'})
    checks=[]
    for u,w,p in itertools.product((-3,-2,-1,1,2,3),(-3,-2,-1,1,2,3),(2,3,5)):
        m=p**(4 if p==2 else 3); square_all={w*z*z%m for z in range(m)};square_units={w*z*z%m for z in range(m) if z%p}
        modular=any((x*x-u*y*y)%m in (square_all if x%p or y%p else square_units) for x in range(m) for y in range(m))
        h=hilbert_symbol(u,w,p);ih=independent_hilbert(u,w,p)
        checks.append({'u':u,'w':w,'p':p,'modulus':m,'primitive_modular_point':modular,'primary':h,'secondary':ih})
    composite=399165290221*798330580441
    code="import sys;sys.path.insert(0,"+repr(str(ROOT/'workflows/tasks/certified_challenges'))+");from c048_ternary_quadratic_forms.judge_packet.independent_checker import _independent_is_prime;print(_independent_is_prime(2305843009213693951))"
    try:r=subprocess.run([sys.executable,'-B','-c',code],capture_output=True,text=True,timeout=2);timing={'completed':True,'stdout':r.stdout}
    except subprocess.TimeoutExpired:timing={'completed':False,'timeout_seconds':2,'limits':'Bounded probe terminated; no final trial-division verdict inferred.'}
    write('_c048_probes.json',{'controls':rows,'primitive_modular_conic_checks':checks,'mismatches':[r for r in checks if (r['primary']==1)!=r['primitive_modular_point'] or r['primary']!=r['secondary']],'above_64bit_composite':{'n':composite,'factor1':399165290221,'factor2':798330580441,'primary_is_prime':is_prime(composite)},'large_prime_trial_division':timing,'only_at2_label_refuted':{'form':[1,1,-7],'symbol_at2':hilbert_symbol(7,7,2),'symbol_at7':hilbert_symbol(7,7,7)}})
    print([(r['name'],r['results']) for r in rows]);print('modular controls',len(checks),'MR composite',is_prime(composite),'timing',timing)
if __name__=='__main__':main()
