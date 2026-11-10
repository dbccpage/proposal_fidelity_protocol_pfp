"""Finalize Paper006 exact reading receipts and bounded artifact/test dispositions."""
import hashlib,json,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P='additional_paper_006_support';BASE='papers/pfp/006_pfp_epistemic_immune_system_and_cemetery_dag_mining/';OUT=HERE/(P+'_inspection')
def sha(b):return hashlib.sha256(b).hexdigest()
def load(s):return json.loads((HERE/(P+s)).read_text(encoding='utf-8'))
def write(s,x):(HERE/(P+s)).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
scope=load('_scope.json');rows={x['path']:x for x in scope['files']};all_rows={x['path']:x for x in scope['files']+scope['excluded_prior_full_reads']}
notes={}
for path in sorted(HERE.glob(P+'_notes*.json')):notes.update(json.loads(path.read_text(encoding='utf-8')))
coverage={}
for read in load('_read_ledger.json'):
 if not read.get('output_truncated'):coverage.setdefault(read['path'],set()).update(n for a,b in read['reviewed_lines'] for n in range(a,b+1))
transfers={x['path']:x for x in load('_base_transfer.json')};base_full={x['path']:x for x in json.loads((HERE/'additional_paper_004_support.json').read_text(encoding='utf-8'))['file_reviews'] if x['full_source_read']}
reviews=[]
for name,assessment in notes.items():
 path=BASE+name;row=rows[path];r={'path':path,'sha256':row['sha256'],'scope_role':'assigned','full_source_read':True,'reviewed_lines':[[1,row['lines']]] if row['lines'] else [],'review_level':'full_source_body_read','assessment':assessment}
 if path in transfers:
  t=transfers[path];assert t['base_sha256']==base_full[t['base_path']]['sha256'];assert sha((ROOT/t['base_path']).read_bytes())==t['base_sha256'];assert t['raw_equal'] or name=='pyproject.toml';r['base_equality_delta_transfer']=t
 else:assert coverage[path]==set(range(1,row['lines']+1)),path
 reviews.append(r)
assert len(reviews)==32
pdfs=json.loads((OUT/'pdf_inventory.json').read_text(encoding='utf-8'));pdf_equal={x['path']:x for x in load('_pdf_equality.json')}
for pdf in pdfs:
 r={'path':pdf['path'],'sha256':pdf['sha256'],'scope_role':'assigned','full_source_read':False,'reviewed_lines':[],'reviewed_pages':[[1,pdf['pages']]],'review_level':'all_pages_visual_with_explicit_equality_transfer','assessment':'All pages visually covered directly or through proven exact rendered-pixel/raw equality. Retained October2 v0.1 document, not current Markdown or fresh execution evidence. Tables, code and text readable at rendered review resolution; no clipping observed. Original omega_engine_symbol_game/Landau identifiers remain in PDFs, whereas loose Markdown/TeX have different later translations. Preserve historical PDF bytes; a current guide must identify the applicable source names.','binary_limit':'No raw PDF object-stream or full extracted-text reading claimed.'}
 if pdf['path'] in pdf_equal:r['equality_transfer']=pdf_equal[pdf['path']]
 elif pdf.get('raw_equal_render_base'):r['equality_transfer']={'method':'raw_byte_equality','base_path':pdf['raw_equal_render_base'],'base_sha256':pdf['sha256']}
 else:r['direct_visual_review']={'pages':pdf['pages'],'sheets':pdf['sheets'],'page_images':pdf['page_images']}
 reviews.append(r)
