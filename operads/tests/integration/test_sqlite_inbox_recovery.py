"""File-backed SQLite-local inbox effects; no external exactly-once claim."""

import hashlib
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from omega_engine_operations.domain.rop.result import Err, Ok
from omega_engine_operads.domain.entities.catalog_v3 import EstateCatalogV3
from omega_engine_operads.domain.errors.domain_errors import DomainInvariantError
from omega_engine_operads.domain.events.domain_events import EstateCapturedV3
from omega_engine_operads.domain.value_objects.content_digest import ContentDigest
from omega_engine_operads.domain.value_objects.identifier import EstateRef
from omega_engine_operads.infrastructure.storage.outbox_dispatcher import (
    OutboxMessageDispatcher,
)
from omega_engine_operads.infrastructure.storage.sqlite_inbox_subscriber import (
    SqliteInboxSubscriber,
)
from omega_engine_operads.infrastructure.storage.sqlite_unit_of_work import (
    SqliteUnitOfWork,
)


def envelope():
    return {
        "outbox_id": "delivery:1",
        "created_at": "2026-10-10T00:00:00Z",
        "event_id": "event:1",
        "destination": "events.oewas.v3",
        "stream_id": "catalog:1",
        "event_type": "EstateCapturedV3",
        "correlation_id": "corr",
        "causation_id": "cause",
        "occurred_at": "2026-10-10T00:00:00Z",
        "payload_json": '{"event_type":"EstateCapturedV3"}',
    }


def make_effect_table(path):
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE local_effects (event_id TEXT NOT NULL)")


def apply_effect(connection, event):
    connection.execute("INSERT INTO local_effects VALUES (?)", (event["event_id"],))


def counts(path):
    with sqlite3.connect(path) as connection:
        return (
            connection.execute("SELECT count(*) FROM local_effects").fetchone()[0],
            connection.execute("SELECT count(*) FROM subscriber_inbox_v1").fetchone()[0],
        )


def test_duplicate_after_reopen_has_one_durable_effect(tmp_path):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)
    with SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as subscriber:
        assert subscriber(envelope()).is_ok
    assert counts(path) == (1, 1)

    redelivery = dict(envelope(), outbox_id="delivery:2", created_at="2026-10-11T00:00:00Z")
    with SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as reopened:
        assert reopened(redelivery).is_ok
    assert counts(path) == (1, 1)


@pytest.mark.parametrize("transaction_control", ["commit", "rollback", "executescript"])
def test_callback_cannot_end_the_effect_and_inbox_transaction(tmp_path, transaction_control):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)

    def unpermitted_effect(connection, event):
        apply_effect(connection, event)
        if transaction_control == "executescript":
            connection.executescript("SELECT 1;")
        else:
            getattr(connection, transaction_control)()

    with SqliteInboxSubscriber(path, "catalog-projection", unpermitted_effect) as subscriber:
        outcome = subscriber(envelope())
        assert outcome.is_err
    assert counts(path) == (0, 0)
    with SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as recovered:
        assert recovered(envelope()).is_ok
    assert counts(path) == (1, 1)


@pytest.mark.parametrize("ambiguous_payload", [{1: "value"}, ("a", "b"), float("nan")])
def test_non_json_or_ambiguous_envelope_is_refused(tmp_path, ambiguous_payload):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)
    with SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as subscriber:
        result = subscriber(dict(envelope(), payload=ambiguous_payload))
        assert result.is_err
        assert result.unwrap_err().code == "INBOX_INVALID_EVENT"
    assert counts(path) == (0, 0)


@pytest.mark.parametrize(
    "field",
    [
        "destination",
        "stream_id",
        "event_type",
        "correlation_id",
        "causation_id",
        "occurred_at",
        "payload_json",
        "additional_field",
    ],
)
def test_same_id_changed_event_envelope_cannot_be_transplanted(tmp_path, field):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)
    with SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as subscriber:
        assert subscriber(envelope()).is_ok
        conflict = subscriber(dict(envelope(), **{field: "changed"}))
        assert conflict.is_err
        assert conflict.unwrap_err().code == "INBOX_EVENT_CONFLICT"
        assert subscriber(envelope()).is_ok
    assert counts(path) == (1, 1)


