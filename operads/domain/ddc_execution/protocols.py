"""Execution and parser ports; implementations own all external effects."""

from typing import Any, Protocol, Sequence

from operads.domain.operad.errors import Result

from .errors import OperadDomainError
from .execution import EvaluationOutcome
from .tape import OperadCompositionReceipt
from .value_objects import EvidenceTraceReport, ExecutionRunRecord, OperadOperation


class OperadRegistryPort(Protocol):
    def resolve_operation(self, skill_id: str) -> OperadOperation: ...

    def check_agent_license(self, agent_id: str | None, skill_id: str) -> None: ...


class TraceStoragePort(Protocol):
    def load_trace(self, skill_id: str) -> EvidenceTraceReport: ...

    def append_run(
        self, skill_id: str, record: ExecutionRunRecord, signature_str: str
    ) -> EvidenceTraceReport: ...


class MorphismEvaluatorPort(Protocol):
    def is_bound(self, skill_id: str) -> bool: ...

    def evaluate(
        self, skill_id: str, inputs: Sequence[str], output_hint: str | None = None
    ) -> Result[EvaluationOutcome, OperadDomainError]: ...


class ArtifactCustodyPort(Protocol):
    def verify(self, path: str, sha256: str) -> None: ...


class DdcTapeParserPort(Protocol):
    def parse(
        self, source: str | Sequence[dict[str, Any]]
    ) -> Result[OperadCompositionReceipt, OperadDomainError]: ...


class DdcReceiptStoragePort(Protocol):
    def destination(self, run_id: str, explicit: str | None, vault: str | None) -> str: ...

    def persist(
        self, receipt: OperadCompositionReceipt, path: str
    ) -> Result[str, OperadDomainError]: ...
