from pathlib import Path
import json,hashlib,collections,sys
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_eis_artifacts_remaining';s=json.loads(Path(str(P)+'_scope.json').read_text());rows=s['files']
def h(b):return hashlib.sha256(b).hexdigest()
def obj(i):
 b=(R/rows[i]['path']).read_bytes();assert h(b)==rows[i]['sha256'];return json.loads(b)
if sys.argv[1]=='sparse144':
 a,b=map(int,sys.argv[2:]);r=rows[144];raw=(R/r['path']).read_bytes();assert h(raw)==r['sha256'];ls=raw.decode().splitlines();shown=[]
 print(r['path'],r['sha256'])
 for i in range(a,b+1):
  if len(ls[i-1])<=1000:print(f'{i}: {ls[i-1]}');shown.append(i)
  else:print(f'{i}: <OMITTED long line {len(ls[i-1])}chars; not full-read credit>')
 p=Path(str(P)+'_bounded_read_ledger.json');ledger=json.loads(p.read_text()) if p.exists() else []
 ledger.append({'path':r['path'],'sha256':r['sha256'],'displayed_line_numbers':shown,'omitted_large_lines':True});p.write_text(json.dumps(ledger,indent=2)+'\n')
elif sys.argv[1]=='catalog':
 o=obj(104);a=o['antibodies'];gen={k:v for k,v in a.items() if v['failure_class']=='general_obstruction'}
 checks={k:{'description_template':v['description']=='Custom obstruction defect: '+v['target_pattern'],'negative_template':v['negative_fixture']=='Failing specimen: '+v['target_pattern'],'positive_template':v['positive_fixture']=='Repaired invariant for '+v['target_pattern']} for k,v in gen.items()}
 root=[]
 for i,r in enumerate(rows):
  if i>=58 and i not in (96,97):continue
  v=obj(i);ident=v.get('antibody_id',v.get('name'));cv=a.get(ident)
  delta=None if cv is None else {key:{'file':v.get(key),'catalog':cv.get(key)} for key in set(v)|set(cv) if v.get(key)!=cv.get(key)}
  root.append({'index':i,'id':ident,'catalog_present':cv is not None,'equal':cv==v,'delta':delta})
 out={'catalog_source':rows[104],'records':len(a),'statuses':dict(collections.Counter(v['pharmacy_status'] for v in a.values())),'classes':dict(collections.Counter(v['failure_class'] for v in a.values())),'key_id_mismatches':[k for k,v in a.items() if k!=v['antibody_id']],'general_obstruction_template_counts':{key:sum(v[key] for v in checks.values()) for key in next(iter(checks.values()))},'general_obstruction_count':len(gen),'embedded_admissions':sum('admission' in v for v in a.values()),'root_comparisons':root,'limits':'Whole-population parse/template/key/status comparisons only; catalog-only prose and evidence hashes are not individually human adjudicated.'}
 Path(str(P)+'_catalog_checks.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('catalog_source','root_comparisons')},indent=2));print('ROOT DIFFERENCES',json.dumps([x for x in root if not x['equal']],indent=2))
else:raise SystemExit('unknown')
