from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_eis_artifacts_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
report_bytes=Path(str(P)+'.json').read_bytes();report=json.loads(report_bytes)
scope_bytes=Path(str(P)+'_scope.json').read_bytes();scope=json.loads(scope_bytes)
assert h(scope_bytes)==report['scope_sha256']=='57383045b5b17029d822a586201987b6ada589d0e8a82138efdf1d0fd44ffa60'
pins={r['path']:r for r in scope['files']};assert len(pins)==146
counts={};bytes_count=0;ranges=0;raw_ranges=0;raw_lines=0
for p,row in pins.items():
 b=(R/p).read_bytes();assert h(b)==row['sha256'];assert len(b)==row['size_bytes'];counts[p]=len(b.decode('utf8').splitlines());bytes_count+=len(b)
seen=set()
for review in report['file_reviews']:
 p=review['path'];assert p not in seen;seen.add(p);assert review['sha256']==pins[p]['sha256'];assert review['source_line_count']==counts[p]
 covered=set()
 for a,b in review['reviewed_lines']:
  assert 1<=a<=b<=counts[p];covered.update(range(a,b+1));ranges+=1
 assert len(covered)==review['reviewed_line_count']
 assert review['full_source_read']==(covered==set(range(1,counts[p]+1)))
 if 'transfer_receipt' in review:
  ref=review['transfer_receipt']; assert h((R/ref['path']).read_bytes())==ref['sha256']
  assert review['review_level'].startswith('full_body_via_')
  raw_covered=set()
  for a,b in review['raw_displayed_lines']:
   assert 1<=a<=b<=counts[p];raw_covered.update(range(a,b+1));raw_ranges+=1
  assert len(raw_covered)==review['raw_displayed_line_count'];raw_lines+=len(raw_covered)
 else:
  raw_ranges+=len(review['reviewed_lines']);raw_lines+=len(covered)
 if not review['full_source_read']:
  unread=set()
  for a,b in review['unread_lines']:unread.update(range(a,b+1))
  assert unread.isdisjoint(covered) and unread|covered==set(range(1,counts[p]+1))
 assert review['assessment']
assert seen==set(pins)
evidence_ranges=0
for section in ('claims','findings','file_reviews'):
 for item in report[section]:
  for ev in item['source_evidence']:
   p=ev['path'];assert ev['sha256']==pins[p]['sha256'];a,b=ev['lines'];assert 1<=a<=b<=counts[p];evidence_ranges+=1
for prior in report['prior_evidence_reconciliation']:
 assert h((R/prior['report']).read_bytes())==prior['report_sha256']
assert h((R/report['execution_evidence']['path']).read_bytes())==report['execution_evidence']['sha256']
assert h((R/report['execution_evidence']['helper']).read_bytes())==report['execution_evidence']['helper_sha256']
assert h((R/report['artifact_evidence']['catalog_checks']).read_bytes())==report['artifact_evidence']['catalog_checks_sha256']
artifact=report['artifact_evidence']; transfer_path=R/artifact['body_transfer_validation']
assert h(transfer_path.read_bytes())==artifact['body_transfer_validation_sha256']
transfer=json.loads(transfer_path.read_bytes());assert transfer['status']=='PASS'
for name in ('manifest','assessment_artifact'):
 expected=transfer['manifest_sha256' if name=='manifest' else 'assessment_sha256']
 assert h((R/transfer[name]).read_bytes())==expected
for stem in ('body_read_ledger','raw_read_ledger'):
 suffix='_body_read_ledger.json' if stem=='body_read_ledger' else '_read_ledger.json'
 assert h(Path(str(P)+suffix).read_bytes())==transfer[stem+'_sha256']
for item in transfer['artifacts']:
 assert h((R/item['path']).read_bytes())==item['sha256'] and item['complete']
 units=set()
 for a,b in item['reviewed_ranges']:units.update(range(a,b+(item['mode']=='lines')))
 assert units==set(range(1,item['units']+1) if item['mode']=='lines' else range(item['units']))
cat=transfer['catalog']; assert cat['semantic_full_body_read'] and cat['complete_reconstruction_equal'] and cat['duplicate_keys']==0
assert cat['sha256']==pins[cat['path']]['sha256'] and len(cat['record_receipts'])==1069
actual=json.loads((R/cat['path']).read_bytes())['antibodies'];assert {x['catalog_id'] for x in cat['record_receipts']}==set(actual)
for item in cat['record_receipts']:
 a,b=item['source_lines'];assert 1<=a<=b<=counts[cat['path']]
 if 'base_path' in item:assert h((R/item['base_path']).read_bytes())==item['base_sha256']
assert len(cat['templates'])==11 and cat['root_base_transfers']==43 and cat['template_residual_records']==1026
assert transfer['warning_logs']['semantic_full_body_read'] and transfer['warning_logs']['sha256']==pins[transfer['warning_logs']['path']]['sha256']
assert {x['source_line'] for x in transfer['warning_logs']['logs']}=={221,240,478}
assert h((R/report['review_history']['checkpoint']).read_bytes())==report['review_history']['sha256']=='874dc0c6146bcecf8812e8d4fdc07880a4cbf96fade69f510c215611e0a1bcec'
assert not Path(str(P)+'_checkpoint144.json').exists()
summary=report['summary'];assert summary['bytes']==bytes_count and summary['lines']==sum(counts.values())
assert summary['full_source_reads']==sum(x['full_source_read'] for x in report['file_reviews'])
assert summary['direct_raw_lines_total']==raw_lines==7330
out={'status':'PASS','report_sha256':h(report_bytes),'markdown_sha256':h(Path(str(P)+'.md').read_bytes()),'scope_sha256':h(scope_bytes),'source_pins_checked':len(pins),'body_coverage_ranges_checked':ranges,'raw_reading_ranges_checked':raw_ranges,'raw_displayed_lines':raw_lines,'evidence_ranges_checked':evidence_ranges,'transfer_receipt_sha256':h(transfer_path.read_bytes()),'catalog_records_with_exact_reconstruction_and_reading_receipts':1069,'decoded_logs_complete':3,'summary':summary,'limits':'Custody/range/accounting validation and explicit reading-transfer checks only, not a mathematical proof or new historical execution.'}
Path(str(P)+'_validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
