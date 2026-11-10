"""Persist completed Paper002 reads; keep unread support files explicitly pending."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews'
PREFIX = 'papers/pfp/002_pfp_signed_presentations_and_search_frontier/'
BASE = 'papers/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/'
scope = json.loads((OUT / 'additional_paper_002_support_scope.json').read_text())
pins = {x['path']: x for x in scope['files']}
assessments = {
    'README.md': 'Full package description, algorithm boundaries, reproduction instructions and dependencies read. Finite signed-graph balance and exact fixed-basis matrix adaptation are distinguished from a physical sign-problem classification; enumeration is a protocol example, not an algorithmic speedup.',
    'code/genesis_alpha/sign_graph.py': 'Complete exact finite binary-parity graph checker read. Component BFS returns a gauge or reconstructs an odd closed walk and rechecks it. Witness verification binds all declared vertices and edges, including loops and parallel edges; exact symmetric matrix adaptation fixes the basis and sign grammar.',
    'code/genesis_alpha/frontier_search.py': 'All 423 lines read. Full typed presentation-key equality, immutable matrix snapshot, finite canonical eight-candidate batches, contiguous replayed UNKNOWN history, source/grammar binding and terminal handling reviewed. Hashes supply identity, not authority; node budget bounds new candidate enumeration rather than total replay time or money.',
    'code/native_sign_graph.py': 'Full native discovery, JSON transport, typed refusal and payload-shape checks read. A present failing native backend is not replaced by Python. Shape admission is not independent verification of native mathematical output; error lookup uses error although the bundled native emitter supplies message.',
    'code/live_proposer_demo.py': 'All 344 lines read. Untrusted model proposals are parsed and checked against supplied graph data. Default two-call path lacks whole-run monetary reservation and discards returned token/cost metadata; bounded transport and per-call persistence are prerequisites to benchmark adoption. No provider executed.',
    'code/demo1_signed_gauge.py': 'Complete three-case gauge/odd-walk demonstration read, including formerly truncated middle lines. Separate source checkers verify chosen examples. Direct main entry ignores run_demo Boolean, whereas aggregate runner checks it.',
    'code/demo2_frontier_search.py': 'Complete finite retrieval, frontier continuation, schedule comparison and receipt demonstration read. Toy presentation metadata does not prove a physical adapter; fixed enumeration is deliberately inferior to the linear solver as a graph algorithm. Direct main ignores run_demo Boolean.',
    'code/demo3_fock_obstruction.py': 'Complete bridge to previously reviewed exact rooted integrated Fock-path gap read. Checks finite 192-path census and analytic length bounds. Reuses the same restricted result rather than establishing a new general obstruction; direct main ignores run_demo Boolean.',
    'code/run_demos.py': 'Complete aggregate demonstration/notebook runner read. It checks Boolean demo outcomes and emits failure status; separate direct demo entrypoints do not. No source-mutating aggregate run performed.',
    'code/tests/__init__.py': 'Complete package marker read; no mathematical claim.',
    'code/tests/test_sign_graph.py': 'All three finite graph/carrier/type tests read. An explicitly chosen free presentation and different odd-loop presentation do not establish a canonical quotient from one to the other.',
    'code/tests/test_frontier_search.py': 'All continuation, forged-prefix, worker-schedule, exact key, grammar, metadata-only Hamiltonian binding, immutable-generator snapshot and budget/type cases read. Replaying an unkeyed hash cannot authorize false coverage because actual verdicts are rechecked.',
    'code/tests/test_manuscript_examples.py': 'All exact matrix and zero-based half-open frontier examples read. Gauge 010 and two-then-one candidate trace correspond to the declared finite carrier.',
    'code/tests/test_native_refusals.py': 'Complete controlled fixture-executable transport tests read. Refusal and malformed shape tests exercise adapter behavior, not correctness or compilation of the optional Rust backend.',
    'code/tests/test_native_sign_graph.py': 'Complete discovery and native-or-Python gauge/walk tests read. Discovery can skip and fallback cases cannot be represented as fresh native execution.',
    'code/rust/Cargo.toml': 'Complete standalone native package and dependency declarations read. Rational64 is bounded machine-integer arithmetic; dependency declaration alone supplies no build evidence.',
    'code/rust/src/bin/solve_sign_graph.rs': 'All 252 lines read. JSON entrypoints parse graph/matrix/witness data and emit typed status. Rational64 construction accepts nonzero i64 denominators but may encounter machine-range edge cases; errors are emitted under message and return normal process status. Adapter additionally checks status.',
    'code/rust/src/lib.rs': 'All six lines read. Thin exports bind the bundled sign_graph owner; no independent theorem or extra validation.',
    'code/rust/src/sign_graph.rs': 'Complete native graph implementation and three unit tests read. Mirrors Python BFS, source-bound gauge verification, parity-walk verification and symmetric Rational64 matrix sign extraction. Finite bit operations avoid arithmetic growth in the graph kernel. No fresh native build in this reading slice.',
    'pyproject.toml': 'Complete package/dependency/test configuration read; no install or environment modification performed.',
    'code/PROVENANCE.md': 'All historical source-copy, repair and later renaming records read. Dated hashes and source history remain separate from current execution; path/name normalization does not itself certify unchanged current bytes.',
    'tools/replay_notebook_source.py': 'Full plain-Python notebook source-cell replay helper read. It executes source, not Jupyter transport, display behavior or stored-output equality. Separate audit helper freshly executed every code cell and compared stdout, without invoking this source wrapper.',
    'docs/completion_supplement.md': 'Complete integration note read. Correctly limits the Fock obstruction to individual rooted integrated sequences and excludes extra authority from historical outputs.',
    'paper_claim_ledger.md': 'Complete twelve-claim ledger and evidence distinctions read. Classical balance, fixed-basis positivity and exact restricted gap are useful; it explicitly disclaims a machine-checked formal proof, general physical adapter and measured model benefit.',
    'docs/preprint_review_2026_10_02.md': 'Full historical review, repaired findings, validation table, references and publication boundary read. Its 47 passes and one skip are historical evidence, not a new audit run. It correctly separates shape admission from witness correctness and linear solver baseline from exponential protocol demonstration.',
    'paper.tex': 'Complete TeX source read, including preamble, complete proofs, worked examples, reproduction commands and references. Correct binary balance, diagonal-sign matrix reduction, nonnegative-beta exponential positivity, absolute path convergence and restricted all-length gap; rewritten links differ from the historical PDF edition.',
    '.env.example': 'Complete placeholder-only template read. Explicit environment/file selection and exclusion of live demonstration from manuscript evidence; no actual credential resolved.',
    'docs/descriptions.md': 'Complete abstract read. Scoped certificate-and-replay protocol and restricted Fock example; its shorthand positivity statement inherits the nonnegative-beta premise made explicit in the paper.',
    'docs/keywords.md': 'All metadata keywords read. Discrete signed chains and boundary operators are broader labels than the implemented graph parity and candidate protocol; no extra theorem follows from keyword terminology.',
    'docs/references.md': 'All four references read. Author arXiv records for Klassen/Terhal and Troyer/Wiese freshly verified for bibliography and abstract-level scope. Harary DOI endpoint was inaccessible and targeted publisher search did not corroborate this time; the balance argument is self-contained. Old companion repository path is stale.',
    'zenodo_metadata.json': 'Complete publication, creator, DOI and mixed-license metadata read. Current claimed Zenodo record could not be authenticated through direct access or targeted search; endpoint failure is not evidence of nonpublication. Description remains scoped.',
    'paper_change_log.md': 'Complete dated revision history read. Distinguishes original graph code, immutable-matrix repair, native refusal fixes and later first-preprint release. Historical invocation paths and receipt preservation claims need the archive/current delta qualification.',
    '_lev_examiner_theoretical_minimum_quiz/.gitkeep': 'Empty marker inspected; no mathematical or executable content.',
    '_lev_examiner_theoretical_minimum_quiz/00_preface_at_apartment_50.md': 'Entire fictional preface read. Explicitly separates invented examiner roles from authority or extra mathematical premises; no independent research claim.',
    '_lev_examiner_theoretical_minimum_quiz/study_guide.md': 'Complete study guide read. Correct carrier/coefficient, zero-versus-negative matrix, exact frontier, complete classifier versus incomplete search, pairing and individual-path versus total-tail distinctions.',
    '_lev_examiner_theoretical_minimum_quiz/quiz.md': 'All fourteen questions and scoring conventions read. Exact graph/matrix, two-then-one and full-batch frontier, convergence and all-length gap exercises are meaningful finite teaching controls; score is explicitly not a validated learner metric.',
    '_lev_examiner_theoretical_minimum_quiz/instructor_key.md': 'All fourteen worked answers and credit allocations read. Gauges 010/101, rational repair cost two, DHD, complete-prefix replay, full-batch cursor eight, signs +,+,- and rational all-length inequalities checked against actual code and paper. Public teaching key is unrelated to the sealed benchmark.',
    'jupyter_notebooks/signed_exchange_and_frontier.ipynb': 'Every Markdown/code cell, stored output and metadata field read. All five code cells freshly executed in an offline ordinary Python namespace with exact stdout equality; this is not a Jupyter transport/display test.',
    'code/rust/Cargo.lock': 'Complete dependency lock read. Standalone pfp_sign_graph pins serde, rational and error-handling libraries with registry checksums; num-bigint as a transitive dependency does not change explicit Rational64 use. No fresh native build claimed.',
    'docs/release_validation_2026_10_01.json': 'Full historical six-suite, notebook and three-native-test receipt read. Historical counts apply to its dated source hashes; later path substitutions changed recorded cwd/notebook/stdout text. Original receipt bytes remain in the release archive.',
    'docs/release_validation_2026_10_02.json': 'Full candidate receipt and all embedded stdout/stderr, input hashes, asset hashes and notebook metadata read. It correctly distinguishes working-tree hashes and selected 22-test execution from broader claims; historical cwd and hash-key fields were later rewritten.',
    'docs/preprint_review_validation_2026_10_02.json': 'Full preprint receipt, commands, source hashes, 47/1 test outcome, blocked interactive notebook, source-cell fallback and reference/PDF limits read. Native execution is explicitly absent in this receipt; former native evidence remains separate. Companion hash keys were path-rewritten later.',
    'MANIFEST.sha256': 'Every hash/path binding read and recomputed against current package and archived edition. Current raw and normalized mismatches are explicit in custody report; historical archive bindings all pass. Hashes certify bytes, not theorem truth.',
    'SHA256SUMS': 'Every hash/path binding read and recomputed, including the MANIFEST.sha256 envelope. Current envelope drifts; archived envelope is internally consistent. No manifest was regenerated.',
}
equal_bases = [
    'LICENSE', 'LICENSE-CODE', 'code/exact_fock_gap.py', 'code/fock_path_enumerator.py',
    'code/deposit_paths.py', 'code/tests/test_exact_fock_gap.py',
    'scripts/build_deposit_zip.py', 'scripts/regen_sha256sums.py', 'tools/rebuild_release.py',
]
diff_bases = {
    'code/certificate_gate.py': 'Fully reviewed Paper001 base plus complete difference: only two alias comment lines removed; mathematical certificate implementation unchanged.',
    'verify_deposit.py': 'Fully reviewed Paper001 base plus complete difference: optional/default versus explicitly requested test-selection docstring wording only; implementation unchanged.',
}
base_reviews = {x['path']: x for x in json.loads((OUT / 'additional_paper_001_support.json').read_text())['file_reviews']}
reviews = []
for rel, assessment in assessments.items():
    path = PREFIX + rel
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == pins[path]['sha256'], path
    n = len(data.decode('utf-8-sig').splitlines())
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
                    'reviewed_lines': [[1, n]] if n else [], 'assessment': assessment})
for rel in equal_bases + list(diff_bases):
    path, base = PREFIX + rel, BASE + rel
    data = (ROOT / path).read_bytes()
    assert base_reviews[base]['full_source_read'], base
    assert hashlib.sha256((ROOT / base).read_bytes()).hexdigest() == base_reviews[base]['sha256'], base
    assert hashlib.sha256(data).hexdigest() == pins[path]['sha256'], path
    if rel in equal_bases:
        assert data == (ROOT / base).read_bytes(), path
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
        'reviewed_lines': [[1, len(data.decode('utf-8-sig').splitlines())]], 'base_path': base,
        'review_method': 'Fully reviewed base plus exact byte equality' if rel in equal_bases else 'Fully reviewed base plus complete textual delta reading',
        'assessment': diff_bases.get(rel, 'Exact bytes match fully reviewed Paper001 base; its license, exact Fock-carrier, custody or release-tooling assessment transfers. No additional independent mathematical result.')})
render = json.loads((OUT / 'paper_002_support_inspection/render_receipt.json').read_text())
for item in render['renders']:
    path = item['pdf']
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == pins[path]['sha256']
    if item['index'] >= 2:
        matching = [x for x in render['standalone_correspondence'] if x['pdf_index'] == item['index']]
        assert len(matching) == len(item['pages']) and all(x['complete_pixel_matches'] for x in matching)
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
        'reviewed_lines': [], 'reviewed_pages': [[1, len(item['pages'])]],
        'review_method': 'All eight main and seventeen companion pages visually read with complete source correspondence; all 25 remaining pages have exact complete-pixel equality to those reviewed pages.',
        'assessment': 'Historical edition retains old role/path names. Main mathematics is readable; quiz page 1 loses alpha/XOR symbols and guide page 4 and key page 4 contain overlapping table cells. Source Markdown retains the complete mathematics.',
        'validation': 'dag/reviews/paper_002_support_inspection/render_receipt.json'})
custody = json.loads((OUT / 'additional_paper_002_custody.json').read_text())
assert len(custody['archive_members']) == 62
assert all(e['match'] for m in custody['archive_manifests'] for e in m['entries'])
review_index = {x['path']: x for x in reviews}
archive_dispositions = []
for item in custody['archive_members']:
    base = item['current_path']
    assert not item.get('current_missing'), base
    if base == PREFIX + 'paper.md':
        base_receipt = {'path': base, 'sha256': hashlib.sha256((ROOT / base).read_bytes()).hexdigest(),
            'review_method': 'Complete current manuscript read in this audit in addition to full TeX and visual PDF.'}
    else:
        assert review_index[base]['full_source_read'], base
        base_receipt = {'path': base, 'sha256': review_index[base]['sha256']}
    method = ('exact_bytes' if item.get('current_raw_equal') else
              'complete_text_equal_after_universal_LF' if item.get('current_lf_equal') else
              'fully_reviewed_base_plus_complete_text_delta')
    assert item.get('current_raw_equal') or item.get('current_lf_equal') or item.get('complete_difference_lines'), item
    archive_dispositions.append({**item, 'reviewed_base': base_receipt, 'review_method': method,
        'assessment': 'Inherits the fully read current content with the complete reviewed historical role/path/native-env-variable differences; historical source and receipt scope retained.'})
archive_path = PREFIX + '002_pfp_signed_presentations_and_search_frontier_2026-10-02.zip'
assert hashlib.sha256((ROOT / archive_path).read_bytes()).hexdigest() == pins[archive_path]['sha256']
reviews.append({'path': archive_path, 'sha256': pins[archive_path]['sha256'], 'full_source_read': True,
    'reviewed_lines': [], 'reviewed_archive_members': 62,
    'review_method': 'All 62 logical member contents reviewed through pinned current bases, byte/LF equality or every textual difference; CRC, unique confined membership and all embedded manifest hashes checked.',
    'assessment': 'Complete logical-content review, not a security proof of the ZIP parser or compression implementation. Archive preserves original editions and historical receipt paths; current package hashes do not inherit its custody pass.',
    'validation': 'dag/reviews/additional_paper_002_custody.json'})
done = {x['path'] for x in reviews}
cases = list(ET.parse(OUT / 'additional_paper_002_tests.xml').iter('testcase'))
passed = sum(all(x.find(tag) is None for tag in ('failure', 'error', 'skipped')) for x in cases)
skipped = sum(x.find('skipped') is not None for x in cases)
assert passed == 47 and skipped == 1 and len(cases) == 48
assert done == set(pins)
report = {
    'schema_version': '1.0', 'status': 'scope_complete', 'source_commit': scope['source_commit'],
    'scope_manifest': 'dag/reviews/additional_paper_002_support_scope.json',
    'file_reviews': sorted(reviews, key=lambda x: x['path']),
    'remaining_scope': [x for x in scope['files'] if x['path'] not in done],
    'claims': [
        {'id': 'PAPER002-FINITE-SIGNED-BALANCE', 'statement': 'For a supplied finite signed graph, a binary vertex gauge exists exactly when every closed walk has even parity; component propagation supplies a gauge or a source-checkable odd closed walk.', 'status': 'complete_implementation_read', 'dependencies': ['Declared vertices, edges and binary labels; trusted finite checker.'], 'evidence': [PREFIX + 'code/genesis_alpha/sign_graph.py', PREFIX + 'code/rust/src/sign_graph.rs'], 'limits': 'Classical signed-graph balance; no general physical sign-problem result or novel graph algorithm.'},
        {'id': 'PAPER002-EXACT-FIXED-BASIS-REDUCTION', 'statement': 'A supplied exact real symmetric matrix admits an off-diagonal-nonpositive diagonal sign transform exactly when its nonzero-entry sign graph admits the corresponding binary gauge.', 'status': 'complete_adapter_read', 'dependencies': ['Fixed declared basis and diagonal sign transformation grammar.'], 'evidence': [PREFIX + 'code/genesis_alpha/sign_graph.py'], 'limits': 'No classification under arbitrary basis changes or efficient sampling guarantee.'},
        {'id': 'PAPER002-CONTIGUOUS-SEARCH-REPLAY', 'statement': 'The finite enumerator checks canonical candidate batches and preserves an explicit suffix on UNKNOWN; continuation rechecks a contiguous prefix from zero against the same graph, complete presentation key and grammar.', 'status': 'complete_source_and_test_read', 'dependencies': ['Trusted checker, collision-resistant identity hash and exact current source.'], 'evidence': [PREFIX + 'code/genesis_alpha/frontier_search.py'], 'limits': 'Exponential enumeration illustrates a reusable search protocol. New-node bounds do not bound total replay time, dollars or prove a physical adapter.'},
    ],
    'findings': [
        {'id': 'PAPER002-LIVE-COST-ACCOUNTING', 'severity': 'benchmark_admission_gap', 'statement': 'The live proposer defaults to two calls and a per-call output token limit, but neither reserves a whole-run USD limit nor retains returned token/cost metadata. Adopt only through the separate guarded benchmark transport.', 'evidence': [PREFIX + 'code/live_proposer_demo.py']},
        {'id': 'PAPER002-NATIVE-ERROR-FIELD', 'severity': 'diagnostic_defect', 'statement': 'The native CLI emits refusal details under message, while the Python adapter reads error; a correctly typed refusal can lose its actual diagnostic. Status checking still prevents a silent Python replacement.', 'evidence': [PREFIX + 'code/native_sign_graph.py', PREFIX + 'code/rust/src/bin/solve_sign_graph.rs']},
        {'id': 'PAPER002-DIRECT-DEMO-EXIT', 'severity': 'execution_evidence_gap', 'statement': 'All three standalone demo main blocks ignore the Boolean returned by run_demo, so a printed failed check need not fail the process. The aggregate run_demos wrapper does inspect those Booleans. Direct process exit alone is insufficient demonstration evidence.', 'evidence': [PREFIX + 'code/demo1_signed_gauge.py', PREFIX + 'code/demo2_frontier_search.py', PREFIX + 'code/demo3_fock_obstruction.py', PREFIX + 'code/run_demos.py']},
    ],
    'archive_member_dispositions': archive_dispositions,
    'validation': ['dag/reviews/additional_paper_002_tests.xml', 'dag/reviews/additional_paper_002_probes.json', 'dag/reviews/additional_paper_002_custody.json', 'dag/reviews/paper_002_support_inspection/render_receipt.json'],
    'test_summary': {'passed': passed, 'skipped_native_discovery': skipped, 'failed': 0, 'native_build_performed': False,
        'independent_small_graphs': 4165, 'fresh_notebook_code_cells': 5, 'all_notebook_stdout_matches': True},
    'provider_calls': 0, 'private_answer_access': False,
    'paper_quality_assessment': {'decision': 'retain_scoped_certificate_and_replay_protocol_with_specific_repairs', 'useful_contribution': 'Inspectable finite signed-graph certificates, exact matrix adapter and honest resumable search; the restricted Fock example reuses earlier code. Concrete proofs, refusal controls and replay obligations make it useful program material despite limited theoretical novelty.', 'unestablished': 'Novel signed-graph theorem, generic physical sign-problem classification, workflow cost/accuracy improvement or current release reproducibility. No new native build or formal refinement proof.'},
}
report['findings'].extend([
    {'id': 'PAPER002-CURRENT-MANIFEST-DRIFT', 'severity': 'custody_gap', 'statement': 'Current MANIFEST.sha256 and SHA256SUMS have 27 and 28 raw mismatches; 15 and 16 survive universal LF normalization. All archived manifest bindings pass. Historical release integrity does not establish current tree integrity.', 'evidence': [PREFIX + 'MANIFEST.sha256', PREFIX + 'SHA256SUMS'], 'validation': 'dag/reviews/additional_paper_002_custody.json'},
    {'id': 'PAPER002-EDITED-HISTORICAL-RECEIPTS', 'severity': 'provenance_gap', 'statement': 'All three dated validation JSONs have later role/path substitutions in hash-key, notebook, cwd or captured stdout fields. Their original bytes remain in the ZIP. Label current files as transcriptions and retain historical/source binding separately; no new execution or fabricated result is inferred.', 'evidence': [PREFIX + 'docs/preprint_review_validation_2026_10_02.json', PREFIX + 'docs/release_validation_2026_10_01.json', PREFIX + 'docs/release_validation_2026_10_02.json'], 'validation': 'dag/reviews/paper_002_support_inspection/archive_complete_text_diffs.txt'},
    {'id': 'PAPER002-PDF-MISSING-MATH', 'severity': 'rendering_defect', 'statement': 'Quiz page 1 (companion page 14) visibly loses alpha and XOR in its defining gauge equation, leaving incomplete subscripts/equality; further inline mathematical markup is degraded. Current Markdown and main manuscript contain the correct equation. Repair a new rendered edition while preserving historical PDFs.', 'evidence': [PREFIX + '_lev_examiner_theoretical_minimum_quiz/quiz.pdf', PREFIX + '002_pfp_examiner_companion.pdf'], 'validation': 'dag/reviews/paper_002_support_inspection/render_01/page-14.png'},
    {'id': 'PAPER002-PDF-TABLE-OVERLAP', 'severity': 'rendering_defect', 'statement': 'Study-guide page 4 (companion page 5) overlaps long test paths with the adjacent Supports column. Key page 4 (companion page 10) runs GAUGE_VERIFIED into the witness column. These obscure evidence mappings and the exact frontier example despite correct Markdown.', 'evidence': [PREFIX + '_lev_examiner_theoretical_minimum_quiz/study_guide.pdf', PREFIX + '_lev_examiner_theoretical_minimum_quiz/instructor_key.pdf'], 'validation': 'dag/reviews/paper_002_support_inspection/render_receipt.json'},
    {'id': 'PAPER002-EDITION-PATH-DRIFT', 'severity': 'version_binding_gap', 'statement': 'All seven PDFs retain historical archived bytes and old role/reference paths while current Markdown/TeX were renamed. Internal source metadata still names absent atlas/coda_atlas paths. Published or downloaded editions need explicit source-revision/location bindings; this is not a defect in the balance proof.', 'evidence': [PREFIX + 'paper.tex', PREFIX + 'paper.pdf', PREFIX + 'docs/references.md', PREFIX + '_lev_examiner_theoretical_minimum_quiz/study_guide.md']},
])
for item in report['findings'][:3]:
    if item['id'] != 'PAPER002-LIVE-COST-ACCOUNTING':
        item['validation'] = 'dag/reviews/additional_paper_002_probes.json'
report['external_reference_checks'] = [
    {'url': 'https://arxiv.org/abs/1806.05405', 'status': 'author_record_and_abstract_verified', 'limit': 'Bibliography and local-basis scope only; not a full independent proof audit.'},
    {'url': 'https://arxiv.org/abs/cond-mat/0408370', 'status': 'author_record_and_abstract_verified', 'limit': 'Generic NP-hardness scope; no per-instance impossibility inference.'},
    {'url': 'https://doi.org/10.1307/mmj/1028989917', 'status': 'endpoint_inaccessible', 'limit': 'No absence inference; local balance proof assessed directly.'},
    {'url': 'https://zenodo.org/records/23114127', 'status': 'not_authenticated', 'limit': 'Direct endpoint unavailable and targeted search inconclusive; no nonpublication inference.'},
]
(OUT / 'additional_paper_002_support.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
lines = [f"Paper002 supporting-file review: {len(reviews)}/{len(pins)} logical contents reviewed; {len(report['remaining_scope'])} pending.", '',
         'All 50 PDF pages and 62 archive members have explicit reading/equality/difference provenance. This is a complete declared support slice, not completion of the whole repository audit. Original sources and historical artifacts are unchanged.', '',
         'Fresh validation: 47 Python tests passed, one native-discovery skip; 4,165 independent small-graph comparisons agreed; five notebook code cells reproduced exact saved stdout. No provider/native build/private-answer access. Native shape admission remains a documented trust boundary, not an independently proved Rust result.', '']
for claim in report['claims']:
    lines.extend([claim['statement'], claim['limits'], ''])
for item in report['findings']:
    lines.extend([item['id'] + ': ' + item['statement'], ''])
(OUT / 'additional_paper_002_support.md').write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps({'full': len(reviews), 'pending': len(report['remaining_scope']), 'claims': len(report['claims']), 'findings': len(report['findings'])}))
