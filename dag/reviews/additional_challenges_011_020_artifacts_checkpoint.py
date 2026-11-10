"""Record ten complete case readings and independent finite arithmetic controls."""
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'
scope = json.loads((REV/'additional_challenges_011_020_artifacts_scope.json').read_text())
frozen = {r['path']:r for r in scope['files']}
notes = {
 'C011': 'Full three-cycle gauge-labelled control read. Claims7,-1,2 and weights2,1,3 give optimal weighted L1 residual8: potential(p,q,r)=(0,7,-2) leaves only the weight-one qr residual8, while unit circulation is dual feasible with objective8. This verifies this encoded instance; no comparison with an unseen source gauge fixture or universal parser soundness is inferred.',
 'C012': 'Full two-vertex/one-edge sheaf case read. One vertex stalk is zero-dimensional, the other and edge stalk are one-dimensional. The nonzero1x1 restriction gives rank1, hence H0=H1=0 and both listed targets lie in the coboundary image. The filename isolated does not make the listed vertex graph-isolated. No authentication or general completeness claim follows.',
 'C013': 'Full one-point simplicial complex read. The single vertex42 has unreduced H0=Z and no higher homology or torsion. It is a small identity/control case, not an independent torsion or large-matrix stress test.',
 'C014': 'Full three-vertex weighted tree case read. Positive rational weights1/2,1/3 and flow(1,2) admit potential(0,1,3), so the flow is exact, with zero harmonic and coexact components. This is a useful simple reconstruction control; it does not exercise a nonzero cycle/curl or singular normal equations.',
 'C015': 'Complete poisoned one-vertex filtration read. The literal not_a_fraction fails the declared rational filtration grammar; useful input/refusal regression only. Its invalidity is not a persistence-barcode result, and retained checker refusal handling has separately documented gaps.',
 'C016': 'Complete poisoned cup-product case read. It supplies the boundary tetrahedron as Y and degrees1,1 but omits X; no complete declared product-map problem is present. Useful missing-input control, not evidence for a computed cohomology ring.',
 'C017': 'Complete poisoned lattice case read. It declares a trivial group identity/element list but no multiplication table, and no lattice edge assignments. It is incomplete under the declared carrier contract; no valid nonabelian-holonomy calculation is supported.',
 'C018': 'Complete two-vertex poisoned signed-graph case read. The only edge sign is3, outside the declared signs+1/-1. This tests domain refusal rather than a frustration-index theorem.',
 'C019': 'Full tetrahedral rational extension case read. Explicit oriented incidence and face-edge maps compose to zero, B is zero and all face weights are1. Zero potential is a valid exact extension. This positive case does not test the separate nonzero primal-dual optimum gap found in29 stored owner-PASS records.',
 'C020': 'Complete poisoned three-cell row-filtered diagram read. The two consecutive vertical1x1 maps are identities overF2, so their composite is1 rather than0. This is not a double complex; a refusal control cannot be promoted to a spectral-page certificate.'
}
rows = []
selected = {}
for number in range(11,21):
    family = f'C{number:03}'
    cases = [r for r in scope['files'] if f'/c{number:03}_' in r['path'] and '/judge_packet/cases/' in r['path']]
    item = min(cases,key=lambda r:r['bytes'])
    raw = (ROOT/item['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    selected[family] = json.loads(raw)
    rows.append({'path':item['path'],'sha256':item['sha256'],'full_source_read':True,
                 'reviewed_lines':[[1,len(raw.decode('utf-8').splitlines())]],'assessment':notes[family]})

case = selected['C011']; potential={'p':Q(0),'q':Q(7),'r':Q(-2)}
residual=[Q(e['claim'])-(potential[e['v']]-potential[e['u']]) for e in case['edges']]
objective=sum(Q(e['weight'])*abs(v) for e,v in zip(case['edges'],residual))
assert residual==[0,8,0] and objective==sum(Q(e['claim']) for e in case['edges'])==8
assert all(Q(e['weight'])>=1 for e in case['edges'])
assert all(sum((1 if e['v']==v else 0)-(1 if e['u']==v else 0) for e in case['edges'])==0 for v in case['vertices'])
case=selected['C014'];potential={'v0':Q(0),'v1':Q(1),'v2':Q(3)}
assert all(Q(case['flow'][e])==potential[case['edge_endpoints'][e][1]]-potential[case['edge_endpoints'][e][0]] for e in case['edges'])
case=selected['C019']
nilpotence=[[sum(Q(case['d2'][face].get(edge,0))*Q(case['d1'][edge].get(vertex,0)) for edge in case['edges']) for vertex in case['vertices']] for face in case['faces']]
assert all(x==0 for row in nilpotence for x in row) and all(Q(x)==0 for x in case['B'].values())
case=selected['C020']
assert case['d_v']['1,1'][0][0]*case['d_v']['1,2'][0][0]%2==1
controls={'status':'four_independent_small_case_arithmetic_controls',
 'weighted_cycle_optimum':str(objective),'tree_exact_reconstruction':True,
 'tetrahedron_nilpotence_and_zero_extension':True,'vertical_square_nonzero_over_f2':True,
 'limits':'Four source-bound finite arithmetic checks only; prior1076-file owner replays were not repeated.'}
(REV/'additional_challenges_011_020_artifacts_controls.json').write_text(json.dumps(controls,indent=2)+'\n')
prior=REV/'additional_challenges_011_020.json'
report={'status':'in_progress_prior_replay_reconciliation','source_commit':scope['source_commit'],
 'scope_manifest':'dag/reviews/additional_challenges_011_020_artifacts_scope.json',
 'file_reviews':rows,'pending_paths':sorted(set(frozen)-{r['path'] for r in rows}),
 'claims':[],'findings':[],
 'prior_review':{'path':prior.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),
                 'scope':'208 source bodies and1076 artifact replay entries already recorded. Their outcomes and known checker defects require contextual reconciliation; no new replay credit.'},
 'validation':'dag/reviews/additional_challenges_011_020_artifacts_controls.json',
 'limits':['Only these ten original case bodies have fresh full-source reading credit. Remaining1066 paths are pending this contextual artifact disposition.',
           'Prior PASS is an owner verdict, not a general mathematical soundness or model-efficacy result.',
           'No original change, native/provider execution or private benchmark access.']}
(REV/'additional_challenges_011_020_artifacts.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'fresh_full_cases':len(rows),'pending':len(report['pending_paths']),'independent_small_checks':4}))
