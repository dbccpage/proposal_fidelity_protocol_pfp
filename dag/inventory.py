"""Reproducible non-dot-directory inventory. Hashing is NOT semantic review."""
from __future__ import annotations
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REMOTE = '8050c66900899771766f33e8f5fdd200b7dd9120'

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])

def tree(ref):
    result = {}
    for item in git('ls-tree', '-r', '-z', ref).split(b'\0'):
        if not item:
            continue
        meta, path = item.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        name = path.decode('utf-8')
        if any(p.startswith('.') for p in Path(name).parts[:-1]):
            continue
        result[name] = {'git_oid': oid, 'mode': mode, 'kind': kind}
    return result

def category(path):
    suffix = Path(path).suffix.lower()
    if suffix in {'.py', '.rs', '.lean', '.cs', '.ts', '.js', '.mjs'}:
        return 'source_or_test'
    if suffix in {'.md', '.tex', '.rst', '.txt'}:
        return 'prose_or_data'
    if suffix in {'.json', '.jsonl', '.yaml', '.yml', '.toml', '.csv'}:
        return 'structured_data_or_configuration'
    if suffix in {'.pdf', '.zip', '.docx', '.png', '.jpg', '.svg', '.gif'}:
        return 'document_archive_or_media'
    return 'other'

def main():
    head = git('rev-parse', 'HEAD').decode().strip()
    remote, local = tree(REMOTE), tree(head)
    records = {}
    excluded = ['dot-prefixed ancestor directories', 'dag/ (new audit outputs)',
                'Git-ignored build/cache files not present in the GitHub repository']
    extra = {p.decode('utf-8') for p in git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if p}
    candidates = sorted(set(remote) | set(local) | extra)
    for rel in candidates:
            if any(p.startswith('.') for p in Path(rel).parts[:-1]) or rel.startswith('dag/'):
                continue
            p = ROOT / rel
            if not p.exists():
                continue
            name = p.name
            rec = {'path': rel, 'category': category(rel), 'size_bytes': p.stat().st_size,
                   'local_tracked': rel in local, 'remote_tracked': rel in remote,
                   'review_status': 'inventory_only', 'semantic_review_complete': False}
            if (name == '.env' or name.startswith('.env.')) and name not in {'.env.example', '.env.sample', '.env.template'}:
                rec.update(content_status='sensitive_configuration_not_read', sha256=None)
            elif p.is_symlink():
                rec.update(content_status='symlink_not_followed', sha256=None)
            else:
                try:
                    h = hashlib.sha256()
                    with p.open('rb') as f:
                        for block in iter(lambda: f.read(1024*1024), b''):
                            h.update(block)
                    rec.update(sha256=h.hexdigest(), content_status='bytes_hashed_only')
                except OSError as e:
                    rec.update(sha256=None, content_status='read_error', error=type(e).__name__)
            if rel in remote:
                rec['remote_git_oid'] = remote[rel]['git_oid']
            if rel in local:
                rec['head_git_oid'] = local[rel]['git_oid']
            rec['remote_differs_from_head'] = remote.get(rel) != local.get(rel)
            records[rel] = rec
    for rel in sorted(set(remote) - set(records)):
        records[rel] = {'path': rel, 'category': category(rel), 'local_present': False,
                        'remote_tracked': True, 'remote_git_oid': remote[rel]['git_oid'],
                        'review_status': 'inventory_only', 'semantic_review_complete': False,
                        'content_status': 'remote_blob_not_read'}
    summary = {'schema_version': '1.0', 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
               'repository': 'https://github.com/dbccpage/proposal_fidelity_protocol_pfp',
               'local_head': head, 'remote_main_at_start': REMOTE,
               'scope': 'Every file tracked at the pinned GitHub main or local HEAD whose ancestor directory does not start with a dot, plus nonignored local additions. New dag audit artifacts are tracked separately to avoid self-reference. Root dotfiles are eligible; secret configuration content is not read. Git-ignored local build/cache artifacts are not files in the requested GitHub repository.',
               'local_uncommitted_changes': git('status', '--porcelain=v1', '-uall').decode().splitlines(),
               'counts': {'files': len(records), 'remote_files': len(remote), 'local_head_files': len(local),
                          'bytes': sum(x.get('size_bytes', 0) for x in records.values())},
               'by_top_directory': dict(collections.Counter(p.split('/')[0] if '/' in p else '(root)' for p in records)),
               'by_category': dict(collections.Counter(x['category'] for x in records.values())),
               'excluded_directories': sorted(excluded),
               'files': [records[k] for k in sorted(records)]}
    out = ROOT / 'dag' / 'file_inventory.json'
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    print(json.dumps({k: summary[k] for k in ['counts', 'by_top_directory', 'by_category']}, indent=2))

if __name__ == '__main__':
    main()
