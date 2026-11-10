"""Persist four fully read Majorana entry/finite-algebra owners and exact controls."""
import hashlib
import itertools
import json
from pathlib import Path
import runpy

H = Path(__file__).resolve().parent
P = 'additional_rust_quantum_probability_remaining'
np = H / (P + '_notes.json')
n = json.loads(np.read_text())
n['32'] = {'assessment': 'Full 269-line crate root read. Modules/reexports 29-98 expose the diagnostic family; authority/physical disclaimers 1-17 and 100-107 explicitly separate schedule labels from physical modes and authority. Gf2Weight 108-136 admits only 0/1 bytes, checked-adds a u64 Hamming weight, and independently compares XOR parity with weight modulo two. Tests 229-242 cover one word and an invalid bit. Remaining BoundaryRecord scaffolding checks a declared positive count and capacity only.',
           'limitations': ['No physical Majorana, hardware, topological protection, or authority theorem follows from exports or string constants.', 'The count scaffold is not wired into exported computations or memory/bit budgets.', 'Test source read only; no native execution or independent mutation replay.']}
n['38'] = {'assessment': 'Full 224-line repair-capacity helper read. A positive u32 declared distance yields floor((d-1)/2), with d=0 refused (15-26). The invariant gate independently recomputes this value and checks 2t<d (28-46); because t<=2147483647, 2*t is representable in u32. min_weight_nontrivial (48-56) returns the minimum nonzero mod-two Hamming weight among supplied vectors, without checking shared dimension, closedness, quotient nontriviality or completeness. Tests 149-197 include hand values, u32::MAX, d=0 and mod-two vector cases; count-scaffold tests do not establish a code-distance theorem.',
           'limitations': ['Declared distance is a premise, not measured/verified by the radius arithmetic.', 'The sampled minimum is an upper bound on the true minimum when supplied vectors are a genuine nonempty subset of eligible residuals; the docstring calls it a proxy for a lower bound in the wrong direction (RQPR-F008).', 'No native tests or physical threshold experiment executed.']}
n['31'] = {'assessment': 'Full 267-line LGGR owner read. apply_d1 (31-49) computes the parity syndrome after checking omega length; detect_lggr (51-66) delegates the chain condition and image/kernel classification, then combines d1 omega=0 with ClosedResidual. This correctly distinguishes exact closed schedules from nonexact closed schedules on a well-formed admitted complex. Tests 168-239 cover a torus residual, exact and open cases, short vectors and nonzero d1*d0. The witness is a public, mutable diagnostic record, not an input-bound unforgeable certificate.',
           'limitations': ['The local detector is d1; its blindness to nonzero cohomology is relative to that declared map, not an unconditional epistemic or physical result.', 'Public GF2Matrix representation can bypass shape/binary invariants, so the length-only apply_d1 gate can panic on inconsistent data (RQPR-F009).', 'No fresh Rust replay; count-boundary scaffold does not bound matrix operations.']}
n['27'] = {'assessment': 'Full 511-line GF2 classifier and cyclotomic owner read in two complete chunks. from_data normalizes entries modulo two and pads ragged rows (72-93). On well-formed binary matrices, matmul, RREF, boundary validation, augmented-rank image membership, and n-rank(d1)-rank(d0) implement exact finite cochain classification (95-249). The emitted status is Exact, ClosedResidual or OpenObstruction, with an explicit None authority effect. Cyclotomic16Element is the integer-coefficient quotient by zeta^8+1 with checked i64 multiply/add/subtract (253-303), not a field division or braid verifier. Tests 400-483 cover triangle classifications, ragged constructor padding, zeta^8=-1, order 16, and overflow refusal.',
           'limitations': ['GF2Matrix and receipt fields are public and deserializable; neither shape nor binary entries are re-admitted by the classifier. Raw data can change rank/status or panic (RQPR-F009).', 'A receipt has no source-input digest or witness replay method; its status is evidence of this call only when the actual inputs/execution are independently retained.', 'The opening text at line26 still says exact cyclotomic field arithmetic, while the implemented operation and corrected documentation describe an integer ring with partial bounded arithmetic.', 'Intermediate i64 overflow is refused; this bounded representation is not arbitrary-precision closure of the cyclotomic ring.', 'No native execution, braid proof or physical Majorana evidence is supplied by this file.']}
np.write_text(json.dumps(n, indent=2) + '\n')
runpy.run_path(str(H / (P + '_checkpoint.py')))
rp = H / (P + '.json')
r = json.loads(rp.read_text())
scope = json.loads((H / (P + '_scope.json')).read_text())['files']
def ev(index, a, b):
    f = scope[index]
    return {'path': f['path'], 'sha256': f['sha256'], 'lines': [a, b]}
claim = {'id': 'RQPR-C012',
         'claim': 'On admitted finite binary chain complexes, rank and augmented-rank computations distinguish image(d0), kernel(d1) outside that image, and nonclosed cochains. The LGGR wrapper explicitly compares the local syndrome detector with this global quotient obstruction. Positive-distance repair-radius arithmetic is valid conditional arithmetic, not validation of the distance premise.',
         'evidence': [ev(27, 95, 249), ev(31, 31, 66), ev(38, 15, 46), ev(32, 108, 136)],
         'dependencies': ['Rectangular binary matrices with d1*d0=0', 'Matched finite carrier dimensions', 'For repair-radius interpretation, a genuine code or quotient distance bound supplied externally'],
         'limitations': ['Exact does not imply physical authority; receipt fields remain freely constructible.', 'Shape/binary admission can be bypassed through the public matrix representation.', 'A list of selected nontrivial cycles does not establish a lower distance bound.', 'No native or experimental replay.']}
