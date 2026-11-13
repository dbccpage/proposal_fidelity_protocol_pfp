"""Verify original-byte recovery, current destinations, absent originals and retains."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCES = {'pfp': ROOT, 'private_engine_repo': ROOT.parent / 'private_engine_repo'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8-sig'))


def main():
    plan = read('demo_support_move_plan.json')
    receipt = read('demo_support_move_receipt.json')
    recovery = read('demo_support_recovery.json')
    consumer = read('demo_support_consumer_receipt.json') if (HERE / 'demo_support_consumer_receipt.json').exists() else {}
    if receipt['state'] != 'complete' or (consumer and consumer['status'] != 'complete'):
        raise ValueError('Incomplete move/adaptation receipt')
    if sha((HERE / 'demo_support_move_plan.json').read_bytes()) != receipt['plan_sha256'] or receipt['plan_sha256'] != recovery['plan_sha256']:
        raise ValueError('Plan binding mismatch')
    if len(receipt['entries']) != len(plan['entries']) or any(r['state'] != 'moved_and_verified' for r in receipt['entries']):
        raise ValueError('Incomplete per-file custody')
    edits = {(r['repository'], r['path']): r for r in consumer.get('changes', [])}
    archive_path = Path(recovery['archive'])
    if sha(archive_path.read_bytes()) != recovery['sha256']:
        raise ValueError('Recovery archive changed')
    locations = []
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError('Archive CRC failure')
        for row in plan['entries']:
            original = SOURCES[row['source_repo']] / row['source_relative_path']
            destination = ROOT / row['destination_relative_path']
            if original.exists():
                raise ValueError('Source original still present: ' + str(original))
            raw = archive.read(row['source_repo'] + '/' + row['source_relative_path'])
            if sha(raw) != row['sha256'] or len(raw) != row['bytes']:
                raise ValueError('Original archive binding mismatch')
            adapted = edits.get(('pfp', row['destination_relative_path']))
            if adapted and adapted['before_sha256'] != row['sha256']:
                raise ValueError('Adaptation not based on relocated original')
            expected = adapted['after_sha256'] if adapted else row['sha256']
            if sha(destination.read_bytes()) != expected:
                raise ValueError('Current destination hash mismatch: ' + str(destination))
            locations.append({'source_repo': row['source_repo'], 'original_path': row['source_relative_path'],
                'original_sha256': row['sha256'], 'current_path': row['destination_relative_path'], 'current_sha256': expected,
                'post_move_adaptation': bool(adapted), 'original_archive': str(archive_path),
                'archive_member': row['source_repo'] + '/' + row['source_relative_path']})
    retained_changes = []
    for row in plan['retained']:
        edit = edits.get((row['source_repo'], row['source_relative_path']))
        expected = edit['after_sha256'] if edit else row['sha256']
        if edit and edit['before_sha256'] != row['sha256']:
            raise ValueError('Retained edit original hash mismatch')
        path = SOURCES[row['source_repo']] / row['source_relative_path']
        if sha(path.read_bytes()) != expected:
            raise ValueError('Retained source drift: ' + str(path))
        if edit:
            retained_changes.append({'source_repo': row['source_repo'], 'path': row['source_relative_path'],
                'original_sha256': row['sha256'], 'current_sha256': expected,
                'original_archive': consumer['backup'], 'archive_member': row['source_repo'] + '/' + row['source_relative_path']})
    if consumer:
        backup = Path(consumer['backup'])
        if sha(backup.read_bytes()) != consumer['backup_sha256']:
            raise ValueError('Consumer backup changed')
        with zipfile.ZipFile(backup) as archive:
            if archive.testzip() is not None:
                raise ValueError('Consumer backup CRC failure')
            for row in consumer['changes']:
                if sha((SOURCES[row['repository']] / row['path']).read_bytes()) != row['after_sha256']:
                    raise ValueError('Consumer current hash mismatch')
                if row['before_sha256'] and sha(archive.read(row['repository'] + '/' + row['path'])) != row['before_sha256']:
                    raise ValueError('Consumer original backup hash mismatch')
    report = {'schema_version': '1.0', 'status': 'verified', 'verified_utc': datetime.now(timezone.utc).isoformat(),
        'move_counts': dict(Counter(r['source_repo'] for r in plan['entries'])), 'moved_files': len(plan['entries']),
        'original_bytes': sum(r['bytes'] for r in plan['entries']), 'source_originals_absent': True,
        'all_current_destination_hashes_verified': True, 'all_original_recovery_hashes_verified': True,
        'retained_files_verified': len(plan['retained']), 'retained_files_with_explicit_consumer_edits': len(retained_changes),
        'consumer_changes_verified': len(consumer.get('changes', [])), 'provider_calls': 0,
        'locations': locations, 'retained_source_revisions': retained_changes,
        'limits': 'Byte custody and relocation only. Historical claims are not freshly validated. Moved runnable owners may require the separate private engine runtime and explicit adapters.'}
    (HERE / 'demo_support_verification.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('locations', 'retained_source_revisions')}))


if __name__ == '__main__':
    main()
