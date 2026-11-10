from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
inv=json.loads(Path(str(P)+'_inventory.json').read_text());rows=inv['files'];notes=json.loads(Path(str(P)+'_notes.json').read_text());reviews=[]
for k,n in notes['assessments'].items():
 r=rows[int(k)];assert hashlib.sha256((R/r['path']).read_bytes()).hexdigest()==r['sha256']
 full=n.get('full_source_read',True)
 reviews.append(dict(path=r['path'],sha256=r['sha256'],bytes=r['bytes'],source_line_count=r['lines'],
  full_source_read=full,reviewed_lines=n.get('reviewed_lines',[[1,r['lines']]] if full else []),
  review_level=n.get('review_level','full_text_source_review'),reading_method=n.get('reading_method','complete numbered body display'),
  assessment=n['assessment'],**{k:v for k,v in n.items() if k not in {'assessment','full_source_read','reviewed_lines','review_level','reading_method'}}))
pending=[r['path'] for r in rows if str(r['index']) not in notes['assessments']]
report=dict(status='in_progress',scope_manifest=P.relative_to(R).as_posix()+'_scope.json',scope_sha256=inv['scope_sha256'],
 summary=dict(frozen_paths=len(rows),disposed=len(reviews),full_source_reads=sum(r['full_source_read'] for r in reviews),bounded_assessments=sum(not r['full_source_read'] for r in reviews),pending=len(pending)),
 file_reviews=reviews,pending_paths=pending,claims=[],findings=[],candidate_findings=notes.get('candidate_findings',[]),
 limits=['Checkpoint; no automatic full-body credit from hashing/parsing or linked sources.','No retained program, provider, native or private benchmark execution. Historical tests remain historical.'])
Path(str(P)+'.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
md=['# Operad receipts audit checkpoint','',str(report['summary']),'']
for r in reviews:md+=['## '+r['path'],'',r['assessment'],'']
Path(str(P)+'.md').write_text('\n'.join(md)+'\n',encoding='utf8');print(json.dumps(report['summary']))
