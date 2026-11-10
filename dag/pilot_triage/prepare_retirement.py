"""Freeze reviewed stub/trivial retirements; this program does not delete anything."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TRIAGE = ROOT / 'dag/pilot_triage'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    target = TRIAGE / 'retirement_plan.json'
    lessons_path = TRIAGE / 'retained_lessons.json'
    if target.exists() or lessons_path.exists() or (TRIAGE / 'retirement_receipt.json').exists():
        raise ValueError('Frozen retirement artifacts already exist; refusing overwrite')
    catalog = read('dag/pilot_triage/catalog.json')
    if catalog['initially_assessed'] != catalog['numbered_pilots']:
        raise ValueError('Complete numbered-pilot triage before freezing retirement')
    migration = read('dag/migrations/anomalon_pilots_move.json')
    recovery = read('dag/migrations/pilot_recovery_archive.json')
    if recovery['original_custody_drift'] or recovery['archive_current_sha256_mismatches']:
        raise ValueError('Recovery archive has unresolved drift')
    if digest(Path(recovery['archive_path']).read_bytes()) != recovery['archive_sha256']:
        raise ValueError('Archive hash differs')
    base = migration['destination_relative_path']
    selected = [p for p in catalog['pilots'] if p['verdict'] in ('stub_candidate', 'trivial_candidate')]
    if not selected:
        raise ValueError('No reviewed retirement candidates')
    pilots = []
    lessons = []
    with zipfile.ZipFile(recovery['archive_path']) as archive:
        for pilot in selected:
            if pilot['path'] != base + '/' + pilot['id']:
                raise ValueError('Unexpected pilot path')
            folder = (ROOT / pilot['path']).resolve()
            if folder.parent != (ROOT / base).resolve() or not folder.is_dir():
                raise ValueError('Pilot directory absent or outside incoming root')
            directories = {p.relative_to(ROOT / base).as_posix() for p in folder.rglob('*') if p.is_dir()}
            expected_directories = {p for p in migration['directories'] if p.startswith(pilot['id'] + '/')}
            if directories != expected_directories:
                raise ValueError('Unknown or missing directories; do not delete: ' + pilot['id'])
            entries = [r for r in migration['entries'] if r['path'].startswith(pilot['id'] + '/')]
            expected = {base + '/' + r['path']: r for r in entries}
            actual = {p.relative_to(ROOT).as_posix(): p for p in folder.rglob('*') if p.is_file()}
            if set(actual) != set(expected):
                raise ValueError('Unknown or missing files; do not delete: ' + pilot['id'])
            for path, file in actual.items():
                row = expected[path]
                data = file.read_bytes()
                if len(data) != row['bytes'] or digest(data) != row['sha256']:
                    raise ValueError('Current file changed: ' + path)
                if archive.read(row['path']) != data:
                    raise ValueError('Archive does not preserve current file: ' + path)
            report_bytes = (ROOT / pilot['report']).read_bytes()
            reviewed = [r for r in json.loads(report_bytes)['pilots'] if r['id'] == pilot['id']]
            if len(reviewed) != 1 or any(reviewed[0].get(k) != pilot.get(k) for k in (
                    'path', 'verdict', 'rationale', 'contribution', 'mathematical_basis',
                    'reusable_mechanism_name', 'next_action', 'qm_seed_transfer',
                    'workflow_mapping', 'source_evidence')):
                raise ValueError('Catalog does not match current assessment: ' + pilot['id'])
            pilots.append({'id': pilot['id'], 'path': pilot['path'], 'verdict': pilot['verdict'],
                           'rationale': pilot['rationale'], 'report': pilot['report'],
                           'report_sha256': digest(report_bytes), 'file_count': len(entries),
                           'bytes': sum(r['bytes'] for r in entries), 'entries': entries})
            lessons.append({k: pilot.get(k) for k in (
                'id', 'contribution', 'mathematical_basis', 'reusable_mechanism_name',
                'rationale', 'next_action', 'qm_seed_transfer', 'workflow_mapping', 'source_evidence')})
            lessons[-1].update({'kind': 'historical_lesson_or_negative_fixture_not_executable_workflow',
                                'archive_prefix': pilot['id'] + '/', 'report': pilot['report']})
    lessons_bytes = (json.dumps({'schema_version': '1.0', 'scope': 'Preserve useful cautions and candidate mechanisms while retiring unimplemented or trivial standalone pilots. These are not new workflow families, executable adapters, or benchmark results.',
                                'lessons': lessons}, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    plan = {'schema_version': '1.0', 'status': 'frozen_ready_for_checked_removal',
            'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'authorization': 'User requested moving the pilots into this repository and deleting pilots that are stubs, repeats, trivial or too domain specific. This batch selects only substantively reviewed stub/trivial candidates.',
            'selection': ['stub_candidate', 'trivial_candidate'],
            'excluded': 'Duplicate, domain-specific, retain and uncertain candidates remain for separate consolidation. Original workflow owners are untouched.',
            'repository_root': str(ROOT), 'incoming_root': str(ROOT / base),
            'custody_manifest': 'dag/migrations/anomalon_pilots_move.json',
            'recovery_archive': {k: recovery[k] for k in ('archive_path', 'archive_sha256', 'archive_bytes')},
            'lessons_path': 'dag/pilot_triage/retained_lessons.json', 'lessons_sha256': digest(lessons_bytes),
            'removal_preflight_requirement': 'PowerShell must independently reject links, non-default NTFS streams and directory drift before removal. Python preparation alone does not authorize removal.',
            'pilot_count': len(pilots), 'file_count': sum(p['file_count'] for p in pilots),
            'bytes': sum(p['bytes'] for p in pilots), 'pilots': pilots}
    lessons_path.write_bytes(lessons_bytes)
    target.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'pilot_count': len(pilots), 'file_count': plan['file_count'], 'bytes': plan['bytes'],
                      'verdicts': dict(Counter(p['verdict'] for p in pilots)), 'deleted': False}))


if __name__ == '__main__':
    main()
