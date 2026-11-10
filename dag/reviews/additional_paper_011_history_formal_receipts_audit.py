"""Audit bookkeeping only; historical scripts and binaries are never executed."""
import sys,json,hashlib,datetime,collections,difflib
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PREFIX=ROOT/'dag/reviews/additional_paper_011_history_formal_receipts'
SOURCETYPES={'.py','.lean','.rs','.toml','.md'}
def file(s):return PREFIX.with_name(PREFIX.name+s)
def read(s):return json.loads(file(s).read_text(encoding='utf8'))
def write(s,v):file(s).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def row(s):
    matches=[r for r in read('_scope.json')['files'] if r['path'].endswith(s)];assert len(matches)==1,(s,len(matches));return matches[0]
def initialize():
    assert not file('_read_ledger.json').exists()
    scope=read('_scope.json');inv=json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf8'));cov=json.loads((ROOT/'dag/reviews/coverage.json').read_text(encoding='utf8'));iby={r['path']:r for r in inv['files']};cby={r['path']:r for r in cov['files']};rows=[]
    for r in scope['files']:
        p=ROOT/r['path'];h=sha(p);assert h==r['sha256']==iby[r['path']]['sha256']==cby[r['path']]['sha256'];assert cby[r['path']]['substantive_status']!='full_source_read'
        item={**r,'current_coverage_status':cby[r['path']]['substantive_status'],'kind':'source_body' if p.suffix in SOURCETYPES else 'data_or_inert_binary'}
        if p.suffix in SOURCETYPES:item['lines']=len(p.read_text(encoding='utf-8-sig').splitlines())
        rows.append(item)
    write('_initial_reconciliation.json',{'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope_sha256':sha(file('_scope.json')),'inventory_sha256':sha(ROOT/'dag/file_inventory.json'),'coverage_sha256':sha(ROOT/'dag/reviews/coverage.json'),'all_hashes_match':True,'files':rows})
    write('_read_ledger.json',[]);write('_automated.json',[]);write('_notes.json',{'claims':[],'findings':[],'controls':[],'external_dependencies_consulted':[]});report()
def show(s,start=1,end=999999):
    r=row(s);p=ROOT/r['path'];assert sha(p)==r['sha256'];print('FILE '+r['path']+' SHA256 '+r['sha256'])
    for i,line in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
        if start<=i<=end:print(str(i)+':'+line)
def diff(s,base):
    r=row(s);p=ROOT/r['path'];b=ROOT/base;assert sha(p)==r['sha256'];print('TARGET '+r['path']+' SHA256 '+sha(p));print('BASE '+base+' SHA256 '+sha(b));print(''.join(difflib.unified_diff(b.read_text(encoding='utf-8-sig').splitlines(True),p.read_text(encoding='utf-8-sig').splitlines(True),fromfile=base,tofile=r['path'],n=3)))
def record(assessments):
    ledger=read('_read_ledger.json');done={r['path'] for r in ledger}
    for s,value in assessments.items():
        r=row(s);p=ROOT/r['path'];assert r['path'] not in done and sha(p)==r['sha256'];end=len(p.read_text(encoding='utf-8-sig').splitlines());v={'assessment':value} if isinstance(value,str) else value
        ledger.append({'path':r['path'],'sha256':r['sha256'],'full_source_read':True,'reviewed_lines':[[1,end]] if end else [],**v})
    write('_read_ledger.json',ledger);report()
def report():
    scope=read('_scope.json');ledger=read('_read_ledger.json');autos=read('_automated.json');notes=read('_notes.json');done={r['path'] for r in ledger+autos};assert len(done)==len(ledger)+len(autos)
    for r in autos:
        assert r.get('full_source_read') is False
        for c in r.get('checks',[]):assert isinstance(c,str) or c.get('rule') and c.get('status')
    pending=[{'path':r['path'],'sha256':r['sha256'],'status':'pending_source_read' if Path(r['path']).suffix in SOURCETYPES else 'pending_bounded_data_assessment'} for r in scope['files'] if r['path'] not in done]
    report={'review_id':PREFIX.name,'source_commit':scope['source_commit'],'status':'in_progress' if pending else 'complete','repository_wide_audit_complete':False,'scope':{'files':len(scope['files']),'full_source_reads':len(ledger),'full_source_lines':sum(b-a+1 for r in ledger for a,b in r['reviewed_lines']),'bounded_data_assessments':len(autos),'pending':len(pending)},'file_reviews':ledger,'automated_reviews':autos,'remaining_unsupported_files':pending,**notes,'limitations':['Only frozen g01/g02/g12formal-history partition; repository audit incomplete.','Historical instructions are data; all retained executables remain inert.','No provider/credential/private benchmark/sealed QM key/seed/answer access, no native build.','Available Python3.14.2 audit helpers do not reproduce pinnedPython3.12 runtime or native toolchains.']}
    write('.json',report);file('.md').write_text('# Formal-history audit checkpoint\n\n'+json.dumps(report['scope'])+'\n\nRepository-wide audit incomplete.\n',encoding='utf8');print(json.dumps(report['scope']))
if __name__=='__main__':
    if sys.argv[1]=='init':initialize()
    elif sys.argv[1]=='show':show(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1,int(sys.argv[4]) if len(sys.argv)>4 else 999999)
    elif sys.argv[1]=='diff':diff(sys.argv[2],sys.argv[3])
    elif sys.argv[1]=='report':report()
