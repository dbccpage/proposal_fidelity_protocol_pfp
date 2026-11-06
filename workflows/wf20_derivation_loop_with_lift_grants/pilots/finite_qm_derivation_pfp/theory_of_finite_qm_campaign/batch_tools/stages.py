"""File-based PFP stage engine shared by every batch (P0 mission/P1/P2/P3/P5).

This is bookkeeping and host verification, not a provider runner or a theorem oracle. A node's
mathematics lives in its spec: a reviewed profile, an operad delta, an independent checker
(check_candidate.py), a wire formatter and the candidate data. P4 is in challenge.py.
Retained attempts are never overwritten; a failed gate stays on disk and a repair is a new attempt.
"""
from __future__ import annotations

import copy
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (BOILERPLATE_NEXT_TEST, Ctx, check_lean_version, cargo_target_guard, disk_precheck, find_tool,  # noqa: E402
                    json_bytes, lean_environment, lean_toolchain, load_json, load_module, load_yaml, native_record,
                    replace_bytes, require, save, sha, yaml_bytes, yaml_new)

IDENTITY = ('task_id', 'stage_id', 'attempt_id', 'input_sha256')
PROFILE_KEYS = ('source_review_status', 'source_scope_review', 'independent_predicates', 'claim_boundary', 'carrier',
                'coefficient_ring', 'production_sources', 'build_sources', 'challenge_plan', 'composition_tree',
                'anchors', 'checker_id', 'result_or_obstruction', 'next_mathematical_step', 'report', 'construction',
                'p2_gates')
BOUNDARY_KEYS = ('supports', 'does_not_support', 'narrowest_claim', 'next_test')
DELTA_KEYS = ('add_or_refine_generators', 'add_or_refine_relations', 'checked_compositions', 'failed_compositions',
              'counterexamples', 'open_obligations')
PYTHON_TESTS = r'Ran (\d+) tests?[\s\S]*\bOK\b'
CARGO_TESTS = r'test result: ok\. (\d+) passed; 0 failed'
PYTEST_TESTS = r'(\d+) passed'
AXIOM_REPORT = re.compile(r"'([^']+)' (?:depends on axioms:\s*\[([^\]]*)\]|does not depend on any axioms)")
STANDARD_AXIOMS = {'propext', 'Classical.choice', 'Quot.sound'}
GATE_NEEDS = (None, 'cargo', 'lean')


class Batch:
    def __init__(self, ctx: Ctx, directory):
        self.ctx = ctx
        self.dir = Path(directory)
        self.selection = load_json(self.dir / 'selection.json')
        self.rows = self.selection['nodes']

    def row(self, task):
        return next(r for r in self.rows if r['node_id'] == task)

    def run(self, task) -> Path:
        return self.ctx.root / self.row(task)['run']

    def tasks(self):
        return [r['node_id'] for r in self.rows]

    def policy(self):
        return load_json(self.dir / 'execution_policy.json')

    def pin(self, path):
        path = Path(path)
        return {'path': self.ctx.rel(path), 'sha256': sha(path)}

    def snapshots(self, names, folder):
        pins = []
        for name in names:
            target = Path(folder) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.ctx.root / name, target)
            pins.append(self.pin(target))
        return pins


