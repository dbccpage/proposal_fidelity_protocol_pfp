"""Persist seventeen complete fixture readings and bounded independent controls."""
from fractions import Fraction as Q
from itertools import product
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
PREFIX='additional_challenges_021_030_artifacts'
scope=json.loads((REV/(PREFIX+'_scope.json')).read_text())
report=json.loads((REV/(PREFIX+'.json')).read_text())
frozen={r['path']:r for r in scope['files']}
rows={r['path']:r for r in report['file_reviews']}
notes={
21:'Full one-qubit positive case read: H=(I-Z)/2 has diagonal(0,1), exact minimum0 and degeneracy1. This checks a simple normalization/target convention, not general commuting Pauli certificates or physics.',
22:'Full six-qubit poison read. The only generator is negative identity, whose positive-one eigenspace is zero; it is excluded from a consistent stabilizer code. Useful typed-refusal control rather than a distance example.',
23:'Full two-qubit signed tableau read. Its four image words preserve the X0/X1/Z0/Z1 binary symplectic pairing, independently checked; this establishes a valid generator commutation pattern, not a particular synthesized circuit within16 gates or its minimality.',
24:'Full graph poison read. For num_vertices4 the named vertex4 is outside the carrier0..3. A refusal is warranted, but its witness must identify this actual defect rather than an invented edge.',
25:'Full request for five bases in dimension4 read. It contains no supplied bases or certificate. A meaningful finite MUB construction target, not stored verification of their mutual inner products; prior owner replay remains conditional on its documented gaps.',
26:'Full two-site projector case read. The site1 matrix is outer((1,-7),(1,-7))/50: exact symmetric idempotent of rank1 with kernel(7,1). Weight1 is positive; tensoring with the unacted two-dimensional site gives a two-dimensional zero-energy kernel. This small valid control does not validate misleading model labels in other fixtures.',
27:'Full dimension5 poison read. Its coordinate vector is nonzero but the dimension violates the declared3/4 carrier. No contextuality conclusion follows from this malformed input.',
28:'Full three-mode identity-encoding anti-normal-order control read. The supplied operator I-a0*a0_dagger equals a0_dagger*a0 by the CAR. On occupation-bit basis its diagonal is bit0, independently checked on all8states. No general Hamiltonian encoding or characteristic-polynomial verification follows.',
29:'Full nine-bit weighted syndrome case read. Exhausting all512 binary corrections against the exact supplied4x9 Hz finds weight3 attained by the singleton columns0 and3. This certifies this matrix problem without assuming the rotated-distance3 label establishes a lattice or trusting the defective advertised matching dual.',
30:'Full contraction poison read. TensorA repeats indexi, outside the declared no-repeated-index-per-tensor rule. This is a malformed-input regression, not an instance of the ordinary symmetric-difference contraction model or evidence for handling trace contractions.'
}
selected={}
for n in range(21,31):
    cases=[r for r in scope['files'] if f'/c{n:03}_' in r['path'] and '/judge_packet/cases/' in r['path']]
    item=min(cases,key=lambda r:r['bytes']);path=item['path'];raw=(ROOT/path).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    selected[n]=json.loads(raw)
    rows[path]={'path':path,'sha256':item['sha256'],'full_source_read':True,
               'reviewed_lines':[[1,len(raw.decode('utf-8').splitlines())]],'assessment':notes[n]}

images=selected[23]['images'];order=['X0','X1','Z0','Z1']
def symplectic(a,b):return sum(x!='I' and y!='I' and x!=y for x,y in zip(a[1:],b[1:]))%2
for i,a in enumerate(order):
    for j,b in enumerate(order):assert symplectic(images[a],images[b])==int(abs(i-j)==2)
matrix=[[Q(x[0]) for x in row] for row in selected[26]['terms'][0]['matrix']]
assert all(x[1]=='0' for row in selected[26]['terms'][0]['matrix'] for x in row)
assert all(sum(matrix[i][k]*matrix[k][j] for k in range(2))==matrix[i][j] for i,j in product(range(2),repeat=2))
assert all(sum(matrix[i][j]*[7,1][j] for j in range(2))==0 for i in range(2))
assert matrix[0][0]+matrix[1][1]==1
case=selected[29];valid=[]
for bits in product((0,1),repeat=9):
    if [sum(a*b for a,b in zip(row,bits))%2 for row in case['hz']]==case['syndrome']:
        valid.append((sum(w*b for w,b in zip(case['weights'],bits)),bits))
