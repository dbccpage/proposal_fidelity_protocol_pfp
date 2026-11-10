"""Persist a source-derived counterexample, without executing original/native code."""
import json,hashlib
from pathlib import Path
root='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g12/original/lean4/Derivation/'
e=[]
for name,spans in [('StableContent.lean',[[61,78],[254,286],[496,506]]),('PrimitivePassage.lean',[[109,116],[599,676],[912,915]])]:
    p=root+name
    e.append({'path':p,'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest(),'lines':spans})
statement='The recorded openExactStabilityCharacterization is false on a live funded two-occurrence state: occ=[0,1], asserted=wit=prot=[(1,0)], obs=some[[0]], budget=1, licensed=true, refusals=[], halted=false, queried at(0,1). protSep(s,1,0)=true, so protSep_trace_stable proves separation of(1,0) after every trace. sepCol and hence sepP are symmetric, so(0,1) is also trace-stable; protSep(s,0,1)=false because protection stores ordered pairs. All hypotheses of the displayed open proposition hold and its conclusion fails. This is a source-derived all-traces argument using the existing sufficiency theorem, not a bounded trace search or fresh Lean result. The state is also reachable by admitting0,1, asserting/retaining/protecting(1,0), declaring observation, setting budget2 and adding[0]. Replace the open converse with an appropriately unoriented or closure-aware characterization; preserve historical bytes.'
p=Path('dag/reviews/additional_paper_011_native_findings.json');d=json.loads(p.read_text(encoding='utf-8'))
row={'id':'P011-NATIVE-F016','title':'Reverse protected orientation refutes the live-funded stability converse','assessment':statement,'statement':statement,'source_evidence':e,'evidence':[x['path'] for x in e],'severity':'false_open_conjecture','validation_status':'source_derived_counterexample_using_existing_trace_sufficiency_no_Lean_execution'}
d=[x for x in d if x['id']!=row['id']]+[row]
p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
print(row['id'])
