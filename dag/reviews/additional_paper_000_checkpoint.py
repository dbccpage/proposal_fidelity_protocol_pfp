"""Record completed parent reads; source files and historical receipts stay untouched."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent
REPORT = OUT / 'additional_paper_000_support.json'
report = json.loads(REPORT.read_text(encoding='utf-8-sig'))
scope = json.loads((OUT / 'additional_paper_000_support_scope.json').read_text(encoding='utf-8-sig'))
prefix = 'papers/pfp/000_pfp_introduction/'
notes = {
    'MANIFEST.sha256': 'All 35 entries read and compared against current and archived bytes. Current package has 21 raw mismatches, 14 surviving universal newline normalization; archived manifest has no mismatches. This is a custody inventory, not mathematical evidence.',
    'SHA256SUMS': 'All 36 entries read and compared against current and archived bytes. Current package has 22 raw mismatches, 15 surviving universal newline normalization; archived manifest has no mismatches.',
    'docs/release_validation_2026_10_01.json': 'Full historical record read. Twenty-four tests and two notebook working directories are historical results, not fresh remote authentication. Archived/current complete diff shows rewritten path strings while dates and execution assertions remain historical.',
    'docs/release_validation_2026_10_02.json': 'Full historical record including source hashes, bounded scope and PDF build metadata read. Explicitly excludes contemporary notebook/native/Lean/model validation. Current paths differ from historical archive; retained hashes do not automatically bind renamed or edited current sources.',
    'docs/release_validation_2026_10_02_review_repairs.json': 'Full historical record read, including 28 tests, four malformed-index controls, wheel import and PDF compilation. Current cwd and source-path strings differ from archived receipt. Current selected tests were independently rerun previously, but historical execution provenance is not authenticated by this JSON.',
    'jupyter_notebooks/000_from_marks_to_returned_packets.ipynb': 'All 19 cells, metadata and empty outputs read, comprising 123 source lines. Nine code cells implement eight finite exercises with explicit positive/negative controls; no empirical model, physical emergence, or general convergence claim. Original notebook not modified.',
    'paper.tex': 'All 973 lines read. The source explains finite typed predicates, input binding, replay, bijective renaming and bounded attempts, and explicitly distinguishes supplied laws from Genesis derivation. Complete archive diff checked: renamed references and companion names do not introduce a new theorem. The five rewritten education reference paths do not exist at the pinned historical source commit.',
}
existing = {row['path'] for row in report['file_reviews']}
for relative, assessment in notes.items():
    path = prefix + relative
    frozen = next(row for row in scope['files'] if row['path'] == path)
    source = ROOT / path
    assert hashlib.sha256(source.read_bytes()).hexdigest() == frozen['sha256'], path
    if path in existing:
        continue
    report['file_reviews'].append({
        'path': path, 'sha256': frozen['sha256'], 'full_source_read': True,
        'reviewed_lines': [[1, len(source.read_text(encoding='utf-8-sig').splitlines())]],
        'assessment': assessment,
        'review_method': 'Complete source/body read plus manifest/archive comparisons where applicable',
    })
reviewed = {row['path'] for row in report['file_reviews'] if row.get('full_source_read')}
report['remaining_scope'] = [row['path'] for row in scope['files'] if row['path'] not in reviewed]
report['limits'][0] = 'No original source changed. Six PDFs and the release ZIP still require completed content/layout reconciliation; 28 selected tests do not validate the complete repository.'
REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
print(json.dumps({'full': len(reviewed), 'remaining': len(report['remaining_scope'])}))
