"""Integration test for OutboxMessageDispatcher verifying at-least-once delivery and idempotency."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from operads.domain.entities.catalog_v3 import EstateCatalogV3
from operads.domain.events.domain_events import (
    CatalogCompiledV3,
    DocumentImportedV3,
    EstateCapturedV3,
)
from operads.domain.value_objects.content_digest import ContentDigest
from operads.domain.value_objects.identifier import (
    EstateRef,
)
from operads.infrastructure.storage.outbox_dispatcher import (
    OutboxMessageDispatcher,
)
from operads.infrastructure.storage.sqlite_unit_of_work import (
    SqliteUnitOfWork,
)


class TestOutboxMessageDispatcher(unittest.TestCase):
    def setUp(self) -> None:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = Path(self._temp_dir.name)
        self.db_path = str(self.workspace_root / "outbox_dispatch.db")
        self.uow = SqliteUnitOfWork(self.db_path)
        self.dispatcher = OutboxMessageDispatcher(self.uow)

    def tearDown(self) -> None:
        self.uow.close()
        self._temp_dir.cleanup()

    def test_successful_dispatch_delivers_and_marks_outbox(self) -> None:
        # 1. Populate database with catalog and 2 events
        now = datetime.now(timezone.utc)
        catalog = EstateCatalogV3(
            catalog_id="cat_dispatch_01",
            estate_ref=EstateRef("canonical"),
            epoch=1,
            compiled_at=now,
            skills={},
            operations={},
            capability_slices={},
            aliases={},
            catalog_digest=ContentDigest.empty_sha256(),
        )
        evt1 = EstateCapturedV3.create(
            event_id="evt_d_01",
            correlation_id="corr-d-01",
            causation_id="cause-d-01",
        )
        evt2 = CatalogCompiledV3.create(
            event_id="evt_d_02",
            correlation_id="corr-d-01",
            causation_id="cause-d-01",
            catalog_id="cat_dispatch_01",
        )
        self.uow.save_catalog(catalog, (evt1, evt2))

        # 2. Register subscriber
        received_events: list[dict] = []
        self.dispatcher.subscribe("events.oewas.v3", lambda msg: received_events.append(msg))

        # 3. Dispatch pending outbox messages
        report_res = self.dispatcher.dispatch_pending()
        self.assertTrue(report_res.is_ok)
        report = report_res.unwrap()

        self.assertEqual(report.total_polled, 2)
        self.assertEqual(report.delivered_count, 2)
        self.assertEqual(report.failed_count, 0)
        self.assertEqual(len(received_events), 2)
        self.assertEqual(received_events[0]["event_id"], "evt_d_01")
        self.assertEqual(received_events[1]["event_id"], "evt_d_02")

        # 4. Assert subsequent poll returns 0 pending messages
        pending_res = self.uow.fetch_pending_outbox()
        self.assertTrue(pending_res.is_ok)
        self.assertEqual(len(pending_res.unwrap()), 0)

    def test_subscriber_failure_retains_message_for_at_least_once_retry(self) -> None:
        now = datetime.now(timezone.utc)
        catalog = EstateCatalogV3(
            catalog_id="cat_retry_01",
            estate_ref=EstateRef("canonical"),
            epoch=1,
            compiled_at=now,
            skills={},
            operations={},
            capability_slices={},
            aliases={},
            catalog_digest=ContentDigest.empty_sha256(),
        )
        evt = DocumentImportedV3.create(
            event_id="evt_retry_01",
            correlation_id="corr-r-01",
            causation_id="cause-r-01",
        )
        self.uow.save_catalog(catalog, (evt,))

        attempt_count = 0

        def flaky_subscriber(msg: dict) -> None:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise ConnectionError("Simulated temporary network partition")
            # Succeeds on second attempt

        self.dispatcher.subscribe("events.oewas.v3", flaky_subscriber)

        # Attempt 1: Should fail and leave message in outbox
        report1 = self.dispatcher.dispatch_pending().unwrap()
        self.assertEqual(report1.total_polled, 1)
        self.assertEqual(report1.failed_count, 1)
        self.assertEqual(report1.delivered_count, 0)

        # Verify still in pending outbox
        self.assertEqual(len(self.uow.fetch_pending_outbox().unwrap()), 1)

        # Attempt 2: Re-attempt dispatch -> succeeds and marks delivered
        report2 = self.dispatcher.dispatch_pending().unwrap()
        self.assertEqual(report2.total_polled, 1)
        self.assertEqual(report2.failed_count, 0)
        self.assertEqual(report2.delivered_count, 1)

        # Verify outbox is now empty
        self.assertEqual(len(self.uow.fetch_pending_outbox().unwrap()), 0)

    def test_subscriber_idempotency_deduplication(self) -> None:
        now = datetime.now(timezone.utc)
        catalog = EstateCatalogV3(
            catalog_id="cat_idem_01",
            estate_ref=EstateRef("canonical"),
            epoch=1,
            compiled_at=now,
            skills={},
            operations={},
            capability_slices={},
            aliases={},
            catalog_digest=ContentDigest.empty_sha256(),
        )
        evt = EstateCapturedV3.create(
            event_id="evt_idem_99",
            correlation_id="corr-idem-99",
            causation_id="cause-idem-99",
        )
        self.uow.save_catalog(catalog, (evt,))

        processed_events: set[str] = set()
        execution_count = 0

        def idempotent_consumer(msg: dict) -> None:
            nonlocal execution_count
            event_id = msg["event_id"]
            if event_id in processed_events:
                # Deduplicated: do not re-execute side effects
                return
            processed_events.add(event_id)
            execution_count += 1

        self.dispatcher.subscribe("events.oewas.v3", idempotent_consumer)

        # First dispatch
        self.dispatcher.dispatch_pending()
        self.assertEqual(execution_count, 1)

        # Simulate redelivery / duplicate dispatch of the same message payload
        fake_duplicate_msg = {"event_id": "evt_idem_99", "destination": "events.oewas.v3"}
        idempotent_consumer(fake_duplicate_msg)

        # Assert execution count is unchanged (deduplicated)
        self.assertEqual(execution_count, 1)
        self.assertEqual(len(processed_events), 1)


    def _seed_one_event(self, catalog_id: str, event_id: str) -> None:
        now = datetime.now(timezone.utc)
        catalog = EstateCatalogV3(
            catalog_id=catalog_id,
            estate_ref=EstateRef("canonical"),
            epoch=1,
            compiled_at=now,
            skills={},
            operations={},
            capability_slices={},
            aliases={},
            catalog_digest=ContentDigest.empty_sha256(),
        )
        evt = EstateCapturedV3.create(
            event_id=event_id,
            correlation_id="corr-ns-01",
            causation_id="cause-ns-01",
        )
        self.uow.save_catalog(catalog, (evt,))

    def test_no_subscriber_leaves_the_message_pending(self) -> None:
        """A message nobody received is not a delivered message.

        The dispatcher used to mark it delivered. `fetch_pending_outbox`
        filters on `delivered_at IS NULL`, so it was never offered again --
        a subscriber registering later, the ordinary startup case, silently
        lost every event queued before it.

        Mutation: restore `mark_outbox_delivered` in the no-handler branch and
        this fails on both the count and the surviving pending row.
        """
        self._seed_one_event("cat_nosub_01", "evt_nosub_01")

        report = self.dispatcher.dispatch_pending().unwrap()

        self.assertEqual(report.total_polled, 1)
        self.assertEqual(report.delivered_count, 0, "nothing was delivered")
        self.assertEqual(report.failed_count, 0, "nothing failed either")
        self.assertEqual(report.undeliverable_count, 1)

        pending = self.uow.fetch_pending_outbox().unwrap()
        self.assertEqual(len(pending), 1, "the message must remain pending")
        self.assertEqual(pending[0]["event_id"], "evt_nosub_01")

    def test_a_late_subscriber_still_receives_the_event(self) -> None:
        """The consequence that makes the defect matter.

        Dispatch with no subscriber, then register one and dispatch again. The
        event must arrive. Under the old behaviour it was already marked
        delivered and gone.
        """
        self._seed_one_event("cat_late_01", "evt_late_01")

        first = self.dispatcher.dispatch_pending().unwrap()
        self.assertEqual(first.undeliverable_count, 1)

        received: list[dict] = []
        self.dispatcher.subscribe("events.oewas.v3", lambda msg: received.append(msg))

        second = self.dispatcher.dispatch_pending().unwrap()
        self.assertEqual(second.delivered_count, 1)
        self.assertEqual(second.undeliverable_count, 0)
        self.assertEqual([m["event_id"] for m in received], ["evt_late_01"])

        self.assertEqual(len(self.uow.fetch_pending_outbox().unwrap()), 0)

    def test_pending_unsubscribed_messages_do_not_starve_a_bounded_poll(self) -> None:
        """A retained no-subscriber record must not block a later delivery.

        The older undeliverable record is deliberately first in created_at
        order. With a one-message limit, the dispatcher must select the later
        subscribed event instead of repeatedly polling the earlier one.
        """
        self._seed_one_event("cat_starve_01", "evt_starve_unsubscribed")
        self._seed_one_event("cat_starve_02", "evt_starve_deliverable")
        with self.uow._conn:
            self.uow._conn.execute(
                "UPDATE outbox_v3 SET destination = ?, created_at = ? WHERE event_id = ?",
                ("events.no_subscriber", "2020-01-01T00:00:00+00:00", "evt_starve_unsubscribed"),
            )
            self.uow._conn.execute(
                "UPDATE outbox_v3 SET created_at = ? WHERE event_id = ?",
                ("2020-01-02T00:00:00+00:00", "evt_starve_deliverable"),
            )

        received: list[dict] = []
        self.dispatcher.subscribe("events.oewas.v3", lambda msg: received.append(msg))
        report = self.dispatcher.dispatch_pending(limit=1).unwrap()

        self.assertEqual(report.total_polled, 1)
        self.assertEqual(report.delivered_count, 1)
        self.assertEqual(report.undeliverable_count, 0)
        self.assertEqual([msg["event_id"] for msg in received], ["evt_starve_deliverable"])
        pending = self.uow.fetch_pending_outbox().unwrap()
        self.assertEqual([msg["event_id"] for msg in pending], ["evt_starve_unsubscribed"])

    def test_a_subscribed_destination_is_not_reported_undeliverable(self) -> None:
        """Negative control.

        Without it, a dispatcher that reported everything undeliverable and
        delivered nothing would pass both tests above.
        """
        self._seed_one_event("cat_ctrl_01", "evt_ctrl_01")
        received: list[dict] = []
        self.dispatcher.subscribe("events.oewas.v3", lambda msg: received.append(msg))

        report = self.dispatcher.dispatch_pending().unwrap()

        self.assertEqual(report.delivered_count, 1)
        self.assertEqual(report.undeliverable_count, 0)
        self.assertEqual(len(received), 1)

    def test_a_wildcard_subscriber_counts_as_a_subscriber(self) -> None:
        """`*` handlers are merged into the destination's handler list, so a
        wildcard subscription must make the message deliverable."""
        self._seed_one_event("cat_star_01", "evt_star_01")
        received: list[dict] = []
        self.dispatcher.subscribe("*", lambda msg: received.append(msg))

        report = self.dispatcher.dispatch_pending().unwrap()

        self.assertEqual(report.delivered_count, 1)
        self.assertEqual(report.undeliverable_count, 0)
        self.assertEqual(len(received), 1)


if __name__ == "__main__":
    unittest.main()
