"""Console presentation formatter for PFP demos, gates, and pipeline execution.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import List

from ...domain.stages.demos import DemoRunReceipt
from ...domain.contracts.gates import GateReceipt
from ...use_cases.execute_stage_pipeline import PipelineExecutionReceipt


class PfpConsoleView:
    """Formats PFP machine receipts into clear console output."""

    @staticmethod
    def render_demo_receipt(receipt: DemoRunReceipt) -> str:
        lines = [
            "=" * 70,
            f" DEMO RECEIPT: {receipt.demo_id} [{receipt.terminal_status.upper()}]",
            f" Runner: {receipt.runner_id} | Duration: {receipt.duration_sec:.4f}s",
            f" All Checks Passed: {receipt.all_passed}",
            "-" * 70,
        ]
        for c in receipt.checks:
            status_symbol = "[PASS]" if c.passed else "[FAIL]"
            msg = f"  {status_symbol} {c.name}"
            if not c.passed and c.error_message:
                msg += f" -> Error: {c.error_message}"
            lines.append(msg)
        lines.append("=" * 70)
        return "\n".join(lines)

    def display_demo_receipt(self, receipt: DemoRunReceipt) -> None:
        print(self.render_demo_receipt(receipt))

    def display_gate_receipt(self, receipt: GateReceipt) -> None:
        print(self.render_gate_receipt(receipt))

    def display_pipeline_receipt(self, receipt: PipelineExecutionReceipt) -> None:
        print(self.render_pipeline_receipt(receipt))

    @staticmethod
    def render_gate_receipt(receipt: GateReceipt) -> str:
        lines = [
            "=" * 70,
            f" ADVERSARY TRIBUNAL RECEIPT: {receipt.candidate_id} [{receipt.terminal_disposition.upper()}]",
            f" All Gates Passed: {receipt.all_passed}",
            "-" * 70,
        ]
        for v in receipt.verdicts:
            mark = "[PASS]" if v.passed else "[REFUSE]"
            line = f"  {mark} {v.gate_id} ({v.character}): {v.observation}"
            if v.fences_violated:
                line += f"\n         Violations: {', '.join(v.fences_violated)}"
            lines.append(line)
        lines.append("=" * 70)
        return "\n".join(lines)

    @staticmethod
    def render_pipeline_receipt(receipt: PipelineExecutionReceipt) -> str:
        lines = [
            "=" * 70,
            f" PFP STAGE PIPELINE RECEIPT: {receipt.demo_id}",
            f" Terminal Status: {receipt.final_terminal_status.value}",
            f" Completed Stages: {receipt.completed_stages}",
            "-" * 70,
        ]
        for stage_num in receipt.completed_stages:
            resp = receipt.stage_responses.get(stage_num, {})
            lines.append(f"  Stage {stage_num}: OK | Continue={resp.get('should_continue')}")
        lines.append("=" * 70)
        return "\n".join(lines)
