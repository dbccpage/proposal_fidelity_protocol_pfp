"""Application orchestration for the governed OEOS task lifecycle.

The service owns no concrete database, provider, process, or API. Its only
effectful collaborators implement the ports in :mod:`ports`.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from threading import RLock

from ..domain import (
    TERMINAL_STATES,
    CapabilitySnapshotV1,
    EncryptedArtifactRefV1,
    HarnessEventV1,
    TaskAggregateV1,
    TaskEnvelopeV1,
    TaskStateV1,
    digest_payload,
    require_identifier,
    require_sha256_digest,
    utc_now,
)
from .ports import (
    CancellationProbe,
    CapabilitySnapshotPort,
    CheckoutLeaseEvidenceV1,
    CheckoutLeaseGuardPort,
    CheckoutLeasePort,
    CheckoutLeaseRefusal,
    ExecutionDispositionV1,
    ExecutionResultV1,
    IndependentVerifierPort,
    TaskExecutorPort,
    TaskStorePort,
    VerificationResultV1,
)


class TaskServiceError(RuntimeError):
    """Stable refusal for application operations."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}:{message}")

    def to_canonical(self) -> dict[str, str]:
        return {
            "authority_effect": "None",
            "message": self.message,
            "refusal_code": self.code,
            "status": "REFUSED",
        }


class BoundedTaskQueue:
    """Thread-safe finite FIFO with no eviction and no duplicate task IDs."""

    def __init__(self, capacity: int) -> None:
        if type(capacity) is not int or not 1 <= capacity <= 100_000:
            raise TaskServiceError(
                "INVALID_QUEUE_CAPACITY", "capacity is outside bounds"
            )
        self.capacity = capacity
        self._items: deque[str] = deque()
        self._present: set[str] = set()
        self._lock = RLock()

    def enqueue(self, task_id: str) -> bool:
        if type(task_id) is not str or not task_id:
            raise TaskServiceError("INVALID_TASK_ID", "task_id must be a string")
        with self._lock:
            if task_id in self._present:
                return True
            if len(self._items) >= self.capacity:
                return False
            self._items.append(task_id)
            self._present.add(task_id)
            return True

    def dequeue(self) -> str | None:
        with self._lock:
            if not self._items:
                return None
            task_id = self._items.popleft()
            self._present.remove(task_id)
            return task_id

    def remove(self, task_id: str) -> bool:
        with self._lock:
            if task_id not in self._present:
                return False
            self._items.remove(task_id)
            self._present.remove(task_id)
            return True

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)

    def snapshot(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._items)


class _StoreCancellationProbe(CancellationProbe):
    def __init__(self, store: TaskStorePort, task_id: str) -> None:
        super().__init__()
        self._store = store
        self._task_id = task_id

    def is_cancellation_requested(self) -> bool:
        task = self._store.load(self._task_id)
        return task is None or task.cancellation_requested


