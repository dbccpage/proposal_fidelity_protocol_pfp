"""Read retired pilot evidence only through an explicit, completed removal receipt."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
TRIAGE = ROOT / 'dag/pilot_triage'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class EvidenceStore:
    """Live files remain authoritative; missing unretired files are errors."""

    def __init__(self):
        self.retired = {}
        self.in_progress = {}
        self.archive = None
        receipt_path = TRIAGE / 'retirement_receipt.json'
        if not receipt_path.exists():
            return
        receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        plan_bytes = (TRIAGE / 'retirement_plan.json').read_bytes()
        if sha256(plan_bytes) != receipt['plan_sha256']:
            raise ValueError('Retirement plan changed after removal began')
        plan = json.loads(plan_bytes)
        planned = {p['id']: p for p in plan['pilots']}
        if len(planned) != len(plan['pilots']):
            raise ValueError('Duplicate retirement identifiers')
        if plan['lessons_path'] != 'dag/pilot_triage/retained_lessons.json':
            raise ValueError('Unexpected preserved lesson path')
        lessons_bytes = (ROOT / plan['lessons_path']).read_bytes()
        if sha256(lessons_bytes) != plan['lessons_sha256']:
            raise ValueError('Preserved lessons changed after retirement was frozen')
        lesson_ids = [r['id'] for r in json.loads(lessons_bytes)['lessons']]
        if len(set(lesson_ids)) != len(lesson_ids) or set(lesson_ids) != set(planned):
            raise ValueError('Preserved lesson identifiers do not match the retirement plan')
        if receipt['status'] not in ('applying', 'complete'):
            raise ValueError('Unknown retirement receipt status')
        for removed in receipt['removed']:
            item = planned[removed['id']]
            if removed['path'] != item['path'] or removed['id'] in self.retired:
                raise ValueError('Conflicting retirement receipt')
            if (ROOT / item['path']).exists():
                raise ValueError('Retired directory unexpectedly present: ' + item['path'])
            self.retired[item['id']] = item
        if receipt['status'] == 'complete' and len(self.retired) != len(planned):
            raise ValueError('Incomplete removal presented as complete')
        intent = receipt.get('removal_intent')
        if intent is not None:
            item = planned[intent['id']]
            if receipt['status'] != 'applying' or intent['path'] != item['path'] or intent['id'] in self.retired:
                raise ValueError('Conflicting in-progress removal intent')
            self.in_progress[intent['id']] = item
        if not self.retired and not self.in_progress:
            return
        archive_path = Path(plan['recovery_archive']['archive_path'])
        if sha256(archive_path.read_bytes()) != plan['recovery_archive']['archive_sha256']:
            raise ValueError('Recovery archive changed')
        self.archive = zipfile.ZipFile(archive_path)
        names = self.archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate archive names')

    def read(self, path: str) -> bytes:
        target = (ROOT / path).resolve()
        if not target.is_relative_to(ROOT.resolve()):
            raise ValueError('Evidence path escaped repository')
        if target.exists():
            return target.read_bytes()
        parts = Path(path).parts
        if len(parts) < 4 or parts[:2] != ('pilots', 'anomalon_woland'):
            raise FileNotFoundError(path)
        item = self.retired.get(parts[2], self.in_progress.get(parts[2]))
        if item is None or self.archive is None:
            raise FileNotFoundError('Missing evidence has no completed retirement receipt: ' + path)
        archived_name = '/'.join(parts[2:])
        expected = {r['path']: r for r in item['entries']}.get(archived_name)
        if expected is None:
            raise ValueError('Missing evidence outside retired file manifest: ' + path)
        data = self.archive.read(archived_name)
        if len(data) != expected['bytes'] or sha256(data) != expected['sha256']:
            raise ValueError('Retired evidence differs from custody: ' + path)
        return data

    def status(self, pilot_id: str) -> dict:
        item = self.retired.get(pilot_id)
        if item is None:
            if pilot_id in self.in_progress:
                return {'deletion_status': 'removal_incomplete_archive_available',
                        'retirement_plan': 'dag/pilot_triage/retirement_plan.json',
                        'retirement_receipt': 'dag/pilot_triage/retirement_receipt.json',
                        'archive_prefix': pilot_id + '/'}
            return {'deletion_status': 'not_deleted'}
        return {'deletion_status': 'retired_from_checkout_archived',
                'retirement_plan': 'dag/pilot_triage/retirement_plan.json',
                'retirement_receipt': 'dag/pilot_triage/retirement_receipt.json',
                'preserved_mechanism': 'dag/pilot_triage/retained_lessons.json#' + pilot_id,
                'archive_prefix': pilot_id + '/'}

    def close(self):
        if self.archive is not None:
            self.archive.close()
