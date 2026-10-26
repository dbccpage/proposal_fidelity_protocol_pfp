"""Ports for the research Level Engine. AuthorityEffect: None."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class LevelEngineOutcome:
    challenge_id: str
    terminal: str
    evidence_grade: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("research outcomes cannot promote authority")

    def __hash__(self) -> int:
        return hash((type(self), self.challenge_id, self.terminal, self.evidence_grade, self.authority_effect))

class LevelEngineRunner(Protocol):
    def run(self, challenge_id: str) -> LevelEngineOutcome: ...

class LevelEngineEvidenceReader(Protocol):
    def read_bytes(self, version: str, path: str, *, revision: str | None = None,
                   sha256: str | None = None) -> bytes: ...
