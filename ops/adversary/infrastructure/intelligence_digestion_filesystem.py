"""Confined local filesystem adapter for intelligence digestion writes.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adversary.use_cases.intelligence_digestion.archive_custody import checked_path


@dataclass(frozen=True)
class LocalIntelligenceDigestionFileSystem:
    """Perform durable writes only beneath one validated repository root."""

    repo_root: Path

    def _checked(self, path: Path) -> Path:
        return checked_path(self.repo_root, path)

    def ensure_directory(self, path: Path) -> None:
        self._checked(path).mkdir(parents=True, exist_ok=True)

    def create_directory(self, path: Path) -> None:
        target = self._checked(path)
        self.ensure_directory(target.parent)
        target.mkdir(exist_ok=False)

    def atomic_write_json(self, path: Path, payload: Mapping[str, Any]) -> None:
        target = self._checked(path)
        self.ensure_directory(target.parent)
        encoded = (
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        ).encode("utf-8")
        temporary = self._checked(target.with_name(f".{target.name}.tmp"))
        try:
            with open(temporary, "wb") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
            self._sync_directory(target.parent)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _sync_directory(directory: Path) -> None:
        if os.name == "nt":
            return
        descriptor = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def append_bytes(self, path: Path, payload: bytes) -> None:
        target = self._checked(path)
        self.ensure_directory(target.parent)
        with open(target, "ab") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
