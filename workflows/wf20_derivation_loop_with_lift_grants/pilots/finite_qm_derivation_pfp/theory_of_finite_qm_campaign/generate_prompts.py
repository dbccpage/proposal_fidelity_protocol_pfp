"""Generate PFP prompts, operad collections, audit-extension rows and index rows from DAG nodes.

The sealed corpus (the 177 prompts of prompt_audit.json, filename_custody.json, custody.py)
is never edited. For every node of dag/derivation_dag.json without a prompt this tool emits

* dag/prompts/<stage>_<id>_<status>.yaml   (name through custody.canonical_filename),
* dag/operads/<id>.yaml                    (target, paper pins, declaration-scan candidates,
                                            empty presentation),
* a row of dag/pfp/prompt_audit_extension.json (same row shape as prompt_audit.json, with
  after_sha256, plus the digests of every generation input),
* a row of dag/operads/index.json, appended after the sealed rows in tier order:
  A = OPEN, CONDITIONAL, IMPORTED_ASSUMPTION, PROVED_PROSE, COMPUTATIONALLY_CHECKED,
      SOURCE_RECORD, REFUTED;  B = PROVED_LEAN;  C = DEFINITION, ADMITTED_PRIMITIVE.
  Within a tier the DAG order is kept. Rows that have already run keep their position.

Generation is deterministic (no clock, no git state, no network) and idempotent. The inputs of
each emitted prompt are recorded, so --check reports a prompt as stale when the node statement,
status, stage, assumptions, bottleneck, source references, paper pins or scanned local source
changed after generation; --write regenerates stale prompts that have not run yet. A prompt that
has run (its index row has latest_run) is never rewritten: it is reported as needing a manual
delta. A recorded stage history also protects a collection when its index update was missed.
An explicit retained_collection binding in the extension can reconcile a P0 delta with the
unchanged generated inputs and prompt; it binds the generated skeleton, current collection
and recorded delta bytes, without accepting their mathematical content.
Declaration scanning reads only files inside this repository; sources that are not
checked in here are bound as external with a null digest and are pinned when a batch is
prepared. Papers that dag/sync_pregenesis_to_wdp.py renders or rewrites (the fragment records TFQ-0417
upward and their parents) are not pinned, because that sync must stay free to write them. Nothing here
accepts a theorem: AuthorityEffect None.

    python -I -X utf8 dag/pfp/generate_prompts.py --check --all-missing
    python -I -X utf8 dag/pfp/generate_prompts.py --write --nodes ID [ID ...]
    python -I -X utf8 dag/pfp/generate_prompts.py --write --all-missing
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from custody import canonical_filename  # noqa: E402  (sealed helper, imported not edited)

REPO = HERE.parents[1]
GENERATOR_VERSION = 1
EXTENSION_SCHEMA = 'omega.pfp.finite-qm.prompt-audit-extension.v1'
EXTENSION_PATH = 'dag/pfp/prompt_audit_extension.json'
EXTERNAL_COMMIT = '727bf06ef98a8ac75652cdf2348843ed7f34b208'
TIER_A = ('OPEN', 'CONDITIONAL', 'IMPORTED_ASSUMPTION', 'PROVED_PROSE', 'COMPUTATIONALLY_CHECKED',
          'SOURCE_RECORD', 'REFUTED')
TIER_B = ('PROVED_LEAN',)
TIER_C = ('DEFINITION', 'ADMITTED_PRIMITIVE')
OPERATION_KINDS = ('def', 'structure', 'inductive', 'abbrev', 'class')
RELATION_KINDS = ('theorem', 'lemma')
EXCERPT_LIMIT = 600
OPERATION_LIMIT = 16
BODY_LINES = 60
AGGREGATE_NAME = re.compile(r'^master_|census|tranche|_witness$|dag_177|route_partition')
AGGREGATE_CONJUNCTS = 12
BOUNDED_DOMAIN = re.compile(r'Fin\s+\d|native_decide|\bdecide\b')
BOUNDED_WARNING = ('This declaration includes a fixed finite enumeration; no unbounded conclusion '
                   'follows automatically.')
SCOPE_OBLIGATION = ('Compare this declaration with the full target; existence in a file is not a '
                    'discharged proof.')
LABEL_RULE = ('Historical status is a source annotation. Check the exact theorem scope and remaining '
              'imports before reusing a result.')
BASE_OBLIGATIONS = [
    'Match the exact source theorem to this target, including quantifiers and imported hypotheses.',
    'Select and semantically check the generators needed by one useful next step.',
    'Record actual typed compositions, identity/unit/associativity obligations, and justified relations.',
    'Bind independent certificate predicates and real checker anchors before P1.',
]
NO_SCAN_OBLIGATION = ('No source definition was recovered by the bounded declaration scan. Inspect imported '
                      'modules and function-valued premises; do not invent an operation.')
COHERENCE = ['identity_operations', 'unit_laws', 'partial_composition_associativity',
             'symmetric_action_if_claimed', 'relations_stable_under_grafting']
DECLARATION = re.compile(
    r'^(?:@\[[^\]]*\]\s*)*(?:(?:private|protected|noncomputable|partial|unsafe)\s+)*'
    r'(theorem|lemma|def|structure|inductive|class|abbrev|instance|axiom|opaque)\s+([^\s:({\[]+)')
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_.'!?]*")
RUST_DECLARATION = r'^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+|const\s+|unsafe\s+)*(?:fn|struct|enum|trait|type)\s+%s\b'
USER_PROMPT = (
    'Current stage: P0_MINE_OPERAD.\n'
    'Research target (source claim; verify its scope before reuse):\n'
    '{statement}\n\n'
    'Declared assumptions:\n{assumptions}\n\n'
    'Source bottleneck:\n{bottleneck}\n\n'
    'Open ../operads/{operad_name}. Review the source-pinned operation and relation candidates.\n'
    'Collect useful typed generators, actual relations, composition laws, and remaining obligations.\n'
    'Start with the most useful unresolved dependency. If it needs more work, remain at P0 and save the partial collection.\n'
    'Return the P0 stage contract and operad delta; do not attempt the final derivation in this mining turn.\n'
    'A host-reviewed next step can later enter P1_DERIVE. Verification, repair, challenge, and recording are distinct stages.\n')


# ---------------------------------------------------------------- small helpers
LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)


def load_yaml(data):
    return yaml.load(data, Loader=LOADER)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


class _Dumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


def _text(dumper, value):
    return dumper.represent_scalar('tag:yaml.org,2002:str', value, style='|' if '\n' in value else None)


_Dumper.add_representer(str, _text)


def dump_yaml(value) -> bytes:
    return yaml.dump(value, Dumper=_Dumper, sort_keys=False, allow_unicode=True, width=100).encode('utf-8')


def dump_json(value) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def atomic_write(path: Path, data: bytes):
    """Replace, never modify in place: other links to the old bytes stay intact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_bytes(data)
    os.replace(temporary, path)


