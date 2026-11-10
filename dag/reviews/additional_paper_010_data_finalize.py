"""Publish all completed Paper010 data-body receipts; no parent report/source edits."""
import hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_010_data';B='papers/pfp/010_pfp_holonomy_checks_and_model_pilots/'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def load(suffix):return json.loads((H/(P+suffix)).read_text(encoding='utf-8'))
def save(suffix,value):(H/(P+suffix)).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
scope=load('_scope.json');checks=load('_checks.json');ledger=load('_read_ledger.json');notes=load('_notes.json');notes.update(load('_notes_final.json'));notes.pop('_checkpoint_note',None)
coverage={}
for row in ledger:
 assert sha((R/row['path']).read_bytes())==row['sha256'] and not row['output_truncated']
 coverage.setdefault(row['path'],set()).update(i for a,b in row['reviewed_lines'] for i in range(a,b+1))
reviews=[]
for row in scope['files']:
 raw=(R/row['path']).read_bytes();assert sha(raw)==row['sha256'] and len(raw.decode('utf-8').splitlines())==row['lines']
 assert coverage[row['path']]==set(range(1,row['lines']+1))
 name=row['path'][len(B):];assessment=notes[name]
 assessment=re.sub(r'\b(All|Complete)(\d+)', r'\1 \2', assessment)
 reviews.append({'path':row['path'],'sha256':row['sha256'],'full_source_read':True,'reviewed_lines':[[1,row['lines']]],
                 'review_level':'complete_raw_source_body_and_semantic_review', 'assessment':assessment,
                 'reading_receipt':'dag/reviews/'+P+'_read_ledger.json',
                 'limits':'Full reading of retained content, including complete stored strings, does not reconstruct omitted historical inputs/replies or authenticate execution.'})
assert len(reviews)==len(notes)==27
def evidence(name,*ranges):return {'path':B+name,'sha256':sha((R/(B+name)).read_bytes()),'lines':[list(pair) for pair in ranges]}
def entry(id,statement,sources,**kw):return {'id':'PAPER010-DATA-'+id,'statement':statement,'source_evidence':sources,'evidence':[x['path'] for x in sources],**kw}
claims=[
 entry('FINITE-GROUP-AND-LATTICE-ADMISSION',
  'The five supplied fixtures admit their declared finite group tables: closure, identity, inverses and every associativity triple pass independent finite checks. All 302 directed edges are exactly the declared open/periodic rectangular neighbours and carry inverse reverse labels. The pois_01 internal name inv_mismatch does not describe an actual inverse mismatch in these retained bytes.',
  [evidence('code/data/c017/base_01.json',(1,113)),evidence('code/data/c017/base_02.json',(1,141)),evidence('code/data/c017/base_03.json',(1,199)),evidence('code/data/c017/base_13.json',(1,177)),evidence('code/data/c017/pois_01.json',(1,103))],
  status='full_body_review_and_fresh_exact_finite_data_reductions',limits='Five public fixtures, 1,376 associativity triples counting each supplied table; not arbitrary input admission or production-checker soundness.'),
 entry('LOCAL-VERSUS-GLOBAL-HOLONOMY',
  'All 64 canonical plaquette products were independently calculated. base_02 has 12 identity products and a globally consistent potential. base_03 has 30 identity products but seam cycles r and r2, so no global potential trivializes every link; the two cycle products commute. Each remaining fixture has one nonidentity plaquette. This supplies finite positive and negative controls distinguishing local flatness from global triviality.',
  [evidence('code/data/c017/base_02.json',(77,140)),evidence('code/data/c017/base_03.json',(77,198)),evidence('code/data/c017/pois_01.json',(77,102)),evidence('code/data/c017/base_01.json',(77,112)),evidence('code/data/c017/base_13.json',(113,176))],
  status='full_body_review_and_fresh_exact_finite_data_reductions',limits='Ordered multiplication under explicit orientation and supplied finite group tables. No physical gauge interpretation or infinite/general torus classification proved here.'),
 entry('EXTRACTION-AND-DESCRIPTIVE-RECOUNT',
  'All 25 extracted C017 entries match their retained source records on verdict, expected verdict, pass flag, reason, tokens and retained certificate fields. All 240 C045-C050 model-case rows recount to their stored panel totals, treating the single C045 JSON_ERROR without a pass flag as nonacceptance. Six baseline identifier partitions/counts are internally consistent.',
  [evidence('code/data/c017/model_claims.json',(1,462)),evidence('docs/historical_evidence/formal_math_baselines.json',(1,597)),evidence('docs/v01_review_2026_10_02.json',(74,82),(149,159))],
  status='complete_raw_record_review_and_fresh_all_record_comparisons',limits='Exact data consistency only; historical acceptance, category annotations and provider identity are not independently validated mathematical/model outcomes.')]
