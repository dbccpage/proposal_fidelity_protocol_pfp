"""Compile completed Paper009 reads and bounded offline observations; preserve originals."""
import collections
import hashlib
import json
import zipfile
from pathlib import Path

H = Path(__file__).resolve().parent
R = H.parents[1]
P = 'additional_paper_009_support'
BASE = 'papers/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates/'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def load(suffix):
    return json.loads((H / (P + suffix)).read_text(encoding='utf-8'))

def save(suffix, value):
    (H / (P + suffix)).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

scope = load('_scope.json')
scope_hash = sha((H / (P + '_scope.json')).read_bytes())
rows = {row['path']: row for row in scope['files']}
reviews = [row for row in load('.json')['file_reviews'] if row['full_source_read']]
assert len(rows) == 66 and len(reviews) == 55
for row in reviews:
    row['review_level'] = 'full_body_semantic_review_with_explicit_base_delta_transfer_when_recorded'
full = {row['path']: row for row in reviews}
custody = load('_custody.json')
bindings = load('_binding_checks.json')
pdf = load('_pdf_review.json')
probes = load('_probes.json')
followup = load('_followup_probes.json')

def evidence(name, *ranges, pages=None):
    path = BASE + name
    item = {'path': path, 'sha256': sha((R / path).read_bytes()), 'lines': [list(pair) for pair in ranges]}
    if pages:
        item['pages'] = pages
    return item

def record(identifier, statement, sources, **kwargs):
    return {'id': 'PAPER009-' + identifier, 'statement': statement, 'source_evidence': sources,
            'evidence': [item['path'] for item in sources], **kwargs}

def bounded(path, assessment, level, **kwargs):
    return {'path': path, 'sha256': rows[path]['sha256'], 'full_source_read': False,
            'reviewed_lines': [], 'review_level': level, 'assessment': assessment, **kwargs}

for item in pdf['pdfs']:
    assessment = ('Every rendered page is accounted through direct visual reading or explicit complete raw/RGB equality. '
                  'The retained October2 manuscript presents exact triangle arithmetic, historical-label recounts and narrow formal contracts; '
                  'it is distinct from the October23 Markdown extension. Historical role/path names remain in these PDFs. '
                  'No material clipping observed at review resolution; no binary PDF-source reading claim.')
    if 'companion' in item['path']:
        assessment += ' Combined order is preface, guide, answer key (pages5-7), quiz (pages8-10), contrary to attempt-before-key instructions.'
    elif '_minimum_quiz/' in item['path']:
        assessment += ' Instructional worked examples and practice rubric are not a learner study or independently graded benchmark.'
    reviews.append(bounded(item['path'], assessment, 'complete_rendered_page_visual_review_not_pdf_binary_source', page_review=item))

manifest_counts = []
for manifest in custody['current_manifests']:
    count = len(manifest['entries'])
    raw = sum(not item['raw_match'] for item in manifest['entries'])
    unresolved = sum(not (item['raw_match'] or item.get('lf_match')) for item in manifest['entries'])
    manifest_counts.append((raw, unresolved))
    reviews.append(bounded(BASE + manifest['path'],
        f'All {count} parsed identity records checked against current files: {raw} raw mismatches, {unresolved} unresolved after LF normalization. '
        'Normalization diagnoses newline drift and does not establish exact byte identity. Archived internal manifest validates; original hashes not regenerated. '
        'Manifest textual differences received automated record comparison, not full manual diff reading.',
        'all_records_parsed_and_identity_checked_not_full_manual_text', records=count,
        raw_mismatches=raw, unresolved_after_lf=unresolved, detail_receipt='dag/reviews/' + P + '_custody.json'))
assert manifest_counts == [(34, 21), (35, 22)]
reviews.append(bounded(BASE + 'lean4/full_axiom_report.txt',
    'All 516 unique declaration records parsed: 491 no axioms, 21 propext, 4 Quot.sound+propext; no Classical.choice. '
    'Includes generated/private declarations from four roots, not 516 distinct manuscript theorems. '
    'Historical report matches protected digest only after LF normalization; no current Lean execution. All524 raw text lines were not manually read.',
    'all_declaration_rows_parsed_and_axiom_sets_checked_not_full_manual_text', declarations=516,
    detail_receipt='dag/reviews/' + P + '_binding_checks.json'))

