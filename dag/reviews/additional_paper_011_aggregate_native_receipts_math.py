"""Bounded independent arithmetic on public retained matrices; never runs native code."""
import hashlib,json
from fractions import Fraction as F
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts'
B=R/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/docs'
def read(p):return json.loads((B/p).read_bytes())
def matrix(x):return [[F(v) for v in row] for row in x]
def transpose(a):return [list(x) for x in zip(*a)]
def mul(a,b):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*b)] for row in a]
def rank(a,mod=None):
 a=[list(row) for row in a];r=0
 for c in range(len(a[0]) if a else 0):
  pivot=next((i for i in range(r,len(a)) if (a[i][c] % mod if mod else a[i][c])!=0),None)
  if pivot is None:continue
  a[r],a[pivot]=a[pivot],a[r];v=a[r][c]
  a[r]=[(x*pow(int(v),-1,mod))%mod if mod else x/v for x in a[r]]
  for i in range(len(a)):
   if i!=r:
    f=a[i][c];a[i]=[(x-f*y)%mod if mod else x-f*y for x,y in zip(a[i],a[r])]
  r+=1
  if r==len(a):break
 return r
def det(a):
 a=[list(row) for row in a];n=len(a);assert all(len(x)==n for x in a);d=F(1)
 for c in range(n):
  pivot=next((i for i in range(c,n) if a[i][c]),None)
  if pivot is None:return F(0)
  if pivot!=c:a[c],a[pivot]=a[pivot],a[c];d=-d
  q=a[c][c];d*=q
  for i in range(c+1,n):
   f=a[i][c]/q;a[i]=[x-f*y for x,y in zip(a[i],a[c])]
 return d
def zero(a):return all(x==0 for row in a for x in row)
requests=read('native_dossier_homology/run_v4/request.json')['cases'];results=read('native_dossier_homology/run_v4/result.json')['results']
rational=[]
for q,out in zip(requests[:8],results):
 mats=[matrix(m) for m in q['matrices']];dims=[len(mats[0][0])]+[len(m) for m in mats];ranks=[rank(m) for m in mats]
 products=[mul(b,a) for a,b in zip(mats,mats[1:])];assert all(zero(x) for x in products)
 extended=[0]+ranks+[0];betti=[n-extended[k]-extended[k+1] for k,n in enumerate(dims)]
 assert dims==out['dimensions'] and ranks==out['ranks'] and betti==out['betti_over_q']
 assert all([[str(x) for x in row] for row in product]==captured['product'] for product,captured in zip(products,out['boundary_products']))
 rational.append({'case_id':q['case_id'],'dimensions':dims,'ranks':ranks,'betti_over_q':betti,'declared_mismatches':[x for x in out['declared_betti_comparisons'] if not x['matches']]})
replay=read('native_dossier_integral/run_v3/replay_request.json')['cases'];integral_out=read('native_dossier_integral/run_v3/result.json')['results'];integral=[];cert_count=0
for i,(q,out) in enumerate(zip(replay[:8],integral_out)):
 mats=[matrix(m) for m in q['matrices']];assert q['matrices']==requests[i]['matrices']
 invariants=[];certificates=[]
 for degree,(m,c) in enumerate(zip(mats,q['certificates']),1):
  assert c['degree']==degree
  a=transpose(m);u=matrix(c['u']);v=matrix(c['v']);d=matrix(c['d']);du=det(u);dv=det(v)
  assert abs(du)==abs(dv)==1 and mul(mul(u,a),v)==d
  assert all(x==0 for r,row in enumerate(d) for col,x in enumerate(row) if r!=col)
  diag=[d[k][k] for k in range(min(len(d),len(d[0])))];nonzero=[x for x in diag if x]
  assert all(x.denominator==1 and x>0 for x in nonzero) and diag[:len(nonzero)]==nonzero
  assert all(b%a==0 for a,b in zip(nonzero,nonzero[1:]))
  invariants.append([int(x) for x in nonzero]);certificates.append({'degree':degree,'det_u':str(du),'det_v':str(dv),'invariants':[str(x) for x in nonzero]});cert_count+=1
 dims=q['carrier_dimensions'];ranks=[len(x) for x in invariants];r2=[rank([[int(x)%2 for x in row] for row in m],2) for m in mats]
 bq=[n-a-b for n,a,b in zip(dims,[0]+ranks,ranks+[0])];b2=[n-a-b for n,a,b in zip(dims,[0]+r2,r2+[0])]
 torsions=[[x for x in d if x>1] for d in invariants]+[[]]
 for k,g in enumerate(out['integral_homology']):
  assert g['degree']==k and g['free_rank']==bq[k] and g['torsion']==[str(x) for x in torsions[k]] and g['mod2_dimension']==b2[k]
  uct=bq[k]+sum(x%2==0 for x in torsions[k])+sum(x%2==0 for x in (torsions[k-1] if k else []))
  assert uct==b2[k]==g['uct_dimension']
 assert out['euler_characteristic']==str(sum((-1)**k*n for k,n in enumerate(dims)))
 integral.append({'case_id':q['case_id'],'certificates':certificates,'free_ranks':bq,'chain_torsion_by_degree':torsions,'mod2_dimensions':b2})
control_outcomes={}
for rel in ['native_dossier_homology/run_v4/stdout.bin','native_dossier_integral/run_v3/compute_stdout.bin','native_dossier_integral/run_v3/replay_stdout.bin']:
 v=read(rel);control_outcomes[rel]=[{k:x[k] for k in ('case_id','success','error') if k in x} for x in v['cases'][8:]]
inputs=['native_dossier_homology/run_v4/request.json','native_dossier_homology/run_v4/result.json','native_dossier_integral/run_v3/replay_request.json','native_dossier_integral/run_v3/result.json',*control_outcomes]
result={'status':'pass','method':'Independent Python stdlib Fraction Gaussian rank/determinant, exact UAV equality, Smith shape/divisibility, rational and mod2 rank, chain torsion and UCT arithmetic. No original owner imports or native calls.','rational':rational,'integral':integral,'smith_certificates_checked':cert_count,'recorded_control_outcomes':control_outcomes,'input_hashes':{p:hashlib.sha256((B/p).read_bytes()).hexdigest() for p in inputs},'limits':'Finite arithmetic on the exact supplied matrices; not a geometric realization, manifold/intersection proof, physical identification, historical-execution authentication or native implementation validation.'}
(H/(P+'_math_checks.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'pass','rational_cases':len(rational),'integral_cases':len(integral),'smith_certificates':cert_count,'declared_mismatches':sum(len(x['declared_mismatches']) for x in rational),'controls':control_outcomes},indent=2))
