"""Back up, verify and optionally apply reviewed non-destructive consumer edits."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCES = {'pfp': ROOT, 'anomalon': ROOT.parent / 'anomalon'}
BACKUP = Path(r'C:\Users\a343o\.codex\visualizations\2026\11\10\01a1c373-155b-7b31-94f8-3156bd6dbc35\.support_recovery\consumer_originals_before_adaptation.zip')
RECEIPT = HERE / 'demo_support_consumer_receipt.json'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text(encoding='utf-8-sig'))


def contained(repo, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or ':' in relative or '\\' in relative:
        raise ValueError('Unsafe consumer path')
    root = SOURCES[repo].resolve()
    target = root.joinpath(*path.parts)
    if not target.resolve().is_relative_to(root) or relative.startswith(('.', 'dag/')):
        raise ValueError('Consumer outside source tree')
    for parent in (target, *target.parents):
        if parent.exists() and (parent.is_symlink() or getattr(parent.lstat(), 'st_file_attributes', 0) & 0x400):
            raise ValueError('Reparse point: ' + str(parent))
        if parent == root:
            break
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if RECEIPT.exists() or BACKUP.exists():
        raise SystemExit('Consumer receipt/backup already exists; inspect before resuming.')
    moves = read('demo_support_move_receipt.json')
    if moves['state'] != 'complete':
        raise ValueError('Complete byte-preserving move required first')
    removed = {(r['source_repo'], r['source_relative_path']): r for r in moves['entries']}
    changes = []
    for row in read('woland_support_consumer_patch.json')['changes']:
        target = contained(row['repository'], row['path'])
        if row['after'] is None:
            if (row['repository'], row['path']) not in removed or target.exists():
                raise ValueError('Only already-verified moved sources may be absent')
            continue
        after = row['after'].encode('utf-8')
        before = row['before_sha256']
        if before is None and target.exists():
            if sha(target.read_bytes()) != sha(after):
                raise ValueError('Add target already exists with different bytes: ' + str(target))
            continue  # Unmodified calibration test was relocated byte-for-byte.
        changes.append({'repository': row['repository'], 'path': row['path'], 'before_sha256': before,
                        'after_sha256': row['after_sha256'], 'after_bytes': after, 'reason': row['reason']})
    for row in read('education_demo_classification_adaptation_plan.json')['changes']:
        if 'after_bytes_base64' in row:
            after = base64.b64decode(row['after_bytes_base64'], validate=True)
        else:
            after = row['after_text'].encode('utf-8')
        changes.append({'repository': 'pfp', 'path': row['post_move_path'],
                        'before_sha256': row['original_sha256'], 'after_sha256': row['post_adaptation_sha256'],
                        'after_bytes': after, 'reason': 'Explicit education navigation/path adaptation after unchanged relocation.'})
    spec = importlib.util.spec_from_file_location('navigation_review', HERE / 'woland_documentation_demo_classification_navigation_patch.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for row in module.plans(SOURCES['anomalon']):
        changes.append({'repository': 'anomalon', 'path': row['path'], 'before_sha256': row['source_sha256'],
                        'after_sha256': row['proposed_sha256'], 'after_bytes': row['proposed_raw'],
                        'reason': 'Retained operator guide navigation and explicit live pricing references.'})
    if len(changes) != len({(r['repository'], r['path'].casefold()) for r in changes}):
        raise ValueError('Overlapping consumer edits')
    originals = {}
    for row in changes:
        target = contained(row['repository'], row['path'])
        if row['before_sha256'] is None:
            if target.exists():
                raise ValueError('New target already exists')
        else:
            raw = target.read_bytes()
            if sha(raw) != row['before_sha256']:
                raise ValueError('Consumer changed: ' + str(target))
            originals[row['repository'] + '/' + row['path']] = raw
        if sha(row['after_bytes']) != row['after_sha256']:
            raise ValueError('Proposed consumer hash mismatch')
    summary = {repo: sum(r['repository'] == repo for r in changes) for repo in SOURCES}
    print(json.dumps({'preflight_changes': summary, 'originals_to_archive': len(originals)}))
    if not args.apply:
        return
    public_rows = [{k: v for k, v in r.items() if k != 'after_bytes'} for r in changes]
    plan_bytes = (json.dumps(public_rows, indent=2) + '\n').encode('utf-8')
    BACKUP.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(BACKUP, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('consumer_changes.json', plan_bytes)
        for name, raw in originals.items():
            archive.writestr(name, raw)
    with BACKUP.open('r+b') as stream:
        stream.flush()
        os.fsync(stream.fileno())
    with zipfile.ZipFile(BACKUP) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != {*originals, 'consumer_changes.json'}:
            raise ValueError('Consumer archive failed verification')
        for name, raw in originals.items():
            if archive.read(name) != raw:
                raise ValueError('Consumer archive bytes differ')
    receipt = {'status': 'applying', 'started_utc': datetime.now(timezone.utc).isoformat(),
        'backup': str(BACKUP), 'backup_sha256': sha(BACKUP.read_bytes()),
        'all_backup_members_verified': True, 'changes': public_rows, 'applied': []}

    def save():
        temporary = RECEIPT.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        temporary.replace(RECEIPT)

    save()
    for row in changes:
        target = contained(row['repository'], row['path'])
        current = sha(target.read_bytes()) if target.exists() else None
        if current != row['before_sha256']:
            raise ValueError('Consumer changed after preflight')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(row['after_bytes'])
        if sha(target.read_bytes()) != row['after_sha256']:
            raise ValueError('Consumer write verification failed')
        receipt['applied'].append({'repository': row['repository'], 'path': row['path']})
        save()
    receipt['status'] = 'complete'
    receipt['completed_utc'] = datetime.now(timezone.utc).isoformat()
    save()
    print(json.dumps({'applied': summary, 'backup_sha256': receipt['backup_sha256']}))


if __name__ == '__main__':
    main()