custody=load('_custody.json');manifest_stats=[]
for m in custody['current_manifests']:
 stats={'path':BASE+m['path'],'rows':len(m['entries']),'raw_failures':sum(not r.get('raw_match') for r in m['entries']),'unresolved_after_lf':sum(not(r.get('raw_match') or r.get('lf_match')) for r in m['entries'])};manifest_stats.append(stats)
 reviews.append({'path':stats['path'],'sha256':rows[stats['path']]['sha256'],'scope_role':'assigned','full_source_read':False,'reviewed_lines':[],'review_level':'all_records_parsed_hash_and_delta_validation','parsed_record_count':stats['rows'],'assessment':f"All {stats['rows']} path/digest pairs parsed, safe names checked, and bytes compared. {stats['raw_failures']} raw mismatches; {stats['unresolved_after_lf']} unresolved after LF normalization. Full historical/current manifest record differences also compared. This is custody accounting, not a source-body read or execution proof.",'validation_artifacts':['dag/reviews/'+P+'_custody.json','dag/reviews/'+P+'_manifest_deltas.json']})
catalog_path=BASE+'code/fixtures/pharmacy_catalog_52cb5457f6c4.json'
reviews.append({'path':catalog_path,'sha256':rows[catalog_path]['sha256'],'scope_role':'assigned','full_source_read':False,'reviewed_lines':[],'review_level':'all_records_parsed_bounded_semantic_catalog_review','parsed_record_count':61,'assessment':'All61 rows/schema and distinct semantic fields inspected, including every12 nonplaceholder row and every distinct placeholder pattern. Counts61 entries,14 classes,56 candidate/5 active labels,49 placeholder pairs match. Fifteen fields per entry; all labels remain data, not executable detectors. The syntax-error negative fixture is valid Python, and token-budget literals are not a general detector; no operational claim follows. Raw bytes differ from required historical SHA solely through CRLF conversion, so current worksheet/catalog tests fail. LF reconstruction exactly equals original archived bytes. Raw JSON punctuation and every identifier/date string were not claimed as a full text-body reading.','validation_artifacts':['dag/reviews/'+P+'_catalog.json','dag/reviews/'+P+'_test_results.json','dag/reviews/'+P+'_custody.json']})

full_paths={r['path'] for r in reviews if r['full_source_read']}|{BASE+'paper.md'}
manual_diffs={5,7,9,11,13,15,22,23,25,26,30,31,33,34,35,36};bounded_diffs={4,6};zip_reviews=[]
with zipfile.ZipFile(ROOT/custody['archive_path']) as z:
 for i,original in enumerate(custody['zip_members']):
  r=dict(original);r.update(archive_path=custody['archive_path'],archive_sha256=custody['archive_sha256'],full_source_read=False,base_review_path=r['current_path'])
  base_is_full=r['current_path'] in full_paths
  if 'complete_diff_path' in r:
   assert i in manual_diffs|bounded_diffs
   assert sha((ROOT/r['complete_diff_path']).read_bytes())==r['complete_diff_sha256']
   if i in manual_diffs:assert base_is_full;r.update(full_source_read=True,review_method='full_current_body_plus_complete_manually_read_diff')
   else:r['review_method']='all_record_manifest_base_plus_all_record_delta';r['limit']='Parsed manifest review does not become full source-body reading.'
  else:
   assert r.get('current_raw_equal') or r.get('current_lf_equal'),r['member']
   r['full_source_read']=base_is_full;r['review_method']=('full_read_base_plus_' if base_is_full else 'bounded_artifact_base_plus_')+('raw_equality' if r['current_raw_equal'] else 'complete_CRLF_LF_equality')
  if r['full_source_read']:
   count=len(z.read(r['member']).decode().splitlines());r['reviewed_lines']=[[1,count]] if count else []
  zip_reviews.append(r)
archive_path=custody['archive_path']
reviews.append({'path':archive_path,'sha256':rows[archive_path]['sha256'],'scope_role':'assigned','full_source_read':False,'reviewed_lines':[],'review_level':'archive_all_member_custody_with_complete_base_delta_dispositions','assessment':'All42 regular ZIP member bytes hashed; CRC, unique safe names, embedded40-entry MANIFEST and41-entry SHA256SUMS verified with no missing/mismatched members. Every member has a full-read base plus raw/LF equality or complete delta, or an explicitly bounded PDF/catalog/manifest disposition. Sixteen source/prose/receipt diffs manually read completely; two manifest deltas compared across every record. Five selected safe members copied byte-identically for fresh historical-copy tests; no broad source extraction or external model/native execution.','member_disposition_artifact':'dag/reviews/'+P+'.json#zip_member_reviews'})
assert len(reviews)==43 and {r['path'] for r in reviews}==set(rows)