r['claims'] = [c for c in r['claims'] if c['id'] != claim['id']] + [claim]
findings = [
    {'id': 'RQPR-F008', 'severity': 'medium', 'title': 'Selected residual minima have the wrong stated distance-bound direction',
     'finding': 'min_weight_nontrivial describes its selected-list minimum as a proxy for a distance lower bound. Even when every supplied vector really is closed and nontrivial, minimizing over a subset yields an upper bound on the full minimum. For d0=0,d1=0 on F2^3, true nontrivial quotient distance is 1; supplying only [1,1,1] returns 3, whose inferred radius would be 1 instead of the true guaranteed radius 0. The helper also does not itself check closedness or quotient nontriviality.',
     'evidence': [ev(38, 48, 56), ev(38, 183, 195)],
     'recommended_action': 'Describe the returned quantity as a selected-candidate minimum; only use it as a distance lower bound after a separate exhaustive or proved exclusion of all smaller nontrivial classes. Keep the supplied distance premise explicit.',
     'validation': 'Independent exhaustive enumeration of the seven nonzero binary words of length three; no original Rust execution.'},
    {'id': 'RQPR-F009', 'severity': 'medium', 'title': 'Public GF2 matrix data bypasses classifier admission',
     'finding': 'GF2Matrix has public rows/cols/data and derives Deserialize. from_data normalizes entries, but raw construction/deserialization bypasses it. RREF pivots only on literal 1 while other paths use parity. With raw d0=[[3]], shape1x1, d1=zeros(0,1), omega=[1], the classifier computes rank(d0)=0, normalized augmented rank=1 and emits ClosedResidual with q1_dimension=1. Modulo-two semantics give d0=[[1]], so omega is Exact and quotient dimension0. Raw inconsistent row lengths additionally reach unchecked indexing in matmul/rref/apply_d1 rather than a typed refusal.',
     'evidence': [ev(27, 54, 93), ev(27, 95, 151), ev(27, 188, 249), ev(31, 31, 48)],
     'recommended_action': 'Make representation private with validated deserialization, or validate/normalize dimensions and binary entries at every public computation boundary. Add malformed-deserialization and nonbinary-raw regression cases.',
     'validation': 'Exact independent reconstruction of the one-column pivot/augmentation counterexample; native panic paths are source-derived, not executed.'}
]
ids = {f['id'] for f in findings}
r['findings'] = [f for f in r['findings'] if f['id'] not in ids] + findings

words = [w for w in itertools.product([0, 1], repeat=3) if any(w)]
true_distance = min(map(sum, words))
selected_minimum = sum([1, 1, 1])
assert true_distance == 1 and selected_minimum == 3
raw_rank = int(3 == 1)
normalized_rank = int((3 % 2) == 1)
augmented_rank = 1  # [3,1] -> from_data -> [1,1].
assert (raw_rank, normalized_rank, augmented_rank) == (0, 1, 1)
control = {'method': 'Independent exact small integer enumeration/reconstruction; not Rust execution',
           'controls': [
               {'id': 'RQPR-MAJ-01', 'passed': True, 'admitted_complex': 'd0=0,d1=0 on C1=F2^3', 'nonzero_words_enumerated': 7, 'true_distance': true_distance, 'selected_minimum': selected_minimum, 'true_radius': (true_distance - 1)//2, 'unsupported_selected_radius': (selected_minimum - 1)//2},
               {'id': 'RQPR-MAJ-02', 'passed': True, 'raw_d0': [[3]], 'd1_shape': [0, 1], 'omega': [1], 'source_raw_rank': raw_rank, 'normalized_rank': normalized_rank, 'augmented_rank': augmented_rank, 'raw_status': 'ClosedResidual', 'mod_two_status': 'Exact'}]}
cp = H / (P + '_majorana_controls.json')
cp.write_text(json.dumps(control, indent=2) + '\n')
r['validation'] = [v for v in r['validation'] if v.get('id') != 'RQPR-MAJ-CONTROLS']
r['validation'].append({'id': 'RQPR-MAJ-CONTROLS', 'path': str(cp.relative_to(H.parents[1])).replace('\\', '/'), 'sha256': hashlib.sha256(cp.read_bytes()).hexdigest(), 'controls': 2, 'passed': True, 'native_execution': False})
rp.write_text(json.dumps(r, indent=2) + '\n')
with (H / (P + '.md')).open('a', encoding='utf-8') as f:
    f.write('\n\n## Four Majorana owners reviewed while awaiting the section control\n\n'
            'Coverage is now 31/51 complete bodies, with 20 pending. The GF(2) classifier, LGGR wrapper, crate root and repair-capacity helper were fully read. '
            'The conditional finite image/kernel classifier is substantive; physical and authority fences remain explicit. '
            'RQPR-F008 records the wrong distance-bound direction for a selected residual minimum. RQPR-F009 records that public/deserialized nonbinary matrices can produce a wrong class, and malformed shapes can reach unchecked indexing. '
            'Two independent small integer controls pass; no Rust execution or source edits occurred.\n')
print(json.dumps({'full': r['full_source_read_count'], 'remaining': len(r['remaining_work']), 'claims': len(r['claims']), 'findings': len(r['findings']), 'report_sha256': hashlib.sha256(rp.read_bytes()).hexdigest()}))