prior_md = scope['excluded_prior_full_reads'][0]
prior_report_path = H / 'papers_audit.json'
prior_entry = next(item for item in json.loads(prior_report_path.read_text(encoding='utf-8'))['files'] if item['path'] == prior_md['path'])
assert prior_entry['sha256'] == prior_md['sha256'] and prior_entry['review_status'] == 'full-text-read'

# Complete changed-source bodies were read before this compilation. Manifest bases remain parsed artifacts.
delta_assessments = {
    5: 'Historical README omits the later author-review extension and uses original package/role names; count and replay limits remain edition-specific.',
    7: 'Preface role names and source namespace differ; attempt-before-key pedagogical instruction remains explicit.',
    9: 'Answer-key role/namespace naming differs; historical arithmetic and declared digest-success answer are evaluated against archived records.',
    11: 'Quiz role/namespace naming differs; historical command and exercise wording preserved.',
    13: 'Guide role/namespace naming differs; exact worked exercise and evidence boundaries retained.',
    21: 'Archived test refers to the original private gate-falsifier filename, matching that archive member.',
    24: 'Historical completion supplement uses the original source namespace; present adaptation does not create a new historical run.',
    25: 'Description role label renamed; empirical and formal ceilings unchanged.',
    29: 'Archived provenance retains original gate filename and source paths; its three SHA/Git identities validate archived members exactly.',
    30: 'Archived gate-record namespace remains private engine; current translation changes the digest although observations are retained.',
    31: 'Keyword namespace/role wording differs; indexing metadata does not change checker behavior.',
    33: 'Archived first release receipt retains original command/source paths and author labels; these are dated historical outputs.',
    34: 'Archived second release receipt retains original command/source paths and protected compiler identities; no fresh build transfer.',
    35: 'Archived v0.1 review retains original receipt paths/author references; its historical success is tested separately on archived bytes.',
    47: 'Archive pins Lean4.34.0; current loose toolchain pins4.35.0. Historical formal checks cannot certify the new compiler run.',
    48: 'Archived Markdown is the October2 v0.1 edition; current October23 v0.2 adds an explicitly unmeasured author-review harness and renamed source references. Complete145-line diff read; previously truncated lines84-110 recovered separately.',
    50: 'Archived TeX retains old namespace/role labels; both TeX bodies retain the October2 paper rather than the later Markdown extension.',
    51: 'Archived chronology stops before later author-review extension and namespace updates; historical assertions kept separate from current state.',
    52: 'Archived claim ledger lacks later author-review extension; original empirical/proof limitations are retained.',
    58: 'Archived renderer searches Jeremy H. Carroll, consistent with archived header; current renderer instead requires Bare Metal Anchor and fails on the present header.',
    62: 'Archived capstone uses original gate filename/namespace, matching its exact provenance inputs; current adapted file fails raw custody before recount.',
    64: 'Archived metadata retains original title/role names; no external deposit status independently verified.'
}
zip_reviews = []
delta_receipts = []
with zipfile.ZipFile(R / custody['archive_path']) as archive:
    assert archive.testzip() is None
    names = archive.namelist()
    assert len(names) == 65 and len(set(names)) == 65
    assert all(not name.startswith(('/', '\\')) and '..' not in Path(name).parts for name in names)
    for item in custody['zip_members']:
        raw = archive.read(item['member'])
        assert sha(raw) == item['sha256']
        path = item['current_path']
        assert item['current_exists'] and sha((R / path).read_bytes()) == item['current_sha256']
        is_full = path in full or path == prior_md['path']
        base_assessment = (full[path]['assessment'] if path in full else
                           'Prior matching full manuscript read; archived edition assessed through complete current/archive differences.' if path == prior_md['path'] else
                           next(row['assessment'] for row in reviews if row['path'] == path))
        result = {**item, 'full_source_read': is_full,
                  'reviewed_lines': [[1, len(raw.decode('utf-8').splitlines())]] if is_full and raw else [],
                  'assessment': base_assessment}
        if item.get('complete_diff_path'):
            diff_path = R / item['complete_diff_path']
            assert sha(diff_path.read_bytes()) == item['complete_diff_sha256']
            index = int(diff_path.stem.rsplit('_', 1)[1])
            manual = index in delta_assessments
            assert manual == is_full and (manual or index in (4, 6))
            delta = {'path': item['complete_diff_path'], 'sha256': item['complete_diff_sha256'],
                     'reviewed_lines': [[1, item['complete_diff_lines']]] if manual else [],
                     'full_diff_read': manual, 'base_body_full_read': is_full,
                     'assessment': delta_assessments.get(index, 'Parsed manifest identity comparison only; no manual full-diff or full-base reading receipt.')}
            delta_receipts.append(delta)
            result['delta_reading'] = delta
            result['transfer_method'] = ('Complete fully reviewed current/prior body plus every changed line in complete diff.' if manual else
                                         'All manifest rows parsed and checked; base and diff remain bounded artifact review.')
            if manual:
                result['assessment'] = delta['assessment'] + ' Base body context: ' + base_assessment
        else:
            assert item['current_raw_equal'] or item.get('current_lf_equal')
            result['transfer_method'] = ('Raw equality or complete newline-normalized body equality to a fully read current source; byte equality separately recorded.' if is_full else
                                         'Equality transfers the bounded artifact disposition only, never a full text-reading receipt.')
        if path == prior_md['path']:
            result['base_reading_receipt'] = {'path': 'dag/reviews/papers_audit.json', 'sha256': sha(prior_report_path.read_bytes()), 'entry': prior_entry}
        zip_reviews.append(result)
