"""Scene catalog and receipt effect boundaries."""

from pathlib import Path
from typing import Protocol

from .scene_models import SceneExecutionReceipt, WolandScene


class SceneRepository(Protocol):
    def load_scenes(self) -> list[WolandScene]: ...


class SceneReceiptStore(Protocol):
    intelligence_dir: Path

    def save_receipt(
        self, receipt: SceneExecutionReceipt, target_dir: Path | None = None
    ) -> Path: ...