def tier_of(status: str) -> str:
    if status in TIER_A:
        return 'A'
    if status in TIER_B:
        return 'B'
    if status in TIER_C:
        return 'C'
    raise ValueError('unknown node status (no tier): ' + status)


# ---------------------------------------------------------------- corpus loading
class Corpus:
    """Everything read from one tree; the tree is REPO for real runs and a copy for tests."""

    def __init__(self, root: Path):
        self.root = Path(root)
        dag = json.loads((self.root / 'dag/derivation_dag.json').read_bytes())
        self.dag = dag
        self.nodes = dag['nodes']
        self.position = {n['id']: i for i, n in enumerate(self.nodes)}
        if len(self.position) != len(self.nodes):
            raise ValueError('duplicate node ids in DAG')
        self.by_id = {n['id']: n for n in self.nodes}
        self.records = defaultdict(list)
        for line in (self.root / 'dag/theory_of_finite_qm.jsonl').read_text(encoding='utf-8').splitlines():
            if line.strip():
                row = json.loads(line)
                for node_id in row.get('existing_derivation_dag_ids', []):
                    self.records[node_id].append(row['id'])
        self.papers = {}
        for path in sorted((self.root / 'dag/derivations').glob('*/tfq_*.md')):
            match = re.match(r'tfq_(\d+)_', path.name)
            if match:
                self.papers.setdefault('TFQ-' + match.group(1), []).append(path)
        # Papers that dag/sync_pregenesis_to_wdp.py renders (fragment records) or rewrites (section 4 of
        # an unpinned parent). Pinning one would make the sync's pinned_parent flags and the pin digests
        # stale, and pinned papers must never be rewritten, so these are never pinned here.
        self.sync_owned = set()
        fragment = self.root / 'dag/fragments/pregenesis_to_wdp.json'
        if fragment.is_file():
            for row in json.loads(fragment.read_bytes()).get('records', []):
                self.sync_owned.update((row['id'], row['parent_id']))
        self.index_path = self.root / 'dag/operads/index.json'
        self.index = json.loads(self.index_path.read_bytes())
        self.base_audit = json.loads((self.root / 'dag/pfp/prompt_audit.json').read_bytes())
        self.base_ids = [row['node_id'] for row in self.base_audit['nodes']]
        ext = self.root / EXTENSION_PATH
        self.extension = json.loads(ext.read_bytes()) if ext.is_file() else None
        self.ext_rows = {row['node_id']: row for row in (self.extension or {}).get('nodes', [])}
        self.prompt_of = {}
        for path in sorted((self.root / 'dag/prompts').glob('*.yaml')):
            self.prompt_of[re.search(rb'^node_id: (\S+)', path.read_bytes(), re.M).group(1).decode()] = path
        self.index_rows = {row['node_id']: row for row in self.index['nodes']}
        self._lean = {}

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def has_prompt(self, node_id: str) -> bool:
        return node_id in self.prompt_of or node_id in self.index_rows

    def executed(self, node_id: str) -> bool:
        row = self.index_rows.get(node_id) or self.ext_rows.get(node_id)
        if not row:
            return False
        if row.get('latest_run'):
            return True
        # A missed index update must not erase a recorded (including negative) run.
        path = self.root / row['operad_collection']
        return path.is_file() and bool(load_yaml(path.read_bytes()).get('stage_history'))

    def missing(self):
        return [n for n in self.nodes if not self.has_prompt(n['id'])]

    # ---- local source resolution and declaration scan
    def resolve_local(self, ref_path: str):
        candidates = [ref_path]
        if ref_path.startswith('lean4/quantum_mechanics/'):
            candidates.append('lean4/' + ref_path[len('lean4/quantum_mechanics/'):])
        for name in candidates:
            target = self.root / name
            if target.is_file():
                return name, target
        return None, None

    def lean_table(self, path: Path):
        if path not in self._lean:
            text = path.read_bytes().decode('utf-8', errors='replace')
            lines = text.splitlines()
            stack, table = [], []
            for number, line in enumerate(lines, 1):
                stripped = line.strip()
                namespace = re.match(r'namespace\s+(\S+)', stripped)
                section = re.match(r'section(?:\s+(\S+))?\s*$', stripped)
                end = re.match(r'end(?:\s+(\S+))?\s*$', stripped)
                if namespace:
                    stack.append(('ns', namespace.group(1)))
                elif section:
                    stack.append(('sec', section.group(1) or ''))
                elif end and stack:
                    stack.pop()
                match = DECLARATION.match(line)
                if match and line[:1] not in (' ', '\t', '-'):
                    kind, name = match.groups()
                    prefix = '.'.join(n for k, n in stack if k == 'ns')
                    full = name[len('_root_.'):] if name.startswith('_root_.') else (prefix + '.' + name if prefix else name)
                    table.append({'kind': kind, 'name': name, 'full': full, 'line': number})
            self._lean[path] = (lines, table)
        return self._lean[path]


