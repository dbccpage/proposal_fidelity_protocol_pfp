"""Unified narrative script emission for a Symbol Game run.

The emitter holds no filesystem root and performs no file I/O: every artifact
goes through the injected ``RunArtifactSinkPort``, which the composition root
binds to an explicit output root. The evidence digest is supplied by the
caller from what the run produced; the emitter never derives one from the task
id or a step count, and it never invents dialogue that no character spoke.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
import time
from typing import Any, Optional, Sequence, Tuple

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_pfp.domain import PacketEnvelopeV2
from omega_engine_pfp.domain.ports.run_artifact_port import (
    RunArtifactSinkPort,
    create_filesystem_artifact_sink,
)
from omega_engine_pfp.functional_boundary import require_rust_functional

from .pharmacy_seeder import PharmacySeeder
from .sbe import SBEAnalyzer
from .symbol_game_models import SymbolGameStepResult
from .symbol_game_packet_ledger import PacketLedgerWriter
from .symbol_game_uns_renderer import UNSRenderer
from .unified_oe_trace import UnifiedOETraceStore

DEFAULT_RUNS_PREFIX = canonical_intelligence_route("_intelligence/symbol_game/runs")
_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


class EvidenceDigestRequired(ValueError):
    """An emission was requested without a digest of the run's own content."""

    code = "EVIDENCE_DIGEST_REQUIRED"


def require_evidence_digest(value: object) -> str:
    if type(value) is not str or _SHA256_HEX.fullmatch(value) is None:
        raise EvidenceDigestRequired(
            f"{EvidenceDigestRequired.code}: evidence_sha256 must be a lowercase "
            f"64-hex digest computed from the run's artifacts, got {value!r}"
        )
    return value


