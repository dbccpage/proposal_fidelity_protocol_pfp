"""Exact tensor and Clifford checks for fully reviewed local functions."""
import sys
sys.dont_write_bytecode=True
import ast
from fractions import Fraction
from typing import Dict,List,Sequence
import additional_pfp_tests_remaining_audit as a
b='pfp/tests/normal_forms/'
nodes=[];bindings=[]
for name,symbol in [('test_tranche18_wdw_and_schlafli.py','exact_de_witt_supermetric_contraction'),('test_tranche20_lattice_fermions_and_overlap.py','exact_dirac_gamma_matrices')]:
    p=b+name;t=ast.parse('\n'.join(a.source(p)));node=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==symbol)
    nodes.append(node);bindings.append({'path':p,'sha256':a.row(p)['sha256'],'symbol':symbol,'lines':[node.lineno,node.end_lineno]})
ns={'Fraction':Fraction,'Sequence':Sequence,'Dict':Dict,'List':List}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<read-vetted tensor functions>','exec'),ns)
I=[[Fraction(i==j) for j in range(3)] for i in range(3)]
G=[[2*v for v in row] for row in I]
actual=ns['exact_de_witt_supermetric_contraction'](G,I,I)
expected=sum(((G[i][k]*G[j][l]+G[i][l]*G[j][k])/2-G[i][j]*G[k][l])*I[i][j]*I[k][l] for i in range(3) for j in range(3) for k in range(3) for l in range(3))
assert actual==-6 and expected==-24
zero_accepted=ns['exact_de_witt_supermetric_contraction']([[Fraction(0)]*3 for _ in range(3)],I,I)
assert zero_accepted==-6
gammas=ns['exact_dirac_gamma_matrices']()
def anti(A,B):return [[sum(A[i][k]*B[k][j]+B[i][k]*A[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
off=anti(gammas['gamma_1'],gammas['gamma_4'])
assert any(v for row in off for v in row)
assert not any(v for row in anti(gammas['gamma_5'],gammas['gamma_1']) for v in row)
a.write('_probe12.json',{'runtime':sys.version,'sources':bindings,'dewitt':{'gamma_diagonal':[2,2,2],'pi_a_and_pi_b':'I3','actual':str(actual),'expected_from_displayed_contravariant_tensor_formula':str(expected),'zero_metric_accepted_result':str(zero_accepted),'interpretation':'The declared formula uses supplied gamma as contravariant coefficients; regardless of covariant/inverse convention, the implementation never reads gamma.'},'clifford':{'available':list(gammas),'gamma1_gamma4_anticommutator':[[str(v) for v in row] for row in off],'required_for_distinct_Euclidean_indices':'zero4x4','tested_gamma5_gamma1_anticommutator_is_zero':True},'limits':['Exact Fraction arithmetic over read-vetted test-local functions only.','No physical simulation, production owner/native code or external references used.']})
print('ignored metric and failed Clifford pair controls confirmed')
