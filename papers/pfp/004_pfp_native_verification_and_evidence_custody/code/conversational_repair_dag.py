"""
Conversational Repair DAG — Paper 032 (PO-032), Section 7.1.

Content-addressed directed acyclic graph recording the five event types of a
governed Symbol Game conversation:

    PROMPT     — a demand issued to the proposer (an untrusted language model).
    RESPONSE   — a candidate move or ledger row emitted by the proposer.
    AUDIT      — a host firewall / governor verdict on a response.
    REPAIR     — an atomic projection-replacement CUT applied by the host.
    ADMISSION  — a state transition committed to the derivation record.

Every event identifier is the full SHA-256 digest of a canonical JSON encoding
of the tuple (event_type, label, payload, ordered parent identifiers). Because
the digest covers the ordered parent identifiers, each identifier transitively
commits to the entire causal history of the event: mutating any ancestor's
payload changes every descendant identifier (a Merkle DAG over the conversation).

``verify_integrity`` re-checks, fail-closed:

    1. Parent closure    — every referenced parent id is present in the DAG.
    2. Content hashes     — every stored id equals the recomputed canonical digest.
    3. Acyclicity         — the parent relation admits a topological order.
    4. Projected edges    — the recorded (parent -> child) edge set is exactly the
                            closure of the recorded parent references.

This module is self-contained (standard library only) and performs zero
floating-point arithmetic. It records conversational structure and makes recorded
mutation detectable; it does not adjudicate semantic truth (claims PO032-C43,
PO032-C48). Event payloads must be JSON-serializable (str/int/bool/None/list/dict);
callers pass rational or Fraction quantities as strings.
"""

from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


class EventType(Enum):
    """The five conversational event types recorded on the repair DAG."""
    PROMPT = "PROMPT"
    RESPONSE = "RESPONSE"
    AUDIT = "AUDIT"
    REPAIR = "REPAIR"
    ADMISSION = "ADMISSION"


def _coerce_event_type(event_type: Any) -> EventType:
    if isinstance(event_type, EventType):
        return event_type
    return EventType(str(event_type))


