"""Paper 011 core audit bookkeeping. Original files are read only."""
import sys,json,hashlib,datetime
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PREFIX=ROOT/'dag/reviews/additional_paper_011_core'
def file(s):return PREFIX.with_name(PREFIX.name+s)
def read(s):return json.loads(file(s).read_text(encoding='utf8'))
def write(s,v):file(s).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def initialize():
    assert not file('_read_ledger.json').exists()
    scope=read('_scope.json');inv=json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf8'));iby={r['path']:r for r in inv['files']};cp=ROOT/'dag/reviews/coverage.json';cov=json.loads(cp.read_text(encoding='utf8'));cby={r['path']:r for r in cov['files']}
    rows=[]
    for r in scope['files']:
        p=ROOT/r['path'];digest=sha(p);assert digest==r['sha256']==iby[r['path']]['sha256']==cby[r['path']]['sha256']
        rows.append({'path':r['path'],'sha256':digest,'lines':len(p.read_text(encoding='utf-8-sig').splitlines()),'current_coverage_status':cby[r['path']]['substantive_status']})
    write('_initial_reconciliation.json',{'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inventory_sha256':sha(ROOT/'dag/file_inventory.json'),'coverage_sha256':sha(cp),'scope_sha256':sha(file('_scope.json')),'files':rows,'all_hashes_match':True})
    write('_read_ledger.json',[]);write('_notes.json',{'claims':[],'findings':[],'controls':[],'external_dependencies_consulted':[]});write('_automated.json',[]);report()
def show(s,start=1,end=999999):
    rows=[r for r in read('_scope.json')['files'] if r['path'].endswith(s)];assert len(rows)==1
    r=rows[0];p=ROOT/r['path'];assert sha(p)==r['sha256'];print('FILE '+r['path']+' SHA256 '+r['sha256'])
    for n,l in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
        if start<=n<=end:print(str(n)+':'+l)
def record(assessments):
    scope=read('_scope.json');ledger=read('_read_ledger.json');done={r['path'] for r in ledger}
    for s,assessment in assessments.items():
        rows=[r for r in scope['files'] if r['path'].endswith(s)];assert len(rows)==1;r=rows[0];assert r['path'] not in done
        p=ROOT/r['path'];assert sha(p)==r['sha256'];end=len(p.read_text(encoding='utf-8-sig').splitlines())
        ledger.append({'path':r['path'],'sha256':r['sha256'],'full_source_read':True,'reviewed_lines':[[1,end]] if end else [],'assessment':assessment})
    write('_read_ledger.json',ledger);report()
def report():
    s=read('_scope.json');ledger=read('_read_ledger.json');autos=read('_automated.json');notes=read('_notes.json');done={r['path'] for r in ledger+autos};assert len(done)==len(ledger)+len(autos)
    for r in autos:
        for c in r.get('checks',[]):assert isinstance(c,str) or c.get('rule') and c.get('status')
    pending=[{'path':r['path'],'sha256':r['sha256'],'status':'pending_source_read' if r['path'].endswith('.py') else 'pending_data_assessment'} for r in s['files'] if r['path'] not in done]
    report={'review_id':PREFIX.name,'source_commit':s['source_commit'],'status':'in_progress' if pending else 'complete','scope':{'files':len(s['files']),'full_source_reads':len(ledger),'full_source_lines':sum(b-a+1 for r in ledger for a,b in r['reviewed_lines']),'bounded_data_assessments':len(autos),'pending':len(pending)},'file_reviews':ledger,'automated_reviews':autos,'remaining_unsupported_files':pending,**notes,'limitations':['Only this frozen Paper 011 core partition is covered; the repository-wide audit remains incomplete.','No providers, paid models, credentials, sealed QM key, broad native builds or unreviewed binary execution.','Source reading and bounded synthetic controls do not authenticate historical runs or external mathematical claims.']}
    write('.json',report);file('.md').write_text('# Paper 011 core audit checkpoint\n\n'+json.dumps(report['scope'])+'\n\nStatus: '+report['status']+'. The repository-wide audit remains incomplete.\n',encoding='utf8');print(json.dumps(report['scope']))
if __name__=='__main__':
    if sys.argv[1]=='init':initialize()
    elif sys.argv[1]=='show':show(sys.argv[2],int(sys.argv[3]) if len(sys.argv)>3 else 1,int(sys.argv[4]) if len(sys.argv)>4 else 999999)
    elif sys.argv[1]=='report':report()