# --------------------------------------------------------------------------- P0
def p0_request(batch: Batch, task, external_roots=None):
    """File-only P0 request plus a byte-custody inventory of every source the collection pins."""
    ctx, row = batch.ctx, batch.row(task)
    run = batch.run(task)
    collection = load_yaml(ctx.root / row['operad_collection'])
    save(run / 'p0/request.json', ctx.prepare.build_packet(ctx.root / row['prompt'], attempt_id='p0'))
    custody = ctx.custody()
    sources = [('this_repository', row['prompt'], None), ('this_repository', row['operad_collection'], None)]
    sources += [(b.get('repository', 'this_repository'), b['path'], b.get('sha256')) for b in collection['source_bindings'] if b.get('path')]
    sources += [('this_repository', p['path'], p['sha256']) for p in collection['target'].get('paper_source_pins', [])]
    records, seen = [], set()
    for repository, relative, expected in sources:
        if (repository, relative) in seen:
            continue
        seen.add((repository, relative))
        base = ctx.root if repository == 'this_repository' else (external_roots or {}).get(repository)
        actual = Path(base) / relative if base else None
        record = {'repository': repository, 'source_path': relative, 'recorded_sha256': expected,
                  'available': bool(actual and actual.is_file())}
        if record['available']:
            record['actual_sha256'] = sha(actual)
            record['matches_recorded_pin'] = expected is None or expected == record['actual_sha256']
            if expected and not record['matches_recorded_pin']:
                resolved = False
                if custody is not None:
                    try:
                        resolved = custody.matches('paper', relative, expected, task)
                    except ValueError:
                        resolved = False
                require(resolved, 'Unresolved source pin ' + relative + ' (regenerate the prompt or record a successor)')
                record['pin_resolution'] = 'Explicit filename-custody migration; original expected digest retained'
                record['custody_ledger_sha256'] = sha(ctx.root / 'dag/pfp/filename_custody.json')
            snapshot = run / 'inputs' / repository / relative
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(actual, snapshot)
            record['snapshot'] = ctx.rel(snapshot)
        records.append(record)
    save(run / 'p0/source_inventory.json', {'task_id': task, 'source_records': records, 'boundary': (
        'Availability and byte custody only; declaration and mathematical scope still require substantive mining.')})
    return {'task': task, 'sources': len(records), 'missing': sum(not r['available'] for r in records)}


def validate_spec(profile, delta):
    missing = [k for k in PROFILE_KEYS if k not in profile]
    require(not missing, 'Profile lacks: ' + ', '.join(missing))
    require(profile['source_review_status'] == 'semantics_reviewed_for_selected_step', 'Semantic review required')
    require(all(k in profile['claim_boundary'] for k in BOUNDARY_KEYS), 'claim_boundary needs ' + ', '.join(BOUNDARY_KEYS))
    boundary = profile['claim_boundary']
    require(len(boundary['next_test'].strip()) >= 30 and not BOILERPLATE_NEXT_TEST.match(boundary['next_test'])
            and boundary['next_test'].strip() != boundary['does_not_support'].strip(),
            'next_test must name this node\'s own unpaid obligation, not boilerplate')
    require(profile['p2_gates'] and all(g.get('needs') in GATE_NEEDS and g.get('id') and g.get('argv') for g in profile['p2_gates']),
            'p2_gates need id, argv and needs in (None, cargo, lean)')
    missing = [k for k in DELTA_KEYS if k not in delta]
    require(not missing, 'Operad delta lacks: ' + ', '.join(missing))
    require(profile['source_scope_review'] and profile['independent_predicates'] and delta['add_or_refine_generators']
            and delta['add_or_refine_relations'], 'Incomplete four missions')
    # The same graft rule validate_prompts applies after P5: the outer slot colour must equal the inner output colour.
    generators = {g['id']: g for g in delta['add_or_refine_generators']}
    require(len(generators) == len(delta['add_or_refine_generators']), 'Duplicate generator ids')
    for composition in delta['checked_compositions']:
        outer, inner = generators.get(composition['outer_operation']), generators.get(composition['inner_operation'])
        require(outer is not None and inner is not None, 'Composition names an unknown generator: %s o %s' % (composition['outer_operation'], composition['inner_operation']))
        slot = composition['input_slot']
        require(type(slot) is int and 0 <= slot < len(outer['ordered_inputs']), 'Invalid graft slot in %s o %s' % (outer['id'], inner['id']))
        require(outer['ordered_inputs'][slot] == inner['output'],
                'Graft colour mismatch: %s slot %d takes %s but %s outputs %s' % (outer['id'], slot, outer['ordered_inputs'][slot], inner['id'], inner['output']))