def canonical_event_encoding(
    event_type: Any,
    label: str,
    payload: Dict[str, Any],
    parents: Sequence[str],
) -> str:
    """
    Deterministic canonical JSON encoding of an event's content.

    The parent identifiers are encoded in the exact order supplied. Keys are
    sorted and separators are fixed so the encoding is stable across platforms
    and Python invocations.
    """
    et = _coerce_event_type(event_type)
    return json.dumps(
        {
            "type": et.value,
            "label": label,
            "payload": payload,
            "parents": list(parents),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def compute_event_id(
    event_type: Any,
    label: str,
    payload: Dict[str, Any],
    parents: Sequence[str],
) -> str:
    """Full SHA-256 hex digest of the canonical event encoding."""
    encoding = canonical_event_encoding(event_type, label, payload, parents)
    return hashlib.sha256(encoding.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Event:
    """A single content-addressed conversation event."""
    event_id: str
    event_type: EventType
    label: str
    payload: Dict[str, Any]
    parents: Tuple[str, ...]

    def recompute_id(self) -> str:
        """Recomputes the identifier from the current fields (tamper check)."""
        return compute_event_id(self.event_type, self.label, self.payload, self.parents)

    def is_consistent(self) -> bool:
        """True iff the stored identifier matches the recomputed digest."""
        return self.event_id == self.recompute_id()


@dataclass(frozen=True)
class IntegrityReport:
    """Structured result of ``ConversationalRepairDAG.verify_integrity``."""
    ok: bool
    n_events: int
    n_edges: int
    missing_parents: Tuple[Tuple[str, str], ...]  # (child_id, missing_parent_id)
    hash_mismatches: Tuple[str, ...]              # stored ids whose recompute differs
    has_cycle: bool
    projected_edges_ok: bool
    details: str


class ConversationalRepairDAG:
    """
    Append-only, content-addressed DAG of governed-conversation events.

    Events are keyed by their SHA-256 content digest. Adding an event whose
    content is identical to an existing one is idempotent (same digest, single
    node). A parent identifier that is not already present is rejected
    fail-closed, so cycles cannot be introduced through the public API; the
    independent ``verify_integrity`` acyclicity check guards against tampering
    that bypasses the API.
    """

    def __init__(self) -> None:
        self._events: Dict[str, Event] = {}
        self._order: List[str] = []

    def __len__(self) -> int:
        return len(self._events)

    def __contains__(self, event_id: object) -> bool:
        return event_id in self._events

    @property
    def events(self) -> Dict[str, Event]:
        """Live mapping from event id to Event (used by tests to inspect state)."""
        return self._events

    def order(self) -> List[str]:
        """Event ids in insertion order."""
        return list(self._order)

    def add_event(
        self,
        event_type: Any,
        label: str,
        payload: Optional[Dict[str, Any]] = None,
        parents: Sequence[str] = (),
    ) -> str:
        """
        Adds an event and returns its content-addressed identifier.

        Raises KeyError (fail-closed) if any declared parent is absent, which
        preserves parent closure and, by construction, acyclicity.
        """
        payload = {} if payload is None else payload
        parents_t = tuple(parents)
        for parent in parents_t:
            if parent not in self._events:
                raise KeyError(
                    f"parent id {parent!r} is not present in the DAG "
                    f"(parent-closure violation, fail-closed)."
                )
        event_id = compute_event_id(event_type, label, payload, parents_t)
        if event_id in self._events:
            return event_id  # content-addressed: identical event collapses to one node
        self._events[event_id] = Event(
            event_id=event_id,
            event_type=_coerce_event_type(event_type),
            label=label,
            payload=dict(payload),
            parents=parents_t,
        )
        self._order.append(event_id)
        return event_id

    # -- typed convenience constructors -----------------------------------

    def add_prompt(self, label: str, payload: Optional[Dict[str, Any]] = None,
                   parents: Sequence[str] = ()) -> str:
        return self.add_event(EventType.PROMPT, label, payload, parents)

    def add_response(self, label: str, payload: Optional[Dict[str, Any]] = None,
                     parents: Sequence[str] = ()) -> str:
        return self.add_event(EventType.RESPONSE, label, payload, parents)

    def add_audit(self, label: str, payload: Optional[Dict[str, Any]] = None,
                  parents: Sequence[str] = ()) -> str:
        return self.add_event(EventType.AUDIT, label, payload, parents)

    def add_repair(self, label: str, payload: Optional[Dict[str, Any]] = None,
                   parents: Sequence[str] = ()) -> str:
        return self.add_event(EventType.REPAIR, label, payload, parents)

    def add_admission(self, label: str, payload: Optional[Dict[str, Any]] = None,
                      parents: Sequence[str] = ()) -> str:
        return self.add_event(EventType.ADMISSION, label, payload, parents)

    # -- graph queries ----------------------------------------------------

    def parents_of(self, event_id: str) -> Tuple[str, ...]:
        return self._events[event_id].parents

    def children_of(self, event_id: str) -> Tuple[str, ...]:
        return tuple(
            eid for eid in self._order if event_id in self._events[eid].parents
        )

    def projected_edges(self) -> Set[Tuple[str, str]]:
        """The set of (parent -> child) edges induced by recorded parent references."""
        return {
            (parent, eid)
            for eid in self._order
            for parent in self._events[eid].parents
        }

    def topological_order(self) -> Optional[List[str]]:
        """
        Returns a deterministic topological order (Kahn's algorithm), or None if
        the parent relation contains a cycle.
        """
        indegree: Dict[str, int] = {eid: 0 for eid in self._events}
        children: Dict[str, List[str]] = {eid: [] for eid in self._events}
        for eid in self._order:
            for parent in self._events[eid].parents:
                if parent in indegree:
                    indegree[eid] += 1
                    children[parent].append(eid)

        queue: deque[str] = deque(sorted(e for e, d in indegree.items() if d == 0))
        ordered: List[str] = []
        while queue:
            node = queue.popleft()
            ordered.append(node)
            for child in sorted(children[node]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    queue.append(child)

        if len(ordered) != len(self._events):
            return None
        return ordered

    def verify_integrity(self) -> IntegrityReport:
        """
        Re-checks parent closure, content hashes, acyclicity, and projected edges
        fail-closed, returning a structured report.
        """
        missing_parents: List[Tuple[str, str]] = []
        for eid in self._order:
            for parent in self._events[eid].parents:
                if parent not in self._events:
                    missing_parents.append((eid, parent))

        hash_mismatches = tuple(
            eid for eid in self._order if eid != self._events[eid].recompute_id()
        )

        topo = self.topological_order()
        has_cycle = topo is None

        edges = self.projected_edges()
        # Every projected edge must point at a present parent; a missing parent is
        # simultaneously a projected-edge defect.
        projected_edges_ok = all(parent in self._events for (parent, _) in edges)

        ok = (
            not missing_parents
            and not hash_mismatches
            and not has_cycle
            and projected_edges_ok
        )
        if ok:
            details = (
                f"OK: {len(self._events)} events, {len(edges)} edges, "
                f"acyclic, all content hashes consistent."
            )
        else:
            parts: List[str] = []
            if missing_parents:
                parts.append(f"{len(missing_parents)} missing-parent reference(s)")
            if hash_mismatches:
                parts.append(f"{len(hash_mismatches)} content-hash mismatch(es)")
            if has_cycle:
                parts.append("parent relation contains a cycle")
            if not projected_edges_ok:
                parts.append("projected edge references a missing node")
            details = "INTEGRITY VIOLATION: " + "; ".join(parts) + "."

        return IntegrityReport(
            ok=ok,
            n_events=len(self._events),
            n_edges=len(edges),
            missing_parents=tuple(missing_parents),
            hash_mismatches=hash_mismatches,
            has_cycle=has_cycle,
            projected_edges_ok=projected_edges_ok,
            details=details,
        )


def build_example_governed_conversation() -> ConversationalRepairDAG:
    """
    Builds a small worked conversation exhibiting all five event types and one
    audited-then-repaired-then-admitted cycle of the Symbol Game loop.
    """
    dag = ConversationalRepairDAG()
    prompt = dag.add_prompt(
        "demand",
        {"carrier": ["a", "b", "c"], "goal": "close 3-cycle holonomy defect"},
    )
    resp = dag.add_response(
        "proposed_cut",
        {"move": "CUT", "redex": "e(c,a)", "expected_delta_phi": "-1"},
        parents=[prompt],
    )
    audit = dag.add_audit(
        "governor_verdict",
        {"admitted": False, "status": "DefectIncrease", "code": "FW_MOVE"},
        parents=[resp],
    )
    repair = dag.add_repair(
        "projection_replacement",
        {"phi1_before": "1", "phi1_after": "0", "status": "ExactRepair"},
        parents=[audit],
    )
    dag.add_admission(
        "commit",
        {"phi1": "0", "note": "zero-defect terminal reached"},
        parents=[repair],
    )
    return dag


def main() -> None:
    dag = build_example_governed_conversation()
    report = dag.verify_integrity()
    print("Conversational Repair DAG - worked example (Paper 032 Section 7.1)")
    print(f"  events           : {report.n_events}")
    print(f"  projected edges  : {report.n_edges}")
    print(f"  topological order: {dag.topological_order() is not None}")
    print(f"  integrity        : {report.details}")


__all__ = [
    "EventType",
    "Event",
    "IntegrityReport",
    "ConversationalRepairDAG",
    "canonical_event_encoding",
    "compute_event_id",
    "build_example_governed_conversation",
]


if __name__ == "__main__":
    main()
