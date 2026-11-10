"""Durable aggregate admission ledger; no provider calls and no secret access.

The hard cost implication is conditional on an honest upper quote and provider
enforcement of its token/tariff bounds. An observed overrun is retained and
blocks the run; no local after-the-fact check can undo external billing.
"""
from __future__ import annotations
from contextlib import contextmanager
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
import sqlite3

MAX_RUN_MICROUSD=100_000

class BudgetError(ValueError): pass

def integer(value, name, *, positive=False):
    if type(value) is not int or value < (1 if positive else 0):
        raise BudgetError(f'{name}: exact nonnegative integer required')
    return value

def quote_microusd(input_token_bound:int, output_token_bound:int,
                   input_usd_per_million:str, output_usd_per_million:str,
                   fixed_usd:str='0') -> int:
    """USD/Mtoken equals microusd/token; decimal strings prevent binary rounding."""
    integer(input_token_bound,'input bound');integer(output_token_bound,'output bound')
    values=[]
    for value in (input_usd_per_million,output_usd_per_million,fixed_usd):
        if type(value) is not str: raise BudgetError('price must be a decimal string')
        d=Decimal(value)
        if not d.is_finite() or d<0:raise BudgetError('nonfinite or negative price')
        values.append(d)
    result=input_token_bound*values[0]+output_token_bound*values[1]+1_000_000*values[2]
    return int(result.to_integral_value(rounding=ROUND_CEILING))

class RunLedger:
    def __init__(self,path:Path):
        self.db=sqlite3.connect(path,timeout=30,isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS runs(
          id TEXT PRIMARY KEY, seed_sha256 TEXT NOT NULL,
          cap INTEGER NOT NULL, blocked INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS calls(
          id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(id),
          request_sha256 TEXT NOT NULL, quote INTEGER NOT NULL,
          actual INTEGER, response_sha256 TEXT, state TEXT NOT NULL);
        ''')

    def close(self):self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK');raise

    @staticmethod
    def digest(value):
        if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
            raise BudgetError('canonical SHA-256 digest required')
        return value

    def start(self,run_id:str,seed_sha256:str,cap:int=MAX_RUN_MICROUSD):
        integer(cap,'cap',positive=True);self.digest(seed_sha256)
        if cap>MAX_RUN_MICROUSD:raise BudgetError('run cap exceeds USD 0.10')
        if type(run_id) is not str or not run_id:raise BudgetError('run id required')
        with self.transaction():
            if self.db.execute('SELECT 1 FROM runs WHERE id=?',(run_id,)).fetchone():
                raise BudgetError('run identity already exists; resume without resetting budget')
            self.db.execute('INSERT INTO runs(id,seed_sha256,cap) VALUES(?,?,?)',(run_id,seed_sha256,cap))

    def summary(self,run_id):
        row=self.db.execute('SELECT seed_sha256,cap,blocked FROM runs WHERE id=?',(run_id,)).fetchone()
        if row is None:raise BudgetError('unknown run')
        spent,held=self.db.execute('''SELECT
            COALESCE(SUM(CASE WHEN actual IS NOT NULL THEN actual ELSE 0 END),0),
            COALESCE(SUM(CASE WHEN actual IS NULL THEN quote ELSE 0 END),0)
            FROM calls WHERE run_id=?''',(run_id,)).fetchone()
        return {'run_id':run_id,'seed_sha256':row[0],'cap_microusd':row[1],
                'spent_microusd':spent,'held_microusd':held,'available_microusd':row[1]-spent-held,
                'blocked':bool(row[2])}

    def reserve(self,run_id,call_id,request_sha256,quote):
        integer(quote,'quote');self.digest(request_sha256)
        if type(call_id) is not str or not call_id:raise BudgetError('call id required')
        with self.transaction():
            s=self.summary(run_id)
            if s['blocked']:raise BudgetError('run blocked pending reconciliation')
            if self.db.execute('SELECT 1 FROM calls WHERE id=?',(call_id,)).fetchone():
                raise BudgetError('call identity already exists; dispatch must not repeat')
            if quote>s['available_microusd']:raise BudgetError('aggregate run cap would be exceeded')
            self.db.execute('INSERT INTO calls(id,run_id,request_sha256,quote,state) VALUES(?,?,?,?,?)',
                            (call_id,run_id,request_sha256,quote,'reserved'))

    def mark_uncertain(self,call_id):
        with self.transaction():
            row=self.db.execute('SELECT run_id,actual FROM calls WHERE id=?',(call_id,)).fetchone()
            if row is None or row[1] is not None:raise BudgetError('unknown or settled call')
            self.db.execute('UPDATE calls SET state=? WHERE id=?',('uncertain',call_id))
            self.db.execute('UPDATE runs SET blocked=1 WHERE id=?',(row[0],))

    def block(self,run_id):
        with self.transaction():
            self.summary(run_id)
            self.db.execute('UPDATE runs SET blocked=1 WHERE id=?',(run_id,))

    def settle(self,call_id,actual,response_sha256):
        integer(actual,'actual');self.digest(response_sha256)
        overrun=False
        with self.transaction():
            row=self.db.execute('SELECT run_id,quote,actual FROM calls WHERE id=?',(call_id,)).fetchone()
            if row is None or row[2] is not None:raise BudgetError('unknown or already settled call')
            overrun=actual>row[1]
            self.db.execute('UPDATE calls SET actual=?,response_sha256=?,state=? WHERE id=?',
                            (actual,response_sha256,'overrun' if overrun else 'settled',call_id))
            if overrun:self.db.execute('UPDATE runs SET blocked=1 WHERE id=?',(row[0],))
        if overrun:raise BudgetError('actual bill exceeded quote; recorded and run blocked')
