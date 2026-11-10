"""Validate only this frozen audit, preserving all original bytes."""
from pathlib import Path
import ast,hashlib,json,re
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_rust_adversary_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
def load(s):return json.loads(Path(str(P)+s).read_bytes())
raw=Path(str(P)+'_scope.json').read_bytes()
assert h(raw)=='d0547aab64c96d5e8cb280c02ad499283cff257d6931ca886f113cb4235ccd27'
S=json.loads(raw)['files'];report=load('.json');ledger=load('_read_ledger.json');transfers=load('_template_transfers.json');controls=load('_controls.json')
assert len(S)==99 and len(report['file_reviews'])==99 and report['status']=='complete_declared_scope'
scope_by={r['path']:r for r in S};bodies={};counts={};totalbytes=0
for r in S:
 b=(R/r['path']).read_bytes();assert h(b)==r['sha256'] and len(b)==r['size_bytes'];bodies[r['path']]=b.decode('utf8').splitlines();counts[r['path']]=len(bodies[r['path']]);totalbytes+=len(b)
assert totalbytes==1602171 and sum(counts.values())==45350
seen={i:set() for i in range(99)}
for r in ledger:
 i=r['index'];assert r['path']==S[i]['path'] and r['sha256']==S[i]['sha256'];a,z=r['displayed_lines'];assert 1<=a<=z<=counts[r['path']];seen[i].update(range(a,z+1))
def suffix(lines):
 start=max(i for i,x in enumerate(lines) if x.startswith('// Origin: '));text='\n'.join(lines[start:]);ids=set(re.findall(r'(?:BoundaryRecord|BoundaryError|l4_boundary_tests_)([a-f0-9]{8})',text));assert len(ids)==1;ident=next(iter(ids))
 assert len(re.findall(ident,text))==len(re.findall(r'(?:BoundaryRecord|BoundaryError|l4_boundary_tests_)'+ident,text))
 norm=text.replace(lines[start],'// Origin: {ORIGIN}',1).replace(lines[start+1],'// Claim: {CLAIM}',1).replace(ident,'{ID}')
 return start+1,text,ident,norm
tm={t['index']:t for t in transfers['transfers']};assert len(tm)==69
for t in transfers['transfers']:
 i=t['index'];assert t['path']==S[i]['path'] and t['sha256']==S[i]['sha256'];a,text,ident,norm=suffix(bodies[t['path']]);base=t['base'];bi=base['index'];bs,bt,bid,bnorm=suffix(bodies[base['path']])
 assert base['path']==S[bi]['path'] and base['sha256']==S[bi]['sha256']
 assert set(range(base['lines'][0],base['lines'][1]+1))<=seen[bi]
 assert [a,counts[t['path']]]==t['reviewed_lines'] and [bs,counts[base['path']]]==base['lines']
 assert h(text.encode())==t['trailer_sha256_utf8_lf'] and h(bt.encode())==base['body_sha256_utf8_lf']
 assert norm==bnorm and h(norm.encode())==t['normalized_complete_text_sha256'] and t['all_other_text_exactly_equal']
 assert t['complete_residual']=={'origin':bodies[t['path']][a-1],'claim':bodies[t['path']][a],'identifier':ident,'identifier_occurrences':len(re.findall(ident,text))}
assert set(r['path'] for r in report['file_reviews'])==set(scope_by)
direct=0;transfer=0
for i,r in enumerate(report['file_reviews']):
 assert r['path']==S[i]['path'] and r['sha256']==S[i]['sha256'];n=counts[r['path']]
 assert r['full_source_read'] is True and r['source_line_count']==n and r['reviewed_lines']==[[1,n]] and len(r['assessment'])>150
 got=set(seen[i]);whole=set(range(1,n+1))
 if got==whole:direct+=1;assert 'template_transfer' not in r
 else:
  transfer+=1;assert r['template_transfer']==tm[i];a,z=tm[i]['reviewed_lines'];got.update(range(a,z+1))
 assert got==whole
assert (direct,transfer)==(33,66)
ranges=0
def walk(x):
 global ranges
 if isinstance(x,dict):
  if all(k in x for k in ['path','sha256','lines']) and x['path'] in scope_by:
   row=scope_by[x['path']];assert x['sha256']==row['sha256'];a,z=x['lines'];assert 1<=a<=z<=counts[x['path']];ranges+=1
  for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(report);walk(controls)
assert len(report['claims'])==6 and len(report['findings'])==11 and len(controls['controls'])==14
ids=[r['id'] for r in report['claims']+report['findings']+controls['controls']];assert len(ids)==len(set(ids))
controlids={r['id'] for r in controls['controls']};assert all(r['status']=='PASS' for r in controls['controls'])
for r in report['claims']+report['findings']:assert set(r.get('independent_controls',[]))<=controlids
assert report['controls_sha256']==h(Path(str(P)+'_controls.json').read_bytes())
assert report['reading_ledger_sha256']==h(Path(str(P)+'_read_ledger.json').read_bytes())
assert report['template_transfer_sha256']==h(Path(str(P)+'_template_transfers.json').read_bytes())
for r in report['audit_inputs']+[report['prior_report'],report['completion_reading_snapshot']]:assert h((R/r['path']).read_bytes())==r['sha256']
assert load('_remaining_scope.json')['pending_files']==0
syntax=[]
for p in sorted(P.parent.glob(P.name+'*.py')):ast.parse(p.read_text(encoding='utf8'));syntax.append(p.relative_to(R).as_posix())
snap=Path(str(P)+'_final.json.snapshot');rb=Path(str(P)+'.json').read_bytes()
if snap.exists():assert snap.read_bytes()==rb
else:snap.write_bytes(rb)
artifacts=[]
for suffix in ['.json','.md','_controls.py','_controls.json','_read_ledger.json','_template_transfers.json','_notes.json','_finalize.py','_validate.py','_final.json.snapshot']:
 p=Path(str(P)+suffix);artifacts.append({'path':p.relative_to(R).as_posix(),'sha256':h(p.read_bytes()),'size_bytes':p.stat().st_size})
result={'status':'PASS','scope_sha256':h(raw),'source_pins_checked':99,'source_bytes_checked':totalbytes,'source_lines_checked':sum(counts.values()),'full_direct_reads':direct,'full_prefix_template_reads':transfer,'complete_template_rows_rederived':69,'evidence_ranges_checked':ranges,'partial':0,'bounded':0,'pending':0,'claims':6,'findings':11,'independent_controls_passed':14,'original_execution':0,'original_source_edits':0,'audit_python_syntax_checked':syntax,'artifacts':artifacts,'limits':'Custody/range validation verifies reading-receipt consistency, not theorem correctness or production behavior. Semantic body assessments and fresh independent finite controls are separately recorded.'}
Path(str(P)+'_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ['audit_python_syntax_checked','artifacts']},indent=2))
print('VALIDATION_SHA256',h(Path(str(P)+'_validation.json').read_bytes()))
for r in artifacts[:4]:print(r['path'],r['sha256'])
