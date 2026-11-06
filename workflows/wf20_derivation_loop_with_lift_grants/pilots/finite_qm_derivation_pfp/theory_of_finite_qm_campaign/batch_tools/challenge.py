"""P4 challenge: coordinate mutants plus task-specific semantic near misses, decided by the node's own checker.

Coordinate mutants perturb one leaf, drop a list tail or delete a key of the candidate data. They
catch sloppy checkers but say little about the mathematics. A *semantic* near miss changes the
candidate so that it stays well formed and plausible yet breaks a stated premise: a counterexample
to the unpaid bridge, a wrong carrier, an off-by-gauge value, a swapped convention. Such mutants
are node specific, so they come from a hook the researcher writes next to the checker:

    # <run>/semantic_mutants.py  (copied from the node spec)
    def semantic_mutants(data, profile):      # every one must be REJECTED by check_candidate
        return [{'id': 'swap_basis', 'rationale': 'why a reviewer would believe it', 'mutate': fn}]
    def semantic_controls(data, profile):     # optional; every one must be ACCEPTED
        return [{'id': 'relabel_rows', 'rationale': 'valid change next to the near miss', 'mutate': fn}]

`mutate(data)` edits a deep copy in place. A mutant that leaves the data unchanged is an error.
At least one semantic mutant is required unless the run records a written waiver.
"""
from __future__ import annotations

import copy
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_json, load_module, load_yaml, require, save, sha, yaml_new  # noqa: E402
from stages import IDENTITY, Batch  # noqa: E402

MIN_WAIVER_CHARS = 40


def _walk(value, path=()):
    if isinstance(value, dict):
        for key in value:
            yield from _walk(value[key], path + (key,))
    elif isinstance(value, list):
        for position, item in enumerate(value):
            yield from _walk(item, path + (position,))
    else:
        yield path, value


def _get(data, path):
    for step in path:
        data = data[step]
    return data


def perturbed(value):
    if isinstance(value, bool):
        return not value
    if isinstance(value, int):
        return value + 1
    if value is None:
        return 0
    if isinstance(value, str):
        try:
            fraction = Fraction(value)
            if str(fraction) == value:
                return str(fraction + 1)
        except (ValueError, ZeroDivisionError):
            pass
        return value + '~'
    return None


def coordinate_mutants(data, ignore=(), limit=None):
    """Deterministic one-edit mutants of the candidate data: leaf change, list tail drop, key deletion."""
    ignored = {tuple(p) if isinstance(p, list) else p for p in ignore}
    found = []
    for path, value in _walk(data):
        label = '/'.join(map(str, path)) or '(root)'
        if label in ignored:
            continue
        new = perturbed(value)
        if new is not None:
            def mutate(d, path=path, new=new):
                _get(d, path[:-1])[path[-1]] = new
            found.append(('coordinate_' + label, mutate))
    containers = [((), data)] + [(p, v) for p, v in _containers(data)]
    for path, value in containers:
        label = '/'.join(map(str, path)) or '(root)'
        if isinstance(value, list) and value:
            found.append(('drop_last_' + label, lambda d, path=path: _get(d, path).pop()))
        elif isinstance(value, dict):
            for key in value:
                key_label = label + '/' + str(key)
                if key_label not in ignored:
                    found.append(('delete_' + key_label, lambda d, path=path, key=key: _get(d, path).pop(key)))
    return found[:limit] if limit else found


def _containers(value, path=()):
    if isinstance(value, dict):
        for key in value:
            if isinstance(value[key], (dict, list)):
                yield path + (key,), value[key]
                yield from _containers(value[key], path + (key,))
    elif isinstance(value, list):
        for position, item in enumerate(value):
            if isinstance(item, (dict, list)):
                yield path + (position,), item
                yield from _containers(item, path + (position,))


def load_semantic(run, data, profile):
    path = run / 'semantic_mutants.py'
    if not path.is_file():
        return [], []
    module = load_module('semantic_' + sha(path)[:12], path)
    near = list(module.semantic_mutants(copy.deepcopy(data), profile)) if hasattr(module, 'semantic_mutants') else []
    controls = list(module.semantic_controls(copy.deepcopy(data), profile)) if hasattr(module, 'semantic_controls') else []
    for item in near + controls:
        require(isinstance(item, dict) and item.get('id') and callable(item.get('mutate')) and item.get('rationale'),
                'Semantic mutant needs id, rationale and mutate')
    ids = [i['id'] for i in near + controls]
    require(len(ids) == len(set(ids)), 'Duplicate semantic mutant ids')
    return near, controls


