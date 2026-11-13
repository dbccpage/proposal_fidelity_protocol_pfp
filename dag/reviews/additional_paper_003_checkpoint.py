"""Persist incremental Paper003 reading with exact frozen-source bindings."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'dag/reviews'
PREFIX = 'papers/pfp/003_pfp_host_admitted_failure_detectors/'
scope = json.loads((OUT / 'additional_paper_003_support_scope.json').read_text())
pins = {x['path']: x for x in scope['files']}
assessments = {
    'README.md': 'Complete package and reproduction instructions read. October 23 lemma extension is explicitly newer than the historical release PDFs and archive; live extension experiment is NOT_RUN. Native host and canonical private engine implementation have distinct scopes.',
    'paper_claim_ledger.md': 'Every claim, withdrawal and extension read, including P3-23 through P3-25 separately after truncated output. States finite fuel/state/receipt limits, phrase-detector non-admission, supplied-evidence boundary, and three elementary detector lemmas without claiming model accuracy.',
    'pyproject.toml': 'Complete Python dependency, package and pytest configuration read. No environment installation performed.',
    'code/detector_lemmas.py': 'All exact rational two-signal, Hill-gate and finite-mask controls read. Canonical gate collapse needs the stated high-severity self-derived signal; half-activation threshold is K independently of Hill exponent; universal finite-panel safety is exactly executed-mask inclusion in screened-mask. These are conditional finite facts, not detector adequacy or empirical improvement.',
    'code/danger_gate.py': 'Complete supplied-evidence state table read. Package deliberately treats every supplied Signal2 record as present and all co-presence as quarantine, unlike canonical low/medium co-presence and positive-count rules. Dataclass records and confidence are supplied inputs, not validated factual evidence.',
    'code/canaries.py': 'Complete sixteen-substring, four-category scanner read. At most one finding per category; lowercased phrase matches cannot distinguish quotation, negation or truth. Package explicitly labels these candidates unadmitted.',
    'code/self_panel.py': 'Complete synthetic panel generator read. One thousand rows arise from forty templates and twenty-five tagged repetitions; this is not one thousand independent controls or a detector-accuracy sample.',
    'code/host_engine.py': 'All 501 lines read across two complete ranges. Deep-copy rollback, per-attempt fuel, terminal behavior and five explicitly missing native routes reviewed. Receipt verifier checks thirty coordinates and unkeyed event/digest consistency without replaying state, fuel or authorizing mathematical validity. No route currently returns a scoped certificate.',
    'code/native_host_detector.py': 'Complete explicit/discovered native selection, JSON transport, typed refusal and payload parsing read. Present native refusal is not silently replaced by Python. Shape admission does not independently establish native semantic correctness, and scalar field types are weakly checked.',
    'code/demo_checks.py': 'Complete explicit demonstration require helper read. Failed conditions raise even under Python optimization; no removable assert-based evidence.',
    'code/tests/conftest.py': 'Complete local import-path fixture read; no provider calls or mathematical assertion.',
    'code/tests/test_two_signals_one_detector.py': 'All exact tests and finite domains read: four-count derived-signal tables, rational Hill thresholds and all six-bit mask inclusions with nonempty panels. Proof tests remain bounded corroboration of explicit elementary lemmas.',
    'code/tests/test_danger_gate.py': 'All gate, substring, negation, synthetic-panel and optional native-parity tests read. Constructed positives and clean examples do not calibrate deployment precision or recall.',
    'code/tests/test_demo_3_host.py': 'All 404 lines read in two ranges: fuel, rollback, deep alias isolation, owner guard, missing native routes, receipt coordinate/hash refusals and synthetic-panel multiplicity. No claim that receipt consistency proves underlying mathematics.',
    'code/live_proposer_demo.py': 'All 333 lines read. One optional provider request lacks max_tokens, whole-run monetary reservation and usage persistence. Structural JSON parsing supplies Signal2 independently from phrase Signal1; Python JSON nonfinite values can survive parsing and later fail canonical event serialization. Missing credentials or failed query still allow offline fixtures to produce overall PASSED status.',
    'code/run_demos.py': 'Complete aggregate offline runner read. Checks explicit statuses and catches failures, always invokes live=False; native discovery can still select an installed backend.',
    'code/demo1_host_transactions.py': 'Complete transaction demonstration read. Tests rollback/fuel and thirty-cell digest receipt with explicit checks; receipt is consistency evidence, not route certification.',
    'code/demo2_two_signal_gate.py': 'Complete constructed six-case gate demonstration read. Uses available native gate or named Python fallback and explicit status checks; no empirical detector validation.',
    'code/demo3_canaries_audit.py': 'Complete constructed canary and repeated-template panel demonstration read. Explicitly limits its findings to demonstration behavior; no independent real-world labels or calibrated error rates.',
    'code/rust/src/danger_gate.rs': 'Entire native table and three tests read. Typed enum severities and unsigned counts narrow inputs; declared package co-presence and any-record policies match Python for the common typed domain. Supplied evidence is not independently established.',
    'code/rust/src/canaries.rs': 'All sixteen phrases, four detector records, scanner and seven tests read. Lowercase substring semantics preserve the stated non-admission and negation limitations.',
    'code/rust/src/lib.rs': 'Complete package exports read. Explicitly names this as the standalone re-implementation, not the canonical host.',
    'code/rust/src/host.rs': 'Complete host, serializer, rollback branches and three tests read. Mirrors the package finite-fuel behavior on typed inputs; all nonempty routes refuse NO_NATIVE_PORT. Host state is publicly mutable, digest omits initial fuel/full state and arbitrary JSON values have a wider Rust payload type than the Python annotation.',
    'code/rust/src/bin/solve_host_detector.rs': 'Complete stdin JSON command dispatcher and response paths read. CLI run_batch initializes a fresh host per command. Hex parsing slices UTF-8 strings by byte offsets and can panic on even-length non-ASCII input instead of returning its promised error.',
    'code/rust/Cargo.toml': 'All dependency and target declarations read; no native package build or registry retrieval performed.',
    'code/rust/Cargo.lock': 'Complete dependency lock, version-disambiguated syn edges and registry checksums read. Lock declarations are not fresh native execution evidence.',
    'docs/functional_boundary_register.md': 'Complete baseline-specific native ownership and missing-route register read. Separates runtime dispatcher, additive library and restricted host, and excludes global parity claims from their existence.',
    'docs/completion_supplement.md': 'Complete reproduction boundary read. Historical canonical host and standalone re-implementation are explicitly distinguished; no missing witness route is silently upgraded.',
    'docs/review_response.md': 'Complete disposition table read. Rejects conclusions about live effects, semantic authentication and unrestricted physical adapters from scripted protocol receipts.',
    'docs/first_publication_review_2026_10_02.md': 'Complete historical review, repair table, 59-pass/one-skip record, source/harvest/teaching scope and publication boundary read. Its pinned pytest 8.3.5 account differs from current minimum-version metadata; historical results are not current source verification.',
    '.env.example': 'Entire placeholder-only configuration template read. Live execution must be requested and env-file selection is explicit; no actual credential was resolved.',
    'docs/descriptions.md': 'Complete description read. Correctly presents admission/evaluation as proposed and all phrase detectors as unadmitted; the historical-byte preservation claim still requires separate archive comparison.',
    'docs/keywords.md': 'All eight metadata terms read. Component names grant no semantic verification or mathematical novelty.',
    'docs/references.md': 'All seven bibliographic entries read. Six corresponding author arXiv records/abstracts freshly checked, with Troyer-Wiese already verified during Paper002. This validates attribution and broad scope, not all external proofs.',
    'zenodo_metadata.json': 'Every metadata field and full abstract read, separately reread after initial truncation. Mixed text/code licenses are identified. Claimed Zenodo endpoint was inaccessible; publication is unverified here, not disproved.',
    'paper_change_log.md': 'Full dated history read, separately reread after truncation. Later text withdraws stronger early fuel/cryptographic/parity claims. Current metadata, historical receipts and author-review extension have distinct version/source bindings.',
    '_lev_examiner_theoretical_minimum_quiz/.gitkeep': 'Zero-byte marker verified; no mathematical content.',
    '_lev_examiner_theoretical_minimum_quiz/00_preface_at_apartment_50.md': 'Entire fictional teaching preface read. Explicitly disclaims historical examination authority; source_paths retains an obsolete atlas location.',
    '_lev_examiner_theoretical_minimum_quiz/study_guide.md': 'Complete worked guide read: two gate variants, rollback/accounting, sum versus sensor count, predicate implications, three separate physics conditions and statistical denominators. Rational practice example and scope distinctions agree with the manuscript.',
    '_lev_examiner_theoretical_minimum_quiz/quiz.md': 'All twenty-four questions and ninety-six-point rubric read. Demands concrete finite calculations, singleton counterexamples, source binding and experimental design. This is useful pedagogy, not a validated learner metric.',
    '_lev_examiner_theoretical_minimum_quiz/instructor_key.md': 'All twenty-four answers and replay worksheet read. Gate policies, 9/25 Hill value, three contributors under 3/4 cap, signed-triangle distinction, 3/10 success, 2/20 false suppression, and 299/408 confidence thresholds are correctly scoped. Public teaching key is unrelated to the sealed benchmark.',
    'demos/README.md': 'Complete historical-demo boundary read. Raw trace status is distinguished from current canonical missing-port refusals and current package replay.',
    'demos/demo_antimorphic_reversal/README.md': 'Entire historical illustration notice read. Finite legacy adapter/action names do not establish a reversible transition family or native integration.',
    'demos/demo_eis_failure_classes/README.md': 'Entire twelve-positive/twelve-control historical fixture notice read. Class labels and expected dispositions do not establish parity, sensitivity or held-out transfer.',
    'demos/demo_token_frontier/README.md': 'Entire historical rational-masking notice read. Explicit missing native route and absence of a deployed model-generation filter or measured safety effect.',
    'demos/demo_3/3_demo.md': 'Full proposed experiment read, including the omitted middle range reread after truncation. Separates finite gauge, rational membership and pairing routes from physical adapters, distinguishes feedback delivery and assisted controls, and preserves UNKNOWN for partial frontier. Relative Demo1/Demo2 dependencies are not bundled here.',
    'demos/demo_3/experiment_manifest.yaml': 'Every proposed contract, six fixture entries, seven comparisons, detector rule and stopping field read in two ranges. Live disabled, source/model unpinned and frontier explicitly unimplemented. Host-only labels are public teaching data requiring a distinct renderer; this manifest alone enforces neither secrecy nor the stated parser/budget contract.',
}
reviews = []
assessments.update({
    'docs/first_publication_validation_2026_10_02.json': 'All metadata, four execution command records, thirty-three input digests, three PDF commands and trailing fields reviewed. Full current PDF stdout reconstructed exactly from 116 unique lines and complete ordered references; historical microtype warnings and source paths retained. Archive comparison exposes later edits to cwd, hash-key names and captured stdout paths. The historical fifty-nine passes/one skip are separate from the fresh same-count Python run; no current native or provider result follows.',
    'paper.tex': 'All 1,343 lines read, including preamble, both gate policies, canonical-versus-package boundaries, experimental design, three elementary lemmas, source-pinned anti-skill account and bibliography. This TeX is a historical manuscript edition and does not include the later Markdown author-review extension. Mathematical claims remain conditional and do not establish native correspondence or model improvement.',
    'demos/demo_3/traces/holonomy3c_r2b_1790205330.jsonl': 'All three complete records read. Prompt calls (-2,1,1) a differential adjustment that closes cycle (1,2,2), but additive adjustment leaves oriented sum five. Raw numerical host fields remain -1 and admission remains pending/false despite feedback saying ExactRepair. No terminal verified receipt or authenticated provider replay is established.',
    'demos/demo_3/traces/diamond_r4b_1790206003.jsonl': 'All twelve logical records reviewed through full first record and every changed field, with exact reconstruction of repeated prompts. Five assertions are followed by seven identical CUT proposals; two fenced responses are parsed despite raw-JSON instruction. Raw status fields remain pending/false and -1. Declared initial oriented cycle sums are six and four, whereas feedback reports Phi_1 eight; absent a metric/host binding these are not verified defect-reduction outcomes.',
    'docs/validation.md': 'All 103 lines read. Historical 1,472-test aggregation, source/tree pins, source-pattern ownership guard and unavailable native witness routes are distinct from fresh execution. No whole-program or live-model validation follows from this receipt.',
    'validation/ownership_guard.json': 'All fourteen lines and declared pattern counts read. Historical source ownership scan is recorded, not independently rerun or a semantic ownership proof.',
    'MANIFEST.sha256': 'All seventy-seven digest/path rows read and checked separately by custody tooling. Current and archive bindings have distinct results; a digest does not validate mathematical content.',
    'SHA256SUMS': 'All seventy-eight digest/path rows read and checked separately by custody tooling. Current line-ending normalization does not resolve all surviving mismatches.',
    'docs/validation.json': 'All 162 lines and all historical test/source/provenance fields read. Counts are retained historical assertions; current focused tests are recorded separately.',
    'docs/release_validation_2026_10_01.json': 'All seventy-three lines read. Historical Python suite totals and thirteen Rust passes are version-bound evidence, not fresh native-package verification.',
    'docs/release_validation_2026_10_02.json': 'All 103 lines read. Earlier fifteen lemma tests precede later parametrized additions; no conflict with the separately scoped current fifty-nine passes and one native skip.',
    'demos/demo_3/demo_3_live_protocol.ipynb': 'All twelve cells, six code bodies, six Markdown bodies, metadata and empty outputs read. Referenced historical runner is absent from this deposit, so this is an illustrative notebook rather than a standalone executable protocol. No notebook execution performed.',
    'demos/demo_antimorphic_reversal/demo_antimorphic_reversal.ipynb': 'All twelve cells and their metadata/output fields read. Six code bodies depend on an unbundled historical runner and library. Conditional finite cochain/reversal illustrations do not prove general contravariance or native integration; outputs are empty.',
    'demos/demo_token_frontier/demo_token_frontier.ipynb': 'All ten cells and metadata/output fields read. Five code bodies illustrate finite-mask renormalization when retained mass is positive, but imported runner is absent and outputs are empty. No deployed generation-filter result follows.',
    'demos/demo_3/results/live_openrouter_trial_receipt.json': 'Every logical JSON value read through ten full trial bases, all twenty remaining exact deltas and complete header. Reconstruction verifies all thirty trials; remaining trials differ only by seed and receipt envelope hash. Independent rational checks reproduce all forty-eight witness dispositions, fuel accounting, declared 20,382 tokens and interval formulas. Ten distinct trial bodies do not establish thirty independent provider trials; raw requests, full replies, request IDs, costs and elapsed times are absent.',
    'demos/demo_eis_failure_classes/receipt.json': 'All twenty-four fixture records and complete summary read. Twelve designated positives and twelve designated controls are historical constructed labels, not held-out calibration or native parity. Identical subject digests can occur with different external contexts; this receipt alone cannot replay those contexts.',
})
for rel, assessment in assessments.items():
    path = PREFIX + rel
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == pins[path]['sha256'], path
    n = len(data.decode('utf-8-sig').splitlines())
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
                    'reviewed_lines': [[1, n]] if n else [], 'assessment': assessment})
base_prefix = 'papers/pfp/002_pfp_signed_presentations_and_search_frontier/'
base_reviews = {x['path']: x for x in json.loads((OUT / 'additional_paper_002_support.json').read_text())['file_reviews']}
for rel in ['LICENSE', 'LICENSE-CODE', 'code/deposit_paths.py', 'scripts/build_deposit_zip.py',
            'scripts/regen_sha256sums.py', 'tools/rebuild_release.py', 'verify_deposit.py']:
    path, base = PREFIX + rel, base_prefix + rel
    current, previous = (ROOT / path).read_bytes(), (ROOT / base).read_bytes()
    assert base_reviews[base]['full_source_read']
    assert hashlib.sha256(previous).hexdigest() == base_reviews[base]['sha256']
    assert hashlib.sha256(current).hexdigest() == pins[path]['sha256']
    if rel == 'verify_deposit.py':
        assert current == previous.replace(b'Explicitly requested named test files', b'Optional/Default named test files')
    else:
        assert current == previous
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
        'reviewed_lines': [[1, len(current.decode('utf-8-sig').splitlines())]], 'base_path': base,
        'review_method': 'Previously fully reviewed source plus exact byte equality' if current == previous else 'Previously fully reviewed source plus entire one-line docstring delta',
        'assessment': 'Same license or package-relative custody/release implementation as fully reviewed Paper002; no new independent theorem. Optional/Default versus Explicitly requested verifier wording is the sole differing line.'})
trace_bases = json.loads((OUT / 'additional_paper_001_artifacts.json').read_text())['file_reviews']
for name in ['demo2_r1_stoquastic_1790206807.jsonl', 'demo2_r2_freefermion_1790207175.jsonl']:
    path = PREFIX + 'demos/demo_3/traces/' + name
    current = (ROOT / path).read_bytes()
    matches = [x for x in trace_bases if x['sha256'] == pins[path]['sha256'] and x['full_source_read']]
    assert len(matches) >= 1, path
    base = matches[0]
    assert current == (ROOT / base['path']).read_bytes()
    assert hashlib.sha256(current).hexdigest() == pins[path]['sha256']
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
        'reviewed_lines': [[1, len(current.decode('utf-8-sig').splitlines())]],
        'base_path': base['path'], 'base_review': 'dag/reviews/additional_paper_001_artifacts.json',
        'review_method': 'Exact byte equality to fully reviewed Paper001 trace; complete base assessment reread in this context.',
        'assessment': base['assessment']})
render = json.loads((OUT / 'paper_003_support_inspection/render_receipt.json').read_text())
assert sum(len(x['pages']) for x in render['renders']) == 62
for item in render['renders']:
    path = item['pdf']
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == pins[path]['sha256']
    if item['index'] >= 2:
        matches = [x for x in render['standalone_correspondence'] if x['pdf_index'] == item['index']]
        assert len(matches) == len(item['pages']) and all(x['complete_pixel_matches'] for x in matches)
    reviews.append({'path': path, 'sha256': pins[path]['sha256'], 'full_source_read': True,
        'reviewed_lines': [], 'reviewed_pages': [[1, len(item['pages'])]],
        'review_method': 'All fifteen main and sixteen companion pages visually read across eight complete contact sheets; gate-table page additionally viewed at full page scale. Thirty-one other pages transfer by exact complete-pixel equality.',
        'assessment': 'Historical mathematical and teaching content corresponds to the fully read current sources except later names, paths and author-review extension. Main proof text is readable; study-guide page two gate table and instructor-key page three source-pin table have overlapping cells. Historical PDFs are preserved unchanged.',
        'validation': 'dag/reviews/paper_003_support_inspection/render_receipt.json'})
archive = json.loads((OUT / 'additional_paper_003_archive_checks.json').read_text())
review_index = {x['path']:x for x in reviews}
archive_dispositions = []
for member in archive['members']:
    base = member['current_path']
    assert base == PREFIX+'paper.md' or review_index[base]['full_source_read'], base
    archive_dispositions.append({**member,
        'base_reading': 'Complete current manuscript contextual read' if base == PREFIX+'paper.md' else 'Complete support reading receipt in this report',
        'assessment': 'Logical content transferred from fully reviewed current base, exact byte/LF equality or every reviewed difference. Full reverse-hunk reconstruction passed; long changed JSON log lines were read via all exact character replacements against reviewed current logs.'})
assert len(archive_dispositions) == 79
reviews.append({'path':archive['archive'],'sha256':archive['archive_sha256'],'full_source_read':True,
    'reviewed_lines':[],'reviewed_archive_members':79,
    'review_method':'All current bases fully read; all 1,256 difference lines reviewed directly or through exact complete long-line changes, with full reverse-hunk reconstruction. Seven PDFs transfer by byte equality to visually reviewed copies.',
    'assessment':'Historical archive preserves original labels, paths and receipts. Later current edits do not establish new execution. This is full logical-member content assessment, not a ZIP parser or compression proof.',
    'validation':'dag/reviews/additional_paper_003_archive_checks.json'})
done = {x['path'] for x in reviews}
assert done == set(pins) and len(reviews) == len(pins)
report = {
    'schema_version': '1.0', 'status': 'scope_complete', 'source_commit': scope['source_commit'],
    'scope_manifest': 'dag/reviews/additional_paper_003_support_scope.json',
    'file_reviews': sorted(reviews, key=lambda x: x['path']),
    'remaining_scope': [x for x in scope['files'] if x['path'] not in done],
    'archive_member_dispositions': archive_dispositions,
    'claims': [
        {'id': 'PAPER003-DERIVED-SIGNAL-COLLAPSE', 'statement': 'A second signal determined by the first makes the gate a one-input function; with matching presence and fixed high severity it reaches only tolerance or quarantine.', 'status': 'proof_and_complete_implementation_read', 'evidence': [PREFIX + 'paper.md', PREFIX + 'code/detector_lemmas.py'], 'limits': 'Elementary substitution/table result; it does not prove independence or accuracy of actual detectors.'},
        {'id': 'PAPER003-HILL-SUM-THRESHOLD', 'statement': 'For positive K and exponent, a Hill gate is a threshold on the positive-input sum; the half-activation threshold is K. A contributor count requires a per-entry upper bound.', 'status': 'proof_and_exact_integer_exponent_implementation_read', 'evidence': [PREFIX + 'paper.md', PREFIX + 'code/detector_lemmas.py'], 'limits': 'Distinct agents, independence and provenance do not follow from counting positive entries.'},
        {'id': 'PAPER003-PREDICATE-SCREEN-SOUNDNESS', 'statement': 'Screening has no executed hit on every admitted finite panel exactly when the executed predicate implies the screened predicate; avoiding harmless rejection adds the reverse implication.', 'status': 'proof_and_finite_bitmask_implementation_read', 'evidence': [PREFIX + 'paper.md', PREFIX + 'code/detector_lemmas.py'], 'limits': 'Panel-relative property; equality of predicates establishes neither coverage of valid unseen inputs nor a false-suppression rate.'},
        {'id': 'PAPER003-PACKAGE-ROLLBACK-BOUNDARY', 'statement': 'The standalone typed host restores semantic state on a refused batch while retaining its fuel charge and event-chain receipt; all declared witness routes currently refuse with NO_NATIVE_PORT.', 'status': 'complete_source_and_focused_test_read', 'evidence': [PREFIX + 'code/host_engine.py', PREFIX + 'code/rust/src/host.rs'], 'limits': 'Charged batches only; no total bytes/time/money bound, witness certificate, authenticated producer or native/Python refinement proof.'},
    ],
    'findings': [
        {'id': 'PAPER003-EDITED-HISTORICAL-RECORDS', 'severity': 'provenance_gap', 'statement': 'The four dated validation JSONs and ownership guard have later role/path substitutions, including command cwd, input-hash key names, captured compiler stdout, suite names and owner paths. Original archived records remain intact. Label current copies as edited transcriptions with explicit mapping; preserving dates is not preservation of original bytes. This is not evidence of fabricated historical test outcomes.', 'evidence': [PREFIX+'docs/first_publication_validation_2026_10_02.json',PREFIX+'docs/release_validation_2026_10_01.json',PREFIX+'docs/release_validation_2026_10_02.json',PREFIX+'docs/validation.json',PREFIX+'validation/ownership_guard.json'], 'validation':'dag/reviews/additional_paper_003_archive_checks.json'},
        {'id': 'PAPER003-PINNED-PATH-RENAMING', 'severity': 'version_binding_gap', 'statement': 'Current prose and TeX replace historical module names inside commit-pinned source URLs and command paths without changing commit IDs; Markdown uses pfp where TeX uses symbol_game. The archive retains original omega_engine paths. Reproduction needs a versioned old-to-current map, not a silent substitution within a historical citation. Historical PDF bytes also predate the October23 Markdown extension.', 'evidence': [PREFIX+'paper.md',PREFIX+'paper.tex',PREFIX+'docs/review_response.md'], 'validation':'dag/reviews/paper_003_support_inspection/archive_complete_text_diffs.txt'},
        {'id': 'PAPER003-HISTORICAL-TRACE-CONTRACT', 'severity': 'historical_protocol_gap', 'statement': 'The three-cycle prompt advertises a differential adjustment whose sum is zero as closing initial holonomy five; under additive semantics the holonomy remains five. The diamond prompt initial cycle-sum norm is ten while feedback reports eight. All fifteen raw trace rows retain pending/false admission and -1 numerical fields. Preserve these as historical proposals/feedback, not checked execution results; a different quotient metric would need its own explicit binding.', 'evidence': [PREFIX + 'demos/demo_3/traces/holonomy3c_r2b_1790205330.jsonl', PREFIX + 'demos/demo_3/traces/diamond_r4b_1790206003.jsonl'], 'validation': 'dag/reviews/paper_003_support_inspection/historical_trace_arithmetic.json'},
        {'id': 'PAPER003-HISTORICAL-TRIAL-REPLICATION', 'severity': 'empirical_evidence_gap', 'statement': 'Thirty historical trial records reduce to ten distinct bodies after seed and envelope hash removal; snippets, usage and state digests repeat exactly across three seeds. All forty-eight finite witness dispositions and aggregate arithmetic reproduce, but this cannot establish thirty independent model calls or a causal improvement. The receipt lacks request IDs, full prompts/replies, money and latency. Repetition alone is not proof of fabrication.', 'evidence': [PREFIX + 'demos/demo_3/results/live_openrouter_trial_receipt.json'], 'validation': 'dag/reviews/additional_paper_003_historical_checks.json'},
        {'id': 'PAPER003-NOTEBOOK-DEPENDENCIES', 'severity': 'reproduction_gap', 'statement': 'The three historical notebooks import runners absent from the deposit and retain only empty output cells. Their finite illustrations remain useful, but standalone executable demonstration claims require bundled, pinned dependencies and fresh receipts.', 'evidence': [PREFIX + 'demos/demo_3/demo_3_live_protocol.ipynb', PREFIX + 'demos/demo_antimorphic_reversal/demo_antimorphic_reversal.ipynb', PREFIX + 'demos/demo_token_frontier/demo_token_frontier.ipynb']},
        {'id': 'PAPER003-LIVE-ACCOUNTING', 'severity': 'benchmark_admission_gap', 'statement': 'Live request has no max_tokens or whole-run monetary reservation and returns only text, discarding supplied usage. Route through the guarded benchmark transport before any paid comparison.', 'evidence': [PREFIX + 'code/live_proposer_demo.py'], 'validation': 'dag/reviews/additional_paper_003_probes.json'},
        {'id': 'PAPER003-LIVE-FAILURE-OVERALL-PASS', 'severity': 'execution_evidence_gap', 'statement': 'Missing credentials or a failed live query still lead to overall PASSED and zero CLI exit after four offline examples. Nested acquisition status is explicit, but the top-level result cannot be treated as successful live execution.', 'evidence': [PREFIX + 'code/live_proposer_demo.py'], 'validation': 'dag/reviews/additional_paper_003_probes.json'},
        {'id': 'PAPER003-NONFINITE-PARSER-ESCAPE', 'severity': 'input_refusal_gap', 'statement': 'Python JSON parsing accepts a NaN witness payload without a structural defect; later allow_nan=False event serialization raises outside the wrapper instead of returning a structured refusal. A public synthetic response reproduces this.', 'evidence': [PREFIX + 'code/live_proposer_demo.py', PREFIX + 'code/host_engine.py'], 'validation': 'dag/reviews/additional_paper_003_probes.json'},
        {'id': 'PAPER003-NATIVE-HEX-UTF8-PANIC', 'severity': 'input_refusal_gap', 'statement': 'The native hex helper slices arbitrary UTF-8 text at two-byte offsets. Even-byte-length a-é-a panics inside a codepoint instead of returning an invalid-hex refusal. Exact isolated source compilation reproduces it; full native package was not built.', 'evidence': [PREFIX + 'code/rust/src/bin/solve_host_detector.rs'], 'validation': 'dag/reviews/additional_paper_003_probes.json'},
        {'id': 'PAPER003-CURRENT-MANIFEST-DRIFT', 'severity': 'custody_gap', 'statement': 'Current MANIFEST.sha256 and SHA256SUMS have 44/45 raw mismatches, of which 26/27 survive universal LF normalization. All archived bindings pass. Archive logical contents now have separate full reading and exact reconstruction evidence; hash agreement alone would not complete that review.', 'evidence': [PREFIX + 'MANIFEST.sha256', PREFIX + 'SHA256SUMS'], 'validation': 'dag/reviews/additional_paper_003_custody.json'},
        {'id': 'PAPER003-EXTENSION-LINK-DRIFT', 'severity': 'navigation_gap', 'statement': 'Author-review extension links still target ../029_pfp_evidence_bound_harness_evolution rather than the current 019 directory. Historical Demo1/Demo2 relative dependencies and atlas source_paths also require explicit current-location guidance.', 'evidence': [PREFIX + 'paper.md', PREFIX + 'demos/demo_3/3_demo.md', PREFIX + '_lev_examiner_theoretical_minimum_quiz/study_guide.md']},
        {'id': 'PAPER003-PDF-TABLE-OVERLAP', 'severity': 'rendering_defect', 'statement': 'Study-guide page 2 (companion page 3) overlaps severity, exact decision and refusal columns, obscuring the gate table. Instructor-key page 3 (companion page 9) overlaps full commit hashes with their descriptions. Markdown retains the complete data; preserve historical PDFs and repair a newly bound edition.', 'evidence': [PREFIX + '_lev_examiner_theoretical_minimum_quiz/study_guide.pdf', PREFIX + '_lev_examiner_theoretical_minimum_quiz/instructor_key.pdf', PREFIX + '003_pfp_examiner_companion.pdf'], 'validation': 'dag/reviews/paper_003_support_inspection/render_receipt.json'},
    ],
    'validation': ['dag/reviews/additional_paper_003_tests.xml', 'dag/reviews/additional_paper_003_probes.json', 'dag/reviews/additional_paper_003_custody.json', 'dag/reviews/additional_paper_003_historical_checks.json', 'dag/reviews/paper_003_support_inspection/artifact_reading_preparation.json'],
    'provider_calls': 0, 'private_answer_access': False,
    'limits': 'Complete eighty-file supporting slice and contextual current-manuscript review, including three notebooks, four traces, full TeX, thirty-trial receipt, 62 PDF pages and 79 archive logical contents. Runtime results remain scoped to fifty-nine Python passes, one native skip, seven isolated controls and independent historical rational/arithmetic checks. No notebook, full native package, provider, private answer or original-source mutation. This does not complete the broader repository audit or establish model improvement.',
}
cases = list(ET.parse(OUT / 'additional_paper_003_tests.xml').iter('testcase'))
assert len(cases) == 60 and sum(x.find('skipped') is not None for x in cases) == 1
assert all(x.find('failure') is None and x.find('error') is None for x in cases)
report['test_summary'] = {'passed': 59, 'skipped_native_parity': 1, 'native_explicitly_disabled_for_python_run': True,
    'setup_failures_before_collection': 4, 'setup_resolution': 'Preload stdlib pdb before pytest importlib-mode conftest loading.',
    'isolated_probes': 7, 'full_native_build': False}
report['paper_quality_assessment'] = {'decision': 'retain_useful_scoped_methods_and_elementary_lemmas_repair_reproduction_and_provenance',
    'contribution': 'Precise detector admission obligations, three small proofs, explicit missing-route boundary and a proposed controlled evaluation. These contribute reusable falsifiers and experiment design.',
    'unestablished': 'Admitted active detector benefit, generic hallucination reduction, benchmark resource cap, historical receipt authenticity or completed native integration.'}
report['external_reference_checks'] = [{'url': 'https://arxiv.org/abs/' + ident, 'status': 'author_record_and_abstract_verified',
    'limit': 'Bibliography and broad scope only; external full proofs not independently audited.'}
    for ident in ['2303.11366v4', '2303.17651v2', 'cond-mat/0407272v3', '1601.05780', '1601.01994', 'cond-mat/9902128']]
report['external_reference_checks'].append({'url': 'https://zenodo.org/records/23114331', 'status': 'endpoint_inaccessible', 'limit': 'No inference of nonpublication.'})
(OUT / 'additional_paper_003_support.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
(OUT / 'additional_paper_003_support.md').write_text(
    f"Paper003 support review complete: {len(reviews)}/{len(pins)} full logical contents read; {len(report['remaining_scope'])} pending in this slice.\n\n" + report['limits'] + '\n\n' +
    '59 Python tests passed with one deliberately skipped native parity check. Four initial setup failures occurred before collection; their launcher cause was resolved without source changes. Seven isolated controls are separate evidence; no provider or private answer access.\n\n' +
    '\n\n'.join(x['id'] + ': ' + x['statement'] for x in report['findings']) + '\n', encoding='utf-8')
print(json.dumps({'full': len(reviews), 'pending': len(report['remaining_scope'])}))
