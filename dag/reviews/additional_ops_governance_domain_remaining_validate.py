"""Read-only source custody and audit-artifact reference validation."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_ops_governance_domain_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
def read(s):return json.loads(Path(str(P)+s).read_bytes())
sb=Path(str(P)+'_scope.json').read_bytes();assert h(sb)=='c68c6e94776473c2a759da43724b5a6c74fc33dfc07927e1fc6ece096b535ea9'
scope=json.loads(sb);report=read('.json');ledger=read('_read_ledger.json');controls=read('_controls.json');notes=read('_notes.json');remaining=read('_remaining_scope.json')
assert len(scope['files'])==164 and len(report['file_reviews'])==164 and len(notes)==164
assert not remaining['files'] and remaining['pending_files']==0
by_path={};source_bytes=0;lines=0
for i,row in enumerate(scope['files']):
 p=R/row['path'];b=p.read_bytes();t=b.decode('utf8');n=len(t.splitlines())
 assert h(b)==row['sha256'] and len(b)==row['size_bytes']
 ast.parse(t,filename=row['path'])
 by_path[row['path']]={'sha256':h(b),'lines':n,'index':i};source_bytes+=len(b);lines+=n
assert source_bytes==377900 and lines==10427
for row in report['file_reviews']:
 info=by_path[row['path']];n=info['lines'];i=info['index']
 assert row['sha256']==info['sha256'] and row['full_source_read'] is True and row['reviewed_lines']==[[1,n]] and row['source_line_count']==n
 assert row['assessment']==notes[str(i)] and len(row['assessment'])>50
 seen=set()
 for receipt in ledger:
  if receipt['index']==i:
   assert receipt['path']==row['path'] and receipt['sha256']==info['sha256'] and receipt['total_lines']==n
   a,z=receipt['displayed_lines'];assert 1<=a<=z<=n;seen.update(range(a,z+1))
 assert seen==set(range(1,n+1))
ids=[r['id'] for key in ('claims','findings') for r in report[key]]
assert len(ids)==len(set(ids))==24
control_ids={r['id'] for r in controls['controls']};assert len(control_ids)==20
for row in report['findings']:assert set(row['independent_controls'])<=control_ids
range_count=0
def check_refs(value):
 global range_count
 if isinstance(value,dict):
  if all(k in value for k in ('path','sha256','lines')):
   assert value['path'] in by_path
   info=by_path[value['path']];a,z=value['lines']
   assert value['sha256']==info['sha256'] and 1<=a<=z<=info['lines'];range_count+=1
  for child in value.values():check_refs(child)
 elif isinstance(value,list):
  for child in value:check_refs(child)
check_refs(report);check_refs(controls)
assert report['reading_ledger_sha256']==h(Path(str(P)+'_read_ledger.json').read_bytes())
assert report['controls_sha256']==h(Path(str(P)+'_controls.json').read_bytes())
for prior in report['prior_review_reconciliation']:
 p=R/prior['path'];assert h(p.read_bytes())==prior['sha256']
 d=json.loads(p.read_bytes());existing={r['id'] for k in ('claims','findings') for r in d.get(k,[])}
 assert set(prior['claim_or_finding_ids'])<=existing
assert report['status']=='complete_declared_scope'
assert report['summary']['full_source_reads']==164 and report['summary']['pending']==0
assert report['summary']['original_modules_executed']==0 and controls['summary']['original_functions_executed']==0
for suffix in ['_build.py','_read.py','_finish_notes.py','_controls.py','_finalize.py','_validate.py']:
 ast.parse(Path(str(P)+suffix).read_text(encoding='utf8'))
artifacts={}
for suffix in ['.json','.md','_scope.json','_read_ledger.json','_notes.json','_controls.py','_controls.json','_build.py','_finalize.py','_validate.py','_remaining_scope.json']:
 p=Path(str(P)+suffix);b=p.read_bytes();artifacts[p.relative_to(R).as_posix()]={'sha256':h(b),'bytes':len(b)}
out={'status':'PASS','scope_sha256':h(sb),'summary':{'source_pins_checked':164,'full_source_reads':164,'partial_source_reads':0,'bounded_artifact_dispositions':0,'pending':0,'source_bytes':source_bytes,'source_lines':lines,'source_ast_parse_count':164,'source_evidence_ranges_checked':range_count,'claims':6,'findings':18,'independent_finite_controls':20,'original_functions_or_modules_executed':0},'validation_limits':['AST parsing checks syntax only, not imports, runtime behavior, formal proof or functional correctness.','Ledger coverage and hashes validate custody of the declared readings; substantive assessments are manual, not inferred from the validator.','Twenty controls are independent finite predicate reconstructions, not retained test-suite passes.'], 'artifacts':artifacts}
Path(str(P)+'_validation.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'status':'PASS','summary':out['summary'],'report_sha256':artifacts['dag/reviews/additional_ops_governance_domain_remaining.json']['sha256'],'validation_sha256':h(Path(str(P)+'_validation.json').read_bytes())},indent=2))