assert len(zip_reviews) == 65 and sum(row['full_source_read'] for row in zip_reviews) == 55
assert len(delta_receipts) == 24 and sum(row['full_diff_read'] for row in delta_receipts) == 22
save('_zip_delta_reading.json', delta_receipts)
reviews.append(bounded(custody['archive_path'],
    'All65 unique safe regular members CRC-checked and SHA-bound; internal manifests63/64 entries have zero mismatches. '
    '55 textual member bodies reviewed via complete full base and exact equality/all differences;10 members remain bounded artifacts. '
    'All22 source-body differences manually read; two manifest differences only parsed/compared. Exact archived tests pass26 and capstone passes. '
    'Integrity consistency is not publisher authenticity or new historical model execution.',
    'all_members_accounted_with_55_full_text_body_transfers_and_10_bounded_artifacts', members=65,
    full_text_member_bodies=55, bounded_member_artifacts=10, detail_receipt='dag/reviews/' + P + '_custody.json'))
assert len(reviews) == 66 and len({row['path'] for row in reviews}) == 66

claims = [
    record('EXACT-TRIANGLE-INVARIANT',
        'For the declared oriented triangle, the sum of a potential difference is zero by telescoping. Subtracting it preserves the input cycle sum. The exact fixture h=(1/3,1/3,1/3), f=(0,1/3,2/3) gives residual(0,0,1), sum1; replacing h by df instead changes the problem to sum0. This is the same reusable cochain mechanism already present in Paper007.',
        [evidence('code/triangle_cycle_sum.py', (1,47)), evidence('code/tests/test_triangle_cycle_sum.py', (1,46))],
        status='complete_source_review_and_fresh_offline_fixture_tests', limits='Fixed exact rational triangle and stated algebra; no general minimal-repair algorithm or physical semantics.'),
    record('EXACT-HISTORICAL-RECOUNT',
        'The ten supplied labels and CHALLENGE/CONCUR verdicts give6TP,0FN,2FP,2TN, with exact fractions1,1/2,3/4,4/5 for the four explicitly named denominators. Actual Boolean labels/status consistency are checked, zero denominators returnNone, and the constant caught flag is deliberately ignored. Changed-verdict and ignored-flag controls test this recount.',
        [evidence('code/review_counts.py', (1,61)), evidence('code/tests/test_review_counts.py', (1,96)), evidence('tools/review_capstone.py', (1,57))],
        status='complete_source_review_and_fresh_current_arithmetic_and_archived_capstone', limits='Descriptive association with supplied historical checker labels, not independently established truth or population/model performance.'),
    record('FINITE-FORGETFUL-COUNTERMODEL',
        'Two stipulated PromptWorld constructors map to the same Unit packet shape but to opposite Boolean truth labels; no Unit-to-Bool function can factor those labels. This is a valid finite nonfactorization witness under those definitions.',
        [evidence('lean4/SLevel.lean', (99,121))], status='complete_written_Lean_proof_body_review_historical_receipt_only',
        limits='A deliberately lossy finite encoding; not a theorem that every packetization loses semantic truth or arbitrary natural language cannot be faithfully encoded. No fresh Lean run.'),
    record('TRIGGER-DOES-NOT-SUPPLY-LICENSE',
        'The exhibited SLevel has liftBudget0 and both trigger flags true. Every LicensedLift requires a strictly smaller natural budget, so this source has no licensed target. This demonstrates trigger-population does not imply a lift license, rather than merely rejecting one chosen target.',
        [evidence('lean4/SLevel.lean', (18,43)), evidence('lean4/TriggerNotLicense.lean', (17,63))],
        status='complete_written_Lean_proof_body_review_and_exact_Nat_reasoning', limits='Finite non-implication under the declared licensing contract; not all triggers unlicensed, not a real authority oracle, no current kernel execution.'),
    record('CONTRACT-FIDELITY-IS-CONDITIONAL',
        'PacketizationContract requires successful compilation to preserve six supplied strings and assign authorityEffect.none. The two preservation results project that assumed sound field. LicensedLift similarly packages next-level, decreasing-budget and increasing-declared-mass obligations.',
        [evidence('lean4/SLevel.lean', (30,51), (53,97))], status='complete_definition_and_proof_body_review',
        limits='Useful explicit admission obligations, not a constructed faithful semantic compiler, external authority, or verified caller implementation.'),
    record('BOUNDED-CPYTHON-NOTEBOOK-REPLAY',
        'The exact embedded CPython worker and comparator execute all five ordinary notebook code cells in a fresh subprocess with assertions enabled and cleared stored outputs/counts. Current and archived cell source/position/count/output comparisons pass in a stdlib-JSON fallback; changing the expected output only in memory is rejected.',
        [evidence('tools/replay_notebook.py', (1,160)), evidence('jupyter_notebooks/009_triangle_cycle_sum.ipynb', (1,207))],
        status='complete_raw_notebook_source_read_and_fresh_bounded_fallback_execution',
        limits='Official package replay is blocked by missing nbformat. Fallback is not nbformat validation, Jupyter/IPython replay, sandboxing, dependency-integrity certification or a learner outcome.')
]

