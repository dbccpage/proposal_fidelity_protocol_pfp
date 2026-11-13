"""Freeze reviewed classifications into one exact, collision-checked move plan."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PRIVATE_ENGINE_REPO = ROOT.parent / 'private_engine_repo'
OUT = HERE / 'demo_support_move_plan.json'


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8-sig'))


def main():
    if OUT.exists():
        raise SystemExit('Frozen move plan already exists; do not overwrite.')
    frozen = read('imported_pilots_support_inventory.json')
    inventory = {r['source_relative_path']: r for r in frozen['entries']}
    other = read('imported_pilots_support_other_classification.json')['entries']
    documentation = read('private_documentation_demo_classification.json')
    education = read('education_demo_classification.json')
    docs = documentation['files']
    educ = education['files']
    if documentation['status'] != 'complete_read_only_classification' or education['status'] != 'classification_complete_read_only':
        raise ValueError('Classification is not complete')
    dispositions = []
    for row in other:
        dispositions.append({**row, 'source_repo': 'private_engine_repo', 'classification': 'dag/migrations/imported_pilots_support_other_classification.json'})
    for row in docs:
        relative = 'private_engine/documentation/' + row['path']
        dispositions.append({**inventory[relative], 'source_repo': 'private_engine_repo',
            'disposition': row['disposition'], 'reason': row['rationale'],
            'destination_relative_path': row.get('proposed_destination'),
            'classification': 'dag/migrations/private_documentation_demo_classification.json'})
    for row in educ:
        dispositions.append({'source_repo': 'pfp', 'source_relative_path': row['path'],
            'bytes': row['bytes'], 'sha256': row['sha256'], 'disposition': row['disposition'],
            'reason': row['reason'], 'destination_relative_path': row.get('proposed_destination'),
            'classification': 'dag/migrations/education_demo_classification.json'})
    if len(dispositions) != 1793 or len({(r['source_repo'], r['source_relative_path']) for r in dispositions}) != 1793:
        raise ValueError('Classification does not cover the exact 254 + 1539 named-scope files')
    if {r['source_relative_path'] for r in dispositions if r['source_repo'] == 'private_engine_repo'} != set(inventory):
        raise ValueError('private engine named scope mismatch')
    for row in dispositions:
        if row['disposition'] not in ('move', 'retain'):
            raise ValueError('Unresolved disposition')
        path = (PRIVATE_ENGINE_REPO if row['source_repo'] == 'private_engine_repo' else ROOT) / row['source_relative_path']
        raw = path.read_bytes()
        if len(raw) != row['bytes'] or hashlib.sha256(raw).hexdigest() != row['sha256']:
            raise ValueError('Source changed: ' + str(path))
    entries = [r for r in dispositions if r['disposition'] == 'move']
    ancillary = {
        'private_engine/tests/test_calibration_tasks.py': 'pilots/imported_pilots_support/tests/test_calibration_tasks.py',
        'private_engine/tests/research/test_frozen_review_replay.py': 'pilots/imported_pilots_support/tests/historical_sources/test_frozen_review_replay.py.txt',
    }
    for source, target in ancillary.items():
        raw = (PRIVATE_ENGINE_REPO / source).read_bytes()
        metadata = subprocess.check_output(['git', '-C', str(PRIVATE_ENGINE_REPO), 'ls-files', '--stage', '--', source], text=True).strip()
        mode, blob, stage = metadata.split('\t')[0].split()
        if stage != '0':
            raise ValueError('Unmerged ancillary test')
        entries.append({'source_repo': 'private_engine_repo', 'source_relative_path': source,
            'destination_relative_path': target, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'source_git_tracked': True, 'git_mode': mode, 'git_blob': blob, 'disposition': 'move',
            'reason': 'Dedicated corpus regression test moves with its owner; adapted wrappers remain separate from preserved original bytes.',
            'classification': 'dag/migrations/imported_pilots_support_consumer_patch.json'})
    targets = [r['destination_relative_path'] for r in entries]
    if any(not p for p in targets) or len(targets) != len(set(p.casefold() for p in targets)):
        raise ValueError('Missing or colliding destination')
    for target in targets:
        path = (ROOT / target).resolve()
        if not path.is_relative_to(ROOT / 'pilots') or path.exists():
            raise ValueError('Destination escapes pilot root or already exists: ' + target)
    report = {'schema_version': '1.0', 'status': 'reviewed_ready_for_relocation',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'private_engine_repo_base': read('imported_pilots_support_branch_base.json'),
        'named_scope_files': len(dispositions),
        'named_scope_dispositions': dict(Counter(r['disposition'] for r in dispositions)),
        'move_counts_by_source': dict(Counter(r['source_repo'] for r in entries)),
        'total_bytes': sum(r['bytes'] for r in entries), 'ancillary_source_tests': list(ancillary),
        'entries': entries, 'retained': [r for r in dispositions if r['disposition'] == 'retain'],
        'evidence_ceiling': 'Ownership/content classification with per-file depth in source reports. Migration preserves bytes; it does not validate historical scientific claims or model results.'}
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('named_scope_files', 'named_scope_dispositions', 'move_counts_by_source', 'total_bytes')}))


if __name__ == '__main__':
    main()
