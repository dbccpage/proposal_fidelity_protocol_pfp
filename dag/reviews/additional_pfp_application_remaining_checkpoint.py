"""Materialize manual semantic dispositions; structural parsing never grants credit."""
import gzip,hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining'
scope=json.loads((H/(P+'_scope.json')).read_text());prep=json.loads((H/(P+'_preparation.json')).read_text());notes=json.loads((H/(P+'_notes.json')).read_text());ledger=json.loads((H/(P+'_read_ledger.json')).read_text())
reviews=[]
for i,note in sorted(notes.items(),key=lambda x:int(x[0])):
 row=prep['files'][int(i)];raw=(R/row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];decoded=gzip.decompress(raw)if row['path'].endswith('.gz')else raw;lines=decoded.decode('utf-8').splitlines();covered=set();full=note.get('full_source_read',True)
 if full:
  for a,b in ledger[row['path']]['emitted_ranges']:covered.update(range(a,b+1))
  assert covered==set(range(1,len(lines)+1)),(i,'incomplete emission')
 review={'path':row['path'],'sha256':row['sha256'],'full_source_read':full,'reviewed_lines':[[1,len(lines)]]if full else note['reviewed_lines'],'review_level':note.get('review_level','full_body_semantic'),'assessment':note['assessment'],'limitations':note['limits']}
 if not full:review.update(population_review_artifact=note['population_review_artifact'],automated_scanned_lines=[[1,len(lines)]],line_coordinate_system='decompressed_UTF8'if row['path'].endswith('.gz')else'UTF8_source')
 reviews.append(review)
out={'source_commit':scope['source_commit'],'status':'in_progress','scope_count':len(scope['files']),'full_source_read_count':sum(r['full_source_read']for r in reviews),'bounded_data_review_count':sum(not r['full_source_read']for r in reviews),'claims':[],'findings':[],'validation':[{'kind':'source_pins_and_structured_scan','artifact':P+'_preparation.json','semantic_credit':False}],'file_reviews':reviews,'remaining_work':[r['path']for i,r in enumerate(scope['files'])if str(i)not in notes]}
rp=H/(P+'.json')
if rp.exists():
 old=json.loads(rp.read_text());out['claims']=old['claims'];out['findings']=old['findings'];out['validation']=old['validation']
rp.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'full_body':out['full_source_read_count'],'bounded':out['bounded_data_review_count'],'remaining':len(out['remaining_work'])}))
