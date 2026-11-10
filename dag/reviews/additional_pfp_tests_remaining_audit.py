"""Explicit read receipts for frozen440 test/support slice; never imports test sources."""
import sys,json,hashlib,datetime,collections,subprocess,difflib,ast
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PREFIX=ROOT/'dag/reviews/additional_pfp_tests_remaining';SCOPE=PREFIX.with_name(PREFIX.name+'_scope.json')
def file(s):return PREFIX.with_name(PREFIX.name+s)
def read(s):return json.loads(file(s).read_text(encoding='utf8'))
def write(s,v):file(s).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scope():return json.loads(SCOPE.read_text(encoding='utf8'))
def row(path):
 r=dict(next(r for r in scope()['files'] if r['path']==path))
 if file('_authorized_revisions.json').exists():r.update(read('_authorized_revisions.json').get(path,{}))
 return r
def source(path,current=False):
 r=row(path)
 if r.get('original_git_object') and not current:p=file(r.get('preserved_original_suffix','_original_consistency_teaching.py.txt'))
 else:p=ROOT/path
 assert sha(p)==(r.get('current_sha256',r['sha256']) if current else r['sha256'])
 return p.read_text(encoding='utf-8-sig').splitlines()
def show(path,start=1,end=None,current=False):
 lines=source(path,current);r=row(path);end=end or len(lines)
 print('FILE '+path+' '+('CURRENT' if current else 'ORIGINAL')+' SHA256 '+(r.get('current_sha256',r['sha256']) if current else r['sha256'])+' TOTAL_LINES '+str(len(lines)))
 for i in range(start,min(end,len(lines))+1):print(str(i)+':'+lines[i-1])
 if not lines:print('[EMPTY BODY;0lines]')
def record(path,start,end,assessment,current=False):
 r=row(path);lines=source(path,current);assert (not lines and start==end==0) or 1<=start<=end<=len(lines)
 items=read('_read_ledger.json');key='current_adapted' if current else 'original'
 assert not any(x['path']==path and x.get('version','original')==key and not(end<x['lines'][0] or start>x['lines'][1]) for x in items)
 items.append({'path':path,'sha256':r.get('current_sha256',r['sha256']) if current else r['sha256'],'version':key,'lines':[start,end],'empty_file_read':not lines,'assessment':assessment});write('_read_ledger.json',items)
def report():
 sc=scope();idx=read('_index.json');ledger=read('_read_ledger.json');notes=read('_notes.json');reviews=[];pending=[];data=read('_data_reviews.json');bounded={x['path'] for x in data}
 for x in data:assert not x.get('full_source_read',False) and all(isinstance(c,str) or ('rule'in c and 'status'in c) for c in x['checks'])
 for r in idx['files']:
  parts=sorted([x for x in ledger if x['path']==r['path'] and x['version']=='original'],key=lambda x:x['lines']);covered={i for x in parts if not x['empty_file_read'] for i in range(x['lines'][0],x['lines'][1]+1)};full=bool(parts) and covered==set(range(1,r['line_count']+1))
  if parts:
   rec={'path':r['path'],'sha256':r['sha256'],'full_source_read':full,'reviewed_lines':[x['lines'] for x in parts if not x['empty_file_read']],'line_count':r['line_count'],'empty_file_read':bool(parts) and r['line_count']==0,'assessment':' '.join(x['assessment'] for x in parts),'chunk_assessments':parts}
   binding=row(r['path'])
   if binding.get('original_git_object'):rec.update(original_git_object=binding['original_git_object'],current_sha256=binding['current_sha256'],current_adapted_reads=[x for x in ledger if x['path']==r['path'] and x['version']=='current_adapted'],migration_receipt=binding.get('migration_receipt'))
   reviews.append(rec)
  if not full and r['path'] not in bounded:pending.append({'path':r['path'],'sha256':r['sha256'],'unread_line_count':r['line_count']-len(covered),'first_unread_line':next((i for i in range(1,r['line_count']+1) if i not in covered),None),'reviewed_lines':[x['lines'] for x in parts]})
 counts={'files':len(sc['files']),'original_bytes':sum(x['size_bytes'] for x in sc['files']),'original_lines':sum(x['line_count'] for x in idx['files']),'full_source_reads':sum(x['full_source_read'] for x in reviews),'partial_source_reads':sum(not x['full_source_read'] for x in reviews),'bounded_data_dispositions':len(data),'reviewed_original_lines':sum(x['lines'][1]-x['lines'][0]+1 for x in ledger if x['version']=='original' and not x['empty_file_read']),'pending_files':len(pending)}
 out={'review_id':PREFIX.name,'source_commit':sc['source_commit'],'status':'complete' if not pending and notes.get('analysis_complete') else 'in_progress','repository_wide_audit_complete':False,'scope':counts,'file_reviews':reviews,'automated_reviews':data,'remaining_unsupported_files':pending,**notes};write('.json',out)
 file('.md').write_text('# PFP remaining tests/support audit checkpoint\n\n'+json.dumps(counts)+'\n\nStatus: '+out['status']+'. Every pending path is explicit in JSON. Full body reads and bounded data dispositions remain separate. Repository audit incomplete.\n',encoding='utf8');print(json.dumps(counts))