findings = [
    record('CURRENT-CUSTODY-DRIFT',
        'Current MANIFEST has34 raw mismatches among63 entries and SHA256SUMS35 among64;21/22 remain after LF normalization. Fresh default verification fails with35 issues, and current capstone fails before recount. The four non-notebook current test files pass17 and fail9 custody assertions; the exact archived counterpart passes26 and capstone passes. Both ZIP internal manifests validate.',
        [evidence('MANIFEST.sha256'), evidence('SHA256SUMS'), evidence('code/tests/test_recorded_bout_counts.py', (1,116)), evidence('code/tests/test_review_counts.py', (1,96)), evidence('tools/review_capstone.py', (14,24))],
        severity='current_reproduction_failure', recommended_action='Preserve the original archive and receipts. Prepare a separate versioned current edition with explicit old/new paths and byte identities before regenerating current manifests or expected digests; do not overwrite history to hide drift.'),
    record('RENDERER-AUTHOR-HEADER',
        'Current render_paper.render searches for an author line beginning Bare Metal Anchor, while current paper.md contains Jeremy H. Carroll. A guarded call raises StopIteration before any subprocess or file write. Archived renderer instead searches Jeremy H. Carroll and therefore does not share this particular mismatch.',
        [evidence('tools/render_paper.py', (24,35)), evidence('paper.md', (1,7))],
        severity='reproducible_current_code_defect', recommended_action='For an authorized new edition, parse a declared author metadata field rather than a hardcoded identity and add a focused header admission check. Preserve original renderer/PDF bytes; no repair or native rendering performed in this audit.'),
    record('FORMAL-LABELS-EXCEED-ENCODINGS',
        'Level15 advertises15 authority theorems but contains nine numbered theorem bodies. Independence is defined only as unequal Nat parameter hashes; trace extension ignores its extension; replay is hashVal%997 congruence; zero integer gap establishes equality without feasibility; terminalization branches on a supplied defect count. Runtime redaction returns four safe flags without processing event content, and calibration bounds falseRefusals by a supplied budget while benignTotal is unused. These proofs are valid narrow facts and do not certify the broader named mechanisms.',
        [evidence('lean4/Level15AuthorityCalculus.lean', (4,17), (50,89), (116,140), (173,192)), evidence('lean4/RuntimeLimits.lean', (1,190))],
        severity='mathematical_and_runtime_scope_boundary', recommended_action='Reuse actual constructor distinctions, finite budget descent and conditional record invariants under precise names. A real independent checker, redactor, statistical calibration or feasible optimality certificate needs new encodings, predicates, data and implementation-to-proof links.'),
    record('PROTECTED-HISTORY-EDITION-BINDING',
        'None of the three historical record digests match current raw bytes; trace and receipt match after LF normalization, while renamed gate content also differs. All three archived records match expected SHA and Git blobs. Of13 protected review artifacts,7 match raw and10 after LF normalization; four formal modules remain raw-equal, but the toolchain changed4.34 to4.35 and release receipts were adapted. Retained PDFs/TeX and current Markdown also describe different dated editions.',
        [evidence('docs/historical_evidence/provenance.json', (1,39)), evidence('docs/v01_review_2026_10_02.json', (1,287)), evidence('lean4/lean-toolchain', (1,1)), evidence('README.md', (1,109))],
        severity='historical_receipts_not_current_execution', recommended_action='Keep exact archived identities as historical records and record an explicit adaptation map for the current edition. A current compiler/proof claim requires its own source-bound execution; do not transplant old successes to renamed or changed inputs.'),
    record('RECOUNT-AND-GATE-EVIDENCE-CEILINGS',
        'The old caught flag is true in allten trials, including concurrence; it is not a correct positive-detection label. The later retained replay refuses allten but does not pin its checker revision. Five stored gate observations expose four specific historical failure families, yet inspecting those records does not rerun those external owners. Toy gate tests consume supplied strings, counters and flags rather than calculate semantic truth. Modern manuscript and claim ledger appropriately narrow these older interpretations.',
        [evidence('docs/historical_evidence/demo2_r7_adversarial_debate_receipt.json', (1,162)), evidence('docs/historical_evidence/adversary_gate_falsifiers.json', (1,78)), evidence('docs/historical_evidence/README.md', (1,19)), evidence('code/tests/test_009_adversarial_reality_gate.py', (1,130)), evidence('paper_claim_ledger.md', (1,68))],
        severity='empirical_and_checker_adequacy_boundary', recommended_action='Reuse finite counterexample/control designs with new independently labelled inputs and pinned actual checkers. Preserve historical assertions and corrections; do not use supplied answer-bearing records as new sealed benchmark inputs or claim general model capability.'),
    record('NOTEBOOK-DEPENDENCY-AND-REPLAY-BOUNDARY',
        'Initial full package test collection and the documented CPython notebook command fail because nbformat is absent in this environment. No dependency installation occurred. The narrower stdlib fallback succeeds for allfive cells in both editions and rejects changed expected output, but it bypasses notebook schema validation. The replay owner compares code source/output/position/count, not imported-module hashes, Markdown or metadata, and ordinary exec does not emulate IPython display.',
        [evidence('tools/replay_notebook.py', (1,160)), evidence('code/tests/test_notebook_replay.py', (1,72)), evidence('pyproject.toml', (1,39))],
        severity='environment_and_validation_scope_limit', recommended_action='For a documented full replay, use a separately approved environment with the declared notebook dependencies and bind local imported modules as inputs. Preserve this fallback result as a bounded check; do not report the official replay or notebook suite as passed.'),
    record('COMPANION-KEY-BEFORE-QUIZ',
        'The combined companion places the answer key on pages5-7 and the quiz on pages8-10, although the current preface directs guide then quiz before key. All40 retained PDF pages were reviewed directly or via exact complete equality; no material clipping observed at review resolution. The80-point practice rubric does not establish independently measured competence.',
        [evidence('009_pfp_examiner_companion.pdf', pages=[1,5,6,7,8,9,10]), evidence('_lev_examiner_theoretical_minimum_quiz/00_preface_at_apartment_50.md', (17,21)), evidence('_lev_examiner_theoretical_minimum_quiz/quiz.md', (1,125))],
        severity='document_usability_and_evaluation_boundary', recommended_action='In a separately versioned teaching edition, put the attempted quiz before the worked key and make answer exposure explicit. Preserve historical PDF bytes; do not infer validated learning from self-study scoring.')
]

