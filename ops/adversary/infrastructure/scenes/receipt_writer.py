"""Scene receipts, trace custody and pharmacy effects at the outer layer."""

import json
import re
import time
from pathlib import Path
from typing import Optional

from eis.domain.pharmacy_seeder import PharmacySeeder
from eis.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from operating_system.adapters.intelligence_custody.ic_routing import intelligence_path
from pfp.domain.bridge.unified_oe_trace import UnifiedOETraceStore
from adversary.domain.residual_algebra.scene_models import SceneExecutionReceipt


class SceneReceiptWriter:
    def __init__(self, repo_root: Path) -> None:
        self.intelligence_dir = intelligence_path(repo_root, "_intelligence/_adversary")
        self.trace_store = UnifiedOETraceStore(repo_root)
        self.pharmacy_seeder = PharmacySeeder(
            repo_root,
            byte_writer=filesystem_byte_writer,
            byte_source=filesystem_catalog_bytes,
        )

    def save_receipt(
        self, receipt: SceneExecutionReceipt, target_dir: Optional[Path] = None
    ) -> Path:
        """Persists a single scene execution receipt to JSON and Markdown in _ic/adversary/."""
        if re.fullmatch(r"[A-Za-z0-9_-]+", receipt.scene_id) is None:
            raise ValueError("scene_id must be a filename-safe identifier")
        out_dir = target_dir or self.intelligence_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = time.strftime("%m%d%Y_%H%M%S")

        # 1. Timestamped JSON receipt
        record = receipt.to_dict()
        if not receipt.valuation.is_measured:
            record["downstream_emissions"] = {
                "unified_trace": "NOT_EMITTED_METRICS_UNAVAILABLE",
                "pharmacy": "NOT_EMITTED_NO_OBSERVED_DEFECT",
            }
        json_content = json.dumps(record, indent=2)
        ts_json_path = out_dir / f"{timestamp_str}_receipt_{receipt.scene_id}.json"
        with open(ts_json_path, "w", encoding="utf-8") as f:
            f.write(json_content)

        # 2. Timestamped Markdown trace
        md_lines = [
            f"# Scene Execution Trace: {receipt.title}",
            "",
            f"- **Scene ID:** `{receipt.scene_id}`",
            f"- **Timestamp:** `{timestamp_str}`",
            f"- **Multicategory Term:** `{receipt.multicategory_term}`",
            f"- **Evidence SHA-256:** `{receipt.evidence_sha256}`",
            f"- **Valuation Residual Norm $\\Phi_1$:** `{receipt.valuation.residual_norm_phi_1}`",
            f"- **Measurement:** `{'MEASURED' if receipt.valuation.is_measured else 'NOT_MEASURED'}`",
            f"- **Valuation detail:** {receipt.valuation.diagnostics.get('reason', '')}",
            f"- **Licensing Verdict:** `{receipt.licensing_verdict}`",
            "- **AuthorityEffect:** `None`",
            "",
            "## Dialogue Beats",
            "",
        ]
        for idx, beat in enumerate(receipt.beats_executed, start=1):
            md_lines.append(f"### Beat {idx}: {beat.speaker} ({beat.operator_tag})")
            md_lines.append("")
            md_lines.append(f"**Cue:** {beat.cue}")
            md_lines.append("")
            md_lines.append(beat.dialogue)
            md_lines.append("")

        md_content = "\n".join(md_lines).strip() + "\n"
        ts_md_path = out_dir / f"{timestamp_str}_trace_{receipt.scene_id}.md"
        with open(ts_md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        if not receipt.valuation.is_measured:
            return ts_json_path

        # 3. Harvest and farm antibodies if any unmitigated defects or non-exact valuations exist
        failure_modes = []
        if receipt.valuation.residual_norm_phi_1 > 0.0:
            failure_modes.append(
                f"scene_residual:{receipt.scene_id}:phi1_{receipt.valuation.residual_norm_phi_1}"
            )
        if receipt.licensing_verdict != "PASS_TO_MASTER":
            failure_modes.append(f"unlicensed_scene_verdict:{receipt.scene_id}")

        farmed = self.pharmacy_seeder.farm_antibodies_from_defects(
            failure_modes,
            run_id=f"{timestamp_str}_scene_{receipt.scene_id}",
            task_id=f"scene_{receipt.scene_id}",
        )
        antibody_ids = [ab.antibody_id for ab in farmed]

        # 4. Append master UTS trace record
        self.trace_store.append_trace(
            task_id=f"scene_{receipt.scene_id}",
            initial_input=f"{receipt.title} | {receipt.multicategory_term}",
            terminal_status=receipt.licensing_verdict,
            rounds_completed=len(receipt.beats_executed),
            final_phi1=receipt.valuation.residual_norm_phi_1,
            final_gamma2=receipt.valuation.gamma_2,
            final_active_count=len(failure_modes),
            failure_modes=failure_modes,
            antibodies_mined=antibody_ids,
            evidence_sha256=receipt.evidence_sha256,
            model="adversary_scene_deliberation_v1",
            run_id=f"{timestamp_str}_scene_{receipt.scene_id}",
        )

        return ts_json_path