def p0_missions(batch: Batch, task, spec, spec_dir=None):
    """Reviewed missions, host review and P0 response from a node spec (profile, public_input, delta, files)."""
    ctx, row, prepare = batch.ctx, batch.row(task), batch.ctx.prepare
    run = batch.run(task)
    profile, public, delta = spec['profile'], spec['public_input'], copy.deepcopy(spec['operad_delta'])
    validate_spec(profile, delta)
    base = Path(spec_dir or batch.dir / 'specs')
    for name, target in (('checker', 'check_candidate.py'), ('format', 'format_certificate.py'), ('semantic_mutants', 'semantic_mutants.py')):
        if spec.get(name):
            source = base / spec[name]
            require(source.is_file(), 'Spec file missing: ' + str(source))
            (run / target).parent.mkdir(parents=True, exist_ok=True)
            if not (run / target).exists():
                shutil.copyfile(source, run / target)
    checker, wire = run / 'check_candidate.py', run / 'format_certificate.py'
    require(checker.is_file() and wire.is_file(), 'Checker/complete wire format unavailable')
    original = load_yaml(ctx.root / row['operad_collection'])['target']['source_statement']
    inventory = load_json(run / 'p0/source_inventory.json')
    extra = run / 'p0/additional_source_inventory.json'
    if extra.exists():
        inventory['source_records'] += load_json(extra)['source_records']
    sources = [{'path': r['snapshot'], 'sha256': r['actual_sha256']} for r in inventory['source_records'] if r['available']]
    sources += batch.snapshots([p for p in profile['production_sources'] if not p.endswith('.lean')], run / 'p0/operation_sources')
    exact = ctx.root / 'dag/pfp/exact_json.py'
    sources += [batch.pin(checker), batch.pin(exact), batch.pin(wire)]
    for generator in delta['add_or_refine_generators']:
        generator.setdefault('source_pins', copy.deepcopy(sources))
        generator.setdefault('evidence_status', 'Source semantics reviewed; actual native and candidate kernel acceptance remain P2 gates.')
    for relation in delta['add_or_refine_relations']:
        relation.setdefault('source_pins', copy.deepcopy(sources))
    collection = load_yaml(ctx.root / row['operad_collection'])
    slots = {
        prepare.SLOTS[0]: {'mining_status': 'FILLED', 'carrier': profile['carrier'], 'coefficient_ring': profile['coefficient_ring'],
                           'source_pins': sources, 'public_input': public, 'original_target': original,
                           'source_scope_review': profile['source_scope_review'],
                           'admitted_assumptions': collection['target']['declared_assumptions']},
        prepare.SLOTS[1]: {'mining_status': 'FILLED', 'operations': [
            {'catalog_id': g['id'], 'inputs': g['ordered_inputs'], 'output': g['output'], 'semantic_predicate': g['semantic_predicate']}
            for g in delta['add_or_refine_generators']], 'composition_plan': delta['checked_compositions'], 'tree': profile['composition_tree']},
        prepare.SLOTS[2]: {'mining_status': 'FILLED', 'algebraic_relations': delta['add_or_refine_relations'],
                           'rejection_predicates': profile['independent_predicates'], 'negative_control_plan': profile['challenge_plan']},
        prepare.SLOTS[3]: {'mining_status': 'FILLED', 'certificate_predicates': profile['independent_predicates'],
                           'anchors': profile['anchors'], 'unpaid_imports': delta['open_obligations'],
                           'anchor_status': 'New Lean anchors are candidate declarations until the retained P2 compiler runs; compiled source leads retain their literal scope.'}}
    catalog = {'entries': [{'id': g['id'], 'inputs': g['ordered_inputs'], 'output': g['output'], 'semantic_predicate': g['semantic_predicate']}
                           for g in delta['add_or_refine_generators']]}
    schema = {'type': 'object', 'required': ['schema_id', 'task_id', 'stage_id', 'attempt_id', 'input_sha256', 'source_pins', 'data'],
              'properties': {k: {'type': 'string'} for k in ('schema_id', 'task_id', 'stage_id', 'attempt_id', 'input_sha256')}}
    schema['properties'].update({'source_pins': {'type': 'array', 'items': {'type': 'object'}}, 'data': {'type': 'object'}})
    reviewed = {'original_target': original, 'work_unit': {
        'schema_id': 'omega.pfp.finite-qm-work-unit.v1', 'task_id': task, 'objective': original,
        'selected_catalog_ids': [g['id'] for g in delta['add_or_refine_generators']], 'operad_slots': slots,
        'answer_schema': schema, 'checker_id': profile['checker_id']}, 'catalog': catalog}
    save(run / 'p0/profile.json', profile)
    save(run / 'public_input.json', public)
    save(run / 'p0/reviewed_missions.json', reviewed)
    reviewer = spec.get('reviewer') or batch.policy().get('researcher', 'one local researcher')
    save(run / 'p0/host_review.json', {
        'task_id': task, 'review_status': 'accepted_for_next_step', 'reviewed_sha256': sha(run / 'p0/reviewed_missions.json'),
        'checker_pins': [batch.pin(checker), batch.pin(exact)], 'reviewer': reviewer + ', source and typed-contract review. No independent reviewer at this stage.',
        'boundary': 'Prerequisites reviewed; no theorem acceptance from FILLED or source status labels.'})
    request = load_json(run / 'p0/request.json')
    binding = {k: request[k] for k in IDENTITY}
    response = {**binding, 'status': 'ready_for_host_review', 'mission_patch': slots, 'source_checks': inventory['source_records'],
                'next_missing_dependency': 'Actual candidate construction and independent/native/kernel P2 execution',
                'operad_delta': delta, 'claim_boundary': profile['claim_boundary'],
                'execution': 'Serialized local researcher artifact, not a provider transcript.'}
    save(run / 'p0/candidate.json', response)
    save(run / 'p0/raw_response.json', response)
    yaml_new(run / 'p0/operad_delta.yaml', delta)
    save(run / 'p0/host_check.json', {**binding, 'candidate_sha256': sha(run / 'p0/candidate.json'), 'status': 'reviewed_for_next_step',
                                      'predicate_results': {'source_scope_review': profile['source_scope_review'], 'reviewed_sha256': sha(run / 'p0/reviewed_missions.json')},
                                      'bounded_failure_codes': [], 'operad_delta': delta, 'claim_boundary': profile['claim_boundary']})
    return run


