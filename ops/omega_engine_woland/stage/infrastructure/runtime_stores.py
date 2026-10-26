"""
runtime_stores.py
=================

Canonical Universal Narrative Stream (UNS) and Universal Trace Stream (UTS)
persistence stores for the Woland stage.

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

AUTHORITY_EFFECT_NONE = "None"


class UniversalNarrativeStore:
    """Canonical Universal Narrative Stream (UNS) writer.

    Renders clean, human-readable 7-Act UNS novellas into _ic/odni/narratives/uns_<session_id>.md.
    """

    def __init__(self, repo_root: Path | str) -> None:
        self.repo_root = Path(repo_root)
        self.narratives_root = self.repo_root / canonical_intelligence_route("_intelligence/narratives")

    def record_narrative(
        self, session_id: str, turn_md: str, *, title: str = ""
    ) -> Result[str, Refusal]:
        """Write or append clean UNS narrative novella markdown."""
        try:
            self.narratives_root.mkdir(parents=True, exist_ok=True)
            file_stem = session_id if session_id.startswith("uns_") else f"uns_{session_id}"
            novella_file = self.narratives_root / f"{file_stem}.md"

            content = turn_md.strip()
            if content.startswith("# Universal Narrative") or content.startswith("# UNS"):
                novella_file.write_text(content + "\n", encoding="utf-8")
            else:
                now_utc = datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%SZ"
                )
                if not novella_file.exists():
                    doc_title = title or f"Universal Narrative Stream: {session_id}"
                    header = (
                        f"# {doc_title}\n\n"
                        f"- **Session ID:** `{session_id}`\n"
                        f"- **Created (UTC):** {now_utc}\n"
                        f"- **AuthorityEffect:** `None`\n\n"
                        f"---\n\n"
                    )
                    novella_file.write_text(header, encoding="utf-8")

                entry = f"### Turn [{now_utc}]\n\n{content}\n\n---\n\n"
                with open(novella_file, "a", encoding="utf-8") as fp:
                    fp.write(entry)

            # Also maintain canonical latest novella link
            latest_file = self.repo_root / canonical_intelligence_route("_intelligence/universal_narrative_stream.md")
            latest_file.parent.mkdir(parents=True, exist_ok=True)
            if content.startswith("# Universal Narrative") or content.startswith("# UNS"):
                latest_file.write_text(content + "\n", encoding="utf-8")

            return Ok(session_id)
        except OSError as e:
            return Err(
                Refusal(
                    code="UNS_PERSISTENCE_FAILED",
                    message=f"Failed to write narrative to {novella_file}: {e}",
                    locus="UniversalNarrativeStore.record_narrative",
                )
            )


@dataclass(frozen=True)
class PromptPerception:
    """Prompt perception metrics extracted from input payload."""

    prompt_class: str = "Assertion"
    morphism_type: str = "Verify"
    entropy: float = 0.5
    coherence: float = 1.0
    decidability: float = 0.5
    hostility: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class UnifiedTraceRecord:
    """Master terminal trace record for unified_oe_trace.jsonl."""

    timestamp: str
    run_id: str
    task_id: str
    model: str
    fingerprint: str
    prompt_length: int
    perception: dict[str, Any]
    sbe: dict[str, Any]
    residuals: dict[str, Any]
    verdict: dict[str, Any]
    antibodies_mined: list[str]
    evidence_sha256: str
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True) + "\n"


class UniversalTraceStore:
    """Canonical Universal Trace Stream (UTS) writer.

    Records every Intelligence Event (IE) to per-day JSONL files under _ic/nsa/events/
    and terminal run records to _ic/odni/unified_oe_trace.jsonl.
    """

    def __init__(self, repo_root: Path | str) -> None:
        self.repo_root = Path(repo_root)
        self.events_root = self.repo_root / canonical_intelligence_route("_intelligence/events")
        self.trace_file = self.repo_root / canonical_intelligence_route("_intelligence/unified_oe_trace.jsonl")

    def record_event(self, event: Any, raw_payload: bytes) -> Result[str, Refusal]:
        """Record an Intelligence Event to disk."""
        try:
            self.events_root.mkdir(parents=True, exist_ok=True)
            day_str = getattr(event, "ts_utc", "")[:10] or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            day_file = self.events_root / f"events_{day_str}.jsonl"

            line = json.dumps(asdict(event) if hasattr(event, "__dataclass_fields__") else event, sort_keys=True) + "\n"
            with open(day_file, "a", encoding="utf-8") as fp:
                fp.write(line)

            payload_file = self.events_root / f"{getattr(event, 'ie_id', 'event')}.payload"
            payload_file.write_bytes(raw_payload)

            return Ok(getattr(event, "ie_id", ""))
        except OSError as e:
            return Err(
                Refusal(
                    code="UTS_PERSISTENCE_FAILED",
                    message=f"Failed to record event: {e}",
                    locus="UniversalTraceStore.record_event",
                )
            )

    def record_terminal(self, record: UnifiedTraceRecord) -> Result[str, Refusal]:
        """Record a terminal run record to unified_oe_trace.jsonl."""
        try:
            self.trace_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.trace_file, "a", encoding="utf-8") as fp:
                fp.write(record.to_json_line())
            return Ok(record.run_id)
        except OSError as e:
            return Err(
                Refusal(
                    code="UTS_PERSISTENCE_FAILED",
                    message=f"Failed to record terminal trace: {e}",
                    locus="UniversalTraceStore.record_terminal",
                )
            )


__all__ = [
    "UniversalNarrativeStore",
    "PromptPerception",
    "UnifiedTraceRecord",
    "UniversalTraceStore",
]
