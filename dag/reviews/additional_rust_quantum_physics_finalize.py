"""Validate audit custody/coverage and emit final report; never changes source."""
import collections,datetime,hashlib,json,pathlib,re,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics'
def unique_object(pairs):
 d={}
 for k,v in pairs:
  if k in d:raise ValueError('duplicate JSON key: '+k)
  d[k]=v
 return d
def read(s):return json.loads((H/(P+s)).read_text(encoding='utf-8'),object_pairs_hook=unique_object)
def sha(raw):return hashlib.sha256(raw).hexdigest()
scope=read('_scope.json');files={x['path']:x for x in scope['files']};notes=read('_notes.json');extra=read('_supplement.json')
assert len(files)==203 and set(notes)==set(files)
for path,x in files.items():
 raw=(R/path).read_bytes();assert sha(raw)==x['sha256'];assert len(raw)==x['bytes'];assert len(raw.decode().splitlines())==x['lines'];assert len(notes[path])>80
templates=read('_template_receipts.json');assert len({x['path']for x in templates})==len(templates)
emissions=read('_emissions.json');coverage={p:set()for p in files};shared_lines=0
for e in emissions:
 assert e['sha256']==files[e['path']]['sha256'];lo,hi=e['emitted_lines'];assert 1<=lo<=hi<=files[e['path']]['lines'];coverage[e['path']].update(range(lo,hi+1))
normalize=lambda x:re.sub(r'(?<=BoundaryRecord)[0-9a-f]{8}|(?<=BoundaryError)[0-9a-f]{8}|(?<=l4_boundary_tests_)[0-9a-f]{8}','TEMPLATE',x)
for t in templates:
 target=t['path'];canon=t['canonical_path'];assert canon in notes
 assert t['sha256']==t['reconstruction_sha256']==files[target]['sha256'];assert t['canonical_sha256']==files[canon]['sha256']
 a=(R/canon).read_bytes().decode().splitlines(keepends=True);rebuilt=[];cursor=1
 for chunk in t['chunks']:
  lo,hi=chunk['target_lines'];assert lo==cursor;assert hi-lo+1==len(chunk['target_text']);cursor=hi+1
  if chunk['kind']=='shared_full_segment':
   cl,ch=chunk['canonical_lines'];assert list(map(normalize,a[cl-1:ch]))==list(map(normalize,chunk['target_text']));shared_lines+=hi-lo+1
  else:assert chunk['kind']=='full_source_text'
  rebuilt.extend(chunk['target_text']);coverage[target].update(range(lo,hi+1))
 assert cursor==files[target]['lines']+1;assert sha(''.join(rebuilt).encode())==files[target]['sha256']
assert all(set(range(1,files[p]['lines']+1))<=lines for p,lines in coverage.items())
probe_runs=0;probe_sources=set();probe_receipts=[]
for i in range(1,17):
 suffix=f'_validation_{i:02}.json';receipt=read(suffix);probe=H/(P+f'_probe_{i:02}.rs');assert sha(probe.read_bytes())==receipt['probe_sha256']
 for pin in receipt['source_files']:
  assert sha((R/pin['path']).read_bytes())==pin['sha256'];probe_sources.add(pin['path'])
 runs=receipt.get('runs',[receipt.get('run')]);assert all(run['compile_exit']==0 and run['exit_code']==0 for run in runs);probe_runs+=len(runs)
 probe_receipts.append({'path':'dag/reviews/'+P+suffix,'sha256':sha((H/(P+suffix)).read_bytes()),'successful_executions':len(runs)})
for finding in extra['findings']:
 if finding['id'] in {'QP-F041','QP-F042','QP-F043','QP-F044'}:
  finding['status']='bounded native counterexamples reproduced';finding['validation_receipt']='dag/reviews/'+P+'_validation_16.json'
 elif finding['id']=='QP-F045':
  finding['status']='source-confirmed missing semantic binding; fixed positive native control passed';finding['validation_receipt']='dag/reviews/'+P+'_validation_16.json'
