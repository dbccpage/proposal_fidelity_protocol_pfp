"""Persist three fully reviewed exact-field bodies and their bounded controls."""
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
P = R / 'dag/reviews/additional_rust_linear_algebra_remaining'
path = Path(str(P) + '_notes.json')
notes = json.loads(path.read_bytes())
pins = {x['path']: x['sha256'] for x in json.loads(Path(str(P) + '_scope.json').read_bytes())['files']}
assessments = {
    'src/exact_field/mod.rs': 'Read all399 lines. Generic exact-field facade and private rectangular Grid implement typed errors, checked shape arithmetic, fallible allocation, scalar-operation charging and inverse refusal. Unlike the separate sealed CheckedExactField interface, Field plus ExactRing leaves algebraic laws and scalar panic/Clone/Drop behavior as stated premises. Per-matrix allocation and arithmetic-call bounds are explicitly not bit-length, heap or elapsed-time guarantees. Inverse presence does not itself establish inverse laws. Broad prose about nonlinear with_limits availability exceeds some helper interfaces. Substantive shared utilities, not a mathematical proof or native validation; no original execution.',
    'src/exact_field/elimination.rs': 'Read all1598 lines in four complete ranges. Leftmost-pivot Gauss-Jordan reduction gives canonical reduced rows, free-coordinate kernel vectors and original pivot-column image generators. Solve preflights both success and refusal paths, replays Ax=b, and constructs a dual witness by solving [A^T;b^T]y=e with full replay of y^T A=0 and y^T b!=0. Inverse and determinant use standard exact elimination under lawful field operations; the private inconsistency witness has substantive public verification. The operation estimate is conservative, not a scalar bit-complexity guarantee. Principal-minor enumeration is explicitly capped at n<=12. Extensive embedded tests cover empty shapes, several finite fields, singularity, tampering and budgets, but were not run. Independent exhaustive F2/F3 model checks793 systems,572 solution families and221 dual refusals; no original execution.',
    'src/exact_field/matrix.rs': 'Read all1697 lines in five complete ranges. Shape-checked constructors, products, tensor products, stacks, powers and finite predicates are substantive operations with private BasicMatrix storage; multiplication counts both mul and add, and whole-power preflight is conservative. Generic scalar laws and scalar resource behavior remain external premises. Row and column extraction validate indices only inside the opposite-axis loop, accepting an out-of-range index for zero-width or zero-height matrices. Row-list conversion also loses the column dimension of0xn matrices despite inverse wording. Rational conversion assumes canonical nonzero-denominator inputs but public raw ratio constructors can violate that premise: narrowing checks the unreduced pair and can refuse a representable value; raw zero denominators are not admitted explicitly. Dependency constructor/reduction excerpts were read separately, not credited as whole files. Substantive tests cover ordinary field operations and budgets but miss these edge cases. No original execution.'
}
for name, assessment in assessments.items():
    notes['files'][name] = {'full_source_read': True, 'assessment': assessment}
notes['files']['src/row_constraint_implication.rs']['assessment'] = notes['files']['src/row_constraint_implication.rs']['assessment'].replace('owner still pending', 'owner now fully read and separately assessed')
for item in notes['claims']:
    if item['id'] == 'RLA-C10':
        item['limits'] = 'Well-formed exact rationals and available resources are premises; the implication solver body is now fully read with separate finite controls. No memory, policy, physical or general answer-correctness interpretation is derived; no native execution.'

def ev(name, lo, hi):
    p = 'code/rust/core_linear_algebra/' + name
    return {'path': p, 'sha256': pins[p], 'lines': [lo, hi]}

claims = [{
    'id': 'RLA-C12',
    'statement': 'The generic exact-field solver constructs either an affine solution family or a dual inconsistency witness, and separately replays its answer against the supplied matrix and right-hand side. Under lawful field operations these are concrete finite linear-algebra certificates, with explicit preflight limits for both branches.',
    'evidence': [ev('src/exact_field/mod.rs', 32, 54), ev('src/exact_field/elimination.rs', 237, 282), ev('src/exact_field/elimination.rs', 316, 476)],
    'controls': ['RLA-P13'],
    'limits': 'The independent exhaustive control covers2x2 systems over F2/F3, not native execution or arbitrary-field validation. Algebraic laws, well-formed scalar values and scalar resource behavior remain premises.'
}]
findings = [{
    'id': 'RLA-F04',
    'statement': 'Empty-axis matrix helpers weaken their stated shape/index contract: row(2x0,99) and column(0x2,99) return an empty vector because no indexed element is visited; to_rows followed by from_rows turns0x3 into0x0 despite inverse wording.',
    'evidence': [ev('src/exact_field/matrix.rs', 85, 112), ev('src/exact_field/matrix.rs', 144, 163)],
    'controls': ['RLA-P14'],
    'limits': 'Independent tiny control-flow and shape model; no native memory safety failure is asserted. Ordinary nonempty-axis accesses are checked.',
    'recommended_action': 'Validate the requested row/column before iteration and either carry shape metadata in row-list conversion or document its loss for zero-row matrices.'
}, {
    'id': 'RLA-F05',
    'statement': 'Exact rational conversion relies on an unstated canonical-value admission at its boundary. Narrowing checks raw numerator and denominator before normalization, so raw2^63/2 is refused although its reduced value2^62 fits Rational64; raw zero denominators also reach constructors without a local validity gate.',
    'evidence': [ev('src/exact_field/matrix.rs', 165, 199)],
    'controls': ['RLA-P15'],
    'limits': 'Dependency num-rational0.4.2 raw/normal constructor and reduction excerpts are pinned in the control receipt. Canonical valid ratios avoid the mismatch; no native conversion or panic was executed. Generic field law premises do not by themselves validate raw values at this public conversion boundary.',
    'recommended_action': 'Explicitly reject zero denominators and normalize before representability checks, or make the valid canonical input precondition explicit and enforce it at ingress.'
}]
for group, items in [('claims', claims), ('findings', findings)]:
    ids = {x['id'] for x in items}
    notes[group] = [x for x in notes[group] if x['id'] not in ids] + items
receipt = Path(str(P) + '_controls04.json')
result = json.loads(receipt.read_bytes())
assert result['status'] == 'finite_controls_pass'
assert hashlib.sha256(receipt.with_suffix('.py').read_bytes()).hexdigest() == result['helper_sha256']
ids = {x['id'] for x in result['controls']}
notes['controls'] = [x for x in notes['controls'] if x['id'] not in ids]
for item in result['controls']:
    notes['controls'].append({**item, 'receipt': {'path': receipt.relative_to(R).as_posix(), 'sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}})
path.write_text(json.dumps(notes, indent=2, ensure_ascii=False) + '\n', encoding='utf8')
print('Persisted three full bodies, one claim, two qualified findings and three controls.')
