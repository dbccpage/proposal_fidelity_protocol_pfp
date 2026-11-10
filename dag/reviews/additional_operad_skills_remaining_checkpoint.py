"""Assemble manual per-file assessments only; parsing is not review."""
import hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';prep=json.loads((H/(P+'_preparation.json')).read_text());fs=prep['files'];np=H/(P+'_notes.json');notes=json.loads(np.read_text())if np.exists()else{};lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text())if lp.exists()else{};rp=H/(P+'.json');r=json.loads(rp.read_text())if rp.exists()else{};reviews=[]
for k,n in sorted(notes.items(),key=lambda x:int(x[0])):
 f=fs[int(k)];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];full=n.get('full_source_read',True)
 if full and f['lines']:
  e=ledger[f['path']];covered={i for a,b in e['emitted_ranges']for i in range(a,b+1)};assert covered==set(range(1,f['lines']+1)),(k,'unemitted full source')
 reviews.append({'path':f['path'],'sha256':f['sha256'],'full_source_read':full,'reviewed_lines':[[1,f['lines']]]if full and f['lines']else n.get('reviewed_lines',[]),'review_level':n.get('review_level','full_body_semantic'),'assessment':n['assessment'],'limitations':n['limits']})
r.update({'source_commit':prep['source_commit'],'status':'in_progress','scope_count':len(fs),'scope_bytes':sum(x['bytes']for x in fs),'full_source_read_count':sum(x['full_source_read']for x in reviews),'bounded_review_count':sum(not x['full_source_read']for x in reviews),'claims':r.get('claims',[]),'findings':r.get('findings',[]),'validation':r.get('validation',[]),'file_reviews':reviews,'remaining_work':[x['path']for x in fs if str(x['index'])not in notes]});rp.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'full':r['full_source_read_count'],'bounded':r['bounded_review_count'],'pending':len(r['remaining_work'])}))