dependency_assessments={
 'pfp/domain/exceptions.py':'Complete153-line body read. Domain error hierarchy and aliases are local exception types; TypedRefusalError requires a nonempty code and retains cause. LedgerIntegrity/Truncation errors supply taxonomy, not proof that every malformed input is caught. No provider/native imports.',
 'pfp/domain/entities/cemetery_entry.py':'Complete135-line body read. Frozen dataclasses enforce fixed marker/nonnegative exact counts and mapping/string types, but nested maps remain mutable and receipt digests/schema are not independently verified. Header promise of permanent full raw retention exceeds these constructors. Hash/equality are local object mechanisms, not authentication. Imported directly in isolated probes without package initializers.',
 'pfp/infrastructure/persistence/cemetery_sink.py':'Complete424-line body read in ranges1–224/225–424. Normalizes fractions, arbitrary stringified mapping keys and float tags; computes exact stored-byte digests, validates ordered entry schema/links/count/head, and rewrites through one .tmp path with os.replace. No lock/fsync; memory advances before write; cached receipt does not reread disk; header schema/genesis unbound and nested maps mutable. Current float rejection differs from historical baseline; float.hex loses distinct NaN payload bits and aliases explicit tag mappings, contradicting bit-for-bit claim. No universal persistence guarantee. Eleven existing storage tests pass only under explicitly isolated source loading, not production initialization.'}
deps=load('_dependency_scope.json')
for d in deps:
 raw=(ROOT/d['path']).read_bytes();assert sha(raw)==d['sha256'];assert len(raw.decode().splitlines())==d['lines']
 reviews.append({'path':d['path'],'sha256':d['sha256'],'scope_role':'additional_read_dependency','full_source_read':True,'reviewed_lines':[[1,d['lines']]],'review_level':'full_source_body_read','assessment':dependency_assessments[d['path']]})
all_rows.update({d['path']:{**d} for d in deps})

def ev(name,ranges=None):
 path=name if name.startswith(('papers/','pfp/')) else BASE+name;r=all_rows[path]
 return {'path':path,'sha256':r['sha256'],'lines':ranges if ranges is not None else ([[1,r['lines']]] if r.get('lines') else [])}
claims=[];findings=[]
def claim(suffix,statement,names,limits):
 es=[ev(n) for n in names];claims.append({'id':'PAPER006-'+suffix,'statement':statement,'status':'source_read_with_explicit_bounded_evidence','evidence':[e['path'] for e in es],'source_evidence':es,'limits':limits})
def finding(suffix,severity,statement,refs,action,validation=None):
 es=[ev(n,r) for n,r in refs];x={'id':'PAPER006-'+suffix,'severity':severity,'statement':statement,'evidence':[e['path'] for e in es],'source_evidence':es,'recommended_action':action}
 if validation:x['validation']='dag/reviews/'+P+validation
 findings.append(x)