# --------------------------------------------------------------------------- P1 / P3
def _reviewed(run):
    return {'reviewed_path': run / 'p0/reviewed_missions.json', 'review_path': run / 'p0/host_review.json'}


def begin_p1(batch: Batch, task):
    run = batch.run(task)
    request = batch.ctx.prepare.build_packet(batch.ctx.root / batch.row(task)['prompt'], 'P1_DERIVE', attempt_id='p1', **_reviewed(run))
    save(run / 'p1/request.json', request)
    return request


def p3_request(batch: Batch, task, attempt, *, from_attempt='p1', from_checkpoint='p2'):
    """Bounded-failure repair packet. Authorised only by a repairable host check on the original bytes."""
    run = batch.run(task)
    packet = batch.ctx.prepare.build_packet(batch.ctx.root / batch.row(task)['prompt'], 'P3_REPAIR', attempt_id=attempt,
                                            candidate_path=run / from_attempt / 'candidate.json',
                                            host_check_path=run / from_checkpoint / 'host_check.json', **_reviewed(run))
    save(run / attempt / 'request.json', packet)
    return packet


def submit_candidate(batch: Batch, task, data, public_tsv=None, *, attempt='p1', source_names=None):
    """Seal one candidate: request (P1 built here, P3 prepared earlier), construction snapshots, delta, response."""
    run = batch.run(task)
    profile = load_json(run / 'p0/profile.json')
    stage = 'P1_DERIVE' if attempt == 'p1' else 'P3_REPAIR'
    if (run / attempt / 'request.json').exists():
        request = load_json(run / attempt / 'request.json')
        require(request['stage_id'] == stage, 'Attempt %s holds a %s request' % (attempt, request['stage_id']))
    else:
        require(attempt == 'p1', 'A repair attempt needs p3_request first')
        request = batch.ctx.prepare.build_packet(batch.ctx.root / batch.row(task)['prompt'], 'P1_DERIVE', attempt_id='p1', **_reviewed(run))
        save(run / 'p1/request.json', request)
    names = list(dict.fromkeys(source_names or (profile['production_sources'] + profile['build_sources'])))
    candidate = {'schema_id': 'finite-qm.domain-certificate.v1', **{k: request[k] for k in IDENTITY},
                 'source_pins': batch.snapshots(names, run / attempt / 'construction'), 'data': data}
    save(run / attempt / 'candidate.json', candidate)
    delta = load_yaml(run / 'p0/operad_delta.yaml')
    response = {**{k: request[k] for k in IDENTITY}, 'candidate_certificate': candidate, 'construction': profile['construction'],
                'remaining_obligations': delta['open_obligations'], 'operad_delta': delta, 'claim_boundary': profile['claim_boundary'],
                'execution': 'Actual local exact producer output; no external provider dispatched.'}
    save(run / attempt / 'response.json', response)
    save(run / attempt / 'raw_response.json', response)
    yaml_new(run / attempt / 'operad_delta.yaml', delta)
    if public_tsv is not None and not (run / 'public_input.tsv').exists():
        (run / 'public_input.tsv').write_bytes(public_tsv.encode('utf-8'))
    attempts = run / 'attempts.json'
    history = load_json(attempts) if attempts.exists() else []
    history.append({'attempt': attempt, 'stage_id': stage, 'checkpoint': 'p2' if attempt == 'p1' else 'p2_after_' + attempt})
    attempts.write_bytes(json_bytes(history))
    return candidate


