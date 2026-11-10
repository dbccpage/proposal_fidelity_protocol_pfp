"""Present every JSON value compactly; whitespace alone is elided, no semantic credit automatic."""
import hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining'
prep=json.loads((H/(P+'_preparation.json')).read_text());lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text())
for idx in map(int,sys.argv[1].split(',')):
 row=prep['files'][idx];raw=(R/row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];s=raw.decode('utf8');v=json.loads(s)
 compact=json.dumps(v,ensure_ascii=False,separators=(',',':'));assert json.loads(compact)==v
 print('\nFILE',idx,row['path'],row['sha256'],'FULL JSON VALUES; ORIGINAL LINES',len(s.splitlines()));print(compact)
 rec=ledger.setdefault(row['path'],{'sha256':row['sha256'],'emitted_ranges':[],'semantic_credit':False});rec['emitted_ranges'].append([1,len(s.splitlines())]);rec['presentation']='All decoded JSON values; whitespace elided; duplicate-key scan separately verified'
lp.write_text(json.dumps(ledger,indent=2)+'\n')
