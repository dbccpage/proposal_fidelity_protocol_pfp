"""Host-check and durable ingestion ports. AuthorityEffect: None."""

from dataclasses import dataclass
from typing import Iterable, Mapping, Protocol


@dataclass(frozen=True)
class SourceRecordV1:
    path: str
    offset: int
    next_offset: int
    prefix_sha256: str
    raw: bytes


@dataclass(frozen=True)
class DefectWitnessV1:
    """An exact host replay result; a raw model finding is not this witness."""

    defect_id: str
    observation_id: str
    checker_digest: str
    witness_digest: str


class TelemetrySource(Protocol):
    def read_batch(
        self, checkpoints: Mapping[str, tuple[int, str]], limit: int,
    ) -> Iterable[SourceRecordV1]: ...


class DefectVerifier(Protocol):
    def verify(self, record: Mapping[str, object], source: SourceRecordV1) -> DefectWitnessV1 | None: ...


class MetabolismStore(Protocol):
    def checkpoints(self) -> Mapping[str, tuple[int, str]]: ...

    def record(
        self, source: SourceRecordV1, witness: DefectWitnessV1 | None,
        required_support: int, residual: str | None,
    ) -> str | None: ...
