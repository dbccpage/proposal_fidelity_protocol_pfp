"""Frozen-source review receipts only; no Rust/Cargo or original program execution."""
import sys,json,hashlib,datetime
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PREFIX=ROOT/'dag/reviews/additional_rust_homology_remaining'
def file(s):return PREFIX.with_name(PREFIX.name+s)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(s):return json.loads(file(s).read_text(encoding='utf8'))
def write(s,x):file(s).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def scope():return read('_scope.json')
def row(p):return next(x for x in scope()['files'] if x['path']==p)
def source(p):
 assert sha(ROOT/p)==row(p)['sha256'];return (ROOT/p).read_text(encoding='utf-8-sig').splitlines()
def show(p,start=1,end=None):
 lines=source(p);end=end or len(lines);print('FILE '+p+' SHA256 '+row(p)['sha256']+' TOTAL_LINES '+str(len(lines)))
 for i in range(start,min(end,len(lines))+1):print(str(i)+':'+lines[i-1])
 if not lines:print('[EMPTY BODY]')
def ev(p,start,end):return {'path':p,'sha256':row(p)['sha256'],'lines':[start,end]}
def record(p,start,end,assessment):
 lines=source(p);assert (start==end==0 and not lines) or 1<=start<=end<=len(lines)
 items=read('_read_ledger.json');assert not any(x['path']==p and not(end<x['lines'][0] or start>x['lines'][1]) for x in items)
 items.append({**ev(p,start,end),'empty_file_read':not lines,'assessment':assessment});write('_read_ledger.json',items)
def report():
 ledger=read('_read_ledger.json');notes=read('_notes.json');reviews=[];pending=[]
 for r in read('_index.json')['files']:
  chunks=sorted([x for x in ledger if x['path']==r['path']],key=lambda x:x['lines'])
  covered={i for x in chunks if not x['empty_file_read'] for i in range(x['lines'][0],x['lines'][1]+1)}
  full=bool(chunks) and covered==set(range(1,r['line_count']+1))
  if chunks:reviews.append({'path':r['path'],'sha256':r['sha256'],'line_count':r['line_count'],'full_source_read':full,'empty_file_read':r['line_count']==0,'reviewed_lines':[x['lines'] for x in chunks if not x['empty_file_read']],'assessment':' '.join(x['assessment'] for x in chunks),'chunk_assessments':chunks})
  if not full:pending.append({'path':r['path'],'sha256':r['sha256'],'reviewed_lines':[x['lines'] for x in chunks if not x['empty_file_read']],'unread_line_count':r['line_count']-len(covered),'first_unread_line':next((i for i in range(1,r['line_count']+1) if i not in covered),None)})
 counts={'files':len(scope()['files']),'original_bytes':sum(x['size_bytes'] for x in scope()['files']),'original_lines':sum(x['line_count'] for x in read('_index.json')['files']),'full_source_reads':sum(x['full_source_read'] for x in reviews),'partial_source_reads':sum(not x['full_source_read'] for x in reviews),'reviewed_original_lines':sum(len(set(i for lo,hi in x['reviewed_lines'] for i in range(lo,hi+1))) for x in reviews),'bounded_data_dispositions':0,'pending_files':len(pending)}
 out={'review_id':PREFIX.name,'source_commit':scope()['source_commit'],'status':'complete' if not pending and notes.get('analysis_complete') else 'in_progress','repository_wide_audit_complete':False,'scope':counts,'file_reviews':reviews,'automated_reviews':[],'remaining_unsupported_files':pending,**notes};write('.json',out)
 file('.md').write_text('# Rust core_homology audit checkpoint\n\n'+json.dumps(counts)+'\n\nStatus: '+out['status']+'. Explicit pending paths and full/partial read receipts are in JSON. No Rust/native execution. Repository audit remains incomplete.\n',encoding='utf8');print(json.dumps(counts))