summary = {'assigned_paths': 66, 'full_source_bodies': 55, 'bounded_artifacts': 11,
           'bounded_types': {'pdf': 7, 'zip': 1, 'hash_manifest': 2, 'historical_axiom_listing': 1},
           'zip_members': 65, 'zip_full_text_bodies_via_explicit_transfer': 55, 'zip_bounded_artifacts': 10,
           'complete_manually_read_archive_diffs': 22, 'parsed_manifest_diffs': 2,
           'pdf_pages': 40, 'direct_visual_pdf_pages': 20, 'raw_equal_pdf_pages': 10,
           'pixel_equal_pdf_pages': 10, 'excluded_prior_full_manuscript': 1}
tests = {'current_non_notebook': '17 passed,9 custody failures across four read-vetted test files',
         'archive_same_non_notebook': '26 passed', 'current_default_verifier': 'exit1;35 custody issues',
         'current_capstone': 'exit1; retained trace raw digest mismatch', 'archive_capstone': 'PASS;6/0/2/2 and exact1,1/2,3/4,4/5',
         'initial_full_test_collection': 'exit2;missing nbformat', 'official_notebook_command': 'exit1;missing nbformat',
         'bounded_notebook_fallback': 'current5 and archive5 ordinary cells match all code source/position/count/output; wrong expected output rejected',
         'renderer_guarded_call': 'StopIteration before any subprocess/write;0 native calls',
         'named_census_generation_only': 'exit0;not Lean execution',
         'receipts': ['dag/reviews/' + P + '_probes.json', 'dag/reviews/' + P + '_followup_probes.json'],
         'historical': 'Dated16/33-test, Lean4.34 and external66/44 gate-test assertions are historical retained records, never fresh executions in this audit.'}
