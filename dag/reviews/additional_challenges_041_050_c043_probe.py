"""Independent finite colouring certificates and adversarial controls."""
import sys,json,itertools
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
from additional_challenges_041_050_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c043_ramsey_vdw_constructions.judge_packet.checkers.dual_evaluator import evaluate_dual
from c043_ramsey_vdw_constructions.reference_solver import algebraic_seeds as seeds

def independent(case,colors):
    n=case['n']; typ=case['type']
    if typ=='vdw':
        if len(colors)!=n or any(x not in ''.join(map(str,range(case['r']))) for x in colors):return False
        if any(colors[int(pos)]!=str(c) for pos,c in case.get('fixed',[])):return False
        k=case['k']
        return not any(len({colors[i] for i in inds})==1 for inds in itertools.combinations(range(n),k) if len({b-a for a,b in zip(inds,inds[1:])})==1)
    pairs=list(itertools.combinations(range(n),2)); mapping=dict(zip(pairs,colors))
    if len(colors)!=len(pairs):return False
    for f in case.get('fixed',[]):
        edge,col=(tuple(sorted(f[:2])),f[2]) if len(f)==3 else (pairs[int(f[0])],f[1])
        if mapping[edge]!=str(col):return False
    sizes={str(c):3 for c in range(3)} if typ=='ramsey3' else {'0':case['s'],'1':case['t']}
    if any(c not in sizes for c in colors):return False
    return not any(all(mapping[e]==c for e in itertools.combinations(vertices,2)) for c,size in sizes.items() for vertices in itertools.combinations(range(n),size))

def control(label,c,a):
    try: result=evaluate_dual(c,a)
    except Exception as e:result={'exception':type(e).__name__,'message':str(e)}
    return {'label':label,'case':c,'answer':a,'result':result}

if __name__=='__main__':
    counts={};failures=[]
    for typ,maxn,alphabet in [('ramsey2',5,'01'),('ramsey3',4,'012'),('vdw',9,'01')]:
        count=0
        for n in range(2,maxn+1):
            c={'case_id':'audit','type':typ,'n':n,'s':3,'t':3,'r':2,'k':3,'fixed':[]}
            length=n if typ=='vdw' else n*(n-1)//2
            for t in itertools.product(alphabet,repeat=length):
                colors=''.join(t); ok=independent(c,colors);result=evaluate_dual(c,{'status':'SOLVED','colours':colors})[0];count+=1
                if result!=ok:failures.append({'case':c,'colours':colors,'independent':ok,'owner':result})
        counts[typ]=count
    seed_checks=[]
    for name,n,r,k in [('vdw_seed_w23',8,2,3),('vdw_seed_w24',34,2,4),('vdw_seed_w25',80,2,5),('vdw_seed_w33',26,3,3)]:
        s=getattr(seeds,name)(n)
        seed_checks.append({'name':name,'requested_length':n,'actual_length':len(s),'independent_valid':independent({'type':'vdw','n':n,'r':r,'k':k},s)})
    seed_checks += [{'name':'Paley17','independent_valid':independent({'type':'ramsey2','n':17,'s':4,'t':4},seeds.paley_17_colouring())},{'name':'GreenwoodGleason16','independent_valid':independent({'type':'ramsey3','n':16},seeds.greenwood_gleason_16_colouring())}]
    c={'case_id':'audit','type':'ramsey2','n':3,'s':3,'t':3,'fixed':[[0,1,0],[0,2,0]]}
    controls=[control('duplicate_vertices_false_impossibility',c,{'status':'OUT_OF_SCOPE','witness':{'reason':'FIXED_COLOURS_CONTAIN_MONO','structure':[0,1,1]}}),
      control('same_case_valid_colouring',c,{'status':'SOLVED','colours':'001'}),
      control('conflicting_fixed_overwrite',{'case_id':'audit','type':'vdw','n':2,'r':2,'k':3,'fixed':[[0,0],[0,1]]},{'status':'SOLVED','colours':'10'}),
      control('missing_kind_and_wrong_id',{'case_id':'audit','type':'vdw','n':2,'r':2,'k':3,'fixed':[]},{'case_id':'wrong','status':'SOLVED','colours':'10'}),
      control('k_one_crash',{'type':'vdw','n':2,'r':2,'k':1,'fixed':[]},{'status':'SOLVED','colours':'10'}),
      control('malformed_drat_crash',{'type':'ramsey2','n':3,'s':3,'t':3,'fixed':[]},{'status':'OUT_OF_SCOPE','witness':{'reason':'PROVABLY_INFEASIBLE_SAT','drat_proof':['bad 0']}})]
    write('_c043_probes.json',{'exhaustive_coloring_controls':counts,'failures':failures,'algebraic_seed_checks':seed_checks,'controls':controls,
      'limits':['Finite certificate enumeration supplies lower-bound witnesses, not all advertised exact upper Ramsey/VDW numbers.','Infeasibility routes share C042 DRAT engine and C043 encoders.']})
    print(json.dumps({'counts':counts,'failures':len(failures),'seeds':seed_checks,'controls':[(r['label'],r['result'][0] if isinstance(r['result'],tuple) else r['result']) for r in controls]}))
