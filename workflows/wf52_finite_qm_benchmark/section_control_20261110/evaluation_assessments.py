"""Post-freeze manual final-only grades and exact final-answer quotations.

Evaluator-only material. No provider calls, draft reads, private references or
workflow modifications. The independent raw sections are graded as one answer.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_SHA = '2485687210cbc5b5a68ed078659ada960ad263a5a62fd6f70e42292098cfce8c'
ANSWER_SHA = 'd176dd483a23c8bff6c580929de3609146ab1941a36eb6e6f837e6910dbd8ed5'
raw = (HERE / 'runs/00_sections/run.json').read_bytes()
assert hashlib.sha256(raw).hexdigest() == RUN_SHA
answer = json.loads(raw)['answer_text']
assert hashlib.sha256(answer.encode()).hexdigest() == ANSWER_SHA
lines = answer.splitlines(keepends=True)
assert len(lines) == 805 and len(answer) == 37510


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
            'character_range': [0, len(answer)], 'line_range': [1, 805]}


rows = []


def row(criterion_id, points, assessment, *evidence):
    rows.append({'criterion_id': criterion_id, 'points': points,
                 'assessment': assessment, 'evidence': list(evidence)})


row('spectrum.block_reduction', 2,
    'Correct invariant subspaces and corrected odd block in Parts1-2 earn partial credit. Deduct2 for unresolved cross-section contradictions: Part3 substitutes an odd block involving K instead of Delta, and Part4 adds a nonexistent even-sector2J coupling and reverses Delta. The assembly never chooses or reconciles these incompatible Hamiltonians.',
    excerpt(135, 137), excerpt(254, 261), excerpt(386, 391), excerpt(647, 657))
row('spectrum.energies', 2,
    'The odd energies -K+/-2sqrt(J^2+Delta^2) are derived correctly, and the even block K I appears in Part1. Deduct2 because the final assembly also explicitly asserts the false full spectrum K+/-2J,-K+/-2r, contradicting the even multiplicity.',
    excerpt(170, 174), excerpt(274, 276), excerpt(669, 674))
row('spectrum.projectors', 2,
    'Credit2 for the correct normalized odd eigenvectors, valid all-sign theta convention and explicit orthogonality/eigenvalue calculation in Part2. Deduct4: no complete spectral-projector resolution/reconstruction is delivered; the thermal section additionally gives eigenvectors for its incompatible Hamiltonian.',
    excerpt(295, 301), excerpt(314, 322), excerpt(702, 706), omission())
row('spectrum.coincident_energies', 0,
    'Neither K=+r nor K=-r even/odd crossing, nor a merged equal-energy eigenspace, is handled. The generic discussion of ordering and degeneracy does not supply these cases.',
    excerpt(674), omission())
row('spectrum.zero_radius', 1,
    'The check section explicitly reduces J=Delta=0 to H=K Z tensor Z, and its J=0 energy list specializes to K,-K,-K,K. Deduct1: there is no explicit zero-radius spectral resolution or complete K=0 degeneracy treatment.',
    excerpt(754, 759), excerpt(767), omission())
row('dynamics.state', 4,
    'Part2 derives the correct generic spectral evolution and amplitudes, and Part5 supplies the correct J=0 eigenstate phase. Deduct4 for the unretracted incompatible Part3 Hamiltonian/state, which depends on K as a detuning and drops Delta. Credit is for the correct delivered subderivation, not an assumed reconciliation.',
    excerpt(330, 350), excerpt(394, 400), excerpt(445, 461), excerpt(761))
row('dynamics.probability', 2,
    'Part2 gives the correct probability for r>0 and an explicit J=0 branch. Deduct2: Part5 repeats a probability with half the correct oscillation frequency, and Part3 uses a different detuning; the zero-radius denominator is also falsely declared harmless because its numerator vanishes.',
    excerpt(370, 377), excerpt(574), excerpt(765, 767))
row('dynamics.supremum', 1,
    'Only the specific J=Delta=1,K=0 value1/2 is correctly stated. Deduct3 because the general supremum, with all parameter branches, is absent; the example is not a general result.',
    excerpt(770, 778), omission())
row('dynamics.earliest_and_constant_branches', 0,
    'No correct general earliest maximizing time or t=0 constant-case maximum is supplied. The one proposed nontrivial maximizing time pi/(2sqrt2) is wrong: for J=Delta=1,K=0 the true probability there is0, while the first maximum occurs at pi/(4sqrt2).',
    excerpt(377, 379), excerpt(776, 778), omission())
row('pure_state.reduced_density', 1,
    'Credit1 for identifying the two diagonal partial-trace contributions. Deduct3 because the settled reduced matrix wrongly retains coherences between terms with orthogonal second-spin states, and uses the wrong evolved amplitudes. At J=1,Delta=K=0,t=pi/8 it predicts a rank-one matrix instead of I/2.',
    excerpt(490, 498), excerpt(527, 537))
row('pure_state.entropy', 2,
    'Credit2 for the correct generic Schmidt-weight binary-entropy formula in bits. Deduct2: the time-dependent weights come from the wrong Hamiltonian, the entropy contradicts the displayed rank-one reduced matrix, and the required endpoint convention0log0=0 is absent.',
    excerpt(550, 580), omission())
row('pure_state.concurrence', 2,
    'Credit2 for the correct generic coefficient-matrix identity C=2|ab*|=2|ab| for a|01>+b|10>, with the stated spin-flip definition. Deduct2 because a,b are from the wrong Hamiltonian and the explicit time-dependent result/derivation remains unfinished at the section cutoff.',
    excerpt(585, 593), excerpt(445, 461))
row('pure_state.CHSH', 0,
    'No maximal CHSH formula or measurement optimization is delivered anywhere in the final answer.', omission())
row('pure_state.maximal_entanglement_reachability', 0,
    'No necessary and sufficient maximal-entanglement reachability condition or exceptional branch is delivered.', omission())
row('pure_state.earliest_maximal_entanglement', 0,
    'No earliest maximal-entanglement time, equality case or unreachable-case result is delivered.', omission())
row('thermal.Gibbs_state', 0,
    'No correct normalized Gibbs matrix is delivered. The definition exp(-beta H)/Z alone earns no result credit. The only completed exponential block contains a spurious even-sector sinh coupling; the odd block stops before its expression.',
    excerpt(597), excerpt(726, 729), omission())
row('thermal.partition_function', 2,
    'Credit2 for the correct odd-sector contribution2exp(beta K)cosh(2beta r) and trace-of-exponential method. Deduct2 for the false even contribution2exp(-beta K)cosh(2beta J), which should be2exp(-beta K). At J=1,Delta=K=0 it gives4cosh(2beta), rather than2+2cosh(2beta).',
    excerpt(676, 688))
row('thermal.partial_transpose', 0,
    'The partial transpose and its four eigenvalues are entirely absent from the delivered final answer.', omission())
row('thermal.entanglement_criterion', 0,
    'No necessary and sufficient thermal entanglement criterion or equality/separability condition is delivered.', omission())
row('thermal.thermal_limits', 0,
    'Neither beta=0 nor J=Delta=0 is evaluated for the thermal state. The separate zero-coupling dynamical check does not supply a Gibbs limit.', omission())
row('checks.conventions', 0,
    'Pauli/basis declarations and a log2 formula appear, but conventions are not consistent across the delivered answer: the Delta term swaps sign in Part4, K substitutes for detuning in Part3, the even coupling changes, and no partial-transpose convention is implemented. Deduct2 for failure of the required consistency.',
    excerpt(13, 15), excerpt(386, 391), excerpt(637, 657), excerpt(568), omission())
row('checks.normalization', 2,
    'The explicit Hermiticity-to-unitarity argument correctly proves normalization of e^(-iHt)|01> and is an algebraic consistency check. This earns its limited criterion credit even though it does not catch the incompatible formulas elsewhere.',
    excerpt(735, 736))
row('checks.initial_condition', 2,
    'An explicit t=0 trigonometric coefficient substitution gives c01=1 and all other amplitudes0, consistently with the correct Part2 formula.',
    excerpt(738, 743))
row('checks.decoupled_limit', 1,
    'The J=0 diagonal energies, eigenstate phase and no-transition conclusion are correctly computed. Deduct1 because the same check misstates the oscillation formula and asserts that a zero numerator makes its zero-radius0/0 expression valid; it therefore does not validate the stated formulas on all decoupled branches.',
    excerpt(754, 767))
row('checks.nontrivial_numerical_example', 0,
    'The numerical example is not correct: its half-frequency formula and alleged maximum at pi/(2sqrt2) disagree with the actual Hamiltonian. The attempted independent matrix check is cut off before any reconciliation.',
    excerpt(770, 778), excerpt(801, 805))

counterexamples = [
    {'id': 'SC-CE-01', 'issue': 'Spurious even coupling and inconsistent spectrum/thermal trace',
     'parameters': {'J': 1, 'Delta': 0, 'K': 0, 'beta': 1},
     'actual': {'even_block': [[0, 0], [0, 0]], 'energies': [0, 0, 2, -2],
                'partition_function': '2+2cosh(2)'},
     'asserted': {'even_block': [[0, 2], [2, 0]], 'energies': [2, -2, 2, -2],
                  'partition_function': '4cosh(2)'},
     'argument': 'The two tensor products cancel on |00>,|11>. Part1 states this correctly; Part4 subsequently inserts an unretracted coupling. Since cosh(2)>1, the partition functions differ.',
     'evidence': [excerpt(207, 218), excerpt(647, 672), excerpt(684)]},
    {'id': 'SC-CE-02', 'issue': 'Partial trace retains impossible coherence',
     'parameters': {'J': 1, 'Delta': 0, 'K': 0, 't': 'pi/8'},
     'actual_state': '(|01>-i|10>)/sqrt(2)',
     'actual_reduced_state': [['1/2', '0'], ['0', '1/2']],
     'asserted_reduced_state': [['1/2', 'i/2'], ['-i/2', '1/2']],
     'actual_determinant': '1/4', 'asserted_determinant': '0',
     'argument': 'The cross terms vanish because <0|1>=0 on spin2. The asserted matrix has eigenvalues0,1, contradicting both the actual I/2 reduction and the answer own later Schmidt entropy1.',
     'evidence': [excerpt(498), excerpt(527, 537), excerpt(555, 568)]},
    {'id': 'SC-CE-03', 'issue': 'Numerical maximum uses half-frequency',
     'parameters': {'J': 1, 'Delta': 1, 'K': 0, 't': 'pi/(2sqrt(2))'},
     'actual_probability': '0', 'asserted_probability': '1/2',
     'actual_first_maximizing_time': 'pi/(4sqrt(2))',
     'argument': 'The correct sine argument2sqrt(2)t is pi, while the check section uses sqrt(2)t=pi/2. Its proposed maximum is a zero of the actual probability.',
     'evidence': [excerpt(370), excerpt(765), excerpt(776, 778)]},
    {'id': 'SC-CE-04', 'issue': 'Pure-state section changes the Hamiltonian',
     'parameters': {'J': 1, 'Delta': 1, 'K': 0},
     'actual_odd_block': [[2, 2], [2, -2]],
     'part3_odd_block': [[0, 2], [2, 0]],
     'actual_probability_supremum': '1/2', 'part3_probability_supremum': '1',
     'argument': 'Part3 drops Delta and uses K as detuning. Its entanglement time dependence therefore concerns a different problem, even where a generic pure-state identity is valid.',
     'evidence': [excerpt(254, 259), excerpt(386, 394), excerpt(574)]}
]
assert len(rows) == 25 and sum(r['points'] for r in rows) == 26
(HERE / 'criterion_assessments.json').write_text(json.dumps(
    {'run_sha256': RUN_SHA, 'answer_sha256': ANSWER_SHA,
     'criteria': rows, 'counterexamples': counterexamples},
    indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

report = '''# Section-control evaluation

The assembled final answer scores **26/100** under the unchanged 25-criterion rubric. All five headings are present, but every section is truncated and the sections retain incompatible Hamiltonians and formulas.

| Section | Points |
|---|---:|
| Spectrum | 7/20 |
| Dynamics | 7/20 |
| Pure-state entanglement | 5/25 |
| Thermal entanglement | 2/25 |
| Consistency checks | 5/10 |
| Total | **26/100** |

Credit comes from actual correct material: the corrected Part2 odd block/evolution/probability and odd eigenbasis, generic Schmidt/concurrence identities, the odd-sector thermal trace contribution, and normalization/initial-condition checks. Headings, promised results and generic definitions receive no completion credit. Contradictory results elsewhere reduce the corresponding criteria; no reconciliation was inferred.

The main concrete failures are:

- Part3 replaces Delta with K as the odd-sector detuning, then keeps coherences in the partial trace. At J=1, Delta=K=0, t=pi/8, the true first-spin state is I/2; the displayed matrix instead has determinant0 and eigenvalues0,1.
- Part4 adds a nonexistent2J coupling between |00> and |11>, contradicting Part1. For J=1, Delta=K=0, its partition function is4cosh(2beta), whereas the Hamiltonian gives2+2cosh(2beta).
- Part5 halves the correct oscillation frequency. Its J=Delta=1,K=0 time pi/(2sqrt2), claimed to attain probability1/2, actually gives probability0.
- The spectral crossings, general maximum/time branches, CHSH result, maximal-entanglement reachability/time, normalized Gibbs matrix, partial-transpose spectrum and thermal-entanglement condition are not completed.

The receipt reports five calls, each ending with `finish_reason=length` at3,200 output tokens:16,000 total output tokens. Spending was9,065 microUSD with zero held charges. A completed host receipt therefore records a completed attempt, not mathematical completeness.

The evaluator read all805 final-answer lines /37,510 Unicode characters after freeze confirmation. Only assembled `answer_text` supplied mathematical credit; nested provider evidence and individual draft payloads were not expanded. Reference provenance was frozen before current-output access, and the original rubric weights were unchanged. All25 judgments, exact quote ranges, cross-section counterexamples and hashes are retained in `criterion_evidence.json`; score/custody checks are in `evaluation_validation.json`.

This is one section-allocation attempt on one fixed problem. It does not establish a general workflow or model ranking. Previous grades, workflows and original sources are unchanged.
'''
(HERE / 'evaluation.md').write_text(report, encoding='utf-8')
print(json.dumps({'manual_criteria': len(rows), 'total': 26}))
