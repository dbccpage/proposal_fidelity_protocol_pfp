"""Independent exact finite countermodels; no retained owner import/execution."""
import hashlib,json,pathlib,sys,re
from fractions import Fraction as F
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,k,observation,limits):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'OPSKILL-CHECK-{k:03}','status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':observation,'limitations':limits})
def mm(a,b):return [[sum(x*y for x,y in zip(row,col))for col in zip(*b)]for row in a]
def plus(a,b):return [[x+y for x,y in zip(r,s)]for r,s in zip(a,b)]
def scale(c,a):return [[c*x for x in row]for row in a]
def tr(a):return sum(a[i][i]for i in range(len(a)))
I=[[F(1),F(0)],[F(0),F(1)]];P0=[[F(1),F(0)],[F(0),F(0)]];Pplus=[[F(1,2),F(1,2)],[F(1,2),F(1,2)]]
rho=[[F(1,3),F(0)],[F(0),F(2,3)]]
channel=lambda a:plus(scale(a[0][0],P0),scale(a[1][1],Pplus))
sigma=channel(rho);B=channel(P0);assert B==P0 and tr(sigma)==1 and sigma[0][0]*sigma[1][1]-sigma[0][1]**2==F(1,9)
# Kraus K0=|0><0|, K1=(|0>+|1>)<1|/sqrt(2).
# Verify without irrational arithmetic: K1 numerator N, K1†K1=N†N/2.
N=[[F(0),F(1)],[F(0),F(1)]];Nt=list(map(list,zip(*N)));assert plus(mm(P0,P0),scale(F(1,2),mm(Nt,N)))==I
for a in (rho,P0):assert plus(mm(mm(P0,a),P0),scale(F(1,2),mm(mm(N,a),Nt)))==channel(a)
# sqrt(sigma)=(sigma+I/3)/sqrt(5/3). Its square and positivity are checked exactly.
M=plus(sigma,scale(F(1,3),I));assert scale(F(3,5),mm(M,M))==sigma
assert M[0][0]>0 and M[0][0]*M[1][1]-M[0][1]**2>0
first=tr(mm(sigma,mm(B,B)));second=F(3,5)*tr(mm(mm(mm(M,B),M),B));skew=first-second;assert skew==F(1,15)
assert mm(rho,P0)==mm(P0,rho) # initial square root also diagonal, so initial skew=0.
add(351,50,{'definition':'I_rho(H)=Tr(rho H^2)-Tr(sqrt(rho) H sqrt(rho) H)','rho':rho,'H':P0,'channel':'E(A)=A00*|0><0|+A11*|+><+|','kraus':['|0><0|','(|0>+|1>)<1|/sqrt(2)'],'sum_Kdagger_K':I,'E_rho':sigma,'E_H':B,'H_held_fixed_by_channel':True,'E_rho_positive_determinant':F(1,9),'sqrt_E_rho':'(E(rho)+I/3)/sqrt(5/3)','initial_skew_information':0,'final_first_term':first,'final_second_term':second,'final_skew_information':skew,'claimed_nonincrease':False},'Exact admitted2x2 quantum matrices. Refutes the source inequality with its own simultaneous state/observable Schrödinger-channel action, even though H happens to be fixed. Does not refute monotone Riemannian metrics with their correct tangent-vector transport, or restricted covariance/observable-preservation theorems. Both density states are positive definite. No physical premise derived.')
zero=[[F(0)]];assert mm(zero,zero)==zero
add(351,51,{'C0_C1_C2':'Q each','d0':zero,'d1':zero,'d1_d0':zero,'kernel_d1_dimension':1,'image_d0_dimension':0,'H1_dimension':1},'Separates nilpotence from exactness. Source says exact complexes with d²=0; that wording can be read as imposing both, so this is a missing-definition/control warning, not proof that its sentence explicitly asserts an implication.')
D=[[-1,1,0],[0,-1,1],[1,0,-1]];local=[0,1,2];diff=[sum(x*y for x,y in zip(row,local))for row in D];assert diff==[1,1,-2] and sum(diff)==0
add(354,52,{'local_sections':local,'edge_differences':diff,'triangle_coboundary_sum':sum(diff),'pairwise_equal':False},'Exact additive coefficient triangle: delta(delta(s))=0 follows nilpotence and does not imply delta(s)=0. It refutes the claimed equivalence between closed overlap-difference cochains and pairwise agreement, not the valid cochain trichotomy.')
add(354,53,{'space':'three-vertex circle with three edges and no faces','constant_sheaf_coefficients':'Q','d0':D,'d1':'zero to C2=0','rank_d0':2,'H1_dimension':1,'nonempty_global_sections':'all constant vertex assignments, including0'},'Ordinary sheaf/cochain counterexample to nonzero H1-group iff no global sections. A distinguished contextuality obstruction class requires a separate support model and construction; no such identification is supplied by the quoted formula.')
add(353,54,{'J':[[-1]],'DF':[[-1]],'determinants_equal':True,'positive':False},'Equality of two determinants alone cannot prove positivity or eliminate a sign problem. Does not refute positivity under additional independently checked model premises.')
Q=[[F(0),F(1)],[F(0),F(0)]];Qd=list(map(list,zip(*Q)));ham=scale(F(1,2),I);assert plus(mm(Q,Qd),mm(Qd,Q))==scale(2,ham);assert mm(Q,Q)==[[0,0],[0,0]]
add(353,55,{'Q':Q,'Qdagger':Qd,'H':ham,'anticommutator':I,'Q_squared':mm(Q,Q),'psi':[0,1],'Q_psi':[1,0]},'The stated superalgebra does not force Q psi=0 for every state. An admitted zero-energy physical-state condition would change the conclusion; it is not implied by the algebra alone.')
pairs=[(4,1),(3,2),(2,3),(1,4)];assert all(p+q==5 for p,q in pairs)
add(353,56,{'source_move_counts':pairs,'counts_sum':5,'four_dimensional_bistellar_required_sum':6,'four_dimensional_pairs':[(1,5),(2,4),(3,3),(4,2),(5,1)]},'Combinatorial d-dimensional Pachner replacement splits the d+2 facets of a(d+1)-simplex; quoted counts fit dimension3, not4. No triangulation engine run.')
add(351,57,{'dimension':3,'rho':'I/3','trace_each_phase_point_operator':1,'source_W_each':F(1,3),'phase_space_cells':9,'source_W_sum':3,'normalized_W_each':F(1,9)},'Uses the stated Weyl phase-point normalization with only identity displacement having nonzero trace. The displayed W lacks1/d; characteristic2 also lacks inverse2. No finite-phase or physical correspondence theorem asserted.')
quoted="'gt:test'";double_only=re.match(r'^\s*-\s*"?([^"]+)"?\s*$', '  - '+quoted).group(1);assert not double_only.startswith('gt:')
add(352,58,{'valid_single_quoted_alias':quoted,'after_double_quote_only_strip':double_only,'recognized_as_gt_alias':False,'status_mapping':'MANUAL -> VERIFIED'},'Isolated lexical consequence of source mapping, no file rewrite or retained script execution. Evidence status changes require new evidence, not vocabulary normalization.')
(H/(P+'_checks08.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2,default=str)+'\n');print(json.dumps({'observed':len(out)}))
