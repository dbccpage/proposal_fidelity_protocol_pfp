"""Bounded archive/manifest custody and exact shared-body transfer candidates."""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'papers/pfp/010_pfp_holonomy_checks_and_model_pilots'
REV = ROOT/'dag/reviews'
OUT = REV/'paper_010_support_inspection'
OUT.mkdir(exist_ok=True)


def sha(raw): return hashlib.sha256(raw).hexdigest()
def lf(raw): return raw.replace(b'\r\n', b'\n')
def current_name(name): return name.replace('_lev_landau_', '_lev_examiner_').replace('_pfp_landau_companion', '_pfp_examiner_companion')


scope = json.loads((REV/'additional_paper_010_support_scope.json').read_text())
prior = {}
for report_path in REV.glob('additional_*.json'):
    if report_path.name.startswith('additional_paper_010'): continue
    report = json.loads(report_path.read_text(encoding='utf-8'))
    if not isinstance(report, dict): continue
    for row in report.get('file_reviews', []):
        if row.get('full_source_read') and row.get('path') and row.get('sha256'):
            old = ROOT/row['path']
            if old.is_file() and sha(old.read_bytes()) == row['sha256']:
                prior.setdefault(row['sha256'], {'path':row['path'], 'report':report_path.relative_to(ROOT).as_posix(),
                                                'assessment':row.get('assessment'), 'reviewed_lines':row.get('reviewed_lines')})
transfers = []
for row in scope['files']:
    if row['sha256'] in prior:
        transfers.append({'path':row['path'],'sha256':row['sha256'],'prior_full_read':prior[row['sha256']],
                          'limit':'Exact-byte body transfer only; current paper context assessed separately.'})
(OUT/'shared_body_candidates.json').write_text(json.dumps(transfers,indent=2)+'\n',encoding='utf-8')

archive = next(BASE.glob('*.zip'))
target = (OUT/'archive').resolve()
target.mkdir(exist_ok=True)
rows = []; delta_lines = []
with zipfile.ZipFile(archive) as zipped:
    assert len(zipped.infolist()) <= 100 and sum(i.file_size for i in zipped.infolist()) < 10_000_000
    prefix = PurePosixPath(zipped.namelist()[0]).parts[0]
    members = {}
    for info in zipped.infolist():
        pure = PurePosixPath(info.filename)
        assert not pure.is_absolute() and '..' not in pure.parts and '\\' not in info.filename and ':' not in info.filename
        assert pure.parts[0] == prefix and not info.is_dir()
        name = str(PurePosixPath(*pure.parts[1:])); assert name not in members
        data = zipped.read(info); members[name] = data
        destination = (target/name).resolve(); assert destination.is_relative_to(target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists(): assert destination.read_bytes() == data
        else: destination.write_bytes(data)
        current = BASE/current_name(name)
        raw = current.read_bytes() if current.is_file() else None
        relation = 'byte_equal' if raw == data else ('LF_equal' if raw is not None and lf(raw) == lf(data) else 'different')
        row = {'member':name,'bytes':len(data),'sha256':sha(data),'current_path':current.relative_to(ROOT).as_posix(),
               'current_sha256':sha(raw) if raw is not None else None,'relation':relation}
        if relation == 'different' and current.suffix not in ('.pdf','.zip') and raw is not None:
            old, new = lf(data).decode('utf-8-sig'), lf(raw).decode('utf-8-sig')
            diff = list(difflib.unified_diff(old.splitlines(),new.splitlines(),fromfile='archive/'+name,tofile='current/'+current_name(name),lineterm='',n=2))
            row['delta_lines'] = len(diff)
            delta_lines += diff + ['']
        rows.append(row)
    manifests = {}
    for name in ('MANIFEST.sha256','SHA256SUMS'):
        checks = []
        for line in members[name].decode().splitlines():
            if not line or line.startswith('#'): continue
            expected, relative = line.split('  ',1)
            checks.append({'path':relative,'expected':expected,'actual':sha(members[relative]),'matches':sha(members[relative])==expected})
        manifests[name] = checks

current_manifests = {}
for name in ('MANIFEST.sha256','SHA256SUMS'):
    checks=[]
    for line in (BASE/name).read_text().splitlines():
        if not line or line.startswith('#'): continue
        expected, relative=line.split('  ',1)
        p=BASE/relative;raw=p.read_bytes() if p.is_file() else None
        checks.append({'path':relative,'expected':expected,'matches':raw is not None and sha(raw)==expected,
                       'LF_matches':raw is not None and sha(lf(raw))==expected})
    current_manifests[name]=checks

result={'archive_sha256':sha(archive.read_bytes()),'members':rows,'archive_manifests':manifests,
        'current_manifests':current_manifests,'body_relation_counts':dict(Counter(row['relation'] for row in rows)),
        'shared_body_candidates':transfers,'limit':'Custody/delta inventory does not itself give semantic reading credit.'}
(OUT/'archive_inventory.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(OUT/'archive_deltas.txt').write_text('\n'.join(delta_lines)+'\n',encoding='utf-8')
print(json.dumps({'members':len(rows),'relations':result['body_relation_counts'],'delta_lines':len(delta_lines),
                  'archive_manifest_counts':{k:(len(v),sum(not x['matches'] for x in v)) for k,v in manifests.items()},
                  'current_manifest_counts':{k:(len(v),sum(not x['matches'] for x in v),sum(not x['LF_matches'] for x in v)) for k,v in current_manifests.items()},
                  'shared_body_candidates':len(transfers)}))
