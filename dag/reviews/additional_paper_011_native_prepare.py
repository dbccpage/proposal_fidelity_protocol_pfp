"""Validate frozen native scope and find explicit full-body reuse candidates; no reading credit."""
import collections,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_native'
def sha(raw):return hashlib.sha256(raw).hexdigest()
scope_path=H/(P+'_scope.json');scope=json.loads(scope_path.read_text(encoding='utf-8'));rows=[]
for item in scope['files']:
 raw=(R/item['path']).read_bytes();assert sha(raw)==item['sha256'];row=dict(item)
 try:row['lines']=len(raw.decode('utf-8').splitlines());row['utf8_text']=True
 except UnicodeDecodeError:row['lines']=None;row['utf8_text']=False
 rows.append(row)
index={};reports_scanned=0
for path in sorted(H.glob('*.json')):
 if path.name.startswith(P):continue
 try:report=json.loads(path.read_text(encoding='utf-8'))
 except (UnicodeError,json.JSONDecodeError):continue
 if not isinstance(report,dict):continue
 for row in report.get('file_reviews',[]):
  if row.get('full_source_read') is not True or not row.get('path') or not row.get('sha256'):continue
  index.setdefault(row['sha256'],[]).append({'report':path.relative_to(R).as_posix(),'report_sha256':sha(path.read_bytes()),'reading_receipt':row})
 reports_scanned+=1
candidates=[]
for row in rows:
 for candidate in index.get(row['sha256'],[]):
  base=candidate['reading_receipt'];basepath=R/base['path']
  if basepath.is_file() and sha(basepath.read_bytes())==base['sha256']:
   candidates.append({'path':row['path'],'sha256':row['sha256'],'base':candidate,'raw_equal':True});break
result={'scope_path':scope_path.relative_to(R).as_posix(),'scope_sha256':sha(scope_path.read_bytes()),'files':rows,
        'full_body_transfer_candidates':candidates,'limit':'Only metadata/equality candidate discovery. No source reading credit or context assessment is granted by this helper.'}
(H/(P+'_preparation.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'paths':len(rows),'bytes':sum(r['bytes'] for r in rows),'lines':sum(r['lines'] or 0 for r in rows),'text':sum(r['utf8_text'] for r in rows),
 'full_body_candidates':len(candidates),'candidate_reports':dict(collections.Counter(c['base']['report'] for c in candidates)),
 'candidate_groups':dict(collections.Counter(c['path'].split('/')[4] for c in candidates))},indent=2))
