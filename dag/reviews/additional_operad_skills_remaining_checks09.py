"""Pure source-predicate and exact algebra controls, no retained owner invocation."""
import ast,hashlib,json,pathlib,re,sys
from dataclasses import dataclass
from fractions import Fraction as F
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,k,o,l):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'OPSKILL-CHECK-{k:03}','status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':o,'limitations':l})
path='engine/research/published/004_projection_obstruction/001_from_covering_edge_descent_complexes_to_functorial_presheaves_and_coherence_defects.md';parts=path.split('/');below=parts[parts.index('published')+1:];assert len(below)==2
add(357,59,{'indexed_source_path':path,'below_published_parts':below,'encyclopedia_overview_predicate':True,'retained_for_extraction':False},'Exact path predicate applied to a path actually present in scoped spine_index.md:207. Does not assert the linked paper currently exists or execute the generator.')
mixed='"ENC-0001", ENC-9999';items=[m.group(1)or m.group(2)for m in re.finditer(r'"([^"]*)"|\x27([^\x27]*)\x27',mixed)];assert items==['ENC-0001']
add(357,60,{'input_inline_list':'['+mixed+']','parsed_items':items,'dropped_bare_dependency':'ENC-9999'},'Exact isolated inline-list regex; invalid or unsupported mixed input must refuse, not silently remove a dependency. No source parser invoked.')
key=lambda kind,label,name,occ:f'{kind}::{label}::{name}::{occ}'
add(357,61,{'before_statement':'Theorem T (Safe): every accepted candidate is valid','after_statement':'Theorem T (Safe): every candidate is accepted','before_key':key('Theorem','T','Safe',1),'after_key':key('Theorem','T','Safe',1),'body_changed_key_unchanged':True},'Shows absence of body binding in the actual disposition key. It does not assert any historical statement was changed or verdict reused in this checkout.')
@dataclass(frozen=True)
class A: value:int
@dataclass(frozen=True)
class B: value:int
@dataclass(frozen=True)
class Child(A): pass
assert A(1)!=B(1) and A(1)!=Child(1) and A(1)!=1
add(384,62,{'generated_dataclass_equality':{'other_dataclass':A(1)==B(1),'subclass':A(1)==Child(1),'integer':A(1)==1},'explicit_eq_defined_in_source':False},'Fresh synthetic Python dataclasses demonstrate exact-class generated equality. Does not prove every custom equality method safe.')
bad='def __eq__(self, other):\n    "type(self) is not type(other)"\n    return True\n';s=ast.unparse(ast.parse(bad).body[0]);guard='type(self) is not type(other)'in s;assert guard
add(384,63,{'synthetic_method':bad,'guard_substring_present':guard,'method_returns':True},'Exact checker substring on in-memory AST accepts a docstring with no enforcing branch. No source checker invocation.')
roots=['pfp','operations','core','engine_old','the_symbol_game'];selected=[x for x in roots if x.startswith('engine')or x=='the_symbol_game'];assert 'pfp'not in selected
add(393,64,{'candidate_roots':roots,'discovered':selected},'Pure discovery predicate, not a new filesystem census or architecture execution.')
add(381,65,{'d0':[[0]],'d1':[[0]],'omega':[1],'Phi1_inf_alpha_abs_omega_minus_d0alpha':1,'Gamma2':0,'both_forced_zero':False},'Exact quotient distance to image(d0)={0}; nilpotent zero boundary does not force positive residual to vanish.')
add(381,66,{'graph':'one edge, two vertices, no2-faces','d0':[[-1,1]],'omega':[1],'repair_vertex_values':[0,1],'after_residual':[0],'exact_repair_valid':True},'Exact graph repair without2-faces disproves a universal2-face requirement, not the useful demand to bind an actual system residual.')
values=[0,1,2,3];first=[bool(x)for x in values];second=[x!=0 for x in values];assert first==second
add(381,67,{'residues':values,'Some_high_bit_else_none_arm_boolean':first,'not_is_zero_predicate':second},'For correctly specified high_bit/is_zero, match(Some=>true,None=>false) computes a predicate and is not a tautology merely because return arms contain literals.')
Q=[[1,0],[0,0]];W=[[0,0],[0,0]]
add(369,68,{'tangent':'zero subspace','Q':Q,'sign_Q':Q,'V':[[-1,0],[0,0]],'W_signQ_plus_TperpV':W,'operator_norm_W':0,'pairing_W_Q':0,'trace_norm_Q':1,'valid_norm_bound':True,'valid_subgradient':False},'The norm-only recipe does not ensure saturation; full displayed norm+saturation+annihilation certificate is sufficient and remains a positive mechanism.')
add(369,69,{'fixed_tangent':'span(diag(1,-1))','L':'diag(1,-1)','channel':'Hadamard unitary conjugation','E_L':[[0,1],[1,0]],'distance_before':0,'distance_after':2,'min_formula':'min_a 2*sqrt(1+a²)=2'},'Exact norm-preserving channel can increase distance to an untransported tangent. Transporting the tangent or proving invariance restores the relevant contraction argument.')
rows=[('x',5,1,'alpha'),('x',5,1,'beta')];chosen=[sorted(order,key=lambda x:(-x[1],-x[2]))[0][3]for order in (rows,list(reversed(rows)))];assert chosen==['alpha','beta']
add(389,70,{'equal_order_key_rows':rows,'admissible_tied_winners':chosen,'unique_snapshot_defined':False},'Demonstrates missing uniqueness in SQL ordering keys; Python stable sorting illustrates two legal tie resolutions, not an SQLite engine run.')
instance={('a1','b1','c1'),('a2','b1','c2')};ab={(a,b)for a,b,c in instance};bc={(b,c)for a,b,c in instance};joined={(a,b,c)for a,b in ab for bb,c in bc if b==bb};assert len(joined-instance)==2
add(391,71,{'original':sorted(instance),'reconstruction':sorted(joined),'spurious':sorted(joined-instance)},'Positive exact finite relational example from source, independent set operations; not an implementation parity test.')
truths=[True,1,'false',[],False];a=[x is True for x in truths];b=[bool(x)for x in truths];assert a!=b
add(395,72,{'inputs':truths,'strict_true':a,'truthiness':b},'A blanket syntactic rewrite widens the accepted carrier; context-specific Boolean coercion can be intentional but is not semantics-preserving in general.')
(H/(P+'_checks09.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))