def validate(label):
 r=read('.json');idx={x['path']:x for x in read('_index.json')['files']}
 for p in idx:assert sha(ROOT/p)==idx[p]['sha256'] and len(source(p))==idx[p]['line_count']
 for x in r['file_reviews']:
  assert x['sha256']==idx[x['path']]['sha256'];covered=[i for lo,hi in x['reviewed_lines'] for i in range(lo,hi+1)];assert len(covered)==len(set(covered))
  if x['full_source_read']:assert covered==list(range(1,x['line_count']+1))
 for g in ('findings','claims','controls'):
  ids=[x['id'] for x in r[g]];assert len(ids)==len(set(ids))
  for x in r[g]:
   if g=='controls':assert 'rule'in x and 'status'in x
   for e in x.get('evidence',x.get('source_evidence',[])):assert e['sha256']==idx[e['path']]['sha256'] and 1<=e['lines'][0]<=e['lines'][1]<=idx[e['path']]['line_count']
   for k in ('helper','receipt'):
    if isinstance(x.get(k),dict):assert sha(ROOT/x[k]['path'])==x[k]['sha256']
 snap=file('_'+label+'_report.json.snapshot');assert not snap.exists();snap.write_bytes(file('.json').read_bytes())
 out={'status':'complete_scope_validated' if r['status']=='complete' else 'checkpoint_validated_incomplete','scope':r['scope'],'scope_sha256':sha(file('_scope.json')),'report_sha256':sha(file('.json')),'snapshot':str(snap.relative_to(ROOT)).replace('\\','/'),'snapshot_sha256':sha(snap),'all126_current_hashes_match_original':True,'source_ranges_and_evidence_pins_valid':True,'repository_wide_audit_complete':False};write('_'+label+'_validation.json',out);print(json.dumps(out))
def init():
 assert not file('_read_ledger.json').exists();assert sha(file('_scope.json'))=='6bcbbbca1fd29535e26badb949d0f4655439b42d5634e1be09c978bfdb3ca729'
 inv={x['path']:x for x in json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))['files']};cp=ROOT/'dag/reviews/coverage.json';cov={x['path']:x for x in json.loads(cp.read_text(encoding='utf8'))['files']};rows=[]
 for x in scope()['files']:
  assert x['sha256']==inv[x['path']]['sha256']==sha(ROOT/x['path']);assert (ROOT/x['path']).stat().st_size==x['size_bytes']
  assert not any(y.get('status')=='full_source_read' for y in cov[x['path']].get('reading_receipts',[]))
  rows.append({**x,'line_count':len(source(x['path'])),'initial_coverage_status':cov[x['path']]['substantive_status']})
 write('_initial_reconciliation.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_sha256':sha(file('_scope.json')),'inventory_sha256':sha(ROOT/'dag/file_inventory.json'),'coverage_sha256':sha(cp),'all126_original_and_current_hashes_match':True,'none_already_fully_reviewed':True,'files':rows});write('_index.json',{'files':rows});write('_read_ledger.json',[]);write('_notes.json',{'analysis_complete':False,'claims':[],'findings':[],'controls':[],'external_dependencies_consulted':[],'limits':['Original Rust/manifests and historical evidence remain unchanged.','No Rust/Cargo/native/provider or retained program execution, broad suite, credentials or private answer access.','Only complete displayed source bodies earn full reading credit; parse/census and narrow dependency consultations remain separate.','Independent exact finite controls are bounded to their declared carrier/input and do not establish general native correctness.']});report()
if __name__=='__main__':
 if sys.argv[1]=='init':init()
 elif sys.argv[1]=='show':show(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1,int(sys.argv[4]) if len(sys.argv)>4 else None)
 elif sys.argv[1]=='bundle':
  for p in sys.argv[2:]:show(p)
 elif sys.argv[1]=='report':report()
 elif sys.argv[1]=='validate':validate(sys.argv[2])
