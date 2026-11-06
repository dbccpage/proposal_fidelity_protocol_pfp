"""Select the cohort of the Fable-versus-swarm comparison and write cohort.json.

    python -I -X utf8 dag/pfp/compare/build_cohort.py [--base origin/main] [--controls 6] [--print]

Read-only: it reads git objects and the run folders already on disk. It calls no provider and runs no verifier; the Arm F
outcomes it records are what the receipts and validation records on disk say, with anything missing marked.

Selection rule (frozen in protocol.md, section 2):
  D  every run folder under dag/results/*/runs/ (other than _ladder runs) whose provenance names an expensive model:
     a Co-Authored-By trailer (Fable, Opus) on a commit that added it, or a model field inside the folder
     (budget.json, model_access.json). Runs are grouped by node: one prompt = one DAG node.
  P  every node whose _ladder runs contain an attempt by claude-opus-5-5 or claude-fable-5-1 (paired by construction: the
     stored request is replayed byte for byte to the swarm).
  C  controls: for each D prompt, the never-run prompt of the same family nearest in operation+relation candidates.
Everything else is listed under excluded_candidates with the reason. Nothing is chosen by outcome.

AuthorityEffect: None.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from compare_common import (COHORT, COHORT_SCHEMA_ID, DEFAULT_MAX_CALLS, DEFAULT_WALLCLOCK_S, LEAN_VERSION, PROTOCOL, REPO,  # noqa: E402
                            STANDARD_AXIOMS, CompareError, git, git_show, json_bytes, packet_bytes_sha256, protocol_sha256,
                            sha256_bytes)

EXPENSIVE = ('claude-opus-5-5', 'claude-fable-5-1')
FABLE_OUT_USD_PER_MTOK = 50.0   # llm_ladder/config.py PRICES[('anthropic', 'claude-fable-5-1')]
BYTES_PER_TOKEN = 3.5           # llm_ladder/packets.py estimate_tokens
TRAILER = re.compile(r'Co-Authored-By:\s*Claude\s+(\w+)\s+([\d.]+)', re.I)
AUTHORED_EXT = ('.lean', '.py', '.rs', '.md', '.json', '.yaml')
NOT_AUTHORED = ('.doc.yaml', '.contract.score.yaml', 'raw_response.json', 'manifest.json', 'accepted_modules.json')


# --------------------------------------------------------------------------- git history, one pass
def history(base: str) -> dict:
    """run folder (dag/results/N/runs/R) -> commits that ADDED files in it, oldest first."""
    raw = git('log', base, '--diff-filter=A', '--name-only', '--no-renames',
              '--format=%x1e%H%x1f%P%x1f%an%x1f%cI%x1f%s%x1f%B%x1d', '--', 'dag/results')
    runs = collections.defaultdict(dict)
    for record in raw.split('\x1e'):
        if '\x1d' not in record:
            continue
        head, names = record.split('\x1d', 1)
        commit, parents, author, when, subject, body = head.split('\x1f', 5)
        models = sorted({m[0].capitalize() + ' ' + m[1] for m in TRAILER.findall(body)})
        info = {'commit': commit, 'parents': parents.split(), 'author': author, 'date': when, 'subject': subject, 'trailers': models}
        for name in names.split('\n'):
            match = re.match(r'(dag/results/[^/]+/runs/[^/]+)/', name.strip())
            if match:
                runs[match.group(1)].setdefault(commit, info)
    return {run: sorted(commits.values(), key=lambda c: c['date']) for run, commits in runs.items()}


def in_folder_model(run_dir: Path):
    models = set()
    budget = run_dir / 'budget.json'
    if budget.is_file():
        try:
            for call in json.loads(budget.read_bytes().decode('utf-8')).get('calls', []):
                if call.get('model'):
                    models.add(call['model'])
        except (ValueError, OSError):
            pass
    access = run_dir / 'model_access.json'
    if access.is_file():
        try:
            line = json.loads(access.read_bytes().decode('utf-8').splitlines()[0])
            if line.get('id'):
                models.add(line['id'])
        except (ValueError, OSError, IndexError):
            pass
    return sorted(models)


def classify(run_rel: str, commits: list) -> dict:
    folder = REPO / run_rel
    in_models = in_folder_model(folder)
    trailers = sorted({t for c in commits for t in c['trailers']})
    category = 'unknown'
    names = ' '.join(in_models + trailers).lower()
    if 'fable' in names:
        category = 'fable'
    elif 'opus' in names:
        category = 'opus'
    elif 'sonnet' in names:
        category = 'sonnet'
    elif commits and not trailers:
        category = 'no_trailer'
    return {'category': category, 'in_folder_models': in_models, 'commit_trailers': trailers,
            'first_commit': commits[0]['commit'] if commits else None, 'commits': [c['commit'] for c in commits]}


# --------------------------------------------------------------------------- Arm F units from disk
def load_json(path: Path):
    try:
        return json.loads(path.read_bytes().decode('utf-8'))
    except (OSError, ValueError):
        return None


def toolchain_of(receipt: dict):
    argv = receipt.get('argv') or []
    first = argv[0] if isinstance(argv, list) and argv else ''
    match = re.search(r'v(\d+\.\d+\.\d+)', str(first))
    return match.group(1) if match else None


def lean_units(run_rel: str, repo_toolchain: str | None) -> list:
    folder = REPO / run_rel
    accepted = load_json(folder / 'accepted_modules.json') or {}
    kernel = load_json(folder / 'verification' / 'kernel_axioms.json') or {}
    per_source = collections.defaultdict(list)
    for row in kernel.get('printed_receipts', []):
        per_source[row.get('source')].append(row.get('axioms') or [])
    units = []
    for module, receipt_id in accepted.items():
        receipt_path = folder / 'verification' / receipt_id / 'receipt.json'
        receipt = load_json(receipt_path)
        axioms = per_source.get(module, [])
        profiles = collections.Counter('[' + ', '.join(a) + ']' for a in axioms)
        standard = bool(axioms) and all(set(a) <= set(STANDARD_AXIOMS) for a in axioms)
        exit_code = receipt.get('exit_code') if receipt else None
        verdict = 'not_recorded'
        if receipt is not None:
            verdict = 'accepted' if exit_code == 0 and standard else ('rejected' if exit_code not in (0, None) or (axioms and not standard) else 'incomplete_receipt')
        tool = toolchain_of(receipt) if receipt else None
        units.append({'unit_id': '%s::%s' % (run_rel.rsplit('/', 1)[-1], module), 'class': 'L', 'kind': 'lean_module', 'module': module,
                      'run_path': run_rel + '/' + module, 'lean4_copy': 'lean4/' + module if (REPO / 'lean4' / module).is_file() else None,
                      'receipt': (run_rel + '/verification/%s/receipt.json' % receipt_id) if receipt else None,
                      'exit_code': exit_code, 'axiom_receipts': len(axioms), 'axiom_profiles': dict(sorted(profiles.items())),
                      'axioms_all_standard': standard, 'receipt_toolchain': tool, 'repo_toolchain_at_run': repo_toolchain,
                      'meets_lean_%s_on_disk' % LEAN_VERSION.replace('.', '_'): tool == LEAN_VERSION,
                      'on_disk_verdict': verdict, 'evidence_kind': 'sealed_receipt' if receipt else 'none'})
    return units


def parse_witness(label: str, record) -> dict:
    raw = json.dumps(record, ensure_ascii=False) if record is not None else ''
    count, verdict = None, 'not_recorded'
    if isinstance(record, dict):
        if re.search(r'NOT RUN', raw, re.I):
            verdict = 'not_run'
        else:
            if isinstance(record.get('passed'), int):
                count, verdict = record['passed'], 'accepted'
            else:
                match = re.search(r'(\d+) passed', str(record.get('result', '')))
                if match:
                    count, verdict = int(match.group(1)), 'accepted'
                elif isinstance(record.get('tests'), int):
                    count, verdict = record['tests'], 'count_recorded_pass_not_stated'
    command = (record or {}).get('command') if isinstance(record, dict) else None
    tests_file = record.get('tests') if isinstance(record, dict) and isinstance(record.get('tests'), str) else None
    cargo_filter = None
    if command and not tests_file and label == 'python_tests':
        match = re.search(r'pytest\s+(\S+\.py)', command)
        if match:
            tests_file = match.group(1) if match.group(1).startswith('code/') else 'code/python/' + match.group(1)
    if command and label == 'rust_tests':
        match = re.search(r'cargo test --lib\s+(\S+)', command)
        cargo_filter = match.group(1) if match else None
    return {'class': 'W', 'kind': label, 'module': (record or {}).get('module') if isinstance(record, dict) else None,
            'tests_file': tests_file, 'cargo_filter': cargo_filter,
            'recorded_tests': count, 'on_disk_verdict': verdict, 'evidence_kind': 'self_reported_in_validation_json',
            'recorded_command': command}


def witness_units(run_rel: str) -> list:
    validation = load_json(REPO / run_rel / 'validation.json') or {}
    units = []
    for key, label in (('python', 'python_tests'), ('rust', 'rust_tests')):
        if key in validation:
            unit = parse_witness(label, validation[key])
            unit['unit_id'] = '%s::%s' % (run_rel.rsplit('/', 1)[-1], label)
            if label == 'rust_tests' and unit['module'] and not unit.get('cargo_filter'):
                unit['cargo_filter'] = re.sub(r'^code/rust/src/', '', unit['module']).removesuffix('.rs').replace('/', '::')
            units.append(unit)
    return units


def api_run_units(run_rel: str) -> list:
    """The one API-dispatched Fable run (budget.json, model_access.json). Units come from its own receipts."""
    folder = REPO / run_rel
    units = []
    for stem, label, cls in (('matrix_instance_lean', 'MatrixInstance.lean (first compile, retained failure)', 'L'),
                             ('matrix_instance_repaired_lean', 'MatrixInstanceRepaired.lean', 'L'),
                             ('rust_tests', 'rust tests of numeric_replay.rs', 'W'), ('numeric_checker_preflight', 'python numeric checker', 'W')):
        receipt = load_json(folder / 'p2_prepared' / (stem + '_receipt.json'))
        code = receipt.get('exit_code') if receipt else None
        units.append({'unit_id': '%s::%s' % (run_rel.rsplit('/', 1)[-1], stem), 'class': cls, 'kind': label, 'exit_code': code,
                      'receipt': run_rel + '/p2_prepared/%s_receipt.json' % stem if receipt else None,
                      'on_disk_verdict': 'not_recorded' if code is None else ('accepted' if code == 0 else 'rejected'),
                      'authored_by': 'host session (not the Fable API reply); credited to Arm F by the generosity rule',
                      'receipt_toolchain': None, 'evidence_kind': 'process_receipt_exit_code_only'})
    review = load_json(folder / 'p0_mine' / 'claim_review.json') or {}
    dispositions = collections.Counter(c.get('disposition') for c in review.get('claims', []))
    units.append({'unit_id': '%s::p0_claims' % run_rel.rsplit('/', 1)[-1], 'class': 'O', 'kind': 'fable_p0_claims_after_host_review',
                  'claims_reviewed': len(review.get('claims', [])), 'dispositions': dict(sorted(dispositions.items())),
                  'accepted_as_theorem': 0, 'on_disk_verdict': 'not_accepted',
                  'note': 'No P0 claim was accepted by the ladder verifier (it did not exist then); the host disposition is recorded. '
                          'P1 returned zero visible bytes (max_tokens spent in thinking).', 'evidence_kind': 'host_review_json'})
    return units


def tfq0084_units(run_rel: str) -> list:
    folder = REPO / run_rel / 'p0'
    units = []
    for stem, marker in (('relation_sign_check', 'ALL_RELATIONS_HOLD_ON_FINITE_CARRIER'), ('schlafli_rational_form_check', 'T4_NEAR_MISS_NONZERO_WITH_VALID_CONTROL')):
        out = folder / (stem + '.out')
        text = out.read_bytes().decode('utf-8', 'replace') if out.is_file() else ''
        units.append({'unit_id': '%s::%s' % (run_rel.rsplit('/', 1)[-1], stem), 'class': 'W', 'kind': 'python_script_receipt',
                      'script': run_rel + '/p0/%s.py' % stem, 'recorded_output': run_rel + '/p0/%s.out' % stem if out.is_file() else None,
                      'success_marker': marker, 'marker_in_recorded_output': marker in text,
                      'on_disk_verdict': 'accepted' if marker in text else ('rejected' if text else 'not_recorded'),
                      'evidence_kind': 'recorded_stdout_pinned_by_sha256_in_run_README'})
    candidate = load_json(folder / 'candidate.json') or {}
    delta = candidate.get('operad_delta') or {}
    if isinstance(delta, str):  # the candidate points at the YAML delta beside it
        import yaml
        target = REPO / delta
        delta = (yaml.safe_load(target.read_bytes()) or {}) if target.is_file() else {}
    units.append({'unit_id': '%s::p0_operad_delta' % run_rel.rsplit('/', 1)[-1], 'class': 'O', 'kind': 'staged_p0_operad_delta',
                  'counts': {k: len(v) for k, v in delta.items() if isinstance(v, list)}, 'status': candidate.get('status'),
                  'on_disk_verdict': 'not_recorded',
                  'note': 'ready_for_host_review: the host-stage files (host_check.json etc.) are deliberately absent, so no host verdict is on disk.',
                  'evidence_kind': 'candidate_json_only'})
    return units


# --------------------------------------------------------------------------- cost
def authored_bytes(base: str, run_rel: str, validation: dict) -> dict:
    listing = git('ls-tree', '-r', '-l', base, run_rel + '/')
    total, files = 0, []
    for line in listing.splitlines():
        meta, path = line.split('\t', 1)
        size = int(meta.split()[-1]) if meta.split()[-1].isdigit() else 0
        rel = path[len(run_rel) + 1:]
        parts = rel.split('/')
        if len(parts) > 2 or (len(parts) == 2 and parts[0] != 'p0'):
            continue
        if not path.endswith(AUTHORED_EXT) or path.endswith(NOT_AUTHORED):
            continue
        total += size
        files.append(path)
    for key in ('python', 'rust'):
        record = validation.get(key)
        if isinstance(record, dict):
            for field in ('module', 'tests'):
                value = record.get(field)
                if isinstance(value, str) and value.startswith('code/'):
                    size = git('cat-file', '-s', '%s:%s' % (base, value), check=False).strip()
                    if size.isdigit():
                        total += int(size)
                        files.append(value)
    return {'bytes': total, 'files': len(files)}


def fable_lower_bound_usd(nbytes: int) -> float:
    return round(nbytes / BYTES_PER_TOKEN * FABLE_OUT_USD_PER_MTOK / 1e6, 4)


def api_cost(run_rel: str):
    budget = load_json(REPO / run_rel / 'budget.json') or {}
    micro = sum(int(call.get('rated_microusd') or 0) for call in budget.get('calls', []))
    return {'recorded_usd': round(micro / 1e6, 6), 'basis': 'rated from provider usage at published standard rates (budget.json calls[].rated_microusd); invoice unobserved',
            'calls': [{'stage': c.get('stage'), 'model': c.get('model'), 'effort': c.get('effort'), 'input_tokens': (c.get('usage') or {}).get('input_tokens'),
                       'output_tokens': (c.get('usage') or {}).get('output_tokens'), 'rated_usd': round(int(c.get('rated_microusd') or 0) / 1e6, 6),
                       'status': c.get('status'), 'seconds': c.get('seconds')} for c in budget.get('calls', [])]}


# --------------------------------------------------------------------------- markers and exclusions
def lean_markers(run_rel: str) -> tuple:
    """Module stems and namespaces of the Lean files this run installed under lean4/ (the names an Arm S packet must never contain)."""
    folder = REPO / run_rel
    stems, namespaces = set(), set()
    for path in folder.glob('*.lean'):
        if not (REPO / 'lean4' / path.name).is_file():
            continue
        stems.add(path.stem)
        for match in re.finditer(r'^namespace\s+(\S+)', path.read_bytes().decode('utf-8', 'replace'), re.M):
            namespaces.add(match.group(1))
    return stems, namespaces


def artifact_paths(run_rel: str, base: str) -> list:
    folder = REPO / run_rel
    out = []
    for path in folder.glob('*.lean'):
        out.append('lean4/' + path.name)
    validation = load_json(folder / 'validation.json') or {}
    for key in ('python', 'rust'):
        record = validation.get(key)
        if isinstance(record, dict):
            for field in ('module', 'tests'):
                value = record.get(field)
                if isinstance(value, str) and value.startswith('code/'):
                    out.append(value)
    return sorted(set(out))


# --------------------------------------------------------------------------- items
def prompt_block(index_rows: dict, node: str, freeze: str, base: str) -> dict:
    position, row = index_rows[node]
    prompt_freeze = git_show(freeze, row['prompt'])
    prompt_base = git_show(base, row['prompt'])
    collection_freeze = git_show(freeze, row['operad_collection'])
    return {'prompt_path': row['prompt'], 'prompt_sha256_at_freeze': sha256_bytes(prompt_freeze) if prompt_freeze else None,
            'prompt_sha256_at_base': sha256_bytes(prompt_base) if prompt_base else None,
            'operad_collection': row['operad_collection'],
            'operad_collection_sha256_at_freeze': sha256_bytes(collection_freeze) if collection_freeze else None,
            'index_position_at_base': position,
            'source_candidates_at_base': row['source_operation_candidates'] + row['source_relation_candidates'],
            'note': 'The model never reads the prompt file; both arms receive the packet compiled from the operad collection '
                    '(llm_ladder/packets.py). The packet identity is packet_bytes_sha256, recorded at run time.'}


def dedupe_units(units: list) -> list:
    """A later run of the same node re-ships earlier modules and test files under the same names. The verification target is the
    installed copy, so one module or test file is one unit: the latest run's unit stands and lists the runs it supersedes."""
    kept, order = {}, []
    for unit in units:
        if unit['class'] in ('L', 'W') and (unit.get('module') or unit.get('tests_file') or unit.get('cargo_filter')):
            key = (unit['class'], unit['kind'], unit.get('module') if unit['class'] == 'L' else
                   (unit.get('tests_file') or unit.get('cargo_filter') or unit.get('module')))
            if key in kept:
                unit = dict(unit, supersedes=kept[key].get('supersedes', []) + [kept[key]['unit_id']])
                order.remove(key)
            kept[key] = unit
            order.append(key)
        else:
            kept[(id(unit),)] = unit
            order.append((id(unit),))
    return [kept[k] for k in order]


