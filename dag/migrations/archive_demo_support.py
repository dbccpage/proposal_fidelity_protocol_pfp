"""Archive a frozen relocation plan before any source removal; never overwrite."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOURCES = {'pfp': ROOT, 'anomalon': Path(r'C:\Users\a343o\source\repos\anomalon')}
ARCHIVE = Path(r'C:\Users\a343o\.codex\visualizations\2026\11\10\01a1c373-155b-7b31-94f8-3156bd6dbc35\.support_recovery\demo_support_before_move.zip')
PLAN = HERE / 'demo_support_move_plan.json'
RECEIPT = HERE / 'demo_support_recovery.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checked_source(row):
    relative = PurePosixPath(row['source_relative_path'])
    if relative.is_absolute() or '..' in relative.parts or '\\' in str(relative) or ':' in str(relative):
        raise ValueError('Unsafe source path')
    root = SOURCES[row['source_repo']].resolve()
    path = root.joinpath(*relative.parts)
    if not path.resolve().is_relative_to(root):
        raise ValueError('Source escapes repository')
    for ancestor in (path, *path.parents):
        if ancestor.is_symlink() or getattr(ancestor.lstat(), 'st_file_attributes', 0) & 0x400:
            raise ValueError('Reparse point: ' + str(ancestor))
        if ancestor == root:
            break
    data = path.read_bytes()
    if len(data) != row['bytes'] or sha(data) != row['sha256']:
        raise ValueError('Source changed: ' + str(path))
    return data


def main():
    if ARCHIVE.exists() or RECEIPT.exists():
        raise SystemExit('Recovery already exists; do not overwrite it.')
    plan_bytes = PLAN.read_bytes()
    plan = json.loads(plan_bytes)
    if plan['status'] != 'reviewed_ready_for_relocation' or not plan['entries']:
        raise ValueError('Plan not frozen and ready')
    names = [r['source_repo'] + '/' + r['source_relative_path'] for r in plan['entries']]
    if len(names) != len(set(names)):
        raise ValueError('Duplicate archive member')
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ARCHIVE, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr('relocation_plan.json', plan_bytes)
        for row, member in zip(plan['entries'], names, strict=True):
            archive.writestr(member, checked_source(row))
    with ARCHIVE.open('r+b') as stream:
        stream.flush()
        os.fsync(stream.fileno())
    with zipfile.ZipFile(ARCHIVE) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != {*names, 'relocation_plan.json'}:
            raise ValueError('Archive members/CRC mismatch')
        if archive.read('relocation_plan.json') != plan_bytes:
            raise ValueError('Archived plan mismatch')
        for row, member in zip(plan['entries'], names, strict=True):
            data = archive.read(member)
            if sha(data) != row['sha256'] or len(data) != row['bytes']:
                raise ValueError('Archive content mismatch: ' + member)
    receipt = {
        'schema_version': '1.0', 'created_utc': datetime.now(timezone.utc).isoformat(),
        'archive': str(ARCHIVE), 'sha256': sha(ARCHIVE.read_bytes()), 'bytes': ARCHIVE.stat().st_size,
        'plan_sha256': sha(plan_bytes), 'source_files': len(names),
        'source_bytes': sum(r['bytes'] for r in plan['entries']),
        'all_member_hashes_verified': True, 'all_member_crc_verified': True,
        'scope': 'Original bytes and paths only; not semantic verification or a claim that old campaigns executed.'
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
