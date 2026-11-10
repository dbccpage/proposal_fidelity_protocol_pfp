"""Persist ordered-field and congruence bodies, with exact finite replay control."""
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[2]
P = R / 'dag/reviews/additional_rust_linear_algebra_remaining'
path = Path(str(P) + '_notes.json')
notes = json.loads(path.read_bytes())
pins = {x['path']: x['sha256'] for x in json.loads(Path(str(P) + '_scope.json').read_bytes())['files']}
notes['files']['src/exact_field/ordered.rs'] = {'full_source_read': True, 'assessment': 'Read all1627 lines in four complete ranges. OrderedExactField and HermitianOrdered explicitly state universal sign/order/conjugation/positive-norm obligations; local guards only check sign range and zero consistency, not all those laws. BigRational sign uses its admitted reduced positive-denominator representation, so arbitrary raw ratios are outside that valid representation premise. Inertia delegates to congruence and counts signs; nonpivoting LDL constructs exact factors or a negative direction, lifting through the partial unit-lower factor. Zero-pivot/nonzero-Schur-column witness has value exactly-1, including the correctly conjugated Hermitian formula. Extensive tests compare minors, rank, congruence, realification and both witness branches; none were run. The paragraph398-405 incorrectly suggests a positive-definite matrix can require permutation to avoid a zero leading principal minor; the actual zero-column rule is complete for PSD under the stated laws, as later tests explicitly expect. Several smaller test comments overstate tolerance independence or misstate matrix size, without changing the asserted finite equations. Independent760 rational symmetric cases replay factors/witnesses and agree with every-principal-minor criterion. Capacity bookkeeping is separate from these mathematical facts.'}
notes['files']['src/exact_field/congruence.rs'] = {'full_source_read': True, 'assessment': 'Read all735 lines in two complete ranges. Square symmetric/Hermitian ingress is checked; characteristic2 is explicitly refused for nonempty inputs. Swaps, shears and elementary elimination track S with S* A S=diag(D); inverse off-diagonal shear also works for imaginary entries. Transform is a product of determinant+-1 operations. The private certificate exposes separate replay which checks shape, transform invertibility and every diagonal/off-diagonal product entry; construction itself does not automatically invoke replay. Calling the Hermitian replay method alone establishes its stated matrix equation, not an additional independent positivity or Hermiticity admission. Budgeted construction and unbudgeted verifier are distinct interfaces. Substantive source tests cover empty shapes, finite fields, nonunits, imaginary shear and several tamper classes; no Rust execution. Independent760 symmetric rational cases compare full elementary products and intact-input replay, determinant+-1 and PSD signs. No physical interpretation or proof about arbitrary scalar implementations follows.'}
notes['files']['src/exact_field/pseudoinverse.rs']['assessment'] = notes['files']['src/exact_field/pseudoinverse.rs']['assessment'].replace('the HermitianOrdered owner remains pending', 'the HermitianOrdered owner is now fully read and its universal laws remain implementor obligations')
for item in notes['claims']:
    if item['id'] == 'RLA-C15':
        item['limits'] = 'Independent1560 rational inputs and1560 tampered-output refusals; not native execution or validation of every HermitianOrdered implementation. Involution alone supplies a Hermitian form, not positivity; the ordered owner explicitly states the additional universal laws without universally checking them.'

def ev(name, lo, hi):
    p = 'code/rust/core_linear_algebra/' + name
    return {'path': p, 'sha256': pins[p], 'lines': [lo, hi]}

claims = [{
    'id': 'RLA-C16',
    'statement': 'Congruence diagonalization tracks invertible elementary basis changes and offers a separate verifier of S*AS=diag(D). Under the explicit ordered-field or positive Hermitian-norm premises, the sign counts give inertia, while LDL returns either a reconstructing positive-semidefinite factorization or a concrete negative quadratic-form witness.',
    'evidence': [ev('src/exact_field/congruence.rs', 37, 115), ev('src/exact_field/congruence.rs', 192, 306), ev('src/exact_field/ordered.rs', 36, 131), ev('src/exact_field/ordered.rs', 453, 590)],
    'controls': ['RLA-P21'],
    'limits': '760 independent rational symmetric cases, including33 PSD,445 negative-pivot and282 zero-pivot/nonzero-column outcomes. No native execution or universal validation of open scalar traits. Congruence production and optional replay are distinct, and sign guards alone do not prove ordering laws.'
}]
findings = [{
    'id': 'RLA-F08',
    'statement': 'The LDL documentation suggests a matrix can be positive definite up to a permutation yet have a zero leading principal minor, and presents this routine as incomplete for PSD. Under its lawful ordered/Hermitian premises this cannot occur: positive definiteness is invariant under permutation and every principal restriction remains positive definite. The implemented zero-pivot/zero-column rule is the complete PSD rule, consistent with later source tests.',
    'evidence': [ev('src/exact_field/ordered.rs', 398, 405), ev('src/exact_field/ordered.rs', 538, 571), ev('src/exact_field/ordered.rs', 1238, 1283)],
    'controls': ['RLA-P21'],
    'limits': 'A mathematical documentation inconsistency, not a demonstrated algorithmic false rejection. The finite control corroborates cases; completeness reasoning comes from the stated factorization and negative-witness construction.',
    'recommended_action': 'Remove the impossible positive-definite example and state that LDL completes exactly for PSD under lawful coefficient and representability premises.'
}]
for group, items in [('claims', claims), ('findings', findings)]:
    ids = {x['id'] for x in items}
    notes[group] = [x for x in notes[group] if x['id'] not in ids] + items
receipt = Path(str(P) + '_controls07.json')
result = json.loads(receipt.read_bytes())
assert result['status'] == 'finite_controls_pass'
assert hashlib.sha256(receipt.with_suffix('.py').read_bytes()).hexdigest() == result['helper_sha256']
ids = {x['id'] for x in result['controls']}
notes['controls'] = [x for x in notes['controls'] if x['id'] not in ids]
for item in result['controls']:
    notes['controls'].append({**item, 'receipt': {'path': receipt.relative_to(R).as_posix(), 'sha256': hashlib.sha256(receipt.read_bytes()).hexdigest()}})
path.write_text(json.dumps(notes, indent=2, ensure_ascii=False)+'\n', encoding='utf8')
print('Persisted two complete bodies, one claim, one documentation finding and one control.')
