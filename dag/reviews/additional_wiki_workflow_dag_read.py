import hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_wiki_workflow_dag';scope=json.loads((H/(P+'_scope.json')).read_text());r=scope['files'][0];raw=(R/r['path']).read_bytes();assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'];lines=raw.decode().splitlines()
if len(sys.argv)<2:
 print('LINES',len(lines),'SHA',r['sha256'])
 for i,s in enumerate(lines,1):
  if s.startswith('#'):print(i,s)
else:
 a,b=map(int,sys.argv[1:3]);assert 1<=a<=b<=len(lines);print(r['path'],r['sha256'],'RANGE',a,b,'TOTAL',len(lines))
 for i,s in enumerate(lines[a-1:b],a):print(str(i)+': '+s)
 p=H/(P+'_read_ledger.json');v=json.loads(p.read_text()) if p.exists() else [];v.append({'path':r['path'],'sha256':r['sha256'],'reviewed_lines':[[a,b]],'full_output':True});p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