@pytest.mark.parametrize("invalid_id", [None, "", " ", " event:1", 1, False, ["event:1"]])
def test_invalid_event_identity_cannot_create_effect_or_inbox_row(tmp_path, invalid_id):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)
    with SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as subscriber:
        invalid = subscriber(dict(envelope(), event_id=invalid_id))
        assert invalid.is_err
        assert invalid.unwrap_err().code == "INBOX_INVALID_EVENT"
        missing = dict(envelope())
        del missing["event_id"]
        assert subscriber(missing).is_err
    assert counts(path) == (0, 0)


@pytest.mark.parametrize("name", [None, "", " ", " name", 1])
def test_subscriber_identity_must_be_stable_and_unambiguous(tmp_path, name):
    with pytest.raises(ValueError, match="subscriber_name"):
        SqliteInboxSubscriber(str(tmp_path / "inbox.sqlite3"), name, apply_effect)


def test_one_event_can_belong_to_two_explicitly_named_consumers(tmp_path):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)
    with SqliteInboxSubscriber(path, "projection-a", apply_effect) as first:
        assert first(envelope()).is_ok
    with SqliteInboxSubscriber(path, "projection-b", apply_effect) as second:
        assert second(envelope()).is_ok
        assert second(envelope()).is_ok
    assert counts(path) == (2, 2)


@pytest.mark.parametrize("failure", ["exception", "typed_refusal", "unknown_return"])
def test_local_effect_failure_rolls_back_and_can_retry(tmp_path, failure):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)

    def failed_effect(connection, event):
        apply_effect(connection, event)
        if failure == "exception":
            raise RuntimeError("local effect failed after INSERT")
        if failure == "typed_refusal":
            return Err(DomainInvariantError(code="PROJECTION_REFUSED", message="retry later"))
        return False

    with SqliteInboxSubscriber(path, "catalog-projection", failed_effect) as subscriber:
        result = subscriber(envelope())
        assert result.is_err
        expected = {
            "exception": "INBOX_EFFECT_FAILED",
            "typed_refusal": "PROJECTION_REFUSED",
            "unknown_return": "INBOX_EFFECT_RESULT_INVALID",
        }
        assert result.unwrap_err().code == expected[failure]
    assert counts(path) == (0, 0)
    with SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as recovered:
        assert recovered(envelope()).is_ok
    assert counts(path) == (1, 1)


@pytest.mark.parametrize(
    "sql",
    [
        "SAVEPOINT callback_savepoint",
        "PRAGMA synchronous=OFF",
        "ATTACH DATABASE ':memory:' AS other",
        "DELETE FROM subscriber_inbox_v1",
        "DROP TABLE local_effects",
    ],
)
def test_callback_cannot_reconfigure_database_or_modify_inbox(tmp_path, sql):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)

    def unpermitted_effect(connection, event):
        apply_effect(connection, event)
        connection.execute(sql)

    with SqliteInboxSubscriber(path, "catalog-projection", unpermitted_effect) as subscriber:
        assert subscriber(envelope()).is_err
    assert counts(path) == (0, 0)


def test_callback_gets_only_a_detached_bound_event_envelope(tmp_path):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)
    message = dict(envelope(), payload={"nested": ["original"]})

    def effect(connection, event):
        assert "outbox_id" not in event
        assert "created_at" not in event
        event["payload"]["nested"].append("local callback mutation")
        apply_effect(connection, event)
        return Ok(None)

    with SqliteInboxSubscriber(path, "catalog-projection", effect) as subscriber:
        assert subscriber(message).is_ok
        assert message["payload"] == {"nested": ["original"]}
        assert subscriber(dict(reversed(list(message.items())))).is_ok
    assert counts(path) == (1, 1)