# --------------------------------------------------------------------------- P2
def _tokens(batch, run, attempt):
    ctx = batch.ctx
    mapping = {'python': sys.executable, 'root': str(ctx.root), 'run': str(run), 'attempt': attempt,
               'candidate': str(run / attempt / 'candidate.json'), 'request': str(run / attempt / 'request.json')}
    for name in ('cargo', 'lean'):
        mapping[name] = None
    return mapping


def _expand(argument, mapping, ctx):
    for key in ('cargo', 'lean'):
        if '{%s}' % key in argument:
            mapping[key] = mapping[key] or find_tool(key)
    for key, value in mapping.items():
        if value is not None:
            argument = argument.replace('{%s}' % key, value)
    return argument


def _count(pattern, text):
    match = re.search(pattern, text)
    return int(match.group(1)) if match else None


def p2(batch: Batch, task, attempt='p1', checkpoint=None, *, min_free_gb=20.0, max_target_gb=6.0, cargo_target=None, max_path_chars=40):
    """Host verification of the original candidate bytes by independent, declared native predicates."""
    ctx = batch.ctx
    run = batch.run(task)
    profile = load_json(run / 'p0/profile.json')
    checkpoint = checkpoint or ('p2' if attempt == 'p1' else 'p2_after_' + attempt)
    candidate = load_json(run / attempt / 'candidate.json')
    working = []
    for pin in candidate['source_pins']:
        source = ctx.root / pin['path'].split('/' + attempt + '/construction/', 1)[1]
        require(sha(source) == pin['sha256'], 'Working source differs from submitted bytes')
        working.append(source)
    digest = sha(run / attempt / 'candidate.json')
    binding = {'task_id': task, 'stage_id': 'P2_VERIFY', 'attempt_id': checkpoint, 'input_sha256': digest}
    folder = run / checkpoint
    gates = [{'id': 'certificate', 'argv': ['{python}', '-X', 'utf8', '{run}/check_candidate.py', '{request}', '{candidate}'],
              'cwd': '.', 'needs': None, 'pins': ['check_candidate.py']}] + list(profile['p2_gates'])
    save(folder / 'request.json', {**binding, 'candidate': '../' + attempt + '/candidate.json',
                                   'host_action': 'Actual independent predicates and native execution, no acceptance by label.'})
    save(folder / 'candidate.json', {'candidate_sha256': digest})
    mapping = _tokens(batch, run, attempt)
    env, guard = {}, None
    receipts = {}
    for gate in gates:
        needs = gate.get('needs')
        gate_env = dict(env)
        if needs == 'cargo':
            if guard is None:
                guard = cargo_target_guard(cargo_target, min_free_gb=min_free_gb, max_target_gb=max_target_gb, max_path_chars=max_path_chars)
                save(folder / 'native/cargo_guard.json', guard['report'])
            gate_env.update(guard['env'])
        elif needs == 'lean':
            disk_precheck(ctx.root, 1.0, 'Lean compile')
            gate_env.update(lean_environment(ctx))
            if 'lean_version' not in receipts:
                receipts['lean_version'] = native_record(folder / 'native', 'lean_version', [find_tool('lean'), '--version'], cwd=ctx.root / 'lean4',
                                                         env=lean_environment(ctx), tool_sources=[Path(__file__)])
        argv = [_expand(a, mapping, ctx) for a in gate['argv']]
        stdin = (run / gate['stdin_file']).read_bytes() if gate.get('stdin_file') else None
        extra = [run / p for p in gate.get('pins', [])]
        if gate['id'] == 'certificate':
            extra += [ctx.root / 'dag/pfp/exact_json.py']
        receipts[gate['id']] = native_record(folder / 'native', gate['id'], argv, cwd=ctx.root / gate.get('cwd', '.'), sources=working + extra,
                                             stdin=stdin, env=gate_env, tool_sources=[Path(__file__)])
        print('{"node": "%s", "gate": "%s", "exit_code": %d, "seconds": %s}' % (task, gate['id'], receipts[gate['id']]['exit_code'], receipts[gate['id']]['seconds']), flush=True)
    checks = profile.get('p2_checks', {})
    lean_ok = True
    version = None
    if 'lean_version' in receipts:
        reported = (folder / 'native/lean_version.stdout.log').read_text(encoding='utf-8', errors='replace')
        version = {'expected': lean_toolchain(ctx), 'reported': reported.strip(), 'matches': check_lean_version(ctx, reported)}
        lean_ok = version['matches']
    if checks.get('lean'):
        text = (folder / 'native' / (checks['lean']['gate'] + '.stdout.log')).read_text(encoding='utf-8', errors='replace')
        expected = set(checks['lean']['anchors'])
        reports = [(n, a) for n, a in AXIOM_REPORT.findall(text) if n in expected]
        lean_ok = lean_ok and len(reports) == len(expected) and {n for n, _ in reports} == expected and \
            all({x.strip() for x in a.split(',') if x.strip()} <= STANDARD_AXIOMS for _, a in reports) and 'sorryAx' not in text
    cross = True
    if checks.get('wire'):
        module = load_module('wire_' + task.replace('-', '_') + '_' + checkpoint, run / checks['wire'].get('module', 'format_certificate.py'))
        lines = (folder / 'native' / (checks['wire']['gate'] + '.stdout.log')).read_text(encoding='utf-8').splitlines()
        cross = lines == module.lines(candidate['data'])
    counts, tests_ok = {}, True
    for name, test in checks.get('tests', {}).items():
        stream = (folder / 'native' / (test['gate'] + '.' + test.get('stream', 'stdout') + '.log')).read_text(encoding='utf-8', errors='replace')
        counts[name] = _count(test.get('pattern') or PYTHON_TESTS, stream)
        tests_ok = tests_ok and bool(counts[name])
    ok = all(r['exit_code'] == 0 for r in receipts.values()) and lean_ok and cross and tests_ok
    delta = load_yaml(run / attempt / 'operad_delta.yaml')
    codes = [] if ok else (['G5_SCOPE'] if (not lean_ok or any(r['exit_code'] for g, r in receipts.items() if g.startswith('lean'))) else ['G3_WITNESS'])
    result = {**binding, 'candidate_sha256': digest, 'status': 'accepted_candidate_for_challenge' if ok else 'repairable_candidate_defect',
              'checker_pins': [batch.pin(run / 'check_candidate.py'), batch.pin(ctx.root / 'dag/pfp/exact_json.py')],
              'predicate_results': {'native_exit_codes': {k: v['exit_code'] for k, v in receipts.items()},
                                    'required_named_Lean_reports': lean_ok, 'lean_version': version,
                                    'exact_cross_language_full_output': cross, 'nonempty_test_coverage': tests_ok,
                                    'test_counts': counts, 'cargo_guard': guard['report'] if guard else None,
                                    'scope': profile['claim_boundary']},
              'bounded_failure_codes': codes, 'operad_delta': delta}
    save(folder / 'host_check.json', result)
    save(folder / 'raw_response.json', result)
    yaml_new(folder / 'operad_delta.yaml', delta)
    save(run / attempt / 'host_check.json', {**{k: candidate[k] for k in IDENTITY}, 'candidate_sha256': digest,
                                              'status': 'see_host_checkpoint', 'host_check': '../' + checkpoint + '/host_check.json'})
    return result


