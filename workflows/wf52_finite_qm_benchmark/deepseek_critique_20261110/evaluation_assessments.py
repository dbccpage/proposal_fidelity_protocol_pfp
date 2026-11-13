"""Manual final-only judgments under the unchanged, pre-output rubric."""
import importlib.util
import json
from pathlib import Path

H = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('evaluation_tools', H / 'evaluation_tools.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
m.preparation()
v, _ = m.validator()
run, run_sha = v.read_frozen_receipt(m.RUN_PATH)
assert run_sha == '9f961bc5eca2d597df3bc8fc6384910917e0cd002de21e16f3645978c4737489'
answer = run['answer_text']
assert run['answer_sha256'] == 'ab4786978b6419b19fc4e1bbe28c7b083c66a1267dd198a75104c4f5b0540ba8'
lines = answer.splitlines(keepends=True)

def q(lo, hi):
    start = sum(map(len, lines[:lo-1]))
    quote = ''.join(lines[lo-1:hi]).rstrip('\r\n')
    return {'quote': quote, 'character_range': [start, start+len(quote)],
            'line_range': [lo, lo+len(quote.splitlines())-1]}

def omission():
    return {'kind': 'full_final_body_review_for_omission',
            'character_range': [0, len(answer)], 'line_range': [1, len(lines)]}

rows = []
def criterion(cid, points, assessment, *evidence):
    rows.append({'criterion_id': cid, 'points': points,
                 'assessment': assessment, 'evidence': list(evidence)})

criterion('spectrum.block_reduction', 4,
    'Correct tensor products, factor2 in both odd-block terms, and invariant even/odd reduction derived in the stated basis.', q(21,50), q(52,68))
criterion('spectrum.energies', 4,
    'Correct four eigenvalues K,K,-K+2R,-K-2R; the generic multiplicities are stated. Coincident-energy completeness is scored separately.', q(66,77))
criterion('spectrum.projectors', 6,
    'The real c,d basis is normalized and orthogonal for R+Delta>0, including negative J. Its rank-one projectors plus the even projector resolve identity and reconstruct H. J=0,Delta<0 is explicitly handled by swapped computational eigenvectors. Equal-energy merging is scored separately.', q(82,102), q(104,114))
criterion('spectrum.coincident_energies', 2,
    'The equation K=-K+/-2R identifies both possible crossings implicitly. It does not give K=+/-R with their rank3 merged projectors/eigenspaces; the summary again calls K doubly degenerate without an exception.', q(75,77), q(99,102), q(368,368), omission())
criterion('spectrum.zero_radius', 1,
    'R=0 is handled with even/odd computational projectors and no division, but K=0 is not identified as a single rank4 zero-energy eigenspace. At that point the two claimed doubly degenerate energies coincide.', q(104,114), omission())

criterion('dynamics.state', 8,
    'Correct odd-block exponential, global phase and signs. The otherwise singular R=0 evolution is explicitly supplied later as exp(iKt)|01>.', q(125,146), q(352,353))
criterion('dynamics.probability', 4,
    'Correct J^2/R^2 sin^2(2Rt), with J=0 and R=0 assigned probability0.', q(149,163))
criterion('dynamics.supremum', 4,
    'Correct nonzero-radius supremum and explicit zero-coupling/zero-radius supremum0. The Delta=0 perfect-oscillation bullet is read with the more specific zero-radius exception stated immediately below it.', q(154,163))
criterion('dynamics.earliest_and_constant_branches', 3,
    'Correct pi/(4R) for J!=0 and correctly recognizes constant probability for J=0, but the assertion that there is no unique earliest time is false on t>=0: the earliest maximizing time is0.', q(165,173), q(374,374))

criterion('pure_state.reduced_density', 4,
    'Correct partial trace diag(1-p,p); its diagonal entries sum to1. The vanished cross terms are correctly associated with orthogonal second-spin basis states.', q(179,188))
criterion('pure_state.entropy', 3,
    'Correct binary entropy in bits, but no0log0=0 endpoint convention is supplied, including at the initial product state.', q(191,194), q(376,376), omission())
criterion('pure_state.concurrence', 4,
    'Correct spin-flip definition and specialization C=2|ab|=2sqrt(p(1-p)).', q(196,200))
criterion('pure_state.CHSH', 3,
    'The general formula and final summary correctly give2sqrt(1+C^2), earning formula credit. The proposed derivation is invalid and internally contradictory: Tyy has the wrong sign, phase-sensitive Txy/Tyx are dropped, and the derived expression215 gives2 for Delta=0 even when C=1. For J=1,Delta=K=0,t=pi/8 the exact T has singular values1,1,1 and the maximum is2sqrt2.', q(202,215), q(356,361), q(376,376))
criterion('pure_state.maximal_entanglement_reachability', 3,
    'Correct nonzero-coupling threshold |J|>=|Delta|, but the stated iff includes J=Delta=0, which preserves a product state. The missing requirement is J!=0.', q(218,227), q(352,353), q(376,376))
criterion('pure_state.earliest_maximal_entanglement', 2,
    'The principal-arcsine formula is correct on J!=0 and |J|>=|Delta|. However the explicit equality branch is wrong: |J|=|Delta|!=0 gives pi/(4sqrt2|J|), not pi/(8|J|). The formula also has no defined zero-coupling branch despite the preceding iff including it.', q(229,246))

criterion('thermal.Gibbs_state', 6,
    'Correct spectral Gibbs construction and computational-basis matrix, with normalized weights. The c,d matrix representation is explicitly restricted to R+Delta>0; the earlier swapped computational eigenvectors and the stated R=0 diagonal branch supply the exceptional spectral basis.', q(261,283), q(95,97), q(336,338))
criterion('thermal.partition_function', 4,
    'Correct degeneracy-weighted partition function2exp(-beta K)+2exp(beta K)cosh(2beta R).', q(252,258))
criterion('thermal.partial_transpose', 7,
    'Correct spin2 partial transpose, two scalar eigenvalues and unordered pair(C+/-w)/Z. The pair need not use |w| to be a correct eigenvalue multiset.', q(285,305))
criterion('thermal.entanglement_criterion', 4,
    'The final iff and strict inequality are correct and imply equality is separable. The displayed derivation incorrectly turns w>C into |w|>C; for J>0,beta>0, w<0 and the negative eigenvalue is(C+w)/Z, not(C-w)/Z. The result is recoverable from the correctly listed unordered eigenvalue pair, but the supplied sign argument is not valid as written.', q(307,333), q(378,378))
criterion('thermal.thermal_limits', 3,
    'Correct beta=0 maximally mixed state and R=0 diagonal/separable state for every beta, stated separately from the divided formulas.', q(336,338), q(104,114), q(261,264))

criterion('checks.conventions', 2,
    'Pauli/basis and Hamiltonian conventions, entropy log base and second-spin partial transpose are stated consistently. The separate CHSH algebra defect is deducted under its owning criterion.', q(3,12), q(21,49), q(191,194), q(285,292))
criterion('checks.normalization', 2,
    'Explicit evolved-state norm identity is a valid independent consistency check; thermal normalization is also identified.', q(344,347))
criterion('checks.initial_condition', 2,
    'Explicit a(0)=1,b(0)=0 check recovers the given initial state.', q(349,350))
criterion('checks.decoupled_limit', 1,
    'The explicit dynamical consistency check covers only J=Delta=0. Other passages cover eigenvectors and zero transition probability for J=0, but the general Delta!=0 decoupled evolution and its consequences are not checked together.', q(95,97), q(160,163), q(352,353), omission())
criterion('checks.nontrivial_numerical_example', 2,
    'The example J=1,Delta=K=0,t=pi/8 correctly gives p=1/2 and C=1, with exact amplitudes. It is presented separately from the general derivation. Its omitted CHSH check does not cure the CHSH contradiction.', q(355,362))

counterexamples = [
    {'id': 'DSC-CE-01', 'criterion': 'pure_state.CHSH',
     'parameters': {'J': 1, 'Delta': 0, 'K': 0, 't': 'pi/8'},
     'state': '(|01>-i|10>)/sqrt2',
     'actual_T': [[0,1,0],[-1,0,0],[0,0,-1]],
     'actual_CHSH_max': '2sqrt2', 'displayed_derived_CHSH': '2',
     'evidence': [q(207,215), q(356,361)],
     'scope': 'Direct Pauli expectations and Gram multiplication; no provider or source execution.'},
    {'id': 'DSC-CE-02', 'criterion': 'pure_state.earliest_maximal_entanglement',
     'parameters': {'J': 1, 'Delta': 1, 'K': 0},
     'claimed_earliest_time': 'pi/8', 'actual_earliest_time': 'pi/(4sqrt2)',
     'probability_at_claimed_time': '(1/2)sin^2(pi sqrt2/4)<1/2',
     'evidence': [q(240,246)],
     'scope': 'Exact branch substitution;0<pi sqrt2/4<pi/2 gives a strict failure to attain maximal entanglement.'},
    {'id': 'DSC-CE-03', 'criterion': 'pure_state.maximal_entanglement_reachability',
     'parameters': {'J': 0, 'Delta': 0, 'K': 1},
     'asserted_reachable': True, 'state': 'exp(it)|01>', 'actual_concurrence': 0,
     'evidence': [q(225,227), q(352,353)],
     'scope': 'Exact diagonal Hamiltonian; no entanglement is generated.'},
    {'id': 'DSC-CE-04', 'criterion': 'dynamics.earliest_and_constant_branches',
     'parameters': {'J': 0, 'Delta': 1, 'K': 0},
     'probability_all_times': 0, 'set_of_maximizers': '[0,infinity)',
     'actual_earliest_maximizer': 0,
     'evidence': [q(173,173)], 'scope': 'The ordered time domain has minimum0 even though all times maximize.'},
    {'id': 'DSC-CE-05', 'criterion': 'thermal.entanglement_criterion',
     'parameters': {'J': 1, 'Delta': 0, 'K': 0, 'beta': 1},
     'w': '-sinh2', 'C': 1, 'w_greater_C': False,
     'absolute_w_greater_C': True, 'negative_eigenvalue': '(1-sinh2)/Z',
     'evidence': [q(307,324)],
     'scope': 'Refutes the intermediate equivalence w>C iff |w|>C, not the final entanglement inequality.'}
]
assert len(rows) == 25
m.write_json('criterion_assessments.json', {'run_sha256': run_sha,
    'answer_sha256': run['answer_sha256'], 'criteria': rows,
    'counterexamples': counterexamples,
    'method': 'Trusted independent full-final-body mathematical review after freeze; no draft, critique, reasoning or earlier-answer credit.'})
print(json.dumps({'criteria': len(rows), 'manual_total': sum(r['points'] for r in rows)}))
