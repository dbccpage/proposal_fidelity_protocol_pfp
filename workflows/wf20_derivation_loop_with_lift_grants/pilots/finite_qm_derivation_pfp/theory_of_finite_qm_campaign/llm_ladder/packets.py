"""Compile a staged PFP prompt into a compact, typed OEPFP-style packet with a closed response schema.

AuthorityEffect: None.

The staged prompt (dag/prompts/*.yaml + dag/pfp/prepare_stage.py) is prose a human or a large model can
read. The compiled packet keeps only what the model needs to fill the P0 operad slots:
  @TARGET/@BOTTLENECK/@ASSUME  the public input (statement, bottleneck, declared assumptions);
  @SRC                         declarations the host already found, the ONLY ones citable as existing;
  @KNOWN+ / @KNOWN-            verified entries and host-refused entries of this node and its DAG neighbours;
  @FILL                        the typed slots to fill, enforced by a JSON schema (generators, relations,
                               compositions, lemmas, near_misses, numeric_claims, open_obligations).
This is the OEPFP idea "slot filling instead of free prose": the reply is short, typed and checkable.
Binding (task id, stage, attempt, input digest) follows prepare_stage.build_packet.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .llm_common import canonical_json, sha256_bytes
from .memory import (HallucinationIndex, dag_neighbours, dag_node, format_negative, format_positive, index_path,
                     positive_entries)
from .verify import DeclIndex

LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)

_S = {'type': 'string'}
_REF = {'type': 'object', 'additionalProperties': False, 'required': ['path', 'decl', 'status'],
        'properties': {'path': _S, 'decl': _S, 'status': {'type': 'string', 'enum': ['existing', 'proposed_new', 'none']}}}


def _obj(required, properties):
    return {'type': 'object', 'additionalProperties': False, 'required': required, 'properties': properties}


P0_SCHEMA = _obj(
    ['status', 'generators', 'relations', 'compositions', 'lemmas', 'near_misses', 'numeric_claims', 'open_obligations'],
    {
        'status': {'type': 'string', 'enum': ['incomplete', 'ready_for_host_review']},
        'generators': {'type': 'array', 'items': _obj(
            ['id', 'inputs', 'output', 'arity', 'carrier', 'ref'],
            {'id': _S, 'inputs': {'type': 'array', 'items': _S}, 'output': _S, 'arity': {'type': 'integer'},
             'carrier': _S, 'ref': _REF})},
        'relations': {'type': 'array', 'items': _obj(
            ['id', 'statement', 'hypotheses', 'ref'],
            {'id': _S, 'statement': _S, 'hypotheses': _S, 'ref': _REF})},
        'compositions': {'type': 'array', 'items': _obj(
            ['outer', 'slot', 'inner', 'licensing_relation'],
            {'outer': _S, 'slot': {'type': 'integer'}, 'inner': _S, 'licensing_relation': _S})},
        'lemmas': {'type': 'array', 'items': _obj(
            ['id', 'statement', 'relation_to_target', 'depends_on', 'lean_skeleton', 'claims_proved', 'ref'],
            {'id': _S, 'statement': _S,
             'relation_to_target': {'type': 'string', 'enum': ['restates', 'implies', 'auxiliary', 'strengthens', 'weakens']},
             'depends_on': {'type': 'array', 'items': _S}, 'lean_skeleton': _S, 'claims_proved': {'type': 'boolean'},
             'ref': _REF})},
        'near_misses': {'type': 'array', 'items': _obj(
            ['id', 'claim', 'rejecting_invariant'], {'id': _S, 'claim': _S, 'rejecting_invariant': _S})},
        'numeric_claims': {'type': 'array', 'items': _obj(
            ['id', 'expr', 'value'], {'id': _S, 'expr': _S, 'value': _S})},
        'open_obligations': {'type': 'array', 'items': _S},
    })

def schema_example(schema, name='value'):
    """A literal skeleton of a schema: strings become <key>, enums list their values with |, integers 0, booleans false, and
    every array holds one example item. Put in the system text so that a provider that ignores `response_format` still shows
    the model the exact keys."""
    kind = schema.get('type')
    if kind == 'object':
        return {key: schema_example(sub, key) for key, sub in schema.get('properties', {}).items()}
    if kind == 'array':
        return [schema_example(schema.get('items', {}), name)]
    if 'enum' in schema:
        return '|'.join(str(v) for v in schema['enum'])
    return {'integer': 0, 'boolean': False}.get(kind, '<%s>' % name)


_SYSTEM_P0_RULES = (
    'You mine operad entries for ONE finite quantum mechanics target. Reply with ONE JSON object that matches '
    'the response schema. No prose, no code fences.\n'
    'Rules:\n'
    '- Cite a declaration with status "existing" ONLY if it is listed under @SRC or @KNOWN+. Otherwise use '
    'status "proposed_new" (or "none") and leave path empty. Never invent a file path or a declaration name.\n'
    '- The host greps every existing citation, recomputes every numeric_claim exactly, and elaborates every '
    'Lean skeleton. Each refused claim is recorded against your model name.\n'
    '- Declarations marked [test] are checkers, not operations: cite them only inside a relation or lemma, never as a generator.\n'
    '- generator: a typed operation. inputs = ordered colour names, output = one colour, arity = len(inputs).\n'
    '- composition: plug generator `inner` into input slot `slot` (0-based) of generator `outer`. The inner output '
    'colour must equal that input colour and a relation you listed must license the step.\n'
    '- lemma: relation_to_target is restates|implies|auxiliary|strengthens|weakens. Do not change a number of '
    'the target. Set lean_skeleton to "" when you have no formal statement: never write a placeholder such as `: True`. '
    'A skeleton may use sorry; set claims_proved true only for a sorry-free proof. A lemma that restates the target and '
    'cites the existing declaration that proves it is a good lemma.\n'
    '- numeric_claims: exact rational arithmetic only, e.g. expr "11 - 2/3*5", value "23/3". They are recomputed and a '
    'false one is refused, but a correct one earns no credit: acceptance needs grounded generators, relations, compositions '
    'or lemmas.\n'
    '- Prefer 2-6 well-grounded entries per array over many guesses. Every key below is required; an empty slot is []. '
    'List what you could not ground in open_obligations. AuthorityEffect: None.\n'
)
SYSTEM_P0 = (_SYSTEM_P0_RULES + 'Reply shape (angle brackets mark where your value goes; a | lists the allowed values):\n'
             + json.dumps(schema_example(P0_SCHEMA), separators=(',', ':'), ensure_ascii=False))


@dataclass
class CompiledPacket:
    node_id: str
    stage: str
    attempt_id: str
    system: str
    user: str
    schema: dict
    input_sha256: str
    meta: dict = field(default_factory=dict)
    target_statement: str = ''
    allowed_refs: set | None = None
    credited_paths: set | None = None

    def estimated_tokens(self) -> int:
        return estimate_tokens(self.system + self.user + json.dumps(self.schema))

    def as_request_json(self) -> dict:
        return {'schema_id': 'omega.pfp.finite-qm.ladder-packet.v1', 'task_id': self.node_id, 'stage_id': 'P0_MINE_OPERAD',
                'attempt_id': self.attempt_id, 'input_sha256': self.input_sha256, 'authority_effect': 'None',
                'system_prompt': self.system, 'user_prompt': self.user, 'response_schema': self.schema,
                'meta': self.meta, 'dispatch_status': 'prepared_by_llm_ladder'}


def estimate_tokens(text: str) -> int:
    return int(len(text.encode('utf-8')) / 3.5) + 1


STOP = {'the', 'and', 'for', 'with', 'that', 'this', 'from', 'into', 'are', 'not', 'its', 'rat', 'one', 'two', 'all',
        'any', 'has', 'have', 'than', 'when', 'which', 'does', 'state', 'record', 'records', 'value', 'values', 'identity',
        'identities', 'finite', 'rational', 'exact', 'map', 'research', 'file', 'report', 'source', 'theorem', 'lemma',
        'def', 'nf', 'nc', 'at', 'of', 'in', 'to', 'by', 'is', 'as', 'on', 'or', 'an', 'no', 'it', 'be'}


def _tokens(text: str) -> set:
    parts = re.findall(r'[A-Za-z][a-z]+|[A-Z]+(?![a-z])|\d+', re.sub(r'([a-z])([A-Z])', r'\1 \2', text or ''))
    return {p.lower() for p in parts if len(p) > 2 and not p.isdigit() and p.lower() not in STOP}


def load_row(root, node_id):
    rows = json.loads((Path(root) / 'dag/operads/index.json').read_bytes().decode('utf-8'))['nodes']
    for position, row in enumerate(rows):
        if row['node_id'] == node_id:
            return position, row
    raise KeyError('node %s is not in dag/operads/index.json' % node_id)


GENERIC_FILE_NAMES = {'mod.rs', 'lib.rs', 'main.rs', '__init__.py', 'conftest.py'}
FILE_NAME = re.compile(r'(?<![\w/.-])((?:[\w.-]+/)*[\w.-]+\.(?:lean|rs|py))\b')
IDENTIFIER = re.compile(r'[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+|[a-z]+[A-Z][A-Za-z0-9]*')
# A word that occurs in the stem of more than this many source files ("test", "omega", "contract", "genesis"...) says nothing
# about which file a statement is about.
STEM_DOC_FREQUENCY_LIMIT = 300   # in this repo: drops contract, omega, test(s), math, wdp, mub, quantum, theory, physics; keeps primitive, boundary, genesis
STRUCTURAL_STEM_STOP = {'boundary', 'contract', 'primitive', 'genesis', 'engine', 'lattice', 'manifold', 'gauge',
                        'sector', 'state', 'system', 'model', 'verify', 'check', 'audit', 'test', 'tests'}
MAX_FILE_CANDIDATES = 4        # a bare file name that resolves to more files than this is too ambiguous to offer
NAMED_FILE_DECLS = 10


def anchor_path(anchor: str) -> str:
    """`path:12-40` / `path#L3` -> `path`, with POSIX separators."""
    return re.split(r'[:#]', str(anchor).strip().replace('\\', '/'))[0]


def _distinctive(index: DeclIndex, tokens: set) -> set:
    frequency = getattr(index, '_stem_frequency', None)
    if frequency is None:
        frequency = {}
        for path in index.source_paths():
            for token in _tokens(Path(path).stem):
                frequency[token] = frequency.get(token, 0) + 1
        index._stem_frequency = frequency
    return {t for t in tokens if t not in STRUCTURAL_STEM_STOP and frequency.get(t, 0) <= STEM_DOC_FREQUENCY_LIMIT}


def named_files(index: DeclIndex, text: str, preferred=()) -> list:
    """Repository paths of the source files that `text` names (`obstruction.rs`, `lean4/Foo.lean`, `a/b/c.py`). A bare name
    that resolves to more than MAX_FILE_CANDIDATES files is kept only where it matches one of the `preferred` paths."""
    found = []
    for name in dict.fromkeys(FILE_NAME.findall(text or '')):
        base = name.rsplit('/', 1)[-1]
        if base in GENERIC_FILE_NAMES:
            continue
        paths = index.paths_by_basename().get(base, [])
        if '/' in name:
            paths = [p for p in paths if p == name or p.endswith('/' + name)] or paths
        if len(paths) > MAX_FILE_CANDIDATES:
            paths = [p for p in paths if p in preferred]
        found += paths
    return list(dict.fromkeys(found))


def node_code_text(node: dict) -> str:
    """The node's own anchors and source pointers as one string, for file-name resolution."""
    parts = [a for key in ('lean', 'rust', 'python', 'source') for a in (node.get(key) or []) if isinstance(a, str)]
    return '\n'.join(anchor_path(a) for a in parts)


