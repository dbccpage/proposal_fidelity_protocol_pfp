"""Manual post-freeze grading of the corrected direct model control.

Only final answer_text supplies content. No provider reasoning/draft payloads,
private key or new provider calls are used. Original rubric weights are fixed.
"""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
RUN_SHA = '79f366959f1cc0b9e60bc63144cbe9ffccae12c53ec80163eada124f7ff75f1a'
ANSWER_SHA = '9454f47461812b86753a7593c37a8219b25658de71964e2ad6d461e5fb739e12'
raw = (H / 'runs/00_direct/run.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == RUN_SHA
answer = json.loads(raw)['answer_text']
assert hashlib.sha256(answer.encode()).hexdigest() == ANSWER_SHA
lines = answer.splitlines(keepends=True)
assert len(lines) == 661 and len(answer) == 28374


def excerpt(lo, hi=None):
    hi = lo if hi is None else hi
    start = sum(map(len, lines[:lo - 1]))
    quote = ''.join(lines[lo - 1:hi]).rstrip('\r\n')
    end = start + len(quote)
    assert answer[start:end] == quote
    return {'quote': quote, 'character_range': [start, end],
            'line_range': [lo, lo + len(quote.splitlines()) - 1]}


def omission():
    return {'kind': 'full_final_body_review_for_omission',
            'character_range': [0, len(answer)], 'line_range': [1, 661]}


rows = []


def row(cid, points, assessment, *evidence):
    rows.append({'criterion_id': cid, 'points': points,
                 'assessment': assessment, 'evidence': list(evidence)})


row('spectrum.block_reduction', 4,
    'Correct Pauli-product actions, invariant even/odd subspaces and Hamiltonian restrictions. Initial tentative Y-sign mistakes are explicitly corrected within the final answer.',
    excerpt(43, 61), excerpt(83, 100), excerpt(124, 146))
row('spectrum.energies', 4,
    'Correct full spectrum K,K,-K+/-2sqrt(J^2+Delta^2), with its generic multiplicities and zero-radius collapse.',
    excerpt(154, 176), excerpt(647))
row('spectrum.projectors', 4,
    'The orthogonal eigenvectors/outer products give the right complete resolution where the chosen angle exists. Deduct2: theta in[0,pi] with sin(theta)=J/r excludes every negative J, despite the all-real-parameter task. No angle-free spectral-projector replacement is supplied in this section.',
    excerpt(188, 211), excerpt(215, 226))
row('spectrum.coincident_energies', 0,
    'The answer mentions possible extra coincidence but never identifies K=+r or K=-r or explains their three-dimensional equal-energy eigenspaces. Deduct4 for the missing nonzero-radius crossing cases.',
    excerpt(168, 170), omission())
row('spectrum.zero_radius', 2,
    'J=Delta=0 is treated directly as H=K Z tensor Z with the two rank-two eigenspaces. K=0 complete degeneracy is explicitly stated.',
    excerpt(170, 176), excerpt(226))
row('dynamics.state', 6,
    'Correct generic spectral evolution, amplitudes and K phase. Deduct1 for the inherited invalid negative-J angle restriction, and1 because the zero-radius branch gives only a stationary/eigenstate statement, without the requested explicit ket evolution e^(iKt)|01>. This is a missing phase-resolved expression, not a claim that a stationary ray is physically wrong.',
    excerpt(194), excerpt(237, 267), excerpt(282, 290), excerpt(315), omission())
row('dynamics.probability', 4,
    'Correct transition probability, with J=0 and r=0 separately stated as constant zero. The later summary is consistent with the derived frequency.',
    excerpt(301), excerpt(312, 315), excerpt(648))
row('dynamics.supremum', 4,
    'Correct general nonzero-radius supremum and explicit zero/constant cases.',
    excerpt(308, 315), excerpt(649))
row('dynamics.earliest_and_constant_branches', 3,
    'The final summary correctly restricts pi/(4r) to J!=0, repairing the earlier overbroad r>0 wording. Deduct1 because no constant-probability branch explicitly identifies the earliest maximizing time t=0.',
    excerpt(310, 315), excerpt(649), omission())
row('pure_state.reduced_density', 4,
    'Correct explicit partial trace: orthogonal second-spin factors kill both cross terms. The resulting diag(1-p,p) has trace one.',
    excerpt(338, 347), excerpt(353), excerpt(650))
row('pure_state.entropy', 3,
    'Correct binary entropy in bits. Deduct1 for the absent0log0=0 endpoint convention, needed at the initial and decoupled states.',
    excerpt(351, 353), excerpt(650), omission())
row('pure_state.concurrence', 4,
    'Correct coefficient-matrix determinant reasoning and explicit C=2sqrt(p(1-p)). The initial real-coefficient hesitation is superseded by the correct general complex formula.',
    excerpt(359, 365), excerpt(380, 385), excerpt(651))
row('pure_state.CHSH', 2,
    'Credit2 for the correct optimization framework and several correctly derived correlations, including opposite XY/YX signs and ZZ=-1. Deduct4: the final displayed T reverses its correctly derived YX sign, its Gram multiplication drops nonzero off-diagonals, and it selects the two C^2 eigenvalues rather than the largest1 and C^2. The settled result2sqrt(2)C is false; at t=0 it predicts0 instead of2.',
    excerpt(392, 394), excerpt(432, 451), excerpt(458, 491), excerpt(652))
row('pure_state.maximal_entanglement_reachability', 3,
    'Correct |J|>=|Delta| condition on the nonzero-coupling branch, including equality. Deduct1 because the final reachability statement does not exclude J=Delta=0, which satisfies that inequality but remains a product state.',
    excerpt(499, 507), excerpt(315), excerpt(653))
row('pure_state.earliest_maximal_entanglement', 2,
    'Correct general root equation and explicit earliest Delta=0 value pi/(8|J|); equality is recognized as sin^2=1. Deduct1 because no explicit general earliest-root/arcsine expression with the unreachable and zero-coupling branches is completed; the text instead says the Delta=0 example suffices.',
    excerpt(507, 517), excerpt(653), omission())
row('thermal.Gibbs_state', 6,
    'Correct normalized spectral Gibbs state and full computational-basis entries A,B,D. The later explicit c^2=(1+Delta/r)/2, s^2=(1-Delta/r)/2 and signed D=-J exp(beta K)sinh(2beta r)/r make these entries computable and correct for either sign of J, despite the earlier eigenvector-angle defect. The zero-radius Gibbs state is supplied separately.',
    excerpt(540), excerpt(549, 562), excerpt(629))
row('thermal.partition_function', 4,
    'Correct trace with the even degeneracy: Z=2exp(-beta K)+2exp(beta K)cosh(2beta r).',
    excerpt(523, 532))
row('thermal.partial_transpose', 7,
    'Correct spin2 partial-transpose convention, moved coherence block and all four eigenvalues. Listing e^(-beta K)+/-D is equivalent to the unordered pair with +/-|D|.',
    excerpt(566, 599))
row('thermal.entanglement_criterion', 5,
    'The two-qubit PPT argument gives the correct necessary and sufficient strict inequality, using positivity of A,B. The stated iff and strict inequality imply separability on equality; r=0 is separately declared separable.',
    excerpt(604, 629), excerpt(656))
row('thermal.thermal_limits', 3,
    'Both beta=0 and J=Delta=0 are treated explicitly without using undefined r denominators; both states are separable.',
    excerpt(627, 629))
row('checks.conventions', 2,
    'Consistent final Pauli/basis/Hamiltonian, entropy log2, and spin2 partial-transpose conventions. The wrong CHSH correlation entry is charged to CHSH, not double-counted as a convention change.',
    excerpt(10, 19), excerpt(48, 61), excerpt(351), excerpt(568))
row('checks.normalization', 2,
    'Explicit squared-amplitude identity verifies normalization using c^2+s^2=1 and the correct trigonometric frequency.',
    excerpt(635))
row('checks.initial_condition', 2,
    'Explicit t=0 substitution a=1,b=0 is correct and agrees with the displayed evolution.',
    excerpt(267), excerpt(637))
row('checks.decoupled_limit', 1,
    'The no-transition J=0 check is correct, with an explicit positive-Delta eigenbasis branch. Deduct1 because the negative-Delta and zero-radius ket/phase checks are not completed in this check, and the constant-time exception is not verified.',
    excerpt(639), excerpt(312, 315), omission())
row('checks.nontrivial_numerical_example', 2,
    'The J=1,Delta=K=0,t=pi/8 example correctly gives P=1/2, the displayed Bell state and concurrence1. It is identified as a numerical/example check rather than proof of all parameters.',
    excerpt(641))

counterexamples = [
    {'id': 'MC-CE-01', 'issue': 'Incorrect maximal CHSH formula',
     'parameters': {'J': 1, 'Delta': 0, 'K': 0, 't': 0},
     'state': '|01>', 'concurrence': 0, 'asserted_maximal_CHSH': 0, 'actual_maximal_CHSH': 2,
     'argument': 'The answer own T^T T eigenvalues become0,0,1, so the two largest sum to1. Directly, A=A_prime=Z and B=B_prime=-Z give CHSH=-2 Z tensor Z and expectation2 in |01>. Product correlations also bound the maximum by2.',
     'evidence': [excerpt(483, 491), excerpt(637), excerpt(652)]},
    {'id': 'MC-CE-02', 'issue': 'Displayed correlation-matrix Gram calculation is false',
     'normalized_amplitudes': {'a': '3/5', 'b': '12/25+16i/25'},
     'alpha': '72/125', 'beta': '96/125',
     'asserted_symmetric_T_gram_off_diagonal': '-13824/15625',
     'claimed_gram_off_diagonal': '0',
     'argument': 'For the displayed symmetric block[[alpha,-beta],[-beta,alpha]], the off-diagonal of T^T T is-2alpha beta, not0. The actual YX entry has the opposite sign, as the answer itself correctly derives earlier.',
     'evidence': [excerpt(439, 441), excerpt(458, 481)]},
    {'id': 'MC-CE-03', 'issue': 'Negative-J eigenvector parametrization has no admitted angle',
     'parameters': {'J': -1, 'Delta': 0, 'K': 0},
     'argument': 'r=1 requires sin(theta)=-1 although theta is restricted to[0,pi]. Thus the proposed generic eigenbasis is undefined there. Choosing theta=pi/2 from its cosine alone would give the opposite odd eigenvalue.',
     'evidence': [excerpt(193, 194), excerpt(211, 223)]},
    {'id': 'MC-CE-04', 'issue': 'Unexcluded zero-coupling maximal-entanglement condition',
     'parameters': {'J': 0, 'Delta': 0, 'K': 1},
     'asserted_inequality': '|J|>=|Delta| is true',
     'actual_state': 'exp(it)|01>', 'actual_concurrence': 0,
     'argument': 'The state stays a product at every time; the final reachability inequality needs J!=0. The following earliest-time clause restricts J but does not explicitly restrict the preceding reachability assertion.',
     'evidence': [excerpt(315), excerpt(505, 507), excerpt(653)]}
]
assert len(rows) == 25 and sum(r['points'] for r in rows) == 83
(H / 'criterion_assessments.json').write_text(json.dumps(
    {'run_sha256': RUN_SHA, 'answer_sha256': ANSWER_SHA, 'criteria': rows,
     'counterexamples': counterexamples}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
(H / 'evaluation.md').write_text('''# Corrected model-control evaluation

The frozen final answer scores **83/100** under the unchanged 25-criterion rubric. It completes substantially more of the requested mathematics, including the Gibbs state and all partial-transpose eigenvalues, but retains a wrong maximal CHSH formula and several exceptional-parameter gaps.

| Section | Points |
|---|---:|
| Spectrum | 14/20 |
| Dynamics | 17/20 |
| Pure-state entanglement | 18/25 |
| Thermal entanglement | 25/25 |
| Consistency checks | 9/10 |
| Total | **83/100** |

The correct Hamiltonian blocks, spectrum, transition probability, reduced state, concurrence, Gibbs matrix, partition function, partial transpose and strict thermal-entanglement condition earn credit. The explicit thermal entries correctly handle signed J, and both requested thermal limits are supplied.

The main defects are:

- The final CHSH maximum is 2sqrt(2)C instead of 2sqrt(1+C^2). At the initial product state it predicts 0; local Z measurements attain 2. The derivation reverses its own correctly computed YX sign, drops nonzero Gram-matrix terms and selects the wrong pair of eigenvalues.
- The eigenvector angle is restricted to [0,pi] while sin(theta)=J/r, so negative J is not represented. The K=+r and K=-r spectral crossings are not handled.
- The exact zero-radius ket phase, entropy endpoint convention and earliest constant-probability maximum are absent. The maximal-entanglement condition does not explicitly exclude J=Delta=0; the general earliest entangling time remains an implicit equation plus a Delta=0 example.

The evaluator read all 661 lines / 28,374 Unicode characters of final `answer_text` after freeze confirmation. Provider reasoning and draft payloads supplied no credit. This run used one call with 10,805 output tokens and finish reason `stop`, spending 4,211 microUSD with zero held charges. It is separate from the original zero-dispatch admission failure.

All 25 criterion scores, exact quotations, four concrete mathematical controls and receipt/rubric/reference hashes are preserved in the adjacent JSON artifacts. The pre-output reference and original rubric weights remain unchanged. This is one model-control sample on one fixed problem, not a general model or workflow ranking.
''', encoding='utf-8')
print(json.dumps({'criteria': 25, 'total': 83}))