claim('RETAINED-ANCHOR', 'An independently retained count/head can compare a fully verified ordered normalized-entry snapshot under deterministic encoding, checked chain/index relations and the assumed resistance to replacement against expected digests. Local rewritten-header consistency alone does not establish retained history, raw-file identity or event truth.', ['paper.md','code/tests/test_006_worked_example.py','pfp/infrastructure/persistence/cemetery_sink.py'], 'Single-writer controlled custody; independent anchor custody is supplied, not created by an unkeyed digest. Eleven isolated current-source storage controls do not establish all filesystem/parser behavior or historical execution.')
claim('DECAY-AND-COST-ARITHMETIC', 'Fixed-tau idle decay composes by telescoping floor differences: batches3/4/5 at tau5 cross0/1/1 intervals and multiply score by1/4. Under100 equal1000-byte records, whole-history rewrites write5,050,000 entry bytes versus100,000 final bytes. These are exact declared-input calculations.', ['code/examiner_worksheet.py','_lev_examiner_theoretical_minimum_quiz/instructor_key.md'], 'Nonnegative starting score, valid elapsed counts, fixed tau and no intervening reset/stimulation for batching. Cost model excludes headers/batching/compaction and is not measured throughput. Current worksheet stops at catalog hash; byte-identical historical copy completes all calculations.')
claim('CATALOG-IS-NONEXECUTING-DATA', 'The supplied catalog has61 entries,14 classes,56 candidate/5 active labels and49 placeholder fixture pairs. Existing tests reconstruct19 evidence digests from short identifying strings. These facts describe data and naming, not verified reproductions, applied filters or effectiveness.', ['code/fixtures/pharmacy_catalog_52cb5457f6c4.json','code/tests/test_006_catalog_file.py','paper_claim_ledger.md'], 'All-record parsed/schema review and fresh archived-copy three-test census. The entire original run corpus, harvesters and a semantic miner were not newly audited; their baseline negative-search claim stays historical.')
claim('CONTROLLED-REUSE-UTILITY', 'The reusable contribution is the separation of retained event, independently reproduced failure, proposed detector, valid near-miss control, scoped admission and observed host action. The companion teaches these obligations with24 explicit exercises and bounded exact arithmetic.', ['paper.md','_lev_examiner_theoretical_minimum_quiz/quiz.md','_lev_examiner_theoretical_minimum_quiz/instructor_key.md'], 'A proposed method and teaching package, not a measured learning gain or new mathematical foundation. Transfer to another task requires its own encoding, checker, valid controls and action semantics; public historical answers are not new sealed evaluation evidence.')
finding('CATALOG-CRLF-REPLAY-BLOCK', 'reproduction_blocker', 'The current catalog raw SHA is f672aeb1… while tests and worksheet require b95ce7c1…. Complete LF normalization produces exactly the original archived bytes/digest. Fresh current run yields three catalog setup errors and worksheet AssertionError; three toys pass. Five unchanged archived members yield six pure tests and a successful worksheet. This is a byte-custody/line-ending failure, not changed detector semantics.', [('code/tests/test_006_catalog_file.py',[[79,85]]),('code/examiner_worksheet.py',[[24,28]]),('code/fixtures/pharmacy_catalog_52cb5457f6c4.json',[])], 'Preserve original LF snapshot bytes through checkout/distribution controls or read a separately retained exact archive member. Do not merely bless converted bytes by changing the historical expected SHA.', '_test_results.json')
finding('LOOSE-MANIFEST-DRIFT', 'custody_mismatch', 'Current MANIFEST has25 raw mismatches, SHA256SUMS26;15/16 remain after LF normalization. The historical ZIP internal40/41-entry manifests have no mismatches. README says working manifests describe the current author-review revision, which these current checks contradict.', [('MANIFEST.sha256',[]),('SHA256SUMS',[]),('README.md',[[123,129]])], 'Keep historical archive immutable and issue separate current draft custody metadata after any authorized repairs; do not merge historical and current identities.', '_custody.json')
finding('HISTORICAL-RECEIPT-TRANSLATION', 'provenance_ambiguity', 'Loose historical first-publication receipt has rewritten source paths, commands and even retained stdout strings compared with its archived original, while original source hashes remain. Markdown uses pfp paths, TeX symbol_game, and preserved PDF/ZIP omega_engine_symbol_game. The receipt must not be presented as byte-unchanged historical evidence or proof those rewritten commands ran.', [('docs/first_publication_validation_2026_10_02.json',[[22,110],[128,158],[273,329]]),('paper.md',[[608,617]]),('paper.tex',[[208,212],[491,495]])], 'Treat archived receipt bytes as historical authority for provenance; publish a separate explicit current-path translation with before/after hashes. Do not silently translate embedded execution output.', '_custody.json')
finding('CURRENT-RETENTION-DOCSTRINGS', 'source_claim_overstatement', 'Current sink and entry docstrings still promise permanent zero-loss full raw retention, although normalization is lossy, nested maps mutable, whole-file writes lack fsync/locking, failed replace leaves memory ahead of disk, and receipt emission uses cached state. The paper correctly describes these limits; dependency documentation exceeds its actual contract.', [('pfp/infrastructure/persistence/cemetery_sink.py',[[1,14],[308,335],[381,414]]),('pfp/domain/entities/cemetery_entry.py',[[1,18]])], 'Align current API documentation with conditional normalized local retention and explicit recovery/custody limits. Preserve prior historical claims as records, not current guarantees.', '_test_results.json')
finding('FLOAT-BIT-PRESERVATION', 'encoding_claim_counterexample', 'Current sanitizer claims refused float values are recorded bit for bit. Distinct IEEE754 NaN payloads 7ff8000000000001 and7ff8000000000002 both normalize to {"$float_hex":"nan"} and identical encoded bytes. A finite float also aliases its caller-supplied tag mapping. These are pre-hash normalization collisions, not SHA attacks.', [('pfp/infrastructure/persistence/cemetery_sink.py',[[54,73]])], 'Narrow the guarantee to the declared normalized representation, or use an injective typed binary encoding if original float bits/type are required. Do not infer raw reconstruction from current tags.', '_isolated_encoding_probe.json')
finding('CATALOG-NEGATIVE-FIXTURE', 'fixture_semantics_gap', 'An entry labelled active for unterminated-string syntax stores negative fixture table = {\'Λ\': 1}, which Python AST parsing accepts. Replacing its Unicode key with Lambda does not demonstrate repair of that syntax failure. Other placeholder/comment/literal entries likewise need independent executable checker contracts before promotion. The paper already limits catalog labels to data.', [('code/fixtures/pharmacy_catalog_52cb5457f6c4.json',[]),('code/tests/test_006_catalog_file.py',[[101,115]])], 'Retain historical catalog as evidence; derive separately versioned runnable negative and valid near-miss cases before using any entry as a detector or repair rule.', '_test_results.json')
finding('TOOLCHAIN-AND-REBUILD', 'reproduction_maintenance_gap', 'README claims pytest8.3.5 pinned, but current pyproject and install examples require>=9.0.3. The shared rebuild_release tool also rescans/replaces current manifests and deletes older dated ZIPs, contrary to fixed-set-only prose; running its default path would conflict with intentional historical custody.', [('README.md',[[89,94]]),('pyproject.toml',[[14,20]]),('tools/rebuild_release.py',[[1,339]])], 'Name historical and current test environments separately; write new release outputs separately and preserve prior ZIPs. No rebuild or dependency installation was performed.')

