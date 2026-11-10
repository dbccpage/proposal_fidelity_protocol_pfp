"""Independent in-memory mathematics and branch controls. No retained program executed."""
import hashlib,json,pathlib,sys
from fractions import Fraction as Q
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,k,obs,limits):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'OPSKILL-CHECK-{k:03}','status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':obs,'limitations':limits})
c=[Q(1),Q(0),Q(0)];psi=[Q(0),Q(2),Q(-1)];d=[psi[1]-psi[0],psi[2]-psi[1],psi[0]-psi[2]];c2=[a-b for a,b in zip(c,d)];assert sum(c)==sum(c2)==1
# Triangle cycle: |sum residual| <= L1 residual, and any residual with this cycle sum is reachable; one-edge concentration attains it.
add(198,37,{'c':list(map(str,c)),'dpsi':list(map(str,d)),'c_minus_dpsi':list(map(str,c2)),'exact_Phi_before':'1','exact_Phi_after':'1','strict_descent':False},'Exact triangle counterexample plus change-of-variable argument: inf_phi ||c-dpsi-dphi|| equals inf_eta ||c-deta|| for all admitted potentials. No solver/owner execution.')
zero=[0,0,0];assert all(abs(x)<=1 for x in zero)and sum(a*b for a,b in zip(c,zero))==0
add(198,38,{'dual_witness':zero,'annihilation':True,'box_bound':True,'dual_objective':0,'primal_optimum':1,'gap':1},'Dual feasibility is only a lower bound, not a complete optimality certificate. Positive triangle optimum established in CHECK-037.')
def accept(resp):
 if 'schema_id'not in resp or resp.get('schema_id')!='SPK-001':return False
 val=resp.get('candidate',{}).get('answer')
 if isinstance(val,float):return False
 if isinstance(val,bool)and not isinstance(val,int):return False
 return True
cases=[{'schema_id':'SPK-001','candidate':{'answer':True}},{'schema_id':'SPK-001'},{'schema_id':'SPK-001','candidate':{'answer':'x'}},{'schema_id':'SPK-001','candidate':{'answer':None}}];assert all(map(accept,cases))
add(204,39,{'invalid_candidates':cases,'accepted':list(map(accept,cases))},'Exact branch mirror of the nested toy validator, not production validation or retained checker execution.')
m=2**63-1;lhs=m-1;intermediate=lhs%m+m;assert intermediate>m
add(190,40,{'signed_i64_max':m,'modulus':m,'lhs':lhs,'intermediate_lhs_mod_m_plus_m':intermediate,'outside_signed_i64':True,'correct_remainder':lhs},'Mathematical integer calculation exposes fixed-width intermediate overflow; Python itself has unbounded integers. No native build.')
A=[[int(i!=j)for j in range(4)]for i in range(4)];vecs=[[1,1,1,1],[1,-1,0,0],[0,1,-1,0],[0,0,1,-1]];eig=[3,-1,-1,-1]
for v,l in zip(vecs,eig):assert [sum(a*b for a,b in zip(row,v))for row in A]==[l*x for x in v]
add(190,41,{'graph':'K4','degree':3,'independent_eigenvectors':vecs,'eigenvalues':eig,'disjoint_union_spectrum':'Every k-copy graph has masses 1/4 at 3 and 3/4 at -1; these do not change with k.'},'Exact eigenvectors form a basis. Disjoint unions give a deterministic regular-graph sequence contradicting unqualified Kesten--McKay universality. No random/locally-tree-like assumption was admitted.')
before=Q(7);after=Q(7);assert after-before<=0 and not after<before
add(193,42,{'before':'7','after':'7','declared_nonpositive_descent':True,'actual_strict_descent':False},'Direct exact predicate comparison; nonpositive includes stationary. No termination of a concrete workflow is asserted.')
reservation=Q(5,1000);committed=Q(0);cost=Q(-1);committed+=cost;reservation-=cost;assert committed<0
add(204,43,{'reported_cost':'-1','committed_after':str(committed),'reservation_after':str(reservation),'halted':False},'Exact arithmetic mirror of mock ledger branch; no real money, provider, runtime ledger or retained checker involved.')
(H/(P+'_checks06.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))