def seed_outbox(path, *, document_count=0):
    with SqliteUnitOfWork(path) as uow:
        catalog = EstateCatalogV3(
            catalog_id="cat:crash",
            estate_ref=EstateRef("fixture"),
            epoch=1,
            compiled_at=datetime.now(timezone.utc),
            skills={},
            operations={},
            capability_slices={},
            aliases={},
            catalog_digest=ContentDigest.empty_sha256(),
        )
        event = EstateCapturedV3.create(
            event_id="event:crash", correlation_id="corr", causation_id="cause",
            document_count=document_count,
        )
        assert uow.save_catalog(catalog, (event,)).is_ok


CRASH_WORKER = r"""
import os
import sys
from omega_engine_operads.infrastructure.storage.outbox_dispatcher import OutboxMessageDispatcher
from omega_engine_operads.infrastructure.storage.sqlite_inbox_subscriber import SqliteInboxSubscriber
from omega_engine_operads.infrastructure.storage.sqlite_unit_of_work import SqliteUnitOfWork

path, phase = sys.argv[1:]
def local_effect(connection, event):
    connection.execute("INSERT INTO local_effects VALUES (?)", (event["event_id"],))
    if phase == "before_commit":
        os._exit(72)

with SqliteUnitOfWork(path) as uow, SqliteInboxSubscriber(path, "catalog-projection", local_effect) as subscriber:
    def receive(message):
        result = subscriber(message)
        if result.is_err:
            print(result.unwrap_err(), file=sys.stderr, flush=True)
            os._exit(74)
        os._exit(73)  # Inbox+effect committed; dispatcher has not acknowledged.
    dispatcher = OutboxMessageDispatcher(uow)
    dispatcher.subscribe("events.oewas.v3", receive)
    dispatcher.dispatch_pending()
os._exit(75)  # No pending delivery reached the intended crash boundary.
"""


@pytest.mark.parametrize(
    "phase, exit_code, before_replay",
    [
        ("before_commit", 72, (0, 0)),
        ("after_commit", 73, (1, 1)),
    ],
)
def test_real_process_crash_redelivers_then_acknowledges_once(
    tmp_path, phase, exit_code, before_replay
):
    path = str(tmp_path / "recovery.sqlite3")
    seed_outbox(path)
    make_effect_table(path)
    worker = subprocess.run(
        [sys.executable, "-X", "utf8", "-c", CRASH_WORKER, path, phase],
        cwd=Path(__file__).resolve().parents[3],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert worker.returncode == exit_code, worker.stdout + worker.stderr
    assert counts(path) == before_replay
    with (
        SqliteUnitOfWork(path) as uow,
        SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as subscriber,
    ):
        assert len(uow.fetch_pending_outbox().unwrap()) == 1
        dispatcher = OutboxMessageDispatcher(uow)
        dispatcher.subscribe("events.oewas.v3", subscriber)
        report = dispatcher.dispatch_pending().unwrap()
        assert (report.delivered_count, report.failed_count) == (1, 0)
        assert uow.fetch_pending_outbox().unwrap() == ()
        assert dispatcher.dispatch_pending().unwrap().total_polled == 0
    assert counts(path) == (1, 1)


def test_inbox_insert_constraint_refusal_rolls_back_the_local_effect(tmp_path):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)
    with SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as subscriber:
        with sqlite3.connect(path) as connection:
            connection.execute("""CREATE TRIGGER refuse_inbox BEFORE INSERT ON subscriber_inbox_v1
                BEGIN SELECT RAISE(ABORT, 'inbox refused'); END""")
        failed = subscriber(envelope())
        assert failed.is_err
        assert failed.unwrap_err().code == "INBOX_EFFECT_FAILED"
        assert counts(path) == (0, 0)
        with sqlite3.connect(path) as connection:
            connection.execute("DROP TRIGGER refuse_inbox")
        assert subscriber(envelope()).is_ok
    assert counts(path) == (1, 1)


