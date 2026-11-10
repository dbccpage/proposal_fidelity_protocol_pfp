"""Merge imported-pilot assessments without changing or deleting the corpus."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from retirement_custody import EvidenceStore

ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT / 'dag'
TRIAGE = DAG / 'pilot_triage'


def main():
    migration = json.loads((DAG / 'migrations/anomalon_pilots_move.json').read_text(encoding='utf-8'))
    base = migration['destination_relative_path'].rstrip('/')
    custody = {base + '/' + r['path']: r for r in migration['entries']}
    evidence_store = EvidenceStore()
    pilot_ids = sorted({r['path'].split('/')[0] for r in migration['entries']
                        if re.fullmatch(r'pilot_\d{7}', r['path'].split('/')[0])})
    rows = {name: {'id': name, 'path': base + '/' + name, 'review_status': 'pending',
                   'verdict': 'not_assessed', 'deletion_status': 'not_deleted'} for name in pilot_ids}
    reports = []; verified = {}; source_inventory = None; shared_rows = {}
    report_paths = sorted(list(TRIAGE.glob('numbered_*.json')) + list(TRIAGE.glob('shared_*.json')))
    for path in report_paths:
        if path.name.startswith('numbered_') and not re.fullmatch(r'numbered_\d{3}_\d{3}\.json', path.name):
            continue
        report = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(report, dict) or 'pilots' not in report:
            continue
        reports.append(path.relative_to(ROOT).as_posix())
        for pilot in report['pilots']:
            if pilot['id'] in rows:
                target = rows
            elif not re.fullmatch(r'pilot_\d{7}', pilot['id']) and pilot['path'] == base + '/' + pilot['id'] and (
                    any(item.startswith(pilot['path'] + '/') for item in custody)
                    or (pilot.get('owner_kind') == 'root_file' and pilot['path'] in custody)):
                target = shared_rows
            else:
                raise ValueError('Unknown pilot assessment: ' + pilot['id'])
            if pilot['id'] in target and target[pilot['id']]['review_status'] != 'pending':
                raise ValueError('Unknown or duplicate pilot assessment: ' + pilot['id'])
            for evidence in pilot.get('source_evidence', []):
                evidence_path = evidence['path']
                if evidence_path in verified:
                    if verified[evidence_path] != evidence['sha256']:
                        raise ValueError('Conflicting source pins')
                    continue
                resolved = (ROOT / evidence_path).resolve()
                if not resolved.is_relative_to(ROOT.resolve()):
                    raise ValueError('Source evidence outside repository')
                actual = hashlib.sha256(evidence_store.read(evidence_path)).hexdigest()
                if actual != evidence['sha256']:
                    raise ValueError('Assessment source changed: ' + evidence_path)
                if evidence_path in custody:
                    expected = custody[evidence_path]['sha256']
                else:
                    if source_inventory is None:
                        source_inventory = {r['path']: r['sha256'] for r in json.loads(
                            (DAG / 'file_inventory.json').read_text(encoding='utf-8'))['files']}
                    expected = source_inventory.get(evidence_path)
                if expected != actual:
                    raise ValueError('Evidence does not match either pinned corpus: ' + evidence_path)
                verified[evidence_path] = actual
            target[pilot['id']] = {**pilot, 'review_status': 'initial_mechanism_triage_recorded',
                                  **evidence_store.status(pilot['id']), 'report': path.relative_to(ROOT).as_posix(),
                                  'whole_directory_substantively_reviewed': False}
    counts = Counter(r['verdict'] for r in rows.values())
    nonnumbered = Counter(r['path'].split('/')[0] for r in migration['entries']
                          if r['source_git_tracked'] and r['path'].split('/')[0] not in rows)
    result = {'schema_version': '1.0', 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'triage_in_progress', 'source_custody_manifest': 'dag/migrations/anomalon_pilots_move.json',
              'numbered_pilots': len(rows), 'initially_assessed': sum(r['review_status'] != 'pending' for r in rows.values()),
              'shared_owners_assessed': len(shared_rows),
              'verdict_counts': dict(counts), 'source_pins_verified': len(verified), 'reports': reports,
              'retired_numbered_pilots': len(evidence_store.retired),
              'scope': 'Initial mechanism-level triage; full source and historical-artifact review is separately bounded in each report.',
              'nonnumbered_tracked_files_by_root': dict(nonnumbered),
              'nonnumbered_status': 'Shared-owner review partly recorded below; remaining owners and historical evidence are pending.',
              'policy': 'A candidate verdict does not delete files or establish QM transfer. Preserve provenance and test canonical owner equivalence before consolidation.',
              'pilots': list(rows.values()), 'shared_owners': list(shared_rows.values())}
    (TRIAGE / 'catalog.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    evidence_store.close()
    print(json.dumps({k: result[k] for k in ('numbered_pilots', 'initially_assessed', 'verdict_counts', 'source_pins_verified')}))


if __name__ == '__main__':
    main()
