"""Continuation helpers; old checkpoints are never rerun."""
import sys,json,hashlib
sys.dont_write_bytecode=True
import additional_rust_linear_algebra_remaining_audit as a
def evidence(name,lo,hi):
 row=next(x for x in a.read('_scope.json')['files'] if x['path']==a.BASE+name)
 return {'path':row['path'],'sha256':row['sha256'],'lines':[lo,hi]}
def note(name,text):
 n=a.read('_notes.json');assert name not in n['files'];n['files'][name]={'full_source_read':True,'assessment':text};a.write('_notes.json',n)
def checkpoint(label):
 sys.argv=['audit','checkpoint'];a.main()
 dest=a.file('_'+label+'_report.json.snapshot');assert not dest.exists();dest.write_bytes(a.file('.json').read_bytes())
 a.write('_'+label+'_pins.json',{suffix:a.sha(a.file(suffix)) for suffix in ('.json','.md','_notes.json','_read_ledger.json','_validation.json')})
def takeover():
 assert a.sha(a.file('_scope.json'))=='8dfb9e0f063a5e0c37448204f06b261c877c11c3c36595e21b3d935284a454b7'
 r=a.read('.json');assert r['scope']['full_source_reads']==37
 pins={}
 for suffix in ('.json','.md','_notes.json','_read_ledger.json','_validation.json'):
  dest=a.file('_takeover37'+suffix+'.snapshot');assert not dest.exists();dest.write_bytes(a.file(suffix).read_bytes());pins[str(dest.relative_to(a.ROOT)).replace('\\','/')]=a.sha(dest)
 for row in a.read('_scope.json')['files']:assert a.sha(a.ROOT/row['path'])==row['sha256']
 a.write('_takeover37.json',{'status':'preserved_and_current_pins_matched','full_source_files_inherited':37,'inherited_source_lines':18416,'pending_files':46,'scope_sha256':a.sha(a.file('_scope.json')),'snapshots':pins,'note':'Preserved prior parent full body reviews; no inherited source bodies executed or automatically credited to this continuation.'})
 print(json.dumps(a.read('_takeover37.json')))
if __name__=='__main__':takeover()
