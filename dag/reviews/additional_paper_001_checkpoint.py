"""Persist actual completed Paper001 reading and offline checks; never alter sources."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews'
PREFIX = 'papers/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/'
scope = json.loads((OUT / 'additional_paper_001_support_scope.json').read_text())
pins = {x['path']: x for x in scope['files']}
assessments = {
    'paper.tex': 'All 656 lines read, including TeX preamble, mathematical derivations, implementation limits, reproduction commands and references. Graph duality, cycle formula, sparse-existence argument and sufficient uniqueness match the reviewed manuscript mathematics. Rendered edition and source differ in rewritten reference paths; current toolchain/build claims need version binding.',
    '_lev_examiner_theoretical_minimum_quiz/.gitkeep': 'Empty marker explicitly inspected; no executable or mathematical content.',
    'jupyter_notebooks/demo1_holonomy_interactive.ipynb': 'Every cell source, Markdown, stored output and kernel metadata read. Four reviewed code cells executed offline in an ordinary Python namespace with stored stdout equality; finite minimum-5 triangle remains separate from manuscript minimum-3 example.',
    'jupyter_notebooks/demo2_fsp_interactive.ipynb': 'Every cell source, Markdown, stored output and kernel metadata read. Two reviewed code cells executed offline with stored stdout equality, exercising eight fixed sign-gate expectations and one finite pairing.',
    'jupyter_notebooks/demo3_adversarial_debate_interactive.ipynb': 'Every cell source, Markdown, stored output and kernel metadata read. One reviewed code cell replayed ten retained records offline. Fresh stdout differs only in source trace SHA-256; CRLF-to-LF normalization exactly recovers the stored hash. Historical label agreement is not physical truth.',
    '.env.example': 'Complete placeholder-only example read. Live demo explicitly optional and outside paper evidence; no real credential read or resolved.',
    'verify_deposit.py': 'Complete two-way manifest, selected-test and optional Lean wrapper read. Digest custody is distinct from mathematical truth; optional Lean census only inspects recognized axiom lines and does not require any declaration output. No mutation or live subprocess execution of this wrapper.',
    'tools/replay_full_axiom_census.py': 'Full generated module-wide census implementation read. Rejects empty declaration output, duplicate names and non-whitelisted axioms; generates source/report on execution. Not executed in source package.',
    'tools/replay_lean_axiom_census.py': 'Full named-census parser/generator/replay read. Compares ordered declarations but a headerless empty report can yield an empty expected census; actual source output and total-module coverage are separate obligations. Not executed in source package.',
    'scripts/build_deposit_zip.py': 'Complete fixed-order archive writer read. Checks declared input hashes, duplicate member names, path confinement and dated output name; provenance remains dependent on manifest completeness and trusted local reads.',
    'scripts/regen_sha256sums.py': 'Complete two-stage manifest renderer read. Excludes manifests from payload scan and adds MANIFEST.sha256 only to SHA256SUMS. Check mode is read-only; write mode was not run.',
    'paper_change_log.md': 'All 296 lines read. Explicit current scope supersedes old general sign, RFC canonicalization and empirical ground-truth overclaims. Historical claim chronology is retained, not treated as fresh execution evidence.',
    'docs/descriptions.md': 'Full abstract read; accurately presents established exact graph optimization facts and limits native solver/Lean claims, expressly disclaims measured model or general reasoning improvement.',
    'docs/keywords.md': 'All keywords read. Older retraction/toy-involution title is metadata terminology rather than an additional proved mechanism.',
    'docs/references.md': 'Complete four-entry bibliography read. Boyd author page and Necula author publication record verified; ACM DOI request returned 403 and author-linked PostScript could not be rendered by browser. Zenodo record remains unauthenticated. Old atlas companion paths need current-location binding; endpoint inaccessibility does not disprove publication.',
    'zenodo_metadata.json': 'Complete publication metadata read. Description matches scoped mathematical abstract; claimed DOI/publication status not independently authenticated by inaccessible endpoint. Mixed text/code licenses explicitly separated.',
    'lean4/full_axiom_report.txt': 'All 159 lines read: historical census lists 151 package-local generated/private/public declarations over three modules with propext and Quot.sound among dependencies. This is a historical record, not a fresh build in this slice.',
    'public_export/run_notebook.bat': 'Complete Windows launch helper read. Invokes uv with unpinned notebook display dependencies; not a mathematical test or reproducible lock. Not executed.',
    'public_export/run_notebook.sh': 'Complete POSIX launch helper read. Changes to package directory and invokes uv with notebook display dependencies; not executed.',
    'specs/normal_form_contract_schema.yaml': 'All 228 lines read. Custom schema vocabulary describes declared status, predicates, authorization and terminal mappings; this data file itself does not implement a validator or prove any contract condition.',
    '_lev_examiner_theoretical_minimum_quiz/00_preface_at_apartment_50.md': 'All 190 lines read. Explicit fictional theatrical framing includes correct graph triangle arithmetic and witness distinction; narrative adds no independent mathematical result or evidence of teaching effectiveness.',
    '_lev_examiner_theoretical_minimum_quiz/paper001_notebook_learning_worksheet.md': 'All 88 lines and worked answers read. Correct minimum-5 and fractional 7/2 examples, negative coverage, unused Lean admission premise, historical-label arithmetic and byte-custody distinctions provide useful finite controls.',
    '_lev_examiner_theoretical_minimum_quiz/quiz.md': 'All 227 lines read. Thirteen problems and two capstones exercise weak duality, cycle formula, sufficient uniqueness condition, finite fuel and native trust boundary; no claim of measured pedagogical transfer is established.',
    '_lev_examiner_theoretical_minimum_quiz/study_guide.md': 'All 437 lines read. Weak-duality and coboundary-invariance derivations checked algebraically; sparse existence is separated from dense optima and sufficient uniqueness from its invalid converse. Native source link is stale; fictional rhetoric supplies no mathematical premise.',
    '_lev_examiner_theoretical_minimum_quiz/instructor_key.md': 'All 163 lines read. Exact triangle, four-cycle and K4 primal-dual witnesses checked by hand; strict dual slack connects the K4 zero-residual edges and establishes gauge-fixed uniqueness despite failure of the stronger support condition. Build assertions remain historical and separate.',
    'code/certificate_gate.py': 'Full exact rational primal/dual certificate checker read. Verifies source edge coverage, capacity, divergence, recomputed primal/dual objectives and equality; source-binding countercontrol passes. Host checker and supplied graph remain admissions.',
    'code/demo1_holonomy.py': 'Exact rational finite graph example and assertions read. Fixed-source objective obstruction differs from transient descent; example is not a generic reasoning benchmark.',
    'code/demo2_bqnf_fsign.py': 'Finite example sign-gate calls read. Demonstration labels are subordinate to exact gate prerequisites and declared representation.',
    'code/exact_fock_gap.py': 'Complete rational enclosure proof program read. Fixed three-site parameters and integrated rooted hopping sequences give the stated unmatched negative-weight gap; active guards survive Python optimization.',
    'code/fock_path_enumerator.py': 'Complete six-mode occupation enumeration, fermionic signs and integrated-weight series read. Decimal computations and assertions support bounded diagnostics; exact gap owner is separate.',
    'code/native_functional.py': 'Full native resolver/JSON adapter and Python fallback read. Present native failures do not silently fall back. Returned potentials/objective checked, but global primal-dual certification is a separate obligation; selected binary remains trusted.',
    'code/symbol_game_governor.py': 'All 924 lines read. Exact graph certificates, finite spanning-tree search, CUT/ASSERT/RETRACT/VERIFY/LIFT transitions, hash transcript and sign gates assessed. Strict rational descent need not terminate; Python state is host-trusted. Thermal positivity interpretation requires an admitted beta domain absent from the matrix-predicate gate.',
    'code/run_adversarial_debate_benchmark.py': 'Deterministic supplied proposals and receipt generation fully read. Mock comparisons are not measurements of live model improvement.',
    'code/live_adversarial_demo.py': 'All 478 lines read. Default repeated two-model bouts have no whole-run monetary admission. Missing-certificate refusals are mislabeled as obstructions; successful first response is lost if second call fails. Prompt examples do not consistently match executable certificate schema.',
    'code/run_demos.py': 'Complete local orchestration read; subprocess/receipt success must remain distinct from the mathematical scope and historical outputs. Not executed in this audit.',
    'code/generate_figures.py': 'Full deterministic plotting program read. Plot illustrates fixed-source residual descent and unchanged obstruction; it does not measure general workflow benefit.',
    'code/rust/Cargo.toml': 'Full package/dependency declaration read; local core_solvers path resolves outside checkout to an absent owner. Actual repository owner exists at code/rust/core_solvers.',
    'code/rust/src/bin/solve_graph_phi1.rs': 'Complete thin stdin/stdout native solver wrapper read. Mathematical implementation belongs to the referenced core_solvers crate; no native build performed.',
    'code/rust/README.md': 'Full build/run instructions read; current relative Cargo dependency does not resolve as claimed.',
    'code/tests/__init__.py': 'Full package marker read; no independent mathematical result.',
    'code/tests/test_certificate_gate.py': 'All exact certificate source-binding, tamper and type controls read and executed.',
    'code/tests/test_exact_fock_gap.py': 'All fixed-parameter exact-gap tests read and executed, including optimization-mode subprocess guard check.',
    'code/tests/test_fock_path_proposition.py': 'Complete finite Fock path census/weight tests read and executed. Scope remains the declared integrated sequence carrier.',
    'code/tests/test_manuscript_witnesses.py': 'All manuscript witness tests read and executed. Exact finite examples do not establish generic convergence.',
    'code/tests/test_governor.py': 'Complete transition/sign-gate tests read and executed; tests cover supplied local cases rather than arbitrary host tampering.',
    'code/tests/test_proposed_boundaries.py': 'All proposed-boundary tests read and executed; preserves distinction between supplied hypotheses, refusal and obstruction.',
    'code/tests/test_review_regressions.py': 'All regression tests read and executed; source-bound certificates and native failure boundaries assessed.',
    'code/tests/test_zenodo_regression_suite.py': 'All release regression tests read. Every body passes across preserved initial run and four safe-temp reruns; initial setup errors were sandbox temporary-directory failures, not test-body failures.',
    'lean4/InvolutionLaws.lean': 'Complete definitions and cancellation theorem read. Sign reversal and weight preservation imply pair cancellation; involution/no-fixed-point assumptions do not by themselves prove finite-carrier total cancellation or runtime correspondence.',
    'lean4/NonAuthority.lean': 'Full single-constructor authority model read. The no-authority result follows from the supplied type and is not an operational authorization theorem.',
    'lean4/OddCycleObstruction.lean': 'Full finite triangle gauge proof read. Exhausts eight sign assignments and proves alternating site-gauge obstruction only.',
    'lean4/Census.lean': 'Full selected axiom census commands read; declaration listing is not a fresh build receipt.',
    'lean4/FullCensus.lean': 'Full expanded axiom census commands read; supporting report still separately pending.',
    'lean4/lakefile.lean': 'Full local Lean library configuration read; no external package requirement declared here.',
    'lean4/lean-toolchain': 'Pinned Lean v4.35.0 read; historical short census reports v4.34.0-rc1 and cannot authenticate this toolchain run.',
    'lean4/axiom_report.txt': 'Full historical short census read: two listed claims have no axioms, one uses propext and Quot.sound. Historical toolchain differs from current pin; no fresh Paper001 Lean run in this slice.',
    'lean4/lake-manifest.json': 'Full dependency lock metadata read; empty package list and local package name only.',
    'specs/bqnf_fsign_contract.yaml': 'Full representation/normal-form/sign contract read. Finite pairing, positivity and odd-cycle predicates have distinct carrier assumptions; model prose alone is not a witness.',
    'pyproject.toml': 'Full package/test/dependency configuration read. Development pytest lower bound differs from old README validation version; no dependency installation occurred.',
    'README.md': 'Complete package scope/build/replay instructions read. Graph-repair owner and legacy Fock content are distinguished; native path and historical toolchain instructions require version binding.',
    'docs/completion_supplement.md': 'Complete scope supplement read. Retains finite exact checks, non-authority boundary and narrower representation-specific sign claims.',
    'paper_claim_ledger.md': 'Complete claim/evidence ledger read. Source correspondence is assessed separately from historical assertions; native reference path is currently broken.',
}
equal_bases = {
    'LICENSE': 'LICENSE', 'LICENSE-CODE': 'LICENSE-CODE',
    'code/deposit_paths.py': 'code/deposit_paths.py',
    'tools/rebuild_release.py': 'tools/rebuild_release.py',
}
base_report = json.loads((OUT / 'additional_paper_000_support.json').read_text())
base_reviews = {x['path']: x for x in base_report['file_reviews']}
reviews = []
for rel, assessment in assessments.items():
    path = PREFIX + rel
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == pins[path]['sha256'], path
    n = len(data.decode('utf-8-sig').splitlines())
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
                    'reviewed_lines': [[1, n]] if n else [], 'assessment': assessment})
for rel, base_rel in equal_bases.items():
    path = PREFIX + rel
    base = 'papers/pfp/000_pfp_introduction/' + base_rel
    data = (ROOT / path).read_bytes()
    assert data == (ROOT / base).read_bytes(), path
    assert base_reviews[base]['full_source_read']
    assert hashlib.sha256(data).hexdigest() == pins[path]['sha256']
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
                    'reviewed_lines': base_reviews[base]['reviewed_lines'],
                    'assessment': 'Complete byte equality to fully reviewed introductory-package owner; inherits its license, package-location or release-tooling assessment. No new mathematical result.',
                    'review_method': 'Fully read base plus complete byte equality', 'base_path': base})
render = json.loads((OUT / 'paper_001_support_inspection/render_receipt.json').read_text())
for item in render['renders']:
    path = item['pdf']
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == pins[path]['sha256']
    if item['index'] >= 2:
        matching = [m for m in render['standalone_correspondence'] if m['pdf_index'] == item['index']]
        assert len(matching) == len(item['pages']) and all(m['complete_pixel_matches'] for m in matching)
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
        'reviewed_lines': [], 'reviewed_pages': [[1, len(item['pages'])]],
        'review_method': 'All eight main pages and all 36 companion pages read visually with full source correspondence; all 44 other standalone pages have exact complete-pixel equality to those reviewed pages.',
        'assessment': 'Graph derivations and teaching examples retain their stated scope. Historical PDFs retain old naming/reference editions. Preface page 4 has a clipped code-block line; the corresponding Markdown remains complete.',
        'validation': 'dag/reviews/paper_001_support_inspection/render_receipt.json'})
figure = PREFIX + 'public_export/fig1_descent_and_obstruction.png'
assert hashlib.sha256((ROOT / figure).read_bytes()).hexdigest() == pins[figure]['sha256']
reviews.append({'path': figure, 'sha256': pins[figure]['sha256'], 'full_source_read': True, 'reviewed_lines': [],
    'review_method': 'Complete image visual inspection plus complete generator-source reading',
    'assessment': 'Two panels correctly distinguish triangle costs 6,5,4,3 against fixed optimum 3 and finite observations of 2^-t ending at 1/1024 above optimum zero. The latter is an illustration of the proved infinite sequence, not numerical evidence of convergence or a runtime benchmark.'})
test_receipts = ['additional_paper_001_selected_tests.xml', 'additional_paper_001_review_tests.xml', 'additional_paper_001_replay_inputs_tests.xml']
passed, errors = set(), []
for name in test_receipts:
    for case in ET.parse(OUT / name).iter('testcase'):
        node = (case.get('classname'), case.get('name'))
        if case.find('error') is not None:
            errors.append({'receipt': name, 'node': list(node), 'kind': 'initial_temporary_directory_setup_error'})
        elif case.find('failure') is None and case.find('skipped') is None:
            passed.add(node)
assert len(passed) == 74, len(passed)
assert len(errors) == 4, len(errors)
assert all(tuple(x['node']) in passed for x in errors)
claims = [
    {'id': 'PAPER001-EXACT-GRAPH-CERTIFICATE', 'statement': 'For the supplied finite graph and rational edge data, capacity-bounded divergence-free dual flow and equal recomputed primal/dual objectives certify the exact weighted L1 residual minimum. CUT reduces a selected potential residual; it does not lower the fixed-source optimum.', 'status': 'source_read_with_bounded_exact_controls', 'dependencies': ['Supplied graph, orientation, positive rational weights and source-bound claims.', 'Host exact checker and rational arithmetic are trusted.'], 'evidence': [PREFIX + 'code/certificate_gate.py', PREFIX + 'code/symbol_game_governor.py'], 'limits': 'Finite tree enumeration can be exponential and capped. Strict rational descent does not imply finite termination or general model improvement.'},
    {'id': 'PAPER001-FIXED-FOCK-GAP', 'statement': 'On the declared rooted hopping-sequence carrier after ordered times are integrated out, fixed t=1, U=2, beta=1/4, mu=0 yields 192 length-three closed paths, split 96/96 by sign, and an exact rationally enclosed negative magnitude with no positive equal-weight partner in any length class.', 'status': 'complete_source_read_and_exact_local_replay', 'dependencies': ['Six fermionic modes and fixed occupation ordering, triangular lattice and supplied Hamiltonian.', 'Integrated sequences rather than time-labeled paths, regroupings or arbitrary representations.'], 'evidence': [PREFIX + 'code/exact_fock_gap.py', PREFIX + 'code/fock_path_enumerator.py'], 'limits': 'No classification of the general physical fermion sign problem follows.'},
    {'id': 'PAPER001-FORMAL-SCOPE', 'statement': 'The small Lean declarations prove conditional pair cancellation, a no-authority property of a supplied single-constructor type, and the finite triangle alternating-gauge obstruction.', 'status': 'full_source_read_historical_census_separate', 'dependencies': ['Definitions and assumptions in the Lean files; no demonstrated code refinement map.'], 'evidence': [PREFIX + 'lean4/InvolutionLaws.lean', PREFIX + 'lean4/NonAuthority.lean', PREFIX + 'lean4/OddCycleObstruction.lean'], 'limits': 'No fresh Lean build in this support slice; historical toolchain differs from current pin.'},
]
def finding(ident, severity, statement, sources, probe=None):
    item = {'id': ident, 'severity': severity, 'statement': statement,
            'evidence': [PREFIX + p for p in sources]}
    if probe:
        item['validation'] = 'dag/reviews/additional_paper_001_probes.json'
        item['probe_id'] = probe
    return item
findings = [
    {'id': 'PAPER001-NAMED-CENSUS-EMPTY-ADMISSION', 'severity': 'verification_coverage_gap',
     'statement': 'The named-census tool accepts a headerless report with zero declaration rows, generates an import-only Census.lean and passes check_census. A direct isolated parser/render/check control reproduces this without running Lean. Require nonempty expected declarations; zero-output agreement is not evidence that the intended theorems were checked. The separate full-census tool already rejects empty output.',
     'evidence': [PREFIX + 'tools/replay_lean_axiom_census.py', PREFIX + 'tools/replay_full_axiom_census.py'],
     'validation': 'dag/reviews/additional_paper_001_empty_census_probe.json'},
    finding('PAPER001-CURRENT-MANIFEST-DRIFT', 'custody_gap', 'The current 95-entry MANIFEST.sha256 and 96-entry SHA256SUMS have 52 and 53 raw mismatches; 20 and 21 survive universal LF normalization. All 95 and 96 embedded historical archive bindings pass. Historical archive checks cannot certify the current renamed/edited tree.', ['MANIFEST.sha256', 'SHA256SUMS']),
    finding('PAPER001-EDITION-BINDING', 'version_binding_gap', 'All eight PDFs are byte-identical to historical archive members. Companion PDFs retain Landau/adversary-persona naming while current Markdown uses Examiner/Adversary; the current Lean pin is v4.35.0 while prose and short historical census name v4.34.0-rc1. Label historical editions and distinguish current source validation before claiming reproducibility.', ['001_pfp_examiner_companion.pdf', 'paper.tex', 'lean4/lean-toolchain', 'lean4/axiom_report.txt']),
    finding('PAPER001-PDF-CLIPPED-PREFACE', 'rendering_defect', 'Preface page 4 (also companion page 4) visibly clips the code-block sentence about exact rational graph calculations and drawing conversions at the right page edge. The Markdown sentence is complete. A new edition should wrap that block; preserve the historical PDF.', ['_lev_examiner_theoretical_minimum_quiz/00_preface_at_apartment_50.pdf', '001_pfp_examiner_companion.pdf']),
    finding('PAPER001-LIVE-FALSE-OBSTRUCTION', 'false_mathematical_label', 'The live wrapper initializes OpenSignObstruction for non-admitted verification and reports adversary adjudication even when the gate only refuses missing determinant hypotheses. A mock U=0 case reproduces this. Missing evidence is not a proved obstruction; retain the actual typed gate status.', ['code/live_adversarial_demo.py', 'code/symbol_game_governor.py'], 'LIVE-REFUSAL-RELABELLED-AS-OBSTRUCTION'),
    finding('PAPER001-LIVE-NO-RUN-CAP', 'benchmark_admission_gap', 'Default live execution can make twenty model calls before transport retries (up to sixty attempts), with no whole-run dollar reservation, tariff bound or complete cost/token accounting. max_tokens=1000 alone does not enforce the requested USD 0.10 cap. Use the separate guarded benchmark transport before any live adoption.', ['code/live_adversarial_demo.py']),
    finding('PAPER001-LIVE-PARTIAL-LOSS', 'evidence_and_accounting_gap', 'A successful first model response is not persisted when the second call fails; the failed bout records transport error and zero completed trials. Offline reproduction confirms missing first response. Persist and charge each call before attempting the next.', ['code/live_adversarial_demo.py'], 'LIVE-PARTIAL-BOUT-LOSS'),
    finding('PAPER001-NATIVE-PATH', 'reproducibility_gap', 'The Cargo path dependency resolves to absent C:/Users/a343o/engine/crates_rs/core_solvers, while this checkout owns code/rust/core_solvers. Build instructions and corresponding claim-ledger paths need repair or explicit external-dependency instructions.', ['code/rust/Cargo.toml', 'code/rust/README.md', 'paper_claim_ledger.md'], 'NATIVE-DEPENDENCY-PATH'),
    finding('PAPER001-POSITIVITY-DOMAIN', 'missing_interpretation_premise', 'The matrix-predicate gate accepts beta=-1 and a nonnumeric beta while labeling worldline positivity. Its checked off-diagonal predicate is meaningful, but the thermal interpretation requires a separately admitted nonnegative-beta domain: a zero-energy unit-hopping triangle has a three-hop beta^3/3! term equal to -1/6 at beta=-1.', ['code/symbol_game_governor.py', 'specs/bqnf_fsign_contract.yaml'], 'POSITIVITY-BETA-DOMAIN'),
    finding('PAPER001-LIVE-SCHEMA-MISMATCH', 'non_executable_proposal_examples', 'Live prompt examples use xi mapping where the executable gate expects pairs, and an obstruction reason where an obstruction_witness is required. Host parameters omit the explicit matrices or finite weights needed by those verification routes. Such refusals cannot measure the ability to construct an otherwise admissible certificate.', ['code/live_adversarial_demo.py', 'code/symbol_game_governor.py']),
]
done = {x['path'] for x in reviews}
report = {
    'schema_version': '1.0', 'status': 'in_progress', 'source_commit': scope['source_commit'],
    'scope_manifest': 'dag/reviews/additional_paper_001_support_scope.json',
    'file_reviews': sorted(reviews, key=lambda x: x['path']), 'claims': claims, 'findings': findings,
    'remaining_scope': [x for x in scope['files'] if x['path'] not in done],
    'validation': ['dag/reviews/additional_paper_001_probes.json', 'dag/reviews/additional_paper_001_empty_census_probe.json', 'dag/reviews/additional_paper_001_notebook_check.json', 'dag/reviews/additional_paper_001_custody.json', 'dag/reviews/paper_001_support_inspection/render_receipt.json'] + ['dag/reviews/' + p for p in test_receipts],
    'test_summary': {'distinct_test_bodies_passed': len(passed), 'additional_subtests_passed': 35,
                     'initial_setup_errors': errors, 'all_initial_error_nodes_later_passed': True,
                     'source_failures': 0, 'provider_calls': 0},
    'paper_quality_assessment': {'decision': 'retain_exact_mathematical_core_with_scoped_claims_and_specific_repairs',
        'useful_contribution': 'Source-bound exact graph-repair certificates and a narrow exact Fock-carrier obstruction; finite controls can inform checker workflow design.',
        'unestablished': 'No measured general reasoning improvement, model cost benefit, arbitrary-representation sign impossibility, or live runtime refinement theorem.',
        'pending': 'Historical receipts, raw model traces, Cargo.lock, manifest contents and all archive member contexts are still separately pending.'},
    'limits': ['Only explicitly listed complete reads count toward substantive coverage; all other scope paths remain pending.',
        'All probes were offline with synthetic provider responses. No credentials, private QM answer, paid calls or native build were used.',
        'Source files and historical evidence remain unchanged; these are review findings, not applied repairs.'],
    'scope_summary': {'files': len(scope['files']), 'full_reads': len(reviews), 'pending': len(scope['files']) - len(reviews), 'pdfs': 8, 'pdf_pages': 88, 'directly_viewed_pdf_pages': 44, 'standalone_pages_with_complete_pixel_equality': 44, 'fresh_notebook_code_cells': 7},
    'external_source_checks': [
        {'url': 'https://web.stanford.edu/~boyd/cvxbook/', 'status': 'author_book_page_verified', 'scope': 'Publication identity and availability, not a fresh formal proof of every cited LP theorem.'},
        {'url': 'https://people.eecs.berkeley.edu/~necula/papers.html', 'status': 'author_publication_record_verified', 'scope': 'POPL1997 identity and stated proof-carrying-code purpose. Author-linked PostScript unavailable through browser; ACM DOI opening returned 403.'},
        {'url': 'https://zenodo.org/records/23114044', 'status': 'not_independently_authenticated', 'scope': 'Direct opening failed and targeted query did not corroborate the record. No absence or fabrication conclusion follows.'},
    ],
}
(OUT / 'additional_paper_001_support.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
lines = [f"Paper001 supporting-package checkpoint: {len(reviews)} of {len(scope['files'])} files fully reviewed.", '',
         'The exact graph certificate checker and fixed Fock-path gap are useful mathematical components under their declared inputs and carriers. They do not establish general workflow improvement or a physical sign-problem classification.', '',
         'All 74 distinct Python test bodies and 35 subtests passed. Four initial temporary-directory setup errors were preserved and the affected bodies passed using a fresh workspace temporary directory. Six offline controls and seven fresh notebook code-cell executions are recorded separately; no paid calls occurred.',
         'All 88 PDF pages have explicit dispositions: 44 pages directly viewed and 44 standalone pages with complete pixel equality. The current package and historical archive are kept separate; archived bindings pass while current manifests drift.', '']
lines += [f"- {f['id']}: {f['statement']}" for f in findings]
lines += ['', 'The JSON report binds every complete read to its frozen SHA-256 and leaves unread supporting material pending. Sources and historical receipts are unchanged.']
(OUT / 'additional_paper_001_support.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps(report['scope_summary']))