def test_dispatcher_local_failure_reopens_pending_then_recovers(tmp_path):
    path = str(tmp_path / "outbox.sqlite3")
    seed_outbox(path)
    make_effect_table(path)

    def refused_effect(connection, event):
        apply_effect(connection, event)
        return Err(DomainInvariantError(code="LOCAL_PROJECTION_REFUSED", message="retry later"))

    with (
        SqliteUnitOfWork(path) as uow,
        SqliteInboxSubscriber(path, "catalog-projection", refused_effect) as subscriber,
    ):
        dispatcher = OutboxMessageDispatcher(uow)
        dispatcher.subscribe("events.oewas.v3", subscriber)
        report = dispatcher.dispatch_pending().unwrap()
        assert (report.delivered_count, report.failed_count) == (0, 1)
        assert "LOCAL_PROJECTION_REFUSED" in report.errors[0]
    assert counts(path) == (0, 0)
    with (
        SqliteUnitOfWork(path) as uow,
        SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as subscriber,
    ):
        assert len(uow.fetch_pending_outbox().unwrap()) == 1
        dispatcher = OutboxMessageDispatcher(uow)
        dispatcher.subscribe("events.oewas.v3", subscriber)
        assert dispatcher.dispatch_pending().unwrap().delivered_count == 1
        assert uow.fetch_pending_outbox().unwrap() == ()
    assert counts(path) == (1, 1)


def test_pending_same_id_changed_payload_is_refused_then_original_can_ack(tmp_path):
    path = str(tmp_path / "outbox.sqlite3")
    seed_outbox(path, document_count=3)
    make_effect_table(path)
    with (
        SqliteUnitOfWork(path) as uow,
        SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as subscriber,
    ):
        message = uow.fetch_pending_outbox().unwrap()[0]
        original_payload = json.loads(message["payload_json"])
        assert original_payload["document_count"] == 3
        assert original_payload["event_id"] == message["event_id"]
        assert subscriber(message).is_ok  # Local commit, deliberately no ack yet.
        changed_payload = dict(original_payload, document_count=4)
        with sqlite3.connect(path) as connection:
            connection.execute(
                "UPDATE events_v3 SET payload_json=? WHERE event_id=?",
                (json.dumps(changed_payload), message["event_id"]),
            )
        dispatcher = OutboxMessageDispatcher(uow)
        dispatcher.subscribe("events.oewas.v3", subscriber)
        report = dispatcher.dispatch_pending().unwrap()
        assert (report.delivered_count, report.failed_count) == (0, 1)
        assert "INBOX_EVENT_CONFLICT" in report.errors[0]
        assert len(uow.fetch_pending_outbox().unwrap()) == 1
        assert counts(path) == (1, 1)
        with sqlite3.connect(path) as connection:
            connection.execute(
                "UPDATE events_v3 SET payload_json=? WHERE event_id=?",
                (message["payload_json"], message["event_id"]),
            )
        assert dispatcher.dispatch_pending().unwrap().delivered_count == 1
        assert uow.fetch_pending_outbox().unwrap() == ()
    assert counts(path) == (1, 1)


def test_inbox_digest_matches_independent_literal_profile_bytes(tmp_path):
    path = str(tmp_path / "inbox.sqlite3")
    make_effect_table(path)
    event = {"payload": {"value": "é"}, "event_id": "event:1", "outbox_id": "delivery:1"}
    expected_bytes = '{"event_id":"event:1","payload":{"value":"é"}}'.encode("utf-8")
    expected_digest = hashlib.sha256(b"oewas.inbox.envelope.v1\0" + expected_bytes).hexdigest()
    with SqliteInboxSubscriber(path, "catalog-projection", apply_effect) as subscriber:
        assert subscriber(event).is_ok
    with sqlite3.connect(path) as connection:
        stored_digest = connection.execute(
            "SELECT envelope_digest FROM subscriber_inbox_v1"
        ).fetchone()[0]
    assert stored_digest == expected_digest
    assert counts(path) == (1, 1)
