"""Bounded test-local algebra controls; no imported production or native owners."""
import sys
sys.dont_write_bytecode=True
import ast
from dataclasses import dataclass
from fractions import Fraction
import additional_pfp_tests_remaining_audit as a
b='pfp/tests/normal_forms/'
selection=[('test_tranche10_derivation_and_motion.py','is_contractive'),('test_tranche11_cdt_and_quantum_gravity.py','PachnerMove'),('test_tranche12_representation_and_runtime.py','LyndonWord'),('test_tranche13_adversarial_and_rust_parity.py','bareiss_det')]
nodes=[];bindings=[]
for name,symbol in selection:
    p=b+name;t=ast.parse('\n'.join(a.source(p)))
    found=[x for x in ast.walk(t) if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==symbol]
    assert len(found)==1
    nodes+=found;bindings.append({'path':p,'sha256':a.row(p)['sha256'],'symbol':symbol,'lines':[found[0].lineno,found[0].end_lineno]})
ns={'dataclass':dataclass,'Fraction':Fraction,'__name__':__name__}
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<read-vetted local arithmetic>','exec'),ns)
assert ns['is_contractive'](Fraction(10),Fraction(-1))
f=lambda x:x*x
x=Fraction(9,10);y=Fraction(1)
ratio=abs(f(x)-f(y))/abs(x-y)
assert ratio==Fraction(19,10) and ns['is_contractive'](Fraction(1,2),f(Fraction(1,2)))
pachner=[]
for pair in [(0,6),(-1,7),(Fraction(5,2),Fraction(7,2))]:
    result=ns['PachnerMove'](4,*pair).is_valid_4d();assert result
    pachner.append({'initial':str(pair[0]),'final':str(pair[1]),'accepted':result})
word=ns['LyndonWord'].from_cycle('0101').canonical_representation
assert word=='0101' and word[2:]+word[:2]==word
det=ns['bareiss_det']([[0,1],[1,0]])
assert det==1
try:ns['bareiss_det']([[0,0,0],[0,0,0],[0,0,0]])
except ZeroDivisionError:zero_result='ZeroDivisionError'
else:raise AssertionError('expected singular pivot division failure')
a.write('_probe10.json',{'runtime':sys.version,'sources':bindings,'descent':{'negative_metric_admitted':True,'square_map_half_to_quarter_admitted':True,'square_map_distance_ratio_on_0.9_and_1':str(ratio),'square_map_fixed_points':[0,1]},'pachner':pachner,'lyndon':{'canonical':word,'nontrivial_rotation_by_2_equals_word':True,'strict_lyndon':False},'bareiss':{'swap_matrix':[[0,1],[1,0]],'returned':det,'independent_2x2_determinant':-1,'zero_3x3_result':zero_result},'limits':['Only read-vetted test-local definitions extracted; no native/Rust execution or production source imports.','Finite algebra controls do not claim a general test-suite run.']})
print('descent, invalid Pachner counts, periodic word and Bareiss controls confirmed')