findings=[
 entry('PURE-GAUGE-SCRATCHPAD-ERRORS',
  'The three later base_02 false NOT_FLAT claims have different exact defects. Arm5 70B records sr2*s=r, but the table gives r2 and the final product e. Arm5 SBA replaces edge 2,3->1,3=s with sr, so it computes a changed input. Arm6 SBA records r*sr=s, but the table gives sr2 and final product e. A classification failure can therefore reflect arithmetic or instance-binding errors even when a scratchpad appears explicit.',
  [evidence('code/data/c017/base_02.json',(27,33),(59,65),(104,111)),evidence('docs/historical_evidence/arm5_hybrid_report.json',(217,259)),evidence('docs/historical_evidence/arm5_stealth_space_bunny_alpha_report.json',(435,475)),evidence('docs/historical_evidence/arm6_stealth_space_bunny_alpha_report.json',(243,264))],
  severity='exact_retained_counterexamples',recommended_action='Reuse these three error classes as public checker controls with new independently encoded tasks. Verify edge binding and every ordered multiplication; do not treat scratchpad length as correctness or reuse these known answers as a sealed benchmark.'),
 entry('ASSISTANCE-AND-MISSING-PAYLOADS',
  'Recorded C017 acceptance counts are 0/5,0/5,3/5,3/5,4/5. The first two arms retain no actual certificate payloads; later arms add canonical paths, step rules and, in arm6, harness-listed active plaquettes/cycle paths. Two later torus attempts retain PARSE_ERROR and only incomplete raw prefixes. These records cannot isolate causal prompt/learning effects, reconstruct all attempts or establish unaided capability.',
  [evidence('code/data/c017/model_claims.json',(1,22),(66,84),(129,156),(233,260),(337,364)),evidence('docs/historical_evidence/arm5_hybrid_report.json',(262,287)),evidence('docs/historical_evidence/arm5_stealth_space_bunny_alpha_report.json',(478,503))],
  severity='historical_empirical_scope_limit',recommended_action='Keep assistance, missingness, parse failure and certificate acceptance as separate fields; design any future comparison with independently selected cases, fixed assistance and retained complete execution inputs.'),
 entry('CHECKER-LABEL-AND-BASELINE-CEILING',
  'The stored baseline record reports best trivial dual-acceptance counts 10,10,0,3,2,1 for C045-C050. C045/C046 refuse-all policies reportedly pass all ten, and several independent branches accept empty or false nonexistence answers while the exact branch rejects. Identifier partitions are author annotations and several names encode suggested answers. These observations limit the meaning of historical model pass rates; they are not fresh executions of those external checkers.',
  [evidence('docs/historical_evidence/formal_math_baselines.json',(29,123),(145,257),(281,342),(366,435),(459,519),(543,594)),evidence('docs/historical_evidence/c045.json',(38,50)),evidence('docs/historical_evidence/c049_panel_a_0.json',(66,102))],
  severity='historical_checker_adequacy_and_task_binding_limit',recommended_action='Keep the dated constant-answer controls and source commits. Before workflow reuse, audit actual owner predicates, admission and refusal witnesses on new data; two checker labels are not a proof of semantic adequacy or statistical independence.'),
 entry('CURRENT-DATA-CUSTODY',
  'None of the 15 retained report/baseline files matches the current raw SHA/Git identity in provenance. Fourteen match both after LF normalization; formal_math_baselines still differs. All five case fixtures match their explicitly declared CRLF hashes and match the separate LF hashes after normalization. The dual LF/CRLF fixture convention is explicit, but the historical report byte-copy claim is false for the current raw files.',
  [evidence('docs/historical_evidence/README.md',(3,7)),evidence('docs/historical_evidence/provenance.json',(1,111)),evidence('code/data/c017/provenance.json',(1,45))],
  severity='edition_identity_mismatch',recommended_action='Preserve archived originals and use a separately versioned current adaptation map. Parent owns archive/delta validation. Normalized equality is diagnostic; do not silently replace historical raw identities or claim exact bytes from normalized hashes.'),
 entry('PANELS-RUNS-AND-RECEIPTS-ARE-DIFFERENT-SCOPES',
  'C049 panels A and B contain different cases and omit different payloads; their counts are not a repeated same-panel comparison. C050 runs retain distinct 7/4/1 and 6/3/1 totals. The three release receipts record older 21-test, selected 13-test, and later 42-test scopes; the v0.1 review explicitly did not execute pinned Lean or the historical C045-C050 checkers. Its complete embedded outputs are historical evidence, not current execution.',
  [evidence('docs/historical_evidence/c049_panel_a_2.json',(1,154)),evidence('docs/historical_evidence/c049_panel_b.json',(1,188)),evidence('docs/historical_evidence/c050_run_1.json',(1,188)),evidence('docs/historical_evidence/c050_run_2.json',(1,188)),evidence('docs/release_validation_2026_10_01.json',(8,38)),evidence('docs/release_validation_2026_10_02.json',(30,64)),evidence('docs/v01_review_2026_10_02.json',(19,31),(161,173))],
  severity='nonexchangeable_evidence_scopes',recommended_action='Keep per-panel cases, per-run outcomes, and source-bound historical versus current validation separate. No cherry-picked aggregate or automatic formal/model capability transfer.')]
