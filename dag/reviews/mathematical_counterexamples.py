"""Small independent counterexamples to particular written claims; no QM key."""
from fractions import Fraction as F
from pathlib import Path
import json,sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from pfp.domain.cohomology.certificate_checker import check_certificate

findings=[]
def sign(n):return -1 if n%2 else 1
nplus,nminus=1,0
assert sign(nplus-nminus)==sign(nminus-nplus)==-1
findings.append({'claim':'PFP011 sign cancellation from swapping N_plus and N_minus',
                 'counterexample':{'N_plus':1,'N_minus':0,'sign_before':-1,'sign_after':-1},
                 'conclusion':'Swapping negates the integer exponent and preserves parity; it does not produce cancellation.'})

left_path=F(1,2)*F(1,2);right_path=F(1,2)*F(1,2);direct=F(0)
assert left_path-right_path==0 and left_path-direct==F(1,4) and right_path-direct==F(1,4)
findings.append({'claim':'non-PFP004 zero diamond branch difference iff declared diamond flatness',
                 'counterexample':{'all_cover_maps':'1/2','direct_bottom_top_map':'0','branch_difference':'0',
                                   'left_composition_defect':'1/4','right_composition_defect':'1/4'},
                 'conclusion':'Equal path products do not imply equality to the supplied direct restriction map.'})

case={'challenge':'c011','case_id':'dual_support_counterexample','nodes':['a','b','c'],
      'edges':[['a','b'],['b','c'],['c','a']],
      'claims':{'a->b':3,'b->c':0,'c->a':0},'weights':{'a->b':1,'b->c':1,'c->a':1}}
certificate={'status':'SOLVED','phi1':3,'potential':{'a':0,'b':0,'c':0},
             'repair':{'a->b':3,'b->c':0,'c->a':0},'dual':{'a->b':1,'b->c':1,'c->a':1}}
assert check_certificate(case,certificate).passed
assert sum(v!=0 for v in certificate['repair'].values())==1
assert sum(v!=0 for v in certificate['dual'].values())==3
findings.append({'claim':'non-PFP002 dual support must lie on primal residual support',
                 'counterexample':{'case':case,'certificate':certificate,'independent_C011_checker':'PASS'},
                 'conclusion':'Optimal dual coordinates can be nonzero on edges with zero residual.'})

tree_reduced_incidence=F(-1);tree_inverse=1/tree_reduced_incidence
assert tree_inverse==-1
findings.append({'claim':'PFP017 arbitrary oriented tree reduced incidence inverse has only 0/1 entries',
                 'counterexample':{'root':'a','other_vertex':'b','edge':'b->a','d0_convention':'potential(head)-potential(tail)',
                                   'reduced_incidence':[[-1]],'inverse':[[-1]]},
                 'conclusion':'Reversing an edge introduces a negative sign; entries are not restricted to 0/1.'})

result={'source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120','status':'four_counterexamples_confirmed',
        'scope':'Counterexamples apply to the exact statements and conventions identified by the paper audit. They do not invalidate every result or implementation in those papers.',
        'counterexamples':findings}
(ROOT/'dag/reviews/mathematical_counterexamples.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'count':len(findings)}))
