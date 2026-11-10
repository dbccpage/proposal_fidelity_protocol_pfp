"""Execute only reviewed miniature teaching snippets with standard-library inputs."""
import ast
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
P = 'education/009_oeeis/curriculum/520_eis_levels/concepts/'
pins = {r['path']: r['sha256'] for r in json.loads((REV / 'additional_eis_pciv_education_remaining_scope.json').read_text())['files']}


def snippet(name):
    path = P + name
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pins[path]
    blocks = re.findall(r'```python\s*\n(.*?)\n```', raw.decode('utf-8'), flags=re.S)
    assert len(blocks) == 1
    return path, blocks[0]


results = []
path, code = snippet('lesson_520_01_component_role_partitioning.md')
ns = {'dataclass': dataclass}
exec(compile(ast.parse(code), path, 'exec'), ns)
value = ns['AntiSkillSpecV2'](status='ADMITTED', runtime_enforcement=True)
assert value.status == 'ADMITTED' and value.runtime_enforcement
results.append({'path': path, 'sha256': pins[path], 'control': 'Override both dataclass defaults',
                'result': {'status': value.status, 'runtime_enforcement': value.runtime_enforcement},
                'meaning': 'Frozen prevents ordinary reassignment; it does not restrict constructor arguments to the defaults.'})

path, code = snippet('lesson_520_04_learned_guard_two_signal_activation.md')
ns = {'TwoSignalCollapseError': type('SyntheticCollapseError', (Exception,), {})}
exec(compile(ast.parse(code), path, 'exec'), ns)
signal1 = True
copied_signal2 = signal1
assert ns['evaluate_activation'](signal1, copied_signal2) == 'ACTIVATED'
results.append({'path': path, 'sha256': pins[path], 'control': 'Copy true signal1 into signal2',
                'result': 'ACTIVATED', 'meaning': 'Boolean conjunction cannot inspect source provenance or establish signal independence.'})

path, code = snippet('lesson_520_05_independent_observation_support_policy.md')
ns = {}
exec(compile(ast.parse(code), path, 'exec'), ns)
observations = [SimpleNamespace(correlation_key=k, host_event='same-event', observed_value=True) for k in ('A', 'B', 'C')]
assert ns['calculate_support'](observations) == 3
results.append({'path': path, 'sha256': pins[path], 'control': 'Three labels on one shared host event',
                'result': 3, 'meaning': 'Key cardinality establishes only the declared partition count, not causal separation or pairwise statistical decorrelation.'})

path, code = snippet('lesson_520_07_clonal_selection_and_affinity.md')
ns = {'hits': 1, 'total_probes': 3}
exec(compile(ast.parse(code), path, 'exec'), ns)
floating = float(ns['affinity'])
assert isinstance(floating, float)
results.append({'path': path, 'sha256': pins[path], 'control': 'Convert the computed Fraction to float',
                'result': floating, 'meaning': 'Fraction construction and a type assertion do not prohibit later float conversion; that rule needs an explicit boundary check.'})

path, code = snippet('lesson_520_09_external_admission_boundary.md')
ns = {'dataclass': dataclass}
exec(compile(ast.parse(code), path, 'exec'), ns)
value = ns['HumanAntiSkillAdmissionDecisionV1'](rule_byte_hash='', human_signature='', scope='anything')
assert value.human_signature == ''
results.append({'path': path, 'sha256': pins[path], 'control': 'Construct with empty hash/signature',
                'result': {'rule_byte_hash': value.rule_byte_hash, 'human_signature': value.human_signature},
                'meaning': 'String fields and frozen status do not verify a signature, an expected rule digest, or an external authorization decision.'})

out = {'status': 'complete_bounded_teaching_snippet_controls', 'controls': results,
       'limits': ['These are literal lesson snippets with required standard-library imports or a synthetic exception supplied. No runtime package or production detector/gate was imported.',
                  'Counterexamples limit the snippets and their adjacent teaching claims; they are not claims that the real runtime has the same bypass.',
                  'No provider, original file mutation, native build or private benchmark access.']}
(REV / 'additional_eis_pciv_education_lesson_checks.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'controls': len(results), 'status': out['status']}))