def initialize():
 assert not file('_read_ledger.json').exists();sc=scope();inv={x['path']:x for x in json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))['files']};cov={x['path']:x for x in json.loads((ROOT/'dag/reviews/coverage.json').read_text(encoding='utf8'))['files']};rows=[]
 for r in sc['files']:
  assert r['sha256']==inv[r['path']]['sha256'];p=ROOT/r['path'];assert sha(p)==r.get('current_sha256',r['sha256']);assert not any(x.get('status')=='full_source_read' for x in cov[r['path']].get('reading_receipts',[]))
  if r.get('original_git_object'):
   original=subprocess.run(['git','show',r['original_git_object']],cwd=ROOT,check=True,stdout=subprocess.PIPE).stdout;assert hashlib.sha256(original).hexdigest()==r['sha256'] and len(original)==r['size_bytes'];file('_original_consistency_teaching.py.txt').write_bytes(original)
  else:assert p.stat().st_size==r['size_bytes']
  lines=source(r['path']);rows.append({**r,'line_count':len(lines),'current_line_count':len(p.read_text(encoding='utf-8-sig').splitlines()),'initial_coverage_status':cov[r['path']]['substantive_status']})
 write('_initial_reconciliation.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_sha256':sha(SCOPE),'inventory_sha256':sha(ROOT/'dag/file_inventory.json'),'coverage_sha256':sha(ROOT/'dag/reviews/coverage.json'),'current_match_original':439,'authorized_adapted_original_captured':1,'files':rows});write('_index.json',{'files':rows});write('_read_ledger.json',[]);write('_data_reviews.json',[]);write('_notes.json',{'analysis_complete':False,'claims':[],'findings':[],'controls':[],'external_dependencies_consulted':[{'path':'dag/reviews/additional_pfp_domain_remaining.json','sha256':'77da44d9ed4af533ecb63ebbe9c4c48485ecb75f948489f6cd6165e3a8694598','purpose':'Frozen domain owner assessments and exact source pins; no automatic test-body credit.'}],'limits':['Original source/history/shared manifests remain unchanged.','No broad suite, provider, credential, private benchmark/seed/key/answer, native build or retained executable access.','Body reading is explicit; AST parsing and generated data checks never count as full-source reading.','Authorized migration consumer original Git blob and current body are assessed separately; original coverage pins original bytes.']});report()
if __name__=='__main__':
 if sys.argv[1]=='init':initialize()
 elif sys.argv[1]=='show':show(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1,int(sys.argv[4]) if len(sys.argv)>4 else None)
 elif sys.argv[1]=='current':show(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1,int(sys.argv[4]) if len(sys.argv)>4 else None,True)
 elif sys.argv[1]=='bundle':
  for p in sys.argv[2:]:show(p)
 elif sys.argv[1]=='report':report()
 elif sys.argv[1]=='index':
  for r in read('_index.json')['files']:print(str(r['line_count']).rjust(5)+' '+r['path'])
