"""Final custody/accounting validation; no original program imports or execution."""
import sys
sys.dont_write_bytecode=True
import json,hashlib
from pathlib import Path
import additional_rust_linear_algebra_remaining_audit as a
scope=a.read('_scope.json');report=a.read('.json');notes=a.read('_notes.json')
old=json.loads(a.file('_takeover37_notes.json.snapshot').read_text(encoding='utf8'))
assert a.sha(a.file('_scope.json'))=='8dfb9e0f063a5e0c37448204f06b261c877c11c3c36595e21b3d935284a454b7'
assert report['status']=='complete' and report['repository_wide_audit_complete'] is False
assert len(scope['files'])==len(report['file_reviews'])==83
assert not report['remaining_unsupported_files'] and report['scope']['pending']==0
for name,value in old['files'].items():assert notes['files'][name]==value
for group in ('claims','findings','controls'):assert notes[group][:len(old[group])]==old[group]
original={r['path']:r for r in scope['files']};lines=bytes_=ranges=0
for r in report['file_reviews']:
 assert r['path'] in original and r['sha256']==original[r['path']]['sha256']==a.sha(a.ROOT/r['path'])
 body=(a.ROOT/r['path']).read_text(encoding='utf8').splitlines()
 assert r['full_source_read'] is True and r['line_count']==len(body) and r['assessment']
 covered=set()
 for lo,hi in r['reviewed_lines']:
  assert 1<=lo<=hi<=len(body);covered.update(range(lo,hi+1));ranges+=1
 assert covered==set(range(1,len(body)+1))
 lines+=len(body);bytes_+=(a.ROOT/r['path']).stat().st_size
assert lines==35011
ids=[]
controls={c['id']:c for c in report['controls']}
for group in ('claims','findings','controls'):
 for item in report[group]:
  ids.append(item['id'])
  for cid in item.get('controls',[]):assert cid in controls
assert len(ids)==len(set(ids))
receipts={}
for control in report['controls']:
 assert control['rule'] and control['status']
 receipt=control['receipt'];path=a.ROOT/receipt['path'];assert a.sha(path)==receipt['sha256']
 result=json.loads(path.read_text(encoding='utf8'));assert a.sha(path.with_suffix('.py'))==result['helper_sha256']
 receipts[receipt['path']]=receipt['sha256']
pins={s:a.sha(a.file(s)) for s in ('.json','.md','_scope.json','_notes.json','_read_ledger.json','_validation.json','_audit.py','_extend.py')}
snapshot=a.file('_final_report.json.snapshot');assert not snapshot.exists();snapshot.write_bytes(a.file('.json').read_bytes())
out={'status':'complete_declared_slice_validated','repository_wide_audit_complete':False,'files':83,'full_source_reads':83,'bounded_data_dispositions':0,'pending':0,'source_lines':lines,'source_bytes':bytes_,'display_range_records':ranges,'claims':len(report['claims']),'findings':len(report['findings']),'controls':len(controls),'source_sha256_matches':83,'initial37_notes_claims_findings_controls_preserved':True,'inherited_full_source_files':37,'continuation_full_source_files':46,'all_control_rule_status_and_receipt_helper_bindings_valid':True,'pins':pins,'control_receipts':receipts,'runtime':sys.version,'helper_sha256':a.sha(Path(__file__)),'limits':['Validation checks custody/accounting, not mathematical truth automatically.','Full source review and independently authored bounded models; no Rust/Cargo/native/provider execution.','No original source edits; all83hashes still match frozen scope.']}
a.write('_final_validation.json',out)
print(json.dumps({'status':out['status'],'counts':{k:out[k] for k in ('files','source_lines','source_bytes','claims','findings','controls','pending')},'report_sha256':pins['.json'],'markdown_sha256':pins['.md'],'validation_sha256':a.sha(a.file('_final_validation.json')),'control_receipt_bundle_sha256':hashlib.sha256(json.dumps(receipts,sort_keys=True).encode()).hexdigest()}))
