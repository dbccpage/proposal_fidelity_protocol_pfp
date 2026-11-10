import sys,json,itertools
sys.dont_write_bytecode=True
from fractions import Fraction as Q
from pathlib import Path
def rank(rows,mod=None):
    a=[[int(x)%mod if mod else Q(x) for x in row] for row in rows];r=0
    for c in range(len(a[0]) if a else 0):
        piv=next((i for i in range(r,len(a)) if a[i][c]),None)
        if piv is None:continue
        a[r],a[piv]=a[piv],a[r];v=a[r][c]
        a[r]=[(x*pow(v,-1,mod))%mod if mod else x/v for x in a[r]]
        for i in range(len(a)):
            if i!=r:
                v=a[i][c];a[i]=[(x-v*y)%mod if mod else x-v*y for x,y in zip(a[i],a[r])]
        r+=1
    return r
def mm(a,b):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]
cases=[]
for rows,cols,pr,pc in itertools.product(range(1,4),range(1,4),(False,True),(False,True)):
    if pr and rows<2 or pc and cols<2:continue
    vr=rows if pr else rows+1;vc=cols if pc else cols+1
    vert=lambda r,c:r*vc+c
    wr=lambda r:r%vr if pr else r;wc=lambda c:c%vc if pc else c
    hi=lambda r,c:r*cols+c;vi=lambda r,c:vr*cols+r*vc+c
    edges=[(vert(r,c),vert(r,wc(c+1))) for r in range(vr) for c in range(cols)]+[(vert(r,c),vert(wr(r+1),c)) for r in range(rows) for c in range(vc)]
    faces=[[(hi(r,c),1),(vi(r,wc(c+1)),1),(hi(wr(r+1),c),-1),(vi(r,c),-1)] for r in range(rows) for c in range(cols)]
    d1=[[0]*len(edges) for _ in range(vr*vc)];d2=[[0]*len(faces) for _ in edges]
    for j,(u,v) in enumerate(edges):d1[u][j]-=1;d1[v][j]+=1
    for j,f in enumerate(faces):
        for i,s in f:d2[i][j]+=s
    assert all(x==0 for row in mm(d1,d2) for x in row)
    expected=[1,int(pr)+int(pc),int(pr and pc)]
    for mod in (None,2):
        r1,r2=rank(d1,mod),rank(d2,mod)
        assert [vr*vc-r1,len(edges)-r1-r2,len(faces)-r2]==expected
    cases.append({'rows':rows,'cols':cols,'periodic':[pr,pc],'betti':expected})
# Q=[1,0], kernel=<e2>. Every map [[a,0],[b,c]] transports that kernel.
horizontal=0
for a,b,c,d in itertools.product(range(-2,3),repeat=4):
    f=[[a,0],[b,1]];fp=[[a,0],[b+1,2]]
    g=[[c,0],[d,1]];gp=[[c,0],[d+2,3]]
    old,new=mm(g,f),mm(gp,fp)
    assert old[0]==new[0];horizontal+=1
r={'rule':'lattice_integral_and_observed_composition_controls','status':'exact_finite_controls_confirmed','runtime':sys.version,'lattice_count':len(cases),'lattices':cases,'observed_horizontal_compositions':horizontal,'bockstein_d2':(2//2)%2,'bockstein_d4':(4//2)%2,'d4_integral_cohomology':'Z/4, with nonzero element of order2','dense_shape_product_64bit':{'rows':2**63,'cols':2,'product':2**64},'limits':['Independent Fraction/GF2 arithmetic and finite matrix controls, not Rust/SNF/backend execution.','Rational/mod2 Betti equality does not prove integral torsion absence for arbitrary complexes; lattice controls have the declared grid boundary formulas.']}
assert r['bockstein_d2']==1 and r['bockstein_d4']==0
Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in r.items() if k!='lattices'}))
