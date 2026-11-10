"""Persist reviewed native sources; hash/range validation is not itself source review."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent; R=H.parents[1]; P='additional_paper_011_native'
prep=json.loads((H/(P+'_preparation.json')).read_text(encoding='utf-8'))
scope=json.loads((H/(P+'_scope.json')).read_text(encoding='utf-8'))
ledger=json.loads((H/(P+'_read_ledger.json')).read_text(encoding='utf-8'))
notes=json.loads((H/(P+'_notes.json')).read_text(encoding='utf-8'))
transfer_path=H/(P+'_transfers.json')
transfers=json.loads(transfer_path.read_text(encoding='utf-8')) if transfer_path.exists() else []
artifact_path=H/(P+'_artifact_reviews.json')
artifacts=json.loads(artifact_path.read_text(encoding='utf-8')) if artifact_path.exists() else []
reviews=[]; remaining=[]
for row in prep['files']:
 p=row['path']; raw=(R/p).read_bytes(); assert hashlib.sha256(raw).hexdigest()==row['sha256'],p
 name=p.split('/code/',1)[1]
 artifact=next((a for a in artifacts if a['path']==p),None)
 if artifact:
  assert artifact['sha256']==row['sha256'] and not artifact['full_source_read']
  reviews.append(artifact); continue
 if name not in notes: remaining.append(row); continue
 covered=set()
 for entry in ledger:
  if entry['path']==p and entry['sha256']==row['sha256'] and not entry.get('output_truncated'):
   for a,b in entry['reviewed_lines']: covered.update(range(a,b+1))
 transfer=next((t for t in transfers if t['path']==p),None)
 if transfer:
  source=next(x for x in prep['files'] if x['path']==transfer['base_path'])
  assert transfer['sha256']==row['sha256']==source['sha256']
  assert (R/p).read_bytes()==(R/source['path']).read_bytes()
  assert source['path'].split('/code/',1)[1] in notes
  for entry in ledger:
   if entry['path']==source['path'] and entry['sha256']==source['sha256'] and not entry.get('output_truncated'):
    for a,b in entry['reviewed_lines']:covered.update(range(a,b+1))
 assert covered==set(range(1,row['lines']+1)),(p,len(covered),row['lines'])
 reviews.append({'path':p,'sha256':row['sha256'],'full_source_read':True,'reviewed_lines':[[1,row['lines']]],
  'review_level':'complete_exact_byte_equal_base_body_and_context_review' if transfer else 'complete_raw_source_body_and_semantic_review','assessment':notes[name],
  'reading_receipt':'dag/reviews/'+P+'_read_ledger.json',
  'limits':'Written source reviewed; no fresh native or Lean execution is implied. External dependencies and historical claims require their own receipts.'})
 if transfer:reviews[-1]['body_transfer']=transfer
result={'schema_version':1,'source_commit':scope['source_commit'],'status':'in_progress' if remaining else 'complete',
 'scope_manifest':{'path':'dag/reviews/'+P+'_scope.json','sha256':prep['scope_sha256']},
 'scope_summary':{'assigned_paths':len(prep['files']),'full_source_reads':sum(r['full_source_read'] for r in reviews),'bounded_artifact_reviews':len(artifacts),'remaining':len(remaining)},
 'file_reviews':reviews,'claims':[],'findings':[],'fresh_checks':[],
 'remaining_scope':[r['path'] for r in remaining],
 'limits':['Full written source review and bounded Python controls do not imply a fresh Lean kernel or Rust/native build. Historical receipts are not freshly authenticated executions.','Two generated artifacts retain bounded complete-parse dispositions; their raw text is not claimed fully read.','Eleven exact-byte transfers inherit complete baseline body coverage plus recorded target-context assessment, not runtime identity or successful build equivalence.','No provider calls, private benchmark/key access, source edits, or native builds.'],
 'provider_calls':0,'private_answer_access':False,'production_source_edits':0,
 'validation':{'all_scope_hashes_match':True,'reviewed_ranges_complete':True}}
for key in ['claims','findings']:
 extra=H/(P+'_'+key+'.json')
 if extra.exists():result[key]=json.loads(extra.read_text(encoding='utf-8'))
controls=H/(P+'_controls.json')
if controls.exists():result['fresh_checks']=json.loads(controls.read_text(encoding='utf-8'))['checks']
result['methodology']={
 'body_review':'Complete numbered source bodies, or a complete read baseline with exact raw-byte equality and an explicit target-context assessment. Assertions, imports, hashes and schema scans alone are not full-body reading.',
 'direct_full_body_reads':sum(r['full_source_read'] and 'body_transfer' not in r for r in reviews),
 'exact_byte_body_transfers':sum('body_transfer' in r for r in reviews),
 'source_lines_in_scope':sum(r['lines'] for r in prep['files']),
 'scope_bytes':sum(r['bytes'] for r in prep['files']),
 'artifact_limit':'lean_axioms.txt: complete 1530-line grammar parse with selected raw lines. Cargo.lock: complete TOML parse, all local dependency lists inspected, registry records schema-classified. Neither receives full raw-text reading credit.',
 'test_limit':'Ten previously recorded bounded offline Python controls; no native binaries, native builds, Lean execution or provider calls. Counterexample confirmations are intentional outcomes, not ten passing production tests.',
 'custody':'All assigned source bytes rehashed against frozen scope. Original sources and historical artifacts are unchanged.'}
(H/(P+'.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
(H/(P+'_remaining_scope.json')).write_text(json.dumps({'source_commit':scope['source_commit'],'source_scope':result['scope_manifest'],'files':remaining},indent=2)+'\n',encoding='utf-8')
text=f"# Paper011 native source audit{' checkpoint' if remaining else ' complete'}\n\n{result['scope_summary']['full_source_reads']} complete source-body readings, {len(artifacts)} bounded parsed artifact dispositions, and {len(remaining)} pending paths across {len(prep['files'])} assigned paths. All frozen hashes match. No native/Lean builds or provider calls were run.\n\n"
text+=f"The complete source readings comprise {result['methodology']['direct_full_body_reads']} direct bodies and {result['methodology']['exact_byte_body_transfers']} exact-byte baseline transfers with separate context assessments. The frozen scope contains {result['methodology']['source_lines_in_scope']:,} lines and {result['methodology']['scope_bytes']:,} bytes.\n\n"
text+=result['methodology']['artifact_limit']+'\n\n'+result['methodology']['test_limit']+'\n\n'
text+='## Scoped reusable results\n\n'+'\n\n'.join(c['id']+': '+c['statement']+' '+c['limits'] for c in result['claims'])+'\n\n'
text+='## Findings\n\n'
text+='\n\n'.join('## '+f['title']+'\n\n'+f['assessment'] for f in result['findings'])+'\n\n'
text+='\n\n'.join('## '+r['path'].split('/code/',1)[1]+'\n\n'+r['assessment'] for r in reviews)+'\n'
(H/(P+'.md')).write_text(text,encoding='utf-8')
print(json.dumps(result['scope_summary']))