for item in claims+findings:
 for source in item['source_evidence']:
  raw=(R/source['path']).read_bytes();assert sha(raw)==source['sha256']
  for a,b in source['lines']:assert 1<=a<=b<=len(raw.decode('utf-8').splitlines())
report={'schema_version':'1.0','source_commit':scope['source_commit'],'status':'complete_full_body_review_of_declared_27_path_data_slice',
 'scope_manifest':'dag/reviews/'+P+'_scope.json','scope_summary':{'assigned_paths':27,'full_source_bodies':27,'source_lines':6953,'bytes':236225,'bounded_only_files':0,
 'stored_formal_pilot_case_records':240,'extracted_c017_entries':25,'historical_release_receipts':3},
 'file_reviews':reviews,'claims':claims,'findings':findings,'remaining_scope':[],
 'fresh_checks':{'receipt':'dag/reviews/'+P+'_checks.json','mechanism':'Independent stdlib JSON arithmetic, hashes, extraction comparisons and recounts; no imported original modules or checkers executed.',
 'finite_fixture_edges':302,'finite_fixture_plaquettes':64,'group_associativity_triples':1376,'originals_unchanged':27},
 'archive_boundary':'Parent owns Paper010 ZIP/PDF/test audit and already read all archive differences. This report grants current27-body coverage only; any archive transfer must bind the parent member/delta evidence explicitly.',
 'workflow_reuse':[{'mechanism':'Ordered finite-group path products and local/global consistency controls','prerequisites':'Closed lawful group table, full carrier/edge admission, orientation/instance binding and a justified target encoding; QM transfer needs its own physical/operational mapping.'},
 {'mechanism':'Certificate extraction/recount with missingness and constant-answer controls','prerequisites':'Independent checker adequacy and new task labels; stored expected verdicts or public worked answers cannot become sealed benchmark inputs.'}],
 'limits':['Every assigned source body was read losslessly, including all complete stored raw strings; sources themselves may omit/truncate historical responses and input cases.',
 'No new provider trial, secret, private benchmark, native build, historical checker execution, package pytest or external publication lookup occurred in this data slice.',
 'Parent tests/archives remain separate evidence; current report does not upgrade any retained historical pass flag into a freshly verified outcome.',
 'All original source/data bytes are unchanged. Only additional_paper_010_data-prefixed reports/helpers were written.'],
 'provider_calls':0,'private_answer_access':False,'production_source_edits':False,
 'validation':{'all_27_frozen_sha256_unchanged':True,'all_6953_source_lines_covered_by_complete_outputs':True,'all_source_ranges_valid':True,'all_per_path_assessments_present':True}}
save('.json',report)
md=['# Paper010 data and historical-evidence review','',
 '**All 27 assigned files were read in full:** 6,953 raw source lines, 236,225 bytes. Every stored scratchpad, raw prefix, certificate field and embedded release output was inspected. All original hashes remain unchanged. No source body receives parse-only credit.','',
 'Fresh independent finite reductions confirm all five group/lattice fixtures, all 302 directed edges and 64 plaquette products. They distinguish the pure-gauge open fixture from the locally flat torus with nontrivial cycles. All 25 C017 extractions and 240 formal-pilot records reconcile internally; these are checks on data, not new model observations.','']
for item in findings:md.extend([f"- **{item['id']}:** {item['statement']} {item['recommended_action']}",''])
md.extend(['The JSON contains each exact source hash/range and substantive assessment, three scoped claims, five findings and the fresh finite-check receipt. Parent owns the surrounding code, tests, PDF and archive review. No providers, native builds, private benchmark or original edits were used.',''])
(H/(P+'.md')).write_text('\n'.join(md),encoding='utf-8')
save('_final_validation.json',{'report_sha256':sha((H/(P+'.json')).read_bytes()),'markdown_sha256':sha((H/(P+'.md')).read_bytes()),
 'scope_sha256':sha((H/(P+'_scope.json')).read_bytes()),'paths':27,'full_source_bodies':27,'source_lines':6953,'originals_unchanged':27,
 'claims':len(claims),'findings':len(findings),'checks':report['validation']})
print(json.dumps({'complete':True,'paths':27,'source_lines':6953,'report_sha256':sha((H/(P+'.json')).read_bytes())},indent=2))
