"""Own small arithmetic/string controls, no original Rust imports or execution."""
import sys,itertools,json,hashlib,math
from pathlib import Path
sys.dont_write_bytecode=True
def put(x):return x
vs=list(itertools.product((-1,0,1),repeat=3));pairs=accepted=0
for x,y in itertools.product(vs,repeat=2):
 pairs+=1;dot=sum(a*b for a,b in zip(x,y));admitted=any(x) and any(y) and dot==0
 if admitted:
  accepted+=1;assert sum((a+b)**2 for a,b in zip(x,y))==sum(a*a for a in x)+sum(b*b for b in y)
prefix=0
for n in range(1,5):
 for v in itertools.product((-2,0,3),repeat=n):
  ps=[sum(v[:i+1]) for i in range(n)];total=sum(v)
  assert all(total-sum(v[i+1:])==ps[i] for i in range(n));prefix+=1
  bad=ps[:];bad[-1]+=1;assert bad[-1]!=sum(v)
lhs='id_X ; f';rhs='f ; id_Y';assert lhs!='f' and rhs!='f'
x=1e308;product=x*x;nan=product+(-product);assert math.isfinite(x) and math.isinf(product) and math.isnan(nan)
controls=[{'id':'RLA-P27','rule':'Finite integer orthogonality and forward/backward prefix consistency','status':'completed_bounded','pair_cases':pairs,'orthogonal_nonzero_pairs':accepted,'prefix_cases':prefix,'limits':'Own integers in {-1,0,1}^3 and lists length1..4 over {-2,0,3}; no original execution or arbitrary fixed-width overflow guarantee.'},{'id':'RLA-P28','rule':'Symbolic category unit composition differs under actual string equality','status':'counterexample_observed','left_identity_name':lhs,'right_identity_name':rhs,'original_name':'f','limits':'Same valid endpoint labels/dimensions. Shape-only documentation is acknowledged; no upstream category implementation executed.'},{'id':'RLA-P29','rule':'Finite binary64 coordinates can produce nonfinite checked-dot output','status':'counterexample_observed','finite_input':str(x),'squared_output':'inf','mixed_sum_output':'nan','limits':'Own IEEE754 Python scalar operations mirror the two multiply/add expressions only; not Rust execution or evidence about robust numerical owners.'}]
out={'status':'complete_bounded_controls','helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'controls':controls}
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
