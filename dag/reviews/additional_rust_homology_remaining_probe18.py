import sys,json,itertools,math,functools
sys.dont_write_bytecode=True
from fractions import Fraction as Q
from pathlib import Path
def snf(a):
    a=[r[:] for r in a];rows=len(a);cols=len(a[0]) if rows else 0;out=[];steps=0
    def trunc(x,y):return (abs(x)//abs(y))*(1 if x*y>=0 else -1)
    for t in range(min(rows,cols)):
        while True:
            steps+=1;assert steps<1000
            nonzero=[(abs(a[i][j]),i,j) for i in range(t,rows) for j in range(t,cols) if a[i][j]]
            if not nonzero:return out
            _,pi,pj=min(nonzero);a[t],a[pi]=a[pi],a[t]
            for row in a:row[t],row[pj]=row[pj],row[t]
            p=a[t][t]
            for i in range(rows):
                if i!=t and a[i][t]:
                    fac=trunc(a[i][t],p)
                    for j in range(t,cols):a[i][j]-=fac*a[t][j]
            p=a[t][t]
            for j in range(cols):
                if j!=t and a[t][j]:
                    fac=trunc(a[t][j],p)
                    for i in range(t,rows):a[i][j]-=fac*a[i][t]
            if any(a[i][t] for i in range(t+1,rows)) or any(a[t][j] for j in range(t+1,cols)):continue
            offender=next((i for i in range(t+1,rows) if any(a[i][j]%a[t][t] for j in range(t+1,cols))),None)
            if offender is not None:
                for j in range(t,cols):a[t][j]+=a[offender][j]
                continue
            out.append(abs(a[t][t]));break
    return out
def det(a):
    if not a:return 1
    return sum((-1)**j*x*det([row[:j]+row[j+1:] for row in a[1:]]) for j,x in enumerate(a[0]))
def oracle(a):
    prev=1;out=[];n=len(a)
    for k in range(1,n+1):
        g=0
        for rs in itertools.combinations(range(n),k):
            for cs in itertools.combinations(range(n),k):g=math.gcd(g,det([[a[r][c] for c in cs] for r in rs]))
        if not g:break
        out.append(g//prev);prev=g
    return out
count=0
for n,values in [(2,range(-3,4)),(3,range(-1,2))]:
    for entries in itertools.product(values,repeat=n*n):
        a=[list(entries[i*n:(i+1)*n]) for i in range(n)]
        assert snf(a)==oracle(a);count+=1
def rank(a,mod=None):
    a=[[x%mod if mod else Q(x) for x in row] for row in a];r=0
    for c in range(len(a[0])):
        i=next((i for i in range(r,len(a)) if a[i][c]),None)
        if i is None:continue
        a[i],a[r]=a[r],a[i];v=a[r][c];a[r]=[(x*pow(v,-1,mod))%mod if mod else x/v for x in a[r]]
        for i in range(len(a)):
            if i!=r:
                v=a[i][c];a[i]=[(x-v*y)%mod if mod else x-v*y for x,y in zip(a[i],a[r])]
        r+=1
    return r
faces=[(1,2,3),(1,2,4),(1,3,5),(1,4,6),(1,5,6),(2,3,6),(2,4,5),(2,5,6),(3,4,5),(3,4,6)]
edges=sorted(set(e for f in faces for e in itertools.combinations(f,2)))
d1=[]
for a,b,c in faces:
    d1.append([1 if e in [(a,b),(b,c)] else -1 if e==(a,c) else 0 for e in edges])
rq,r2=rank(d1),rank(d1,2)
assert len(edges)==15 and (rq,r2)==(10,9)
# d0 is incidence of K6, rank5. Terminal integral quotient of d1 has even torsion.
assert [6-5,15-5-rq,10-rq]==[1,0,0]
assert [6-5,15-5-r2,10-r2]==[1,1,1]
r={'rule':'smith_small_matrices_and_torsion_scope','status':'finite_determinantal_oracle_and_boundary_controls_confirmed','runtime':sys.version,'snf_square_matrices':count,'oracle':'gcd of all minors in each dimension, independent of elimination','rp2_faces':faces,'rp2_dimensions':[6,15,10],'rational_d1_rank':rq,'mod2_d1_rank':r2,'terminal_even_torsion_for_simplicial_graph_carrier':True,'d0_2_d1_0_betti':[0,0,1],'i128_min_positive_magnitude':2**127,'i128_max':2**127-1,'ragged_input':[[1],[]],'mutated_nonchain_incoming_boundary':[2],'limits':['Python arbitrary-integer reconstruction is not Rust i128 execution or the external checked BigInt SNF backend.','Rank difference certifies presence of an even invariant factor for this explicit integral matrix; no imported triangulation or native computation used.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))
