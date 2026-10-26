"""Reporting and receipt serialization adapter for PFP.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..domain.stages.demos import DemoRunReceipt
from ..domain.contracts.gates import GateReceipt


class PfpReportingAdapter:
    """Serializes demo receipts and gate audit reports into deterministic machine artifacts."""

    @staticmethod
    def dump_demo_receipt(receipt: DemoRunReceipt, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = receipt.model_dump(mode="json")
        output_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    @staticmethod
    def dump_gate_receipt(receipt: GateReceipt, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        data = receipt.model_dump(mode="json")
        output_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
