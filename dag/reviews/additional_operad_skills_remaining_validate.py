"""Independent custody/range/schema check; grants no semantic reading credit."""
import hashlib,json,pathlib,re,collections
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';sp=H/(P+'_scope.json');rp=H/(P+'.json');scope=json.loads(sp.read_text());report=json.loads(rp.read_text());fs={x['path']:x for x in scope['files']};seen=set();fail=[];hashes=0;refs=0
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for path,f in fs.items():
    p=R/path
    if not p.is_file()or sha(p)!=f['sha256']:fail.append('source_pin:'+path)
    else:hashes+=1
for row in report['file_reviews']:
    path=row['path']
    if path in seen or path not in fs:fail.append('duplicate_or_unknown:'+path);continue
    seen.add(path)
    if row['sha256']!=fs[path]['sha256']:fail.append('review_pin:'+path)
    n=len((R/path).read_text(encoding='utf-8-sig').splitlines());ranges=row['reviewed_lines']
    if row['full_source_read'] and ranges!=([[1,n]]if n else[]):fail.append('full_range:'+path)
    for a,b in ranges:
        if not(1<=a<=b<=n):fail.append('range:'+path)
    if not row.get('assessment')or not row.get('limitations'):fail.append('empty_assessment:'+path)
pending=set(report['remaining_work'])
if pending&seen or pending|seen!=set(fs):fail.append('scope_partition')
if len(pending)!=len(report['remaining_work']):fail.append('duplicate_pending')
if report['full_source_read_count']!=sum(x['full_source_read']for x in report['file_reviews']):fail.append('full_count')
if report['bounded_review_count']!=sum(not x['full_source_read']for x in report['file_reviews']):fail.append('bounded_count')
if report['scope_count']!=len(fs):fail.append('scope_count')
if report['status']=='complete'and pending:fail.append('false_completion')
if report['source_commit']!=scope['source_commit']:fail.append('source_commit')
ledger=json.loads((H/(P+'_read_ledger.json')).read_text())
for row in report['file_reviews']:
    path=row['path'];n=len((R/path).read_text(encoding='utf-8-sig').splitlines())
    if type(row['full_source_read'])is not bool:fail.append('nonboolean_read_flag:'+path)
    if row['full_source_read']:
        item=ledger.get(path,{})
        if item.get('sha256')!=row['sha256']:fail.append('read_ledger_pin:'+path)
        covered={i for a,b in item.get('emitted_ranges',[])for i in range(a,b+1)}
        if covered!=set(range(1,n+1)):fail.append('read_ledger_gap:'+path)
extra={}
for row in report.get('additional_source_reviews',[]):
    path=row['path'];p=R/path
    if path in fs or path in extra or not p.is_file():fail.append('extra_source_population:'+path);continue
    extra[path]=row
    if sha(p)!=row['sha256']:fail.append('extra_source_pin:'+path)
    n=len(p.read_text(encoding='utf-8-sig').splitlines())
    if row['full_source_read']and row['reviewed_lines']!=([[1,n]]if n else[]):fail.append('extra_source_range:'+path)
    if not row.get('assessment')or not row.get('limitations'):fail.append('extra_source_assessment:'+path)
ids=[]
for field in ('claims','findings'):
    for obj in report[field]:
        ids.append(obj['id'])
        if field=='claims':
            for key in ('claim','evidence','dependencies','limitations'):
                if key not in obj:fail.append('claim_schema:'+obj['id']+':'+key)
        for ev in obj['evidence']:
            path=ev['path'];refs+=1
            if path not in seen and path not in extra:fail.append('unreviewed_reference:'+path);continue
            if ev['sha256']!=(fs.get(path)or extra[path])['sha256']:fail.append('evidence_pin:'+path)
            a,b=ev['lines'];n=len((R/path).read_text(encoding='utf-8-sig').splitlines())
            if not(1<=a<=b<=n):fail.append('evidence_range:'+path)
if len(ids)!=len(set(ids)):fail.append('duplicate_id')
control_ids=[];control_states=collections.Counter()
for v in report['validation']:
    if sha(R/v['path'])!=v['sha256']:fail.append('control_receipt_pin:'+v['path'])
    if re.fullmatch(P+r'_checks(?:\d+)?\.json',pathlib.PurePosixPath(v['path']).name):
        for control in json.loads((R/v['path']).read_text())['results']:
            control_ids.append(control['id']);control_states[control['status']]+=1
            source=control.get('source')
            if isinstance(source,dict)and 'path'in source and 'sha256'in source:
                if sha(R/source['path'])!=source['sha256']:fail.append('control_source_pin:'+source['path'])
if len(control_ids)!=len(set(control_ids)):fail.append('duplicate_control_ids')
if report['status']=='complete'and control_states!={'observed':104,'not_run':1}:fail.append('control_counts')
receipt={'passed':not fail,'source_commit':report['source_commit'],'scope_sha256':sha(sp),'report_sha256':sha(rp),'source_hashes_checked':hashes,'reviewed_files':len(seen),'full_source_read_count':report['full_source_read_count'],'pending':len(pending),'evidence_references_checked':refs,'control_status_counts':dict(control_states),'full_read_ledger_ranges_verified':True,'semantic_credit_granted_by_validator':False,'failures':fail}
(H/(P+'_validation.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));raise SystemExit(bool(fail))
