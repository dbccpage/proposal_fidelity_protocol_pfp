"""Operad memory for the ladder: the shared hallucination index and the positive (verified) entries.

AuthorityEffect: None.

dag/operads/_hallucination_index.json is a repository-wide set of NEGATIVE operad entries. Each is a
failed_composition or a counterexample (docs: stage_contracts.yaml operad_delta) recorded when the host
refused a model claim, with the model name, the claim and the evidence, keyed two ways:
  by_declaration       decl key (a cited name or path::name)  -> entry ids
  by_claim_pattern     normalised claim pattern                -> entry ids
Before a call the compiler injects the entries that concern the node or its DAG neighbours, plus any
whose declaration key is among the sources offered to the model. A negative entry about a name that
now exists is dropped at injection time (an index entry is evidence about the repository on the day it
was recorded, not a permanent verdict).

Positive entries are the host-verified generators and relations that earlier ladder runs wrote into
dag/results/<NODE>/runs/*_ladder/p0/operad_delta.yaml.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from .llm_common import FileLock, atomic_write, json_bytes, sha256_text, utc_iso

SCHEMA_ID = 'omega.pfp.hallucination-index.v1'
LOADER = getattr(yaml, 'CSafeLoader', yaml.SafeLoader)
_DAG_CACHE: dict = {}


def index_path(root) -> Path:
    return Path(root) / 'dag' / 'operads' / '_hallucination_index.json'


def _empty():
    return {'schema_id': SCHEMA_ID, 'authority_effect': 'None',
            'claim': ('Negative operad entries: model claims the host refused. Not mathematics and not an '
                      'exhaustive list; an entry is evidence about the repository on the date recorded.'),
            'entries': {}, 'by_declaration': {}, 'by_claim_pattern': {}}


def entry_id(cls: str, pattern: str) -> str:
    return 'NEG-' + sha256_text(cls + '|' + pattern)[:12].upper()


class HallucinationIndex:
    def __init__(self, path):
        self.path = Path(path)

    def load(self) -> dict:
        if self.path.is_file():
            data = json.loads(self.path.read_bytes().decode('utf-8'))
            if data.get('schema_id') != SCHEMA_ID:
                raise ValueError('hallucination index has an unknown schema_id')
            return data
        return _empty()

    def add_failures(self, failures, *, node_id, run_id, attempt_id, model, provider, tier, when=None):
        """Merge failures into the index. Returns the entry dicts (as stored) for the receipt."""
        when = when or utc_iso()
        stored = []
        with FileLock(self.path):
            data = self.load()
            for failure in failures:
                pattern = failure.pattern
                eid = entry_id(failure.cls, pattern)
                entry = data['entries'].get(eid)
                if entry is None:
                    entry = {'id': eid, 'entry_type': failure.entry_type, 'class': failure.cls,
                             'claim_kind': failure.claim_kind, 'claim': failure.claim[:400], 'evidence': failure.evidence[:400],
                             'decl_key': failure.decl_key, 'claim_pattern': pattern, 'confidence': failure.confidence,
                             'forbidden_move': forbidden_move(failure), 'first_seen_utc': when,
                             'occurrences': 0, 'models': [], 'nodes': [], 'authority_effect': 'None'}
                    data['entries'][eid] = entry
                entry['occurrences'] += 1
                entry['last_seen_utc'] = when
                for key, value in (('models', model), ('nodes', node_id)):
                    if value not in entry[key]:
                        entry[key].append(value)
                        entry[key].sort()
                entry['last'] = {'node_id': node_id, 'run_id': run_id, 'attempt_id': attempt_id, 'provider': provider,
                                 'model': model, 'tier': tier}
                if failure.decl_key:
                    ids = data['by_declaration'].setdefault(failure.decl_key, [])
                    if eid not in ids:
                        ids.append(eid)
                        ids.sort()
                ids = data['by_claim_pattern'].setdefault(pattern, [])
                if eid not in ids:
                    ids.append(eid)
                    ids.sort()
                stored.append(dict(entry))
            data['entries'] = dict(sorted(data['entries'].items()))
            data['by_declaration'] = dict(sorted(data['by_declaration'].items()))
            data['by_claim_pattern'] = dict(sorted(data['by_claim_pattern'].items()))
            if failures:
                atomic_write(self.path, json_bytes(data))
        return stored

    def relevant(self, node_ids, decl_hints=(), *, limit=12, still_absent=None):
        """Entries for these nodes or declaration keys, most useful first. `still_absent(key)` re-checks names."""
        data = self.load()
        nodes, hints = set(node_ids), {h for h in decl_hints if h}
        scored = []
        for entry in data['entries'].values():
            on_node = bool(nodes & set(entry.get('nodes', [])))
            on_decl = entry.get('decl_key') in hints
            if not (on_node or on_decl):
                continue
            if entry['class'] == 'nonexistent_declaration' and entry.get('decl_key') and still_absent is not None \
                    and not still_absent(entry['decl_key']):
                continue
            scored.append(((0 if on_node else 1), -entry.get('occurrences', 1), entry.get('last_seen_utc', ''), entry))
        scored.sort(key=lambda row: (row[0], row[1], row[2]))
        return [row[3] for row in scored[:limit]]

    def stats(self) -> dict:
        data = self.load()
        classes: dict = {}
        models: dict = {}
        for entry in data['entries'].values():
            classes[entry['class']] = classes.get(entry['class'], 0) + entry['occurrences']
            for model in entry.get('models', []):
                models[model] = models.get(model, 0) + 1
        return {'entries': len(data['entries']), 'by_class': dict(sorted(classes.items())),
                'models': dict(sorted(models.items()))}


def forbidden_move(failure) -> str:
    templates = {
        'nonexistent_declaration': 'Do not cite %s as an existing declaration.',
        'wrong_source_location': 'Do not cite %s at that path; see the evidence for where it lives.',
        'wrong_signature': 'Do not state that arity/signature for %s.',
        'statement_drift': 'Do not restate the source with numerals it does not contain.',
        'false_numeric_claim': 'Do not assert that value; the exact recomputation differs.',
        'vacuous_proof': 'Do not present a sorry/axiom/tautology as a proof.',
        'unjustified_generalisation': 'Do not strengthen the target without a cited justification.',
        'lean_elaboration_failure': 'Do not submit Lean text that fails to elaborate.',
        'composition_type_mismatch': 'Do not compose operations whose colours do not match.',
        'composition_unlicensed': 'Do not compose without a verified licensing relation.',
        'schema_violation': 'Return exactly the schema; no extra or missing fields.',
        'unparseable_reply': 'Return one JSON object and nothing else.',
        'model_refusal': 'The model refused; do not retry the same request unchanged.',
    }
    text = templates.get(failure.cls, 'Do not repeat this move.')
    return text % (failure.decl_key or 'it') if '%s' in text else text


# --------------------------------------------------------------------------- DAG neighbours and positives
def _dag(root):
    root = str(root)
    if root not in _DAG_CACHE:
        path = Path(root) / 'dag' / 'derivation_dag.json'
        if path.is_file():
            data = json.loads(path.read_bytes().decode('utf-8'))
            _DAG_CACHE[root] = {'nodes': {n['id']: n for n in data['nodes']}, 'routes': data['routes']}
        else:
            _DAG_CACHE[root] = {'nodes': {}, 'routes': []}
    return _DAG_CACHE[root]


def dag_node(root, node_id):
    return _dag(root)['nodes'].get(node_id)


def dag_neighbours(root, node_id) -> list:
    """Parents (inputs of routes into the node) and children (outputs of routes that use it)."""
    found = []
    for route in _dag(root)['routes']:
        if route['output'] == node_id:
            found += route['inputs']
        if node_id in route['inputs']:
            found.append(route['output'])
    return sorted({n for n in found if n != node_id})


def positive_entries(root, node_ids, *, limit=8) -> list:
    """Host-verified generators and relations from earlier ladder runs of these nodes (newest first)."""
    rows = []
    for node in node_ids:
        base = Path(root) / 'dag' / 'results' / node / 'runs'
        if not base.is_dir():
            continue
        for run in sorted(base.glob('*_ladder'), reverse=True):
            path = run / 'p0' / 'operad_delta.yaml'
            if not path.is_file():
                continue
            try:
                delta = yaml.load(path.read_bytes(), Loader=LOADER) or {}
            except yaml.YAMLError:
                continue
            for key, kind in (('add_or_refine_generators', 'generator'), ('add_or_refine_relations', 'relation')):
                for item in delta.get(key) or []:
                    if isinstance(item, dict) and item.get('host_evidence'):
                        rows.append({'node_id': node, 'kind': kind, 'run': run.name, 'item': item})
    return rows[:limit]


def format_negative(entry) -> str:
    where = entry.get('decl_key')
    head = '[%s] %s' % (entry['class'], where if where else entry['claim'][:110])
    return '%s -- %s' % (head, entry['forbidden_move'])


def format_positive(row) -> str:
    item = row['item']
    ev = item.get('host_evidence', {})
    where = '%s | %s' % (ev.get('path', '?'), ev.get('decl', '?'))
    if row['kind'] == 'generator':
        return 'g:%s (%s)->%s src=%s' % (item.get('id', '?'), ','.join(item.get('inputs') or item.get('ordered_inputs') or []),
                                           item.get('output', '?'), where)
    return 'r:%s %s src=%s' % (item.get('id', '?'), str(item.get('statement') or item.get('equation_or_predicate', ''))[:110], where)
