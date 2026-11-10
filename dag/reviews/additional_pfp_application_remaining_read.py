"""Emit exact indexed bodies/ranges; emitted text is not automatic semantic credit."""
import hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining'
prep=json.loads((H/(P+'_preparation.json')).read_text());lp=H/(P+'_read_ledger.json');ledger=json.loads(lp.read_text())if lp.exists()else{}
indexes=list(map(int,sys.argv[1].split(',')));start=int(sys.argv[2])if len(sys.argv)>2 else 1;end=int(sys.argv[3])if len(sys.argv)>3 else None
for i in indexes:
 row=prep['files'][i];raw=(R/row['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];assert not row['path'].endswith('.gz')
 lines=raw.decode('utf-8').splitlines();last=min(end or len(lines),len(lines));print('\nFILE',i,row['path'],row['sha256'],'LINES',start,last,'OF',len(lines))
 for n in range(start,last+1):print(str(n)+': '+lines[n-1])
 record=ledger.setdefault(row['path'],{'path':row['path'],'sha256':row['sha256'],'lines':len(lines),'emitted_ranges':[],'semantic_credit':False});record['emitted_ranges'].append([start,last])
lp.write_text(json.dumps(ledger,indent=2)+'\n')
