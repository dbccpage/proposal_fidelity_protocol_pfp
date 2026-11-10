"""Validate later navigation edits without replacing the original audit inventory."""
import hashlib
import json
from pathlib import Path
import zipfile

REGISTRY = 'dag/migrations/consumer_followup_revisions.json'


def followup_revisions(root, inventory_by_path):
    root = Path(root).resolve()
    registry = root / REGISTRY
    if not registry.is_file():
        return []
    data = json.loads(registry.read_text(encoding='utf-8'))
    if data['status'] != 'custody_verified':
        raise ValueError('Unverified consumer revision custody')
    result = []
    seen = set()
    for row in data['revisions']:
        name = row['path']
        if name in seen or name not in inventory_by_path:
            raise ValueError('Duplicate or unknown consumer revision: ' + name)
        seen.add(name)
        current = (root / name).resolve()
        recovery = (root / row['recovery_path']).resolve()
        if not current.is_relative_to(root) or not recovery.is_relative_to(root):
            raise ValueError('Consumer revision path escapes repository')
        if inventory_by_path[name]['sha256'] != row['original_sha256']:
            raise ValueError('Consumer original conflicts with pinned inventory: ' + name)
        if hashlib.sha256(current.read_bytes()).hexdigest() != row['current_sha256']:
            raise ValueError('Current consumer revision changed: ' + name)
        recovered = recovery.read_bytes()
        if hashlib.sha256(recovered).hexdigest() != row['recovery_sha256']:
            raise ValueError('Consumer recovery artifact changed: ' + name)
        if row['recovery_kind'] == 'zip_member':
            with zipfile.ZipFile(recovery) as archive:
                if archive.namelist().count(row['archive_member']) != 1:
                    raise ValueError('Ambiguous consumer recovery member')
                recovered = archive.read(row['archive_member'])
        elif row['recovery_kind'] != 'plain_original':
            raise ValueError('Unknown consumer recovery kind')
        if hashlib.sha256(recovered).hexdigest() != row['original_sha256']:
            raise ValueError('Recovered consumer original changed: ' + name)
        result.append({**row, 'revision_custody': REGISTRY})
    return result