# --------------------------------------------------------------------------- P5
def p5(batch: Batch, task, *, attempt='p1', host_checkpoint='p2', attempts=None):
    """Record the supported result or obstruction, update the canonical collection and the index row."""
    ctx = batch.ctx
    run, row = batch.run(task), batch.row(task)
    profile = load_json(run / 'p0/profile.json')
    delta = load_yaml(run / 'p4/operad_delta.yaml')
    candidate = load_json(run / attempt / 'candidate.json')
    host = load_json(run / host_checkpoint / 'host_check.json')
    require(host['status'] == 'accepted_candidate_for_challenge', 'Missing accepted host result')
    host_ref = ctx.rel(run / host_checkpoint / 'host_check.json')
    for generator in delta['add_or_refine_generators']:
        generator['evidence_status'] = 'Target-specific native predicates checked on retained inputs; relation-specific kernel scope is separate. General refined-carrier operad instantiation remains open.'
        generator['latest_host_check'] = host_ref
    for relation in delta['add_or_refine_relations']:
        relation['latest_host_check'] = host_ref
        if relation['id'] in profile.get('relation_evidence', {}):
            relation['evidence_status'] = profile['relation_evidence'][relation['id']]
    attempts = attempts or ['p0', 'p1', 'p2', 'p4']
    binding = {'task_id': task, 'stage_id': 'P5_RECORD', 'attempt_id': 'p5', 'input_sha256': sha(run / 'p4/host_check.json')}
    save(run / 'p5/request.json', {**binding, 'host_result': '../' + host_checkpoint + '/host_check.json', 'challenge': '../p4/host_check.json'})
    policy = batch.policy()
    result = {**binding, 'result_or_obstruction': profile['result_or_obstruction'], 'attempt_refs': attempts,
              'source_bindings': candidate['source_pins'], 'remaining_obligations': delta['open_obligations'], 'operad_delta': delta,
              'next_mathematical_step': profile['next_mathematical_step'], 'claim_boundary': profile['claim_boundary'],
              'status': 'recorded_pending_batch_review',
              'execution_accounting': {'external_provider_calls': policy.get('external_provider_calls', 0), 'chat_cost': 'unmeasured',
                                       'researcher': policy.get('researcher', 'one local researcher') + ', independent native predicates'}}
    save(run / 'p5/candidate.json', result)
    save(run / 'p5/raw_response.json', result)
    yaml_new(run / 'p5/operad_delta.yaml', delta)
    save(run / 'p5/host_check.json', {**binding, 'candidate_sha256': sha(run / 'p5/candidate.json'),
                                      'status': 'scoped_result_or_obstruction_recorded_pending_batch_review',
                                      'predicate_results': host['predicate_results'], 'bounded_failure_codes': [],
                                      'claim_boundary': profile['claim_boundary']})
    path = ctx.root / row['operad_collection']
    collection = load_yaml(path)
    generators = delta['add_or_refine_generators']
    colours = sorted({g['output'] for g in generators} | {c for g in generators for c in g['ordered_inputs']})
    meanings = profile.get('colour_meanings', {})
    collection['presentation'] = {
        'status': 'scoped_stage_result_pending_batch_review', 'scope': profile['claim_boundary']['narrowest_claim'],
        'colours': [{'id': c, 'meaning': meanings.get(c, 'Scoped semantic carrier with the declared hypotheses.')} for c in colours],
        'generators': generators, 'relations': delta['add_or_refine_relations'], 'compositions': delta['checked_compositions'],
        'identities': [{'colour': c, 'proposed_operation': 'id_' + c, 'signature': c + ' -> ' + c,
                        'status': 'Semantic identity; generic function-substitution laws do not instantiate these refined carriers in Lean.'} for c in colours],
        'symmetric_actions': [], 'coherence_obligations': delta['open_obligations'],
        'failed_compositions': delta['failed_compositions'], 'counterexamples': delta['counterexamples']}
    reviewed = load_json(run / 'p0/reviewed_missions.json')
    collection['operad_slots'] = reviewed['work_unit']['operad_slots']
    collection['operad_slots_scope'] = {'work_unit': ctx.rel(run / 'p0/reviewed_missions.json'),
                                        'scope': 'FILLED means reviewed prerequisites for this selected step; original target and unpaid imports retained.'}
    collection['open_obligations'] = delta['open_obligations']
    collection['latest_run'] = {'path': ctx.rel(run), 'stage': 'P5_RECORD', 'status': 'scoped_result_or_obstruction_pending_batch_review'}
    collection['stage_history'] = [{'stage': load_json(run / a / 'request.json')['stage_id'], 'attempt': a, 'run': ctx.rel(run),
                                    'operad_delta': ctx.rel(run / a / 'operad_delta.yaml'), 'host_check': ctx.rel(run / a / 'host_check.json')}
                                   for a in attempts + ['p5']]
    collection.setdefault('scope_notes', []).append(profile['source_scope_review'])
    replace_bytes(path, yaml_bytes(collection))
    index = load_json(ctx.index_path)
    node = next(n for n in index['nodes'] if n['node_id'] == task)
    node.update({'current_stage': 'P5_RECORD', 'ready_for_derivation': False, 'latest_run': ctx.rel(run),
                 'status': 'scoped_result_or_obstruction_pending_batch_review'})
    replace_bytes(ctx.index_path, json_bytes(index))
    (run / 'README.md').write_bytes((profile['report'] + '\n\nEvery executed checkpoint retains an operad delta, source/candidate bindings and actual host results. '
                                     'This is local file-based PFP execution, not an external-provider transcript. No whole-repository or hosted-CI success is claimed. '
                                     'Awaiting the requested batch review. AuthorityEffect: None.\n').encode('utf-8'))
    return {'node': task, 'stage': 'P5_RECORD', 'generators': len(generators), 'relations': len(delta['add_or_refine_relations'])}
