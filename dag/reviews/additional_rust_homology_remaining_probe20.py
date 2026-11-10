import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
cases=[]
for matrix in [[[1,1],[1,1]],[[0,1],[-1,0]]]:
    det=matrix[0][0]*matrix[1][1]-matrix[0][1]*matrix[1][0]
    predicate=all(abs(matrix[i][i])>=1e-10 for i in range(2))
    assert predicate!=(det!=0)
    cases.append({'matrix':matrix,'diagonal_predicate':predicate,'determinant':det})
r={'rule':'inactive_lefschetz_nondegeneracy_scope','status':'exact_countermodels_confirmed_for_inactive_source','runtime':sys.version,'cases':cases,'limits':['Both lefschetz.rs and transition_scorer.rs have file-level cfg(any()) and are inactive.','Independent determinant arithmetic; no historical source or Rust execution, no current runtime failure inferred.']}
Path(__file__).with_suffix('.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8');print(json.dumps(r))
