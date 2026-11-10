"""Frozen remaining adapter-scope audit bookkeeping; never writes original sources."""
import sys,json,hashlib,datetime,collections
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PREFIX=ROOT/'dag/reviews/additional_pfp_adapters'
def file(s):return PREFIX.with_name(PREFIX.name+s)
def read(s):return json.loads(file(s).read_text(encoding='utf8'))
def write(s,v):file(s).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze():
    assert not file('_scope.json').exists()
    inv=json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf8'));cp=ROOT/'dag/reviews/coverage.json';coverage=json.loads(cp.read_text(encoding='utf8'));by={r['path']:r for r in coverage['files']}
    new=[];old=[]
    for r in inv['files']:
        if not r['path'].startswith('pfp/infrastructure/adapters/'):continue
        actual=sha(ROOT/r['path']);c=by[r['path']];assert actual==r['sha256']==c['sha256'],r['path']
        enriched={**r,'current_sha256':actual,'coverage_status_at_freeze':c['substantive_status']}
        if c['substantive_status']=='full_text_source_review_recorded':old.append({**enriched,'prior_receipts':c['reading_receipts']})
        else:new.append(enriched)
    write('_scope.json',{'source_commit':inv['local_head'],'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'coverage_snapshot_sha256':sha(cp),'scope_rule':'path starts pfp/infrastructure/adapters/; exclude already fully reviewed matching-hash rows','candidate_files':len(new)+len(old),'files':new,'excluded_already_fully_reviewed':old})
    write('_read_ledger.json',[]);write('_notes.json',{'family_assessments':[],'claims':[],'findings':[],'controls':[]});report()
def show(*selectors):
    for r in read('_scope.json')['files']:
        p=r['path']
        if selectors and not any(p.endswith(s) or '/'+s+'/' in p for s in selectors):continue
        print('\nFILE '+p+' SHA256 '+r['sha256'])
        for n,l in enumerate((ROOT/p).read_text(encoding='utf-8-sig').splitlines(),1):print(str(n)+':'+l)
def show_range(selector,start,end):
    rows=[r for r in read('_scope.json')['files'] if r['path'].endswith(selector)];assert len(rows)==1
    r=rows[0];p=ROOT/r['path'];assert sha(p)==r['sha256']
    print('FILE '+r['path']+' SHA256 '+r['sha256'])
    for n,l in enumerate(p.read_text(encoding='utf-8-sig').splitlines(),1):
        if start<=n<=end:print(str(n)+':'+l)
def record(assessments):
    scope=read('_scope.json');ledger=read('_read_ledger.json');done={r['path'] for r in ledger}
    for suffix,assessment in assessments.items():
        matches=[r for r in scope['files'] if r['path'].endswith(suffix)];assert len(matches)==1,(suffix,len(matches));r=matches[0];assert r['path'] not in done,r['path']
        p=ROOT/r['path'];assert sha(p)==r['sha256'];lines=len(p.read_text(encoding='utf-8-sig').splitlines())
        ledger.append({'path':r['path'],'sha256':r['sha256'],'full_source_read':True,'reviewed_lines':[[1,lines]] if lines else [],'assessment':assessment})
    write('_read_ledger.json',ledger);report()
def report():
    scope=read('_scope.json');ledger=read('_read_ledger.json');notes=read('_notes.json');autos=read('_automated.json') if file('_automated.json').exists() else []
    partials=read('_partial_reads.json') if file('_partial_reads.json').exists() else []
    partials=[r for r in partials if r['path'] not in {v['path'] for v in ledger}]
    for r in autos:
        for c in r.get('checks',[]):assert isinstance(c,str) or c.get('rule') and c.get('status')
    done={r['path'] for r in ledger+autos};assert len(done)==len(ledger)+len(autos)
    pending=[{'path':r['path'],'sha256':r['sha256'],'status':'pending_source_read'} for r in scope['files'] if r['path'] not in done]
    report={'review_id':PREFIX.name,'status':'in_progress' if pending else 'complete','source_commit':scope['source_commit'],'scope_rule':scope['scope_rule'],'scope':{'candidate_files':scope['candidate_files'],'excluded_already_fully_reviewed':len(scope['excluded_already_fully_reviewed']),'files':len(scope['files']),'full_source_reads':len(ledger),'full_source_lines':sum(b-a+1 for r in ledger for a,b in r['reviewed_lines']),'automated_files':len(autos),'pending':len(pending)},'completion_basis':'Only actual source-body reading receives full_source_read credit. Parsed data and bounded controls are separately recorded.','file_reviews':ledger+partials,'automated_reviews':autos,'remaining_unsupported_files':pending,**notes,'limitations':['The repository-wide every-file audit remains incomplete.','No provider/private benchmark/sealed material access, original source edits or broad native builds.','Prior fully reviewed paths are excluded without duplicate credit.']}
    write('.json',report);file('.md').write_text('# PFP adapters remaining-path audit\n\n'+json.dumps(report['scope'])+'\n\nStatus: '+report['status']+'. The repository-wide audit remains incomplete.\n',encoding='utf8');print(json.dumps(report['scope']))
if __name__=='__main__':
    if sys.argv[1]=='freeze':freeze()
    elif sys.argv[1]=='show':show(*sys.argv[2:])
    elif sys.argv[1]=='range':show_range(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
    elif sys.argv[1]=='report':report()
