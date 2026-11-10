"""Bounded independent arithmetic and synthetic unittest lifecycle; originals inert."""
import sys
sys.dont_write_bytecode=True
import json,hashlib,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
captured={}
class SyntheticFailure(unittest.TestCase):
    def test_deliberate_failure(self): self.assertTrue(False)
    @classmethod
    def tearDownClass(cls): captured.update(all_properties_satisfied=True,status='PASS')
result=unittest.TestResult()
unittest.defaultTestLoader.loadTestsFromTestCase(SyntheticFailure).run(result)
assert len(result.failures)==1 and captured['all_properties_satisfied']
# Filled oriented triangle, edges01,12,20: d1=(1,1,1).
h=(1,1,1); exact=(3,5,-8)
dot=sum(x*y for x,y in zip(exact,h));curl=sum(h)
assert dot==0 and curl==3
out={'method':'Independent integer cochain arithmetic and synthetic stdlib unittest lifecycle only','synthetic_teardown':{'tests_run':result.testsRun,'failures':len(result.failures),'receipt':captured},'filled_triangle':{'edges':[[0,1],[1,2],[2,0]],'face':[0,1,2],'h':h,'exact':exact,'inner_product':dot,'d1_h':curl,'harmonic':False},'source_bindings':[],'limits':'No actual test suite or production owner import/execution. Synthetic failure is intentional audit control, not an original-suite result.'}
for p in ['pfp/tests/normal_forms/test_physics_fermion_optimization_and_hodge.py','pfp/tests/normal_forms/test_tsnf_property_and_euler_poincare.py','pfp/tests/normal_forms/test_tsnf_3complex_and_euler_poincare.py']:
 out['source_bindings'].append({'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()})
(ROOT/'dag/reviews/additional_pfp_tests_remaining_probe03.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps(out,indent=2))
