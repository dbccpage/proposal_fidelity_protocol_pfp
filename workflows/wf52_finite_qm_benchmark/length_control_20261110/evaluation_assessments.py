"""Manual final-only judgments, with mechanical extraction of exact evidence ranges.

This is evaluator material, never workflow input. Run only after the recorded
parent freeze confirmation. It does not inspect provider evidence or drafts.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_SHA = 'ac77cbf6a6486715ce146b8c4568742dc673b0430051d1cb0ad6b4e7cb5d748b'
ANSWER_SHA = '2a69e0b747904235b40a098b1e7c3cf06c4151dc16f84ab8d467c8d05a46e4e1'
raw = (HERE / 'runs/00_direct/run.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == RUN_SHA
receipt = json.loads(raw)
answer = receipt['answer_text']
assert hashlib.sha256(answer.encode()).hexdigest() == ANSWER_SHA
lines = answer.splitlines(keepends=True)
assert len(lines) == 785 and len(answer) == 26199


def excerpt(lo, hi=None):
    hi = lo if hi is None else hi
    start = sum(map(len, lines[:lo - 1]))
    quote = ''.join(lines[lo - 1:hi]).rstrip('\r\n')
    end = start + len(quote)
    assert answer[start:end] == quote
    return {'quote': quote, 'character_range': [start, end],
            'line_range': [lo, hi]}


def omission():
    return {'kind': 'full_final_body_review_for_omission',
            'character_range': [0, len(answer)], 'line_range': [1, 785]}


rows = []


def row(criterion_id, points, assessment, *evidence):
    rows.append({'criterion_id': criterion_id, 'points': points,
                 'assessment': assessment, 'evidence': list(evidence)})


row('spectrum.block_reduction', 4,
    'The tensor-product derivation gives the correct even/odd invariant blocks and Hamiltonian matrix, including both factors of 2.',
    excerpt(164, 172), excerpt(181, 184))
row('spectrum.energies', 4,
    'The quadratic calculation yields K twice and -K +/- 2 sqrt(J^2+Delta^2).',
    excerpt(191, 202), excerpt(207, 212))
row('spectrum.projectors', 4,
    'The displayed orthonormal eigenvectors and their outer products give a complete spectral resolution on the valid angle domain. Deduct 2: theta in [0,pi] with sin(theta)=J/D does not exist for J<0; thus the claimed general-real-parameter projectors are undefined there. The explicit eigenvector verification is credited on its admitted domain.',
    excerpt(277, 280), excerpt(301, 310), excerpt(323, 325))
row('spectrum.coincident_energies', 4,
    'Both K=D and K=-D crossings and the resulting three-dimensional equal-energy eigenspace are explained. The rubric allows this equivalent degeneracy explanation without an explicit merged-projector matrix.',
    excerpt(332, 338))
row('spectrum.zero_radius', 2,
    'The D=0 block is treated directly, with K and -K each twice and explicit complete degeneracy at K=0.',
    excerpt(340, 355))
row('dynamics.state', 7,
    'The spectral evolution, computational-basis expansion, signed beta amplitude, and D=0 phase are correct. Deduct 1 for the remaining invalid negative-J theta restriction in the state representation. The correct explicit signed beta and the equivalent half-angle-square alpha earn substantial credit; this is not treated as a wrong transition probability.',
    excerpt(395, 406), excerpt(450), excerpt(471), excerpt(518, 531), excerpt(310))
row('dynamics.probability', 4,
    'Correct transition probability, with J=0 and D=0 separately assigned zero.',
    excerpt(462, 473))
row('dynamics.supremum', 4,
    'Correct J^2/(J^2+Delta^2) for D>0 and the constant zero-radius value from the explicit constant branch.',
    excerpt(478), excerpt(487, 492))
row('dynamics.earliest_and_constant_branches', 2,
    'Correct earliest oscillatory maximum for J!=0. Deduct 2: the stated condition D>0 wrongly includes J=0, Delta!=0, for which every time maximizes zero probability and the earliest is t=0. The D=0 branch says constant but does not give earliest t=0.',
    excerpt(467), excerpt(481, 492))
row('pure_state.reduced_density', 4,
    'The final corrected partial trace is diag(|alpha|^2,|beta|^2), with unit trace. Earlier erroneous off-diagonal attempts are explicitly retracted within the final answer and receive no separate credit or penalty.',
    excerpt(628, 643))
row('pure_state.entropy', 3,
    'Correct binary entropy in bits. Deduct 1 for omitting the required 0 log 0 = 0 endpoint convention; the initial and decoupled states have zero eigenvalues.',
    excerpt(667), omission())
row('pure_state.concurrence', 4,
    'The final concurrence is correct and has a correct reduced-purity calculation. Full criterion credit is retained despite the contradictory, false phase qualifications at lines 685-687 and 709; those qualifications are separately recorded as explanatory defects and are not needed for the valid purity derivation.',
    excerpt(691, 707), excerpt(709, 711))
row('pure_state.CHSH', 3,
    'Correct final maximal value 2 sqrt(1+C^2) and connection to Schmidt weights. Deduct 3: no self-contained correlation-matrix or measurement optimization proves the maximum; the intermediate lambda_1/lambda_2 statement is also inconsistent. Recollection of a formula does not fulfill the derivation half of this criterion.',
    excerpt(719, 729), omission())
row('pure_state.maximal_entanglement_reachability', 4,
    'Correct necessary and sufficient condition |Delta|<=|J| with J!=0, derived from requiring transition probability 1/2 and explicitly excluding the zero-coupling case.',
    excerpt(742, 749), excerpt(753, 755), excerpt(775, 779))
row('pure_state.earliest_maximal_entanglement', 3,
    'The stated principal-arcsine formula is the earliest time on the reachable branch. It includes the equality case, and unreachable/zero-coupling cases are explicitly excluded.',
    excerpt(749), excerpt(755), excerpt(761, 781))
for name in ['Gibbs_state', 'partition_function', 'partial_transpose',
             'entanglement_criterion', 'thermal_limits']:
    row('thermal.' + name, 0,
        'Omitted from the delivered final answer. It stops after Part 3 and requests continuation; there is no thermal calculation to grade.',
        excerpt(785), omission())
row('checks.conventions', 1,
    'Correct Pauli/basis/Hamiltonian and entropy log-base conventions. Deduct 1 because the spin-2 partial-transpose convention is never instantiated or checked in the omitted thermal part.',
    excerpt(1, 16), excerpt(667), omission())
row('checks.normalization', 2,
    'The explicit squared-amplitude expansions together with the unit-trace statement supply an equivalent normalization consistency check: using a=c^2,b=s^2, their sum reduces to (a+b)^2=1. This is credited independently of merely declaring a normalized ket.',
    excerpt(643), excerpt(653, 663))
row('checks.initial_condition', 2,
    'The explicit reconstruction c psi_plus - s psi_minus = |01> verifies the initial condition of the subsequent spectral evolution at t=0.',
    excerpt(377, 395))
row('checks.decoupled_limit', 1,
    'The explicit J=0 no-transition check and D=0 eigenstate evolution earn partial credit. Deduct 1: there is no complete general J=0 state/entanglement/thermal consistency check, and the earliest-time claim contradicts the constant branch.',
    excerpt(467, 473), excerpt(484), excerpt(775, 777), omission())
row('checks.nontrivial_numerical_example', 0,
    'No nontrivial numerical parameter example or numerical cross-check occurs in the full delivered body.',
    excerpt(785), omission())

counterexamples = [
    {'id': 'LC-CE-01', 'issue': 'Negative-J angle domain',
     'parameters': {'J': -1, 'Delta': 0, 'K': 0},
     'argument': 'D=1 requires sin(theta)=-1 although theta is restricted to [0,pi]. No such theta exists. If theta=pi/2 were selected from cos(theta)=0 alone, v=(1,1) would have odd-block eigenvalue -2, not the claimed +2.',
     'exact_unnormalized_control': {'odd_block': [[0, -2], [-2, 0]],
                                 'v': [1, 1], 'Hv': [-2, -2],
                                 'claimed_plus_energy_times_v': [2, 2]},
     'evidence': [excerpt(277, 286)]},
    {'id': 'LC-CE-02', 'issue': 'Earliest maximum of a constant function',
     'parameters': {'J': 0, 'Delta': 1, 'K': 0},
     'argument': 'P(t)=0 for every t>=0. The first maximizing time is 0, while the answer gives pi/4 because D=1>0.',
     'evidence': [excerpt(467), excerpt(484)]},
    {'id': 'LC-CE-03', 'issue': 'False phase qualification in the explanation',
     'parameters': {'alpha': '1/sqrt(2)', 'beta': 'i/sqrt(2)'},
     'argument': '|alpha beta|=1/2=|alpha||beta| regardless of their relative phase. In general |zw|^2=|z|^2|w|^2. The answer ultimately uses the correct concurrence and valid purity derivation; this explanatory defect is recorded without an additional point deduction.',
     'evidence': [excerpt(685, 687), excerpt(709, 711)]}
]
assert len(rows) == 25
manual = {'run_sha256': RUN_SHA, 'answer_sha256': ANSWER_SHA,
          'criteria': rows, 'counterexamples': counterexamples}
(HERE / 'criterion_assessments.json').write_text(
    json.dumps(manual, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

report = r'''# Length-control evaluation

The delivered final answer scores **62/100** under the unchanged, pre-frozen 25-criterion rubric. It substantially answers Parts 1–3, then stops before the thermal calculation and numerical example. Its last sentence is “Due to length, we pause here and continue in next message.”

| Section | Points |
|---|---:|
| Spectrum | 18/20 |
| Dynamics | 17/20 |
| Pure-state entanglement | 21/25 |
| Thermal entanglement | 0/25 |
| Consistency checks | 6/10 |
| Total | **62/100** |

The correct Hamiltonian, spectrum, transition probability, reduced density matrix, final concurrence and CHSH formula, and maximal-entanglement reachability/time earn substantial credit. The final answer explicitly corrects its earlier erroneous reduced-density attempt; that abandoned expression is not graded as the settled result.

Material deductions and limitations:

- The eigenvectors require theta in [0,pi] while setting sin(theta)=J/D. This is impossible for negative J. At J=-1, Delta=K=0, choosing theta=pi/2 from its cosine alone gives the opposite eigenvalue. This affects the claimed general projectors and the state parametrization; the explicit signed transition amplitude is nevertheless correct.
- The earliest probability maximum pi/(4D) is incorrectly stated for all D>0. With J=0, Delta=1, probability is constantly zero and the earliest maximizing time is 0.
- The entropy endpoint convention is absent. The correct CHSH formula is recalled but no measurement/correlation-matrix optimization derives it. Contradictory phase comments around concurrence are mathematically false; the final formula and independent purity calculation remain correct and receive full concurrence credit.
- All five thermal criteria and the nontrivial numerical example are absent. Partial-transpose conventions and a complete decoupled-limit check are consequently incomplete.

The host receipt is completed, with one call, 11,241 output tokens, finish reason `stop`, and 6,222 microUSD spent with zero held charges. This was **not a provider-reported length cutoff**. Mathematical incompleteness is assessed from the delivered final answer, which voluntarily requests another message. The evaluator did not execute another model call.

The evaluator fully read all 785 lines / 26,199 Unicode characters of `answer_text`. No drafts, matrix proposals, nested provider evidence, or private answer material supplied grading credit. The reused public-seed reference provenance was frozen before current-output access. Exact source/answer/rubric hashes, all 25 judgments, deductions and exact quote ranges are in `grades.json` and `criterion_evidence.json`; machine validation is in `evaluation_validation.json`.

This is one length-control attempt on one fixed problem. It measures delivered coverage for this attempt; it does not establish a general workflow or model ranking. Previous experiments and grades are unchanged.
'''
(HERE / 'evaluation.md').write_text(report, encoding='utf-8')
print(json.dumps({'manual_criteria': len(rows), 'total': sum(r['points'] for r in rows)}))
