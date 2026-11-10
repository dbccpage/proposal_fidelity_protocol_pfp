"""Bounded ZIP/custody census and prior-body candidates; no extraction/execution."""
from collections import Counter
import hashlib
import json
from pathlib import Path,PurePosixPath
import zipfile

ROOT=Path(__file__).resolve().parents[2]
REV=ROOT/'dag/reviews'
BASE=ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence'
OUT=REV/'paper_011_support_inspection';OUT.mkdir(exist_ok=True)
def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda:stream.read(1048576),b''):digest.update(part)
    return digest.hexdigest()
archive=next(BASE.glob('*.zip'))
rows=[];small={}
with zipfile.ZipFile(archive) as zipped:
    infos=zipped.infolist()
    assert len(infos)<=3000 and sum(x.file_size for x in infos)<=600_000_000
    assert all(x.file_size<=40_000_000 for x in infos)
    names=set();folded=set();prefix=None
    for entry in infos:
        pure=PurePosixPath(entry.filename)
        assert not entry.is_dir() and not pure.is_absolute() and '..' not in pure.parts and '\\' not in entry.filename and ':' not in entry.filename
        prefix=prefix or pure.parts[0];assert pure.parts[0]==prefix
        name=str(PurePosixPath(*pure.parts[1:]));assert name not in names and name.casefold() not in folded
        names.add(name);folded.add(name.casefold())
        digest=hashlib.sha256()
        with zipped.open(entry) as stream:
            for part in iter(lambda:stream.read(1048576),b''):digest.update(part)
        path=(BASE/name).resolve();assert path.is_relative_to(BASE.resolve())
        current=file_sha(path) if path.is_file() else None
        rows.append({'member':name,'bytes':entry.file_size,'sha256':digest.hexdigest(),'current_path':path.relative_to(ROOT).as_posix(),
                     'current_sha256':current,'raw_equal':current==digest.hexdigest()})
        if name in ('MANIFEST.sha256','SHA256SUMS'):small[name]=zipped.read(entry).decode('utf-8')
by_name={x['member']:x for x in rows}
manifests={}
for name,body in small.items():
    checks=[]
    for line in body.splitlines():
        if not line or line.startswith('#'):continue
        expected,path=line.split('  ',1)
        checks.append({'path':path,'matches':path in by_name and by_name[path]['sha256']==expected})
    manifests[name]={'entries':len(checks),'mismatches':sum(not x['matches'] for x in checks),'checks':checks}
result={'archive':archive.relative_to(ROOT).as_posix(),'archive_sha256':file_sha(archive),'members':rows,'archive_manifests':manifests,
        'limits':'Every member streamed for CRC/SHA custody only. No source-body reading, semantic correctness, archived executable execution or extraction implied.'}
(OUT/'archive_inventory.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
prior={}
for p in REV.glob('additional_*.json'):
    if p.name.startswith('additional_paper_011'):continue
    d=json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(d,dict):continue
    for x in d.get('file_reviews',[]):
        if x.get('full_source_read') and x.get('sha256') and (ROOT/x['path']).is_file() and file_sha(ROOT/x['path'])==x['sha256']:
            prior.setdefault(x['sha256'],{'path':x['path'],'report':p.relative_to(ROOT).as_posix(),'assessment':x.get('assessment')})
scope=json.loads((REV/'additional_paper_011_support_scope.json').read_text())
candidates=[{'path':x['path'],'sha256':x['sha256'],'prior_full_read':prior[x['sha256']]} for x in scope['files'] if x['sha256'] in prior]
(OUT/'shared_body_candidates.json').write_text(json.dumps(candidates,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'members':len(rows),'raw_equal':sum(x['raw_equal'] for x in rows),'missing_current':sum(x['current_sha256'] is None for x in rows),
    'manifest_counts':{k:[v['entries'],v['mismatches']] for k,v in manifests.items()},'shared_body_candidates':len(candidates)}))