def source_candidates(root, node_id, collection, index: DeclIndex, statement: str, limit: int, bottleneck: str = ''):
    """[(score, path, decl dict)] best first: operad-record leads; names (files and identifiers) quoted in the statement or the
    bottleneck; the node's own anchors; then declarations of source files whose file name shares DISTINCTIVE words with the
    statement. Nothing below a relevance floor is offered: an empty list is a result ("@SRC none")."""
    chosen: dict = {}

    def offer(score, path, decl):
        key = (path, decl['full'])
        if key not in chosen or chosen[key][0] < score:
            chosen[key] = (score, path, decl)

    text = '%s\n%s' % (statement or '', bottleneck or '')
    for item in (collection.get('operation_candidates') or []) + (collection.get('relation_candidates') or []):
        path = item.get('source')
        entry = index.file_entry(path) if path else None
        if entry:
            for decl in index.match_in_table(entry['table'], item['name']):
                offer(100, path, decl)
    node = dag_node(root, node_id) or {}
    statement_tokens = _tokens(text)
    distinct_tokens = _distinctive(index, statement_tokens)
    for name in set(IDENTIFIER.findall(text)):
        for path, decl in index.find_anywhere(name):
            if decl['full'].split('.')[-1] == name:
                offer(90, path, decl)
    anchors = [anchor_path(a) for a in (node.get('lean') or []) + (node.get('rust') or []) if a]

    def offer_file(path, scores):
        """Declarations of one file, those sharing words with the statement first; `scores` = (>=2 shared, 1 shared, none)."""
        entry = index.file_entry(path)
        table = entry['table'] if entry else []
        ranked = sorted(((len(_tokens(d['full']) & statement_tokens), d) for d in table), key=lambda row: (-row[0], row[1]['line']))
        shared = [(n, d) for n, d in ranked if n >= 1][:NAMED_FILE_DECLS]
        for n, d in shared or ranked[:5]:
            offer(scores[0] + min(n, 5) if n >= 2 else (scores[1] if n == 1 else scores[2]), path, d)

    named = named_files(index, text + '\n' + node_code_text(node), preferred=set(anchors))
    for path in named:
        offer_file(path, (85, 80, 70))
    for anchor in anchors:
        if index.file_entry(anchor):
            offer_file(anchor, (40, 30, 20))
    if len(chosen) < limit:
        by_file = []
        for path in index.source_paths():
            stem_tokens = _distinctive(index, _tokens(Path(path).stem))
            overlap = len(stem_tokens & distinct_tokens)
            is_test = '/tests/' in path or Path(path).name.startswith('test_')
            if overlap >= (3 if is_test else 2) and path not in anchors and path not in named:
                by_file.append((overlap - (1 if is_test else 0), path))
        for overlap, path in sorted(by_file, reverse=True)[:6]:
            entry = index.file_entry(path)
            for decl in (entry['table'] if entry else []):
                hit = len(_tokens(decl['full']) & distinct_tokens)
                if hit >= 1:
                    offer(min(10 + overlap + hit, STRONG_SCORE - 1), path, decl)   # stays below every strong tier
    ranked = sorted(chosen.values(), key=lambda row: (-row[0], row[1], row[2]['line']))
    return ranked[:limit]