test_results=load('_test_results.json');encoding_probe=load('_isolated_encoding_probe.json')
report={'schema_version':'1.0','status':'scope_dispositions_complete','source_commit':scope['source_commit'],'scope_manifest':'dag/reviews/'+P+'_scope.json','additional_dependency_scope':'dag/reviews/'+P+'_dependency_scope.json',
 'scope_summary':{'assigned_original_paths':43,'excluded_prior_full_manuscript':1,'assigned_full_source_bodies':32,'bounded_artifact_paths':11,'additional_full_dependency_bodies':3,'file_review_rows':46,'context_manuscript_lines':617,'pdf_files':7,'pdf_pages_including_duplicates':52,'unique_directly_viewed_pdf_pages':26,'zip_members':42,'zip_full_body_transfers':sum(r['full_source_read'] for r in zip_reviews)},
 'method':['Frozen original inventory exact paths/hashes before reading.','Full bodies of all32 ordinary assigned source/prose files; seven shared bases exact-byte equal to fully reviewed Paper004 bodies, and pyproject reviewed as complete base plus every diff.','Full617-line current manuscript read as context, not duplicated assigned coverage.','All26 unique PDF pages visually reviewed; four standalone PDFs transfer by every-page pixel equality and paper.pdf by raw equality.','All42 ZIP members have complete source/equality/delta or bounded artifact dispositions;16 full source/prose/receipt diffs manually read and two manifest deltas parsed across every record.','Catalog61 records/schema/semantic field sets reviewed; no full raw JSON reading claimed.','Three current dependency bodies read completely; namespace initializers and port implementation excluded from isolated storage execution.'],
 'file_reviews':sorted(reviews,key=lambda r:r['path']),'remaining_scope':[],
 'context_reads':[{'path':BASE+'paper.md','sha256':all_rows[BASE+'paper.md']['sha256'],'full_source_read':True,'reviewed_lines':[[1,617]],'assessment':'Complete manuscript reread; conditional storage argument, declared arithmetic, proposed reuse and unmeasured harness extension kept distinct.'}],
 'claims':claims,'findings':findings,'zip_member_reviews':zip_reviews,'custody_summary':{'current_manifest_results':manifest_stats,'historical_zip_manifests':custody['zip_manifests'],'catalog_comparison':custody['catalog_comparison']},
 'test_summary':{'current_pure_toy_passed':3,'current_catalog_setup_errors':3,'current_worksheet':'failed at snapshot SHA assertion','historical_copy_pure_passed':6,'historical_copy_worksheet':'passed','current_isolated_storage_passed':11,'current_isolated_storage_failed':0,'isolated_encoding_controls':2,'catalog_syntax_parse_controls':1,'receipt':'dag/reviews/'+P+'_test_results.json','encoding_receipt':'dag/reviews/'+P+'_isolated_encoding_probe.json','method_limit':'Current storage bodies loaded with empty namespace packages and object replacement of typing port; no ordinary production bootstrap or baseline replay. Archive-copy successes are separate fresh control executions, not the historical51-pass receipt.','native_builds':0,'provider_calls':0},
 'workflow_reuse':['Ordered normalized-record chain plus independently retained anchor under explicit custody.','Failure reproduction plus a scope-matched valid near miss before detector admission.','Distinguish proposed maintenance records from actual applied host action.','Fixed-parameter exact decay arithmetic and explicit trigger-population denominator.'],
 'limits':['Full-body source reading is distinct from formal proof, fresh ordinary integration and historical author-reported execution.','No provider/model/native build, private benchmark answer, credentials or network access.','Eleven artifacts remain bounded binary/data receipts and must not be promoted into full source reading.','Catalog data and archived fixtures are public historical evidence, not a new sealed benchmark or proof of detector effectiveness.','Historical harvesters, full original run corpus and external references were not comprehensively re-audited; no new literature or effectiveness claim.','All original production and historical bytes preserved; shared coverage/DAG/progress not modified.'],
 'provider_calls':0,'private_answer_access':False,'production_source_edits':0,'validation':['dag/reviews/'+P+'_final_validation.json']}

