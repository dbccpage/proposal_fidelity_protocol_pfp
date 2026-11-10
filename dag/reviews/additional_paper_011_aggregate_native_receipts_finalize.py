import ast,collections,difflib,hashlib,json,re,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts'
def load(s):return json.loads((H/(P+s)).read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
prep=load('_preparation.json');report=load('.json');rows={x['path']:x for x in prep['files']};reviews={x['path']:x for x in report['file_reviews']};assert set(rows)==set(reviews);assert len(reviews)==386;assert report['status']=='complete'
for p,r in rows.items():
 raw=(R/p).read_bytes();assert sha(raw)==r['sha256']==reviews[p]['sha256'];assert len(raw)==r['bytes'];assert reviews[p]['assessment']
 if reviews[p]['full_source_read']:
  assert reviews[p]['reviewed_lines']==([[1,r['lines']]] if r['lines'] else [])
 else:assert reviews[p]['reviewed_lines']==[]
 if p.endswith('.py'):ast.parse(raw,filename=p)
ledger=load('_read_ledger.json');deltas={x['path']:x for x in load('_deltas.json')};prior_deltas={x['path']:x for x in load('_source_comparison.json')};dledger=load('_delta_read_ledger.json');validated=set();visiting=set()
def validate(p):
 if p in validated:return
 assert p not in visiting;visiting.add(p);r=reviews[p];assert r['full_source_read']
 t=r.get('body_transfer')
 if not t:
  read={i for x in ledger if x['path']==p and not x.get('output_truncated') for a,b in x['reviewed_lines'] for i in range(a,b+1)}
  assert read==set(range(1,rows[p]['lines']+1)),p
 else:
  bp=t['base_path'];bb=(R/bp).read_bytes();assert sha(bb)==t['base_sha256']
  if bp in reviews:validate(bp)
  else:
   original=json.loads((R/t['base_report']).read_text())
   q=next(x for x in original['file_reviews'] if x['path']==bp);assert q['full_source_read'] and q['sha256']==t['base_sha256']
  raw=(R/p).read_bytes()
  if raw==bb:assert t['sha256']==t['base_sha256']
  elif p in deltas:
   d=deltas[p];assert t['delta_sha256']==sha('\n'.join(d['diff']).encode())
   read={i for x in dledger if x['path']==p and x['delta_sha256']==t['delta_sha256'] for a,b in x['reviewed_diff_lines'] for i in range(a,b+1)};assert read==set(range(1,len(d['diff'])+1))
   base=ast.unparse(ast.parse(bb))+'\n' if 'normalized_ast' in d['method'] else bb.decode()
   diff=list(difflib.unified_diff(base.splitlines(),raw.decode().splitlines(),fromfile=bp+(' [ast.unparse]' if 'normalized_ast' in d['method'] else ''),tofile=p,n=3));assert diff==d['diff']
  else:
   assert t.get('complete_diff_read');d=prior_deltas[p];diff=list(difflib.unified_diff(bb.decode().splitlines(),raw.decode().splitlines(),fromfile=bp,tofile=p,n=3));assert diff==d['diff']
 visiting.remove(p);validated.add(p)
for p,r in reviews.items():
 if r['full_source_read']:validate(p)
arch=load('_archive_checks.json');assert sha((R/arch['archive']).read_bytes())==arch['archive_sha256'];arows={x['path']:x for x in arch['files']}
target=next(p for p in rows if p.endswith('original_recovery_v1/final_v4/executed_runner.py'));a=arows[target]
with zipfile.ZipFile(R/arch['archive']) as z:
 old=z.read(a['archive_member']);assert sha(old)==a['archive_sha256']
 def rolecheck(raw):
  fn=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='parse_rounds')
  roles=next(n for n in ast.walk(fn) if isinstance(n,ast.List) and len(n.elts)==8 and all(isinstance(v,ast.Constant) and isinstance(v.value,str) for v in n.elts))
  return {'source_lines':[fn.lineno,fn.end_lineno],'required_roles':[n.value for n in roles.elts],'word_shape_matches':{n.value:bool(re.fullmatch(r'\w+',n.value)) for n in roles.elts}}
 add={'prior_finding':'P011CORE-F09','prior_report':'dag/reviews/additional_paper_011_core.json','current_source':{'path':target,'sha256':rows[target]['sha256'],**rolecheck((R/target).read_bytes())},'archive_source':{'archive':arch['archive'],'archive_sha256':arch['archive_sha256'],'member':a['archive_member'],'sha256':a['archive_sha256'],**rolecheck(old)},'conclusion':'Current multiword replacement roles cannot be produced by the unchanged word-only regex; original archived single-word roles satisfy its lexical shape. This establishes a transformation regression and does not establish full original dialogue validation. Original core report remains untouched.','method':'AST-read role constants and independent stdlib regex fullmatch only; original parser and provider/native runtime not executed.'}
(H/(P+'_f09_provenance_addendum.json')).write_text(json.dumps(add,indent=2)+'\n',encoding='utf-8');(H/(P+'_f09_provenance_addendum.md')).write_text('# P011CORE-F09 provenance addendum\n\n'+add['conclusion']+'\n\nCurrent source SHA: '+add['current_source']['sha256']+'\n\nArchived source SHA: '+add['archive_source']['sha256']+'\n\n'+add['method']+'\n',encoding='utf-8')
for f in report['claims']+report['findings']:
 for e in f['source_evidence']:
  assert e['path'] in rows;assert e['sha256']==rows[e['path']]['sha256']
  assert all(1<=lo<=hi<=rows[e['path']]['lines'] for lo,hi in e['lines'])
