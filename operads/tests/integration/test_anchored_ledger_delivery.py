"""Signed external pins, real process interruption and duplicate delivery."""

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from operads.infrastructure.storage.anchored_ledger_subscriber import (
    AnchoredLedgerSubscriber,
)
from operads.infrastructure.storage.receipt_ledger import LedgerError

KEY = b"development-test-key-only-32-bytes"
ROOT = Path(__file__).resolve().parents[3]


def event(identifier="event-one"):
    return dict(event_id=identifier, destination="events.oewas.v3", payload_json='{"value":7}')


def open_subscriber(tmp_path, key=KEY):
    return AnchoredLedgerSubscriber(str(tmp_path / "events.db"), tmp_path / "retained" / "tip.json", key, "development")


def test_reopen_duplicate_and_conflicting_event(tmp_path):
    subscriber = open_subscriber(tmp_path)
    assert subscriber(event()).is_ok
    tip = subscriber.path.read_bytes()
    subscriber.close()
    reopened = open_subscriber(tmp_path)
    try:
        assert reopened(event()).is_ok
        assert len(reopened.ledger) == 1
        assert reopened.path.read_bytes() == tip
        assert reopened(dict(event(), payload_json='{"value":8}')).is_err
        assert len(reopened.ledger) == 1
    finally:
        reopened.close()


