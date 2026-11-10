from pathlib import Path
import hashlib,json,sys,difflib
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
rows=json.loads(Path(str(P)+'_inventory.json').read_text())['files'];base=int(sys.argv[1]);br=rows[base];bb=(R/br['path']).read_bytes();assert hashlib.sha256(bb).hexdigest()==br['sha256']
lp=Path(str(P)+'_delta_ledger.json');ledger=json.loads(lp.read_text()) if lp.exists() else []
for a in sys.argv[2:]:
 i=int(a);r=rows[i];b=(R/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']
 d=''.join(difflib.unified_diff(bb.decode().splitlines(True),b.decode().splitlines(True),fromfile=br['path'],tofile=r['path']))
 print('FULL DIFF',base,'TO',i,'BASE SHA',br['sha256'],'TARGET SHA',r['sha256']);print(d if d else '[BYTE IDENTICAL]' if b==bb else '[TEXT LINES IDENTICAL; BYTE ENCODING DIFFERENCE]')
 ledger.append(dict(base_index=base,target_index=i,base_sha256=br['sha256'],target_sha256=r['sha256'],byte_identical=b==bb,full_diff_displayed=True,diff_sha256=hashlib.sha256(d.encode()).hexdigest()))
lp.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')