def build_d_items(base, index_rows, hist, classes) -> list:
    by_node = collections.defaultdict(list)
    for run_rel, info in classes.items():
        if info['category'] in ('fable', 'opus') and not run_rel.endswith(('_ladder',)) and '_ladder_' not in run_rel:
            by_node[run_rel.split('/')[2]].append(run_rel)
    items = []
    for node in sorted(by_node):
        runs = sorted(by_node[node])
        first = min((x for r in runs for x in hist[r]), key=lambda x: datetime.fromisoformat(x['date']))
        freeze = first['parents'][0]
        run_entries, units, recorded, lb_bytes, unrecorded = [], [], 0.0, 0, []
        exclude, markers = set(), set()
        api_call_rows = []
        for run_rel in runs:
            info = classes[run_rel]
            slug = run_rel.rsplit('/', 1)[-1]
            validation = load_json(REPO / run_rel / 'validation.json') or {}
            toolchain = git_show(info['first_commit'], 'lean4/lean-toolchain')
            repo_tool = re.search(r'v(\d+\.\d+\.\d+)', toolchain.decode('utf-8', 'replace')).group(1) if toolchain and re.search(rb'v\d+\.\d+\.\d+', toolchain) else None
            run_units = []
            if (REPO / run_rel / 'budget.json').is_file():
                run_units += api_run_units(run_rel)
                cost = api_cost(run_rel)
                recorded += cost['recorded_usd']
                api_call_rows += cost['calls']
                cost_status = 'recorded_rated'
            else:
                if (REPO / run_rel / 'accepted_modules.json').is_file():
                    run_units += lean_units(run_rel, repo_tool) + witness_units(run_rel)
                elif slug.endswith('_staged') and node == 'TFQ-0084':
                    run_units += tfq0084_units(run_rel)
                ab = authored_bytes(base, run_rel, validation)
                lb_bytes += ab['bytes']
                unrecorded.append({'run': run_rel, 'authored_bytes': ab['bytes'], 'authored_files': ab['files']})
                cost_status = 'unrecorded'
            units += run_units
            stems, namespaces = lean_markers(run_rel)
            markers |= stems | namespaces | {slug}
            for path in artifact_paths(run_rel, base):
                exclude.add(path)
                if path.startswith('code/'):
                    markers.add(Path(path).stem)
            run_entries.append({'path': run_rel, 'run_slug': slug, 'model': 'claude-fable-5-1' if info['category'] == 'fable' else 'claude-opus-5-5',
                                'model_basis': 'in-folder model field (budget.json / model_access.json)' if info['in_folder_models'] else
                                               'Co-Authored-By trailer on the commit that added the folder: ' + ', '.join(info['commit_trailers']),
                                'agentic_session': not bool(info['in_folder_models']),
                                'first_commit': info['first_commit'], 'cost_status': cost_status, 'units': len(run_units)})
        units = dedupe_units(units)
        lb = fable_lower_bound_usd(lb_bytes)
        cost = {'recorded_usd': round(recorded, 6) if recorded else None,
                'recorded_calls': api_call_rows,
                'unrecorded_runs': unrecorded,
                'estimate_lower_bound_usd_unrecorded_runs': lb if unrecorded else None,
                'estimate_method': ('LOWER BOUND ONLY. committed authored bytes of the unrecorded runs (Lean sources, run notes, twins and their tests; '
                                    'no receipts, no binaries) / %.1f bytes per token x USD %.0f per million output tokens (claude-fable-5-1 list price in '
                                    'llm_ladder/config.py). It omits thinking, tool calls, every re-read of context, repairs and abandoned attempts, so the '
                                    'true cost is higher. The user may supply the real session cost in cost_overrides.json (see protocol.md 6.4).' % (BYTES_PER_TOKEN, FABLE_OUT_USD_PER_MTOK))
                if unrecorded else None,
                'status': 'recorded_rated' if recorded and not unrecorded else ('partly_recorded' if recorded else 'unrecorded')}
        items.append({'stratum': 'D', 'node_id': node, **prompt_block(index_rows, node, freeze, base),
                      'arm_f': {'mode': 'reuse', 'runs': run_entries, 'cost': cost, 'units': units,
                                'comparability': ('Agentic multi-turn Claude Code sessions with tools and human steering; the instruction text each session '
                                                  'received is not in the repository, so the input is NOT byte-identical to Arm S. Outcome comparison only.')
                                if any(r['agentic_session'] for r in run_entries) else 'API-dispatched, but the request was the staged prompt, not the ladder packet'},
                      'arm_s': {'packet_source': 'compile_p0_cleanroom', 'freeze_commit': freeze, 'freeze_rule': 'parent of the oldest commit that added any Arm F run folder of this node',
                                'freeze_commit_date': git('log', '-1', '--format=%cI', freeze).strip(),
                                'exclude_paths': sorted(exclude), 'leak_markers': sorted(m for m in markers if len(m) >= 8)}})
    return items


