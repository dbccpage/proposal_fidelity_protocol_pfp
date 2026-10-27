"""Two independent SQLite connections must not own one live delivery lease."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from operads.infrastructure.storage.sqlite_unit_of_work import (
    SqliteUnitOfWork,
)


def seed(path):
    with SqliteUnitOfWork(str(path)):
        pass
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO events_v3 VALUES ('e','s','event','c','c','now','{}')")
        db.execute("INSERT INTO outbox_v3(outbox_id,event_id,destination,created_at) VALUES ('o','e','topic','now')")


def test_exclusion_expiration_and_fenced_ack(tmp_path):
    path = tmp_path / "delivery.db"
    seed(path)
    with SqliteUnitOfWork(str(path)) as first, SqliteUnitOfWork(str(path)) as second:
        old = first.claim_pending_outbox("worker-one", now=100.0, lease_seconds=10).unwrap()[0]
        assert second.fetch_pending_outbox().unwrap() == ()
        assert second.mark_outbox_delivered("o").is_err
        assert second.claim_pending_outbox("worker-two", now=109.0).unwrap() == ()
        new = second.claim_pending_outbox("worker-two", now=111.0).unwrap()[0]
        assert new["lease_token"] != old["lease_token"]
        assert first.finish_outbox_lease("o", old["lease_token"], now=112.0).is_err
        assert second.finish_outbox_lease("o", new["lease_token"], now=112.0).is_ok
        assert first.fetch_pending_outbox().unwrap() == ()


def test_failed_delivery_backs_off_and_reopen_preserves_attempts(tmp_path):
    path = tmp_path / "delivery.db"
    seed(path)
    with SqliteUnitOfWork(str(path)) as worker:
        row = worker.claim_pending_outbox("one", now=100.0).unwrap()[0]
        assert worker.finish_outbox_lease("o", row["lease_token"], now=101.0, retry_after=5.0).is_ok
    with SqliteUnitOfWork(str(path)) as reopened:
        assert reopened.claim_pending_outbox("two", now=105.0).unwrap() == ()
        row = reopened.claim_pending_outbox("two", now=106.0).unwrap()[0]
        assert row["attempt_count"] == 2


def test_invalid_clock_and_lease_refuse_without_claiming(tmp_path):
    path = tmp_path / "delivery.db"
    seed(path)
    with SqliteUnitOfWork(str(path)) as worker:
        for clock in (float("nan"), float("inf"), -1.0):
            assert worker.claim_pending_outbox("one", now=clock).is_err
        assert worker.claim_pending_outbox("one", now=100.0, lease_seconds=0).is_err
        assert worker.claim_pending_outbox("one", now=100.0).unwrap()[0]["attempt_count"] == 1


def test_real_process_workers_cannot_claim_same_live_row(tmp_path):
    path = tmp_path / "delivery.db"
    seed(path)
    code = '''
import json,sys
from operads.infrastructure.storage.sqlite_unit_of_work import SqliteUnitOfWork
with SqliteUnitOfWork(sys.argv[1]) as worker:
    print(json.dumps(worker.claim_pending_outbox(sys.argv[2],now=100.0).unwrap()))
'''
    workers = [subprocess.Popen([sys.executable, "-c", code, str(path), name],
        cwd=Path(__file__).resolve().parents[3], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for name in ("one", "two")]
    claims = []
    for worker in workers:
        stdout, stderr = worker.communicate(timeout=30)
        assert worker.returncode == 0, stderr.decode(errors="replace")
        claims.extend(json.loads(stdout))
    assert len(claims) == 1
