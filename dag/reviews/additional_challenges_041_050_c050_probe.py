"""Independent bounded algebra checks and adversarial equational certificates."""
import sys,itertools,json,copy
sys.dont_write_bytecode=True
from additional_challenges_041_050_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c050_equational_theorem_proving.reference_solver.prover import prove_equational
from c050_equational_theorem_proving.judge_packet.exact_checker import check_solution
from c050_equational_theorem_proving.judge_packet.independent_checker import independent_check

V={'x','y','z','u','v','w'}
def isvar(x):return isinstance(x,str) and (x in V or len(x)>1 and x[0] in 'xyzuvw' and x[1:].isdigit())
def signature(case):
    funcs={};consts=set();variables=set()
    def term(t):
        if isinstance(t,str):
            (variables if isvar(t) else consts).add(t);return
        if not isinstance(t,list) or not t or not isinstance(t[0],str) or not 0<=len(t)-1<=2:raise ValueError('invalid term')
        f=t[0];arity=len(t)-1
        if f in funcs and funcs[f]!=arity:raise ValueError('inconsistent arity')
        funcs[f]=arity
        for a in t[1:]:term(a)
    if not isinstance(case.get('axioms'),list) or not isinstance(case.get('goal'),list) or len(case['goal'])!=2:raise ValueError('invalid equation envelope')
    for eq in case['axioms']+[case['goal']]:
        if not isinstance(eq,list) or len(eq)!=2:raise ValueError('invalid equation')
        for t in eq:term(t)
    return funcs,consts,variables
def ev(t,env,tables):
    if isinstance(t,str):return env[t]
    x=tables[t[0]]
    for a in t[1:]:x=x[ev(a,env,tables)]
    return x
def names(t):return {t} if isinstance(t,str) else set().union(*(names(a) for a in t[1:]))
def strict_model(case,a):
    try:
        funcs,consts,variables=signature(case);n=a['size'];tables=a['tables'];env=a['assignment']
        if type(n)!=int or not 1<=n<=8:return {'valid':False,'reason':'domain size'}
        for c in consts:
            if c not in env or type(env[c])!=int or not 0<=env[c]<n:return {'valid':False,'reason':'constant assignment'}
        def tablecheck(t,depth):
            if depth==0:return type(t)==int and 0<=t<n
            return isinstance(t,list) and len(t)==n and all(tablecheck(v,depth-1) for v in t)
        for f,arity in funcs.items():
            if f not in tables or not tablecheck(tables[f],arity):return {'valid':False,'reason':'operation table shape/type/closure','symbol':f}
        checked=0
        for l,r in case['axioms']:
            vs=sorted(x for x in names(l)|names(r) if isvar(x))
            for vals in itertools.product(range(n),repeat=len(vs)):
                e={**env,**dict(zip(vs,vals))};checked+=1
                if ev(l,e,tables)!=ev(r,e,tables):return {'valid':False,'reason':'axiom assignment','assignments_checked':checked}
        goalvars={x for t in case['goal'] for x in names(t) if isvar(x)}
        if any(x not in env or type(env[x])!=int or not 0<=env[x]<n for x in goalvars):return {'valid':False,'reason':'goal assignment'}
        l,r=case['goal'];return {'valid':ev(l,env,tables)!=ev(r,env,tables),'reason':'direct exhaustive finite model evaluation','assignments_checked':checked}
    except Exception as e:return {'valid':False,'reason':type(e).__name__}
def strict_proof(case,a):
    try:
        signature(case);curr=copy.deepcopy(case['goal'][0])
        def subst(t,s):return copy.deepcopy(s.get(t,t)) if isinstance(t,str) else [t[0]]+[subst(x,s) for x in t[1:]]
        for step in a['steps']:
            i=step['axiom'];p=step['pos'];s=step['subst'];d=step['dir']
            if type(i)!=int or not 0<=i<len(case['axioms']) or d not in ('lr','rl'):return {'valid':False,'reason':'step reference/direction'}
            l,r=case['axioms'][i];vs={x for x in names(l)|names(r) if isvar(x)}
            if not isinstance(s,dict) or any(x not in vs for x in s):return {'valid':False,'reason':'substitution binds nonvariable or absent variable'}
            l,r=(l,r) if d=='lr' else (r,l);sub=curr
            if not isinstance(p,list):return {'valid':False,'reason':'position'}
            for j in p:
                if type(j)!=int or not isinstance(sub,list) or not 0<=j<len(sub)-1:return {'valid':False,'reason':'position'}
                sub=sub[j+1]
            if sub!=subst(l,s):return {'valid':False,'reason':'match'}
            repl=subst(r,s)
            if p:
                parent=curr
                for j in p[:-1]:parent=parent[j+1]
                parent[p[-1]+1]=repl
            else:curr=repl
            if curr!=step['result']:return {'valid':False,'reason':'step result'}
        return {'valid':curr==case['goal'][1],'reason':'strict variable-only step replay'}
    except Exception as e:return {'valid':False,'reason':type(e).__name__}
