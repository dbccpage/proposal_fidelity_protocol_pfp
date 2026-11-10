"""Independent bounded finite controls, without importing the paper's tests."""
from itertools import product, permutations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'papers/pfp/010_pfp_holonomy_checks_and_model_pilots/code/holonomy.py'
spec=importlib.util.spec_from_file_location('paper010_math_owner',SOURCE)
h=importlib.util.module_from_spec(spec);sys.modules[spec.name]=h;spec.loader.exec_module(h)
checks=[]

def compose(p,q):return tuple(p[q[i]] for i in range(3))
def inverse(p):return tuple(p.index(i) for i in range(3))
def label(p):return ''.join(map(str,p))

perms=list(permutations(range(3)));identity=(0,1,2)
vertices=[(0,0),(0,1),(1,0),(1,1)]
edges=[((0,0),(0,1)),((0,0),(1,0)),((0,1),(1,1)),((1,0),(1,1))]
# g(u) U(u,v) g(v)^-1=e implies U(u,v)=g(u)^-1 g(v).
pure=set()
for tail in product(perms,repeat=3):
    gauge=dict(zip(vertices,(identity,*tail)))
    pure.add(tuple(label(compose(inverse(gauge[u]),gauge[v])) for u,v in edges))
group=h.symmetric_group_s3();lattice=h.Lattice(2,2,False)
assert set(lattice.positive_edges())==set(edges)
counts={'FLAT_TRIVIAL':0,'NOT_FLAT':0}
for values in product([label(p) for p in perms],repeat=4):
    connection=h.Connection(group,lattice,dict(zip(edges,values)))
    report=h.check_flatness(connection)
    expected=h.FLAT_TRIVIAL if values in pure else h.NOT_FLAT
    assert report.verdict==expected
    counts[report.verdict]+=1
    if report.gauge is not None:
        decoded={v:tuple(map(int,g)) for v,g in report.gauge}
        assert all(compose(compose(decoded[u],tuple(map(int,value))),inverse(decoded[v]))==identity for (u,v),value in zip(edges,values))
assert counts=={'FLAT_TRIVIAL':216,'NOT_FLAT':1080}
checks.append({'rule':'all1296_S3_open2x2_connections_vs_independent_permutation_gauge_enumeration','status':'passed','cases':1296,'counts':counts,'oracle_pure_gauges':len(pure)})

vertices=[(r,c) for r in range(3) for c in range(3)]
edges=[edge for r,c in vertices for edge in (((r,c),(r,(c+1)%3)),((r,c),((r+1)%3,c)))]
indices={edge:i for i,edge in enumerate(edges)}
masks=[]
for r,c in vertices:
    cycle=[(r,c),((r+1)%3,c),((r+1)%3,(c+1)%3),(r,(c+1)%3)]
    mask=0
    for i in range(4):
        pair=cycle[i],cycle[(i+1)%4]
        index=indices[pair] if pair in indices else indices[pair[::-1]]
        mask ^= 1<<index
    masks.append(mask)
basis={}
for row in masks:
    while row:
        pivot=row.bit_length()-1
        if pivot in basis:row ^= basis[pivot]
        else:basis[pivot]=row;break
assert len(basis)==8
z2=h.FiniteGroup('Z2',['0','1'],'0',{'0':{'0':'0','1':'1'},'1':{'0':'1','1':'0'}},{'0':'0','1':'1'})
lattice=h.Lattice(3,3,True);assert set(lattice.positive_edges())==set(edges)
flat={}
for gauge_bits in range(256):
    gauge={v:(gauge_bits>>(i-1))&1 if i else 0 for i,v in enumerate(vertices)}
    for a,b in product((0,1),repeat=2):
        values=[gauge[u]^gauge[v]^(a if u[1]==2 and v[1]==0 else b if u[0]==2 and v[0]==0 else 0) for u,v in edges]
        bits=sum(value<<i for i,value in enumerate(values))
        assert all((bits&mask).bit_count()%2==0 for mask in masks)
        assert bits not in flat
        flat[bits]=h.FLAT_TRIVIAL if a==b==0 else h.FLAT_NONTRIVIAL
assert len(flat)==2**(len(edges)-len(basis))==1024
negative={bits^1 for bits in flat}
assert len(negative)==1024 and not negative.intersection(flat)
counts={h.FLAT_TRIVIAL:0,h.FLAT_NONTRIVIAL:0,h.NOT_FLAT:0}
for bits,expected in list(flat.items())+[(bits,h.NOT_FLAT) for bits in negative]:
    links={edge:str((bits>>i)&1) for i,edge in enumerate(edges)}
    verdict=h.check_flatness(h.Connection(z2,lattice,links)).verdict
    assert verdict==expected
    counts[verdict]+=1
assert counts=={h.FLAT_TRIVIAL:256,h.FLAT_NONTRIVIAL:768,h.NOT_FLAT:1024}
checks.append({'rule':'all1024_flat_Z2_torus3x3_connections_and1024_nonflat_controls','status':'passed','cases':2048,
               'independent_plaquette_rank_F2':len(basis),'counts':counts,'limit':'All flat states in this one finite lattice; nonflat controls are a selected1024-state subset.'})
result={'scope':'Independent finite permutation and F2/gauge oracles; no provider/private/Lean execution',
        'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'checks':checks,
        'limits':['Finite carrier/shape checks do not prove the full Python checker for every finite group or lattice.',
                  'No model-performance or quantum-physics inference.']}
(ROOT/'dag/reviews/additional_paper_010_math_controls.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
