from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'dag/reviews/additional_operads_education_atlas'
scope=json.loads(Path(str(P)+'_scope.json').read_text());notes=json.loads(Path(str(P)+'_notes.json').read_text());ledger=json.loads(Path(str(P)+'_read_ledger.json').read_text())
reviews=[]
for key,assessment in notes['assessments'].items():
 r=scope['files'][int(key)];b=(ROOT/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']
 ranges=[v for e in ledger if e['path']==r['path'] and e['sha256']==r['sha256'] for v in e['reviewed_lines']]
 seen=set(n for a,z in ranges for n in range(a,z+1));assert seen==set(range(1,r['lines']+1))
 reviews.append(dict(path=r['path'],sha256=r['sha256'],bytes=r['bytes'],full_source_read=True,reviewed_lines=[[1,r['lines']]],assessment=assessment))
r=scope['supporting_source'];reviews.append(dict(path=r['path'],sha256=r['original_sha256'],bytes=r['original_bytes'],full_source_read=True,reviewed_lines=[[1,r['original_lines']]],assessment=notes['supporting_assessment'],current_source=r,reading_basis='Complete original archive body and complete current body plus complete unified delta; authorized navigation edit only.',supporting_source_outside_52=True))
pending=[r['path'] for i,r in enumerate(scope['files']) if str(i) not in notes['assessments']]
report={'source_commit':scope['source_commit'],'status':'in_progress','scope_manifest':P.relative_to(ROOT).as_posix()+'_scope.json','summary':{'frozen_scope':52,'supporting_sources':1,'full_scope_bodies':len(reviews)-1,'full_supporting_bodies':1,'pending':len(pending)},'file_reviews':reviews,'pending_paths':pending,'claims':[],'findings':[],'limits':['Checkpoint; remaining sources and all images are still pending.','Historical test tables and prior reviews are not fresh execution. No production/native/provider/private-benchmark work.']}
Path(str(P)+'.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
md=['# OPERADS education atlas review checkpoint','',json.dumps(report['summary']),'']
for r in reviews:md += ['## '+r['path'],'',r['assessment'],'']
md += ['## Pending','']+['- '+p for p in pending]
Path(str(P)+'.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps(report['summary']))