def build_p_items(base, index_rows, hist) -> list:
    found = collections.defaultdict(list)
    for receipt_path in sorted((REPO / 'dag' / 'results').glob('*/runs/*_ladder*/ladder_receipt.json')):
        receipt = load_json(receipt_path)
        node = receipt['node_id']
        run_dir = receipt_path.parent
        calls = {c['attempt_id']: c for c in receipt['calls'] if c.get('status') == 'ok'}
        for attempt in receipt['summary']['attempts']:
            if attempt.get('model') in EXPENSIVE and attempt.get('status') in ('accepted', 'rejected'):
                call = calls.get(attempt['attempt_id'], {})
                found[node].append({'run': run_dir.relative_to(REPO).as_posix(), 'attempt_id': attempt['attempt_id'], 'model': attempt['model'],
                                    'input_sha256': attempt['input_sha256'], 'verified_total': attempt['verified_total'],
                                    'failures_total': attempt['failures_total'], 'failures_by_class': attempt['failures_by_class'],
                                    'accepted_by_ladder_policy': attempt['status'] == 'accepted',
                                    'cost_usd': round((call.get('cost_microusd') or 0) / 1e6, 6), 'cost_source': call.get('cost_source'),
                                    'input_tokens': call.get('input_tokens'), 'output_tokens': call.get('output_tokens'),
                                    'latency_s': call.get('latency_s'), 'stop_reason': call.get('stop_reason'),
                                    'request_path': run_dir.relative_to(REPO).as_posix() + '/p0/attempts/%s/request.json' % attempt['attempt_id']})
    rank = {'claude-fable-5-1': 0, 'claude-opus-5-5': 1}
    items = []
    for node in sorted(found):
        attempts = sorted(found[node], key=lambda a: (rank[a['model']], a['run'], a['attempt_id']))
        headline = attempts[0]
        run_rel = headline['run']
        first = hist.get(run_rel, [None])[0]
        if first is None:
            raise CompareError('no commit history for ' + run_rel)
        freeze = first['parents'][0]
        stored = json.loads((REPO / headline['request_path']).read_bytes().decode('utf-8'))
        digest = packet_bytes_sha256(stored['system_prompt'], stored['user_prompt'], stored['response_schema'])
        units = [{'unit_id': '%s::%s' % (a['run'].rsplit('/', 1)[-1], a['attempt_id']), 'class': 'O', 'kind': 'ladder_p0_attempt', 'model': a['model'],
                  'verified_entries': a['verified_total'], 'refused_claims': a['failures_total'], 'refused_by_class': a['failures_by_class'],
                  'accepted_by_ladder_policy': a['accepted_by_ladder_policy'], 'cost_usd': a['cost_usd'], 'input_sha256': a['input_sha256'],
                  'on_disk_verdict': 'accepted' if a['accepted_by_ladder_policy'] else 'rejected',
                  'headline': a is headline, 'evidence_kind': 'ladder_receipt_host_check'} for a in attempts]
        items.append({'stratum': 'P', 'node_id': node, **prompt_block(index_rows, node, freeze, base),
                      'arm_f': {'mode': 'reuse', 'runs': [{'path': r, 'model': sorted({a['model'] for a in attempts if a['run'] == r})[0],
                                                           'model_basis': 'ladder_receipt.json attempt rows', 'agentic_session': False,
                                                           'first_commit': (hist.get(r) or [{}])[0].get('commit'), 'cost_status': 'recorded_rated'}
                                                          for r in sorted({a['run'] for a in attempts})],
                                'headline_attempt': {'run': headline['run'], 'attempt_id': headline['attempt_id'], 'model': headline['model']},
                                'headline_rule': 'the highest-priced model attempted on the node (Fable before Opus), earliest run, earliest attempt',
                                'cost': {'recorded_usd': headline['cost_usd'], 'status': 'recorded_rated', 'basis': 'ladder_receipt.json calls[].cost_microusd (rated from provider usage)',
                                         'all_expensive_attempts_usd': round(sum(a['cost_usd'] for a in attempts), 6)},
                                'units': units,
                                'comparability': 'Byte-identical by construction: the stored request of the headline attempt is replayed to Arm S.'},
                      'arm_s': {'packet_source': 'replay_stored_request', 'freeze_commit': freeze,
                                'freeze_rule': 'parent of the commit that added the ladder run folder holding the headline attempt',
                                'freeze_commit_date': git('log', '-1', '--format=%cI', freeze).strip(),
                                'replay': {'request_path': headline['request_path'], 'attempt_id': headline['attempt_id'],
                                           'input_sha256': headline['input_sha256'], 'packet_bytes_sha256': digest},
                                'exclude_paths': [], 'leak_markers': sorted({a['run'].rsplit('/', 1)[-1] for a in attempts})}})
    return items


