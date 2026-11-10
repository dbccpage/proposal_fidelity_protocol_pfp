"""Preserve the original incoming inventory before any quality-based culling."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[2]
CORPUS=(ROOT/'pilots/anomalon_woland').resolve()
RECOVERY=Path(r'C:\Users\a343o\.codex\visualizations\2026\11\10\01a1c373-155b-7b31-94f8-3156bd6dbc35/.pilot_recovery')
manifest=json.loads((ROOT/'dag/migrations/anomalon_pilots_move.json').read_text(encoding='utf-8'))
RECOVERY.mkdir(exist_ok=True)
target=RECOVERY/'anomalon_pilots_before_quality_triage.zip'
drift=[]
with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for row in manifest['entries']:
        path=(CORPUS/row['path']).resolve()
        if not path.is_relative_to(CORPUS): raise ValueError('Path escaped corpus')
        data=path.read_bytes()
        digest=hashlib.sha256(data).hexdigest()
        if digest!=row['sha256']:
            drift.append({'path':row['path'],'original_sha256':row['sha256'],'current_sha256':digest,
                          'source_git_tracked':row['source_git_tracked']})
        archive.writestr(row['path'],data)
    archive.writestr('_migration_manifest.json',json.dumps(manifest,indent=2).encode())
with zipfile.ZipFile(target) as archive:
    failure=archive.testzip()
    if failure:raise ValueError('Archive CRC failure: '+failure)
    mismatches=[]
    for row in manifest['entries']:
        archived=hashlib.sha256(archive.read(row['path'])).hexdigest()
        current=hashlib.sha256((CORPUS/row['path']).read_bytes()).hexdigest()
        if archived!=current:mismatches.append(row['path'])
    if mismatches:raise ValueError('Archive/current byte mismatch')
digest=hashlib.sha256()
with target.open('rb') as handle:
    while data:=handle.read(1024*1024):digest.update(data)
receipt={'schema_version':'1.0','status':'verified_recovery_archive_no_deletions',
         'created_at_utc':datetime.now(timezone.utc).isoformat(),'archive_path':str(target),
         'archive_sha256':digest.hexdigest(),'archive_bytes':target.stat().st_size,
         'original_inventory_files_archived':len(manifest['entries']),
         'archive_current_sha256_mismatches':0,'original_custody_drift':drift,
         'scope':'Original migration inventory plus its manifest; later generated cache/test artifacts are not part of the incoming corpus.'}
(ROOT/'dag/migrations/pilot_recovery_archive.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:receipt[k] for k in ('status','archive_sha256','archive_bytes','original_inventory_files_archived','original_custody_drift')}))
