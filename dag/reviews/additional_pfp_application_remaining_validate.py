"""Independent final report/pin/range validation, not semantic-reading credit."""
import collections,gzip,hashlib,json,pathlib,platform
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining';errors=[]
def strict_load(path):
 duplicates=[]
 def hook(items):
  d={}
  for k,v in items:
   if k in d:duplicates.append(k)
   d[k]=v
  return d
 x=json.loads(path.read_text(encoding='utf8'),object_pairs_hook=hook);assert not duplicates,(path,duplicates);return x
scope=strict_load(H/(P+'_scope.json'));report=strict_load(H/(P+'.json'));ledger=strict_load(H/(P+'_read_ledger.json'));pins={x['path']:x for x in scope['files']};reviews={x['path']:x for x in report['file_reviews']};linecounts={};source_json_issues=[];scanned_json_records=0
assert len(reviews)==len(report['file_reviews'])==len(pins)==165
assert set(reviews)==set(pins)
for path,pin in pins.items():
 raw=(R/path).read_bytes();assert hashlib.sha256(raw).hexdigest()==pin['sha256']==reviews[path]['sha256'];assert len(raw)==pin['bytes']
 decoded=gzip.decompress(raw)if path.endswith('.gz')else raw;lines=decoded.decode('utf8').splitlines();n=len(lines);linecounts[path]=n;r=reviews[path]
 assert type(r['full_source_read'])is bool and r['assessment']and r['limitations']
 for a,b in r['reviewed_lines']:assert type(a)is int and type(b)is int and 1<=a<=b<=n
 if r['full_source_read']:
  assert r['review_level']=='full_body_semantic'and r['reviewed_lines']==[[1,n]]
  covered=set()
  for a,b in ledger[path]['emitted_ranges']:covered.update(range(a,b+1))
  assert covered==set(range(1,n+1)) and ledger[path]['sha256']==pin['sha256']
 else:
  assert r['review_level']=='bounded_structured_population_with_narrative_context'
  assert r['automated_scanned_lines']==[[1,n]]
 if '.json'in pathlib.PurePosixPath(path).name:
  records=lines if '.jsonl'in path else[decoded.decode('utf8')]
  for index,text in enumerate(records,1):
   duplicate=[];nonfinite=[]
   def hook(items):
    d={}
    for k,v in items:
     if k in d:duplicate.append({'key':k,'different_values':d[k]!=v})
     d[k]=v
    return d
   try:json.loads(text,object_pairs_hook=hook,parse_constant=lambda s:nonfinite.append(s))
   except Exception as exc:source_json_issues.append({'path':path,'record':index,'parse_error':str(exc)});continue
   if duplicate or nonfinite:source_json_issues.append({'path':path,'record':index,'duplicate_keys':duplicate,'nonfinite':nonfinite})
   scanned_json_records+=1
known_probe_ids=set()
for name in [P+'_probes.json',P+'_extra_probes.json']:
 x=strict_load(H/name)
 for q in x['probes']:known_probe_ids.add(q.get('id',q['name']))
 probe_pins=[{'path':p,'sha256':s}for p,s in x['source_pins'].items()]if isinstance(x['source_pins'],dict)else x['source_pins']
 for pin in probe_pins:
  assert hashlib.sha256((R/pin['path']).read_bytes()).hexdigest()==pin['sha256']
ids=[];evidence_count=0
for kind in ['claims','findings']:
 for row in report[kind]:
  ids.append(row['id']);assert row['evidence']
  if kind=='claims':assert row['claim']and row['dependencies']and row['limitations']
  else:
   assert row['statement']and row['next_action']and row['limitations']
   assert set(row['probe_ids'])<=known_probe_ids,(row['id'],row['probe_ids'])
  for ev in row['evidence']:
   assert ev['path']in pins and ev['sha256']==pins[ev['path']]['sha256']
   for a,b in ev['lines']:assert type(a)is int and type(b)is int and 1<=a<=b<=linecounts[ev['path']],(row['id'],ev)
   evidence_count+=1
assert len(ids)==len(set(ids))
assert sum(r['full_source_read']for r in reviews.values())==report['full_source_read_count']==151
assert sum(not r['full_source_read']for r in reviews.values())==report['bounded_data_review_count']==14
assert report['scope_bytes']==sum(x['bytes']for x in pins.values())
extra=strict_load(H/(P+'_population_extra.json'));assert extra['all_consistency_checks_pass']
for ref in report['related_reviews']:assert hashlib.sha256((R/ref['path']).read_bytes()).hexdigest()==ref['sha256']
out={'status':'passed','python':platform.python_version(),'source_commit':report['source_commit'],'scope_files':165,'scope_bytes':report['scope_bytes'],'full_body_read_receipts':151,'bounded_structured_dispositions':14,'claims':len(report['claims']),'findings':len(report['findings']),'source_evidence_items_validated':evidence_count,'probe_reference_count':len(known_probe_ids),'structured_records_strictly_scanned':scanned_json_records,'source_json_issues':source_json_issues,'all_frozen_source_hashes_match':True,'all_cited_source_ranges_valid':True,'all_full_reads_have_complete_emission_receipts':True,'limits':'This validator checks report integrity, source custody and range coverage only; it does not independently prove semantic reading, mathematical truth or runtime behavior.'}
(H/(P+'_validation.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
