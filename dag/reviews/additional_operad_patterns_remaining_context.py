from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[2]
for filename in ['additional_operads_core_remaining.json','additional_eis_pciv_remaining.json','workflows_audit.json','additional_workflow_library_remaining.json','additional_wiki_workflow_dag.json']:
 p=R/'dag/reviews'/filename
 if not p.exists():continue
 j=json.loads(p.read_text());print('REPORT',filename,hashlib.sha256(p.read_bytes()).hexdigest())
 for f in j.get('file_reviews',[]):
  q=f.get('path','')
  if ('anti_pattern_auditor.py' in q or 'residual_honesty.py' in q or 'ab_discrete_bianchi' in q or 'ab_tao_universal' in q or 'pharmacy_catalog.py' in q or 'pattern' in q and 'domain/models.py' in q):print(json.dumps(f))
 for f in j.get('findings',[]):
  s=json.dumps(f)
  if any(x in s.lower() for x in ['pattern catalog','pattern_id','antibod','contractiv','contractive','wf38','wf31']):print(json.dumps(f)[:6000])
print('FAMILY FILES')
for p in (R/'dag').glob('*workflow*'):print(p.relative_to(R).as_posix())
