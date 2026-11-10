"""Persist the completed stochastic-map source review while awaiting grading freeze."""
import hashlib
import json
from pathlib import Path
import runpy
from fractions import Fraction as F

HERE = Path(__file__).resolve().parent
PREFIX = 'additional_rust_quantum_probability_remaining'
notes_path = HERE / (PREFIX + '_notes.json')
notes = json.loads(notes_path.read_text())
notes['15'] = {
    'assessment': 'Full 1380-line owner read across the preserved 1-1095 checkpoint and new 1096-1380 residual. Private finite nonempty row-stochastic maps admit exact normalized rows (77-118), typed composition and pushforward (274-339), bounded powers (345-377), tensor products and deterministic structural maps (133-272,379-402), pullback (295-309), exact Dobrushin coefficient (487-505), and Bayesian inverse (513-539). Copy/discard laws have explicit finite tests (1096-1136); exact stochastic mixtures do not commute with copying a random output. Bayesian disintegration replays p_i M_ij=q_j K_ji on a positive prior example (1183-1200), and refuses zero target mass (1204-1210). Dobrushin tests cover specified rational grids and attaining point masses (1216-1280). Identity/power/shape/label and round-trip tests are concrete assertions, not broad empirical evidence.',
    'limitations': [
        'No native execution. Test source was fully read; no fresh Rust pass or mutation-kill count is claimed.',
        'Rational constructor admission still lacks an explicit denominator-nonzero check before sign/comparison/summation, as described in RQPR-F006.',
        'Bayesian inversion is prior-relative. Reversing it again requires positive recovered source masses; the positive-prior test is not a universal matrix inverse theorem.',
        'The source computes exact finite Dobrushin and composition objects. It does not establish that empirical observations follow these kernels or supply physical preparation/measurement semantics.',
        'Checked cardinality products and an exponent limit do not bound dense allocation or arbitrary-precision bit growth. The separate BoundaryRecord scaffold at 573-657 does not enforce an actual matrix computation budget.',
        'Probability copy is correlated diagonal duplication; independent tensor draws differ for non-Dirac rows. This is a classical algebraic distinction, not a derived quantum no-cloning theorem.'
    ]
}
notes_path.write_text(json.dumps(notes, indent=2) + '\n')
runpy.run_path(str(HERE / (PREFIX + '_checkpoint.py')))
report_path = HERE / (PREFIX + '.json')
report = json.loads(report_path.read_text())
path = 'code/rust/core_finite_probability/src/stochastic_map.rs'
source_sha = '45c54eed58392bd5a0e255f505e7605a4b3e5a5a50dba8e9ab17f36eaad1b9eb'
ev = lambda a, b: {'path': path, 'sha256': source_sha, 'lines': [a, b]}
claim = {
    'id': 'RQPR-C011',
    'claim': 'Finite rational row-stochastic maps implement typed composition, tensor, copy/discard, exact pushforward/pullback, prior-relative Bayesian disintegration, and the sharp total-variation Dobrushin coefficient. These are useful finite transport mechanisms under admitted carrier and probability premises.',
    'evidence': [ev(77, 118), ev(274, 402), ev(487, 539), ev(1096, 1136), ev(1183, 1280)],
    'dependencies': ['Finite nonempty carriers and well-defined rational masses',
                     'Nonnegative rows summing to one',
                     'Strictly positive target marginal for the requested Bayesian posterior'],
    'limitations': ['No native replay or empirical kernel adequacy established.',
                    'The Dobrushin theorem follows from decomposing p-q into equal-mass positive and negative parts and bounding differences of convex combinations of rows; source tests cover only selected finite grids.',
                    'Copy commutation characterizes deterministic rows because diag(p)=p tensor p forces every off-diagonal p_i p_j to vanish. The finite test does not itself prove all carrier sizes.',
                    'Inverse disintegration is not an unconditional inverse of the original stochastic matrix.']
}
report['claims'] = [c for c in report['claims'] if c['id'] != claim['id']] + [claim]
report['partial_source_reviews'] = [r for r in report.get('partial_source_reviews', []) if r['path'] != path]
report['audit_state'] = 'source_review_continues_while_awaiting_section_control_freeze'

# Independent exact, small, mathematical controls; do not import or execute Rust.
m = [[F(1, 2), F(1, 2)], [F(0), F(1)]]
p = [F(1, 2), F(1, 2)]
q = [sum(p[i] * m[i][j] for i in range(2)) for j in range(2)]
k = [[p[i] * m[i][j] / q[j] for i in range(2)] for j in range(2)]
assert q == [F(1, 4), F(3, 4)]
assert k == [[F(1), F(0)], [F(1, 3), F(2, 3)]]
assert all(p[i] * m[i][j] == q[j] * k[j][i] for i in range(2) for j in range(2))
delta = max(sum(abs(m[i][j] - m[l][j]) for j in range(2)) / 2
            for i in range(2) for l in range(2))
assert delta == F(1, 2)
copied = [[F(1, 2), F(0)], [F(0), F(1, 2)]]
independent = [[F(1, 4)] * 2 for _ in range(2)]
assert copied != independent
control = {'method': 'Independent exact Python Fraction reconstruction, not original Rust execution',
           'source_sha256': source_sha,
           'controls': [
               {'id': 'RQPR-STOCH-01', 'passed': True, 'claim': 'Prior-relative Bayes identity',
                'kernel': [[str(x) for x in row] for row in m], 'prior': list(map(str, p)),
                'target': list(map(str, q)), 'posterior': [[str(x) for x in row] for row in k]},
               {'id': 'RQPR-STOCH-02', 'passed': True, 'claim': 'Two-row Dobrushin coefficient attained by distinct Dirac inputs', 'coefficient': str(delta)},
               {'id': 'RQPR-STOCH-03', 'passed': True, 'claim': 'Copying a fair random output differs from two independent draws',
                'copied': [[str(x) for x in row] for row in copied], 'independent': [[str(x) for x in row] for row in independent]}]}
control_path = HERE / (PREFIX + '_stochastic_controls.json')
control_path.write_text(json.dumps(control, indent=2) + '\n')
report['validation'] = [v for v in report['validation'] if v.get('id') != 'RQPR-STOCH-CONTROLS']
report['validation'].append({'id': 'RQPR-STOCH-CONTROLS', 'path': str(control_path.relative_to(HERE.parents[1])).replace('\\', '/'),
                             'sha256': hashlib.sha256(control_path.read_bytes()).hexdigest(),
                             'controls': 3, 'passed': True, 'native_execution': False})
report_path.write_text(json.dumps(report, indent=2) + '\n')
md = HERE / (PREFIX + '.md')
with md.open('a', encoding='utf-8') as f:
    f.write('\n\n## Stochastic-map residual completed while awaiting section-control grading\n\n'
            'Coverage is now 27/51 full source bodies, with 24 files pending. The remaining 285 lines of stochastic_map.rs were fully read; the entire 1,380-line owner now has a complete reading receipt. '
            'The new claim RQPR-C011 distinguishes finite stochastic composition, copy/discard, Dobrushin contraction and prior-relative Bayes disintegration from empirical or physical adequacy. '
            'Three independent exact Fraction controls pass; no Rust code was executed. Original findings and sources remain unchanged.\n')
print(json.dumps({'full': report['full_source_read_count'], 'remaining': len(report['remaining_work']),
                  'claims': len(report['claims']), 'report_sha256': hashlib.sha256(report_path.read_bytes()).hexdigest()}))
