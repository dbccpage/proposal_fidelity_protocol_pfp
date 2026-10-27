"""Atomic budget and attempt storage contract. AuthorityEffect: None."""

from contextlib import contextmanager
from copy import deepcopy
from threading import RLock
from typing import ContextManager, Protocol


class BudgetLedger(Protocol):
    def transaction(self, limit: int) -> ContextManager[dict]: ...


def initial_state(limit: int) -> dict:
    return {"limit": limit, "spent": 0, "attempts": {}, "settlements": {}}


class MemoryBudgetLedger:
    def __init__(self) -> None:
        self._state = None
        self._lock = RLock()

    @contextmanager
    def transaction(self, limit: int):
        with self._lock:
            state = deepcopy(self._state or initial_state(limit))
            if state["limit"] != limit:
                raise ValueError("ledger budget limit differs from configured limit")
            yield state
            self._state = state