def build_c_items(base, index_rows, d_items) -> list:
    unrun = []
    for node, (position, row) in index_rows.items():
        if row.get('latest_run') or (REPO / 'dag' / 'results' / node).is_dir():
            continue
        family = '_'.join(Path(row['prompt']).stem.split('_')[:3])
        unrun.append((node, position, row, family, row['source_operation_candidates'] + row['source_relation_candidates']))
    taken, items, matches = set(), [], []
    # A control is a never-run prompt, but the repository at the base commit already holds every Arm F artifact of the cohort.
    # They are removed from the control clean rooms too, so that a control cannot be graded on Fable's later declarations.
    all_exclude = sorted({p for d in d_items for p in d['arm_s']['exclude_paths']})
    all_markers = sorted({m for d in d_items for m in d['arm_s']['leak_markers']})
    for d in d_items:
        family = '_'.join(Path(d['prompt_path']).stem.split('_')[:3])
        pool = [u for u in unrun if u[0] not in taken]
        same = [u for u in pool if u[3] == family]
        chosen_pool, quality = (same, 'same_family') if same else (pool, 'fallback_any_family')
        chosen = min(chosen_pool, key=lambda u: (abs(u[4] - d['source_candidates_at_base']), u[1]))
        taken.add(chosen[0])
        matches.append((d['node_id'], chosen[0], quality))
        node, position, row, fam, count = chosen
        items.append({'stratum': 'C', 'node_id': node, **prompt_block(index_rows, node, base, base),
                      'matched_to': d['node_id'], 'match_rule': 'same prompt family if any, else any; nearest operation+relation candidate count; lowest index position',
                      'match_quality': quality, 'arm_f': None,
                      'arm_s': {'packet_source': 'compile_p0_cleanroom', 'freeze_commit': base, 'freeze_rule': 'base commit of this cohort, with every Arm F artifact of every D prompt removed (no Arm F exists for a control)',
                                'freeze_commit_date': git('log', '-1', '--format=%cI', base).strip(),
                                'exclude_paths': all_exclude, 'leak_markers': all_markers}})
    return items


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--base', default='origin/main')
    parser.add_argument('--controls', type=int, default=None, help='default: one control per D prompt')
    parser.add_argument('--out', default=str(COHORT))
    parser.add_argument('--print', action='store_true', dest='show')
    args = parser.parse_args(argv)
    base = git('rev-parse', '--verify', args.base + '^{commit}').strip()
    if git('status', '--porcelain', '--', 'dag/results').strip():
        raise CompareError('dag/results has uncommitted changes; build the cohort from a clean results tree')
    if not PROTOCOL.is_file():
        raise CompareError('write protocol.md first: its sha256 is pinned in cohort.json')
    index = json.loads(git_show(base, 'dag/operads/index.json').decode('utf-8'))
    index_rows = {row['node_id']: (position, row) for position, row in enumerate(index['nodes'])}
    hist = history(base)
    classes = {run: classify(run, commits) for run, commits in hist.items() if not run.endswith('_ladder') and '_ladder_' not in run}
    d_items = build_d_items(base, index_rows, hist, classes)
    p_items = build_p_items(base, index_rows, hist)
    c_items = build_c_items(base, index_rows, d_items)
    if args.controls is not None:
        c_items = c_items[:args.controls]
    by_category = collections.Counter(info['category'] for info in classes.values())
    named_unproven = sorted(run for run, info in classes.items() if info['category'] == 'no_trailer' and not run.endswith('_staged'))
    excluded = {
        'scan': {'runs_scanned_excluding_ladder': len(classes), 'by_provenance_category': dict(sorted(by_category.items()))},
        'no_expensive_model_provenance': {
            'reason': 'The commit has no Co-Authored-By model trailer and the folder carries no model field, or the folder text names Codex (the batch runs of 2026-10-19..20). '
                      'Such runs may have been made by a large model but cannot be shown to be; they are not Arm F.',
            'staged_runs_no_trailer': sum(1 for run, info in classes.items() if info['category'] == 'no_trailer' and run.endswith('_staged')),
            'named_runs_no_trailer': named_unproven},
        'sonnet_reference_only': {
            'reason': 'Sonnet 5.5 is not in the expensive set (list price 2/10 USD per million tokens against 10/50 for Fable). The 26 batch-1 staged runs (positions 152-177) are '
                      'listed for context only.',
            'runs': sorted(run for run, info in classes.items() if info['category'] == 'sonnet')},
        'opus_runs': {'reason': 'No completed Opus run folder exists other than the ladder attempts of stratum P. Opus commits are tooling, migration and DAG work, and Opus sub-agents wrote the '
                                'Python and Rust twins inside Fable sessions (named in validation.json); neither is a prompt run.',
                      'runs': sorted(run for run, info in classes.items() if info['category'] == 'opus')}}
    cohort = {'schema_id': COHORT_SCHEMA_ID, 'authority_effect': 'None',
              'claim': ('Pre-registered cohort of the Fable-versus-swarm comparison. Arm F outcomes are what the receipts on disk say; no verifier was re-run to fill this file. '
                        'The instructions of the agentic Fable sessions are not in the repository, so stratum D is an outcome comparison, not a paired one.'),
              'built_from': {'base_ref': args.base, 'base_commit': base, 'base_commit_date': git('log', '-1', '--format=%cI', base).strip()},
              'protocol': {'path': PROTOCOL.relative_to(REPO).as_posix(), 'sha256': protocol_sha256(),
                           'sha256_basis': 'sha256 of the file bytes with CRLF folded to LF'},
              'lean_version_required': LEAN_VERSION, 'standard_axioms': list(STANDARD_AXIOMS),
              'caps_per_prompt': {'max_provider_calls': DEFAULT_MAX_CALLS, 'wallclock_s': DEFAULT_WALLCLOCK_S},
              'strata': {'D': 'prompts with a completed expensive-model derivation run (Fable) in dag/results',
                         'P': 'prompts with expensive-model ladder attempts (Opus, Fable) on a recorded packet',
                         'C': 'matched never-run controls (swarm only; yield and abstention rates, no parity claim)'},
              'items': d_items + p_items + c_items, 'excluded_candidates': excluded}
    Path(args.out).write_bytes(json_bytes(cohort))
    summary = collections.Counter(i['stratum'] for i in cohort['items'])
    print('wrote %s  items=%s  base=%s  protocol_sha256=%s' % (Path(args.out).relative_to(REPO) if Path(args.out).is_relative_to(REPO) else args.out,
                                                                dict(summary), base[:12], cohort['protocol']['sha256'][:12]))
    if args.show:
        for item in cohort['items']:
            cost = (item.get('arm_f') or {}).get('cost') or {}
            print('%s  %-36s freeze=%s  arm_f_units=%s  cost=%s' % (item['stratum'], item['node_id'], item['arm_s']['freeze_commit'][:9],
                                                                       len((item.get('arm_f') or {}).get('units', [])), cost.get('status')))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except CompareError as error:
        print('REFUSED: %s' % error, file=sys.stderr)
        raise SystemExit(2)