checks=[]
for row in scope['files']+scope['excluded_prior_full_reads']+deps:
 raw=(ROOT/row['path']).read_bytes();assert sha(raw)==row['sha256'],row['path'];checks.append({'path':row['path'],'sha256':row['sha256'],'unchanged':True})
for r in reviews:
 if r['full_source_read']:
  n=len((ROOT/r['path']).read_bytes().decode().splitlines());assert {i for a,b in r['reviewed_lines'] for i in range(a,b+1)}==set(range(1,n+1))
assert coverage[BASE+'paper.md']==set(range(1,618))
for x in claims+findings:
 for e in x['source_evidence']:
  raw=(ROOT/e['path']).read_bytes();assert sha(raw)==e['sha256']
  if e['lines']:
   n=len(raw.decode().splitlines());assert all(1<=a<=b<=n for a,b in e['lines']),e
assert len({x['id'] for x in claims+findings})==len(claims)+len(findings)
assert len(reviews)==46 and sum(r['full_source_read'] for r in reviews)==35
assert len(zip_reviews)==42
assert [r['exit_code'] for r in test_results['runs']]==[1,1,0,0,0]
assert encoding_probe['results']['same_encoded'] and encoding_probe['results']['finite_float_tag_alias']
write('.json',report)
md='''# Paper 006 support audit

All 43 assigned original paths have final dispositions: 32 full source/prose bodies and 11 bounded artifacts. The 617-line manuscript was fully reread as context, and three current storage dependencies were read in full. The report has 46 file-review rows; the three additional dependency rows are explicitly marked.

The useful contribution is a conditional retained-anchor argument and a disciplined transition from failure records to independently checked detector proposals. Fixed-tau decay and idealized rewrite cost are exact declared-input arithmetic. The paper appropriately withdraws immutable-retention, integrated-miner and detector-effectiveness claims.

Fresh checks separate current and archived inputs:

- Current pure suites: 3 toy passes, 3 catalog setup errors. Current worksheet fails its catalog SHA assertion.
- Five byte-identical selected historical ZIP members: 6 pure test passes and successful exact worksheet.
- Current fully read storage bodies under isolated namespace loading: 11 worked-example passes. This omits package initializers and replaces the typing port base with object; it is not ordinary production integration or historical-baseline replay.
- Two encoding counterexamples show lost NaN payload bits and an explicit-tag alias. A catalog negative syntax fixture parses as valid Python.

Catalog failure is entirely CRLF conversion: current raw f672aeb1… normalizes exactly to original LF b95ce7c1…. Preserve byte-exact historic data instead of changing the expected historical digest. Historical ZIP custody is internally valid; current loose manifests have 15/16 unresolved mismatches after LF normalization.

All seven PDFs (52 pages with duplicates) have visual coverage through 26 directly viewed unique pages plus exact pixel/byte transfers. No clipping was observed. All 42 ZIP members have explicit complete source-base/delta or bounded artifact dispositions. Catalog review covered all 61 parsed records and semantic fields; it is not full raw-JSON reading or detector execution.

## Findings

'''
for f in findings:md+=f"- **{f['id']}** — {f['statement']} Action: {f['recommended_action']}\n\n"
md+='''## Evidence limits

The JSON contains exact paths/hashes/ranges, 32 assigned full-body assessments, three additional dependency assessments, 11 bounded artifact dispositions, four bounded claims, seven findings and all 42 historical ZIP member dispositions. The first-publication 51-pass record remains historical; translated loose receipt strings are not untouched historical bytes. PDF/TeX/Markdown namespaces identify different retained versions and must not be silently interchanged.

Final validation checks all 44 original package hashes plus three dependency hashes, reading ranges, evidence ranges, report identifiers and expected test outcomes. No original source edits, provider calls, native builds, credentials, sealed benchmark or private answer access occurred. Shared coverage/DAG/progress files were not changed.
'''
(HERE/(P+'.md')).write_text(md,encoding='utf-8')
validation={'status':'pass','assigned_paths':43,'assigned_full_body_receipts':32,'bounded_artifact_receipts':11,'context_manuscripts':1,'additional_dependency_full_bodies':3,'total_original_hashes_unchanged':47,'zip_member_dispositions':42,'zip_full_body_transfers':sum(x['full_source_read'] for x in zip_reviews),'source_evidence_ranges_validated':True,'duplicate_claim_finding_ids':[],'original_files':checks,'report_sha256':sha((HERE/(P+'.json')).read_bytes()),'markdown_sha256':sha((HERE/(P+'.md')).read_bytes()),'scope_sha256':sha((HERE/(P+'_scope.json')).read_bytes()),'test_outcomes_expected_and_recorded':True,'limit':'Metadata validation is not additional semantic reading or execution.'}
write('_final_validation.json',validation)
print(json.dumps({k:v for k,v in validation.items() if k!='original_files'},indent=2))
