"""Exact finite controls and bounded IEEE arithmetic; never imports original code."""
import hashlib,json,pathlib,sys,math,itertools
from fractions import Fraction as Q
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_rust_ooutwire_remaining';fs=json.loads((H/(P+'_scope.json')).read_text())['files'];out=[]
def record(i,title,observed,indices,limits='Independent mathematical/predicate control; no native execution or general theorem certification.'):
 pins=[]
 for k in indices:
  f=fs[k];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];pins.append({'path':f['path'],'sha256':f['sha256']})
 out.append({'id':f'ROUT-CHECK{i:03d}','title':title,'observed':observed,'source_pins':pins,'limitations':limits})
g=0;atol=1;components=[1]*5;paper_bounds=[0]*5;violated=any(a>b+atol for a,b in zip(components,paper_bounds));assembly=1+1+2*1*1+1;m_used=max(0,assembly)if violated else 0
assert not violated and assembly==5 and m_used==0
record(15,'Tolerance does not make the reported coefficient dominate measured assembly',{'g':g,'atol':atol,'components':components,'violated':violated,'assembled_m':assembly,'m_used':m_used},[4])
p=2**126;d=5;assert Q(p,d).denominator==5
wrapped=((p*d+2**127)%2**128)-2**127;assert wrapped==p
outside=math.isqrt(wrapped);assert outside**2==wrapped
wrong=Q(outside,d);ratio=wrong**2/Q(p,d);assert ratio==Q(1,5)
record(16,'Unchecked i128 product changes exact square root',{'input':str(Q(p,d)),'unbounded_product':str(p*d),'wrapped_i128_product':str(wrapped),'returned_surd_as_rational':str(wrong),'square_divided_by_input':str(ratio),'checked_profile':'overflow panic'},[15,14],'Independent fixed-width emulation. Valid Rational is representable; source p*d is unchecked. Runtime profile determines panic versus wrap; no native build was run.')
degree=2**32-1;wrapped_degree=(degree+1)%2**32;assert wrapped_degree==0
record(17,'Sparse polynomial degree overflows without a large polynomial',{'left_monomial_degree':degree,'right_monomial_degree':1,'mathematical_product_degree':degree+1,'unchecked_product_degree':wrapped_degree,'checked_profile':'overflow panic'},[16])
packet={'rows':1,'cols':1,'data':[]};shape_ok=(packet['rows'],packet['cols'])==(1,1);storage_ok=len(packet['data'])==packet['rows']*packet['cols'];assert shape_ok and not storage_ok
record(18,'Observation shape validation misses malformed storage',{'public_matrix':packet,'observe_residual_shape_gate':shape_ok,'storage_gate_needed':storage_ok,'next_multiplication_first_index':0,'available_entries':0},[2,8],'Predicate control of the actual admission gap; Rust indexing panic inferred from read matrix body, not executed.')
dims={'a':2,'b':2,'c':2};support=['a','b','c'];shape=(8,8);accept=all(s in dims for s in support)and shape==(math.prod(dims[s]for s in support),)*2
assert accept and len(support)>2
record(19,'Lattice validator admits a public three-local term',{'dimensions':dims,'support':support,'operator':'Z tensor I tensor I, Hermitian 8x8','product_state':'|0><0| on each site','unique_nonempty_label':'three','validate_terms_accepts':accept,'LocalHamiltonianTerm_new_would_reject':True,'additional_nonhermitian_case':'support[a], operator[[0,1],[0,0]] also passes shape-only lattice validator'},[13])
phase=-2.0*sys.float_info.max;assert not math.isfinite(phase)
record(20,'Finite evolution inputs produce an infinite phase argument',{'Hamiltonian':'1x1 [2]','time':repr(sys.float_info.max),'eigen_residual':0,'phase_product':str(phase),'source_checks_after_phase':'none; Ok is unconditional','expected_Rust_trigonometric_result':'NaN'},[10],'Python evaluates only IEEE product. NaN output is source-based inference for Rust sin/cos(infinity); no original function or libc probe executed.')
t=1e200;nu=0.;g=1.;rhs=nu*t-24.*g*g*t*t;margin=0.-rhs;assert rhs==-math.inf and margin==math.inf and margin>=-1e-9
record(21,'Overflow creates a vacuous green lower-bound comparison',{'Hamiltonian':'I4 as one two-site term','product_state':'|00><00|','time':repr(t),'nu_e':nu,'full_incident_g':g,'signed_rhs':str(rhs),'margin':str(margin),'bound_satisfied':True},[13],'Independent final-expression control. Identity Hamiltonian has exact zero defect and finite phase t; full numerical eigensolver/evolution path not executed. This is an unguarded nonfinite diagnostic, not a false finite inequality.')
def mm(a,b):return [[sum(x*y for x,y in zip(row,col))for col in zip(*b)]for row in a]
def sub(a,b):return [[x-y for x,y in zip(ar,br)]for ar,br in zip(a,b)]
def zero(a):return all(x==0 for row in a for x in row)
def tr(a):return list(map(list,zip(*a)))
def eye(n):return [[int(i==j)for j in range(n)]for i in range(n)]
d0=[[1],[1]];omega=[[1],[-1]];dual=[[1],[-1]];d1=[[1,-1]]
assert zero(mm(tr(d0),dual))and mm(tr(dual),omega)==[[2]]and mm(d1,omega)==[[2]]
samples=[Q(i,8)for i in range(-64,65)];mass=[abs(1-a)+abs(-1-a)for a in samples];assert min(mass)==2
d0closed=[[1],[1],[0]];d1closed=[[0,0,1]];wclosed=[[1],[-1],[0]];assert zero(mm(d1closed,d0closed))and zero(mm(d1closed,wclosed))
record(22,'Primal-dual quotient mass2 is distinct from H1 closedness',{'bigon':{'d0':d0,'d1':d1,'omega':omega,'d1omega':2,'H1_class':False,'primal_alpha':0,'dual':[1,-1],'dual_pairing':2},'closed_three_coordinate_example':{'d0':d0closed,'d1':d1closed,'omega':wclosed,'closed':True,'nonexact':True,'distance':2},'independent_grid_points':len(samples),'all_grid_masses_at_least2':True},[2,11],'Exact dual feasibility and equal primal/dual objective certify the all-alpha lower bound by Holder/weak duality; the 129-point grid alone would not. No native solver ran.')
defects=[[1,0,0],[0,1,0],[0,1,0],[0,0,1],[0,0,1],[1,0,0]];watch=[0,1,1,2,2,0];raw=sum(sum(map(abs,d))for d in defects);observed=[sum(abs(x)for k,x in enumerate(d)if k!=w)for d,w in zip(defects,watch)];assert raw==6 and observed==[0]*6
# Sorted section basis (u1x,u1y,u2x,u2y,xx,xy): D duplicates -x.
D=[[0,0,0,0,-1,0],[0,0,0,0,0,-1],[0,0,0,0,-1,0],[0,0,0,0,0,-1]];O=[[0,1,0,0],[0,0,1,0]];OD=mm(O,D);basis=[[int(i==j)]for i in range(6)for j in []]
kernel=[[[int(i==j)]for i in range(6)]for j in range(4)];assert all(zero(mm(OD,v))and zero(mm(D,v))for v in kernel);assert OD==[[0,0,0,0,0,-1],[0,0,0,0,-1,0]]
record(23,'Observers can miss all defects; coupled attainable defects change adequacy',{'six_edge_raw':raw,'six_edge_observed':observed,'coupled_D':D,'coupled_O':O,'OD':OD,'kernel_basis':'first four coordinate vectors','kernel_dimension':4,'ker_OD_subset_ker_D':True,'each_edge_kernel_dimension':1,'fragmentation_identity_observers_on_two_edges':{'raw':2,'max_J':1,'edgewise_loss':0,'fragmentation':1}},[11],'The displayed exact matrix identities and basis description establish containment for this finite carrier; this is stronger than sampling but is not global detector adequacy.')
J1=[[0,0,0],[0,0,-1],[0,1,0]];J2=[[0,0,1],[0,0,0],[-1,0,0]];J3=[[0,-1,0],[1,0,0],[0,0,0]]
comm=sub(mm(J1,sub(J2,J1)),mm(sub(J2,J1),J1));assert comm==J3
rots=[[[1,0,0],[0,-1,0],[0,0,-1]],[[-1,0,0],[0,1,0],[0,0,-1]],[[-1,0,0],[0,-1,0],[0,0,1]]];W=eye(3)
for u,v in [(0,1),(1,2),(2,0)]:W=mm(W,mm(tr(rots[u]),rots[v]))
assert W==eye(3)
record(24,'Linear gauge ansatz and group pure gauge have different curvature conclusions',{'chi':['0','J1','J2'],'linear_d1A':'zero from d1d0=0','corner_commutator':comm,'group_closed_loop_holonomy':W,'transition_twist_norm':4,'quotient_annotation':2,'annotation_is_not_derived':True},[6],'Exact finite rational matrix identities; no gauge-covariance, cellular realization or cohomology theorem follows from the corner polynomial.')
def Pi(v):x,y,z=v;return (x,y,x*x)
def quarter(v):x,y,z=v;return (z,y,-x)
v=(1,0,1);once=Pi(quarter(v));twice=Pi(quarter(once));halfturn=Pi(quarter(quarter(v)));assert twice==(1,0,1)and halfturn==(-1,0,1)
record(25,'Nonlinear retraction breaks the projected semigroup identity',{'initial':v,'two_projected_quarter_turns':twice,'one_projected_half_turn':halfturn,'defect':tuple(a-b for a,b in zip(halfturn,twice)),'chart_field':'(x^2,0)','chart_derivative':'diag(2x,0)'},[16],'One exact admitted graph retraction and rotation counterexample; no universal claim that every projection destroys a semigroup.')
grid=list(itertools.product((-1,0,1),repeat=2));assert len(grid)==9
unweighted=lambda x:sum(map(abs,x));weighted=lambda x:2*unweighted(x)
assert all(unweighted(x)==sum(unweighted((a,))for a in x)for x in grid)
assert weighted((1,))!=abs(1)and math.sqrt(2)!=2
record(26,'Replica controls separate additivity from singleton calibration',{'grid_points':9,'unweighted_l1_additive':True,'weighted_2l1_additive':True,'weighted_singleton_value':2,'singleton_gauge':1,'l2_two_singletons':{'union':'sqrt(2)','sum':2},'audit_exhaustion_method_has_failure_gate':False,'failed_RE3_search_returns_at_first_counterexample':True},[15],'Finite controls do not prove the sampled RE1-RE5 characterization universally. Exhaustion metadata gap is source-confirmed; no forged Rust instance executed.')
result={'execution_kind':'independent_bounded_controls','controls':out,'all_assertions_passed':True,'helper_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()};(H/(P+'_checks04.json')).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'controls':len(out),'all_assertions_passed':True}))
