"""Read-only source mining with observable parse failures and physical byte offsets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from omega_engine_prompt_civilization.domain.intelligence_metabolism.models import (
    MinedRecordV1,
    MiningFailureV1,
)

from .sources import SOURCE_REGISTRY, DataSourceAdapter


class IntelligenceMiner:
    def __init__(
        self, repo_root: Path, sources: dict[str, DataSourceAdapter] | None = None
    ) -> None:
        self.repo_root = repo_root
        self.sources = SOURCE_REGISTRY if sources is None else sources
        self.failures: list[MiningFailureV1] = []

    def _parse(
        self,
        raw: bytes,
        *,
        source_id: str,
        file_path: str,
        file_sha256: str,
        offset: int,
        parser_kind: str,
    ) -> MinedRecordV1 | None:
        try:
            payload: Any = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            self.failures.append(
                MiningFailureV1(
                    "METABOLISM_RECORD_UNREADABLE",
                    str(error),
                    source_id,
                    file_path,
                    file_sha256,
                    offset,
                )
            )
            return None
        if not isinstance(payload, dict):
            self.failures.append(
                MiningFailureV1(
                    "METABOLISM_RECORD_INVALID",
                    "record must be a JSON object",
                    source_id,
                    file_path,
                    file_sha256,
                    offset,
                )
            )
            return None
        if parser_kind == "receipt_folder":
            record_type = "run_receipt"
        elif parser_kind == "jsonl":
            record_type = payload.get("letter", payload.get("kind", "jsonl_row"))
        else:
            record_type = payload.get("schema", payload.get("schema_version", "generic_json"))
        if not isinstance(record_type, str):
            self.failures.append(
                MiningFailureV1(
                    "METABOLISM_RECORD_INVALID",
                    "record type must be text",
                    source_id,
                    file_path,
                    file_sha256,
                    offset,
                )
            )
            return None
        return MinedRecordV1(source_id, file_path, file_sha256, offset, record_type, payload)

    def mine_source(self, source_id: str) -> Iterator[MinedRecordV1]:
        adapter = self.sources.get(source_id)
        if adapter is None:
            raise KeyError(f"Unknown intelligence source: {source_id}")
        source_dir = adapter.resolve_path(self.repo_root)
        if not source_dir.exists():
            return
        if adapter.record_parser_kind not in {"json", "receipt_folder", "jsonl"}:
            self.failures.append(
                MiningFailureV1(
                    "METABOLISM_SOURCE_INVALID",
                    "unknown record parser kind",
                    source_id,
                    adapter.relative_path,
                    "",
                    0,
                )
            )
            return
        for path in sorted(source_dir.glob(adapter.file_pattern)):
            if not path.is_file():
                continue
            relative_path = str(path.relative_to(self.repo_root)).replace("\\", "/")
            try:
                path.resolve().relative_to(self.repo_root.resolve())
            except ValueError:
                self.failures.append(
                    MiningFailureV1(
                        "METABOLISM_SOURCE_OUTSIDE_ROOT",
                        "source file escapes the declared repository",
                        source_id,
                        relative_path,
                        "",
                        0,
                    )
                )
                continue
            try:
                raw = path.read_bytes()
            except OSError as error:
                self.failures.append(
                    MiningFailureV1(
                        "METABOLISM_SOURCE_UNAVAILABLE", str(error), source_id, relative_path, "", 0
                    )
                )
                continue
            digest = hashlib.sha256(raw).hexdigest()
            if adapter.record_parser_kind == "jsonl":
                offset = 0
                for line in raw.splitlines(keepends=True):
                    if line.strip():
                        record = self._parse(
                            line,
                            source_id=source_id,
                            file_path=relative_path,
                            file_sha256=digest,
                            offset=offset,
                            parser_kind="jsonl",
                        )
                        if record is not None:
                            yield record
                    offset += len(line)
            else:
                record = self._parse(
                    raw,
                    source_id=source_id,
                    file_path=relative_path,
                    file_sha256=digest,
                    offset=0,
                    parser_kind=adapter.record_parser_kind,
                )
                if record is not None:
                    yield record

    def mine_all(self) -> Iterator[MinedRecordV1]:
        for source_id in sorted(self.sources):
            yield from self.mine_source(source_id)
