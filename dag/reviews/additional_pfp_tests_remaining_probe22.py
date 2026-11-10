import sys
sys.dont_write_bytecode=True
import itertools
import struct
from fractions import Fraction
import additional_pfp_tests_remaining_audit as a

def rank(rows):
    m=[list(map(Fraction,row)) for row in rows]
    r=0
    for c in range(len(m[0]) if m else 0):
        pivot=next((i for i in range(r,len(m)) if m[i][c]),None)
        if pivot is None:continue
        m[r],m[pivot]=m[pivot],m[r]
        q=m[r][c];m[r]=[x/q for x in m[r]]
        for i in range(len(m)):
            if i!=r:
                q=m[i][c];m[i]=[x-q*y for x,y in zip(m[i],m[r])]
        r+=1
    return r

def complex_report(n,edges,faces):
    boundary1=[[int(v==y)-int(v==x) for x,y in edges] for v in range(n)]
    boundary2=[[sum(sign for pair,sign in (((x,y),1),((x,z),-1),((y,z),1)) if pair==e) for x,y,z in faces] for e in edges]
    r1,r2=rank(boundary1),rank(boundary2)
    assert all(sum(boundary1[v][i]*boundary2[i][f] for i in range(len(edges)))==0 for v in range(n) for f in range(len(faces)))
    return {'vertices':n,'edges':len(edges),'faces':len(faces),'rank_boundary1':r1,'rank_boundary2':r2,'graph_cycle_rank':len(edges)-r1,'first_betti_of_declared_2_complex':len(edges)-r1-r2}

homology={f'K{n}_2_skeleton':complex_report(n,list(itertools.combinations(range(n),2)),list(itertools.combinations(range(n),3))) for n in (6,7)}
opposites={(0,1),(2,3),(4,5)}
edges=[e for e in itertools.combinations(range(6),2) if e not in opposites]
faces=[f for f in itertools.combinations(range(6),3) if all(e in edges for e in itertools.combinations(f,2))]
homology['standard_octahedral_2_sphere']=complex_report(6,edges,faces)
assert [v['first_betti_of_declared_2_complex'] for v in homology.values()]==[0,0,0]

nan_rows=[]
for bits in ('7ff8000000000001','7ff8000000000002','fff8000000000001'):
    value=struct.unpack('>d',bytes.fromhex(bits))[0]
    assert struct.pack('>d',value).hex()==bits
    nan_rows.append({'input_ieee754_bits':bits,'float_hex':value.hex()})
assert len({r['float_hex'] for r in nan_rows})==1
cycle_a={(0,1):1,(1,2):1,(0,2):-1}
cycle_b={(0,1):1,(1,3):1,(0,3):-1}
cycle_inner_product=sum(cycle_a.get(e,0)*cycle_b.get(e,0) for e in set(cycle_a)|set(cycle_b))
assert cycle_inner_product==1

pins=[]
for name in ('test_cemetery_sink.py','test_cochain_gradient_simplicial_k6.py'):
    p='pfp/tests/'+name;a.source(p);pins.append({'path':p,'sha256':a.row(p)['sha256']})
a.write('_probe22.json',{'status':'observed','method':'Independent bounded Fraction Gaussian elimination and stdlib IEEE-754 encoding; no original imports/native/providers.','source_bindings':pins,'homology':homology,'nan_encoding':nan_rows,'shared_tree_edge_cycle_inner_product':cycle_inner_product,'limits':'Homology computed for the exact standard complexes described in the tests; no owner constructor execution. NaN control compares representation loss, not a production serializer run.'})
print('Recorded exact topology and NaN representation controls.')
