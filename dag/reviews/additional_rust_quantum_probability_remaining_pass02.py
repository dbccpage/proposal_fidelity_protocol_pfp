"""Durable synthesis of the newly completed finite-probability owners; no native execution."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
R = H.parents[1]
P = 'additional_rust_quantum_probability_remaining'
scope = json.loads((H / (P + '_scope.json')).read_text())['files']
path = H / (P + '.json')
report = json.loads(path.read_text())


def ev(index, first, last):
    source = scope[index]
    assert hashlib.sha256((R / source['path']).read_bytes()).hexdigest() == source['sha256']
    return {'path': source['path'], 'sha256': source['sha256'], 'lines': [first, last]}


claims = [
    ('RQPR-C005', 'Classical instruments enforce normalized nonnegative outcome maps, distinguish adaptive from nonadaptive continuation, and recompute the nonadaptive forgetting law. Conditional boxes separately test no-signalling and supplied local hidden-variable tables; PR support refutation does not infer quantum realizability.',
     [ev(1, 125, 178), ev(1, 249, 337), ev(1, 475, 640), ev(1, 720, 812)],
     ['Admitted finite carriers and valid rational encodings', 'Exact finite sums/products', 'LHV nonnegative normalized deterministic mixture model'],
     ['Support compatibility is only a necessary LHV condition unless weights are supplied and replayed.', 'Source tests inspected, not newly executed; no physical/model-selection certificate.']),
    ('RQPR-C006', 'The marginal owner implements pairwise overlap consistency and a standard-form minimax L1 repair reduction, not global-joint existence. The sampling bound is explicitly conditional on iid categorical trials; cross-context union bounding needs no independence.',
     [ev(10, 136, 175), ev(10, 187, 303), ev(10, 329, 362)],
     ['Nonnegative LP variables imposed by caller/solver', 'Caller separately verifies primal feasibility and optimum', 'iid trials within each context for sampling interpretation'],
     ['unpack validates local probability vectors only; it is not an LP or compatibility checker.', 'Local section enumeration budget does not bound dense LP work or rational bit complexity.']),
    ('RQPR-C007', 'Signed representations remain distinct from probability states. Negative indicator values obstruct stochastic representations preserving that readout; coarsening can erase that obstruction. Exact block-sum descent and nonnegative quotient transitions are checked before producing a classical forgetting map.',
     [ev(13, 64, 180), ev(13, 183, 324)],
     ['Finite signed rational masses with positive total', 'Declared surjective report partition', 'Readout-preservation premise for obstruction'],
     ['Public bound records are forgeable data, not authenticated proof objects.', 'Only a literal Ok/Err inline test is present; no semantic test replay.']),
    ('RQPR-C008', 'Prime-log normal forms provide exact equality for rational entropies through unique factorization; sign decisions use rational enclosures and may refuse at finite precision. These are exact finite arithmetic objects in nats, with explicit factorization and precision limits.',
     [ev(8, 1, 29), ev(8, 127, 299), ev(8, 315, 420)],
     ['Correct delegated primality/factorization', 'Correct elementary log interval bounds', 'Rational independence of logarithms of distinct primes'],
     ['No general symbolic transcendental decision procedure.', 'Per-integer factorization budgets and external precision caps do not bound arbitrary input length/bit size.', 'No new native test or dependency replay.']),
    ('RQPR-C009', 'Exact sorted prefix sums decide finite majorization, including incomparability. The HLP constructor produces a finite sequence of two-coordinate stochastic mixes with a decreasing unmatched-coordinate measure. The LOCC helper only decides the correctly oriented Nielsen spectrum criterion.',
     [ev(9, 84, 213), ev(9, 247, 407), ev(9, 744, 832)],
     ['Valid normalized rational distributions', 'Sorted/padded carrier convention', 'External pure bipartite-state and LOCC premises for physical interpretation'],
     ['No implementation or experimental verification of LOCC.', 'Dense maps and exact rational sizes remain caller resource concerns.']),
    ('RQPR-C010', 'Finite Markov structure is computed from exact positive support; stationary distributions are normalized and replayed after exact solves. Absorption/hitting systems and bounded TV mixing calculations are conditional finite-chain computations, not evidence that observations obey a Markov model.',
     [ev(11, 153, 310), ev(11, 372, 466), ev(11, 529, 631), ev(11, 695, 843)],
     ['Admitted square row-stochastic map', 'Correct exact linear algebra', 'Finite homogeneous Markov-chain interpretation'],
     ['No native replay; matrix dimension/bit-size are not bounded by the 1024 step cap.', 'Mixing-time implementation searches positive steps only.', 'Zero-step carrier admission gap is separately recorded.']),
]
for identifier, claim, evidence, dependencies, limitations in claims:
    item = {'id': identifier, 'claim': claim, 'evidence': evidence,
            'dependencies': dependencies, 'limitations': limitations}
    report['claims'] = [x for x in report['claims'] if x['id'] != identifier] + [item]

dependency = Path('C:/Users/a343o/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f/num-rational-0.4.2/src/lib.rs')
dependency_hash = hashlib.sha256(dependency.read_bytes()).hexdigest()
assert dependency_hash == '6ce781e573521fb81f5ca47c1e6dab64e4eafc7f7d8e85094161fca5bb39c015'
findings = [
    {'id': 'RQPR-F005', 'severity': 'medium', 'title': 'Public second marginal helper panics on ragged input',
     'finding': 'second_marginal takes a raw slice of rows, obtains width from the first row, then indexes every row at each column without shape validation. The two-row input [[1],[]] reaches row[0] on the empty second row. This violates the crate-level no-caller-data-panic aspiration; private instrument admission does not protect this separate public helper.',
     'evidence': [ev(1, 340, 346)], 'recommended_action': 'Accept a validated joint-table carrier or return a typed rectangularity error before indexing.',
     'validation': 'Complete source-path counterexample; no native execution.'},
    {'id': 'RQPR-F006', 'severity': 'medium', 'title': 'Several rational admission boundaries panic before rejecting raw zero denominators',
     'finding': 'Rational is a public BigRational alias and admits new_raw(1,0). ProbabilityVector::try_new sees is_negative=false then sums this value; num-rational addition divides by the zero denominator or reduces it with an explicit panic. ClassicalInstrument compares it to zero and num-rational Ord reaches division by zero. SignedValuation sums before any validity check. These APIs return Result but do not make malformed rational input a typed refusal. The simplex/marginal owners demonstrate a stronger explicit denominator gate.',
     'evidence': [ev(9, 93, 112), ev(1, 140, 146), ev(13, 69, 78), ev(10, 136, 147)],
     'dependency_evidence': {'path': str(dependency), 'sha256': dependency_hash,
                             'reviewed_lines': [[70, 90], [125, 190], [335, 400], [475, 505], [1025, 1060]],
                             'context': 'Partial dependency source review only; Cargo.lock pins num-rational 0.4.2, and core_number_theory/src/rational.rs:26 is the alias.'},
     'recommended_action': 'Validate positive/nonzero denominator and canonicalize where appropriate before sign, comparison, sum or quotient operations at every public rational boundary.',
     'validation': 'Source-level derivation using the locally pinned dependency; no compiled Rust or native failure execution.'},
    {'id': 'RQPR-F007', 'severity': 'medium', 'title': 'Zero-step Markov evolution bypasses the chain carrier check',
     'finding': 'distribution_after clones initial and validates its dimension only by calling step in the loop. For steps=0, a two-state chain returns a three-state ProbabilitySimplex unchanged, while steps=1 rejects that same input. The declared output law p P^steps is therefore not on the chain carrier for this admitted branch.',
     'evidence': [ev(11, 345, 368), ev(11, 1094, 1114)],
     'recommended_action': 'Validate initial.n against self.n before the zero-step branch; add a mismatched-carrier zero-step regression.',
     'validation': 'Exact control-flow substitution; existing source test covers only a matching zero-step carrier. No native replay.'},
]
for item in findings:
    report['findings'] = [x for x in report['findings'] if x['id'] != item['id']] + [item]
path.write_text(json.dumps(report, indent=2) + '\n')
summary = [f"# Quantum/probability/Majorana audit — in progress", '',
           f"{report['full_source_read_count']} of {report['scope_count']} frozen files fully reviewed; {len(report['remaining_work'])} remain. Sources remain unchanged. No native/provider execution.", '',
           'New finite-probability owners distinguish exact instrument composition, no-signalling, local models, overlap compatibility, conditional sampling bounds, signed report quotients, prime-log identities, majorization, and finite Markov inference. Their physical/model-selection premises remain explicit.', '',
           'New defects: unchecked ragged public marginals; raw zero-denominator rational admission before arithmetic; zero-step Markov evolution accepting the wrong carrier. Existing measurement and McNemar findings are preserved. The report retains per-file complete reading receipts, exact pins, dependencies and execution limits.']
(H / (P + '.md')).write_text('\n'.join(summary) + '\n', encoding='utf-8')
print(json.dumps({'full': report['full_source_read_count'], 'pending': len(report['remaining_work']),
                  'claims': len(report['claims']), 'findings': len(report['findings'])}))
