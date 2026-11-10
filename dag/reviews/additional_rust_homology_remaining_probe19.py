import sys,json,itertools
sys.dont_write_bytecode=True
from fractions import Fraction as Q
from pathlib import Path
def mm(a,b):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]
def sub(a,b):return [[x-y for x,y in zip(r,s)] for r,s in zip(a,b)]
identity=[[1,0],[0,1]];p=[[1,0]];i=[[1],[0]];boundary=[[0],[1]];h=[[0,-1]]
assert sub(mm(i,p),identity)==mm(boundary,h)
assert mm(h,boundary)==[[-1]]
fillings=[]
for t in range(-5,6):
    z=[[0],[t]];filling=[[-mm(h,z)[0][0]]]
    assert mm(boundary,filling)==z;fillings.append(t)
pairings=0
for z,u in itertools.product(range(-3,4),repeat=2):
    if not z*u:continue
    transported_z=[z,0];transported_u=[u,0]
    assert sum(a*b for a,b in zip(transported_z,transported_u))==z*u;pairings+=1
perturbations=0
for a,b in itertools.product(range(-3,4),repeat=2):
    if b==-1:continue
    q=Q(1+b);d=[[Q(a),q]];ip=[[1],[Q(-a)/q]];r=[[1,0]];hp=[[0],[1/q]]
    assert mm(d,ip)==[[0]] and mm(r,ip)==[[1]]
    assert sub(identity,mm(ip,r))==mm(hp,d)
    assert mm(d,hp)==[[1]] and mm(r,hp)==[[0]]
    perturbations+=1
r={'rule':'integral_equivalence_and_rational_perturbation_sign_controls','status':'nontrivial_reconstruction_and_perturbation_identities_confirmed','runtime':sys.version,'integral_contraction':{'d1':boundary,'projection0':p,'inclusion0':i,'H0':h,'identity_convention':'ip-id=dH+Hd'},'source_fillings':len(fillings),'nonzero_pairing_transports':pairings,'rational_nonzero_perturbations_including_zero_delta':perturbations,'singular_resolvent_b':-1,'cochain_convention':'id-ir=dh+hd; resolvent1+delta*h','limits':['Independent finite exact arithmetic, not Rust execution or the external CochainMap/CochainHomotopy/elimination validators.','Checks one nontrivial family, not every contraction or unbounded perturbation lemma.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))