report = {'schema_version': '1.0', 'status': 'complete_with_explicit_artifact_bounds',
          'source_commit': scope['source_commit'], 'scope_manifest': 'dag/reviews/' + P + '_scope.json',
          'scope_summary': summary, 'file_reviews': sorted(reviews, key=lambda row: row['path']),
          'remaining_scope': [], 'claims': claims, 'findings': findings, 'zip_member_reviews': zip_reviews,
          'context_reads': [{'path': prior_md['path'], 'sha256': prior_md['sha256'], 'receipt': 'dag/reviews/papers_audit.json',
                             'method': 'Previously matching full manuscript read, excluded from55 new body count; complete145-line archive/current difference reviewed, current header rechecked.'}],
          'method': ['Every assigned executable, proof, prose, raw notebook and small receipt body fully reviewed directly or via explicit full prior base plus exact equality/complete differences. Exact source hashes/ranges and substantive assessments are retained.',
                     'The prior Paper001 full reading of allten raw trace records transfers only through exact byte equality and Paper009-specific recount/context assessment; it is not independent replication.',
                     'All65 ZIP members accounted;22 source diffs manually read, two manifest diffs remain parsed comparisons. A bounded base never becomes full through equality.',
                     'All40 PDF pages accounted through20 direct visual pages,10 raw-equal pages and10 exact rendered-RGB-equal pages. Binary PDF/ZIP raw-source reading is not claimed.',
                     'Full axiom listing and two hash manifests receive all-record parsed checks, not full manual body receipts. No provider, native render, Lean build or external historical gate replay.'],
          'custody_summary': {'zip_internal_manifest_mismatches': 0, 'current_manifest_raw_mismatches': [34,35],
                              'current_manifest_unresolved_after_lf': [21,22], 'historical_records_raw_current': '0/3',
                              'historical_records_raw_or_lf_current': '2/3', 'historical_records_raw_and_git_archived': '3/3',
                              'protected_artifacts_raw_current': '7/13', 'protected_artifacts_raw_or_lf_current': '10/13',
                              'four_formal_module_sources_raw_current': '4/4',
                              'details': ['dag/reviews/' + P + '_custody.json', 'dag/reviews/' + P + '_binding_checks.json']},
          'test_summary': tests,
          'workflow_reuse': [
              {'mechanism': 'Exact cycle-sum invariant and task-preserving potential subtraction', 'prerequisites': 'Explicit edge orientation, rational input admission and independent task binding. General graph or QM transfer requires a new graph/physical encoding; replacement by an easier input is not repair.'},
              {'mechanism': 'Strict labelled recount with denominator and negative controls', 'prerequisites': 'Independent label adequacy, frozen record identity and declared population/denominators. Historical labels are not physical truth or a sealed evaluation key.'},
              {'mechanism': 'Finite nonfactorization countermodel', 'prerequisites': 'Explicit source worlds, observation map and target property. A real packet/semantic application needs justified world and fidelity encodings.'},
              {'mechanism': 'Trigger versus licensed transition with strict finite budget', 'prerequisites': 'Actual caller transition contract and source-bound budget accounting; diagnostic flags cannot supply omitted premises.'},
              {'mechanism': 'Source/output-bound ordinary-cell replay', 'prerequisites': 'Declared execution semantics, notebook schema/dependency admission and independent source hashes. No automatic transfer to IPython, arbitrary code security or learner efficacy.'},
              {'mechanism': 'Edition-bound evidence custody and scoped proof census', 'prerequisites': 'Exact bytes/compiler/call identity and separately justified checker/encoding adequacy. Hash/census bookkeeping is not publisher authentication or truth.'}],
          'limits': ['66 paths all have substantive dispositions, but only55 have full source-body reading receipts. The11 artifact rows remain explicitly bounded.',
                     'No provider calls, credentials, private benchmark content, sealed prompt/answer, external publication lookup or target-paper answer input accessed.',
                     'No current Lean kernel check, native rendering, arbitrary prompt fidelity theorem, real redaction/calibration implementation or model/learner improvement established.',
                     'Historical model identifiers and gate observations are supplied records, not authenticated executions. External references and owners were not followed beyond this declared supporting scope.',
                     'Every original assigned file and previously read manuscript retains its frozen SHA; only this report and its uniquely named helpers/inspection outputs were written.'],
          'provider_calls': 0, 'private_answer_access': False, 'production_source_edits': False}

