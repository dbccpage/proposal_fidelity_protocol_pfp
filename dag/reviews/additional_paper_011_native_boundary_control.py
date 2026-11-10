"""Independent bounded reconstruction of the legacy boundary spot-check dimensions."""
import hashlib,json
from pathlib import Path
from collections import Counter
H=Path(__file__).resolve().parent; R=H.parents[1]; P='additional_paper_011_native'
def bd(s,signed):
    return [(((-1)**i if signed else 1),s[:i]+s[i+1:]) for i in range(len(s))]
def twice(s,signed):
    c=Counter()
    for a,t in bd(s,signed):
        for b,u in bd(t,signed):c[u]+=a*b
    return c
rows=[]
for s in [(0,1,2),(0,1,2,3)]:
    unsigned=twice(s,False); signed=twice(s,True)
    queried=[t for _,t in bd(s,False)]
    assert all(unsigned[t]==signed[t]==0 for t in queried)
    assert any(v==2 for v in unsigned.values())
    assert all(v==0 for v in signed.values())
    rows.append({'cell':s,'legacy_query_faces':queried,'signless_legacy_queries':[unsigned[t] for t in queried],
      'correct_codimension_two_faces':[{'face':t,'signless_coefficient':v,'signed_coefficient':signed[t]} for t,v in unsigned.items() if len(t)==len(s)-2]})
control={'id':'g12_legacy_boundary_wrong_dimension','status':'pass','method':'fresh independent stdlib arithmetic reconstruction; no Lean/native execution','cases':rows,
 'limit':'Two minimal cases expose signless false confidence in the first two legacy conjuncts; not a fresh kernel check or exhaustive audit of all cells.'}
p=H/(P+'_controls.json');cs=json.loads(p.read_text(encoding='utf-8'));cs['checks']=[c for c in cs['checks'] if c['id']!=control['id']]+[control];p.write_text(json.dumps(cs,indent=2)+'\n',encoding='utf-8')
e=[]
for name,lines in [('LadderGeneral.lean',[[295,327]]),('BoundaryCancellation.lean',[[371,398],[589,626]])]:
    path='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g12/original/lean4/Derivation/'+name
    e.append({'path':path,'sha256':hashlib.sha256((R/path).read_bytes()).hexdigest(),'lines':lines})
a='The first two conjuncts of d2_zero_dims_2_3_4 query facets of a cell after two boundary operations. Their target lengths are n-1, while every resulting term has length n-2, so these zeros are automatic and do not test cancellation. For triangle(0,1,2), even the signless double boundary passes all queried edge checks although each correct vertex coefficient is2; the tetrahedron case has the analogous triangle-versus-edge mismatch. The third dimension4 conjunct queries two successive facets correctly. BoundaryCancellation independently proves every target coefficient zero and supplies correct signless counterexamples, so the stronger signed theorem is not undermined. Retain historical bytes but do not count the first two conjuncts as substantive cancellation tests.'
f={'id':'P011-NATIVE-F015','title':'Two legacy double-boundary spot-checks query the wrong dimension','assessment':a,'statement':a,'source_evidence':e,'evidence':[x['path'] for x in e],'severity':'test_adequacy_gap','validation_status':'fresh_two_case_independent_arithmetic_reconstruction_no_Lean_execution'}
p=H/(P+'_findings.json');fs=json.loads(p.read_text(encoding='utf-8'));fs=[x for x in fs if x['id']!=f['id']]+[f];p.write_text(json.dumps(fs,indent=2)+'\n',encoding='utf-8')
print(json.dumps(control))