def p4(batch: Batch, task, *, attempt='p1', host_checkpoint='p2', controls=None, waive_semantic=None):
    ctx = batch.ctx
    run = batch.run(task)
    profile = load_json(run / 'p0/profile.json')
    plan = profile.get('challenge', {})
    candidate = load_json(run / attempt / 'candidate.json')
    checker = load_module('checker_' + task.replace('-', '_') + '_p4', run / 'check_candidate.py')
    request = ctx.prepare.build_packet(ctx.root / batch.row(task)['prompt'], 'P4_CHALLENGE', attempt_id='p4',
                                       reviewed_path=run / 'p0/reviewed_missions.json', review_path=run / 'p0/host_review.json',
                                       candidate_path=run / attempt / 'candidate.json', host_check_path=run / host_checkpoint / 'host_check.json')
    save(run / 'p4/request.json', request)
    accepted = checker.check(run / attempt / 'request.json', run / attempt / 'candidate.json')
    near, semantic_controls = load_semantic(run, candidate['data'], profile)
    waiver = waive_semantic or plan.get('semantic_waiver')
    require(near or (waiver and len(waiver.strip()) >= MIN_WAIVER_CHARS),
            'A semantic near-miss hook (semantic_mutants.py) is required, or a written waiver of at least %d characters' % MIN_WAIVER_CHARS)
    mutants = [('coordinate', name, mutate, 'single-edit structural mutant') for name, mutate in
               coordinate_mutants(candidate['data'], plan.get('ignore_paths', []), plan.get('max_coordinate_mutants'))]
    mutants += [('semantic', 'semantic_' + item['id'], item['mutate'], item['rationale']) for item in near]
    results = []
    for kind, name, mutate, why in mutants:
        bad = copy.deepcopy(candidate)
        mutate(bad['data'])
        require(bad['data'] != candidate['data'], 'No-op mutant: ' + name)
        path = run / 'p4/mutants' / (name.replace('/', '__') + '.json')
        save(path, bad)
        try:
            checker.check(run / attempt / 'request.json', path)
        except ValueError as error:
            reason = str(error)
        else:
            raise ValueError('Counterfeit accepted: ' + name)
        results.append({'id': name, 'kind': kind, 'rationale': why, 'path': path.relative_to(run).as_posix(), 'rejected': True, 'reason': reason})
    control_results = []
    for item in semantic_controls:
        good = copy.deepcopy(candidate)
        item['mutate'](good['data'])
        path = run / 'p4/controls' / (item['id'] + '.json')
        save(path, good)
        try:
            outcome = checker.check(run / attempt / 'request.json', path)
        except ValueError as error:
            raise ValueError('Valid semantic control rejected: %s (%s)' % (item['id'], error))
        control_results.append({'id': item['id'], 'rationale': item['rationale'], 'path': path.relative_to(run).as_posix(), 'accepted': True,
                                'changed': good['data'] != candidate['data']})
    delta = load_yaml(run / attempt / 'operad_delta.yaml')
    delta['counterexamples'] += list(controls or [])
    delta['counterexamples'] += [{'id': r['id'], 'kind': 'semantic_near_miss', 'rationale': r['rationale'], 'rejected_by': 'check_candidate'}
                                 for r in results if r['kind'] == 'semantic']
    counts = {'coordinate': sum(r['kind'] == 'coordinate' for r in results), 'semantic': sum(r['kind'] == 'semantic' for r in results),
              'semantic_controls': len(control_results)}
    response = {**{k: request[k] for k in IDENTITY}, 'near_miss': results, 'valid_semantic_controls': control_results,
                'challenged_predicate': profile['independent_predicates'], 'valid_control': accepted,
                'challenge_result': 'The same independent checker evaluated all saved mutations and the original valid candidate.',
                'mutant_counts': counts, 'semantic_waiver': waiver if not near else None, 'operad_delta': delta}
    save(run / 'p4/candidate.json', response)
    save(run / 'p4/raw_response.json', response)
    yaml_new(run / 'p4/operad_delta.yaml', delta)
    save(run / 'p4/host_check.json', {**{k: request[k] for k in IDENTITY}, 'candidate_sha256': sha(run / 'p4/candidate.json'),
                                      'status': 'survives_executed_challenges',
                                      'predicate_results': {'mutants': results, 'valid_control': accepted, 'counterexamples': list(controls or []),
                                                            'valid_semantic_controls': control_results, 'mutant_counts': counts,
                                                            'semantic_waiver': waiver if not near else None,
                                                            'ignored_paths': list(plan.get('ignore_paths', []))},
                                      'bounded_failure_codes': [], 'operad_delta': delta})
    return counts


def run_node(batch: Batch, task, *, attempt=None, waive_semantic=None, controls=None, **p2_options):
    """P2 (unless retained), P4 and P5 for one node; stops with the actual failure retained."""
    from stages import p2, p5
    run = batch.run(task)
    if (run / 'p5/candidate.json').exists():
        return {'task': task, 'skipped': 'p5 exists'}
    attempts = load_json(run / 'attempts.json')
    chosen = next(a for a in attempts if a['attempt'] == attempt) if attempt else attempts[-1]
    name, checkpoint = chosen['attempt'], chosen['checkpoint']
    if (run / checkpoint / 'host_check.json').exists():
        host = load_json(run / checkpoint / 'host_check.json')
    else:
        host = p2(batch, task, attempt=name, checkpoint=checkpoint, **p2_options)
    if host['status'] != 'accepted_candidate_for_challenge':
        raise ValueError('Actual failure retained; repair required: ' + task)
    counts = p4(batch, task, attempt=name, host_checkpoint=checkpoint, controls=controls, waive_semantic=waive_semantic)
    history = ['p0']
    for entry in attempts:
        history.append(entry['attempt'])
        if (run / entry['checkpoint'] / 'host_check.json').exists():
            history.append(entry['checkpoint'])
    history.append('p4')
    p5(batch, task, attempt=name, host_checkpoint=checkpoint, attempts=history)
    failed = [p.parent.name for p in sorted(run.glob('p2*/host_check.json'))
              if load_json(p)['status'] == 'repairable_candidate_defect']
    save(run / 'accepted.json', {'attempt': name, 'host': checkpoint, 'failed_checkpoints': failed, 'mutant_counts': counts})
    return {'task': task, 'accepted_attempt': name, 'mutant_counts': counts}
