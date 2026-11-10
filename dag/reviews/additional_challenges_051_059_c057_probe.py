import sys,itertools,json,math,io,contextlib,importlib
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,write,file
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c057_sorting_network_synthesis.reference_solver import solve
from c057_sorting_network_synthesis.reference_solver.sorting_network import KNOWN_OPTIMAL
from c057_sorting_network_synthesis.judge_packet.exact_checker import check as primary
from c057_sorting_network_synthesis.judge_packet.independent_checker import independent_check as secondary
MISSING=object()
def explicit_binary(n,network):
    for bits in itertools.product((0,1),repeat=n):
        arr=list(bits)
        for i,j in network:arr[i],arr[j]=min(arr[i],arr[j]),max(arr[i],arr[j])
        if arr!=sorted(bits):return {'valid':False,'counterexample':bits}
    return {'valid':True,'vectors':2**n}
def assessment(c,a):
    try:
        if not isinstance(a,dict):return {'valid':False,'reason':'non-object answer'}
        n=c['n'];k=c['k']
        if type(n)is not int or n<4 or n>12:return {'valid':None,'reason':'outside bounded domain'}
        if a.get('status')=='SOLVED':
            net=a['network']
            if not isinstance(net,list) or any(not isinstance(p,(list,tuple)) or len(p)!=2 or any(type(x)is not int for x in p) or not 0<=p[0]<p[1]<n for p in net):return {'valid':False,'reason':'network schema'}
            constraints=len(net)<=k and net[:len(c['prefix'])]==c['prefix'] and not any(p in c['forbidden'] for p in net)
            return {'valid':constraints and explicit_binary(n,net)['valid'],'constraints':constraints,'binary':explicit_binary(n,net),'limits':'0-1 theorem assumes consistent min/max on a total order; no lower-bound conclusion.'}
        if a.get('status')=='UNKNOWN':
            code=a.get('code');info=(math.factorial(n)-1).bit_length()
            holds={'BOUND_BELOW_PREFIX_LENGTH':len(c['prefix'])>k,'BOUND_BELOW_INFORMATION_THEORETIC_LOWER_BOUND':k<info,'FORBIDDEN_ADJACENT_COMPARATOR':any(p[1]==p[0]+1 for p in c['forbidden'])}
            if code=='BOUND_BELOW_PROVEN_OPTIMAL_SIZE':return {'valid':None,'reason':'trusted published optimal-size table, not reconstructed here','code':code}
            return {'valid':holds.get(code,False),'proof_conditions':holds,'code':code}
        return {'valid':None,'reason':'scope rejection separately replayed by owner validators'}
    except Exception as e:return {'valid':False,'reason':type(e).__name__+': '+str(e)}
def evaluate(c,a=MISSING):
    try:a=solve(c) if a is MISSING else a
    except Exception as e:return {'solver_exception':type(e).__name__}
    verdict=[]
    for f in (primary,secondary):
        try:verdict.append(f(c,a))
        except Exception as e:verdict.append({'exception':type(e).__name__})
    return {'answer':a,'owner_verdict':verdict,'independent_certificate':assessment(c,a)}
def main():
    pairs=list(itertools.combinations(range(4),2));case={'case_id':'enumeration','n':4,'k':5,'prefix':[],'forbidden':[]};count=0;sorting=0;failures=[]
    for length in range(6):
        for net in itertools.product(pairs,repeat=length):
            truth=explicit_binary(4,net)['valid'];a={'case_id':'enumeration','status':'SOLVED','network':[list(p) for p in net]};p=primary(case,a)[0];s=secondary(case,a)[0];count+=1;sorting+=truth
            if p!=truth or s!=truth:failures.append({'network':net,'truth':truth,'verdicts':[p,s]})
    known=[{'n':n,'length':len(net),**explicit_binary(n,net)} for n,net in KNOWN_OPTIMAL.items()]
    controls={'non_object_case':evaluate(None),'unhashable_status':evaluate(case,{'case_id':'enumeration','status':[]})}
    runner=importlib.import_module('c057_sorting_network_synthesis.participant_packet.runner');original=runner.__file__;base=file('_c057_runner_fixture');(base/'examples').mkdir(parents=True,exist_ok=True);runner.__file__=str(base/'runner.py')
    tests=[{'input':case,'expected_output':{'status':'BANANA'}},{'input':{**case,'prefix':[[0,1]],'forbidden':[[0,2]]},'expected_output':{'status':'SOLVED','network':[list(p) for p in KNOWN_OPTIMAL[4]]}}]
    for i,payload in enumerate(tests):
        (base/'examples'/'case.json').write_text(json.dumps(payload),encoding='utf-8');out=io.StringIO()
        try:
            with contextlib.redirect_stdout(out):runner.main()
        except SystemExit as e:controls['runner_'+str(i)]={'exit_code':e.code,'stdout':out.getvalue(),'payload':payload}
    runner.__file__=original
    stale=ROOT/'workflows/tasks/certified_challenges/c057_sorting_network_synthesis/judge_packet/cases/c057_b01_unconstrained_n4.json'
    result={'enumerated_networks':count,'sorting_networks':sorting,'failures':failures,'known_networks_binary_checks':known,'controls':controls,'generator_first_legacy_path_exists':stale.exists(),'limits':'Positive network replay verifies construction, not minimality of stored sizes. Literature lower bounds remain trusted.'};write('_c057_probes.json',result);print(json.dumps(result))
if __name__=='__main__':main()
