"""Read-only population checks; no artifact is credited as fully read by this script."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from fractions import Fraction
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
SCOPE = json.loads((REV / 'additional_governance_remaining_scope.json').read_text())
INVENTORY = {r['path']: r for r in json.loads((ROOT / 'dag/file_inventory.json').read_text())['files']}
OUTCOMES = ('killed', 'survived', 'demonstrably_equivalent', 'invalid', 'inconclusive', 'unrun')
GRADES = ('E', 'D', 'C', 'B', 'A', 'A+')
BANDS = {'ccn_max': (10, 15, 20, 50), 'cognitive_max': (15, 20, 25, 40), 'nesting_max': (3, 4, 5, 8)}
cache = {}


def strict_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate JSON key: ' + key)
        out[key] = value
    return out


def reject_constant(value):
    raise ValueError('nonfinite JSON constant: ' + value)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def target_state(name):
    if name in cache:
        return cache[name]
    rel = PurePosixPath(name.replace('\\', '/'))
    if rel.is_absolute() or '..' in rel.parts or any(':' in p for p in rel.parts):
        return {'status': 'unsafe_path_not_read'}
    if any(p.startswith('.') for p in rel.parts):
        return {'status': 'dot_path_excluded_not_read'}
    path = (ROOT / Path(*rel.parts)).resolve()
    if not path.is_relative_to(ROOT):
        return {'status': 'outside_root_not_read'}
    if not path.is_file():
        value = {'status': 'absent'}
    else:
        data = path.read_bytes()
        value = {'status': 'present', 'sha256': digest(data),
                 'lf_normalized_sha256': digest(data.replace(b'\r\n', b'\n')), 'bytes': len(data)}
    cache[name] = value
    return value


def binding(name, expected, locator):
    state = target_state(name)
    if state['status'] != 'present':
        verdict = state['status']
    elif state['sha256'] == expected:
        verdict = 'raw_match'
    elif state['lf_normalized_sha256'] == expected:
        verdict = 'lf_normalized_match_only'
    else:
        verdict = 'different_current_bytes'
    inv = INVENTORY.get(name)
    return {'locator': locator, 'path': name, 'expected_sha256': expected, 'status': verdict,
            'current_sha256': state.get('sha256'),
            'frozen_inventory_relation': ('match' if inv['sha256'] == expected else 'different') if inv else 'not_in_inventory'}


def embedded_bindings(value, where='$'):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            yield binding(value['path'], value['sha256'], where)
        for key, child in value.items():
            yield from embedded_bindings(child, where + '.' + key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from embedded_bindings(child, f'{where}[{index}]')


def expected_counts(mutants):
    counts = Counter(m['outcome'] for m in mutants)
    return {key: counts[key] for key in OUTCOMES}


def ratio(counts):
    denominator = sum(counts[k] for k in ('killed', 'survived', 'inconclusive', 'unrun'))
    return Fraction(counts['killed'], denominator) if denominator else None


def check_counts(actual, declared, label, issues):
    for key, value in actual.items():
        if declared.get(key, 0) != value:
            issues.append(f'{label}.{key}: expected {value}, recorded {declared.get(key)}')
    if 'total' in declared and declared['total'] != sum(actual.values()):
        issues.append(f'{label}.total mismatch')
    if 'conservative_ratio' in declared:
        reported = declared['conservative_ratio']
        expected = ratio(actual)
        if (expected is None and reported is not None) or (expected is not None and
                (reported is None or abs(Fraction(str(reported)) - expected) > Fraction(1, 10**9))):
            issues.append(f'{label}.ratio mismatch: {reported} vs {expected}')


def metric_band(name, value):
    if value is None:
        return 'A+'
    if type(value) is not int or value < 0:
        raise ValueError('invalid metric value')
    return next((grade for upper, grade in zip(BANDS[name], ('A+', 'B', 'C', 'D')) if value <= upper), 'E')


def score_rows(data):
    yield 'current', data['score']
    for i, record in enumerate(data.get('history', [])):
        if 'score' in record:
            yield f'history[{i}]', record['score']


results = []
for source in SCOPE['files']:
    name = source['path']
    if not name.endswith('.json'):
        continue
    raw = (ROOT / name).read_bytes()
    assert digest(raw) == source['sha256'], name
    data = json.loads(raw, object_pairs_hook=strict_pairs, parse_constant=reject_constant)
    row = {'path': name, 'sha256': source['sha256'], 'strict_json': 'pass', 'issues': [],
           'bindings': list(embedded_bindings(data)), 'checks': []}
    issues = row['issues']
    schema = data.get('schema_version')
    if schema == 'pfp.governance-baseline.v1':
        entries = data['entries']
        row['kind'] = 'grandfathered_source_manifest'
        row['entry_count'] = len(entries)
        row['reason_population'] = dict(Counter(x.get('reason', '') for x in entries.values()))
        row['bindings'].extend(binding(path, item['sha256'], '$.entries.' + path) for path, item in entries.items())
        if any(not isinstance(item.get('reason'), str) or not item['reason'].strip() for item in entries.values()):
            issues.append('blank or absent grandfathering reason')
        row['checks'] = ['All entry bindings compared; complete reason-string population counted.',
                         'Grandfathering is a declared exemption, not proof of semantics; historical list monotonicity not assessed.']
    elif schema == 'pfp.evidence-run.v1':
        row['kind'] = 'historical_command_record'
        row['metadata'] = {k: data[k] for k in ('name', 'command', 'working_directory', 'tool_versions', 'started', 'finished', 'exit_status', 'report')}
        row['input_count'] = len(data['inputs'])
        row['distinct_input_paths'] = len({x['path'] for x in data['inputs']})
        row['reported_elapsed_seconds'] = (datetime.fromisoformat(data['finished']) - datetime.fromisoformat(data['started'])).total_seconds()
        if row['reported_elapsed_seconds'] < 0:
            issues.append('negative reported duration')
        if row['input_count'] != row['distinct_input_paths']:
            issues.append('duplicate input paths')
        row['checks'] = ['All input/report digest bindings compared; command and timing metadata retained.',
                         'No command executed; record bytes do not authenticate process execution or prove the input population is complete.']
    elif schema == 'pfp.mutation-report.v1':
        row['kind'] = 'python_or_csharp_mutation_receipt'
        row['bindings'].extend(binding(path, sha, '$.targets.' + path) for path, sha in data['targets'].items())
        actual = expected_counts(data['mutants'])
        check_counts(actual, data['totals'], 'totals', issues)
        for path, declared in data['per_file'].items():
            check_counts(expected_counts([m for m in data['mutants'] if m['path'] == path]), declared, path, issues)
        keys = [(m['path'], m['index']) for m in data['mutants']]
        if len(set(keys)) != len(keys):
            issues.append('duplicate path/index mutant identifiers')
        if set(m['outcome'] for m in data['mutants']) - set(OUTCOMES):
            issues.append('unknown mutation outcome')
        row.update(mutant_count=len(data['mutants']), counts=actual, ratio=str(ratio(actual)),
                   non_killed=[m for m in data['mutants'] if m['outcome'] != 'killed'])
        row['checks'] = ['All mutation outcomes, totals, per-file counts and rational ratios checked.',
                         'Observed outcome strings are historical assertions; no mutant or test was re-executed.']
    elif schema == 'pfp.rust-mutation-report.v1':
        row['kind'] = 'rust_mutation_receipt'
        aggregate = Counter()
        for path, item in data['files'].items():
            row['bindings'].append(binding(path, item['sha256'], '$.files.' + path))
            actual = expected_counts(item['mutants'])
            check_counts(actual, item['counts'], path, issues)
            aggregate.update(actual)
        row['counts'] = dict(aggregate)
        row['mutant_count'] = sum(aggregate.values())
        row['ratio'] = str(ratio(aggregate))
        row['non_killed'] = [{'path': path, **m} for path, item in data['files'].items() for m in item['mutants'] if m['outcome'] != 'killed']
        row['checks'] = ['All per-file outcome counts and aggregate conservative ratio recomputed.',
                         'No Rust build/cargo-mutants execution or historical run authentication.']
    elif schema == 'pfp.mutation-equivalents.v1':
        row['kind'] = 'declared_equivalence_exclusions'
        row['entries'] = len(data['equivalents'])
        row['justification_population'] = dict(Counter(x['justification'] for x in data['equivalents']))
        keys = [(x['path'], x['index']) for x in data['equivalents']]
        if len(set(keys)) != len(keys):
            issues.append('duplicate equivalence identifiers')
        row['checks'] = ['All declared source bindings and repeated justification strings compared.',
                         'Written justifications require the stated observation/caller assumptions; no equivalence proof is inferred.']
    elif schema == 'pfp.contract-score.v1':
        row['kind'] = 'contract_and_policy_grade_declaration'
        row['score_summaries'] = []
        for label, score in score_rows(data):
            gates = list(score['gates'].values())
            weakest = min(gates, key=GRADES.index) if all(g in GRADES for g in gates) else None
            if score['composite_grade'] != weakest:
                issues.append(label + ': weakest gate/composite mismatch')
            if score['score_token'] != f"{score['level']}{score['composite_grade']}":
                issues.append(label + ': score token mismatch')
            if score['composite_grade'] in GRADES and GRADES.index(score['grade_ceiling']) < GRADES.index(score['composite_grade']):
                issues.append(label + ': grade exceeds ceiling')
            mutation = score.get('mutation_accounting')
            if mutation:
                check_counts({k: mutation[k] for k in OUTCOMES}, mutation, label + '.mutation_accounting', issues)
            row['score_summaries'].append({'version': label, 'token': score['score_token'], 'gates': score['gates'],
                'grade_ceiling': score['grade_ceiling'], 'is_complete': score['is_complete'],
                'level_basis': score['level_basis'], 'basis': score['basis']})
        row['checks'] = ['Current/history weakest gate, token, ceiling, mutation ratio and embedded hash predicates checked.',
                         'Narrative grade evidence is declared and not independently proved by arithmetic consistency.']
    elif all(isinstance(item, dict) and 'gate5_ceiling' in item for item in data.values()):
        row['kind'] = 'historical_metric_table'
        for path, item in data.items():
            expected = min((metric_band(k, item[k]) for k in BANDS), key=GRADES.index)
            if expected != item['gate5_ceiling']:
                issues.append(path + ': metric ceiling mismatch')
        row['metric_rows'] = len(data)
        row['ceiling_population'] = dict(Counter(item['gate5_ceiling'] for item in data.values()))
        row['checks'] = ['All retained table values mapped to the declared metric bands.',
                         'No lizard/complexipy rerun or claim that the brace heuristic is a language-complete nesting analysis.']
    else:
        raise ValueError('unhandled schema: ' + name)
    row['binding_status_counts'] = dict(Counter(x['status'] for x in row['bindings']))
    row['predicate_status'] = 'pass' if not issues else 'issues_found'
    results.append(row)

summary = {'files': len(results), 'strict_json_pass': len(results),
           'kind_counts': dict(Counter(r['kind'] for r in results)),
           'declared_arithmetic_or_structure_issues': sum(len(r['issues']) for r in results),
           'binding_population': dict(Counter(b['status'] for r in results for b in r['bindings'])),
           'unique_current_paths_examined': len(cache)}
out = {'source_commit': SCOPE['source_commit'], 'summary': summary, 'files': results,
       'limits': ['These are whole-population predicates, not full-body semantic reading credits.',
                  'LF-only matches are not raw byte matches; current drift is not evidence that a historical command failed.',
                  'No original commands, mutation campaigns, external paths, dot paths, private benchmark or provider calls were executed.']}
(REV / 'additional_governance_artifact_checks.json').write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(summary))
for row in results:
    print(json.dumps({k: row[k] for k in ('path', 'kind', 'issues', 'binding_status_counts')}, ensure_ascii=False))