for p,r in reviews.items():
 r['source_evidence']=[{'path':p,'sha256':r['sha256'],'lines':r['reviewed_lines'],'kind':'full_body' if r['full_source_read'] else 'bounded_parsed_or_opaque_artifact'}]
 r['archive_comparison']={k:arows[p].get(k) for k in ('archive_member','archive_sha256','raw_equal','LF_equal','explicit_name_mapping')}
 r['current_vs_historical']='This receipt assesses the pinned current inventory body. Original archived byte identity and any historical execution claims are separate; see archive comparison and scoped findings.'
 if r['full_source_read'] and ('inherited' in r['assessment'] or 'prior' in r['assessment']):r['assessment']+=' F09 inheritance, where relevant, describes the current transformed checkout only; the original archive has single-word roles and does not share that lexical impossibility.'
report['methodology']={'full_body':'Direct complete untruncated source reads, or hash-bound prior complete baseline plus all displayed differences. AST unparse normalization is explicit and every remaining target text difference was read. Recursive transfer validation is acyclic.','bounded_artifacts':'Every scoped large artifact has an individual purpose/claim assessment, complete parse/census where supported, declared checks and explicit ceilings. Repeated arrays/runtime catalogs and embedded source bytes are not automatically full-read credit. Encrypted envelopes are metadata/base64/custody only; executable binaries are hash/header only.','archive':'All386 originals identified, including6 explicit member-name mappings. Archive checks separate exact-byte transformations from mathematical claim predicates. Generic encoding trials are diagnostic unless the owning contract is explicit. No full archive body claim is made from CRC/hash equality.','fresh_execution':'Independent stdlib exact arithmetic, SHA, JSON, AST and regex controls only; no native/provider/credential/private benchmark access.','historical_evidence':'Retained compiler/test/native/provider records remain historical; copied records and repeated run data are not independent replications.'}
report['prior_findings_addenda']=[{'finding':'P011CORE-F09','path':'dag/reviews/'+P+'_f09_provenance_addendum.json','conclusion':add['conclusion']}]
report['scope_summary']['python_rust_full_body']=sum(p.endswith(('.py','.rs')) and r['full_source_read'] for p,r in reviews.items());report['scope_summary']['bytes']=sum(r['bytes'] for r in rows.values());report['scope_summary']['direct_full_body']=sum(r['full_source_read'] and not r.get('body_transfer') for r in reviews.values());report['scope_summary']['full_body_transfers']=sum(bool(r.get('body_transfer')) for r in reviews.values())
report['validation']={'all386_scope_hashes_and_sizes_match':True,'all_full_body_line_ranges_and_transfer_bases_verified':True,'all74_Python_sources_parse':True,'all_source_evidence_hashes_and_ranges_match':True,'archive_hash_verified':True,'pending':0}
(H/(P+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
md='# Paper011 aggregate and native receipt audit\n\nCompleted all386 frozen paths:162 full-body receipts (including explicit transfers),224 bounded artifacts,0 pending. All78 Python/Rust sources have complete body coverage. Original source bytes were preserved.\n\n'
md+='Independent exact arithmetic confirms8 rational complexes,8 integral cases and22 Smith certificates. This does not validate general geometric or physical interpretations. Four supplied Betti entries disagree with the retained matrices. Historical native/provider runs were not repeated.\n\n'
md+='The original ZIP resolves checkout duplicate keys, embedded input digests, captured machinery pins and all29 top-level self-digest cases. Fourteen archived capability/job artifact references remain unresolved. Current and archive bytes are distinct;108/386 are raw-equal,172/386 are LF-equal.\n\n'
md+='P011CORE-F09 is a current-checkout transformation regression: archived single-word roles fit the regex; replacement names with spaces do not. This is not proof of complete archived dialogue validation. The original core report was left intact.\n\n'
md+='## Findings\n\n'+'\n\n'.join('**'+f['id']+' — '+f['title']+'**\n\n'+f['statement'] for f in report['findings'])
md+='\n\n## Evidence and limits\n\nThe JSON contains one hash-bound assessment per file, reviewed ranges, transfer bases, archive identities, six scoped claims and seven findings. Separate helper receipts record exact arithmetic, all populations, custody comparisons and final validation. Encrypted envelopes, machine code, large source journals and runtime/dependency maps retain bounded dispositions. No sealed benchmark, private key, provider or native executable was accessed or run.\n\n'
md+='## Per-file dispositions\n\n'+'\n\n'.join('`'+p+'` — '+('full body' if r['full_source_read'] else 'bounded artifact')+'\n\n'+r['assessment'] for p,r in reviews.items())+'\n'
(H/(P+'.md')).write_text(md,encoding='utf-8')
validation={'status':'pass','scope':report['scope_summary'],'checks':report['validation'],'report_sha256':sha((H/(P+'.json')).read_bytes()),'markdown_sha256':sha((H/(P+'.md')).read_bytes()),'helper_hashes':{p.name:sha(p.read_bytes()) for p in sorted(H.glob(P+'*.py'))},'addendum_sha256':sha((H/(P+'_f09_provenance_addendum.json')).read_bytes())}
(H/(P+'_validation.json')).write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8');print(json.dumps(validation,indent=2))
