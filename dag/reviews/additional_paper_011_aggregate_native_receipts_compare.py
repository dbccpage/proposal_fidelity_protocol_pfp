import difflib,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts'
rows=json.loads((H/(P+'_preparation.json')).read_text())['files']
bases=[]
for reportname in ['additional_paper_011_core','additional_paper_011_native','additional_paper_011_history_context']:
 for row in json.loads((H/(reportname+'.json')).read_text()).get('file_reviews',[]):
  if row.get('full_source_read'):bases.append({**row,'base_report':'dag/reviews/'+reportname+'.json'})
seen={};results=[]
for row in rows:
 if Path(row['path']).suffix not in {'.py','.rs'}:continue
 exact=next((b for b in bases if b['sha256']==row['sha256']),None)
 if exact:
  assert (R/exact['path']).read_bytes()==(R/row['path']).read_bytes()
  results.append({'path':row['path'],'sha256':row['sha256'],'method':'prior_exact','base_path':exact['path'],'base_sha256':exact['sha256'],'base_report':exact['base_report'],'base_assessment':exact['assessment']})
 elif row['sha256'] in seen:
  results.append({'path':row['path'],'sha256':row['sha256'],'method':'scope_exact','base_path':seen[row['sha256']]})
 else:
  name=Path(row['path']).name
  name={'failed_runner.py':'aggregate_original_recovery_v1.py','source.rs':'native_dossier_integral.rs'}.get(name,name)
  same=[b for b in bases if Path(b['path']).name==name]
  if same:
   b=max(same,key=lambda b:difflib.SequenceMatcher(None,(R/b['path']).read_text(encoding='utf-8').splitlines(),(R/row['path']).read_text(encoding='utf-8').splitlines(),autojunk=True).ratio())
   al=(R/b['path']).read_text(encoding='utf-8').splitlines();bl=(R/row['path']).read_text(encoding='utf-8').splitlines()
   delta=list(difflib.unified_diff(al,bl,fromfile=b['path'],tofile=row['path'],n=3))
   results.append({'path':row['path'],'sha256':row['sha256'],'method':'prior_delta_candidate','base_path':b['path'],'base_sha256':b['sha256'],'base_report':b['base_report'],'base_assessment':b['assessment'],'diff_lines':len(delta),'diff':delta})
  else:results.append({'path':row['path'],'sha256':row['sha256'],'method':'new_body'})
  seen[row['sha256']]=row['path']
(H/(P+'_source_comparison.json')).write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
for r in results:print(r['method'],r['path'].split('/docs/',1)[1],r.get('diff_lines',''),r.get('base_path','').split('/code/')[-1])