# Statuses whose subject is an external publication or an imported theorem: when the host found nothing but fuzzy
# file-name matches for them, there is no code the claim could be grounded on.
EXTERNAL_SUBJECT_STATUSES = ('SOURCE_RECORD', 'IMPORTED_ASSUMPTION')
FINITE_TARGET_MARK = 'Finite statement to formalize'
STRONG_SCORE = 20      # operad lead, quoted identifier, named file or node anchor; below it is a fuzzy file-name match


def groundability(root, node_id, collection, index: DeclIndex, statement: str, bottleneck: str, src_offered: int,
                  src_strong: int = None, known_pos: int = 0) -> dict:
    """Facts for the pre-dispatch skip: operation/relation candidates, code files the node names or anchors that exist in this
    checkout, and the reason when there is nothing to ground a claim on.

    Ungroundable = no operation/relation candidates, no code anchor or named file present in the checkout, and either no `@SRC`
    at all, or (for SOURCE_RECORD / IMPORTED_ASSUMPTION nodes only) nothing but fuzzy file-name matches. A finite target
    ("Finite statement to formalize") is never skipped: its job is to state an exact finite claim, which the numeric and lemma
    slots can address before any code exists."""
    node = dag_node(root, node_id) or {}
    candidates = len(collection.get('operation_candidates') or []) + len(collection.get('relation_candidates') or [])
    anchors = [anchor_path(a) for a in (node.get('lean') or []) + (node.get('rust') or []) if a]
    present = [p for p in dict.fromkeys(anchors) if (Path(root) / p).is_file()]
    present += [p for p in named_files(index, '%s\n%s\n%s' % (statement or '', bottleneck or '', node_code_text(node)), preferred=set(anchors))
                if p not in present]
    strong = src_offered if src_strong is None else src_strong
    status = node.get('status')
    finite_target = FINITE_TARGET_MARK in ((node.get('statement') or '') + (statement or ''))
    no_sources = src_offered == 0
    only_fuzzy = strong == 0 and status in EXTERNAL_SUBJECT_STATUSES
    # @KNOWN+ lines (host-verified entries of this node's DAG neighbours) are citable too: 23 of the 98 Sonnet runs of round 2 that
    # had an empty @SRC were accepted with 2 or more verified citations, all of them through @KNOWN+.
    ungroundable = candidates == 0 and not present and not known_pos and (no_sources or only_fuzzy) and not finite_target
    reason = None
    if ungroundable:
        reason = ('no operation or relation candidates, no code file named by the statement or anchored by the node exists in '
                  'this checkout, and ' + ('no @SRC declaration was found' if no_sources else
                                           'the only @SRC offered are fuzzy file-name matches for a %s node' % status))
    return {'operation_candidates': candidates, 'anchors_present': len(present), 'src_strong': strong,
            'finite_target': finite_target, 'ungroundable': ungroundable, 'ungroundable_reason': reason}


