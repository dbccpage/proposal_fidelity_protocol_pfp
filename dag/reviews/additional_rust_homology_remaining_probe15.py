import sys, json, math
sys.dont_write_bytecode=True
from pathlib import Path
from fractions import Fraction

# Independent, bounded arithmetic controls. No source imports or Rust execution.
empty_tree={'vertices':2,'edges':1,'tree_edges':0,'tree_components':2,'reported_b1':1+2-2,'chords':1,'actual_graph_b1':1-2+1}
assert empty_tree['reported_b1']==empty_tree['chords']==1 and empty_tree['actual_graph_b1']==0
edge={'source':'v','target':'v'}
row=[0];row[0]=-1;row[0]=1
assert row==[1]
diagnostic={'harmonic_projection':[0.,0.], 'xi':.5, 'distortions':[], 'worst_edges':[]}
accepted=len(diagnostic['harmonic_projection'])==2 and all(math.isfinite(x) and x>=0 for x in diagnostic['distortions']) and all(i<len(diagnostic['distortions']) for i in diagnostic['worst_edges'])
assert accepted
bad_ranking={'distortions':[0.,100.],'worst_edges':[0,0]}
assert all(i<len(bad_ranking['distortions']) for i in bad_ranking['worst_edges'])
overflow=2**63-1+1
assert overflow>2**63-1
# Any incidence SVD of K5 has at most 5 listed singular values, while its cycle
# dimension is 10-5+1=6. Omitting missing values cannot return a full cycle basis.
assert 10-5+1>min(5,10)
gradient=1e308+.5*(-1e308-1e308)
assert not math.isfinite(gradient)
receipt={'rule':'cycle_admission_binding_and_completeness','status':'bounded_countermodels_confirmed','runtime':sys.version,'empty_designated_tree':empty_tree,'public_cell_loop_incidence':row,'edge_count_diagnostic_accepts_empty_distortions':accepted,'rank_indices_valid_but_not_worst':bad_ranking,'i64_tree_path_sum':overflow,'k5_cycle_dimension':6,'k5_max_singular_value_list_length':5,'gradient_finite_inputs_nonfinite_intermediate':str(gradient),'limits':['Independent Python integer/float and combinatorial controls, not Rust, nalgebra or external norm execution.','K5 dimension bound establishes structural omission independent of actual SVD rounding; no claimed observed Rust output.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps(receipt))
