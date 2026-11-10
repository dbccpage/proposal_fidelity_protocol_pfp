"""Persist only completed, source-bound field-manual readings."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews'
PREFIX = 'papers/pfp/005_pfp_practitioners_field_manual/'
scope = json.loads((OUT/'additional_paper_005_support_scope.json').read_text())
pins = {x['path']: x for x in scope['files']}
assessments = {
    'README.md': 'Complete package instructions read, including the portion reread after output truncation. Current source, historical deposit and optional native execution are separate; claimed publication differs from manuscript wording and was not externally confirmed.',
    'paper_claim_ledger.md': 'Entire claim ledger read. Quotient obstruction and section defect differ; replacement changes the asserted instance, and graph-labelled examples do not prove their advertised domain problems.',
    'pyproject.toml': 'Complete dependency and pytest configuration read. No dependency installation performed.',
    'code/native_functional.py': 'Entire native selector, digest check, request guard and response decoder read. Explicit binary selection and thirty-second timeout; exact finite rational types and structural output conditions are checked, but optimality and executable/source correspondence are trusted. No native execution in this review.',
    'code/play_demo.py': 'Complete demonstration read. Uses the streaming wrapper and reports example statuses; this is a deterministic supplied-proposal fixture, not a measured model comparison.',
    'code/study_capstone.py': 'Complete worksheet script read. Public teaching examples are separate from the sealed benchmark and do not establish learner or model performance.',
    'code/l1_symbol_game_governor.py': 'All 917 lines read in four complete ranges. Exact rational weighted graph-coboundary minimization enumerates spanning trees per component, with a zero candidate. Gauge cuts and claim replacement have different semantics; ASSERT/RETRACT need not reduce obstruction. Mutable state, duplicate snapshot IDs and inconsistent input-type guards limit the public protocol boundary.',
    'code/llm_streaming_harness.py': 'Entire streaming parser, provider adapter, session initialization/execution and receipt writer read. Conflicting edge spellings overwrite; duplicate JSON keys and unbound schema/parent fields are accepted. Initial values are fraction-converted before exact input guards, and initialization ignores refused ASSERT outcomes. Provider transport has no whole-run monetary reservation and drops usage.',
    'code/quickstart.py': 'Complete quickstart read in two ranges. Exact finite demonstration and optional native adapter are useful, but a printed invariant violation does not prevent the final certified label or successful exit.',
    'code/multi_domain_symbol_game_bouts.py': 'All four labelled graph fixtures, linear hash chain, trace predicate, hypothetical baseline estimates and receipt assembly read. No MUB vectors, AST parser, lock transition semantics or market data are checked. Antibody counts and some intermediate metrics are literal labels; graph edges stay fixed while claims are replaced. This is a useful graph exercise, not empirical domain performance.',
    'code/symbol_game_toolkit.py': 'Complete scaffold and terminal loop read. Eight prompt surfaces and named refusal codes are text, not implemented enforcement. Projection replacement changes claims to a coboundary; zero is therefore expected if admitted. A cut-count limit can produce SURVIVOR_OBSTRUCTION without an irreducibility proof. ASSERT refusals are logged but do not prevent an overall zero terminal.',
    'code/tests/conftest.py': 'Entire import and optional native fixture setup read. Native-dependent tests may be deliberately skipped; their absence is not a current native failure.',
    'code/tests/test_harness_exact_inputs.py': 'Every exact-input parser regression read. Coverage does not include all alias, duplicate-key or initialization coercion cases reproduced by this review.',
    'code/tests/test_manual_contracts.py': 'Complete contract tests read. They establish bounded exact arithmetic and declared guard cases, not semantic authentication or general workflow improvement.',
    'code/tests/test_llm_streaming_harness.py': 'Complete scripted envelope and streaming tests read. Mock proposals are not model samples; top-level receipt assertions alone do not test failure propagation.',
    'code/tests/test_cut_completeness.py': 'Complete finite cut-domain tests read. Missing/unknown claims and exact-domain refusal coverage is distinct from streaming normalization before the governor.',
    'code/tests/test_native_refusal_propagation.py': 'Every mocked native-error propagation test read. Configured native failures are not silently replaced by Python; these are adapter controls, not native execution.',
    'code/tests/test_offline_worksheet.py': 'Complete exact public worksheet tests read. Finite expected values agree with the weighted cycle example; no sealed benchmark content accessed.',
    'code/tests/test_play_demo.py': 'Complete deterministic demo assertions read. Tests use public scripted moves and optional native fixture.',
    'code/tests/test_quickstart_native.py': 'Complete optional native quickstart check read. No source-to-binary proof or independently verified optimality follows.',
    'code/tests/test_cross_domain_bouts.py': 'All six tests read. Check four supplied graph outcomes and chain continuity, but do not independently replay traces or authenticate the associated domain interpretations.',
    'code/tests/test_symbol_game_toolkit.py': 'All three tests read. Scaffold string presence and two finite terminal cases are useful regressions, not enforcement of every declared surface or proof of irreducibility.',
}
assessments.update({
    'paper.tex':'Entire TeX read in two complete ranges through end-document. Matches the historical instructional edition, with later source/role renaming but without the newer Markdown extension. Lower-bound proof and fixed-instance/replacement distinction are sound; historical build instructions need versioned path guidance.',
    'code/paper_033_execution_receipt.json':'Every field, both scenarios and summary read. Five supplied proposal outcomes and two zero terminals are a historical scripted receipt, not a live model comparison or independent verifier. Its stored self-digest needs rechecking after schema renaming.',
    'code/cross_domain_symbol_game_receipt.json':'All four metrics, all29 move records, eight cemetery records and totals read. Baselines are expressly hypothetical; labels such as UNCONSTRAINED_LLM are scripted roles. Deadlock intermediate/cost literals are not executed measurements; chain links and digests do not establish domain validity.',
    'docs/release_validation_2026_10_01.json':'All twelve named test records, commands, source/native hashes and all repeated stdout values read through a lossless25-line pool with complete order sequences. Historical75-pass evidence is distinct from this review\'s unconfigured-native results.',
    'docs/release_validation_2026_10_02.json':'Every field,28 selected input hashes, two worksheet passes, candidate assets and render command read. Broad schema mentions do not upgrade this selected offline run to a full-suite, native or Lean execution.',
    'docs/publication_review_2026_10_02.json':'All98 test case records, source comparisons,52 bound files, rendering commands, limits and complete stdout/stderr read. Seven multi-line strings reconstruct exactly from136 unique log lines and their full order. Historical64-pass34-skip record is distinct from fresh62-pass34-skip2-deselected evidence. Captured compiler path substitutions require archival comparison.',
    'MANIFEST.sha256':'All58 checksum/path bindings read. Hash custody is separate from mathematical assessment; current and archive bindings checked separately.',
    'SHA256SUMS':'All59 checksum/path bindings read, including MANIFEST binding. Current remapped paths and original archived paths are distinct editions.',
    'paper_change_log.md':'Entire dated history read, from current publication and review through earlier fixes and later author-review extension. Historical scope withdrawals are explicit. Later custody claims remain to be checked against archive bytes; a revised description does not supply new execution.',
    'tools/render_paper.py':'Complete renderer read. Extracts manuscript body after title div, emits TeX through pandoc, runs XeLaTeX twice with sixty-second timeouts, and rejects named layout warnings before copying a PDF. Reproduction records are rendering evidence, not mathematical validation. Not executed because historical source outputs are preserved.',
    'code/symbol_game_matolcsi_conjecture2.py':'Complete graph fixture, hardcoded danger, cemetery records and printed antibody narrative read. Explicitly no polynomial evaluation, but actual Python execution accepts the supposed bogus zeroing nine to zero while the cemetery records refusal. The printed antibody has no implemented pre-call gate.',
    'code/symbol_game_r4_playground.py':'Entire playground read. Candidate text and evaluated inflated claims differ; labelled edges do not evaluate analytic inequalities. Actual last replacement leaves quotient four and VERIFY refuses, yet the cemetery stores accepted terminal and zero danger. No edge deletion or R4 theorem occurs.',
    'code/tests/test_symbol_game_matolcsi_conjecture2.py':'All four tests read. They check finite graph size, supplied trigger and alphabet membership, final fixture values and digest length; they miss disagreement between actual intermediate verdict and recorded refusal.',
    'code/tests/test_adversarial_challenges.py':'All source read, including complete rereads of truncated ranges. Exact finite graph, parser, rollback, digest and loopback HTTP tests inspected. Many require explicitly configured native execution. HTTP exception test can pass for local socket denial rather than its intended 401 response.',
    'code/tests/test_vendored_sources.py':'Complete header, Git blob and normalized-AST comparisons read. Optional source objects may be absent; patched functions/methods are excluded from structural equality and need behavioral evidence. Hash/header or string-presence checks are not semantic proofs.',
    'code/tests/__init__.py':'Entire one-line test package marker read.',
    'docs/descriptions.md':'Complete abstract read. Correctly limits contribution to instructional graph session, disclaims new theorem and empirical study. No-deposit wording conflicts with DOI fields elsewhere.',
    'docs/keywords.md':'All eight metadata terms read. Bounded turn fuel is a teaching policy, not implemented enforcement in this package.',
    'docs/references.md':'All three citations and source-copy provenance paragraph read. Primary bibliographic records checked separately; external full proofs not audited.',
    'zenodo_metadata.json':'Every field and full HTML abstract read. Description says no external deposit or DOI, while DOI, record URL, concept DOI and notes claim publication. This is an internal version/status inconsistency, not proof of nonpublication.',
    '_lev_examiner_theoretical_minimum_quiz/.gitkeep':'Verified zero-byte placeholder; no mathematical content.',
    '_lev_examiner_theoretical_minimum_quiz/00_preface_at_apartment_50.md':'Complete fictional teaching frame read. Disclaims authority; source_paths retains an obsolete atlas location.',
    '_lev_examiner_theoretical_minimum_quiz/quiz.md':'All 32 questions, eight levels and grading gates read. Useful distinctions between fixed-instance proof, exact input, scope, execution and custody. Rubric explicitly unvalidated; UNKNOWN and attempt bound are exercise policies.',
    '_lev_examiner_theoretical_minimum_quiz/study_guide.md':'Complete public worked key read, with truncated beginning reread. Triangle lower/upper bounds, orientation reversal, constant gauge freedom, stationary replacement, distinct verification obligations and infinite rational descent are correct. Float/Boolean refusal describes proposal parsing and does not cover initializer coercion.',
    'docs/publication_review_2026_10_02.md':'Complete historical review and twelve corrected findings read. Source-copy normalization excludes patched bodies and requires separate regression coverage. Historical receipt byte-preservation assertions need archive checks; fresh current native replay remains explicitly open.',
})
reviews = []
for rel, assessment in assessments.items():
    path = PREFIX + rel
    data = (ROOT/path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == pins[path]['sha256'], path
    n = len(data.decode('utf-8-sig').splitlines())
    reviews.append({'path':path,'sha256':pins[path]['sha256'],'full_source_read':True,
        'reviewed_lines':[[1,n]] if n else [],'assessment':assessment})
shared = json.loads((OUT/'paper_005_support_inspection/shared_source_comparisons.json').read_text())
for item in shared:
    assert item['byte_equal'] and not item['full_text_delta']
    data = (ROOT/item['path']).read_bytes()
    assert data == (ROOT/item['base_path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == pins[item['path']]['sha256']
    reviews.append({'path':item['path'],'sha256':item['sha256'],'full_source_read':True,
        'reviewed_lines':[[1,len(data.decode('utf-8-sig').splitlines())]],
        'base_path':item['base_path'],'base_review':item['base_report'],
        'review_method':'Complete previously reviewed source plus exact byte equality; base assessment reread in this package context.',
        'assessment':'Identical license or custody/release implementation to the completed Paper003 review. It supplies file/deposit handling, not mathematical proof or fresh execution.'})
render = json.loads((OUT/'paper_005_support_inspection/render_receipt.json').read_text())
assert sum(len(x['pages']) for x in render['renders']) == 40
assert len(render['standalone_correspondence']) == 20
assert all(x['complete_pixel_matches'] for x in render['standalone_correspondence'])
for item in render['renders']:
    path = item['pdf']
    assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest() == pins[path]['sha256']
    reviews.append({'path':path,'sha256':pins[path]['sha256'],'full_source_read':True,
        'reviewed_lines':[],'reviewed_pages':[[1,len(item['pages'])]],
        'review_method':'All8 main and12 companion pages visually read across5 complete sheets; capstone table additionally inspected at original page scale. Remaining20 pages transfer by complete pixel equality.',
        'assessment':'Historical graph tutorial and32-question teaching companion are readable with no obstructive overlap observed. Historical names, environment variables and paths differ from current renamed sources; the PDFs do not include the later author-review extension. Preserve original bytes.',
        'validation':'dag/reviews/paper_005_support_inspection/render_receipt.json'})
archive = json.loads((OUT/'additional_paper_005_archive_checks.json').read_text())
review_index = {x['path']:x for x in reviews}
archive_dispositions = []
for item in archive['members']:
    assert item['current_path'] == PREFIX+'paper.md' or review_index[item['current_path']]['full_source_read']
    archive_dispositions.append({**item,
        'assessment':'Complete current base plus every unique exact replacement rule and all member-to-rule mappings reviewed; numeric title changes additionally read in full context. All28 changed text members reconstruct exactly. Equality transfers remaining32 members, including6 visually reviewed PDFs. No archive execution claimed.'})
assert len(archive_dispositions) == 60 and len(archive['rules']) == 135
reviews.append({'path':archive['archive'],'sha256':archive['archive_sha256'],'full_source_read':True,
    'reviewed_lines':[],'reviewed_archive_members':60,
    'review_method':'Full current bases; all135 exact replacement rules and complete60-member mapping read; all28 changed text members exactly reconstructed;32 equality transfers. Numerical title deltas inspected in context.',
    'assessment':'Historical archive preserves original role/module/environment names, original receipt digest and earlier0.1.0 manuscript. Later0.2.0 extension is absent by design. All117 embedded manifest bindings and9 receipt/chain hashes pass. This is logical-content review, not authentication of historical execution.',
    'validation':'dag/reviews/additional_paper_005_archive_checks.json'})
done = {x['path'] for x in reviews}
assert done == set(pins) and len(reviews) == len(pins)
findings = [
    ('INPUT-NORMALIZATION','input_refusal_gap','The streaming wrapper fraction-converts initial float/Boolean values, silently overwrites conflicting spellings of the same edge, and accepts repeated JSON keys with last-value semantics. These transformations occur before the stricter governor guard.', ['code/llm_streaming_harness.py']),
    ('UNBOUND-ENVELOPE','protocol_binding_gap','A CUT with unrelated schema, nonexistent parent and invented expected delta is admitted when its normalized claims pass. The wrapper does not implement the scaffold\'s chain/surface contract.', ['code/llm_streaming_harness.py','code/symbol_game_toolkit.py']),
    ('IGNORED-INITIAL-REFUSAL','execution_evidence_gap','Initialization appends an ASSERT-shaped trace row for an undeclared edge while discarding the refused verdict. The empty admitted state then has zero obstruction.', ['code/llm_streaming_harness.py']),
    ('WEIGHT-GUARD-PATH','input_domain_gap','Graph construction permits Boolean/float weights and section operations coerce them, while primary minimization rejects these types. The same declared graph can pass earlier paths and fail later evaluation.', ['code/l1_symbol_game_governor.py']),
    ('DUPLICATE-SNAPSHOT-ID','state_binding_gap','Two assertions can reuse a snapshot ID; retracting that ID selects the earlier snapshot. IDs do not uniquely identify a public history state.', ['code/l1_symbol_game_governor.py']),
    ('HARDCODED-RECEIPT-SUCCESS','execution_evidence_gap','With in-memory run_turn replaced by refused verification outcomes, receipt summary still says PASS_ALL_INVARIANTS and retains terminal success labels. This reproduces a summary-construction defect, not an actual provider/native failure.', ['code/llm_streaming_harness.py']),
    ('QUICKSTART-CERTIFIED-AFTER-VIOLATION','execution_evidence_gap','An injected inconsistent second projection makes the quickstart print VIOLATED while still printing CERTIFIED_EXACT_RATIONAL and exiting zero. Certification status must depend on checks.', ['code/quickstart.py']),
    ('LIVE-ACCOUNTING','benchmark_admission_gap','The live adapter has no output-token cap or whole-run monetary reservation, discards usage, and ignores an empty SSE delta carrying finish_reason length. In-memory URL stubs reproduced this without network or credentials.', ['code/llm_streaming_harness.py']),
    ('DOMAIN-LABELS','scope_overclaim','Four labelled bouts prove only facts about supplied finite graph cochains. They do not implement MUB, lock, AST or market semantics; baseline costs are explicitly hypothetical and antibody counts are hardcoded. Preserve the finite exercise and exclude these labels from measured efficacy.', ['code/multi_domain_symbol_game_bouts.py']),
    ('DEADLOCK-COST-AND-INTERMEDIATE','metric_binding_gap','The deadlock fixture records candidate cost one and intermediate obstruction one, but replacing the weight-one claim from one to minus three costs four in the stated weighted L1 metric. The intermediate one is a literal, not an executed state measurement.', ['code/multi_domain_symbol_game_bouts.py']),
    ('TERMINAL-IRREDUCIBILITY','claim_scope_gap','Toolkit SURVIVOR_OBSTRUCTION can result from max_cuts zero or a refusal and does not certify irreducibility. Its projection replacement repairs the graph instance by changing claims; it does not solve the original fixed assertions.', ['code/symbol_game_toolkit.py']),
    ('MATOLCSI-REFUSAL-CONTRADICTS-VERDICT','execution_evidence_gap','Actual Python execution admits the alleged bogus zeroing and reduces quotient nine to zero, yet the cemetery records REFUSED_OBSTRUCTION_TAO_WITNESS and prints a minted pre-call antibody. The graph checker does not enforce the alleged immutable polynomial witness.', ['code/symbol_game_matolcsi_conjecture2.py']),
    ('R4-FALSE-ZERO-TERMINAL','execution_evidence_gap','Actual Python execution ends at quotient four and fails ZERO_OBSTRUCTION, but the cemetery records ACCEPTED_TERMINAL with zero danger and says the graph was repaired to zero. The displayed candidate text also differs from the claim map evaluated in the earlier refusal.', ['code/symbol_game_r4_playground.py']),
    ('VACUOUS-TRACE-VALIDATION','replay_gap','validate_bout_trace accepts an empty trace and an unknown move under an invented domain ID. It imposes no required sequence or completeness and is not an independent trace verifier.', ['code/multi_domain_symbol_game_bouts.py']),
    ('PUBLICATION-STATUS-INCONSISTENCY','metadata_gap','The metadata abstract says no external deposit or DOI is claimed, while the same JSON supplies DOI/record fields and notes saying published October 3. Preserve historical versions and state which status belongs to which edition; endpoint inaccessibility alone proves nothing about publication.', ['zenodo_metadata.json','docs/descriptions.md','README.md']),
    ('CURRENT-MANIFEST-DRIFT','custody_gap','Current MANIFEST.sha256 has34 raw mismatches and31 after LF normalization; SHA256SUMS has35 raw and32 after LF normalization. All58/59 original archive bindings pass. Do not describe current working manifests as valid custody of this renamed/revised package.', ['MANIFEST.sha256','SHA256SUMS']),
    ('EDITED-HISTORICAL-RECEIPT-DIGEST','provenance_gap','Changing the historical execution receipt schema from omega to core left its stored self-digest unchanged. The archived payload verifies; the current payload does not. The cross-domain receipt is LF-equivalent to its archive and all eight entry hashes still verify. Preserve the original and label a renamed copy as a derived transcription.', ['code/paper_033_execution_receipt.json','code/cross_domain_symbol_game_receipt.json']),
    ('HISTORICAL-RECORD-AND-PIN-RENAMING','version_binding_gap','The current publication-review JSON and October2 release-validation JSON contain later path/environment/role substitutions, including captured compiler output and bound-file key names. Current source headers and commit-pinned instructions also rename historical locations. Archive originals remain intact; unchanged dates and commit IDs do not make renamed transcriptions original execution bytes. The October1 validation record differs only by line endings.', ['docs/publication_review_2026_10_02.json','docs/release_validation_2026_10_02.json','docs/release_validation_2026_10_01.json','code/l1_symbol_game_governor.py','paper.tex']),
    ('AUTHOR-REVIEW-LINK-DRIFT','navigation_gap','The later Markdown extension links to ../029_pfp_evidence_bound_harness_evolution even though the current collection uses019. Historical0.1.0 PDFs and archive intentionally omit that0.2.0 extension; they should not be represented as renderings of the current Markdown.', ['paper.md','README.md','paper_change_log.md']),
]
report = {
    'schema_version':'1.0','status':'scope_complete','source_commit':scope['source_commit'],
    'scope_manifest':'dag/reviews/additional_paper_005_support_scope.json',
    'file_reviews':sorted(reviews,key=lambda x:x['path']),
    'remaining_scope':[x for x in scope['files'] if x['path'] not in done],
    'archive_member_dispositions':archive_dispositions,
    'contextual_reads':[{'path':PREFIX+'paper.md','full_source_read':True,
        'sha256':hashlib.sha256((ROOT/(PREFIX+'paper.md')).read_bytes()).hexdigest(),
        'assessment':'All 270 lines reread, including previously truncated middle range. Primary manuscript was already credited in the initial paper review and is excluded from this 61-file support scope.'}],
    'claims':[
        {'id':'PAPER005-WEIGHTED-COBOUNDARY-DISTANCE','statement':'On a fixed finite rational graph with positive weights, Phi1 is weighted L1 distance of edge claims from graph coboundaries. The example triangle has quotient minimum three; a gauge change preserves its oriented cycle sum.','status':'complete_prose_and_implementation_read','evidence':[PREFIX+'paper.md',PREFIX+'code/l1_symbol_game_governor.py'],'limits':'Conditional finite graph mathematics; enumeration can be combinatorial. No domain-adapter or model-efficacy result.'},
        {'id':'PAPER005-INSTANCE-REPLACEMENT','statement':'Replacing edge claims by a computed coboundary makes their quotient obstruction zero. Gauge-changing a section alone cannot remove a nonzero cycle obstruction.','status':'complete_prose_and_implementation_read','evidence':[PREFIX+'paper.md',PREFIX+'code/symbol_game_toolkit.py'],'limits':'The replacement changes the instance. Its acceptability depends on independently declared allowed repairs.'},
    ],
    'findings':[{'id':'PAPER005-'+ident,'severity':severity,'statement':statement,
        'evidence':[PREFIX+p for p in paths],
        'validation':'dag/reviews/additional_paper_005_probes.json' if i < 8 else 'complete source reading; additional controls pending'}
        for i,(ident,severity,statement,paths) in enumerate(findings)],
    'validation':['dag/reviews/additional_paper_005_tests.xml','dag/reviews/additional_paper_005_probes.json'],
    'provider_calls':0,'private_answer_access':False,
    'paper_quality_assessment':{'decision':'retain_scoped_graph_manual_quarantine_demo_receipts_until_repaired',
        'contribution':'Clear distinction between fixed-instance obstruction, section descent and replacement; exact rational graph exercises and adversarial guard cases.',
        'unestablished':'Domain-problem solutions, independent model accuracy/cost improvement, complete protocol enforcement and externally authenticated execution.'},
    'external_reference_checks':[
        {'url':'https://doi.org/10.1145/263699.263712','status':'publisher_record_and_author_bibliography_verified','limit':'Attribution and broad scope only; no independent full external proof audit.'},
        {'url':'https://stanford.edu/~boyd/cvxbook/','status':'author_book_page_verified','limit':'Book attribution only; Chapter 5 not independently audited.'},
        {'url':'https://www.rfc-editor.org/rfc/rfc8785','status':'official_record_and_intro_verified','limit':'Informational JSON canonicalization specification; generic sorted JSON is not automatically JCS.'},
        {'url':'https://zenodo.org/records/23114578','status':'endpoint_inaccessible','limit':'No inference of nonpublication; README and manuscript publication wording differ.'}],
    'limits':'Complete61-file support slice, with a contextual current-manuscript reread,40 PDF pages and60 archive logical members. Fresh evidence:62 pure-suite passes,34 native/source-object skips,2 HTTP exclusions and18 independent observations. An earlier full-suite attempt had one Windows10013 loopback failure and63 passes; it was interrupted after reporting because its server thread stayed alive. Historical results remain separately scoped. No source edits, paid calls, private answer access or native package execution; no general model or domain-performance result.'
}
cases = list(ET.parse(OUT/'additional_paper_005_tests.xml').iter('testcase'))
assert all(x.find('failure') is None and x.find('error') is None for x in cases)
skipped = sum(x.find('skipped') is not None for x in cases)
report['test_summary'] = {'passed':len(cases)-skipped,'skipped':skipped,'native_explicitly_unconfigured':True,'scope':'Eight named, fully read regression modules; not the full package suite.'}
probes = json.loads((OUT/'additional_paper_005_probes.json').read_text())
report['probe_receipt'] = {'path':'dag/reviews/additional_paper_005_probes.json','sha256':hashlib.sha256((OUT/'additional_paper_005_probes.json').read_bytes()).hexdigest()}
report['domain_probe_receipt'] = {'path':'dag/reviews/additional_paper_005_domain_probes.json','sha256':hashlib.sha256((OUT/'additional_paper_005_domain_probes.json').read_bytes()).hexdigest(),'observations':7}
report['validation'].append('dag/reviews/additional_paper_005_domain_probes.json')
report['validation'] += ['dag/reviews/additional_paper_005_archive_checks.json','dag/reviews/paper_005_support_inspection/render_receipt.json']
for finding in report['findings']:
    if finding['id'] in {'PAPER005-DEADLOCK-COST-AND-INTERMEDIATE','PAPER005-TERMINAL-IRREDUCIBILITY','PAPER005-MATOLCSI-REFUSAL-CONTRADICTS-VERDICT','PAPER005-R4-FALSE-ZERO-TERMINAL','PAPER005-VACUOUS-TRACE-VALIDATION'}:
        finding['validation'] = 'dag/reviews/additional_paper_005_domain_probes.json'
    if finding['id'] in {'PAPER005-CURRENT-MANIFEST-DRIFT','PAPER005-EDITED-HISTORICAL-RECEIPT-DIGEST','PAPER005-HISTORICAL-RECORD-AND-PIN-RENAMING'}:
        finding['validation'] = 'dag/reviews/additional_paper_005_archive_checks.json'
full_cases = list(ET.parse(OUT/'additional_paper_005_full_tests.xml').iter('testcase'))
report['full_suite_attempt'] = {'passed':sum(x.find('failure') is None and x.find('error') is None and x.find('skipped') is None for x in full_cases),
    'failed':sum(x.find('failure') is not None for x in full_cases),'skipped':sum(x.find('skipped') is not None for x in full_cases),
    'receipt':'dag/reviews/additional_paper_005_full_tests.xml',
    'failure':'Loopback SSE socket connect denied with Windows10013. Server thread remained waiting after test report, so the tracked process was interrupted. The HTTP-error test passed via ConnectionError but does not establish its intended401 path in this environment.',
    'native_explicitly_unconfigured':True,'user_credential_resolution_disabled':True}
pure_path = OUT/'additional_paper_005_pure_tests.xml'
if pure_path.exists():
    pure = list(ET.parse(pure_path).iter('testcase'))
    assert all(x.find('failure') is None and x.find('error') is None for x in pure)
    skipped_pure = sum(x.find('skipped') is not None for x in pure)
    report['pure_suite'] = {'passed':len(pure)-skipped_pure,'skipped':skipped_pure,'deselected_loopback_HTTP':2,'receipt':'dag/reviews/additional_paper_005_pure_tests.xml','limit':'Native and unavailable source-object checks remain skips; no HTTP path claimed.'}
(OUT/'additional_paper_005_support.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
(OUT/'additional_paper_005_support.md').write_text(
    f"Paper005 support review complete: {len(reviews)}/{len(pins)} full logical contents; {len(report['remaining_scope'])} pending in this slice.\n\n" + report['limits'] + '\n\n' +
    'Retain the manual as useful finite graph pedagogy: weighted distance from coboundaries, an exact dual lower bound, and the distinction between section adjustment and changing the instance. It claims no new theorem. Demo receipt defects and domain labels must be repaired or excluded before workflow admission.\n\n' +
    '\n\n'.join(x['id']+': '+x['statement'] for x in report['findings'])+'\n',encoding='utf-8')
print(json.dumps({'full':len(reviews),'pending':len(report['remaining_scope']),'tests':report['test_summary']}))
