"""Verify audit pins/ranges/transfer bookkeeping without executing retained programs."""
from pathlib import Path
import collections,difflib,hashlib,json
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
load=lambda s:json.loads(Path(str(P)+s).read_text(encoding='utf8'))
inv=load('_inventory.json');rows=inv['files'];report=load('.json');scope=load('_scope.json');notes=load('_notes.json')['assessments'];errors=[];raw={};by={r['path']:r for r in rows}
for r in rows:
 b=(R/r['path']).read_bytes();raw[r['index']]=b
 if hashlib.sha256(b).hexdigest()!=r['sha256']:errors.append(['scope_hash',r['path']])
 if len(b)!=r['bytes']:errors.append(['scope_bytes',r['path']])
 if r['lines'] is not None and len(b.decode('utf8').splitlines())!=r['lines']:errors.append(['scope_lines',r['path']])
if hashlib.sha256(Path(str(P)+'_scope.json').read_bytes()).hexdigest()!=inv['scope_sha256']:errors.append(['scope_manifest_changed'])
reviews={r['path']:r for r in report['file_reviews']}
if set(reviews)!=set(by):errors.append(['population_mismatch'])
if len(reviews)!=len(report['file_reviews']):errors.append(['duplicate_file_review'])
def ranges_valid(path,ranges):
 n=by[path]['lines']
 return all(type(a)is int and type(b)is int and n is not None and 1<=a<=b<=n for a,b in ranges)
for path,r in reviews.items():
 if r['sha256']!=by[path]['sha256']:errors.append(['review_hash',path])
 if not ranges_valid(path,r['reviewed_lines']):errors.append(['review_ranges',path])
 if r['full_source_read'] and r['reviewed_lines']!=[[1,by[path]['lines']]]:errors.append(['full_range_missing',path])
 if not r['assessment'].strip():errors.append(['missing_assessment',path])
 for dep in r.get('related_owner_evidence',[]):
  if dep['path'] not in by or dep['sha256']!=by[dep['path']]['sha256']:errors.append(['context_owner_pin',path,dep['path']])
  elif not reviews[dep['path']]['full_source_read']:errors.append(['context_owner_not_full',path,dep['path']])
for x in report['claims']+report['findings']:
 for e in x['source_evidence']:
  if e['path'] not in by:errors.append(['evidence_outside_scope',x['id'],e['path']]);continue
  if e['sha256']!=by[e['path']]['sha256'] or not ranges_valid(e['path'],e['lines']):errors.append(['evidence_pin_range',x['id'],e['path']])
  if e['full_source_read']!=reviews[e['path']]['full_source_read']:errors.append(['evidence_full_flag',x['id'],e['path']])
full={r['index'] for r in rows if reviews[r['path']]['full_source_read']};direct=set();ledger=load('_read_ledger.json');intervals_by_index=collections.defaultdict(list)
for x in ledger:
 i=x['index'];r=rows[i]
 if x['sha256']!=r['sha256']:errors.append(['read_ledger_hash',i])
 intervals_by_index[i].extend(x['displayed_lines'])
for i,intervals in intervals_by_index.items():
 r=rows[i];intervals=sorted(intervals);covered=0
 for a,b in intervals:
  if a<=covered+1:covered=max(covered,b)
 if r['lines'] is not None and covered>=r['lines'] and i in full:direct.add(i)
edges=[]
for x in load('_delta_ledger.json'):
 a,b=x['base_index'],x['target_index']
 if x['base_sha256']!=rows[a]['sha256'] or x['target_sha256']!=rows[b]['sha256']:errors.append(['delta_pin',a,b])
 d=''.join(difflib.unified_diff(raw[a].decode().splitlines(True),raw[b].decode().splitlines(True),fromfile=rows[a]['path'],tofile=rows[b]['path']))
 if hashlib.sha256(d.encode()).hexdigest()!=x['diff_sha256']:errors.append(['delta_text_hash',a,b])
 if x['full_diff_displayed']:edges.append((a,b,'complete_unified_diff'))
for x in load('_target_delta_ledger.json'):
 a,b=x['base_index'],x['target_index'];aa=raw[a].decode().splitlines();bb=raw[b].decode().splitlines()
 if x['base_sha256']!=rows[a]['sha256'] or x['target_sha256']!=rows[b]['sha256']:errors.append(['target_delta_pin',a,b])
 if [list(y) for y in difflib.SequenceMatcher(a=aa,b=bb,autojunk=False).get_opcodes()]!=x['opcodes']:errors.append(['target_delta_opcodes',a,b])
 edges.append((a,b,'complete_target_delta'))
for k,n in notes.items():
 if n.get('review_level')=='full_source_via_exact_reviewed_base_with_context':
  a,b=n['base_index'],int(k)
  if raw[a]!=raw[b] or n['base_sha256']!=rows[a]['sha256']:errors.append(['exact_transfer',a,b])
  edges.append((a,b,'exact_bytes_with_context'))
closed=set(direct);routes={i:{'method':'complete_numbered_body_display'} for i in direct}
while True:
 old=len(closed)
 for a,b,kind in edges:
  if a in closed and a in full and b in full and b not in closed:closed.add(b);routes[b]={'base_index':a,'base_path':rows[a]['path'],'base_sha256':rows[a]['sha256'],'method':kind}
 if len(closed)==old:break
unaccounted=sorted(full-closed)
if unaccounted:errors.append(['full_read_method_unaccounted',unaccounted])
out={'status':'pass' if not errors else 'fail','source_scope_paths':len(rows),'current_source_hashes_matched':len(rows)-sum(x[0]=='scope_hash' for x in errors),'scope_manifest_sha256':inv['scope_sha256'],'file_reviews':len(reviews),'full_source_reads':len(full),'bounded_dispositions':len(reviews)-len(full),'full_source_line_coverage':report['summary']['full_source_lines'],'pending':len(report['pending_paths']),'claims':len(report['claims']),'findings':len(report['findings']),'full_read_method_accounting':{'direct_complete_display_bases':len(direct),'full_base_equality_or_delta_dependents':len(closed-direct),'unaccounted':unaccounted,'routes':{str(k):v for k,v in sorted(routes.items())}},'evidence_checks':'All source pins/ranges/full flags and related owner pins checked; display ledger supports bookkeeping, notes attest substantive reading, no automated human-read inference.','retained_program_execution':False,'report_sha256':hashlib.sha256(Path(str(P)+'.json').read_bytes()).hexdigest(),'markdown_sha256':hashlib.sha256(Path(str(P)+'.md').read_bytes()).hexdigest(),'controls_sha256':hashlib.sha256(Path(str(P)+'_controls.json').read_bytes()).hexdigest(),'errors':errors}
Path(str(P)+'_validation.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ['full_read_method_accounting']}));print('method_counts',len(direct),len(closed-direct),'unaccounted',unaccounted)
raise SystemExit(bool(errors))