def excerpt(lines, number):
    chunk = []
    for line in lines[number - 1:number + 14]:
        chunk.append(line)
        if ':=' in line or re.search(r'\bwhere\s*$', line):
            break
    text = '\n'.join(chunk)
    for marker in (':=', ' where'):
        if marker in text:
            text = text.split(marker, 1)[0]
    text = text.rstrip()
    return text[:EXCERPT_LIMIT]


def scan_lean(corpus: Corpus, ref_path, symbol):
    """Return (status, declaration or None, table lines, table)."""
    name, path = corpus.resolve_local(ref_path)
    lines, table = corpus.lean_table(path)
    if not symbol:
        return 'file_only_no_symbol', None, lines, table
    hits = [d for d in table if d['full'] == symbol]
    if not hits:
        tail = symbol.split('.')
        hits = [d for d in table if d['full'].split('.')[-len(tail):] == tail] or \
               [d for d in table if d['name'] == symbol]
    if not hits:
        return 'symbol_not_found', None, lines, table
    if len(hits) > 1:
        return 'ambiguous_declaration', hits[0], lines, table
    return 'declaration_found_not_proof_checked', hits[0], lines, table


def scan_rust(path: Path, symbol):
    if not symbol:
        return 'file_only_no_symbol', None
    lines = path.read_bytes().decode('utf-8', errors='replace').splitlines()
    short = symbol.split('::')[-1].split('.')[-1]
    pattern = re.compile(RUST_DECLARATION % re.escape(short))
    hits = [i for i, line in enumerate(lines, 1) if pattern.match(line)]
    if not hits:
        return 'symbol_not_found', None
    return ('declaration_found_not_executed' if len(hits) == 1 else 'ambiguous_declaration'), hits[0]


