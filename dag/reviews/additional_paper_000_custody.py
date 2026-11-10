"""Check package/archive bindings and expose every current/archive text difference."""
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / 'papers/pfp/000_pfp_introduction'
OUT = Path(__file__).with_name('paper_000_support_inspection')
OUT.mkdir(exist_ok=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lf(data):
    return data.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n').encode('utf-8')


def current_name(name):
    return name.replace('_lev_landau_', '_lev_examiner_').replace('_pfp_landau_companion.pdf', '_pfp_examiner_companion.pdf')


report = {'current_manifests': [], 'archive_manifests': [], 'archive_members': [], 'historical_bindings': []}
for name in ('MANIFEST.sha256', 'SHA256SUMS'):
    rows = []
    for line in (PACKAGE / name).read_text().splitlines():
        digest, relative = line.split(None, 1)
        relative = relative.lstrip('* ')
        path = (PACKAGE / relative).resolve()
        assert path.is_relative_to(PACKAGE.resolve())
        raw = path.read_bytes()
        try:
            lf_match = sha(lf(raw)) == digest
        except UnicodeDecodeError:
            lf_match = None
        rows.append({'path': relative, 'expected': digest, 'actual': sha(raw),
                     'raw_match': sha(raw) == digest, 'universal_lf_match': lf_match})
    report['current_manifests'].append({'path': name, 'entries': rows})
diffs = []
with zipfile.ZipFile(PACKAGE / '000_pfp_introduction_2026-10-02.zip') as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert len(names) == len(set(names))
    for member in archive.infolist():
        path = PurePosixPath(member.filename)
        assert not path.is_absolute() and '..' not in path.parts and not member.is_dir()
        relative = str(path.relative_to('000_pfp_introduction'))
        raw = archive.read(member)
        current = PACKAGE / current_name(relative)
        current_raw = current.read_bytes()
        row = {'member': member.filename, 'bytes': len(raw), 'sha256': sha(raw),
               'current_path': current.relative_to(ROOT).as_posix(), 'current_sha256': sha(current_raw),
               'current_raw_equal': raw == current_raw}
        try:
            before, after = lf(raw).decode(), lf(current_raw).decode()
            row['current_lf_equal'] = before == after
            if before != after:
                diff = ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True),
                                                  fromfile='archive/' + relative, tofile='current/' + current_name(relative)))
                diffs.append(diff)
                row['complete_difference_lines'] = len(diff.splitlines())
        except UnicodeDecodeError:
            row['current_lf_equal'] = None
        report['archive_members'].append(row)
    for name in ('MANIFEST.sha256', 'SHA256SUMS'):
        rows = []
        for line in archive.read('000_pfp_introduction/' + name).decode().splitlines():
            digest, relative = line.split(None, 1)
            member = '000_pfp_introduction/' + relative.lstrip('* ')
            rows.append({'member': member, 'expected': digest, 'match': sha(archive.read(member)) == digest})
        report['archive_manifests'].append({'path': name, 'entries': rows})
for path in sorted((PACKAGE / 'docs').glob('release_validation*.json')):
    body = json.loads(path.read_text())
    for key in ('selected_test_input_sha256', 'candidate_asset_sha256', 'executed_file_sha256'):
        for relative, expected in body.get(key, {}).items():
            current = PACKAGE / ('000_paper.pdf' if relative == 'paper.pdf' else relative)
            raw = current.read_bytes()
            try:
                lf_match = sha(lf(raw)) == expected
            except UnicodeDecodeError:
                lf_match = None
            report['historical_bindings'].append({'receipt': path.name, 'field': key, 'path': relative,
                'expected': expected, 'current_raw_match': sha(raw) == expected, 'current_lf_match': lf_match})
target = Path(__file__).with_suffix('.json')
target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
(OUT / 'archive_complete_text_diffs.txt').write_text('\n'.join(diffs), encoding='utf-8')
print(json.dumps({'current_manifest_mismatches': {r['path']: {'raw': sum(not x['raw_match'] for x in r['entries']),
      'survives_lf': sum(not x['raw_match'] and x['universal_lf_match'] is not True for x in r['entries'])} for r in report['current_manifests']},
      'archive_members': len(report['archive_members']), 'archive_manifests_all_match': all(x['match'] for r in report['archive_manifests'] for x in r['entries']),
      'archived_pdf_equal_current': [r['member'] for r in report['archive_members'] if r['member'].endswith('.pdf') and r['current_raw_equal']],
      'archive_current_non_lineending_differences': [r['member'] for r in report['archive_members'] if r['current_lf_equal'] is False],
      'complete_difference_lines': sum(len(d.splitlines()) for d in diffs)}))
