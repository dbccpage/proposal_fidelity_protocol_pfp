import sys,itertools,json,copy
sys.dont_write_bytecode=True
from additional_challenges_051_059_audit import ROOT,write
sys.path.insert(0,str(ROOT/'workflows/tasks/certified_challenges'))
from c052_maxflow_mincut_certificates.reference_solver import solve
from c052_maxflow_mincut_certificates.judge_packet.exact_checker import check_solution as primary
from c052_maxflow_mincut_certificates.judge_packet.independent_checker import check_solution as secondary
def bounded_cut_truth(c):
    n,s,t=c['n'],c['s'],c['t']
    if any(type(v)!=int for v in (n,s,t)) or n<=0 or not 0<=s<n or not 0<=t<n or s==t:return {'status':'invalid_domain'}
    for arc in c.get('arcs',[]):
        if len(arc)!=3 or type(arc[0])!=int or type(arc[1])!=int or type(arc[2]) not in (int,str):return {'status':'invalid_domain'}
        try:cap=int(arc[2])
        except (ValueError,TypeError):return {'status':'invalid_domain'}
        if not 0<=arc[0]<n or not 0<=arc[1]<n or not 0<=cap<=10**18:return {'status':'invalid_domain'}
    if type(n)!=int or n>12:return {'status':'outside_enumeration_ceiling'}
    rest=[v for v in range(n) if v not in (s,t)];best=None;count=0
    for bits in itertools.product((0,1),repeat=len(rest)):
        S={s}|{v for v,b in zip(rest,bits) if b};val=sum(int(cap) for u,v,cap in c['arcs'] if u in S and v not in S);count+=1
        if best is None or val<best:best=val
    return {'status':'enumerated','min_cut':best,'cuts':count}
def certificate_math(c,a):
    try:
        n,s,t=c['n'],c['s'],c['t']
        if any(type(v)!=int for v in (n,s,t)) or n<=0 or not 0<=s<n or not 0<=t<n or s==t:return {'valid':False,'reason':'node schema'}
        if a.get('status')!='SOLVED':return {'valid':None,'reason':'not a flow certificate'}
        arcs=c['arcs'];flows=[int(x) for x in a['flow']];value=int(a['value']);S=set(a['cut_S']);balances=[0]*n
        if len(flows)!=len(arcs) or s not in S or t in S:return {'valid':False,'reason':'dimensions/partition'}
        for (u,v,cap),f in zip(arcs,flows):
            if type(u)!=int or type(v)!=int or type(cap) not in (str,int) or not 0<=u<n or not 0<=v<n:return {'valid':False,'reason':'arc schema'}
            cap=int(cap)
            if cap<0 or cap>10**18:return {'valid':False,'reason':'declared capacity domain'}
            if not 0<=f<=cap:return {'valid':False,'reason':'capacity'}
            balances[u]-=f;balances[v]+=f
        target=[-value if v==s else value if v==t else 0 for v in range(n)]
        cap=sum(int(cap) for u,v,cap in arcs if u in S and v not in S)
        return {'valid':balances==target and cap==value,'reason':'exact balances and cut equality under declared input domain'}
    except Exception as e:return {'valid':False,'reason':type(e).__name__}
def verdict(c,a):
    res=[]
    for fn in (primary,secondary):
        try:res.append(fn(c,a))
        except Exception as e:res.append({'exception':type(e).__name__,'message':str(e)})
    return res
def main():
    checks=0;bad=[]
    for loops,values in [(True,(0,1)),(False,(0,1,2))]:
        pairs=[(u,v) for u in range(3) for v in range(3) if loops or u!=v]
        for caps in itertools.product(values,repeat=len(pairs)):
            c={'case_id':'audit_three_nodes','n':3,'s':0,'t':2,'arcs':[[u,v,str(cap)] for (u,v),cap in zip(pairs,caps)]};ans=solve(c);truth=bounded_cut_truth(c);checks+=1
            if int(ans['value'])!=truth['min_cut'] or not certificate_math(c,ans)['valid'] or not all(v[0] for v in verdict(c,ans)):bad.append({'case':c,'answer':ans,'truth':truth})
    controls={};base={'case_id':'audit_schema','n':2,'s':0,'t':1,'arcs':[[0,1,'2']]}
    for name,edit in [('fractional_capacity',lambda c:c['arcs'][0].__setitem__(2,1.9)),('boolean_capacity',lambda c:c['arcs'][0].__setitem__(2,True)),('fractional_endpoint',lambda c:c['arcs'][0].__setitem__(0,0.9)),('capacity_above_task_bound',lambda c:c['arcs'][0].__setitem__(2,str(10**18+1)))]:
        c=copy.deepcopy(base);edit(c);ans=solve(c);controls[name]={'case':c,'answer':ans,'owner_verdict':verdict(c,ans),'independent_domain_and_certificate':certificate_math(c,ans)}
    for name,c in [('non_object',None),('long_path',{'case_id':'audit_long_path','n':1100,'s':0,'t':1099,'arcs':[[i,i+1,'1'] for i in range(1099)]})]:
        try:r=solve(c);controls[name]={'status':'returned','answer':r}
        except Exception as e:controls[name]={'status':'exception','type':type(e).__name__,'message':str(e),'case_description':'null' if c is None else '1100 vertices, unit-capacity directed chain; mathematical maximum flow1'}
    out={'exhaustive_three_vertex_networks':{'cases':checks,'mismatches':bad,'limits':'512 binary-capacity directed graphs including loops plus729 ternary-capacity loopless directed graphs; min cuts enumerated independently.'},'controls':controls,'limits':['No accepted false optimum found in these bounded well-formed graphs.','Malformed input coercion and recursion are distinct from the flow/cut theorem.']};write('_c052_probes.json',out);print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
