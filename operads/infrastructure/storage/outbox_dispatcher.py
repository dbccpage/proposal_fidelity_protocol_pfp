"""Outbox message dispatcher delivering queued events with at-least-once semantics."""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Callable, Dict, List

from operations.domain.rop.result import Err, Ok, Result

from ...domain.errors.domain_errors import OeopDomainError
from .sqlite_unit_of_work import SqliteUnitOfWork

logger = logging.getLogger(__name__)
Subscriber = Callable[[dict], None | Result[object, OeopDomainError]]


def _invoke_subscriber(handler: Subscriber, message: dict) -> None:
    outcome = handler(message)
    if isinstance(outcome, Err):
        raise RuntimeError(str(outcome.unwrap_err()))
    if outcome is not None and not isinstance(outcome, Ok):
        raise TypeError("Subscriber must return None, Ok or Err")


@dataclass(frozen=True, slots=True)
class DispatchReport:
    total_polled: int
    delivered_count: int
    failed_count: int
    errors: tuple[str, ...] = ()
    #: Messages left pending because no subscriber is registered for their
    #: destination. A third outcome, distinct from both delivered and failed:
    #: nothing went wrong, and nothing was received either. Counting these as
    #: delivered is what made the at-least-once guarantee untrue.
    undeliverable_count: int = 0


class OutboxMessageDispatcher:
    """Dispatches pending outbox records to subscribers with at-least-once guarantees."""

    def __init__(self, uow: SqliteUnitOfWork, *, worker_id: str | None = None,
                 lease_seconds: float = 30, retry_base_seconds: float = 1,
                 clock: Callable[[], float] = time.time) -> None:
        if (type(retry_base_seconds) not in (int, float) or not math.isfinite(retry_base_seconds)
                or retry_base_seconds < 0):
            raise ValueError("retry delay must be finite and nonnegative")
        self._uow = uow
        self._subscribers: Dict[str, List[Subscriber]] = {}
        self._worker_id, self._lease_seconds = worker_id, lease_seconds
        self._retry_base_seconds, self._clock = retry_base_seconds, clock

    def subscribe(self, destination: str, handler: Subscriber) -> None:
        """Register a handler returning legacy None or a typed Ok/Err outcome.

        Err, exceptions and unknown return types leave the message pending.
        Each subscriber must make its own effects idempotent across retries.
        """
        if destination not in self._subscribers:
            self._subscribers[destination] = []
        self._subscribers[destination].append(handler)

    def dispatch_pending(self, limit: int = 100) -> Result[DispatchReport, OeopDomainError]:
        """Poll pending outbox messages and dispatch to registered subscribers."""
        # Retain messages with no subscribers for a late subscriber, but fetch
        # known deliverable destinations first so those retained records cannot
        # starve a bounded poll forever. A wildcard receives every destination,
        # so no preference is necessary in that case.
        preferred_destinations = ()
        if "*" not in self._subscribers:
            preferred_destinations = tuple(sorted(self._subscribers))
        if self._worker_id is not None:
            if not self._subscribers:
                return Ok(DispatchReport(0, 0, 0))
            fetch_res = self._uow.claim_pending_outbox(
                self._worker_id, now=self._clock(), lease_seconds=self._lease_seconds,
                limit=limit, destinations=preferred_destinations,
            )
        else:
            fetch_res = self._uow.fetch_pending_outbox(
                limit=limit, preferred_destinations=preferred_destinations,
            )
        if fetch_res.is_err:
            return Err(fetch_res.unwrap_err())

        messages = fetch_res.unwrap()
        if not messages:
            return Ok(DispatchReport(total_polled=0, delivered_count=0, failed_count=0))

        delivered = 0
        failed = 0
        undeliverable = 0
        errors: List[str] = []

        for msg in messages:
            outbox_id = msg["outbox_id"]
            lease_token = msg.pop("lease_token", None)
            attempt = msg.pop("attempt_count", 1)
            destination = msg.get("destination", "events.oewas.v3")
            handlers = self._subscribers.get(destination, []) + self._subscribers.get("*", [])

            if not handlers:
                # Left pending. Marking it delivered here made the at-least-once
                # guarantee in this class's own docstring untrue: nobody
                # received the message, and `fetch_pending_outbox` filters on
                # `delivered_at IS NULL`, so it would never be offered again.
                # A subscriber registering later -- the ordinary case during
                # startup -- silently lost every event queued before it.
                undeliverable += 1
                logger.warning(
                    "No subscriber for destination %s; leaving outbox %s pending",
                    destination,
                    outbox_id,
                )
                continue

            msg_failed = False
            for handler in handlers:
                try:
                    _invoke_subscriber(handler, msg)
                except Exception as exc:
                    msg_failed = True
                    err_msg = f"Subscriber error for outbox {outbox_id} on {destination}: {exc}"
                    logger.warning(err_msg)
                    errors.append(err_msg)
                    break

            if msg_failed:
                # Leave undelivered in outbox_v3 for at-least-once retry
                failed += 1
                if lease_token is not None:
                    release = self._uow.finish_outbox_lease(
                        outbox_id, lease_token, now=self._clock(),
                        retry_after=min(3600, self._retry_base_seconds * 2 ** min(attempt - 1, 12)),
                    )
                    if release.is_err:
                        errors.append(str(release.unwrap_err()))
            else:
                mark_res = (self._uow.mark_outbox_delivered(outbox_id) if lease_token is None
                            else self._uow.finish_outbox_lease(outbox_id, lease_token, now=self._clock()))
                if mark_res.is_ok:
                    delivered += 1
                else:
                    failed += 1
                    errors.append(f"Failed marking outbox {outbox_id}: {mark_res.unwrap_err()}")

        return Ok(
            DispatchReport(
                total_polled=len(messages),
                delivered_count=delivered,
                failed_count=failed,
                errors=tuple(errors),
                undeliverable_count=undeliverable,
            )
        )
