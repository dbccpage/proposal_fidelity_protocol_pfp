"""Small exact controls for reviewed flow, automata and Bell examples."""
import sys
sys.dont_write_bytecode=True
import ast
from fractions import Fraction
import additional_pfp_tests_remaining_audit as a
b='pfp/tests/normal_forms/'
p=b+'test_tranche23_flow_control_and_horizon_emission.py'
t=ast.parse('\n'.join(a.source(p)));node=next(x for x in t.body if isinstance(x,ast.ClassDef) and x.name=='LeakyBucket')
ns={'Fraction':Fraction};exec(compile(ast.Module(body=[node],type_ignores=[]),'<read-vetted local bucket>','exec'),ns)
bucket=ns['LeakyBucket'](Fraction(10),Fraction(2))
negative=bucket.add(Fraction(-100),Fraction(0));after_negative=bucket.water
oversize=bucket.add(Fraction(100),Fraction(0));assert negative and oversize and after_negative==-100
capacities={('s','a'):3,('s','b'):2,('a','t'):2,('b','t'):3}
cut=lambda S:sum(c for (u,v),c in capacities.items() if u in S and v not in S)
assert cut({'s','a'})==4 and cut({'s','b'})==6
labels={'s1':{'p'},'s2':{'p'},'t':{'q'},'u':{'r'}}
edges={'s1':['t'],'s2':['u'],'t':['t'],'u':['u']}
ex_q=lambda s:any('q'in labels[x] for x in edges[s])
assert labels['s1']==labels['s2'] and ex_q('s1') and not ex_q('s2')
# 1/11 > (5*sqrt(5)-11)/2 iff 123/11 > 5*sqrt(5).
# Both sides are positive, so compare squares exactly.
square_gap=Fraction(123,11)**2-Fraction(125)
assert square_gap==Fraction(4,121)>0
a.write('_probe13.json',{'runtime':sys.version,'sources':[{'path':b+name,'sha256':a.row(b+name)['sha256']} for name in ['test_tranche23_flow_control_and_horizon_emission.py','test_tranche24_fsp_boundary_and_state_nfs.py','test_tranche25_acyclic_cohomology_and_bell_contextuality.py']],'leaky_bucket':{'capacity':10,'negative100_accepted':negative,'water_after_negative':str(after_negative),'positive100_same_time_accepted':oversize,'water_final':str(bucket.water)},'diamond_cuts':{'source_side_s_a':cut({'s','a'}),'source_side_s_b':cut({'s','b'})},'bisimulation':{'initial_labels_equal':True,'EX_q_at_s1':True,'EX_q_at_s2':False,'total_transition_graph':edges,'labels':{k:sorted(v) for k,v in labels.items()}},'hardy':{'candidate':'1/11','source_stated_maximum':'(5*sqrt(5)-11)/2','positive_square_comparison_gap':str(square_gap),'candidate_exceeds_stated_maximum':True},'limits':['Fixed small AST bucket and independent exact finite arithmetic only.','Hardy comparison uses the expression already stated in the reviewed source, not a newly assumed physical theorem.','No production imports, native code or external/private materials.']})
print('negative bucket, cut, bisimulation and Hardy-bound controls confirmed')
