"""Offline independent group-table checks and adversarial envelopes."""
import sys,itertools,collections
sys.dont_write_bytecode=True
from additional_challenges_041_050_audit import ROOT,read,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c044_finite_group_identification.judge_packet.checkers.dual_evaluator import evaluate_dual
from c044_finite_group_identification.reference_solver.solver import solve,get_catalog

def independent(t):
    n=len(t)
    closed=all(len(row)==n and all(type(x)==int and 0<=x<n for x in row) for row in t)
    if not closed:return {'valid_group':False,'closed':False}
    ident=all(t[0][i]==i==t[i][0] for i in range(n))
    inv=all(any(t[i][j]==0==t[j][i] for j in range(n)) for i in range(n))
    assoc=all(t[t[i][j]][k]==t[i][t[j][k]] for i,j,k in itertools.product(range(n),repeat=3))
    orders=[]
    for x in range(n):
        y=0
        for k in range(1,n+1):
            y=t[y][x]
            if y==0:orders.append(k);break
    center=sum(all(t[x][y]==t[y][x] for y in range(n)) for x in range(n))
    return {'valid_group':ident and inv and assoc,'order':n,'centre_order':center,'element_order_histogram':dict(collections.Counter(map(str,orders)))}

def main():
    c={'case_id':'probe','task':'IDENTIFY','presentation':'table','table':[[0,1],[1,0]],'order':2,'gens':[1]}
    rows=[]
    def check(name,case,answer):
        try:out=evaluate_dual(case,answer)
        except Exception as e:out={'exception':type(e).__name__,'message':str(e)}
        rows.append({'name':name,'case':case,'answer':answer,'result':out})
    check('valid C2',c,solve(c))
    for a in ({'status':'UNKNOWN'},{'status':'OUT_OF_SCOPE','witness':{'reason':'MISSING_IDENTITY_OR_INVERSE'}},{'status':'OUT_OF_SCOPE','witness':{'reason':'EXCEEDS_MAX_ORDER','order':65}}):check('unsubstantiated '+a['status'],c,{'case_id':'probe',**a})
    for images in ([1,123],[-1],['bad']):check('image schema '+str(images),c,{'case_id':'probe','status':'SOLVED','kind':'IDENTIFIED','rep_id':[2,1],'images':images})
    red={**c,'gens':[1,1]};comp={'case_id':'probe','task':'COMPARE','G':red,'H':red}
    check('redundant generators identical group',comp,solve(comp))
    ring={'case_id':'probe','presentation':'matrix','p':4,'dim':1,'gens':[[[3]]]}
    check('composite modulus admitted',ring,solve(ring))
    cat=[{'id':r['id'],'name':r['name'],'independent':independent(r['table']),'retained_invariants':r['invariants']} for r in get_catalog()]
    # A4 independently constructed as even permutations on four points.
    perms=[p for p in itertools.permutations(range(4)) if sum(p[i]>p[j] for i in range(4) for j in range(i+1,4))%2==0]
    a4=[[perms.index(tuple(p[q[i]] for i in range(4))) for q in perms] for p in perms]
    write('_c044_probes.json',{'adversarial_controls':rows,'catalog_table_checks':cat,'independent_A4':independent(a4),'A4_times_C2_expected_centre':2,'limits':'Every table checked as a finite group; SmallGroups numeric labels are not independently authenticated.'})
    print([(r['name'],r['result']) for r in rows]);print('catalog',len(cat),'valid',sum(r['independent']['valid_group'] for r in cat))
if __name__=='__main__':main()
