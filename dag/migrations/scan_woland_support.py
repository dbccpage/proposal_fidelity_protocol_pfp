"""Freeze the four explicitly named Woland source trees before classification."""
import hashlib
import json
from pathlib import Path
import stat
import subprocess

DEST = Path(__file__).resolve().parents[2]
SOURCE = Path(r'C:\Users\a343o\source\repos\anomalon').resolve()
NAMES = ('documentation', '_fixtures', 'program_profiles', 'evidence')
OUT = Path(__file__).with_name('woland_support_inventory.json')


def git(*args):
    return subprocess.check_output(['git', '-C', str(SOURCE), *args], text=True, encoding='utf-8').strip()


def main():
    if OUT.exists():
        raise SystemExit('Frozen inventory already exists; do not overwrite it.')
    prefixes = ['omega_engine_woland/' + name for name in NAMES]
    tracked = {}
    for line in git('ls-files', '--stage', '--', *prefixes).splitlines():
        metadata, path = line.split('\t', 1)
        mode, blob, stage = metadata.split()
        if stage != '0':
            raise ValueError('Unmerged source: ' + path)
        tracked[path] = {'git_mode': mode, 'git_blob': blob}
    entries = []
    directories = []
    for prefix in prefixes:
        root = SOURCE / prefix
        assert root.resolve().is_relative_to(SOURCE / 'omega_engine_woland')
        for path in sorted([root, *root.rglob('*')]):
            attrs = path.lstat()
            if path.is_symlink() or getattr(attrs, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Reparse/link in named source scope: ' + str(path))
            relative = path.relative_to(SOURCE).as_posix()
            if path.is_dir():
                directories.append(relative)
                continue
            if not stat.S_ISREG(attrs.st_mode):
                raise ValueError('Not a regular file: ' + relative)
            data = path.read_bytes()
            entries.append({'source_relative_path': relative, 'bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest(), 'source_git_tracked': relative in tracked,
                **tracked.get(relative, {})})
    missing = sorted(set(tracked) - {row['source_relative_path'] for row in entries})
    if missing:
        raise ValueError('Tracked source missing: ' + repr(missing))
    report = {'schema_version': '1.0', 'source_repository': str(SOURCE),
        'source_head': git('rev-parse', 'HEAD'), 'source_branch': git('branch', '--show-current'),
        'destination_repository': str(DEST), 'named_roots': prefixes, 'directories': directories,
        'file_count': len(entries), 'total_bytes': sum(row['bytes'] for row in entries), 'entries': entries}
    OUT.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('source_head', 'file_count', 'total_bytes')}))


if __name__ == '__main__':
    main()
