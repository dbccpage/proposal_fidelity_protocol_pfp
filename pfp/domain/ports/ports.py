"""
ports.py
========

Clean Architecture Domain Protocols for Symbol Game storage, projection, solving, evaluation, and event bus.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol, Sequence, runtime_checkable

from ..entities.cemetery_entry import CemeteryEntry, TailReceipt
from ..events import DomainEvent
from ..models import ObstructionScore, SymbolGameEnvelope, SymbolGameStepOutcome



@runtime_checkable
class CanonicalSerializerProtocol(Protocol):
    """Protocol for canonical deterministic serialization and domain separation."""

    def canonical_bytes(self, payload: Mapping[str, Any]) -> bytes:
        ...

    def domain_digest(self, domain: str, payload: Mapping[str, Any]) -> str:
        ...


@runtime_checkable
class PacketEnvelopeProtocol(Protocol):
    """Protocol for transport packet envelopes."""

    @property
    def packet_id(self) -> str:
        ...

    @property
    def task_id(self) -> str:
        ...

    @property
    def packet_family(self) -> str:
        ...

    @property
    def carrier_id(self) -> str:
        ...

    @property
    def authority_effect(self) -> str:
        ...

    def to_dict(self) -> dict[str, Any]:
        ...


@runtime_checkable
class ObstructionLedgerProtocol(Protocol):
    """Protocol for maintaining and reconciling active obstruction states."""

    def reconcile(
        self,
        projection: Any,
        *,
        step: int,
        witness: str,
    ) -> None:
        ...

    def is_active(self, obstruction_id: str) -> bool:
        ...


@runtime_checkable
class EvaluatorPort(Protocol):
    """Protocol for scoring candidate proposals and evaluating residual reductions."""

    def evaluate_proposal(
        self,
        proposal_id: str,
        initial_mass: Any,
        final_mass: Any,
        effort: Any = 1,
        metadata: Mapping[str, Any] | None = None,
    ) -> Any: ...


@runtime_checkable
class CemeterySinkPort(Protocol):
    """Protocol for append-only candidate turn persistence with tail-truncation receipts.

    Under the Symbol Game Zero Data-Loss Invariant, every refused candidate proposal,
    hallucination, or typed refusal (M) is permanently committed to CemeterySink
    with full raw prompt vectors, cochain projections, and cryptographic tail-truncation receipts.
    """

    def record_refusal(
        self,
        turn_envelope: Any,
        refusal_reason: str,
        prompt_parameters: Mapping[str, Any] | None = None,
        cochain_projection: Mapping[str, Any] | None = None,
    ) -> CemeteryEntry:
        """Permanently commit a refused candidate turn into the append-only ledger."""
        ...

    def tail_digest(self) -> str:
        """Return the current SHA-256 hash-chain digest at the head of the ledger."""
        ...

    def verify_integrity(self) -> bool:
        """Verify hash-chain continuity and reject any tail-truncation or interior bit-flips."""
        ...

    def emit_tail_receipt(self) -> TailReceipt:
        """Emit a cryptographically sealed tail-truncation receipt."""
        ...

    def get_entries(self) -> Sequence[CemeteryEntry]:
        """Return an immutable sequence of all recorded cemetery entries."""
        ...



@runtime_checkable
class StoragePort(Protocol):
    """Protocol for content-addressed artifact persistence and receipt recording."""

    def save_artifact(self, artifact_name: str, payload: Mapping[str, Any]) -> str: ...

    def load_artifact(self, artifact_sha256: str) -> Mapping[str, Any] | None: ...


@runtime_checkable
class ProjectorPort(Protocol):
    """Protocol for geometric and algebraic projection operators."""

    def project(self, state: Any) -> Any: ...

    def verify_retraction(
        self, solver_id: str, before_state: Any, after_state: Any
    ) -> bool: ...


@runtime_checkable
class SolverPort(Protocol):
    """Protocol for proposing manifold state repairs."""

    def propose(self, problem: Any) -> Any: ...


@runtime_checkable
class IEventBus(Protocol):
    """Protocol for publishing and subscribing to Domain Events in-process."""

    def publish(self, event: DomainEvent) -> None: ...

    def subscribe(self, event_type: type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None: ...


@runtime_checkable
class IOutbox(Protocol):
    """Protocol for transactional event outbox staging and dispatch."""

    def stage_event(self, event: DomainEvent) -> None: ...

    def dispatch_pending(self) -> int: ...


# Domain Repository Protocols
@runtime_checkable
class IPromptRepository(Protocol):
    def save(self, artifact: Any) -> None: ...
    def find_by_id(self, artifact_id: str) -> Any | None: ...


@runtime_checkable
class ITurnRepository(Protocol):
    def save(self, run_root: Any) -> None: ...
    def find_by_id(self, run_root_id: str) -> Any | None: ...


# `ICodeChangeRepository` deliberately does not live here. The canonical port is
# the typed one in `code_change_repository.py`; the untyped `save`/`find_by_id`
# duplicate that used to sit at this spot had no direct consumer and gave the
# name a second meaning, so it was deleted rather than kept in step.


@runtime_checkable
class ILearningRepository(Protocol):
    def save(self, policy: Any) -> None: ...
    def find_by_id(self, policy_id: str) -> Any | None: ...


@runtime_checkable
class IResearchRepository(Protocol):
    def save(self, run_root: Any) -> None: ...
    def find_by_id(self, run_root_id: str) -> Any | None: ...


@runtime_checkable
class IScoringEvaluator(Protocol):
    def score(self, proposal: Any) -> Any: ...


@runtime_checkable
class ICecBridgeAdapter(Protocol):
    def evaluate(self, profile: Any) -> Any: ...
