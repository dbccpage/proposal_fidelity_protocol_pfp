"""Read-only generation/display of exact line and normalized-AST source deltas."""
import ast,difflib,hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts'
rows=json.loads((H/(P+'_preparation.json')).read_text())['files']
out=[]
for r in rows:
 if '/adapted_sources/' not in r['path']:continue
 if any(x['sha256']==r['sha256'] for x in out):continue
 name=Path(r['path']).name
 base=next(x for x in rows if '/source_files/' in x['path'] and Path(x['path']).name==name)
 bt=(R/base['path']).read_text(encoding='utf-8');tt=(R/r['path']).read_text(encoding='utf-8')
 normalized=ast.unparse(ast.parse(bt))+'\n'
 diff=list(difflib.unified_diff(normalized.splitlines(),tt.splitlines(),fromfile=base['path']+' [ast.unparse]',tofile=r['path'],n=3))
 out.append({'path':r['path'],'sha256':r['sha256'],'base_path':base['path'],'base_sha256':base['sha256'],'method':'full_source_baseline_normalized_ast_plus_all_text_differences','diff':diff})
pending=[x for x in json.loads((H/(P+'_source_comparison.json')).read_text()) if x['method']=='prior_delta_candidate' and '/execution_machinery_' in x['path'] and 'aggregate_recreated_run' in x['path']]
known={x['base_path']:{'path':x['base_path'],'sha256':x['base_sha256'],'base_report':x['base_report'],'base_assessment':x['base_assessment']} for x in pending}
while pending:
 options=[]
 for x in pending:
  for b in known.values():
   if Path(x['path']).name!=Path(b['path']).name:continue
   diff=list(difflib.unified_diff((R/b['path']).read_text(encoding='utf-8').splitlines(),(R/x['path']).read_text(encoding='utf-8').splitlines(),fromfile=b['path'],tofile=x['path'],n=3))
   options.append((len(diff),x['path'],b['path'],diff))
 _,path,bpath,diff=min(options,key=lambda x:x[:3]);x=next(x for x in pending if x['path']==path);b=known[bpath]
 item={**x,'base_path':bpath,'base_sha256':b['sha256'],'diff':diff,'method':'full_baseline_plus_complete_diff'}
 if '/docs/' in bpath:item['base_report']='dag/reviews/'+P+'.json';item['base_assessment']='Assessment recorded in same scoped report.'
 out.append(item);known[path]={'path':path,'sha256':x['sha256']};pending.remove(x)
(H/(P+'_deltas.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
if len(sys.argv)>1:
 i=int(sys.argv[1]);d=out[i];start=int(sys.argv[2]) if len(sys.argv)>2 else 1;end=int(sys.argv[3]) if len(sys.argv)>3 else len(d['diff'])
 print('DELTA',i,d['path'],'SHA',d['sha256'],'BASE',d['base_path'],'SHA',d['base_sha256'],'RANGE',start,end,'OF',len(d['diff']))
 for j,line in enumerate(d['diff'][start-1:end],start):print(str(j)+': '+line)
 lp=H/(P+'_delta_read_ledger.json');ledger=json.loads(lp.read_text()) if lp.exists() else []
 ledger.append({'path':d['path'],'sha256':d['sha256'],'base_path':d['base_path'],'base_sha256':d['base_sha256'],'delta_sha256':hashlib.sha256('\n'.join(d['diff']).encode()).hexdigest(),'reviewed_diff_lines':[[start,end]],'diff_lines':len(d['diff'])})
 lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf-8')
else:
 for i,d in enumerate(out):print(i,len(d['diff']),d['path'].split('/docs/')[1])
