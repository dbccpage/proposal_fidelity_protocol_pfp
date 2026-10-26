"""Typed subscriber outcomes must not be acknowledged as success."""

from datetime import datetime, timezone

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
from omega_engine_operads.infrastructure.storage.sqlite_unit_of_work import (
    SqliteUnitOfWork,
)


def seed(uow):
    catalog = EstateCatalogV3(
        catalog_id="cat",
        estate_ref=EstateRef("fixture"),
        epoch=1,
        compiled_at=datetime.now(timezone.utc),
        skills={},
        operations={},
        capability_slices={},
        aliases={},
        catalog_digest=ContentDigest.empty_sha256(),
    )
    event = EstateCapturedV3.create(event_id="event:1", correlation_id="corr", causation_id="cause")
    assert uow.save_catalog(catalog, (event,)).is_ok


def test_typed_subscriber_refusal_remains_pending_after_reopen(tmp_path):
    db = tmp_path / "outbox.sqlite3"
    with SqliteUnitOfWork(str(db)) as uow:
        seed(uow)
        dispatcher = OutboxMessageDispatcher(uow)
        dispatcher.subscribe(
            "events.oewas.v3",
            lambda message: Err(
                DomainInvariantError(
                    code="INBOX_EFFECT_REFUSED", message="No durable effect committed"
                )
            ),
        )
        report = dispatcher.dispatch_pending().unwrap()
        assert report.delivered_count == 0
        assert report.failed_count == 1
        assert "INBOX_EFFECT_REFUSED" in report.errors[0]
    with SqliteUnitOfWork(str(db)) as reopened:
        assert len(reopened.fetch_pending_outbox().unwrap()) == 1
        recovered = OutboxMessageDispatcher(reopened)
        recovered.subscribe("events.oewas.v3", lambda message: Ok(None))
        assert recovered.dispatch_pending().unwrap().delivered_count == 1
        assert reopened.fetch_pending_outbox().unwrap() == ()


@pytest.mark.parametrize("outcome", [False, True, 7, {}, "accepted"])
def test_unknown_subscriber_return_cannot_acknowledge(outcome, tmp_path):
    with SqliteUnitOfWork(str(tmp_path / "outbox.sqlite3")) as uow:
        seed(uow)
        dispatcher = OutboxMessageDispatcher(uow)
        dispatcher.subscribe("events.oewas.v3", lambda message: outcome)
        report = dispatcher.dispatch_pending().unwrap()
        assert report.delivered_count == 0
        assert report.failed_count == 1
        assert len(uow.fetch_pending_outbox().unwrap()) == 1


@pytest.mark.parametrize("outcome", [None, Ok(None)])
def test_legacy_none_and_typed_ok_still_acknowledge(outcome, tmp_path):
    with SqliteUnitOfWork(str(tmp_path / "outbox.sqlite3")) as uow:
        seed(uow)
        dispatcher = OutboxMessageDispatcher(uow)
        dispatcher.subscribe("events.oewas.v3", lambda message: outcome)
        assert dispatcher.dispatch_pending().unwrap().delivered_count == 1
        assert uow.fetch_pending_outbox().unwrap() == ()
