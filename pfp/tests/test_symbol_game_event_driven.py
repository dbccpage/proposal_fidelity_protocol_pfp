"""Unit tests for Event-Driven Architecture in pfp."""

from __future__ import annotations

from pfp.domain.events import (
    DomainEvent,
    ProposalEvaluatedEvent,
    RunRootCreatedEvent,
    TurnExecutedEvent,
)
from pfp.infrastructure.events import (
    InMemoryEventBus,
    TransactionalOutbox,
)
from pfp.controllers.symbol_game_engine import SymbolGameEngine


def test_in_memory_event_bus() -> None:
    bus = InMemoryEventBus()
    received_turns = []
    received_all = []

    bus.subscribe(TurnExecutedEvent, lambda e: received_turns.append(e))
    bus.subscribe(DomainEvent, lambda e: received_all.append(e))

    turn_event = TurnExecutedEvent(task_id="task_bus_1", step_id="step_1", purity=0.9, l1_obstruction=0.1)
    bus.publish(turn_event)

    assert len(received_turns) == 1
    assert received_turns[0].task_id == "task_bus_1"
    assert len(received_all) == 1


def test_transactional_outbox() -> None:
    bus = InMemoryEventBus()
    outbox = TransactionalOutbox(event_bus=bus)

    assert outbox.pending_count == 0

    event1 = TurnExecutedEvent(task_id="task_outbox_1")
    event2 = ProposalEvaluatedEvent(proposal_id="prop_outbox_1")

    outbox.stage_event(event1)
    outbox.stage_event(event2)
    assert outbox.pending_count == 2
    assert len(bus.recorded_events) == 0

    # Dispatch pending
    dispatched = outbox.dispatch_pending()
    assert dispatched == 2
    assert outbox.pending_count == 0
    assert len(bus.recorded_events) == 2


def test_symbol_game_engine_event_emission() -> None:
    engine = SymbolGameEngine()
    emitted_proposals = []
    emitted_turns = []

    engine.subscribe(ProposalEvaluatedEvent, lambda e: emitted_proposals.append(e))
    engine.subscribe(TurnExecutedEvent, lambda e: emitted_turns.append(e))

    # Evaluate proposal
    engine.evaluate_proposal("prop_event_1", 4.0, 1.0)
    assert len(emitted_proposals) == 1
    assert emitted_proposals[0].proposal_id == "prop_event_1"

    # Execute turn
    engine.execute_turn("task_event_1", "Sample prompt")
    assert len(emitted_turns) == 1
    assert emitted_turns[0].task_id == "task_event_1"
