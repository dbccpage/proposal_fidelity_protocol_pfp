import sys,json,hashlib,datetime
from pathlib import Path
sys.dont_write_bytecode=True
import additional_paper_011_history_ledgers_audit as a
r=a.read('.json');sc=a.scope();chunks=a.read('_read_ledger.json');n=0
assert r['status']=='complete' and r['analysis_status']=='complete_for_frozen_two_file_scope'
assert r['repository_wide_audit_complete'] is False
assert r['scope']['files']==r['scope']['full_source_reads']==2
assert r['scope']['full_source_lines']==r['scope']['reviewed_chunk_lines']==6589
assert r['scope']['pending_files']==0 and not r['remaining_unsupported_files']
assert len(r['claims'])==10 and len(r['findings'])==3 and len(r['controls'])==5
assert len({x['id'] for key in ['claims','findings','controls'] for x in r[key]})==18
for row in r['file_reviews']:
 frozen=next(x for x in sc['files'] if x['path']==row['path'])
 assert row['full_source_read'] and a.sha(a.ROOT/row['path'])==row['sha256']==frozen['sha256']
 expected=1
 for lo,hi in sorted(row['reviewed_lines']):assert lo==expected;expected=hi+1
 assert expected==row['line_count']+1
 assert all(x['assessment'].strip() and x['sha256']==row['sha256'] for x in row['chunk_assessments'])
for key in ['claims','findings']:
 for entry in r[key]:
  assert entry['statement'].strip() and entry['evidence'] and entry['source_evidence']
  for e in entry['source_evidence']:
   p=a.ROOT/e['path'];assert a.sha(p)==e['sha256'];lines=p.read_text(encoding='utf-8-sig').splitlines()
   for lo,hi in e['lines']:assert 1<=lo<=hi<=len(lines);n+=1
def walk(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if k=='checks':
    for check in v:assert isinstance(check,str) or ('rule'in check and 'status'in check)
   walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(r)
for c in r['controls']:assert c['rule'] and c['status']
for d in r['external_dependencies_consulted']:
 assert not d['full_source_read'] and a.sha(a.ROOT/d['path'])==d['sha256']
result={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'validated','scope_files':2,'full_source_files':2,'bounded_data_dispositions':0,'source_lines':6589,'source_bytes':sum(x['bytes'] for x in sc['files']),'chunk_receipts':len(chunks),'claims':10,'findings':3,'controls':5,'source_evidence_range_checks':n,'all_hashes_current':True,'line_ranges_exact_cover':True,'checks_have_rule_and_status':True,'repository_wide_audit_complete':False,'report_sha256':a.sha(a.file('.json')),'markdown_sha256':a.sha(a.file('.md')),'scope_sha256':a.sha(a.SCOPE),'read_ledger_sha256':a.sha(a.file('_read_ledger.json')),'controls_sha256':a.sha(a.file('_controls.json'))}
a.write('_completion.json',result);print(json.dumps(result))
