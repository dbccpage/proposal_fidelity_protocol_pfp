"""File-based persistence DB context for Symbol Game entities and aggregates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ...domain import BytePayload, MAX_PAYLOAD_BYTES


class SymbolGameDbContext:
    """Encapsulates root directory and transactional file writes for symbol game storage."""

    def __init__(self, root_dir: Path | str) -> None:
        self.root_dir = Path(root_dir).resolve()
        self.prompts_dir = self.root_dir / "prompts"
        self.receipts_dir = self.root_dir / "receipts"
        self.runs_dir = self.root_dir / "runs"
        self.patches_dir = self.root_dir / "patches"
        self.intake_dir = self.root_dir / "intake"
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for d in (self.prompts_dir, self.receipts_dir, self.runs_dir, self.patches_dir, self.intake_dir):
            d.mkdir(parents=True, exist_ok=True)

    def write_json(self, file_path: Path, data: dict[str, Any]) -> None:
        raw_text = json.dumps(data, sort_keys=True, indent=2)
        payload = BytePayload.from_str(raw_text)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(payload.as_bytes())

    def read_json(self, file_path: Path) -> dict[str, Any] | None:
        if not file_path.exists():
            return None
        raw_bytes = file_path.read_bytes()
        payload = BytePayload(raw_bytes)
        return json.loads(payload.as_str())