# ---------------------------------------------------------------- per-node build
def split_ref(reference: str):
    path, _, symbol = reference.partition('::')
    return path, (symbol or None)


def mine_node(corpus: Corpus, node):
    """Source bindings, operation/relation candidates, excluded aggregates and local pins."""
    bindings, operations, relations, excluded = [], [], [], []
    seen_ops, seen_rel, local_pins = set(), set(), {}
    pending_ops = []
    for reference in list(node.get('lean', [])) + list(node.get('rust', [])):
        ref_path, symbol = split_ref(reference)
        local_name, local_path = corpus.resolve_local(ref_path)
        entry = {'original_ref': reference}
        if local_path is None:
            internal = ref_path.startswith(('lean4/', 'code/', 'dag/', 'papers/'))
            entry.update(availability='unavailable' if internal else 'external', symbol=symbol, path=ref_path,
                         repository='this_repository' if internal else 'the_symbol_game', sha256=None,
                         declaration_status='path_not_found_locally' if internal else 'external_source_not_scanned',
                         role='source_lead_only')
            bindings.append(entry)
            continue
        digest = sha(local_path.read_bytes())
        local_pins[local_name] = digest
        if local_name.endswith('.lean'):
            status, declaration, lines, table = scan_lean(corpus, local_name, symbol)
            entry.update(availability='local', symbol=symbol, path=local_name, repository='this_repository',
                         sha256=digest, declaration_status=status)
            if declaration:
                entry['line'] = declaration['line']
                candidate = {'kind': declaration['kind'], 'name': declaration['name'],
                             'line': declaration['line'], 'signature_excerpt': excerpt(lines, declaration['line']),
                             'source': local_name, 'repository': 'this_repository', 'source_sha256': digest,
                             'status': 'source_candidate_requires_semantic_review'}
                if declaration['kind'] in RELATION_KINDS:
                    signature = candidate['signature_excerpt']
                    if AGGREGATE_NAME.search(declaration['name']) or signature.count('∧') >= AGGREGATE_CONJUNCTS:
                        excluded.append({'source': local_name, 'name': declaration['name'],
                                         'reason': 'aggregate_or_proxy_scope_requires_projection_not_a_task_relation'})
                    elif (local_name, declaration['name']) not in seen_rel:
                        seen_rel.add((local_name, declaration['name']))
                        candidate['scope_obligation'] = SCOPE_OBLIGATION
                        if BOUNDED_DOMAIN.search(signature):
                            candidate['bounded_domain_warning'] = BOUNDED_WARNING
                        relations.append(candidate)
                        pending_ops.append((local_name, lines, table, signature, digest))
                elif declaration['kind'] in OPERATION_KINDS and (local_name, declaration['name']) not in seen_ops:
                    seen_ops.add((local_name, declaration['name']))
                    operations.append(candidate)
        else:
            status, line = scan_rust(local_path, symbol)
            entry.update(availability='local', symbol=symbol, path=local_name, repository='this_repository',
                         sha256=digest, declaration_status=status)
            if line:
                entry['line'] = line
        entry['role'] = 'source_lead_only'
        bindings.append(entry)
    # Operation candidates: definitions named in the relation signatures, then (breadth first, bounded)
    # those named in the bodies of the definitions already found, in the same file.
    for local_name, lines, table, signature, digest in pending_ops:
        by_name = {}
        for d in table:
            if d['kind'] in OPERATION_KINDS:
                by_name.setdefault(d['name'], d)
        starts = sorted(d['line'] for d in table)

        def body(declaration):
            later = [n for n in starts if n > declaration['line']]
            end = min(later[0] - 1 if later else len(lines), declaration['line'] + BODY_LINES)
            return '\n'.join(lines[declaration['line'] - 1:end])

        queue = [signature]
        while queue and len(operations) < OPERATION_LIMIT:
            text = queue.pop(0)
            for token in IDENTIFIER.findall(text):
                d = by_name.get(token)
                if d and (local_name, d['name']) not in seen_ops and len(operations) < OPERATION_LIMIT:
                    seen_ops.add((local_name, d['name']))
                    operations.append({'kind': d['kind'], 'name': d['name'], 'line': d['line'],
                                       'signature_excerpt': excerpt(lines, d['line']), 'source': local_name,
                                       'repository': 'this_repository', 'source_sha256': digest,
                                       'status': 'source_candidate_requires_semantic_review'})
                    queue.append(body(d))
    return bindings, operations, relations, excluded, local_pins