optimum=min(cost for cost,bits in valid);best=[list(bits) for cost,bits in valid if cost==optimum]
assert optimum==3 and best==[[0,0,0,1,0,0,0,0,0],[1,0,0,0,0,0,0,0,0]]
# Explicit occupation-basis creation/annihilation on mode0 (no earlier-mode signs).
def ann(state):return state^1 if state&1 else None
def create(state):return None if state&1 else state^1
for state in range(8):
    left=create(state);aa_dagger=0 if left is None else int(ann(left)==state)
    right=ann(state);a_dagger_a=0 if right is None else int(create(right)==state)
    assert 1-aa_dagger==a_dagger_a==(state&1)
ledger_path=REV/'additional_challenges_021_030_automated.jsonl'
assert hashlib.sha256(ledger_path.read_bytes()).hexdigest()=='34ee5779b8282a3aa77a50213df0286fface84244681a3d2f37ed738866fd066'
ledger=[json.loads(line) for line in ledger_path.read_text().splitlines()]
mutant=next(r for r in ledger if r['status']=='checker_exception_caught')
path=mutant['path'];raw=(ROOT/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==frozen[path]['sha256']
data=json.loads(raw);n=data['case']['num_modes'];answer=data['mutated_answer']
assert n==9 and len(answer['majoranas'])==12 and {len(w)-1 for w in answer['majoranas']}=={6}
assert {len(w) for w,value in answer['hamiltonian']}=={6}
rows[path]={'path':path,'sha256':frozen[path]['sha256'],'full_source_read':True,
 'reviewed_lines':[[1,len(raw.decode('utf-8').splitlines())]],
 'assessment':'Complete mutant body read. The case is nine modes but the copied answer supplies12 Majoranas on6qubits and6-character Hamiltonian words; a nine-mode encoding needs18 Majoranas on9qubits. This directly establishes a shape/domain-invalid answer without invoking the owner that previously threw IndexError. kill_verified=true and the empty rejection_message are producer metadata, not that missing verifier result. Preserve this as a negative regression and keep the original caught-exception status separate.'}
out={'status':'bounded_finite_controls_pass','tableau_symplectic_pair_checks':16,'projector_idempotence_and_kernel':True,
 'number_operator_basis_states':8,'syndrome_corrections_enumerated':512,'minimum_weight':3,'minimizers':best,
 'copied_answer_shape':{'declared_modes':9,'required_majoranas':18,'observed_majoranas':12,'observed_word_qubits':6},
 'limits':'Fresh standalone arithmetic/schema checks only; no original checker, model, provider, native library or private benchmark was executed.'}
(REV/(PREFIX+'_controls.json')).write_text(json.dumps(out,indent=2)+'\n')
report['file_reviews']=list(rows.values());report['pending_paths']=sorted(set(frozen)-set(rows))
report['counts']={'scope':1032,'full_body_readings':len(rows),'pending_dispositions':len(report['pending_paths'])}
report['independent_verification_followups']={
 'six_C027_cases':'New exact finite CNF refutations retained separately; old independent checker remains unavailable beyond20rays.',
 'one_C028_mutant':'New independent shape-invalidity check; old caught exception is not rewritten as a successful historical rejection.',
 'no_repository_source_repair':True}
report['claims'][0]['dependencies']=['Exact Q(sqrt2) ray normalization and orthogonality encoding; binary colouring with pair at-most-one and full-context exactly-one constraints.']
report['claims'][0]['source_evidence'].append({'path':'workflows/tasks/certified_challenges/c027_kochen_specker_contextuality/participant_packet/TASK.md',
 'sha256':hashlib.sha256((ROOT/'workflows/tasks/certified_challenges/c027_kochen_specker_contextuality/participant_packet/TASK.md').read_bytes()).hexdigest(),'lines':[[15,37]]})
report['findings']=[{'id':'CAQ-F028-01','severity':'medium','statement':'The retained copied C028 answer is structurally invalid for its nine-mode case: it contains only12 Majoranas of six-qubit width and six-qubit Hamiltonian words. The historical dual checker caught an IndexError instead of producing a typed rejection; the new independent shape check establishes invalidity while leaving that totality defect open.',
 'evidence':[{'path':path,'sha256':frozen[path]['sha256']}],'validation':'dag/reviews/'+PREFIX+'_controls.json',
 'recommended_action':'Validate2N signed Majorana words and N-character operator width before index access; keep exception outcomes distinct from successful mathematical rejection.'}]
report['limits']=[s for s in report['limits'] if not s.startswith('Only six')]+['Only17 complete frozen bodies reviewed at this checkpoint;1015 artifact dispositions remain pending.']
assert len(rows)==17
(REV/(PREFIX+'.json')).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['counts']));print(json.dumps(out))
