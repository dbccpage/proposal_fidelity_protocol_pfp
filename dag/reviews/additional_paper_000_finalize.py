"""Assemble the completed introductory-package review from retained reading receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
P = 'papers/pfp/000_pfp_introduction/'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

report = read(OUT / 'additional_paper_000_support.json')
scope = read(OUT / 'additional_paper_000_support_scope.json')
custody = read(OUT / 'additional_paper_000_custody.json')
inventory = read(OUT / 'paper_000_support_inspection/pdf_inventory.json')
pixels = read(OUT / 'paper_000_support_inspection/pixel_correspondence.json')
references = read(OUT / 'additional_paper_000_reference_bindings.json')
assert all(all(row['matching_pixels']) for row in pixels)
assert all(not row['current_path_present'] and row['archived_path_present'] for row in references['references'])
existing = {row['path'] for row in report['file_reviews']}
assessments = [
    'All twelve pages read through extracted text and rendered pages. Useful finite teaching exposition, with explicit assumptions and limits. No new Genesis derivation, native implementation, model ranking or savings result. Older Landau companion naming remains in this historical rendering, unlike current Markdown/TeX.',
    'All twenty-six companion pages read and visually inspected. The optional six-page fiction supplies no mathematical mechanism; the guide, twenty core questions and four capstones supply concrete finite exercises. The key/guide type-precedence description is stale. Rendered capstone equations lose lambda/sum/inequality/boundary operators, unlike their Markdown source.',
    'All six pages assessed through their exact text and rendered-pixel equality to companion pages 1-6, which were completely read and visually inspected. Optional fictional staging, explicitly not historical quotation or mathematical source; no additional workflow contribution.',
    'All seven pages assessed through exact text and rendered-pixel equality to companion pages 13-19, which were completely read and visually inspected. Correct finite separator/cycle/boundary arguments under supplied assumptions, but Q19 describes old behavior and pages 5-6 lose mathematical operators in the PDF.',
    'All seven pages assessed through exact text and rendered-pixel equality to companion pages 20-26, which were completely read and visually inspected. Twenty core questions and four finite capstones; useful task-binding and counterexample exercises. No measured learning transfer; current Q19 repair wording must acknowledge the already repaired checker.',
    'All six pages assessed through exact text and rendered-pixel equality to companion pages 7-12, which were completely read and visually inspected. Useful concept/checker/identity boundaries; stale type-precedence paragraph and missing symbols in page 5 weak-duality equation need correction.',
]
for index, item in enumerate(inventory):
    path = item['pdf']
    if path in existing:
        continue
    report['file_reviews'].append({
        'path': path, 'sha256': item['sha256'], 'full_source_read': True,
        'reviewed_pages': [[1, item['pages']]],
        'assessment': assessments[index],
        'review_method': 'Complete extracted text and rendered-page inspection' if index < 2 else 'Complete equality of extracted text and rendered pixels to fully inspected companion pages; explicit content disposition',
        'validation': ['dag/reviews/paper_000_support_inspection/render_receipt.json', 'dag/reviews/paper_000_support_inspection/pixel_correspondence.json'],
    })

archive_path = P + '000_pfp_introduction_2026-10-02.zip'
if archive_path not in existing:
    frozen = next(row for row in scope['files'] if row['path'] == archive_path)
    report['file_reviews'].append({
        'path': archive_path, 'sha256': frozen['sha256'], 'full_source_read': True,
        'assessment': 'All 37 members have content dispositions: six PDFs are byte-identical to fully inspected current PDFs; every text member is covered by a fully read current base plus every archived/current textual difference, including both embedded manifests. The initial primary-manuscript review supplies the paper.md base. All CRCs and 71 embedded manifest entries match. Internal consistency does not authenticate historical execution or publication.',
        'review_method': 'Complete member inventory, explicit base-plus-all-differences reading, exact PDF byte transfers, full manifest and CRC verification',
        'validation': 'dag/reviews/additional_paper_000_custody.json',
    })

member_reviews = []
for member in custody['archive_members']:
    basis = 'exact_pdf_bytes_to_fully_inspected_current_pdf' if member['member'].endswith('.pdf') else ('complete_current_text_plus_line_ending_only_difference' if member['current_lf_equal'] else 'complete_current_text_plus_every_archived_current_difference')
    member_reviews.append({**member, 'content_disposition_complete': True, 'reading_basis': basis,
        'base_report': 'dag/reviews/papers_audit.json' if member['current_path'] == P + 'paper.md' else 'dag/reviews/additional_paper_000_support.json'})
assert len(member_reviews) == 37
(OUT / 'additional_paper_000_archive_reading.json').write_text(json.dumps({'archive': archive_path, 'members': member_reviews, 'complete_text_differences': 'dag/reviews/paper_000_support_inspection/archive_complete_text_diffs.txt', 'limits': 'PDF object internals, ZIP parser security, historical process execution and remote publication are not certified.'}, indent=2) + '\n', encoding='utf-8')

new_findings = [
    {
        'id': 'PAPER000-SUPPORT-CURRENT-MANIFEST-DRIFT', 'severity': 'custody_gap',
        'statement': 'MANIFEST.sha256 and SHA256SUMS have 21 and 22 current raw-byte mismatches; 14 and 15 remain after universal LF normalization. All 35 and 36 embedded archive bindings match. Current renamed/edited draft files therefore cannot be certified by the retained release sums. Preserve the historical ZIP and issue a separate current manifest after corrections.',
        'evidence': [P + 'MANIFEST.sha256', P + 'SHA256SUMS', archive_path],
        'validation': 'dag/reviews/additional_paper_000_custody.json',
    },
    {
        'id': 'PAPER000-SUPPORT-HISTORICAL-RECEIPT-REWRITES', 'severity': 'provenance_gap',
        'statement': 'All three current historical release-validation JSON files have cwd and/or source-path strings rewritten relative to the dated release archive, while retaining historical dates, commands, hashes and execution assertions. Treat the archived originals as historical records and current edits as migration adaptations; changed path strings are not evidence of a fresh run. This mismatch does not prove the original tests were fabricated.',
        'evidence': [P + 'docs/' + name for name in ('release_validation_2026_10_01.json', 'release_validation_2026_10_02.json', 'release_validation_2026_10_02_review_repairs.json')],
        'validation': 'dag/reviews/paper_000_support_inspection/archive_complete_text_diffs.txt',
    },
    {
        'id': 'PAPER000-SUPPORT-PINNED-REFERENCE-REWRITE', 'severity': 'reproducibility_gap',
        'statement': 'Five conceptual source links were rewritten from omega_engine_education to education while retaining commit 3f3399766108adc4c4e7615dce2573a57be57dd6. Actual historical Git objects contain all five original paths and none of the five rewritten paths. Restore fixed-commit paths or cite a different explicitly verified revision; renaming a present checkout cannot rewrite a historical tree.',
        'evidence': [P + 'paper.md', P + 'paper.tex', P + 'docs/references.md'],
        'validation': 'dag/reviews/additional_paper_000_reference_bindings.json',
    },
    {
        'id': 'PAPER000-SUPPORT-MISSING-PDF-MATH', 'severity': 'mathematical_rendering_defect',
        'statement': 'Visual inspection confirms missing lambda, summation and inequality operators in study-guide page 5 and instructor-key page 5, and a missing boundary operator on key page 6. The same defects occur on companion pages 11, 17 and 18. Markdown preserves the intended LaTeX formulas; the PDFs alone do not faithfully display these proof steps. Re-render a new reviewed edition with mathematical glyph and equation checks; preserve the historical edition.',
        'evidence': [P + '_lev_examiner_theoretical_minimum_quiz/study_guide.pdf', P + '_lev_examiner_theoretical_minimum_quiz/instructor_key.pdf', P + '000_pfp_examiner_companion.pdf'],
        'validation': ['dag/reviews/paper_000_support_inspection/render_01/sheet-03.png', 'dag/reviews/paper_000_support_inspection/render_01/sheet-05.png', 'dag/reviews/paper_000_support_inspection/pixel_correspondence.json'],
    },
    {
        'id': 'PAPER000-SUPPORT-EDITION-NAMING-DRIFT', 'severity': 'version_binding_gap',
        'statement': 'All six current PDFs are byte-identical to the archived edition and retain Landau/adversary-persona naming; current Markdown/TeX and filenames use Examiner/Adversary naming. The code and finite mathematics need not differ, but these PDFs are historical editions rather than renderings of the current named sources. Label that relationship explicitly.',
        'evidence': [P + '000_paper.pdf', P + '000_pfp_examiner_companion.pdf', P + 'paper.tex', archive_path],
        'validation': 'dag/reviews/additional_paper_000_custody.json',
    },
]
known = {row['id'] for row in report['findings']}
report['findings'].extend(row for row in new_findings if row['id'] not in known)
report['claims'] = [
    {
        'id': 'PAPER000-FINITE-TEACHING-CONTRACT',
        'statement': 'The supplied examples implement finite typed predicates over declared carriers, counts, observation rows and directed triples, with exact-question digest binding, recomputed returns, bijective renaming and bounded candidate attempts. These are executable protocol teaching mechanisms, not a derivation of the supplied relation law or natural-language meaning.',
        'status': 'bounded_source_and_local_execution_support',
        'dependencies': ['Trust the declared finite input model, local checker and caller-retained expected identity.', 'SHA-256 content comparison is used as a binding assumption; it is not producer authentication.', 'Attempt fuel does not bound arbitrary proposer construction, total runtime or paid-provider costs.'],
        'evidence': [P + 'code/basic_packets.py', P + 'code/lesson_packets.py', P + 'jupyter_notebooks/000_from_marks_to_returned_packets.ipynb'],
        'validation': ['dag/reviews/additional_paper_000_support_probes.json', 'dag/reviews/additional_paper_000_notebook_check.json'],
    },
    {
        'id': 'PAPER000-CYCLE-CAPSTONE',
        'statement': 'For one supplied consistently oriented cycle with rational reports c and positive rational weights w, min_f sum_e w_e|c_e-(df)_e| equals min_e(w_e)*|sum_e c_e|. Summing residuals gives the lower bound; placing total residual on a minimum-weight edge permits exact integration of c-r and attains it. A constant feasible circulation with matching sign attains the same dual value.',
        'status': 'elementary_conditional_proof_read_and_checked',
        'dependencies': ['A single consistently oriented cycle is supplied, with rational reports and strictly positive weights.', 'Vertex potentials are unrestricted rational values; no additional faces or physics are inferred.'],
        'evidence': [P + '_lev_examiner_theoretical_minimum_quiz/quiz.md', P + '_lev_examiner_theoretical_minimum_quiz/instructor_key.md'],
        'limits': 'Not a new general graph solver, model-improvement experiment or native formal proof.',
    },
    {
        'id': 'PAPER000-FINITE-CAPSTONE-SCOPE',
        'statement': 'The separator exercise exhausts eight row subsets and retains all three tied two-row minima; the 2^k capacity bound is the supplied binary-signature pigeonhole bound. The tetrahedral boundary exercise cancels every oriented edge in boundary squared. These are useful exact controls for future certificate workflows, not consequences of an uninterpreted bracket inscription.',
        'status': 'finite_hand_check_and_primary_definition_correspondence',
        'dependencies': ['Observation rows and their binary values are explicitly supplied.', 'Ordered simplex and alternating boundary conventions are explicitly supplied; graph edges alone do not admit higher-dimensional cells.'],
        'evidence': [P + '_lev_examiner_theoretical_minimum_quiz/instructor_key.md', P + '_lev_examiner_theoretical_minimum_quiz/quiz.md'],
        'external_source': 'https://kerodon.net/tag/000K',
    },
]
report['paper_quality_assessment'] = {
    'decision': 'retain_as_introductory_pedagogy_with_specific_repairs',
    'useful_contribution': 'Eight small executable exercises teach declared predicates, refusal, question binding, replay and bounded attempts; four exact capstones bridge to independently checkable certificates.',
    'not_a_research_result': 'The optional fiction adds no mathematical mechanism. No measured general reasoning gain, model cost improvement, pedagogical transfer or new Genesis derivation is established.',
    'required_repairs': [row['id'] for row in report['findings']],
    'do_not_infer_authorship': 'Textual quality and technical validity are assessed; these files do not establish whether a language model wrote them.',
}
report['status'] = 'complete_declared_introductory_support_slice'
report['remaining_scope'] = []
report['scope_summary'] = {'files': 38, 'complete_content_dispositions': 38, 'pdfs': 6, 'pdf_pages': 64, 'unique_rendered_pages_read': 38, 'standalone_pages_identical_to_reviewed_companion': 26, 'archive_members': 37, 'focused_tests_previously_passed': 28, 'fresh_notebook_code_cells_passed': 9, 'findings': len(report['findings'])}
report['validation'] = ['dag/reviews/additional_paper_000_support_probes.json', 'dag/reviews/additional_paper_000_custody.json', 'dag/reviews/additional_paper_000_archive_reading.json', 'dag/reviews/additional_paper_000_reference_bindings.json', 'dag/reviews/additional_paper_000_notebook_check.json', 'dag/reviews/paper_000_support_inspection/render_receipt.json', 'dag/reviews/paper_000_support_inspection/pixel_correspondence.json']
report['external_source_checks'] = [
    {'url': 'https://kerodon.net/tag/000K', 'status': 'read_primary_definition_2026_11_10', 'assessment': 'The declared ordered-simplex horn examples match the stated missing-face convention; no higher categorical theorem or physical interpretation is imported.'},
    {'url': 'https://zenodo.org/records/23108137', 'status': 'not_independently_verified', 'assessment': 'Direct opening failed and a targeted search did not corroborate this record. Neither an absence claim nor publication authentication follows.'},
]
report['limits'] = [
    'All 38 frozen support paths have complete content dispositions, including original text, all PDF pages through explicit equality transfers, and all archive members. Raw PDF/ZIP object internals are not a parser-security audit.',
    'The 28 focused tests, two pure countercontrols and nine fresh notebook cell executions are bounded local checks. Notebook execution was ordinary sequential Python, not a Jupyter-kernel or UI test. No provider calls, native build or remote historical execution authentication occurred.',
    'Historical editions, receipts, archive bytes and manuscript sources remain unchanged. Findings are review records, not silently applied publication repairs.',
    'The public historical instructor key is unrelated to and never supplied to the sealed new QM benchmark. No private benchmark answer was read or disclosed in this slice.',
    'The original all-repository audit and workflow evaluation goal remain incomplete.',
]
assert len(report['file_reviews']) == len(scope['files']) == 38
assert {row['path'] for row in report['file_reviews']} == {row['path'] for row in scope['files']}
for row in report['file_reviews']:
    assert hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], row['path']
(OUT / 'additional_paper_000_support.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps(report['scope_summary']))
