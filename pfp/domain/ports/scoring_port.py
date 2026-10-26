"""Native scoring port and explicit composition registry. AuthorityEffect: None."""

from __future__ import annotations

from typing import Any, Mapping, Protocol

from ..entities.coboundary_score import CandidateProposal, CoboundaryScoreResult
from ..exceptions import RefusalError


class NativeScoringRefusal(RefusalError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class ScoringPort(Protocol):
    def invoke_scoring(self, action: str, payload: Mapping[str, Any]) -> Any: ...


_DEFAULT_PORT: ScoringPort | None = None


def register_default_scoring_port(port: ScoringPort) -> None:
    global _DEFAULT_PORT
    _DEFAULT_PORT = port


def get_default_scoring_port() -> ScoringPort:
    if _DEFAULT_PORT is None:
        raise NativeScoringRefusal(
            "SCORING_PORT_UNAVAILABLE", "compose a native scoring adapter or inject scoring_port"
        )
    return _DEFAULT_PORT


class IScoringEvaluator(Protocol):
    """Existing domain scoring port for injected evaluators."""

    def evaluate_coboundary(self, proposal: CandidateProposal) -> CoboundaryScoreResult: ...
