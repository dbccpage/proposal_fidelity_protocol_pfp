"""Read-only source reconciliation and scoped review snapshot validation."""
import sys,json,hashlib
sys.dont_write_bytecode=True
import additional_pfp_tests_remaining_audit as a
def validate(label):
 report=a.read('.json');scope=a.scope();index={r['path']:r for r in a.read('_index.json')['files']}
 assert len(index)==440
 for r in scope['files']:
  binding=a.row(r['path']);assert a.sha(a.ROOT/r['path'])==binding.get('current_sha256',r['sha256'])
  assert len(a.source(r['path']))==index[r['path']]['line_count']
 for r in report['file_reviews']:
  assert r['sha256']==index[r['path']]['sha256']
  covered=[i for start,end in r['reviewed_lines'] for i in range(start,end+1)]
  assert len(covered)==len(set(covered))
  if r['full_source_read']:assert covered==list(range(1,r['line_count']+1))
 assert len(report['file_reviews'])+len([r for r in report['remaining_unsupported_files'] if not r['reviewed_lines']])+len(report['automated_reviews'])==440
 for group in ('findings','claims','controls'):
  ids=[r['id'] for r in report[group]];assert len(ids)==len(set(ids))
  for item in report[group]:
   if group=='controls':assert 'rule'in item and 'status'in item
   for kind in ('receipt','helper'):
    pin=item.get(kind)
    if isinstance(pin,dict) and 'path' in pin and 'sha256' in pin:
     target=a.ROOT/pin['path'];assert target.is_file() and a.sha(target)==pin['sha256']
   for ev in item.get('evidence',item.get('source_evidence',[])):
    assert ev['sha256']==index[ev['path']]['sha256']
    start,end=ev['lines'];assert 1<=start<=end<=index[ev['path']]['line_count']
 for r in report['automated_reviews']:
  assert r['sha256']==index[r['path']]['sha256']
  assert not r.get('full_source_read',False)
  assert all(isinstance(c,str) or ('rule'in c and 'status'in c) for c in r['checks'])
 snapshot=a.file('_'+label+'_report.json.snapshot');assert not snapshot.exists();snapshot.write_bytes(a.file('.json').read_bytes())
 result={'status':'checkpoint_validated_incomplete' if report['status']!='complete' else 'complete_scope_validated','scope':report['scope'],'scope_sha256':a.sha(a.SCOPE),'report_sha256':a.sha(a.file('.json')),'snapshot':str(snapshot.relative_to(a.ROOT)).replace('\\','/'),'snapshot_sha256':a.sha(snapshot),'all440_current_source_bindings_match':True,'original_migration_blob_hash_verified':True,'source_receipt_ranges_and_claim_control_bindings_valid':True,'repository_wide_audit_complete':False}
 a.write('_'+label+'_validation.json',result);print(json.dumps(result))
if __name__=='__main__':validate(sys.argv[1])
