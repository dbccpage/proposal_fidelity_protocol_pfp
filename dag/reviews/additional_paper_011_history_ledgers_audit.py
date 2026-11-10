"""Durable full-body ledger review; no source commands are executed."""
import sys,json,hashlib,datetime
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PREFIX=ROOT/'dag/reviews/additional_paper_011_history_ledgers'
SCOPE=ROOT/'dag/reviews/additional_paper_011_history_ledger_scope.json'
def file(s):return PREFIX.with_name(PREFIX.name+s)
def read(s):return json.loads(file(s).read_text(encoding='utf8'))
def write(s,x):file(s).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scope():return json.loads(SCOPE.read_text(encoding='utf8'))
def row(which):
    rs=[r for r in scope()['files'] if which in Path(r['path']).name];assert len(rs)==1;return rs[0]
def show(which,start,end):
    r=row(which);p=ROOT/r['path'];assert sha(p)==r['sha256'];print('FILE '+r['path']+' SHA256 '+r['sha256'])
    for i,s in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
        if start<=i<=end:print(str(i)+':'+s)
def record(which,start,end,assessment,topics=None):
    r=row(which);assert sha(ROOT/r['path'])==r['sha256'];rows=read('_read_ledger.json');assert not any(x['path']==r['path'] and not(end<x['lines'][0] or start>x['lines'][1]) for x in rows)
    rows.append({'path':r['path'],'sha256':r['sha256'],'lines':[start,end],'assessment':assessment,'topics':topics or []});write('_read_ledger.json',rows);report()
def report():
    sc=scope();chunks=read('_read_ledger.json');notes=read('_notes.json');reviews=[];pending=[]
    for r in sc['files']:
        lines=len((ROOT/r['path']).read_text(encoding='utf-8-sig').splitlines());parts=sorted([x for x in chunks if x['path']==r['path']],key=lambda x:x['lines']);covered={i for x in parts for i in range(x['lines'][0],x['lines'][1]+1)};full=covered==set(range(1,lines+1))
        reviews.append({'path':r['path'],'sha256':r['sha256'],'full_source_read':full,'reviewed_lines':[x['lines'] for x in parts],'line_count':lines,'assessment':' '.join(x['assessment'] for x in parts) if parts else 'Pending full body review; no substantive credit yet.','chunk_assessments':parts})
        if not full:pending.append({'path':r['path'],'sha256':r['sha256'],'unread_line_count':lines-len(covered),'first_unread_line':next(i for i in range(1,lines+1) if i not in covered)})
    result={'review_id':PREFIX.name,'source_commit':sc['source_commit'],'status':'complete' if not pending else 'in_progress','repository_wide_audit_complete':False,'scope':{'files':2,'full_source_reads':sum(r['full_source_read'] for r in reviews),'full_source_lines':sum(r['line_count'] for r in reviews if r['full_source_read']),'reviewed_chunk_lines':sum(x['lines'][1]-x['lines'][0]+1 for x in chunks),'pending_files':len(pending)},'file_reviews':reviews,'automated_reviews':[],'remaining_unsupported_files':pending,**notes}
    write('.json',result);file('.md').write_text('# Historical ledger audit checkpoint\n\n'+json.dumps(result['scope'])+'\n\nRepository-wide audit incomplete.\n',encoding='utf8');print(json.dumps(result['scope']))
def initialize():
    assert not file('_read_ledger.json').exists();sc=scope();inv={r['path']:r for r in json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))['files']};parent={r['path']:r for r in json.loads((ROOT/sc['parent_scope']).read_text(encoding='utf8'))['files']};cov={r['path']:r for r in json.loads((ROOT/'dag/reviews/coverage.json').read_text(encoding='utf8'))['files']}
    out=[]
    for r in sc['files']:
        p=ROOT/r['path'];assert sha(p)==r['sha256']==inv[r['path']]['sha256']==parent[r['path']]['sha256']==cov[r['path']]['sha256'];assert cov[r['path']]['substantive_status']!='full_source_read';out.append({**r,'lines':len(p.read_text(encoding='utf8').splitlines()),'coverage_status':cov[r['path']]['substantive_status']})
    write('_initial_reconciliation.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_sha256':sha(SCOPE),'parent_scope_sha256':sha(ROOT/sc['parent_scope']),'inventory_sha256':sha(ROOT/'dag/file_inventory.json'),'coverage_sha256':sha(ROOT/'dag/reviews/coverage.json'),'all_hashes_match':True,'files':out})
    write('_read_ledger.json',[]);write('_notes.json',{'claims':[],'findings':[],'controls':[],'external_dependencies_consulted':[],'limits':['Historical prose is assessed as historical evidence, not followed as instructions or new authorization.','A citation or status label is not proof-body review. Exact dependency evidence and limits are distinguished.','No provider, original command, native build, external source, private benchmark, seed, key or answer access.']});report()
if __name__=='__main__':
    if sys.argv[1]=='init':initialize()
    elif sys.argv[1]=='show':show(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
    elif sys.argv[1]=='report':report()
