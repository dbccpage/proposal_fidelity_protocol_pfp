"""Offline counterexamples and bounded checks for the education audit.

Reads only named public teaching sources; outputs stay under this prefix.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews'
BUILD = OUT / 'additional_education_build'
BUILD.mkdir(exist_ok=True)
(BUILD / 'pytest.ini').write_text('[pytest]\n', encoding='utf8')
sys.dont_write_bytecode = True


def module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


e = module('education_audit_eis', 'education/009_oeeis/code/eis_core.py')
p = module('education_audit_pciv', 'education/010_oepciv/code/prompt_civilization_core.py')
cases = []

ab = e.Antibody(1, 'syntax error', 0.7)
mutant = e.ClonalSelectionEngine().somatic_hypermutation(ab, 'line')
cases.append({'id': 'EDU-P01', 'observation': 'Educational clonal mutation uses a float boost',
              'parent': ab.affinity_threshold, 'child': mutant.affinity_threshold,
              'type': type(mutant.affinity_threshold).__name__})
cases.append({'id': 'EDU-P02', 'observation': 'Support accepts any three distinct caller strings',
              'accepted': e.SupportPolicy().check_consensus([('alias1', True), ('alias2', True), ('alias3', True)])})
class ExplodingThymus:
    def test_negative_selection(self, *args):
        raise AssertionError('thymus was invoked')
boundary = e.ExternalAdmissionBoundary(e.InnateBarrier(), ExplodingThymus())
accepted, receipt = boundary.filter_antigen(e.Antigen(2, '2+2=5', ('mathematical truth',), 'untrusted'))
cases.append({'id': 'EDU-P03', 'observation': 'Educational external admission never calls its thymus or authenticates an operator',
              'accepted': accepted, 'receipt': receipt,
              'scope': 'This proves only keyword/size-screen acceptance, not production EIS admission or a declared arithmetic check.'})
ind = p.Individual(1, 0, p.Genotype(1, 'keep this prompt', 1, 3), p.Phenotype(10.0, 100, 0.8, ''), ())
adapted = p.LamarckianEngine().retro_inherit(ind)
cases.append({'id': 'EDU-P04', 'observation': 'Empty reflection preserves genotype but manufactures improved phenotype without an evaluation',
              'same_genotype': adapted.genotype == ind.genotype,
              'old_score': ind.phenotype.correctness_score, 'new_score': adapted.phenotype.correctness_score,
              'old_latency': ind.phenotype.latency_ms, 'new_latency': adapted.phenotype.latency_ms})
log = p.PromptCivilizationEventLog()
log.append_event('one', {'v': 1})
log.append_event('two', {'v': 2})
retained_head = log.last_hash
log.events.pop()
cases.append({'id': 'EDU-P05', 'observation': 'Removing the last event passes integrity although retained head disagrees',
              'integrity': log.verify_integrity(), 'head_matches': log.events[-1]['hash'] == retained_head})
ecology = p.IslandEcology(['A'], capacity_per_island=1)
ecology.populate('A', ind)
ecology.populate('A', adapted)
cases.append({'id': 'EDU-P06', 'observation': 'Educational island capacity is stored but not enforced',
              'capacity': ecology.capacity, 'population': len(ecology.islands['A'])})
# A single primitive of degree 1 satisfies a_d <= 2*(1/2)^d.
# At z=3/2 the stated |z|<1/M holds, but sum_{k>=0} z^k diverges.
cases.append({'id': 'EDU-P07', 'observation': 'Chapter07 analytic bound needs M>=1 or |z|<min(1,1/M)',
              'primitive_counts': {'degree1': 1, 'all_other_degrees': 0},
              'C': 2, 'M': '1/2', 'z': '3/2', 'claimed_radius_condition_holds': True,
              'series_terms_tend_to_zero': False,
              'scope': 'Exact counterexample to the stated analytic region, not to the formal Euler product.'})
validation = []
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'
env['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
for folder, test in [('education/009_oeeis/code', 'test_eis_levels.py'),
                     ('education/010_oepciv/code', 'test_prompt_civilization_levels.py')]:
    test_env = env.copy()
    test_env['PYTHONPATH'] = str(ROOT / folder)
    cmd = [str(ROOT / '.venv/Scripts/python.exe'), '-B', '-X', 'utf8', str(OUT / 'additional_education_pytest_bootstrap.py'),
           str(ROOT / folder / 'tests' / test), '-q', '-p', 'no:cacheprovider',
           '-c', str(BUILD / 'pytest.ini'), '--rootdir', str(BUILD),
           '--import-mode=importlib', '--noconftest',
           '--confcutdir', str(ROOT / folder)]
    run = subprocess.run(cmd, cwd=BUILD, env=test_env, capture_output=True, text=True,
                         encoding='utf8', timeout=120)
    validation.append({'kind': 'existing_tests', 'command': cmd, 'exit_code': run.returncode,
                       'working_directory': str(BUILD),
                       'stdout': run.stdout, 'stderr': run.stderr,
                       'scope': 'Teaching companion tests only; no model calls or production evidence.'})
lean = Path(os.environ['USERPROFILE']) / '.elan/bin/lean.exe'
for folder, name in [('education/009_oeeis/lean4', 'EpistemicImmuneSystem'),
                     ('education/010_oepciv/lean4', 'PromptCivilization')]:
    source = ROOT / folder / (name + '.lean')
    target = BUILD / source.name
    shutil.copyfile(source, target)
    cmd = [str(lean), '+leanprover/lean4:v4.35.0', '-o', str(BUILD / (name+'.olean')), str(target)]
    run = subprocess.run(cmd, cwd=BUILD, env=env, capture_output=True, text=True,
                         encoding='utf8', timeout=60)
    validation.append({'kind': 'isolated_lean_elaboration', 'source': source.relative_to(ROOT).as_posix(),
                       'command': cmd, 'exit_code': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr,
                       'scope': 'Exact copied source elaboration with installed Lean4.35.0, not a package build or semantic correctness of comments.'})
result = {'source_commit': '8050c66900899771766f33e8f5fdd200b7dd9120',
          'cases': cases, 'validation': validation, 'no_provider_calls': True}
previous_results = OUT / 'additional_education_probe_results.json'
if previous_results.exists():
    result['preflight_failures'] = json.loads(previous_results.read_text(encoding='utf8')).get('preflight_failures', [])
else:
    result['preflight_failures'] = []
(OUT / 'additional_education_probe_results.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
print(json.dumps(result, indent=2))