v17={'id':'QP-V017','kind':'offline current-source native verifier and diagnostic counterexamples','receipt':'dag/reviews/'+P+'_validation_16.json','result':'Four current owners and current cyclotomic helper compiled and ran with exit0. Zero GHZ state and Some99 Chern grid still pass; excess eigenvector coordinates accepted and short vector panics; WDW nonzero boundary residual omitted; thermal basis[2] produces trace4; negative/NaN anisotropic probabilities accepted. Rank-one Gram gives indistinguishable states but raw product rank4 and Passes; empty tables and dimension0 pass. Seven fixed registry terminals, transport/noisy rivals and33-family/177-label fixed DAG master controls behave as asserted.','limits':'Tiny exact/numerical controls with SHA-pinned cached lower libraries and an explicit parent-import adapter. Initial probe-only import-path compile error preserved in validation_16_probe_error.json. No broad build, proof of universal correctness or physical validation.'}
v18={'id':'QP-V018','kind':'mechanical audit-custody and report-schema checks','receipt':'dag/reviews/'+P+'_integrity.json','result':'All203 original scope source hashes/bytes/line counts, per-file manual assessments, explicit source-emission coverage,155 lossless shared-template reconstructions, unique IDs and evidence ranges validated. Sixteen final native probe receipts retain19 successful executions.','limits':'Coverage and hash checks support custody only. They do not convert parsing, source emission, repetitive scaffold tests or bounded counterexamples into mathematical proof.'}
extra['validation']=[x for x in extra['validation']if x['id']not in {'QP-V017','QP-V018'}]+[v17,v18]
for section in ['claims','findings','validation']:
 ids=[x['id']for x in extra[section]];assert len(ids)==len(set(ids))
for c in extra['claims']:assert all(k in c for k in ['id','claim','evidence','dependencies','limitations'])
evidence_count=0
for entry in extra['claims']+extra['findings']:
 for ev in entry['evidence']:
  lo,hi=ev['lines'];assert ev['path']in files;assert 1<=lo<=hi<=files[ev['path']]['lines'];evidence_count+=1
