"""Bounded mathematical controls, with no production package initialization."""
import ast,dataclasses,hashlib,itertools,json,math,pathlib,platform,types
from fractions import Fraction
import numpy as np
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';pins={};out=[]
def fragment(path,names,env,constants=False):
 b=(R/path).read_bytes();pins[path]=hashlib.sha256(b).hexdigest();t=ast.parse(b);nodes=[]
 for node in t.body:
  if isinstance(node,(ast.FunctionDef,ast.ClassDef))and node.name in names:nodes.append(node)
  elif constants and isinstance(node,(ast.Assign,ast.AnnAssign)):nodes.append(node)
 env=dict(env);m=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[]);exec(compile(ast.fix_missing_locations(m),path,'exec'),env);return env
def rec(id,name,observed,limits):out.append({'id':id,'name':name,'observed':observed,'result':'reproduced','limitations':limits})
class Box:
 @staticmethod
 def ok(v):return types.SimpleNamespace(is_err=False,unwrap=lambda:v)
 @staticmethod
 def err(e):return types.SimpleNamespace(is_err=True,unwrap_err=lambda:e)
class Matrix:
 def __init__(self,rows,cols,data):self.rows=rows;self.cols=cols;self.data=tuple(tuple(r)for r in data)
 @classmethod
 def from_nested_ints(cls,data):return cls(len(data),len(data[0])if data else 0,data)
 def multiply_matrix(self,b):return Matrix(self.rows,b.cols,[[sum(self.data[i][k]*b.data[k][j]for k in range(self.cols))for j in range(b.cols)]for i in range(self.rows)])
 def multiply_vector(self,x):return tuple(sum(a*b for a,b in zip(row,x))for row in self.data)
 def __eq__(self,b):return(self.rows,self.cols,self.data)==(b.rows,b.cols,b.data)
env={'PfpSolverPort':object,'GenesisCycleSolverPort':object,'Fraction':Fraction,'itertools':itertools,'comb':math.comb,'require_rational':lambda _:None,'Result':Box,'IntegerMatrix':Matrix,'SmithNormalFormResult':lambda **kw:types.SimpleNamespace(**kw),'RefusalCode':types.SimpleNamespace(POLICY_VIOLATION='policy'),'DomainError':lambda *args:args}
maths=fragment('pfp/infrastructure/exact_math.py',['ExactRationalSolver','ExactIntegerSmithNormalFormSolver','rational','vec','dot','mv','transpose','sub','same','l1_certificate'],env)
s=maths['ExactRationalSolver']();mat=Matrix(1,1,[[1]]);omega=types.SimpleNamespace(values=(Fraction(1),));errors={}
for name,args in [('compute_gamma2',(mat,omega)),('compute_phi1',(mat,omega)),('verify_duality_gap',(mat,omega,Fraction(0),(Fraction(0),))),('compute_hodge_decomposition',(mat,mat,omega))]:
 try:getattr(s,name)(*args)
 except NameError as exc:assert 'core'in str(exc);errors[name]=str(exc)
 else:raise AssertionError(name)
rec('PFPINFRA-P028','four_rational_methods_reference_undefined_core',errors,'Actual method bodies with minimal shape DTOs; no domain constructors or runtime import path exercised.')
snf=maths['ExactIntegerSmithNormalFormSolver']();count=0
for values in itertools.product(range(-2,3),repeat=4):
 a,b,c,d=values;mat=Matrix(2,2,[[a,b],[c,d]]);res=snf.compute_snf(mat);assert not res.is_err,res.unwrap_err()if res.is_err else None;v=res.unwrap();g=math.gcd(*values);det=abs(a*d-b*c);expected=()if g==0 else(g,)if det==0 else(g,det//g)
 assert v.invariant_factors==expected,(values,v.invariant_factors,expected)
 identity=Matrix(2,2,[[1,0],[0,1]]);assert v.v.multiply_matrix(v.v_inv)==identity;assert v.u.multiply_matrix(mat).multiply_matrix(v.v)==v.d
 assert abs(v.u.data[0][0]*v.u.data[1][1]-v.u.data[0][1]*v.u.data[1][0])==1;count+=1
rec('PFPINFRA-P029','snf_625_small_integer_matrices_match_independent_minors',{'cases':count,'entry_domain':[-2,-1,0,1,2],'matrix_shape':[2,2],'checks':['gcd entries and absolute determinant invariant factors','UAV=D','det(U)=+-1','V*V_inverse=I']},'Finite control only, minimal exact matrix/result DTOs injected; no general SNF termination proof or domain serialization test.')
cycle=[[-1,1,0],[0,-1,1],[1,0,-1]];w=[1,1,1];cert={'alpha':[0,0,0],'dual':[1,1,1],'residual':[1,1,1],'value':3};value=maths['l1_certificate'](cycle,w,cert);assert value==3
bad={**cert,'value':0}
try:maths['l1_certificate'](cycle,w,bad)
except ValueError as exc:rejection=str(exc)
else:raise AssertionError('bad optimum accepted')
rec('PFPINFRA-P030','exact_l1_zero_gap_positive_and_tampered_value_control',{'accepted_value':str(value),'tampered_refusal':rejection},'Specific rational3cycle only; mathematical sufficiency follows weak duality under this supplied linear model, not physical encoding.')
def parsed(_):
 return types.SimpleNamespace(num_qubits=2,hamiltonian=types.SimpleNamespace(terms=[types.SimpleNamespace(weight=Fraction(1),target_sign=1,pauli=types.SimpleNamespace(word='ZI')),types.SimpleNamespace(weight=Fraction(10**15),target_sign=1,pauli=types.SimpleNamespace(word='IZ'))]))
dense=fragment('pfp/infrastructure/quantum/dense_checker.py',['pauli_to_matrix','build_dense_hamiltonian','verify_dense_spectrum'],{'np':np,'Fraction':Fraction,'parse_challenge':parsed},True)
r=dense['verify_dense_spectrum']({}, {'status':'SOLVED','energy':[0,1],'degeneracy':2});assert r['dense_check']=='PASSED'and r['dense_multiplicity']==2
rec('PFPINFRA-P031','large_scale_hamiltonian_false_degeneracy_agreement',{'diagonal_exact':[0,10**15,1,10**15+1],'true_ground_multiplicity':1,'reported':r},'Read-vetted numeric body with injected admitted-style2qubit positive rational Pauli terms; no domain parser rerun. Evidence is explicitly SECONDARY_NUMERIC, not a formal certificate.')
(H/(P+'_checks05.json')).write_text(json.dumps({'python':platform.python_version(),'numpy':np.__version__,'source_pins':pins,'method':'Fully read source AST definitions with minimal in-memory DTOs and independent integer minors/diagonal controls. No source edits, production package imports, native/provider/private reads.','controls':out},indent=2)+'\n');print(json.dumps({'controls':len(out),'all_reproduced':True,'small_matrix_cases':count}))
