"""Consolidate already-read evidence; no source imports or native execution."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
R = H.parents[1]
P = 'additional_paper_011_native'
B = 'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code/native_genesis_g12/original/lean4/Derivation/'

def ev(name, *ranges):
    p = B + name + '.lean'
    return {'path': p, 'sha256': hashlib.sha256((R / p).read_bytes()).hexdigest(), 'lines': list(ranges)}

claims = json.loads((H / (P + '_claims.json')).read_text(encoding='utf-8'))
new = [
    {
        'id': 'P011-NATIVE-C004',
        'statement': 'The signed list-boundary owner proves every double-boundary target coefficient zero, without ascending-list hypotheses in its strongest statement. Separate ascending-list lemmas establish distinct faces, and signless controls demonstrate that cancellation depends on the supplied signs. This is reusable exact finite chain arithmetic; the earlier wrong-dimension spot-checks are unnecessary to that general written theorem.',
        'source_evidence': [ev('BoundaryCancellation', [333, 423], [592, 626])],
        'status': 'full_written_proof_review_with_separate_bounded_arithmetic_control',
        'limits': 'No fresh Lean kernel run. Lists, integer coefficients and signed boundary convention are admitted; no derivation of geometric realization or physical topology.'
    },
    {
        'id': 'P011-NATIVE-C005',
        'statement': 'The trace owner supplies a replay-sound terminating and confluent normalizer for adjacent repetition and deletion after halt. It proves uniqueness for this rewrite relation and explicitly exhibits replay-equivalent histories with different normal forms, so the normalizer is useful for scoped trace compression but is not complete for all replay equivalence.',
        'source_evidence': [ev('TraceAlgebra', [756, 805], [922, 1001])],
        'status': 'full_written_source_and_proof_review',
        'limits': 'The supplied PEvent interpreter and equality notion determine soundness. No native/kernel execution, complete semantic quotient or autonomous event generation is inferred.'
    },
    {
        'id': 'P011-NATIVE-C006',
        'statement': 'The event-classification owner proves that every accepted step of its live protection-contained-in-retention state class has a unique declared one-step code. The codebook has 13 values, or 12 after the guard label is erased. Explicit common-suffix countermodels establish that this finite projection is not a congruence for future execution; policy origin labels also do not establish authority or provenance.',
        'source_evidence': [ev('TransitionAlphabet', [1113, 1257], [1395, 1669], [1763, 1818])],
        'status': 'full_written_source_and_proof_review',
        'limits': 'Cardinality is relative to the exact admitted grammar and projection. Witness minimality is not proved here; no fresh Lean or Python minimum search was run.'
    },
    {
        'id': 'P011-NATIVE-C007',
        'statement': 'For an inhabited carrier and a supplied symbol action, the Breaking owner proves that an orbit-constant equivariant endomap exists exactly when a common fixed point exists. The inhabitant is explicitly supplied and used to evaluate the selector, so the theorem does not make the false corresponding assertion for an empty carrier.',
        'source_evidence': [ev('Breaking', [387, 423])],
        'status': 'full_written_source_and_proof_review',
        'limits': 'No group laws are required by this theorem; orbit-constancy and equivariance are both explicit predicates. No general ban on equivariant maps or fresh kernel replay follows.'
    }
]
by_id = {c['id']: c for c in claims}
for c in new:
    c['evidence'] = [e['path'] for e in c['source_evidence']]
    by_id[c['id']] = c
(H / (P + '_claims.json')).write_text(json.dumps(list(by_id.values()), indent=2) + '\n', encoding='utf-8')
print({'claims': len(by_id)})