def test_forged_tip_and_wrong_key_refuse_without_repin(tmp_path):
    subscriber = open_subscriber(tmp_path)
    assert subscriber(event()).is_ok
    path = subscriber.path
    subscriber.close()
    with pytest.raises(LedgerError, match="AUTHENTICATION"):
        open_subscriber(tmp_path, b"wrong-development-key-32-bytes!!!")
    wire = json.loads(path.read_bytes())
    wire["body"]["tip"] = "0" * 64
    path.write_text(json.dumps(wire), encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(LedgerError, match="AUTHENTICATION"):
        open_subscriber(tmp_path)
    assert path.read_bytes() == before


def test_tail_truncation_and_lost_pin_refuse(tmp_path):
    subscriber = open_subscriber(tmp_path)
    assert subscriber(event()).is_ok
    assert subscriber(event("event-two")).is_ok
    path = subscriber.path
    pin = path.read_bytes()
    subscriber.close()
    with sqlite3.connect(tmp_path / "events.db") as db:
        db.execute("DROP TRIGGER receipt_ledger_v1_no_delete")
        db.execute("DELETE FROM receipt_ledger_v1 WHERE sequence=2")
    with pytest.raises(LedgerError, match="INCOMPLETE"):
        open_subscriber(tmp_path)
    assert path.read_bytes() == pin
    path.unlink()
    with pytest.raises(LedgerError, match="MISSING"):
        open_subscriber(tmp_path)
    assert not path.exists()


def test_real_process_death_after_database_commit_recovers_signed_intent(tmp_path):
    child = '''
import os, sys
from pathlib import Path
from operads.infrastructure.storage.anchored_ledger_subscriber import AnchoredLedgerSubscriber
class Interrupted(AnchoredLedgerSubscriber):
    def _write(self,path,body):
        if path == self.path and body.get("sequence",0) > 0:
            os._exit(43)
        return super()._write(path,body)
root=Path(sys.argv[1])
s=Interrupted(str(root/"events.db"),root/"retained"/"tip.json",b"development-test-key-only-32-bytes","development")
s(dict(event_id="event-one",destination="events.oewas.v3",payload_json='{"value":7}'))
'''
    outcome = subprocess.run([sys.executable, "-c", child, str(tmp_path)], cwd=ROOT, capture_output=True, timeout=30)
    assert outcome.returncode == 43, outcome.stderr.decode(errors="replace")
    assert (tmp_path / "retained/tip.json.pending").is_file()
    recovered = open_subscriber(tmp_path)
    try:
        assert len(recovered.ledger) == 1
        assert recovered(event()).is_ok
        assert len(recovered.ledger) == 1
        assert not recovered.pending.exists()
    finally:
        recovered.close()


def test_hardlinked_pin_refuses_before_write(tmp_path):
    import os
    subscriber = open_subscriber(tmp_path)
    path = subscriber.path
    subscriber.close()
    os.link(path, tmp_path / "foreign-tip")
    before = path.read_bytes()
    with pytest.raises(LedgerError, match="PATH_UNSAFE"):
        open_subscriber(tmp_path)
    assert path.read_bytes() == before


def test_memory_database_and_absent_trust_refuse(tmp_path):
    with pytest.raises(LedgerError, match="FILE_DB"):
        AnchoredLedgerSubscriber(":memory:", tmp_path / "tip", KEY, "development")
    with pytest.raises(LedgerError, match="TRUST"):
        AnchoredLedgerSubscriber(str(tmp_path / "db"), tmp_path / "tip", b"short", "development")


@pytest.mark.parametrize("suffix", ["", ".pending", ".lock"])
def test_tip_files_cannot_alias_database_before_any_write(tmp_path, suffix):
    with pytest.raises(LedgerError, match="TIP_PATH_UNSAFE"):
        AnchoredLedgerSubscriber(str(tmp_path / ("tip" + suffix)), tmp_path / "tip", KEY, "development")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_linked_sqlite_sidecar_refuses_before_database_open(tmp_path, suffix):
    import os

    from operads.infrastructure.bootstrap import OeopContainer
    foreign = tmp_path / "outside"
    foreign.write_bytes(b"outside sentinel")
    db = tmp_path / "events.db"
    os.link(foreign, Path(str(db) + suffix))
    with pytest.raises(LedgerError, match="TIP_PATH_UNSAFE"):
        open_subscriber(tmp_path)
    with pytest.raises(LedgerError, match="TIP_PATH_UNSAFE"):
        OeopContainer(db_path=str(db))
    assert foreign.read_bytes() == b"outside sentinel"
    assert not db.exists()


def test_public_cli_dispatch_reopen_and_zero_duplicate_receipts(tmp_path):
    from operads.tests.integration.test_outbox_worker_leases import (
        seed,
    )
    db_path = tmp_path / "delivery.db"
    seed(db_path)
    with sqlite3.connect(db_path) as db:
        db.execute("UPDATE outbox_v3 SET destination='events.oewas.v3'")
    key_path = tmp_path / "operator.key"
    key_path.write_bytes(KEY)
    command = [sys.executable, "-m", "operads.frontend.cli",
        "--workspace", str(ROOT), "--db-path", str(db_path), "--json", "dispatch-events",
        "--tip-path", str(tmp_path / "retained/tip.json"), "--tip-key-file", str(key_path),
        "--ledger-id", "development"]
    first = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30)
    assert first.returncode == 0, first.stderr.decode(errors="replace") + first.stdout.decode(errors="replace")
    assert json.loads(first.stdout)["delivered_count"] == 1
    second = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30)
    assert second.returncode == 0
    assert json.loads(second.stdout)["delivered_count"] == 0
    with sqlite3.connect(db_path) as db:
        assert db.execute("SELECT count(*) FROM receipt_ledger_v1").fetchone()[0] == 1


def test_public_cli_alias_configuration_refuses_without_database_creation(tmp_path):
    key = tmp_path / "operator.key"
    key.write_bytes(KEY)
    database = tmp_path / "tip.pending"
    command = [sys.executable, "-m", "operads.frontend.cli",
        "--db-path", str(database), "--json", "dispatch-events", "--tip-path", str(tmp_path / "tip"),
        "--tip-key-file", str(key), "--ledger-id", "development"]
    observed = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=30)
    assert observed.returncode == 1
    assert json.loads(observed.stdout)["code"] == "TIP_PATH_UNSAFE"
    assert not database.exists()
    assert not (tmp_path / "tip").exists()
