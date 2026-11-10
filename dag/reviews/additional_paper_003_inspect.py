"""Read-only PDF text extraction and package/archive custody inventory."""
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
NAME = '003_pfp_host_admitted_failure_detectors'
PACKAGE = ROOT / 'papers/pfp' / NAME
OUT = Path(__file__).with_name('paper_003_support_inspection')
OUT.mkdir(exist_ok=True)
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def lf(raw):
    return raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
def present(name):
    return name.replace('_lev_landau_', '_lev_examiner_').replace('_pfp_landau_companion.pdf', '_pfp_examiner_companion.pdf')
pdfs = []
for index, path in enumerate(sorted(PACKAGE.rglob('*.pdf'))):
    pages = [p.extract_text(extraction_mode='layout') or '' for p in PdfReader(path).pages]
    target = OUT / f'pdf_{index:02d}.txt'
    target.write_text('\n'.join(f'\nPAGE {i+1}\n{s}' for i,s in enumerate(pages)), encoding='utf-8')
    pdfs.append({'pdf': path.relative_to(ROOT).as_posix(), 'pages': len(pages), 'sha256': sha(path.read_bytes()),
                 'extraction': target.relative_to(ROOT).as_posix()})
(OUT / 'pdf_inventory.json').write_text(json.dumps(pdfs, indent=2) + '\n')
report = {'current_manifests': [], 'archive_manifests': [], 'archive_members': []}
for name in ('MANIFEST.sha256', 'SHA256SUMS'):
    entries = []
    for line in (PACKAGE / name).read_text().splitlines():
        digest, rel = line.split(None, 1)
        rel = rel.lstrip('* ')
        path = (PACKAGE / rel).resolve()
        assert path.is_relative_to(PACKAGE.resolve())
        if not path.is_file():
            entries.append({'path': rel, 'expected': digest, 'missing': True, 'raw_match': False, 'universal_lf_match': False})
            continue
        raw = path.read_bytes()
        try:
            normal = sha(lf(raw).encode()) == digest
        except UnicodeDecodeError:
            normal = None
        entries.append({'path': rel, 'expected': digest, 'actual': sha(raw), 'raw_match': sha(raw) == digest, 'universal_lf_match': normal})
    report['current_manifests'].append({'path': name, 'entries': entries})
diffs = []
with zipfile.ZipFile(PACKAGE / f'{NAME}_2026-10-02.zip') as archive:
    assert archive.testzip() is None
    assert len(archive.namelist()) == len(set(archive.namelist()))
    for info in archive.infolist():
        path = PurePosixPath(info.filename)
        assert not path.is_absolute() and '..' not in path.parts
        if info.is_dir():
            continue
        rel = str(path.relative_to(NAME))
        raw = archive.read(info)
        current = PACKAGE / present(rel)
        row = {'member': info.filename, 'sha256': sha(raw), 'bytes': len(raw), 'current_path': current.relative_to(ROOT).as_posix()}
        if current.is_file():
            now = current.read_bytes()
            row.update(current_sha256=sha(now), current_raw_equal=raw == now)
            try:
                before, after = lf(raw), lf(now)
                row['current_lf_equal'] = before == after
                if before != after:
                    delta = ''.join(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), fromfile='archive/' + rel, tofile='current/' + present(rel)))
                    diffs.append(delta)
                    row['complete_difference_lines'] = len(delta.splitlines())
            except UnicodeDecodeError:
                row['current_lf_equal'] = None
        else:
            row['current_missing'] = True
        report['archive_members'].append(row)
    for name in ('MANIFEST.sha256', 'SHA256SUMS'):
        entries = []
        for line in archive.read(NAME + '/' + name).decode().splitlines():
            digest, rel = line.split(None, 1)
            member = NAME + '/' + rel.lstrip('* ')
            entries.append({'member': member, 'expected': digest, 'match': sha(archive.read(member)) == digest})
        report['archive_manifests'].append({'path': name, 'entries': entries})
(OUT / 'archive_complete_text_diffs.txt').write_text('\n'.join(diffs), encoding='utf-8')
Path(__file__).with_name('additional_paper_003_custody.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'pdfs': pdfs,
 'current_mismatches': {r['path']: {'raw':sum(not e['raw_match'] for e in r['entries']), 'survives_lf':sum(not e['raw_match'] and e['universal_lf_match'] is not True for e in r['entries'])} for r in report['current_manifests']},
 'archive_members': len(report['archive_members']), 'archive_bindings_all_match': all(e['match'] for r in report['archive_manifests'] for e in r['entries']),
 'archive_current_differences': [r['member'] for r in report['archive_members'] if r.get('current_lf_equal') is False],
 'complete_difference_lines':sum(len(d.splitlines()) for d in diffs)}))
