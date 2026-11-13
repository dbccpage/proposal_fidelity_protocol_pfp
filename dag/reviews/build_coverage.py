"""Merge explicit reading receipts without treating a structural scan as a proof."""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT / 'dag'
sys.path.insert(0, str(DAG))
from source_revisions import followup_revisions

def read(name):
    return json.loads((DAG / name).read_text(encoding='utf-8'))

def check_rules(checks):
    # Some reports inline each verdict; others name checks and keep verdicts in a JSONL ledger.
    # Naming a check never implies that it passed.
    return [{'rule': c, 'status': 'see_report_detail_ledger'} if isinstance(c, str)
            else {'rule': c['rule'], 'status': c['status']} for c in checks]

def main():
    inventory = read('file_inventory.json')
    rows = {r['path']: {
        'path': r['path'], 'sha256': r['sha256'], 'size_bytes': r['size_bytes'],
        'structural_review': 'dag/structural_review.json',
        'substantive_status': 'pending', 'reading_receipts': [], 'automated_assessments': [],
        'bounded_file_assessments': [],
    } for r in inventory['files']}

    def add(path, report, full, detail, digest=None):
        if path not in rows:
            return
        row = rows[path]
        if digest is not None and digest != row['sha256']:
            row['reading_receipts'].append({'report': report, 'status': 'stale_hash', 'detail': detail})
            return
        row['reading_receipts'].append({'report': report, 'status': 'full_source_read' if full else 'partial_source_read', 'detail': detail})
        if full:
            row['substantive_status'] = 'full_text_source_review_recorded'
        elif row['substantive_status'] == 'pending':
            row['substantive_status'] = 'partial_source_review_recorded'

    for r in read('reviews/systems_audit.json')['files']:
        if r.get('semantic_full_review') or r.get('reviewed_line_ranges'):
            add(r['path'], 'dag/reviews/systems_audit.json', r.get('semantic_full_review', False), r.get('reviewed_line_ranges'), r.get('sha256'))
    for r in read('reviews/papers_audit.json')['files']:
        if r['review_status'] in ('full-text-read', 'partial-text-read'):
            add(r['path'], 'dag/reviews/papers_audit.json', r['review_status'] == 'full-text-read', r.get('reviewed_ranges'), r.get('sha256'))
    for r in read('reviews/workflows_audit.json')['file_reviews_remote_main']:
        if r.get('review_level') in ('semantic_full_text', 'semantic_selected_sections'):
            add(r['path'], 'dag/reviews/workflows_audit.json', r['review_level'] == 'semantic_full_text', r.get('review_level'), r.get('sha256'))
    pfp = read('reviews/pfp_audit.json')
    for path in pfp['full_source_reads']:
        add(path, 'dag/reviews/pfp_audit.json', True, 'Full source reading recorded by parent at pinned commit')
    for path in pfp['partial_source_reads']:
        add(path, 'dag/reviews/pfp_audit.json', False, 'Partial source reading; directory entries are not expanded')
    # Additional agents use this small shared receipt format, without overwriting earlier reviews.
    for report in sorted((DAG / 'reviews').glob('additional_*.json')):
        content = json.loads(report.read_text(encoding='utf-8'))
        if not isinstance(content, dict):
            continue
        # Validation summaries use integer file_reviews/claims counts; they are
        # bookkeeping, not a second source-reading receipt population.
        if isinstance(content.get('file_reviews'), int):
            continue
        for r in content.get('file_reviews', []):
            if r.get('full_source_read') or r.get('reviewed_lines'):
                add(r['path'], report.relative_to(ROOT).as_posix(), r.get('full_source_read', False), r.get('assessment'), r.get('sha256'))
            elif r.get('path') in rows and r.get('assessment'):
                # Preserve an explicit bounded disposition without calling it a full source read.
                row = rows[r['path']]
                row['bounded_file_assessments'].append({
                    'report': report.relative_to(ROOT).as_posix(),
                    'status': 'bounded_assessment_recorded' if r.get('sha256') == row['sha256'] else 'stale_hash',
                    'review_level': r.get('review_level', 'see_report_for_exact_scope'),
                    'assessment': r['assessment'],
                    'detail_ledger': r.get('detail_receipt'),
                })
        for r in content.get('automated_reviews', []):
            if r.get('path') not in rows:
                continue
            row = rows[r['path']]
            row['automated_assessments'].append({
                'report': report.relative_to(ROOT).as_posix(),
                'status': r.get('status') if r.get('sha256') == row['sha256'] else 'stale_hash',
                'rules': check_rules(r.get('checks', [])),
                'detail_ledger': r.get('ledger'),
                'evidence_ceiling': r.get('evidence_ceiling'),
                'scope': 'Selected schema/accounting/custody predicates only; does not change source-reading status.',
            })

    relocation_path = DAG / 'migrations' / 'demo_support_verification.json'
    if relocation_path.exists():
        relocation = json.loads(relocation_path.read_text(encoding='utf-8'))
        if relocation.get('status') != 'verified':
            raise ValueError('Unverified education relocation')
        for item in relocation['locations']:
            if item['source_repo'] != 'pfp' or item['original_path'] not in rows:
                continue
            row = rows[item['original_path']]
            if row['sha256'] != item['original_sha256']:
                raise ValueError('Relocation conflicts with pinned inventory')
            row['current_location'] = item
            row['relocation_receipt'] = 'dag/migrations/demo_support_verification.json'
        for item in relocation['retained_source_revisions']:
            if item['source_repo'] == 'pfp' and item['path'] in rows:
                row = rows[item['path']]
                if row['sha256'] != item['original_sha256']:
                    raise ValueError('Consumer revision conflicts with pinned inventory')
                row['post_inventory_revision'] = item
                row['review_scope_note'] = 'Reading receipts assess original pinned bytes; navigation revisions have separate custody.'
    for item in followup_revisions(ROOT, rows):
        row = rows[item['path']]
        if row.get('post_inventory_revision'):
            raise ValueError('Conflicting consumer revision registries')
        row['post_inventory_revision'] = item
        row['review_scope_note'] = 'Reading receipts assess original pinned bytes; later navigation revisions have separately validated original/current custody.'
    counts = Counter(r['substantive_status'] for r in rows.values())
    disposition_counts = Counter()
    for row in rows.values():
        source_status = row['substantive_status']
        if source_status != 'pending':
            disposition = source_status
        elif any(a['status'] == 'bounded_assessment_recorded' for a in row['bounded_file_assessments']):
            disposition = 'bounded_file_assessment_recorded'
        else:
            disposition = 'no_source_or_bounded_file_disposition'
        row['review_disposition'] = disposition
        disposition_counts[disposition] += 1
    by_tree = {}
    for r in rows.values():
        tree = r['path'].split('/')[0] if '/' in r['path'] else '[root]'
        by_tree.setdefault(tree, Counter())[r['substantive_status']] += 1
    result = {
        'schema_version': '1.0', 'source_commit': inventory['local_head'],
        'scope_files': len(rows), 'counts': dict(counts),
        'review_disposition_counts': dict(disposition_counts),
        'files_with_explicit_bounded_assessment': sum(any(a['status'] == 'bounded_assessment_recorded' for a in r['bounded_file_assessments']) for r in rows.values()),
        'disposition_interpretation': 'Bounded file assessments retain their precise receipt/schema/custody limits. They do not change full-source reading status, certify nested mathematics, or count structural/automated-only scans as a substantive disposition.',
        'files_with_bounded_automated_assessment': sum(bool(r['automated_assessments']) for r in rows.values()),
        'all_files_substantively_reviewed': counts.get('pending', 0) == counts.get('partial_source_review_recorded', 0) == 0,
        'interpretation': 'Full source reading is an assessment receipt, not a proof of correctness. Tests, formal proofs, artifact authenticity, references and runtime correspondence require their own evidence. Exact duplicate hashes do not automatically inherit contextual semantic review.',
        'by_top_directory': {k: dict(v) for k, v in sorted(by_tree.items())},
        'files': list(rows.values()),
    }
    target = DAG / 'reviews' / 'coverage.json'
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('scope_files', 'counts', 'all_files_substantively_reviewed')}))

if __name__ == '__main__':
    main()
