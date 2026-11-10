"""Assemble explicit manual dispositions; coverage remains independent of parsing."""
import hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';prep=json.loads((H/(P+'_preparation.json')).read_text());rows=prep['files'];np=H/(P+'_notes.json');notes=json.loads(np.read_text())if np.exists()else{};lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text())if lp.exists()else{};reviews=[]
for k,n in sorted(notes.items(),key=lambda x:int(x[0])):
 f=rows[int(k)];b=(R/f['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==f['sha256'];full=n.get('full_source_read',True)
 if full:
  assert f['kind']=='text';covered=set()
  for a,z in ledger[f['path']]['emitted_ranges']:covered.update(range(a,z+1))
  assert covered==set(range(1,f['lines']+1)),(k,'incomplete body emission')
 reviews.append({'path':f['path'],'sha256':f['sha256'],'full_source_read':full,'reviewed_lines':[[1,f['lines']]]if full else n.get('reviewed_lines',[]),'review_level':n.get('review_level','full_body_semantic'),'assessment':n['assessment'],'limitations':n['limits']})
rp=H/(P+'.json');old=json.loads(rp.read_text())if rp.exists()else{}
out={'source_commit':prep['source_commit'],'status':'in_progress','scope_count':len(rows),'scope_bytes':sum(f['bytes']for f in rows),'full_source_read_count':sum(r['full_source_read']for r in reviews),'bounded_review_count':sum(not r['full_source_read']for r in reviews),'claims':old.get('claims',[]),'findings':old.get('findings',[]),'validation':old.get('validation',[]),'file_reviews':reviews,'remaining_work':[f['path']for i,f in enumerate(rows)if str(i)not in notes]};out.update({k:old[k]for k in ('related_context','validation_environment_limits')if k in old});rp.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'full':out['full_source_read_count'],'bounded':out['bounded_review_count'],'remaining':len(out['remaining_work'])}))