def paper_pins(corpus: Corpus, node_id):
    refs = []
    for record_id in corpus.records.get(node_id, []):
        if record_id not in corpus.sync_owned:
            refs.extend(corpus.papers.get(record_id, []))
    refs = sorted(set(refs), key=lambda p: (p.name, p.as_posix()))
    return [{'path': corpus.rel(p), 'sha256': sha(p.read_bytes())} for p in refs]


def node_inputs(node, pins, local_pins):
    return {'statement_sha256': sha(node['statement'].encode('utf-8')), 'status': node['status'], 'stage': node['stage'],
            'assumptions_sha256': sha(canonical_json(node.get('imported_structure', []))),
            'bottleneck_sha256': sha(node.get('bottleneck', '').encode('utf-8')),
            'source_refs_sha256': sha(canonical_json([node.get('source', []), node.get('lean', []), node.get('rust', [])])),
            'paper_pins': pins, 'local_sources': [{'path': k, 'sha256': v} for k, v in sorted(local_pins.items())]}


def build_node(corpus: Corpus, node, prompt_path=None):
    node_id, statement = node['id'], node['statement']
    status, stage = node['status'], node['stage']
    tier_of(status)
    prompt_rel = prompt_path or 'dag/prompts/' + canonical_filename('%s_%s_%s.yaml' % (stage, node_id, status))
    operad_name = canonical_filename(node_id + '.yaml')
    operad_rel = 'dag/operads/' + operad_name
    bindings, operations, relations, excluded, local_pins = mine_node(corpus, node)
    pins = paper_pins(corpus, node_id)
    assumptions = list(node.get('imported_structure', []))
    bottleneck = node.get('bottleneck', '')
    template = load_yaml((corpus.root / 'dag/pfp/prompt_template.yaml').read_bytes())
    prompt = {
        'schema_id': 'omega.pfp.finite-qm.staged-dag-prompt.v1', 'node_id': node_id, 'research_stage': stage,
        'authority_effect': 'None', 'workflow': '../pfp/workflow.yaml', 'mode': '../pfp/mode.yaml',
        'stage_contracts': '../pfp/stage_contracts.yaml', 'default_stage': 'P0_MINE_OPERAD',
        'operad_record': '../operads/' + operad_name, 'results_root': '../results/' + node_id,
        'system_prompt': template['system_prompt'],
        'user_prompt': USER_PROMPT.format(statement=statement, bottleneck=bottleneck, operad_name=operad_name,
                                          assumptions='\n'.join('- ' + a for a in assumptions))}
    obligations = list(BASE_OBLIGATIONS)
    if not operations and not relations:
        obligations.insert(0, NO_SCAN_OBLIGATION)
    record = {
        'schema_id': 'omega.pfp.finite-qm.operad-collection.v1', 'node_id': node_id, 'authority_effect': 'None',
        'collection_status': 'source_candidates_collected_semantic_mining_open',
        'target': {'source_statement': statement, 'statement_status': 'source_claim_to_scope_check_not_accepted_result',
                   'declared_assumptions': assumptions, 'source_bottleneck': bottleneck,
                   'source_refs': list(node.get('source', [])), 'paper_refs': [p['path'] for p in pins],
                   'source_claim_label': status, 'label_rule': LABEL_RULE, 'unavailable_paper_refs': [],
                   'paper_source_pins': pins},
        'source_provenance': {'repository': 'this_repository', 'generator': 'dag/pfp/generate_prompts.py',
                              'generator_version': GENERATOR_VERSION,
                              'dag_source_commit': corpus.dag.get('source_commit'), 'path': prompt_rel,
                              'external_repository_commit': EXTERNAL_COMMIT},
        'operation_candidates': operations, 'relation_candidates': relations, 'source_bindings': bindings,
        'presentation': {'colours': [], 'generators': [], 'relations': [], 'compositions': [], 'identities': [],
                         'symmetric_actions': [], 'coherence_obligations': list(COHERENCE)},
        'operad_slots': {
            'slot_m1_layer0_ambient_carrier': {'mining_status': 'UNREVIEWED', 'carrier': None, 'coefficient_ring': None,
                                               'assumptions': list(assumptions), 'source_pins': [], 'public_input': {}},
            'slot_m2_layer1_forward_morphisms': {'mining_status': 'UNREVIEWED', 'operations': [], 'composition_plan': []},
            'slot_m3_layer2_ideals_and_annihilators': {'mining_status': 'UNREVIEWED', 'algebraic_relations': [],
                                                       'rejection_predicates': [], 'negative_control_plan': []},
            'slot_m4_tri_language_witness_anchors': {'mining_status': 'UNREVIEWED', 'certificate_predicates': [],
                                                     'anchors': [], 'unpaid_imports': list(assumptions)}},
        'stage_history': [], 'open_obligations': obligations, 'excluded_relation_leads': excluded}
    prompt_bytes, record_bytes = dump_yaml(prompt), dump_yaml(record)
    if load_yaml(prompt_bytes) != prompt or load_yaml(record_bytes) != record:
        raise ValueError(node_id + ': YAML round trip altered the content')
    if statement not in load_yaml(prompt_bytes)['user_prompt']:
        raise ValueError(node_id + ': statement not verbatim in user_prompt')
    inputs = node_inputs(node, pins, local_pins)
    audit = {'node_id': node_id, 'prompt': prompt_rel, 'before_sha256': None, 'after_sha256': sha(prompt_bytes),
             'removed_patterns': [], 'operation_candidates': len(operations), 'relation_candidates': len(relations),
             'excluded_aggregate_relation_leads': len(excluded), 'source_binding_issues': [],
             'mining_status': 'semantic_review_open', 'tier': tier_of(status), 'operad_collection': operad_rel,
             'operad_collection_sha256': sha(record_bytes), 'inputs': inputs}
    index = {'node_id': node_id, 'prompt': prompt_rel, 'operad_collection': operad_rel,
             'source_operation_candidates': len(operations), 'source_relation_candidates': len(relations),
             'current_stage': 'P0_MINE_OPERAD', 'ready_for_derivation': False}
    return {'node_id': node_id, 'prompt_path': prompt_rel, 'prompt_bytes': prompt_bytes, 'operad_path': operad_rel,
            'operad_bytes': record_bytes, 'audit': audit, 'index': index, 'inputs': inputs}


