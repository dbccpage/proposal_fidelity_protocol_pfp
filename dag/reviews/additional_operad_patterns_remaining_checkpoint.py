from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'dag/reviews/additional_operad_patterns_remaining'
scope=json.loads(Path(str(P)+'_scope.json').read_text());inventory=json.loads(Path(str(P)+'_inventory.json').read_text())['files']
notes=json.loads(Path(str(P)+'_notes.json').read_text());ledger=json.loads(Path(str(P)+'_read_ledger.json').read_text())
reviews=[]
for key,note in notes['assessments'].items():
    r=inventory[int(key)];assert hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']
    assert any(x['path']==r['path'] and x['sha256']==r['sha256'] and x['reviewed_lines']==[[1,r['lines']]] for x in ledger)
    reviews.append(dict(path=r['path'],sha256=r['sha256'],bytes=r['size_bytes'],full_source_read=True,reviewed_lines=[[1,r['lines']]],
        review_level='full_text_source_review',assessment=note['assessment'],mechanism=note['mechanism'],disposition=note['disposition'],
        actual_execution_status='pattern prose reviewed; no detector, transformation or historical witness executed in this lane'))
pending=[r['path'] for r in inventory if str(r['index']) not in notes['assessments']]
report={'source_commit':scope['source_commit'],'status':'in_progress','scope_manifest':P.relative_to(ROOT).as_posix()+'_scope.json',
    'summary':{'frozen_paths':198,'full_body_receipts':len(reviews),'pending':len(pending)},'file_reviews':reviews,'pending_paths':pending,
    'claims':[],'findings':[],'candidate_findings':notes.get('candidate_findings',[]),
    'limits':['Checkpoint; only explicitly assessed entries carry full-source receipts.','Historical quotations and linked sources are not newly read or executed owners. No provider/native/private-benchmark/source mutation work.']}
Path(str(P)+'.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
md=['# Operad pattern audit checkpoint','',str(report['summary']),'']
for r in reviews:md+=['## '+r['path'],'',r['assessment'],'']
md+=['## Pending','']+['- '+p for p in pending]
Path(str(P)+'.md').write_text('\n'.join(md)+'\n',encoding='utf-8');print(json.dumps(report['summary']))