class UnifiedNarrativeScriptEmitter:
    """Application orchestrator for pharmacy, SBE, UTS, packet ledger, and UNS artifacts."""

    def __init__(
        self,
        *,
        artifact_sink: Optional[RunArtifactSinkPort] = None,
        repo_root: Optional[Any] = None,
        target_dir: Optional[Any] = None,
        pharmacy_seeder: Optional[PharmacySeeder] = None,
        trace_store: Optional[UnifiedOETraceStore] = None,
        sbe_analyzer: Optional[SBEAnalyzer] = None,
        packet_ledger: Optional[PacketLedgerWriter] = None,
        runs_prefix: str = DEFAULT_RUNS_PREFIX,
    ):
        if artifact_sink is None and repo_root is None and target_dir is None:
            raise TypeError("artifact_sink, repo_root, or target_dir must be provided")

        self.runs_prefix = runs_prefix.strip("/")
        if target_dir is not None:
            resolved_sink: RunArtifactSinkPort = create_filesystem_artifact_sink(str(target_dir))
        elif repo_root is not None:
            cleaned_root = str(repo_root).rstrip("/\\")
            root_prefix = f"{cleaned_root}/{self.runs_prefix}"
            resolved_sink = create_filesystem_artifact_sink(root_prefix)
        elif artifact_sink is not None:
            resolved_sink = artifact_sink
        else:
            raise TypeError("artifact_sink, repo_root, or target_dir must be provided")

        if not isinstance(resolved_sink, RunArtifactSinkPort):
            raise TypeError("artifact_sink must implement RunArtifactSinkPort")
        self.artifact_sink = resolved_sink
        self.sbe_analyzer = sbe_analyzer or SBEAnalyzer()
        self.trace_store = trace_store or UnifiedOETraceStore(
            self.artifact_sink, sbe_analyzer=self.sbe_analyzer
        )
        if pharmacy_seeder is not None:
            self.pharmacy_seeder = pharmacy_seeder
        elif repo_root is not None:
            self.pharmacy_seeder = PharmacySeeder(repo_root=repo_root)
        else:
            self.pharmacy_seeder = PharmacySeeder()
        self.packet_ledger = packet_ledger or PacketLedgerWriter()
        self.renderer = UNSRenderer(self.sbe_analyzer)

    @property
    def target_dir(self) -> Any:
        if hasattr(self.artifact_sink, "root"):
            return self.artifact_sink.root
        return self.runs_prefix



    def emit_full_trace(
        self,
        task_id: str,
        step_results: Sequence[SymbolGameStepResult],
        initial_packet: PacketEnvelopeV2,
        *,
        evidence_sha256: str,
        terminal_status: str = "PASS_TO_MASTER",
        run_prefix: Optional[str] = None,
    ) -> Tuple[str, str]:
        return self.emit_uns_trace(
            task_id,
            initial_packet,
            step_results,
            terminal_status,
            evidence_sha256,
            run_prefix,
        )

    def emit_uns_trace(
        self,
        task_id: str,
        packet_0: PacketEnvelopeV2,
        step_results: Sequence[SymbolGameStepResult],
        terminal_status: str,
        evidence_sha256: str,
        run_prefix: Optional[str] = None,
    ) -> Tuple[str, str]:
        if not step_results:
            require_rust_functional("UnifiedNarrativeScriptEmitter.empty_trace")
        evidence_sha256 = require_evidence_digest(evidence_sha256)
        timestamp_str = time.strftime("%m%d%Y_%H%M%S")
        clean_slug = task_id.replace("-", "_")[:32].rstrip("_")
        run_id = f"{timestamp_str}_{clean_slug}"

        defects = list(
            dict.fromkeys(
                obstruction
                for step in step_results
                for obstruction in step.obstruction_score.active_obstruction_ids
            )
        )
        # Only dialogue the characters actually produced; an empty debate stays empty.
        dialogue_turns = [beat.dialogue for step in step_results for beat in step.character_debates]
        antibodies = self.pharmacy_seeder.farm_antibodies_from_defects(
            defects, run_id=run_id, task_id=task_id
        )
        antibody_ids = [antibody.antibody_id for antibody in antibodies]
        session_sbe = self.sbe_analyzer.analyze_dialogue_ensemble(dialogue_turns)

        final_score = step_results[-1].obstruction_score
        initial_input = self._packet_initial_input(packet_0, task_id)
        self.trace_store.append_trace(
            task_id=task_id,
            initial_input=initial_input,
            terminal_status=terminal_status,
            rounds_completed=len(step_results),
            final_phi1=final_score.phi_1,
            final_gamma2=final_score.gamma_2,
            final_active_count=final_score.active_count,
            failure_modes=defects,
            antibodies_mined=antibody_ids,
            evidence_sha256=evidence_sha256,
            run_id=run_id,
            sbe_metrics=session_sbe.to_dict(),
        )

        run_dir = (run_prefix or f"{self.runs_prefix}/{run_id}").strip("/")
        packets_locator, packets_filename = self.packet_ledger.write(
            artifact_sink=self.artifact_sink,
            run_dir=run_dir,
            timestamp_str=timestamp_str,
            clean_slug=clean_slug,
            task_id=task_id,
            packet_0=packet_0,
            step_results=step_results,
        )

        uns_markdown, _ = self.renderer.render(
            task_id=task_id,
            packet_0=packet_0,
            step_results=step_results,
            terminal_status=terminal_status,
            evidence_sha256=evidence_sha256,
            timestamp_str=timestamp_str,
            antibody_ids=antibody_ids,
            session_sbe=session_sbe,
            packets_filename=packets_filename,
            packets_path=packets_locator,
        )

        uns_locator = self.artifact_sink.put_text(f"{run_dir}/{run_id}_uns_trace.md", uns_markdown)
        return uns_locator, packets_locator

    def _packet_initial_input(self, packet_0: PacketEnvelopeV2, fallback_task_id: str) -> str:
        payload = packet_0.payload if isinstance(packet_0.payload, dict) else {}
        if "content" in payload:
            return str(payload["content"])
        if "prompt" in payload:
            return str(payload["prompt"])
        if "title" in payload:
            return str(payload["title"])
        return f"task:{fallback_task_id}"


__all__ = [
    "DEFAULT_RUNS_PREFIX",
    "EvidenceDigestRequired",
    "UnifiedNarrativeScriptEmitter",
    "require_evidence_digest",
]
