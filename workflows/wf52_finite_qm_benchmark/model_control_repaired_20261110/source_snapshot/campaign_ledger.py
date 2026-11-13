"""Finite campaign admission; every planned run is reserved before dispatch.

A manifest is an explicit execution configuration, not evidence of user consent.
Creating a ledger never sends requests. Unknown charges retain the full run cap
and block further runs until a separately implemented reconciliation is reviewed.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3

from budget_ledger import BudgetError, MAX_RUN_MICROUSD, RunLedger, integer


def validate_manifest(manifest):
    from reference_runner import PLANS, canonical, sha
    if set(manifest) != {'schema_version', 'campaign_id', 'seed_sha256', 'cap_microusd', 'runs'} or manifest['schema_version'] != '1.0':
        raise BudgetError('Unsupported campaign manifest')
    if type(manifest['campaign_id']) is not str or not manifest['campaign_id']:
        raise BudgetError('Campaign identity required')
    RunLedger.digest(manifest['seed_sha256'])
    cap = integer(manifest['cap_microusd'], 'campaign cap', positive=True)
    runs = manifest['runs']
    if not isinstance(runs, list) or not runs:
        raise BudgetError('Finite nonempty run list required')
    seen = set(); total = 0
    for run in runs:
        required = {'run_id', 'plan', 'plan_sha256', 'provider_identity', 'max_output_tokens', 'cap_microusd'}
        if set(run) != required or run['plan'] not in PLANS:
            raise BudgetError('Unsupported run definition')
        if type(run['run_id']) is not str or not run['run_id'] or run['run_id'] in seen:
            raise BudgetError('Unique run identity required')
        seen.add(run['run_id'])
        if run['plan_sha256'] != sha(canonical(PLANS[run['plan']])):
            raise BudgetError('Compiled plan hash differs')
        identity = run['provider_identity']
        if set(identity) != {'adapter', 'model', 'endpoint_slug'} or identity['adapter'] != 'openrouter-context-bound-v1':
            raise BudgetError('Unsupported provider adapter')
        if any(type(value) is not str or not value for value in identity.values()):
            raise BudgetError('Provider identity strings required')
        integer(run['max_output_tokens'], 'max output', positive=True)
        total += integer(run['cap_microusd'], 'run cap', positive=True)
        if run['cap_microusd'] > MAX_RUN_MICROUSD:
            raise BudgetError('Run exceeds USD 0.10')
    if total > cap:
        raise BudgetError('Sum of planned run ceilings exceeds campaign budget')
    return manifest


class CampaignLedger:
    def __init__(self, path: Path):
        self.db = sqlite3.connect(path, timeout=30, isolation_level=None)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS campaign(
            singleton INTEGER PRIMARY KEY CHECK(singleton=1),
            manifest_sha256 TEXT NOT NULL, manifest TEXT NOT NULL,
            cap INTEGER NOT NULL, blocked INTEGER NOT NULL DEFAULT 0);
          CREATE TABLE IF NOT EXISTS admissions(
            run_id TEXT PRIMARY KEY, cap INTEGER NOT NULL, actual INTEGER,
            known_spent INTEGER NOT NULL DEFAULT 0,
            state TEXT NOT NULL, receipt_sha256 TEXT);
        ''')

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def close(self):
        self.db.close()

    def create(self, manifest):
        from reference_runner import canonical, sha
        validate_manifest(manifest)
        data = canonical(manifest)
        with self.transaction():
            if self.db.execute('SELECT 1 FROM campaign').fetchone():
                raise BudgetError('Campaign already exists; its budget cannot be reset')
            self.db.execute('INSERT INTO campaign(singleton,manifest_sha256,manifest,cap) VALUES(1,?,?,?)',
                            (sha(data), data.decode(), manifest['cap_microusd']))

    def manifest(self):
        from reference_runner import sha
        row = self.db.execute('SELECT manifest,manifest_sha256 FROM campaign WHERE singleton=1').fetchone()
        if row is None or sha(row[0].encode()) != row[1]:
            raise BudgetError('Missing or damaged campaign manifest')
        return validate_manifest(json.loads(row[0]))

    def summary(self):
        row = self.db.execute('SELECT cap,blocked,manifest_sha256 FROM campaign WHERE singleton=1').fetchone()
        if row is None:
            raise BudgetError('Uninitialized campaign')
        spent, held = self.db.execute('''SELECT COALESCE(SUM(known_spent),0),
            COALESCE(SUM(CASE WHEN actual IS NULL THEN MAX(cap-known_spent,0) ELSE 0 END),0) FROM admissions''').fetchone()
        return {'cap_microusd': row[0], 'spent_microusd': spent, 'held_microusd': held,
                'blocked': bool(row[1]), 'manifest_sha256': row[2]}

    def admit(self, run_id, plan, provider_identity, seed_sha256, max_output_tokens):
        with self.transaction():
            manifest = self.manifest()
            planned = next((r for r in manifest['runs'] if r['run_id'] == run_id), None)
            if planned is None or manifest['seed_sha256'] != seed_sha256 or planned['plan'] != plan or \
                    planned['provider_identity'] != provider_identity or planned['max_output_tokens'] != max_output_tokens:
                raise BudgetError('Run is not an exact member of the frozen campaign')
            summary = self.summary()
            if summary['blocked']:
                raise BudgetError('Campaign blocked by an uncertain or overrun charge')
            if self.db.execute('SELECT 1 FROM admissions WHERE run_id=?', (run_id,)).fetchone():
                raise BudgetError('Campaign run already admitted; dispatch cannot repeat')
            if self.db.execute("SELECT 1 FROM admissions WHERE state='reserved'").fetchone():
                raise BudgetError('An unfinished run holds the campaign; reconciliation required')
            admitted = {r[0] for r in self.db.execute('SELECT run_id FROM admissions')}
            next_id = next(r['run_id'] for r in manifest['runs'] if r['run_id'] not in admitted)
            if run_id != next_id:
                raise BudgetError('Run is out of the frozen campaign order')
            if summary['spent_microusd'] + summary['held_microusd'] + planned['cap_microusd'] > summary['cap_microusd']:
                raise BudgetError('Aggregate campaign cap exceeded')
            self.db.execute('INSERT INTO admissions(run_id,cap,state) VALUES(?,?,?)',
                            (run_id, planned['cap_microusd'], 'reserved'))
            return planned['cap_microusd']

    def finish(self, run_id, receipt, receipt_sha256):
        RunLedger.digest(receipt_sha256)
        if receipt['run_id'] != run_id:
            raise BudgetError('Receipt run binding differs')
        budget = receipt['budget']
        actual = integer(budget['spent_microusd'], 'spent')
        held = integer(budget['held_microusd'], 'held')
        with self.transaction():
            row = self.db.execute('SELECT cap,state FROM admissions WHERE run_id=?', (run_id,)).fetchone()
            if row is None or row[1] != 'reserved':
                raise BudgetError('Run admission missing or already frozen')
            uncertain = held != 0 or budget['blocked']
            overrun = actual > row[0]
            self.db.execute('UPDATE admissions SET actual=?,known_spent=?,state=?,receipt_sha256=? WHERE run_id=?',
                            (None if uncertain else actual, actual,
                             'uncertain' if uncertain else 'overrun' if overrun else 'settled', receipt_sha256, run_id))
            if uncertain or overrun:
                self.db.execute('UPDATE campaign SET blocked=1 WHERE singleton=1')


class CampaignAdmission:
    def __init__(self, ledger):
        self.ledger = ledger

    def admit(self, *args):
        return self.ledger.admit(*args)

    def finish(self, *args):
        return self.ledger.finish(*args)
