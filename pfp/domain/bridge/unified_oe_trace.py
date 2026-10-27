"""Unified OE append-only trace, written through the run artifact port.

The store holds no filesystem root and opens no file; the injected
``RunArtifactSinkPort`` is bound to an explicit output root by the composition
root. A record's evidence digest must be supplied by the caller; the store
never derives one from the task id, run id and clock.

AuthorityEffect: None.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Sequence

from governance.domain.intelligence_community import canonical_intelligence_route
from pfp.domain.ports.run_artifact_port import (
    RunArtifactSinkPort,
    create_filesystem_artifact_sink,
)

from .trace_models import PromptPerception, UnifiedTraceRecord
from .trace_policy import PromptPerceptionClassifier, TraceVerdictPolicy


class SBEAnalyzerPort(Protocol):
    def analyze_text(self, text: str): ...


TRACE_LEDGER = canonical_intelligence_route("_intelligence/unified_oe_trace.jsonl")
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class UnifiedOETraceStore:
    """Append-only JSONL persistence; classification and verdict policy are injected collaborators."""

    def __init__(
        self,
        artifact_sink: Optional[RunArtifactSinkPort | Any] = None,
        *,
        perception_classifier: Optional[PromptPerceptionClassifier] = None,
        verdict_policy: Optional[TraceVerdictPolicy] = None,
        sbe_analyzer: Optional[SBEAnalyzerPort] = None,
    ):
        if artifact_sink is None:
            from operating_system.adapters.intelligence_custody.intelligence_root import (
                resolve_intelligence_repo_root,
            )

            self.artifact_sink: RunArtifactSinkPort = create_filesystem_artifact_sink(
                resolve_intelligence_repo_root()
            )
        elif isinstance(artifact_sink, RunArtifactSinkPort):
            self.artifact_sink = artifact_sink
        elif isinstance(artifact_sink, str) or hasattr(artifact_sink, "__fspath__"):
            self.artifact_sink = create_filesystem_artifact_sink(str(artifact_sink))
        else:
            raise TypeError("artifact_sink must implement RunArtifactSinkPort or be a path/str")
        self.perception_classifier = perception_classifier or PromptPerceptionClassifier()
        self.verdict_policy = verdict_policy or TraceVerdictPolicy()
        self._sbe_analyzer = sbe_analyzer

    def append_trace(
        self,
        *,
        task_id: str,
        initial_input: str,
        terminal_status: str,
        rounds_completed: int,
        final_phi1: float,
        final_gamma2: float,
        final_active_count: int,
        evidence_sha256: str,
        failure_modes: Sequence[str] = (),
        antibodies_mined: Sequence[str] = (),
        model: str = "symbol_game_control_spine_v1",
        run_id: Optional[str] = None,
        perception: Optional[PromptPerception] = None,
        sbe_metrics: Optional[Dict[str, Any]] = None,
    ) -> UnifiedTraceRecord:
        if type(evidence_sha256) is not str or _SHA256_HEX.fullmatch(evidence_sha256) is None:
            raise ValueError(
                "EVIDENCE_DIGEST_REQUIRED: evidence_sha256 must be a lowercase 64-hex "
                f"digest of the run's artifacts, got {evidence_sha256!r}"
            )
        now_utc = datetime.now(timezone.utc).isoformat()
        rid = run_id or str(uuid.uuid4())
        fingerprint = hashlib.sha256(initial_input.encode("utf-8")).hexdigest()[:16]
        perception_value = perception or self.perception_classifier.classify(initial_input)
        sbe_dict = dict(sbe_metrics) if sbe_metrics is not None else self._analyze_input(initial_input)
        residuals = self.verdict_policy.residuals(
            final_phi1=final_phi1,
            final_gamma2=final_gamma2,
            final_active_count=final_active_count,
            rounds_completed=rounds_completed,
        )
        verdict = self.verdict_policy.verdict(
            residuals,
            terminal_status=terminal_status,
            failure_modes=failure_modes,
        )

        record = UnifiedTraceRecord(
            timestamp=now_utc,
            run_id=rid,
            task_id=task_id,
            model=model,
            fingerprint=fingerprint,
            prompt_length=len(initial_input),
            perception=perception_value.to_dict(),
            sbe=sbe_dict,
            residuals=residuals,
            verdict=verdict,
            antibodies_mined=list(antibodies_mined),
            evidence_sha256=evidence_sha256,
            authority_effect="None",
        )

        self.artifact_sink.append_lines(TRACE_LEDGER, [record.to_json_line().rstrip("\n")])
        return record

    def read_all_traces(self) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for line in self.artifact_sink.read_lines(TRACE_LEDGER):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return records

    def _analyze_input(self, initial_input: str) -> Dict[str, Any]:
        analyzer = self._sbe_analyzer
        if analyzer is None:
            from .sbe import SBEAnalyzer
            analyzer = SBEAnalyzer()
            self._sbe_analyzer = analyzer
        return analyzer.analyze_text(initial_input).to_dict()


__all__ = ["PromptPerception", "TRACE_LEDGER", "UnifiedTraceRecord", "UnifiedOETraceStore"]
