"""Bookkeeping for the C051–C059 remaining-scope source and certificate audit."""
import sys,json,re,hashlib,collections,datetime
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
PREFIX=ROOT/'dag/reviews/additional_challenges_051_059'
RULE=r'^workflows/tasks/certified_challenges/(?:c05[1-9]_[^/]+/|test_c05[1-9][^/]*\.py$)'
def file(s):return PREFIX.with_name(PREFIX.name+s)
def read(s):return json.loads(file(s).read_text(encoding='utf-8'))
def write(s,v):file(s).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze():
    assert not file('_scope.json').exists(),'Frozen scope already exists'
    inv=json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf-8'));cp=ROOT/'dag/reviews/coverage.json';cov=json.loads(cp.read_text(encoding='utf-8'));by={r['path']:r for r in cov['files']}
    candidates=[r for r in inv['files'] if re.match(RULE,r['path'])];records=[];excluded=[]
    for r in candidates:
        p=r['path'];c=by[p];current=sha(ROOT/p)
        assert current==r['sha256']==c['sha256'],p
        enriched={**r,'current_sha256':current,'hash_matches_inventory':True,'coverage_status_at_freeze':c['substantive_status']}
        if c['substantive_status']=='full_text_source_review_recorded':excluded.append({**enriched,'prior_receipts':c['reading_receipts']})
        else:records.append(enriched)
    write('_scope.json',{'source_commit':inv['local_head'],'scope_rule':RULE,'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'coverage_snapshot_sha256':sha(cp),'candidate_files':len(candidates),'excluded_already_fully_reviewed':excluded,'files':records,'counts':dict(collections.Counter('source' if r['path'].endswith(('.py','.md')) else 'data' for r in records)),'coverage_reconciliation':'Excluded only full_text_source_review_recorded paths whose coverage SHA equals inventory/current bytes. Partial paths remain in the new scope; previous full-read receipts are not duplicated.'})
    write('_read_ledger.json',[]);write('_notes.json',{'family_assessments':[],'claims':[],'findings':[],'primary_sources':[]});report()
def show(family,selectors=()):
    for r in read('_scope.json')['files']:
        p=r['path']
        if '/'+family+'_' not in p and '/test_'+family not in p:continue
        if not p.endswith(('.py','.md')) or selectors and not any(x in p for x in selectors):continue
        print('\nFILE '+p+' SHA256 '+r['sha256'])
        for n,l in enumerate((ROOT/p).read_text(encoding='utf-8-sig').splitlines(),1):print(str(n)+':'+l)
def record(family,assessments):
    rows=read('_scope.json')['files'];ledger=read('_read_ledger.json');existing={r['path'] for r in ledger}
    for suffix,assessment in assessments.items():
        matches=[r for r in rows if ('/'+family+'_' in r['path'] or '/test_'+family in r['path']) and r['path'].endswith(suffix)]
        assert len(matches)==1,(suffix,len(matches));r=matches[0];assert r['path'] not in existing
        n=len((ROOT/r['path']).read_text(encoding='utf-8-sig').splitlines())
        ledger.append({'path':r['path'],'sha256':r['sha256'],'full_source_read':True,'reviewed_lines':[[1,n]] if n else [],'assessment':assessment})
    write('_read_ledger.json',ledger)
def report():
    scope=read('_scope.json');ledger=read('_read_ledger.json');notes=read('_notes.json');autos=[]
    for p in sorted(PREFIX.parent.glob(PREFIX.name+'_c???_automated.jsonl')):autos.extend(json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l)
    for r in autos:
        for c in r.get('checks',[]):assert isinstance(c,str) or isinstance(c,dict) and c.get('rule') and c.get('status')
    done={r['path'] for r in ledger+autos};assert len(done)==len(ledger)+len(autos)
    pending=[{'path':r['path'],'sha256':r['sha256'],'status':'pending_source_read' if r['path'].endswith(('.py','.md')) else 'pending_data_disposition'} for r in scope['files'] if r['path'] not in done]
    findings=[{**f,'family':row['family']} for row in notes['family_assessments'] for f in row.get('findings',[])]+notes.get('findings',[])
    result={'review_id':PREFIX.name,'status':'in_progress' if pending else 'complete','source_commit':scope['source_commit'],'scope_rule':RULE,'scope':{'candidate_files':scope['candidate_files'],'excluded_already_fully_reviewed':len(scope['excluded_already_fully_reviewed']),'files':len(scope['files']),'full_source_reads':len(ledger),'full_source_lines':sum(b-a+1 for r in ledger for a,b in r['reviewed_lines']),'automated_files':len(autos),'pending':len(pending)},'completion_basis':'Full source/spec/test reading and bounded schema-specific data assessment are distinct. Complete means only that every newly scoped path has one of these dispositions.','family_assessments':notes['family_assessments'],'claims':notes.get('claims',[]),'findings':findings,'file_reviews':ledger,'automated_reviews':autos,'remaining_unsupported_files':pending,'primary_sources':notes.get('primary_sources',[]),'validation':{'offline_only':True,'provider_calls':0,'source_edits':0,'coverage_snapshot_sha256':scope['coverage_snapshot_sha256'],'coverage_reconciliation':scope['coverage_reconciliation']},'limitations':['The larger every-file repository audit remains incomplete.','Prior full source reads are excluded, not recredited.','Data parsing and owner replay are not full content reads or proof of retained truth labels.']}
    for key in ('owner_tests','data_summary','custody','evidence_artifacts','supporting_prior_reviews'):
        if key in notes:result[key]=notes[key]
    if file('_reconciliation.json').exists():result['reconciliation']=read('_reconciliation.json')
    write('.json',result)
    md=['# C051–C059 audit ('+result['status']+')','',str(result['scope']),'',result['completion_basis'],'','The repository-wide audit remains incomplete.','']
    for row in notes['family_assessments']:
        md+=['## '+row['family'],'',row['math'],'',row.get('data',''),'']
        md+=['- '+f['id']+': '+f['claim'] for f in row.get('findings',[])];md+=['','Limits: '+' '.join(row.get('limits',[])),'']
    file('.md').write_text('\n'.join(md)+'\n',encoding='utf-8');print(json.dumps(result['scope']))
if __name__=='__main__':
    if sys.argv[1]=='freeze':freeze()
    elif sys.argv[1]=='show':show(sys.argv[2],sys.argv[3:])
    elif sys.argv[1]=='report':report()