def compile_p0(root, node_id, *, attempt_id, policy, index: DeclIndex | None = None, feedback=True,
               hallucinations: HallucinationIndex | None = None) -> CompiledPacket:
    root = Path(root)
    index = index or DeclIndex(root)
    position, row = load_row(root, node_id)
    collection = yaml.load((root / row['operad_collection']).read_bytes(), Loader=LOADER)
    target = collection['target']
    statement = target['source_statement']
    status = (dag_node(root, node_id) or {}).get('status', target.get('source_claim_label', '?'))
    assumptions = target.get('declared_assumptions') or []
    neighbours = dag_neighbours(root, node_id)
    related = [node_id] + neighbours
    bottleneck_text = target.get('source_bottleneck', '') or ''
    candidates = source_candidates(root, node_id, collection, index, statement, policy['max_source_candidates'], bottleneck_text)
    hall =hallucinations or HallucinationIndex(index_path(root))
    negatives, positives = [], []
    if feedback:
        hints = {p + '::' + d['full'] for _, p, d in candidates} | {d['full'] for _, _, d in candidates}
        negatives = hall.relevant(related, hints, limit=policy['max_neg_lines'],
                                  still_absent=lambda key: not index.find_anywhere(key))
        positives = positive_entries(root, related, limit=policy['max_pos_lines'])
    lines = []
    src_lines = []
    for rank, (score, path, decl) in enumerate(candidates):
        is_test = '/tests/' in path or Path(path).name.startswith('test_') or decl['name'].startswith('test_')
        text = '%s | %s | %s%s' % (path, decl['full'], decl['kind'], ' [test]' if is_test else '')
        if rank < 8:
            signature = re.sub(r'\s+', ' ', index.statement(path, decl))[:150]
            text += ' | ' + signature
        src_lines.append(' ' + text)
    public = {'task_id': node_id, 'stage': 'P0', 'attempt_id': attempt_id, 'statement': statement,
              'bottleneck': target.get('source_bottleneck', ''), 'assumptions': assumptions,
              'src': [l.strip() for l in src_lines], 'known_neg': [format_negative(e) for e in negatives],
              'known_pos': [format_positive(r) for r in positives]}
    digest = sha256_bytes(canonical_json(public))
    lines.append('@PFP/1 task=%s stage=P0 attempt=%s in=%s guided=%s' % (node_id, attempt_id, digest[:8], 'yes' if feedback else 'no'))
    lines.append('@TARGET [%s] %s' % (status, re.sub(r'\s+', ' ', statement).strip()))
    if public['bottleneck']:
        lines.append('@BOTTLENECK ' + re.sub(r'\s+', ' ', public['bottleneck']).strip())
    lines.append('@ASSUME ' + ('; '.join(assumptions) if assumptions else 'none declared'))
    lines.append('@SRC path | decl | kind | signature (copy path and the bare decl name into ref.path and ref.decl, never the signature text; cite as existing only from here)' if src_lines else '@SRC none found by the host; cite nothing as existing')
    lines += src_lines
    if public['known_pos']:
        lines.append('@KNOWN+ (host-verified earlier; reusable inside their scope)')
        lines += [' ' + x for x in public['known_pos']]
    if public['known_neg']:
        lines.append('@KNOWN- (host-refused earlier; do not repeat)')
        lines += [' ' + x for x in public['known_neg']]
    lines.append('@FILL generators relations compositions lemmas near_misses numeric_claims open_obligations status')
    meta = {'src_offered': len(src_lines), 'known_neg_injected': len(negatives), 'known_pos_injected': len(positives),
            'neighbours': neighbours[:12], 'feedback': feedback, 'index_position': position,
            'neg_entry_ids': [e['id'] for e in negatives]}
    meta.update(groundability(root, node_id, collection, index, statement, bottleneck_text, len(src_lines),
                              sum(1 for score, _, _ in candidates if score >= STRONG_SCORE), len(positives)))
    node_obj = dag_node(root, node_id) or {}
    anchors = [anchor_path(a) for a in (node_obj.get('lean') or []) + (node_obj.get('rust') or []) + (node_obj.get('python') or []) if a]
    named = named_files(index, '%s\n%s\n%s' % (statement or '', bottleneck_text or '', node_code_text(node_obj)), preferred=set(anchors))
    cand_sources = [item.get('source') for item in (collection.get('operation_candidates') or []) + (collection.get('relation_candidates') or []) if item.get('source')]
    credited_paths = {p for _, p, _ in candidates} | set(anchors) | set(named) | set(cand_sources)
    allowed_refs = {(p, d['full']) for _, p, d in candidates} | {(p, d['name']) for _, p, d in candidates}
    for p in set(anchors) | set(named) | set(cand_sources):
        for d in (index.file_entry(p) or {}).get('table', []):
            allowed_refs.add((p, d['full']))
            allowed_refs.add((p, d['name']))
    for row_pos in positives:
        ev = (row_pos.get('item') or {}).get('host_evidence') or {}
        ev_p, ev_d = ev.get('path'), ev.get('decl')
        if ev_p and ev_d:
            allowed_refs.add((ev_p, ev_d))
            allowed_refs.add((ev_p, ev_d.split('.')[-1]))
            if row_pos.get('node_id') == node_id:
                credited_paths.add(ev_p)
    return CompiledPacket(node_id, 'P0', attempt_id, SYSTEM_P0, '\n'.join(lines) + '\n', P0_SCHEMA, digest, meta, statement,
                          allowed_refs=allowed_refs, credited_paths=credited_paths)


def staged_baseline_tokens(root, node_id) -> int | None:
    """Token estimate of the packet the file-only prepare_stage helper produces for the same node (for comparison)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location('pfp_prepare_stage', Path(root) / 'dag/pfp/prepare_stage.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _, row = load_row(root, node_id)
        packet = module.build_packet(Path(root) / row['prompt'], 'P0_MINE_OPERAD', attempt_id='baseline')
        text = json.dumps({k: packet[k] for k in ('system_prompt', 'user_prompt', 'public_context', 'response_contract')})
        return estimate_tokens(text)
    except Exception:  # baseline is informational only
        return None
