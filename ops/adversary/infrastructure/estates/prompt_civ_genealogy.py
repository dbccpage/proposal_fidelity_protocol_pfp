"""Prompt Civilization's hash-chained genealogy store as the Adversary lineage port.

Each bout is recorded as a re-entry lineage entry from its task to its receipt, with the
bout's blockers as structural deficiencies. The store is append-only and refuses a
conflicting entry for an existing child.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from operations.domain.rop.result import Err, Ok, Refusal, Result
from pciv.domain.models import GenealogyEntryV1
from pciv.infrastructure.genealogy_adapter import (
    FileGenealogyAdapter,
)
from adversary.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from adversary.domain.specialization import PortName

from .probe_support import observed, refusal, run_probe

_LOCUS = "adversary.infrastructure.estates.prompt_civ_genealogy"
RE_ENTRY_REASON = "ADVERSARY_SWARM_BOUT"


class PromptCivGenealogyAdapter:
    estate = EstateName.PROMPT_CIVILIZATION
    port = PortName.PROMPT_GENEALOGY
    adapter_id = "prompt_civilization.file_genealogy"

    def __init__(self, lineage_file: Path) -> None:
        self.lineage_file = Path(lineage_file)

    @staticmethod
    def _entry(
        parent_key: str, child_key: str, deficiencies: Sequence[str], guidance: str
    ) -> GenealogyEntryV1:
        # The store takes normalized, unique, non-empty text; blockers are trimmed and
        # deduplicated in order rather than refused for surrounding whitespace.
        cleaned = tuple(dict.fromkeys(item.strip() for item in deficiencies if item.strip()))
        return GenealogyEntryV1(
            parent_run_key=parent_key,
            child_run_key=child_key,
            structural_deficiencies=cleaned,
            concrete_fixes=(),
            next_run_guidance=guidance.strip(),
            re_entry_reason=RE_ENTRY_REASON,
        )

    def record_lineage(
        self, parent_key: str, child_key: str, deficiencies: Sequence[str], guidance: str
    ) -> Result[str, Refusal]:
        try:
            entry = self._entry(parent_key, child_key, deficiencies, guidance)
        except (TypeError, ValueError) as exc:
            return Err(refusal("GENEALOGY_ENTRY_INVALID", exc, _LOCUS))
        recorded = FileGenealogyAdapter(self.lineage_file).record_lineage(entry)
        if isinstance(recorded, Err):
            return recorded
        return Ok(entry.lineage_id)

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            path = Path(scratch_root) / "swarm_lineage.jsonl"
            entry = self._entry(
                "task:connection-probe", "bout:connection-probe", ("probe deficiency",), "probe"
            )
            recorded = FileGenealogyAdapter(path).record_lineage(entry)
            if isinstance(recorded, Err):
                return disconnected(self.estate, self.port, self.adapter_id, recorded.error.code)
            read_back = FileGenealogyAdapter(path).get_lineage(entry.child_run_key)
            if isinstance(read_back, Err) or read_back.value != entry:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "lineage entry not read back"
                )
            raw = path.read_bytes()
            sealed = json.loads(raw.splitlines()[0])
            if sealed["payload"]["lineage_id"] != entry.lineage_id:
                return disconnected(
                    self.estate, self.port, self.adapter_id, "sealed record differs"
                )
            return observed(
                self.estate,
                self.port,
                self.adapter_id,
                raw,
                "appended one sealed lineage record and read it back",
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)


__all__ = ["RE_ENTRY_REASON", "PromptCivGenealogyAdapter"]
