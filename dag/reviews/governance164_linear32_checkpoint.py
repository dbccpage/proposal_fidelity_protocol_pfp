"""Freeze active source-review reports and validate a reproducible parent checkpoint."""
from collections import deque
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

R = Path(__file__).resolve().parents[2]
P = R / 'dag/reviews/governance164_linear32'

def read(p):
    return json.loads(p.read_bytes())

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def pin(p):
    return {'path': p.relative_to(R).as_posix(), 'sha256': digest(p)}

def write(p, d):
    p.write_text(json.dumps(d, indent=2)+'\n', encoding='utf8')

inputs = Path(str(P)+'_inputs.json')
if sys.argv[1] == 'capture':
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    rows = []
    for part in ('linear_algebra', 'homology', 'ooutwire', 'adversary'):
        p = R / ('dag/reviews/additional_rust_'+part+'_remaining.json')
        raw = p.read_bytes()
        report = json.loads(raw)
        snapshot = p.with_name(p.stem+'_parent_'+stamp+'.json.snapshot')
        snapshot.write_bytes(raw)
        reviews = report['file_reviews']
        full = sum(x.get('full_source_read') is True for x in reviews)
        rows.append({'report': p.relative_to(R).as_posix(), 'snapshot': pin(snapshot), 'status': report['status'], 'full_source_reads': full, 'claims': len(report.get('claims', [])), 'findings': len(report.get('findings', []))})
    write(inputs, {'stamp': stamp, 'active_reports': rows})
    print('Captured four active report snapshots; no additional reading credit.')
    raise SystemExit

assert sys.argv[1] == 'finish'
data = read(inputs)
for row in data['active_reports']:
    assert digest(R / row['report']) == row['snapshot']['sha256'], 'Active report changed; capture and rebuild before finishing.'
    assert digest(R / row['snapshot']['path']) == row['snapshot']['sha256']
integration = read(R/'dag/reviews/governance164_parent_integration.json')
for path, key in [
    ('additional_ops_governance_domain_remaining.json', 'report_sha256'),
    ('additional_ops_governance_domain_remaining_validation.json', 'validation_sha256'),
    ('additional_ops_governance_domain_remaining_controls.json', 'controls_sha256'),
    ('additional_ops_governance_domain_remaining_controls.py', 'controls_helper_sha256')
]:
    assert digest(R/'dag/reviews'/path) == integration[key]

def graph(name):
    d = read(R/'dag'/name)
    assert d['status'] == 'in_progress' and d['scope_complete'] is False
    ids = [x['id'] for x in d['nodes']]
    assert len(ids) == len(set(ids))
    incoming = dict.fromkeys(ids, 0)
    adjacent = {i: [] for i in ids}
    for edge in d['edges']:
        a, b = edge['from'], edge['to']
        assert a in incoming and b in incoming
        adjacent[a].append(b)
        incoming[b] += 1
    queue = deque(i for i, degree in incoming.items() if not degree)
    seen = 0
    while queue:
        i = queue.popleft()
        seen += 1
        for j in adjacent[i]:
            incoming[j] -= 1
            if incoming[j] == 0:
                queue.append(j)
    assert seen == len(ids)
    return {'unique_nodes': len(ids), 'edges': len(d['edges']), 'acyclic': True}

coverage = read(R/'dag/reviews/coverage.json')
assert coverage['scope_files'] == 32261 and sum(coverage['counts'].values()) == 32261
assert coverage['all_files_substantively_reviewed'] is False
parent = read(R/'dag/reviews/additional_rust_linear_algebra_remaining.json')
assert parent['scope']['full_source_reads'] == 32 and parent['scope']['pending'] == 51
assert len(parent['claims']) == 16 and len(parent['findings']) == 8 and len(parent['controls']) == 21
artifacts = ['dag/reviews/governance164_parent_integration.json', 'dag/reviews/additional_ops_governance_domain_remaining.json', 'dag/reviews/additional_ops_governance_domain_remaining_validation.json', 'dag/reviews/additional_ops_governance_domain_remaining_controls.json', 'dag/reviews/additional_rust_linear_algebra_remaining_validation.json', 'dag/reviews/coverage.json', 'dag/derivations_dag.json', 'dag/workflows_dag.json', 'dag/FOUNDATIONS.md', 'dag/swarm_manifest.json', 'dag/wiki/workflow_documentation.json', 'dag/wiki/workflow_publication_20261110.json', 'dag/reviews/additional_rust_quantum_probability_remaining_scope.json']
artifacts += ['dag/reviews/additional_rust_linear_algebra_remaining_controls'+n+'.json' for n in ('04', '05', '06', '07')]
out = {
    'status': 'progress_checkpoint_repository_audit_incomplete',
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'source_commit': coverage['source_commit'],
    'completed_agent_slice': {'files': 164, 'source_lines': 10427, 'claims': 6, 'findings': 18, 'independent_controls': 20, 'integration': 'dag/reviews/governance164_parent_integration.json'},
    'parent_active_scope': {**parent['scope'], 'claims': 16, 'findings': 8, 'independent_controls': 21},
    'coverage': coverage['counts'],
    'derivations': graph('derivations_dag.json'),
    'workflows': graph('workflows_dag.json'),
    'active_report_snapshots': data['active_reports'],
    'wiki_status': 'Five implemented QM plans published at3093fd13e22aa3eccb7c3954871d71026d23b419; no new completed workflow in this checkpoint. Completion-to-Wiki requirement remains active.',
    'limits': ['Active agent reports remain provisional until their completed-scope parent integration.', 'No original source edits, native/provider execution or private answer access in this continuation; paid runs remain zero.', 'Finite controls and custody checks do not complete the repository-wide audit or establish universal application correctness.'],
    'artifacts': [pin(R/x) for x in artifacts]+[pin(Path(__file__))]
}
checkpoint = Path(str(P)+'_parent_checkpoint.json')
write(checkpoint, out)
note = '\n\nCheckpoint '+out['generated_at_utc']+': governance164 integrated; parent linear-algebra32/83 full,15903 lines,16 claims,8 findings,21 controls. Coverage '+str(coverage['counts'])+'. Both DAGs acyclic; scope incomplete. Five QM plans already published to Wiki; no new workflow, paid/native run or private-answer access. Checkpoint '+checkpoint.relative_to(R).as_posix()+' SHA256 '+digest(checkpoint)+'.\n'
with (R/'dag/PROGRESS.md').open('ab') as handle:
    handle.write(note.encode('utf8'))
print(json.dumps({'checkpoint': pin(checkpoint), 'coverage': out['coverage'], 'derivations': out['derivations'], 'workflows': out['workflows']}, indent=2))
