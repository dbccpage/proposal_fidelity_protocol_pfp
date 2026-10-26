from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class PromptPerception:
    prompt_class: str = "Assertion"
    morphism_type: str = "Verify"
    entropy: float = 0.5
    coherence: float = 1.0
    decidability: float = 0.5
    hostility: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UnifiedTraceRecord:
    timestamp: str
    run_id: str
    task_id: str
    model: str
    fingerprint: str
    prompt_length: int
    perception: Dict[str, Any]
    sbe: Dict[str, Any]
    residuals: Dict[str, Any]
    verdict: Dict[str, Any]
    antibodies_mined: List[str]
    evidence_sha256: str
    authority_effect: str = "None"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json_line(self) -> str:
        import json
        return json.dumps(self.to_dict()) + "\n"
