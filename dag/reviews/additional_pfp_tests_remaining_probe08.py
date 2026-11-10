"""Finite exact controls for fully read category/physics test-local claims."""
import sys
sys.dont_write_bytecode=True
import ast
from dataclasses import dataclass
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/normal_forms/test_tranche5_sheaf_and_categories.py'
t=ast.parse('\n'.join(a.source(p)))
nodes=[x for x in t.body if isinstance(x,ast.ClassDef) and x.name in ('SchemaObject','SchemaMorphism')]
assert [(x.name,x.lineno,x.end_lineno) for x in nodes]==[('SchemaObject',33,43),('SchemaMorphism',47,79)]
ns={'dataclass':dataclass,'__name__':__name__}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<read-vetted morphism classes>','exec'),ns)
Obj=ns['SchemaObject'];Mor=ns['SchemaMorphism']
s=Obj('source',frozenset({'a','b'}));d=Obj('target',frozenset({'y','z'}))
f=Mor(s,d,(('z','b'),('y','a')));identity=Mor(s,s,(('a','a'),('b','b')))
fi=f.compose(identity)
assert f.mapping != fi.mapping and dict(f.mapping)==dict(fi.mapping) and f!=fi
I=[[1,0],[0,1]];g1=[[0,1],[1,0]];g2=[[0,-1j],[1j,0]]
def mul(A,B):return [[sum(A[i][k]*B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
def add(A,B):return [[A[i][j]+B[i][j] for j in range(2)] for i in range(2)]
def dagger(A):return [[complex(A[j][i]).conjugate() for j in range(2)] for i in range(2)]
def scale(A,c):return [[c*v for v in row] for row in A]
A=add(I,mul(g1,g2))
ad1=scale(mul(mul(A,g1),dagger(A)),.5)
ad2=scale(mul(mul(A,g2),dagger(A)),.5)
assert ad1==scale(g2,-1) and ad2==g1
H=[[0 if i==j else -1 for j in range(3)] for i in range(3)]
assert all(H[i][j]<=0 for i in range(3) for j in range(3) if i!=j)
a.write('_probe08.json',{'runtime':sys.version,'sources':[{'path':p,'sha256':a.row(p)['sha256'],'extracted_ranges':[[33,43],[47,79]]},{'path':'pfp/tests/normal_forms/test_tranche6_physics_and_gauge_complexes.py','sha256':a.row('pfp/tests/normal_forms/test_tranche6_physics_and_gauge_complexes.py')['sha256'],'claim_ranges':[[179,228],[324,339]]}], 'morphism_identity':{'input_mapping':f.mapping,'composed_mapping':fi.mapping,'equal_as_dict':True,'equal_under_declared_object_equality':False},'negative_triangle':{'off_diagonal':-1,'cycle_sign':-1,'identity_gauge_is_stoquastic':True},'majorana':{'representation':'gamma1=sigma_x, gamma2=sigma_y; B=(I+gamma1 gamma2)/sqrt(2)','exact_dyadic_matrix_checks':True,'B_gamma1_Bdagger':'-gamma2','B_gamma2_Bdagger':'gamma1','test_local_braid_corresponds_to_inverse_convention':True},'limits':['Category counterexample uses valid injective attribute map with unsorted tuple presentation.','Physics controls are exact finite algebra under the explicitly stated representation, not physical model simulations or native tests.','No original imports or external sources.']})
print('morphism identity, stoquastic-cycle and Majorana sign controls confirmed')