# ---------------------------------------------------------------- planning
def stale_reasons(old_inputs, new_inputs):
    reasons = []
    for key in sorted(new_inputs):
        if old_inputs.get(key) != new_inputs[key]:
            reasons.append(key)
    return reasons


def retained_collection_matches(corpus: Corpus, row: dict, built: dict) -> bool:
    """Recognise an explicitly bound P0 delta, never semantic acceptance of it.

    The complete generated audit and prompt must still match, as must the target,
    provenance, retained collection bytes and the last history entry's delta bytes.
    Any subsequent input, generator, collection or evidence drift fails closed.
    """
    retained = row.get('retained_collection')
    keys = {'generated_operad_collection_sha256', 'operad_delta', 'operad_delta_sha256'}
    if not isinstance(retained, dict) or set(retained) != keys:
        return False
    generated = {k: v for k, v in row.items() if k != 'retained_collection'}
    generated['operad_collection_sha256'] = retained['generated_operad_collection_sha256']
    if generated != built['audit']:
        return False
    prompt, operad = corpus.root / row['prompt'], corpus.root / row['operad_collection']
    if not prompt.is_file() or prompt.read_bytes() != built['prompt_bytes'] or not operad.is_file():
        return False
    data = operad.read_bytes()
    if sha(data) != row['operad_collection_sha256']:
        return False
    actual, original = load_yaml(data), load_yaml(built['operad_bytes'])
    if not isinstance(actual, dict):
        return False
    identity = ('schema_id', 'node_id', 'authority_effect', 'collection_status', 'target', 'source_provenance')
    if any(actual.get(k) != original[k] for k in identity):
        return False
    history = actual.get('stage_history')
    if not isinstance(history, list) or not history or not isinstance(history[-1], dict):
        return False
    relative = retained['operad_delta']
    if not isinstance(relative, str) or relative != history[-1].get('operad_delta'):
        return False
    evidence = (corpus.root / relative).resolve()
    runs = (corpus.root / 'dag/results' / row['node_id'] / 'runs').resolve()
    if not evidence.is_relative_to(runs) or not evidence.is_file():
        return False
    return sha(evidence.read_bytes()) == retained['operad_delta_sha256']