# Validate both attribution ranges and the exact frozen originals before publishing this snapshot.
for row in reviews:
    original = rows[row['path']]
    assert row['sha256'] == original['sha256'] == sha((R / row['path']).read_bytes())
    count = original['lines']
    for start, end in row['reviewed_lines']:
        assert count is not None and 1 <= start <= end <= count
    if row['full_source_read']:
        assert row['reviewed_lines'] == ([[1,count]] if count else [])
assert sha((R / prior_md['path']).read_bytes()) == prior_md['sha256']
for item in claims + findings:
    for source in item['source_evidence']:
        raw = (R / source['path']).read_bytes()
        assert sha(raw) == source['sha256']
        for start, end in source['lines']:
            assert 1 <= start <= end <= len(raw.decode('utf-8').splitlines())
ledger_coverage = {}
for item in load('_read_ledger.json'):
    assert sha((R / item['path']).read_bytes()) == item['sha256']
    if not item.get('output_truncated'):
        ledger_coverage.setdefault(item['path'], set()).update(i for a,b in item['reviewed_lines'] for i in range(a,b+1))
for path, row in full.items():
    transfer = row.get('base_equality_delta_transfer')
    if transfer:
        base_report = json.loads((R / transfer['base_report']).read_text(encoding='utf-8'))
        base_row = next(item for item in base_report['file_reviews'] if item['path'] == transfer['base_path'])
        assert base_row['full_source_read'] and base_row['sha256'] == transfer['base_sha256']
        assert transfer['raw_equal'] or transfer.get('diff_read')
        if transfer.get('base_report_sha256'):
            assert sha((R / transfer['base_report']).read_bytes()) == transfer['base_report_sha256']
    else:
        assert ledger_coverage[path] == set(range(1, rows[path]['lines'] + 1))
