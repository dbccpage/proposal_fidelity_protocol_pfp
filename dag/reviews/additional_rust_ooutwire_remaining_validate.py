"""Independent source custody/range/transfer/schema validator; no semantic credit."""
import hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_rust_ooutwire_remaining';sp=H/(P+'_scope.json');rp=H/(P+'.json');s=json.loads(sp.read_text());r=json.loads(rp.read_text());fs={x['path']:x for x in s['files']};ledger=json.loads((H/(P+'_read_ledger.json')).read_text());fail=[];seen={};refs=0;transfers=0
def sha(raw):return hashlib.sha256(raw).hexdigest()
for path,f in fs.items():
 raw=(R/path).read_bytes()
 if sha(raw)!=f['sha256']or len(raw)!=f['size_bytes']:fail.append('source_pin:'+path)
for row in r['file_reviews']:
 path=row['path']
 if path in seen or path not in fs:fail.append('population:'+path);continue
 seen[path]=row;raw=(R/path).read_bytes();lines=raw.splitlines(keepends=True);n=len(lines);item=ledger.get(path,{})
 if row['sha256']!=fs[path]['sha256']or row['size_bytes']!=len(raw):fail.append('row_pin:'+path)
 if type(row['full_source_read'])is not bool:fail.append('read_flag:'+path)
 if row['line_count']!=n or(row['full_source_read']and row['reviewed_lines']!=([[1,n]]if n else[])):fail.append('row_range:'+path)
 if r['status']=='complete'and row.get('reviewed_bytes_half_open')!=[[0,len(raw)]]:fail.append('row_bytes:'+path)
 covered={i for a,b in item.get('emitted_ranges',[])for i in range(a,b+1)}
 for t in row.get('template_transfers',[]):
  transfers+=1;tp=t['template_path'];traw=(R/tp).read_bytes();a,b=t['template_lines'];original=b''.join(traw.splitlines(keepends=True)[a-1:b]);chunk=original
  if sha(traw)!=t['template_sha256']or sha(original)!=t['template_chunk_sha256']:fail.append('template_pin:'+path)
  for old,new in t['substitutions'].items():chunk=chunk.replace(old.encode(),new.encode())
  a,b=t['target_lines'];target=b''.join(lines[a-1:b]);covered.update(range(a,b+1))
  if not 1<=a<=b<=n or chunk!=target or sha(target)!=t['target_chunk_sha256']:fail.append('reconstruction:'+path)
  if not any(x['path']==tp and x['full_source_read']for x in r['file_reviews']):fail.append('unreviewed_template:'+path)
 if row['full_source_read']and covered!=set(range(1,n+1)):fail.append('read_gap:'+path)
 if item.get('sha256')!=row['sha256']:fail.append('ledger_pin:'+path)
 if not row['assessment']or not row['limitations']:fail.append('assessment:'+path)
pending=set(r['remaining_work'])
if pending&set(seen)or pending|set(seen)!=set(fs)or len(pending)!=len(r['remaining_work']):fail.append('partition')
if r['full_source_read_count']!=sum(x['full_source_read']for x in r['file_reviews']):fail.append('full_count')
if r['source_commit']!=s['source_commit']or r['scope_sha256']!=sha(sp.read_bytes()):fail.append('scope_pin')
if r['status']=='complete'and pending:fail.append('false_complete')
ids=[]
for field in ['claims','findings']:
 for obj in r[field]:
  ids.append(obj['id'])
  required=['claim','evidence','dependencies','limitations']if field=='claims'else['title','finding','evidence','recommended_action','validation']
  for k in required:
   if not obj.get(k):fail.append('object_schema:'+obj['id']+':'+k)
  for ev in obj['evidence']:
   refs+=1;path=ev['path'];a,b=ev['lines']
   if path not in seen or ev['sha256']!=fs[path]['sha256']or not 1<=a<=b<=seen[path]['line_count']:fail.append('evidence:'+obj['id'])
if len(ids)!=len(set(ids)):fail.append('duplicate_id')
control_ids=[]
for v in r['validation']:
 if sha((R/v['path']).read_bytes())!=v['sha256']:fail.append('validation_pin:'+v['path'])
 payload=json.loads((R/v['path']).read_text())
 if 'controls'in payload or 'results'in payload:
  helper=R/v['path'].replace('.json','.py')
  if payload.get('helper_sha256')and sha(helper.read_bytes())!=payload['helper_sha256']:fail.append('control_helper:'+v['path'])
  for c in payload.get('controls',payload.get('results',[])):
   control_ids.append(c['id'])
   pins=c.get('source_pins',[])+([c['source']]if 'source'in c else[])
   for pin in pins:
    if pin['path']not in fs or fs[pin['path']]['sha256']!=pin['sha256']:fail.append('control_source:'+c['id'])
if len(control_ids)!=len(set(control_ids)):fail.append('duplicate_control_id')
if r['status']=='complete'and len(control_ids)!=r['independent_control_count']:fail.append('control_count')
receipt={'passed':not fail,'source_commit':r['source_commit'],'scope_sha256':sha(sp.read_bytes()),'report_sha256':sha(rp.read_bytes()),'source_hashes_checked':len(fs),'full_source_read_count':r['full_source_read_count'],'pending':len(pending),'exact_template_transfers_checked':transfers,'evidence_references_checked':refs,'independent_controls_checked':len(control_ids),'semantic_credit_granted_by_validator':False,'failures':fail}
(H/(P+'_validation.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));raise SystemExit(bool(fail))
