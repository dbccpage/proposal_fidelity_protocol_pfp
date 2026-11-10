"""Read all narrative around large generated evidence tables; no full-file credit."""
import json,pathlib,sys,hashlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining';s=json.loads((H/(P+'_preparation.json')).read_text())['files'];lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text())
for i in map(int,sys.argv[1].split(',')):
 row=s[i];b=(R/row['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==row['sha256'];lines=b.decode().splitlines();print('FILE',i,row['path'],'LINES',len(lines));ranges=[];start=None;omitted=[]
 for j,line in enumerate(lines,1):
  if line.lstrip().startswith('|'):
   omitted.append(j)
   if start is not None:ranges.append([start,j-1]);start=None
   continue
  if start is None:start=j
  print(str(j)+': '+line)
 if start is not None:ranges.append([start,len(lines)])
 record=ledger.setdefault(row['path'],{'path':row['path'],'sha256':row['sha256'],'lines':len(lines),'emitted_ranges':[],'semantic_credit':False});record['emitted_ranges']+=ranges;record['structured_table_rows_not_manually_read']=omitted
 print('TABLE ROWS OMITTED',len(omitted))
lp.write_text(json.dumps(ledger,indent=2)+'\n')