assert sha((H / (P + '_scope.json')).read_bytes()) == scope_hash
report['validation'] = {'all_66_frozen_paths_present': True, 'all_66_frozen_sha256_unchanged': True,
                        'prior_full_manuscript_sha256_unchanged': True, 'source_ranges_valid': True,
                        'full_body_ledger_or_explicit_transfer_valid': True, 'zip_member_hashes_valid': True,
                        'full_and_bounded_labels_distinct': True}
save('.json', report)
save('_remaining_scope.json', {'files': [], 'status': 'all66_dispositioned_with55_full_bodies_and11_explicit_bounded_artifacts'})
markdown = ['# Paper009 supporting-file audit', '',
            'Completed all66 frozen paths: **55 full source bodies and11 explicitly bounded artifacts**. The prior full manuscript is excluded from the new body count. All67 original hashes remain unchanged.', '',
            'The useful mechanisms are exact triangle cycle-sum preservation, denominator-aware recount with negative controls, a finite information-loss countermodel, and a trigger-versus-license counterexample. Most authority/runtime results are explicit constructor or contract facts; broader names do not supply operational semantics.', '',
            'Fresh offline checks: current four-file non-notebook suite **17 passed,9 custody failures**; exact archived counterpart **26 passed**, and archived capstone passed. Current verifier reports35 custody issues. Official notebook replay and full collection are blocked by missing nbformat. A source-vetted stdlib fallback executes allfive ordinary cells in both editions and rejects altered expected output; this is not package/Jupyter validation. No providers, Lean builds or native renderers ran.', '',
            'All65 ZIP members are accounted:55 complete text-body transfers and10 bounded artifacts. All22 source diffs were read; two manifest diffs remain parsed comparisons. Both internal manifests validate. All40 PDF pages are accounted:20 directly viewed,10 raw-equal and10 exact RGB-equal. The516-row axiom listing is parsed evidence, not a full manual body read.', '']
for item in findings:
    markdown.extend([f"- **{item['id']}:** {item['statement']} {item['recommended_action']}", ''])
markdown.extend(['The JSON records every path/hash/range/assessment, six scoped claims, seven findings, archive member/difference receipts, historical-versus-current tests and new-encoding prerequisites. No original source or historical byte was changed.', ''])
(H / (P + '.md')).write_text('\n'.join(markdown), encoding='utf-8')
save('_final_validation.json', {'report_path': 'dag/reviews/' + P + '.json',
     'report_sha256': sha((H / (P + '.json')).read_bytes()), 'markdown_sha256': sha((H / (P + '.md')).read_bytes()),
     'scope_sha256': scope_hash, 'scope_summary': summary, 'checks': report['validation'], 'originals_unchanged': 67,
     'archive_member_counts': dict(collections.Counter('full_text' if item['full_source_read'] else 'bounded_artifact' for item in zip_reviews)),
     'claims': len(claims), 'findings': len(findings), 'fresh_tests': tests})
print(json.dumps({'complete': True, 'scope_summary': summary, 'report_sha256': sha((H / (P + '.json')).read_bytes())}, indent=2))
