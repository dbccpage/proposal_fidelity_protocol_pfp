"""Append-only event journal + pure packet state reducer (Sprint 030).

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Sequence

from .event_journal import EventJournal
from .illegal_transition import IllegalTransition
from .journal_event import JournalEvent
from .packet_state import PacketState

__all__ = [
    "EventJournal",
    "IllegalTransition",
    "JournalEvent",
    "PacketState",
    "reduce_events",
]

# Legal edges: from -> set of next
_TRANSITIONS: dict[PacketState, frozenset[PacketState]] = {
    PacketState.ADMITTED: frozenset({PacketState.DEVELOPING}),
    PacketState.DEVELOPING: frozenset(
        {PacketState.CANDIDATE_BOUND, PacketState.ADMITTED}
    ),
    PacketState.CANDIDATE_BOUND: frozenset(
        {PacketState.AWAITING_HUMAN, PacketState.DEVELOPING}
    ),
    PacketState.AWAITING_HUMAN: frozenset(
        {PacketState.READY_FOR_LICENSE, PacketState.CANDIDATE_BOUND}
    ),
    PacketState.READY_FOR_LICENSE: frozenset(
        {PacketState.MERGED, PacketState.AWAITING_HUMAN}
    ),
    PacketState.MERGED: frozenset({PacketState.PRUNED}),
    PacketState.PRUNED: frozenset(),
}


def reduce_events(events: Sequence[JournalEvent], packet_id: str) -> PacketState | None:
    """Pure reducer: replay events for one packet; refuse illegal transitions."""
    state: PacketState | None = None
    last_seq = -1
    for ev in events:
        if ev.packet_id != packet_id:
            continue
        if ev.seq <= last_seq:
            raise ValueError(f"SEQUENCE_NOT_MONOTONE:{ev.seq}")
        last_seq = ev.seq
        if state is None:
            if ev.to_state is not PacketState.ADMITTED:
                raise IllegalTransition(None, ev.to_state, "must_start_ADMITTED")
            state = PacketState.ADMITTED
            continue
        allowed = _TRANSITIONS[state]
        if ev.to_state not in allowed:
            raise IllegalTransition(state, ev.to_state)
        state = ev.to_state
    return state