def verdict(c,a):
    res=[]
    for f in (check_solution,independent_check):
        try:res.append(f(c,a))
        except Exception as e:res.append({'exception':type(e).__name__,'message':str(e)})
    return res
def main():
    out={}
    c={'case_id':'audit_constant_substitution','axioms':[['a','b']],'goal':['c','d']}
    a={'case_id':c['case_id'],'status':'SOLVED','kind':'PROOF','steps':[{'axiom':0,'dir':'lr','pos':[],'subst':{'a':'c','b':'d'},'result':'d'}]}
    model={'size':2,'tables':{},'assignment':{'a':0,'b':0,'c':0,'d':1}}
    out['constant_substitution']={'case':c,'answer':a,'owner_verdict':verdict(c,a),'independent_proof':strict_proof(c,a),'independent_refuting_model':strict_model(c,model),'model':model}
    c={'case_id':'audit_nonclosed_model','axioms':[[['f','x'],['f','x']]],'goal':[['f','a'],'a']}
    a={'case_id':c['case_id'],'status':'SOLVED','kind':'COUNTERMODEL','size':1,'tables':{'f':[1]},'assignment':{'a':0}}
    out['nonclosed_one_element_model']={'case':c,'answer':a,'owner_verdict':verdict(c,a),'independent':strict_model(c,a),'reason':'Any actual one-element algebra satisfies every equation; f(0)=1 is outside the domain.'}
    c={'case_id':'audit_violated_axiom','axioms':[[['f','x'],'x']],'goal':[['f','a'],'a']}
    a={'case_id':c['case_id'],'status':'SOLVED','kind':'COUNTERMODEL','size':2,'tables':{'f':[0,0]},'assignment':{'a':1}}
    out['secondary_ignores_axioms']={'case':c,'answer':a,'owner_verdict':verdict(c,a),'independent':strict_model(c,a)}
    c={'case_id':'audit_boolean_table','axioms':[[['f','x'],'x']],'goal':[['f','a'],'b']}
    a={'case_id':c['case_id'],'status':'SOLVED','kind':'COUNTERMODEL','size':2,'tables':{'f':[False,True]},'assignment':{'a':0,'b':1}}
    out['boolean_table']={'case':c,'answer':a,'owner_verdict':verdict(c,a),'independent':strict_model(c,a)}
    malformed={'case_id':'audit_integer_term','axioms':[],'goal':[17,17]};a={'case_id':malformed['case_id'],'status':'SOLVED','kind':'PROOF','steps':[]}
    out['malformed_integer_terms']={'case':malformed,'answer':a,'owner_verdict':verdict(malformed,a),'independent':strict_proof(malformed,a)}
    c={'case_id':'audit_negative_position','axioms':[['x','y']],'goal':[['f','a'],['g','a']]};a={'case_id':c['case_id'],'status':'SOLVED','kind':'PROOF','steps':[{'axiom':0,'dir':'lr','pos':[-1],'subst':{'x':'f','y':'g'},'result':['g','a']}]}
    out['secondary_negative_position']={'case':c,'answer':a,'owner_verdict':verdict(c,a),'independent':strict_proof(c,a),'limits':'Axiom x=y trivializes the theory; this isolates malformed proof-step acceptance, not a false theorem.'}
    unary=lambda x:[x,['f',x],['f',['f',x]]]
    modelchecks=0;primary_mismatch=0;secondary_mismatch=0;proofs=0;proof_bad=[]
    for l,r in itertools.product(unary('x'),repeat=2):
        for s,t in itertools.product(unary('a'),repeat=2):
            c={'case_id':'audit_unary','axioms':[[l,r]],'goal':[s,t]}
            p=prove_equational([(l,r)],(s,t),max_depth=2,max_nodes=100)
            if p:
                p['case_id']=c['case_id'];proofs+=1
                if not strict_proof(c,p)['valid'] or not all(v[0] for v in verdict(c,p)):proof_bad.append(c)
            for tbl in itertools.product(range(2),repeat=2):
                for av in range(2):
                    a={'case_id':c['case_id'],'status':'SOLVED','kind':'COUNTERMODEL','size':2,'tables':{'f':list(tbl)},'assignment':{'a':av}}
                    actual=strict_model(c,a)['valid'];v=verdict(c,a);modelchecks+=1
                    primary_mismatch+=v[0][0]!=actual;secondary_mismatch+=v[1][0]!=actual
                    if p and actual:proof_bad.append({'case':c,'refuting_model':a})
    out['bounded_unary_exhaustion']={'model_certificates':modelchecks,'primary_mismatches':primary_mismatch,'secondary_mismatches':secondary_mismatch,'proofs_replayed':proofs,'proof_failures':proof_bad,'limits':'Nine unary axioms and nine ground goals of depth at most two; all four two-element unary operations and two constant assignments. Not a general completeness proof.'}
    write('_c050_probes.json',out)
    print(json.dumps({k:{x:y for x,y in v.items() if x not in ('case','answer')} for k,v in out.items()},ensure_ascii=False))
if __name__=='__main__':main()