(H/(P+'_supplement.json')).write_text(json.dumps(extra,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,'-B','-X','utf8',str(H/(P+'_checkpoint.py'))],check=True)
d=read('.json');assert not d['remaining_work'];assert d['status']=='complete';assert all(x['full_source_read']is True and x['reviewed_lines']==[[1,files[x['path']]['lines']]]for x in d['file_reviews'])
d['methodology']={'scope_basis':'Frozen pending original-inventory files under code/rust/core_quantum_physics, excluding prior full reads; source commit8050. Completion applies only to this203-file slice.','semantic_review':'Each complete distinct source body and every semantic difference was manually read and assessed.155 files use explicitly identified previously read exact segments plus full differences and generated-name substitutions;48 use direct complete text. Source emissions or reconstruction alone never supplied full-read credit.','shared_segment_reconstruction_files':len(templates),'shared_segment_lines':shared_lines,'source_read_emission_coverage':'All99,889 source lines covered by direct emissions or lossless shared-template receipts.','mathematical_boundaries':'Declared finite carriers, physical admissions, exact checks, numerical diagnostics, status labels and formal proof are kept distinct in per-file notes and claims.','validation_limits':'Sixteen focused offline probe receipts with19 successful executions; cached dependencies explicitly pinned; current owning modules or documented current prefixes compiled. No whole-crate test/build or Lean proof run. Failure artifacts and probe corrections preserved.','excluded':'No source edits; no private benchmark, seed, answer key, live provider or network/download access. No extrapolation to original every-file corpus completion.'}
(H/(P+'.json')).write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
severity=collections.Counter(x['severity']for x in d['findings'])
integrity={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':scope['source_commit'],'files':203,'lines':99889,'bytes':3692137,'semantic_assessments':len(notes),'full_source_read_rows':203,'remaining_paths':0,'source_hashes_match':True,'direct_or_shared_emission_coverage_complete':True,'template_reconstructions':len(templates),'template_canonical_hashes_and_normalized_segments_match':True,'unique_claim_ids':len(d['claims']),'unique_finding_ids':len(d['findings']),'unique_validation_ids':len(d['validation']),'evidence_ranges_in_source_bounds':evidence_count,'probe_receipts':probe_receipts,'successful_native_executions':probe_runs,'probe_source_pin_paths':len(probe_sources),'report_sha256':sha((H/(P+'.json')).read_bytes()),'limits':'This is mechanical custody/schema validation, not independent semantic review or a mathematical proof. Native library hashes are recorded by each compilation receipt; final integrity checks source and probe hashes without rerunning or rebuilding dependencies.'}
(H/(P+'_integrity.json')).write_text(json.dumps(integrity,indent=2)+'\n',encoding='utf-8')
md=f'''# Rust quantum physics source audit

Completed **203/203 frozen files**, **99,889 lines**, **3,692,137 bytes**, pinned to `{scope['source_commit']}`. No pending paths in this slice. The original repository-wide audit remains separate.

The [JSON report]({P}.json) contains 33 claims, 45 findings ({severity['high']} high, {severity['medium']} medium, {severity['low']} low), exact source references, dependencies, limitations and one substantive assessment per file. This review distinguishes supplied finite mathematics from physical premises and from numerical or catalogue evidence.

There are genuine finite mechanisms here: Gaussian-rational states and operators; exact Kraus/Choi and density checks; finite contextuality, MUB and stabilizer constructions; rational/cyclotomic Bell, Page–Wootters and interference controls; and exact finite representation identities. Their carriers, inner products, tensor rules, positive cones, physical formulas and measured constants are admitted inputs. The controls do not derive these admissions from primitive difference, choose a unique physical theory, or establish a continuum limit.

The principal actionable findings are:

- **Certificate/receipt replay:** public mutable CHSH, GHZ, Chern, Everett and MUB reports can retain passing labels after witness corruption. Exact claims need reconstruction from bound carriers and witnesses, rather than stored flags or unverified fields.
- **False enclosures and omitted obligations:** entropy workpad interval admission and odd pi/zeta truncation controls accept invalid claimed bounds; higher-dimensional exact-spectrum obligations can miss zero multiplicities. Numerical Regge residuals omit boundary equations and thermal construction trusts unnormalized eigenvectors.
- **Operational tomography:** the general pairing audit ranks raw product-effect coordinates even when a degenerate Gram erases state distinguishability. Empty composite tables and inconsistent declared dimensions also pass.
- **DAG evidence overreach:** `derivation_dag_witnesses.rs` returns a 33-family, 177-label passing master by finite examples, fixed counts and table sums. Its 142-node completion applies one generic C4/affine predicate, with no actual DAG, theorem, source-hash or route-contract binding. This is a regression catalogue, not independent proof coverage (QP-F045).
- **Resource/domain limits:** malformed shapes can panic; some probability and rational encodings evade intended guards; aggregate allocations and enumeration costs are not always covered by local limits. Unsafe large allocations were assessed analytically and were not executed.

**Validation:** 16 focused offline native probe receipts contain 19 successful executions, including positive controls and bounded counterexamples. The final probe confirms zero-GHZ/Some99-Chern acceptance, a shape-invalid eigenvector, zero reported WDW residual with nonzero boundary equations, trace4 thermal output, invalid noise probabilities, and degenerate-pairing tomography acceptance. The seven fixed pairing registry terminals still behave as specified. These results do not constitute a whole-crate test run, a Lean proof, or empirical physical evidence.

**Review custody:** 48 files were read as complete direct text; 155 were read using complete distinct bodies/differences plus explicitly identified previously read exact segments. All 155 reconstructions match source hashes. Manual per-file assessments supplied semantic credit; parsing/emission and disconnected generated boundary tests did not. The [integrity receipt]({P}_integrity.json) validates all source pins, line ranges, review rows and final probe receipts. Probe-only mistakes remain preserved alongside corrected runs.

No original sources were changed. No private benchmark/seed/key, provider call, download or broad native build was used. Findings are a repair backlog; this audit does not claim they have been fixed.
'''
(H/(P+'.md')).write_text(md,encoding='utf-8')
print(json.dumps({k:integrity[k]for k in ['files','lines','full_source_read_rows','remaining_paths','template_reconstructions','unique_claim_ids','unique_finding_ids','successful_native_executions','report_sha256']},indent=2))