def classify(corpus: Corpus, node):
    """missing / current / stale / executed_stale / sealed for one node."""
    node_id = node['id']
    if node_id in corpus.base_ids:
        return 'sealed', None, []
    row = corpus.ext_rows.get(node_id)
    if row is None:
        return ('foreign' if corpus.has_prompt(node_id) else 'missing'), None, []
    built = build_node(corpus, node, row['prompt'])
    on_disk = corpus.root / row['prompt']
    operad = corpus.root / row['operad_collection']
    same = (on_disk.is_file() and on_disk.read_bytes() == built['prompt_bytes'] and operad.is_file() and
            operad.read_bytes() == built['operad_bytes'] and row == built['audit'])
    if same or retained_collection_matches(corpus, row, built):
        return 'current', built, []
    reasons = stale_reasons(row.get('inputs', {}), built['inputs']) or ['generator_output_or_file_changed']
    return ('executed_stale' if corpus.executed(node_id) else 'stale'), built, reasons


def select_nodes(corpus: Corpus, ids, all_missing):
    if ids:
        unknown = [i for i in ids if i not in corpus.by_id]
        if unknown:
            raise ValueError('unknown node ids: ' + ', '.join(unknown))
        return [corpus.by_id[i] for i in sorted(set(ids), key=corpus.position.get)]
    if all_missing:
        return corpus.missing() + [n for n in corpus.nodes if n['id'] in corpus.ext_rows]
    return []


def plan(corpus: Corpus, nodes):
    report = {'create': [], 'current': [], 'stale': [], 'executed_stale': [], 'sealed': [], 'foreign': []}
    for node in nodes:
        state, built, reasons = classify(corpus, node)
        if state == 'missing':
            report['create'].append((node, build_node(corpus, node), []))
        else:
            report[state].append((node, built, reasons))
    return report


def collision_check(corpus: Corpus, built_nodes):
    """No two generated nodes share a file name, and none takes a file another node owns."""
    owner = {}
    for built in built_nodes:
        for key in (built['prompt_path'], built['operad_path']):
            if owner.setdefault(key, built['node_id']) != built['node_id']:
                raise ValueError('file name collision: %s for %s and %s' % (key, owner[key], built['node_id']))
            existing = corpus.root / key
            if existing.is_file() and load_yaml(existing.read_bytes()).get('node_id') != built['node_id']:
                raise ValueError('file name collision: %s already belongs to another node' % key)


def merged_index(corpus: Corpus, fresh):
    """Sealed head untouched; executed generated rows first; the rest in (tier, DAG) order."""
    sealed = set(corpus.base_ids)
    head = [row for row in corpus.index['nodes'] if row['node_id'] in sealed]
    generated = {nid: corpus.index_rows[nid] for nid in corpus.ext_rows if nid in corpus.index_rows}
    generated.update(fresh)
    stray = [r['node_id'] for r in corpus.index['nodes'] if r['node_id'] not in sealed and r['node_id'] not in generated]
    if stray:
        raise ValueError('index holds rows that are neither sealed nor generated: ' + ', '.join(stray[:5]))
    tiers = {nid: tier_of(corpus.by_id[nid]['status']) for nid in generated}
    ran = [r['node_id'] for r in corpus.index['nodes'] if r['node_id'] in generated and corpus.executed(r['node_id'])]
    rest = sorted((nid for nid in generated if nid not in set(ran)), key=lambda nid: (tiers[nid], corpus.position[nid]))
    return head + [generated[nid] for nid in ran + rest]


def write_changes(corpus: Corpus, report):
    """Write files for new and stale (not yet run) prompts; return the new extension and index."""
    todo = report['create'] + report['stale']
    collision_check(corpus, [built for _, built, _ in todo])
    rows = dict(corpus.ext_rows)
    fresh = {}
    written = Counter()
    for node, built, _ in todo:
        for rel, data in ((built['prompt_path'], built['prompt_bytes']), (built['operad_path'], built['operad_bytes'])):
            target = corpus.root / rel
            if not (target.is_file() and target.read_bytes() == data):
                atomic_write(target, data)
        rows[node['id']] = built['audit']
        fresh[node['id']] = built['index']
        written['rewritten' if node['id'] in corpus.ext_rows else 'created'] += 1
    ordered = sorted(rows, key=corpus.position.get)
    extension = {'schema_id': EXTENSION_SCHEMA, 'authority_effect': 'None', 'generator': 'dag/pfp/generate_prompts.py',
                 'generator_version': GENERATOR_VERSION, 'dag_source_commit': corpus.dag.get('source_commit'),
                 'base_audit_sha256': sha((corpus.root / 'dag/pfp/prompt_audit.json').read_bytes()),
                 'tier_order': {'A': list(TIER_A), 'B': list(TIER_B), 'C': list(TIER_C)},
                 'prompts_reviewed': len(ordered),
                 'claim_boundary': ('Generated source-candidate collections for nodes that had no prompt. This audit binds '
                                    'prompt digests and generation inputs; it does not certify any source claim or '
                                    'complete semantic operad mining.'),
                 'nodes': [rows[nid] for nid in ordered]}
    index = dict(corpus.index)
    corpus.ext_rows = rows
    index['nodes'] = merged_index(corpus, fresh)
    return written, extension, index


