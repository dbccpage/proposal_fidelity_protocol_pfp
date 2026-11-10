"""Independent exact fixture arithmetic/encoding checks, not source-reading receipts."""
import hashlib,itertools,json,pathlib,struct
from fractions import Fraction as Q
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_functional_certifiers'
def strict(p):
 def pairs(xs):
  d={}
  for k,v in xs:
   assert k not in d,(p,k)
   d[k]=v
  return d
 return json.loads(p.read_text(),object_pairs_hook=pairs)
def add(a,b):return(a[0]+b[0],a[1]+b[1])
def mul(a,b):return(a[0]*b[0]-a[1]*b[1],a[0]*b[1]+a[1]*b[0])
def conj(a):return(a[0],-a[1])
def det(m):
 n=len(m);total=(Q(0),Q(0))
 for p in itertools.permutations(range(n)):
  v=(Q((-1)**sum(p[i]>p[j]for i in range(n)for j in range(i+1,n))),Q(0))
  for i,j in enumerate(p):v=mul(v,m[i][j])
  total=add(total,v)
 return total
out=[];inputs=[]
base=R/'code/rust/tests/core_functional/fixtures'
def fixture(name):
 p=base/name;inputs.append({'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return strict(p)
f=fixture('finite_hermitian_spectrum.json')
for c in f['cases']:
 m=[[tuple(map(Q,z))for z in row]for row in c['matrix']];n=len(m);vals=c['eigenvalues']
 assert all(len(row)==n for row in m)
 assert all(m[i][j]==conj(m[j][i])for i in range(n)for j in range(n))
 assert vals==sorted(vals)and len(vals)==n
 for t in range(n+1):
  lhs=det([[add(m[i][j],(-Q(t),Q(0)))if i==j else m[i][j]for j in range(n)]for i in range(n)])
  rhs=Q(1)
  for v in vals:rhs*=v-t
  assert lhs==(rhs,Q(0)),c['name']
 assert c['spacings']==[b-a for a,b in zip(vals,vals[1:])]
 out.append({'fixture':c['name'],'result':'exact Hermitian/characteristic polynomial/spacings pass','method':'n+1 exact rational Gaussian determinant evaluations identify degree-n polynomial'})
f=fixture('state_trace_distance.json')
for c in f['diagonal_cases']:
 a=list(map(lambda x:Q(*x),c['left']));b=list(map(lambda x:Q(*x),c['right']));v=list(map(lambda x:Q(*x),c['eigenvalues']));d=Q(*c['distance'])
 assert sum(a)==sum(b)==1 and min(a+b)>=0
 assert sorted(x-y for x,y in zip(a,b))==v and sum(abs(x)for x in v)/2==d
 out.append({'fixture':c['name'],'result':'exact diagonal density and distance pass'})
for c in f['pure_cases']:
 a=[tuple(Q(*z)for z in x)for x in c['left']];b=[tuple(Q(*z)for z in x)for x in c['right']]
 norm=lambda v:sum(mul(conj(x),x)[0]for x in v)
 assert norm(a)==norm(b)==1
 z=(Q(0),Q(0))
 for x,y in zip(a,b):z=add(z,mul(conj(x),y))
 d=Q(*c['distance']);assert d*d==1-mul(z,conj(z))[0]
 assert list(map(lambda x:Q(*x),c['eigenvalues']))==[-d,d]
 out.append({'fixture':c['name'],'result':'exact pure-state overlap/distance pass'})
f=fixture('functional_factory_vectors.json')
def enc(x):return json.dumps(x,separators=(',',':'),ensure_ascii=False).encode()
def h(domain,x,prefix=b'core.functional.v1\0'):
 b=enc(x);d=domain.encode();return list(hashlib.sha256(prefix+struct.pack('<Q',len(d))+d+struct.pack('<Q',len(b))+b).digest())
for c in f['cases']:
 name=c['name'];r=c['expected_record'];st=c['input']['state'];cfg=c['configuration']
 actual={'input_hash':h('input',c['input']),'config_hash':h(name+'-config',cfg)}
 if name=='phi1':
  actual['certificate_refs']=[h('phi1-certificate',st)]
  actual['witness_refs']=[h('phi1-primal',[st['alpha'],st['primal_residual']]),h('phi1-dual',st['dual_witness'])]
 else:
  actual['certificate_refs']=[]
  actual['witness_refs']=[h('gamma2-complex',cfg[1]),h('gamma2-residual',st),h('gamma2-coboundary',r['values'])]
 actual['output_hash']=h('output',{k:actual.get(k,r[k])for k in sorted(r)if k!='output_hash'})
 out.append({'fixture':name,'result':'mismatch'if any(r[k]!=v for k,v in actual.items())else'pass','fields':{k:{'matches':r[k]==v,'actual':v,'recorded':r[k]}for k,v in actual.items()},'prefix_controls':{repr(prefix):h('input',c['input'],prefix)==r['input_hash']for prefix in [b'core.functional.v1',b'core.functional.v1\\0',b'core.functional.v1\0']}})
paths=['code/crates_rs/core_types/src/authority.rs','code/crates_rs/core_contracts/src/kinds.rs','lean4/original_lean_20260809','atlas/coda_atlas/F004_papers','governance/contracts/contract_canonical_definitions/math/functional_layer_boundary.contract.yaml']
receipt={'source_files':inputs,'checks':out,'path_controls':[{'path':p,'exists':(R/p).exists()}for p in paths],'initial_attempt':'Exact spectrum/distance checks passed; script stopped at first Phi1 input hash mismatch before receipt output. This version records all comparisons without asserting expected hashes.','limits':'Exact arithmetic for the13 declared spectrum/distance cases and independent serialization reconstruction for2 fixed records; not a universal numerical error bound or native test execution.'}
(H/(P+'_validation_05.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