class TaskService:
    """One canonical application lifecycle shared by CLI and HTTP adapters."""

    def __init__(
        self,
        *,
        store: TaskStorePort,
        queue: BoundedTaskQueue,
        executor: TaskExecutorPort,
        verifier: IndependentVerifierPort,
        capabilities: CapabilitySnapshotPort,
        checkout_lease: CheckoutLeasePort,
        clock: Callable[[], str] = utc_now,
    ) -> None:
        self._store = store
        self._queue = queue
        self._executor = executor
        self._verifier = verifier
        self._capabilities = capabilities
        self._checkout_lease = checkout_lease
        self._clock = clock
        self._lock = RLock()

    @property
    def checkout_lease(self) -> CheckoutLeasePort:
        """Expose the injected port solely for live composition validation."""

        return self._checkout_lease

    @staticmethod
    def _payload(schema: str, value: object) -> str:
        return digest_payload(schema, value)

    def _save_transition(
        self,
        task: TaskAggregateV1,
        target: TaskStateV1,
        *,
        code: str,
        evidence: object,
        event_type: str = "TASK_STATE_CHANGED",
    ) -> TaskAggregateV1:
        updated = task.transition(
            target,
            occurred_at_utc=self._clock(),
            payload_digest=self._payload(
                "omega.oeos.lifecycle-evidence.v1", {"code": code, "evidence": evidence}
            ),
            event_type=event_type,
        )
        self._store.save(updated, expected_version=task.version)
        return updated

    def submit(self, envelope: TaskEnvelopeV1) -> TaskAggregateV1:
        if type(envelope) is not TaskEnvelopeV1:
            raise TaskServiceError(
                "MALFORMED_TASK_ENVELOPE", "exact TaskEnvelopeV1 required"
            )
        with self._lock:
            submitted = TaskAggregateV1.submit(
                envelope, self._capabilities.snapshot(), self._clock()
            )
            current, created = self._store.create(submitted)
            if not created and current.state is not TaskStateV1.SUBMITTED:
                return current
            if not self._queue.enqueue(envelope.task_id):
                return self._save_transition(
                    current,
                    TaskStateV1.REFUSED,
                    code="QUEUE_CAPACITY_EXHAUSTED",
                    evidence={"capacity": self._queue.capacity},
                )
            try:
                return self._save_transition(
                    current,
                    TaskStateV1.QUEUED,
                    code="TASK_ENQUEUED",
                    evidence={"queue_capacity": self._queue.capacity},
                )
            except Exception:  # noqa: BLE001 - roll back queue reservation and re-raise
                self._queue.remove(envelope.task_id)
                raise

    def get(self, task_id: str) -> TaskAggregateV1:
        task = self._store.load(task_id)
        if task is None:
            raise TaskServiceError("TASK_NOT_FOUND", "task does not exist")
        return task

    def events(self, task_id: str) -> tuple[HarnessEventV1, ...]:
        self.get(task_id)
        return self._store.events(task_id)

    @staticmethod
    def _matches_queued_cancellation(
        task: TaskAggregateV1, expected_version: int, payload_digest: str
    ) -> bool:
        if task.state is not TaskStateV1.CANCELLED or task.version <= expected_version:
            return False
        event = task.events[expected_version]
        return (
            event.sequence == expected_version + 1
            and event.event_type == "TASK_CANCELLED"
            and event.from_state is TaskStateV1.QUEUED
            and event.to_state is TaskStateV1.CANCELLED
            and event.payload_digest == payload_digest
        )

    def cancel_queued(
        self,
        task_id: str,
        *,
        expected_version: int,
        expected_envelope_digest: str,
        request_digest: str,
    ) -> TaskAggregateV1:
        """Cancel one exact queued version; callers own warrant authorization.

        A committed matching event admits historical replay, including after
        later operator outcome records. No new event is written on replay.
        """

        require_identifier(task_id, "task_id")
        if type(expected_version) is not int or not 1 <= expected_version < 10**9:
            raise TaskServiceError(
                "INVALID_EXPECTED_VERSION", "expected_version is outside bounds"
            )
        require_sha256_digest(expected_envelope_digest, "expected_envelope_digest")
        require_sha256_digest(request_digest, "request_digest")
        evidence = {
            "cooperative": False,
            "expected_version": expected_version,
            "expected_envelope_digest": expected_envelope_digest,
            "request_digest": request_digest,
        }
        payload_digest = self._payload(
            "omega.oeos.lifecycle-evidence.v1",
            {"code": "TASK_CANCELLED", "evidence": evidence},
        )
        with self._lock:
            task = self.get(task_id)
            if (
                task.envelope.task_id != task_id
                or task.envelope.canonical_digest != expected_envelope_digest
            ):
                raise TaskServiceError(
                    "TASK_ENVELOPE_MISMATCH", "task identity differs from request"
                )
            if self._matches_queued_cancellation(task, expected_version, payload_digest):
                self._queue.remove(task_id)
                return task
            if task.version != expected_version:
                raise TaskServiceError(
                    "TASK_VERSION_MISMATCH", "task version differs from request"
                )
            if task.state is not TaskStateV1.QUEUED:
                raise TaskServiceError("TASK_NOT_QUEUED", "task is no longer queued")
            updated = self._save_transition(
                task,
                TaskStateV1.CANCELLED,
                code="TASK_CANCELLED",
                evidence=evidence,
                event_type="TASK_CANCELLED",
            )
            self._queue.remove(task_id)
            return updated

    def cancel(self, task_id: str) -> TaskAggregateV1:
        with self._lock:
            task = self.get(task_id)
            if task.state in TERMINAL_STATES:
                return task
            if task.state in {
                TaskStateV1.SUBMITTED,
                TaskStateV1.QUEUED,
                TaskStateV1.NEEDS_INPUT,
                TaskStateV1.STATUS_UNKNOWN,
            }:
                self._queue.remove(task_id)
                return self._save_transition(
                    task,
                    TaskStateV1.CANCELLED,
                    code="TASK_CANCELLED",
                    evidence={"cooperative": False},
                    event_type="TASK_CANCELLED",
                )
            if task.cancellation_requested:
                return task
            updated = task.record(
                "CANCELLATION_REQUESTED",
                occurred_at_utc=self._clock(),
                payload_digest=self._payload(
                    "omega.oeos.cancellation-request.v1", {"task_id": task_id}
                ),
                cancellation_requested=True,
            )
            self._store.save(updated, expected_version=task.version)
            return updated

    def provide_input(
        self, task_id: str, encrypted_input_ref: EncryptedArtifactRefV1
    ) -> TaskAggregateV1:
        with self._lock:
            task = self.get(task_id)
            if task.state not in {
                TaskStateV1.NEEDS_INPUT,
                TaskStateV1.STATUS_UNKNOWN,
            }:
                raise TaskServiceError(
                    "TASK_NOT_WAITING_FOR_INPUT",
                    "task is not awaiting input or recovery evidence",
                )
            if type(encrypted_input_ref) is not EncryptedArtifactRefV1:
                raise TaskServiceError(
                    "MALFORMED_ENCRYPTED_INPUT_REF",
                    "operator input requires exact EncryptedArtifactRefV1",
                )
            # Retain only the opaque reference, bound to this lifecycle event.
            payload = self._payload(
                "omega.oeos.operator-input.v1",
                {"encrypted_input_ref": encrypted_input_ref.to_canonical()},
            )
            if not self._queue.enqueue(task_id):
                return self._save_transition(
                    task,
                    TaskStateV1.REFUSED,
                    code="QUEUE_CAPACITY_EXHAUSTED",
                    evidence={"capacity": self._queue.capacity},
                )
            try:
                updated = task.transition(
                    TaskStateV1.QUEUED,
                    occurred_at_utc=self._clock(),
                    payload_digest=payload,
                    event_type="OPERATOR_INPUT_BOUND",
                    encrypted_input_ref=encrypted_input_ref,
                )
                self._store.save(updated, expected_version=task.version)
                return updated
            except Exception:  # noqa: BLE001 - roll back queue reservation and re-raise
                self._queue.remove(task_id)
                raise

    def record_outcome(
        self, task_id: str, outcome_code: str, evidence_digest: str
    ) -> TaskAggregateV1:
        require_identifier(outcome_code, "outcome_code")
        require_sha256_digest(evidence_digest, "evidence_digest")
        with self._lock:
            task = self.get(task_id)
            if task.state not in TERMINAL_STATES:
                raise TaskServiceError(
                    "TASK_NOT_TERMINAL", "outcome requires a terminal task"
                )
            updated = task.record(
                "OPERATOR_OUTCOME_RECORDED",
                occurred_at_utc=self._clock(),
                payload_digest=self._payload(
                    "omega.oeos.operator-outcome.v1",
                    {"evidence_digest": evidence_digest, "outcome_code": outcome_code},
                ),
            )
            self._store.save(updated, expected_version=task.version)
            return updated

    def recover_queued(self) -> tuple[str, ...]:
        """Rehydrate durable queue state and close crash-left submissions.

        Interrupted in-flight states become recoverable ``STATUS_UNKNOWN``.
        Already-queued tasks retain precedence over ``SUBMITTED`` rows because
        their admission decision was committed before the prior process died.
        """

        recovered = []
        for state in (
            TaskStateV1.PREFLIGHT,
            TaskStateV1.RUNNING,
            TaskStateV1.VERIFYING,
        ):
            for task_id in self._store.tasks_in_state(state):
                task = self.get(task_id)
                self._save_transition(
                    task,
                    TaskStateV1.CANCELLED
                    if task.cancellation_requested
                    else TaskStateV1.STATUS_UNKNOWN,
                    code="TASK_CANCELLED"
                    if task.cancellation_requested
                    else "PROCESS_RESTART_STATUS_UNKNOWN",
                    evidence={
                        "cooperative": task.cancellation_requested,
                        "interrupted_state": state.value,
                    },
                )
        present = set(self._queue.snapshot())
        for task_id in self._store.tasks_in_state(TaskStateV1.QUEUED):
            if task_id in present:
                continue
            if not self._queue.enqueue(task_id):
                return tuple(recovered)
            recovered.append(task_id)
            present.add(task_id)
        for task_id in self._store.tasks_in_state(TaskStateV1.SUBMITTED):
            task = self.get(task_id)
            if not self._queue.enqueue(task_id):
                return tuple(recovered)
            try:
                self._save_transition(
                    task,
                    TaskStateV1.QUEUED,
                    code="SUBMISSION_RECOVERED",
                    evidence={"queue_capacity": self._queue.capacity},
                )
            except Exception:  # noqa: BLE001 - roll back queue reservation and re-raise
                self._queue.remove(task_id)
                raise
            recovered.append(task_id)
            present.add(task_id)
        return tuple(recovered)

    def _run_claimed(
        self,
        task_id: str,
        task: TaskAggregateV1,
        lease: CheckoutLeaseGuardPort,
    ) -> TaskAggregateV1:
        evidence = lease.evidence
        if type(evidence) is not CheckoutLeaseEvidenceV1:
            raise CheckoutLeaseRefusal(
                "MALFORMED_CHECKOUT_LEASE", "lease evidence type differs"
            )
        task = self._save_transition(
            task,
            TaskStateV1.RUNNING,
            code="EXECUTION_STARTED",
            evidence={
                "envelope": task.envelope.canonical_digest,
                "lease": evidence.to_canonical(),
            },
        )
        cancellation = _StoreCancellationProbe(self._store, task_id)
        try:
            result = self._executor.execute(task, cancellation)
            if type(result) is not ExecutionResultV1:
                raise TaskServiceError(
                    "MALFORMED_EXECUTOR_RESULT", "executor returned a different type"
                )
        except Exception as exc:  # noqa: BLE001 - executor port is the boundary
            current = self.get(task_id)
            return self._save_transition(
                current,
                TaskStateV1.CANCELLED
                if current.cancellation_requested
                else TaskStateV1.FAILED,
                code="TASK_CANCELLED"
                if current.cancellation_requested
                else "EXECUTOR_EXCEPTION",
                evidence={
                    "cooperative": current.cancellation_requested,
                    "exception_type": type(exc).__name__,
                },
            )

        lease.assert_held()
        task = self.get(task_id)
        if task.cancellation_requested:
            return self._save_transition(
                task,
                TaskStateV1.CANCELLED,
                code="TASK_CANCELLED",
                evidence={"cooperative": True},
            )
        disposition_targets = {
            ExecutionDispositionV1.NEEDS_INPUT: TaskStateV1.NEEDS_INPUT,
            ExecutionDispositionV1.REFUSED: TaskStateV1.REFUSED,
            ExecutionDispositionV1.FAILED: TaskStateV1.FAILED,
            ExecutionDispositionV1.STATUS_UNKNOWN: TaskStateV1.STATUS_UNKNOWN,
        }
        if result.disposition in disposition_targets:
            return self._save_transition(
                task,
                disposition_targets[result.disposition],
                code=f"EXECUTOR_{result.disposition.value}",
                evidence=result.to_canonical(),
            )
        if result.disposition is not ExecutionDispositionV1.SUCCEEDED:
            raise TaskServiceError("MALFORMED_EXECUTOR_RESULT", "unknown disposition")

        task = self._save_transition(
            task,
            TaskStateV1.VERIFYING,
            code="INDEPENDENT_VERIFICATION_STARTED",
            evidence=result.to_canonical(),
        )
        try:
            verdict = self._verifier.verify(task, result)
            if type(verdict) is not VerificationResultV1:
                raise TaskServiceError(
                    "MALFORMED_VERIFIER_RESULT", "verifier returned a different type"
                )
        except Exception as exc:  # noqa: BLE001 - verifier port is the boundary
            current = self.get(task_id)
            return self._save_transition(
                current,
                TaskStateV1.CANCELLED
                if current.cancellation_requested
                else TaskStateV1.STATUS_UNKNOWN,
                code="TASK_CANCELLED"
                if current.cancellation_requested
                else "VERIFIER_STATUS_UNKNOWN",
                evidence={
                    "cooperative": current.cancellation_requested,
                    "exception_type": type(exc).__name__,
                },
            )
        lease.assert_held()
        task = self.get(task_id)
        if task.cancellation_requested:
            return self._save_transition(
                task,
                TaskStateV1.CANCELLED,
                code="TASK_CANCELLED",
                evidence={"cooperative": True},
            )
        target = TaskStateV1.COMPLETED if verdict.accepted else TaskStateV1.REFUSED
        return self._save_transition(
            task,
            target,
            code="INDEPENDENT_VERIFICATION_ACCEPTED"
            if verdict.accepted
            else "INDEPENDENT_VERIFICATION_REFUSED",
            evidence={
                "execution": result.to_canonical(),
                "verification": verdict.to_canonical(),
            },
        )

    def _record_lease_refusal(
        self, task_id: str, code: str, exception_type: str
    ) -> TaskAggregateV1:
        current = self.get(task_id)
        if current.cancellation_requested:
            target = TaskStateV1.CANCELLED
            event_code = "TASK_CANCELLED"
        elif current.state is TaskStateV1.PREFLIGHT:
            target = TaskStateV1.REFUSED
            event_code = code
        elif current.state in {TaskStateV1.RUNNING, TaskStateV1.VERIFYING}:
            target = TaskStateV1.STATUS_UNKNOWN
            event_code = "CHECKOUT_LEASE_STATUS_UNKNOWN"
        else:
            raise TaskServiceError(
                "LEASE_STATE_MISMATCH", "lease refusal occurred outside execution"
            )
        return self._save_transition(
            current,
            target,
            code=event_code,
            evidence={"exception_type": exception_type, "lease_code": code},
        )

    def run_next(self) -> TaskAggregateV1 | None:
        task_id = self._queue.dequeue()
        if task_id is None:
            return None
        task = self.get(task_id)
        if task.state is not TaskStateV1.QUEUED:
            raise TaskServiceError(
                "QUEUE_STATE_MISMATCH", "queued item has a different state"
            )
        if task.cancellation_requested:
            return self._save_transition(
                task,
                TaskStateV1.CANCELLED,
                code="TASK_CANCELLED",
                evidence={"cooperative": True},
            )
        task = self._save_transition(
            task,
            TaskStateV1.PREFLIGHT,
            code="PREFLIGHT_ENTERED",
            evidence={"capability_snapshot": task.capability_snapshot.canonical_digest},
        )
        if task.operator_input_version is not None and task.encrypted_input_ref is None:
            return self._save_transition(
                task, TaskStateV1.NEEDS_INPUT,
                code="OPERATOR_INPUT_UNAVAILABLE",
                evidence={"input_event_sequence": task.operator_input_version},
            )
        try:
            with self._checkout_lease.claim(task.envelope) as lease:
                return self._run_claimed(task_id, task, lease)
        except CheckoutLeaseRefusal as exc:
            return self._record_lease_refusal(task_id, exc.code, type(exc).__name__)

    def capabilities(self) -> CapabilitySnapshotV1:
        return self._capabilities.snapshot()

    def doctor(self) -> dict[str, object]:
        components = {
            "capabilities": self._capabilities.diagnostic(),
            "checkout_lease": self._checkout_lease.diagnostic(),
            "executor": self._executor.diagnostic(),
            "store": self._store.diagnostic(),
            "verifier": self._verifier.diagnostic(),
        }
        healthy = all(value.get("status") == "HEALTHY" for value in components.values())
        return {
            "authority_effect": "None",
            "components": components,
            "queue_capacity": self._queue.capacity,
            "queue_depth": len(self._queue),
            "status": "HEALTHY" if healthy else "DEGRADED",
        }


__all__ = ["BoundedTaskQueue", "TaskService", "TaskServiceError"]