# ---------------------------------------------------------------- reporting
def target_statement(path: Path):
    """source_statement of an operad record, parsed from its head (the target precedes the long lists)."""
    data = path.read_bytes()
    cut = data.find(b'\nsource_provenance:')
    head = data if cut < 0 else data[:cut + 1]
    return load_yaml(head)['target']['source_statement']


def summarize(corpus: Corpus, report):
    by_stage_tier = Counter()
    by_stage, by_tier = Counter(), Counter()
    for node, built, _ in report['create']:
        tier = tier_of(node['status'])
        by_stage_tier[(node['stage'], tier)] += 1
        by_stage[node['stage']] += 1
        by_tier[tier] += 1
    drift = []
    for node in corpus.nodes:
        if node['id'] in corpus.base_ids:
            row = corpus.index_rows.get(node['id'])
            if row:
                if target_statement(corpus.root / row['operad_collection']) != node['statement']:
                    drift.append(node['id'])
    return {
        'would_create': len(report['create']), 'by_tier': dict(sorted(by_tier.items())),
        'by_stage': dict(sorted(by_stage.items())),
        'by_stage_and_tier': {s + '/' + t: n for (s, t), n in sorted(by_stage_tier.items())},
        'current': len(report['current']), 'stale': {n['id']: r for n, _, r in report['stale']},
        'executed_stale_needs_manual_delta': {n['id']: r for n, _, r in report['executed_stale']},
        'sealed_prompts_whose_dag_statement_drifted': drift,
        'prompts_not_owned_by_this_generator_or_the_sealed_audit': [n['id'] for n, _, _ in report['foreign']],
        'with_no_operation_or_relation_candidate': sum(
            1 for _, b, _ in report['create'] if not b['audit']['operation_candidates'] and not b['audit']['relation_candidates']),
        'with_paper_pins': sum(1 for _, b, _ in report['create'] if b['inputs']['paper_pins']),
        'operation_candidates': sum(b['audit']['operation_candidates'] for _, b, _ in report['create']),
        'relation_candidates': sum(b['audit']['relation_candidates'] for _, b, _ in report['create'])}


def run(root, check, write, ids, all_missing, require_complete=False, out=sys.stdout):
    corpus = Corpus(root)
    nodes = select_nodes(corpus, ids, all_missing)
    report = plan(corpus, nodes)
    summary = summarize(corpus, report)
    if check:
        out.write(json.dumps(summary, indent=2, sort_keys=True) + '\n')
        bad = bool(summary['stale'] or summary['executed_stale_needs_manual_delta'])
        if require_complete and summary['would_create']:
            bad = True
        return 1 if bad else 0
    if write:
        if not nodes:
            raise ValueError('--write needs --nodes or --all-missing')
        if report['executed_stale']:
            out.write('refusing to rewrite executed prompts: ' + ', '.join(n['id'] for n, _, _ in report['executed_stale']) + '\n')
        written, extension, index = write_changes(corpus, report)
        atomic_write(corpus.root / EXTENSION_PATH, dump_json(extension))
        atomic_write(corpus.index_path, dump_json(index))
        out.write(json.dumps({'created': written['created'], 'rewritten': written['rewritten'],
                              'unchanged': len(report['current'])}) + '\n')
        return 0
    raise ValueError('choose --check or --write')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='report what would be created and which generated prompts are stale')
    mode.add_argument('--write', action='store_true', help='write prompts, operads, audit extension and index rows')
    target = parser.add_mutually_exclusive_group()
    target.add_argument('--nodes', nargs='+', metavar='ID')
    target.add_argument('--all-missing', action='store_true')
    parser.add_argument('--root', type=Path, default=REPO, help='tree to read and write (default: this repository)')
    parser.add_argument('--require-complete', action='store_true', help='with --check, fail while any node lacks a prompt')
    args = parser.parse_args(argv)
    return run(args.root, args.check, args.write, args.nodes, args.all_missing, args.require_complete)


if __name__ == '__main__':
    raise SystemExit(main())
