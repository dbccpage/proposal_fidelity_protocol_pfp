"""Scoped domain body-reading receipts. Never imports the reviewed package."""
import sys,json,hashlib,datetime,collections
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PREFIX=ROOT/'dag/reviews/additional_pfp_domain_remaining'
SCOPE=ROOT/'dag/reviews/additional_pfp_domain_remaining_scope.json'
def file(s):return PREFIX.with_name(PREFIX.name+s)
def read(s):return json.loads(file(s).read_text(encoding='utf8'))
def write(s,x):file(s).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scope():return json.loads(SCOPE.read_text(encoding='utf8'))
def row(path):
 rows=[r for r in scope()['files'] if r['path']==path];assert len(rows)==1;return rows[0]
def show(path,start=1,end=None):
 r=row(path);p=ROOT/path;assert sha(p)==r['sha256'];body=p.read_text(encoding='utf-8-sig').splitlines();end=end or len(body)
 print('FILE '+path+' SHA256 '+r['sha256']+' TOTAL_LINES '+str(len(body)))
 for i in range(start,min(end,len(body))+1):print(str(i)+':'+body[i-1])
 if not body:print('[EMPTY BODY;0 lines]')
def record(path,start,end,assessment,topics=None):
 r=row(path);assert sha(ROOT/path)==r['sha256'];body=(ROOT/path).read_text(encoding='utf-8-sig').splitlines();assert (not body and start==end==0) or 1<=start<=end<=len(body)
 rows=read('_read_ledger.json');assert not any(x['path']==path and not(end<x['lines'][0] or start>x['lines'][1]) for x in rows)
 rows.append({'path':path,'sha256':r['sha256'],'lines':[start,end],'empty_file_read':not body,'assessment':assessment,'topics':topics or []});write('_read_ledger.json',rows)
def report():
 sc=scope();idx=read('_index.json');chunks=read('_read_ledger.json');notes=read('_notes.json');reviews=[];pending=[]
 automated=read('_data_reviews.json') if file('_data_reviews.json').exists() else []
 automated_paths={x['path'] for x in automated};assert len(automated_paths)==len(automated)
 for x in automated:
  assert x['sha256']==row(x['path'])['sha256'] and not x.get('full_source_read',False)
  assert all(isinstance(c,str) or ('rule' in c and 'status' in c) for c in x['checks'])
 for r in idx['files']:
  parts=sorted([x for x in chunks if x['path']==r['path']],key=lambda x:x['lines']);covered={i for x in parts if not x['empty_file_read'] for i in range(x['lines'][0],x['lines'][1]+1)};full=bool(parts) and covered==set(range(1,r['line_count']+1))
  if parts:reviews.append({'path':r['path'],'sha256':r['sha256'],'full_source_read':full,'reviewed_lines':[x['lines'] for x in parts if not x['empty_file_read']],'line_count':r['line_count'],'empty_file_read':bool(parts) and r['line_count']==0,'assessment':' '.join(x['assessment'] for x in parts),'chunk_assessments':parts})
  if not full and r['path'] not in automated_paths:pending.append({'path':r['path'],'sha256':r['sha256'],'unread_line_count':r['line_count']-len(covered),'first_unread_line':next((i for i in range(1,r['line_count']+1) if i not in covered),None),'reviewed_lines':[x['lines'] for x in parts]})
 result={'review_id':PREFIX.name,'source_commit':sc['source_commit'],'status':'complete' if not pending and notes.get('analysis_complete') else 'in_progress','repository_wide_audit_complete':False,'scope':{'files':len(sc['files']),'bytes':sum(x['bytes'] for x in sc['files']),'source_lines':sum(x['line_count'] for x in idx['files']),'full_source_reads':sum(r['full_source_read'] for r in reviews),'partial_source_reads':sum(not r['full_source_read'] for r in reviews),'bounded_data_dispositions':len(automated),'reviewed_chunk_lines':sum(x['lines'][1]-x['lines'][0]+1 for x in chunks if not x['empty_file_read']),'pending_files':len(pending)},'file_reviews':reviews,'automated_reviews':automated,'remaining_unsupported_files':pending,**notes}
 write('.json',result);file('.md').write_text('# PFP domain audit checkpoint\n\n'+json.dumps(result['scope'])+'\n\nStatus: in progress. Full reads, partial reads and pending paths are explicit in the JSON. Repository-wide audit incomplete.\n',encoding='utf8');print(json.dumps(result['scope']))
def initialize():
 assert not file('_read_ledger.json').exists();sc=scope();inv={r['path']:r for r in json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))['files']};cov={r['path']:r for r in json.loads((ROOT/'dag/reviews/coverage.json').read_text(encoding='utf8'))['files']};rows=[]
 for r in sc['files']:
  p=ROOT/r['path'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']==inv[r['path']]['sha256']==cov[r['path']]['sha256'];assert cov[r['path']]['substantive_status'] not in ('full_source_read','full_text_source_review_recorded');assert not any(x.get('status')=='full_source_read' for x in cov[r['path']].get('reading_receipts',[]));assert len(b)==r['bytes']
  rows.append({**r,'line_count':len(b.decode('utf-8-sig').splitlines()),'coverage_status_at_reconciliation':cov[r['path']]['substantive_status']})
 stamp={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_sha256':sha(SCOPE),'inventory_sha256':sha(ROOT/'dag/file_inventory.json'),'coverage_sha256':sha(ROOT/'dag/reviews/coverage.json'),'all_hashes_match':True,'files':rows}
 write('_initial_reconciliation.json',stamp);write('_index.json',{'files':rows});write('_read_ledger.json',[]);write('_notes.json',{'analysis_complete':False,'claims':[],'findings':[],'controls':[],'external_dependencies_consulted':[],'limits':['Only explicit full-body or complete reviewed-delta receipts receive full-source credit.','All original source and historical evidence are preserved.','No provider, private benchmark/seed/key/answer, original execution or native build has occurred in this slice.']});report()
if __name__=='__main__':
 if sys.argv[1]=='init':initialize()
 elif sys.argv[1]=='show':show(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1,int(sys.argv[4]) if len(sys.argv)>4 else None)
 elif sys.argv[1]=='report':report()
 elif sys.argv[1]=='bundle':
  for path in sys.argv[2:]:show(path)
 elif sys.argv[1]=='index':
  for r in read('_index.json')['files']:print(str(r['line_count']).rjust(5)+' '+r['path'])
