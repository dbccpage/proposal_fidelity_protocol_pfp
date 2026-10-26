"""Content-Addressed Storage (CAS) and Snapshot Vault implementation.

Stores files by SHA-256 digest in an append-only vault structure under:
  _ic/nara/harvest/vault/<digest[:2]>/<digest>
and records snapshot manifests under:
  _ic/nara/harvest/snapshots/<snapshot_id>.json

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Sequence

from omega_engine_operads.domain.autopoiesis.entities import (
    HarvestRecord,
    HarvestSnapshot,
)
from omega_engine_operads.domain.autopoiesis.ports import HarvestVaultPort


class FileHarvestVault(HarvestVaultPort):
    """Local filesystem Content-Addressable Storage (CAS) vault."""

    def __init__(
        self,
        root_dir: Path | str,
        snapshots_dir: Path | str | None = None,
        *,
        archive_snapshots_dir: Path | str | None = None,
    ) -> None:
        self.root_dir = Path(root_dir).resolve()
        self.vault_dir = self.root_dir / "vault"
        self.snapshots_dir = (
            Path(snapshots_dir).resolve() if snapshots_dir else self.root_dir / "snapshots"
        )
        self.archive_snapshots_dir = (
            Path(archive_snapshots_dir).absolute() if archive_snapshots_dir is not None
            else self.root_dir.parent / "archive" / "harvest" / "snapshots"
        )
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.archive_zip_path = self.root_dir / "harvest_vault_archive.zip"
        self._zip_file: zipfile.ZipFile | None = None
        self._zip_namelist: set[str] | None = None

    def _get_archive_zip(self) -> zipfile.ZipFile | None:
        if self._zip_file is None:
            zip_target = self.archive_zip_path
            if not zip_target.exists():
                alt_zip = self.root_dir / "vault.zip"
                if alt_zip.exists():
                    zip_target = alt_zip
            if zip_target.exists():
                self._zip_file = zipfile.ZipFile(zip_target, "r")
                self._zip_namelist = set(self._zip_file.namelist())
        return self._zip_file

    def close(self) -> None:
        if self._zip_file is not None:
            self._zip_file.close()
            self._zip_file = None
            self._zip_namelist = None

    def __enter__(self) -> FileHarvestVault:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    @staticmethod
    def _regular_bytes(path: Path) -> bytes | None:
        try:
            info = path.lstat()
        except FileNotFoundError:
            return None
        if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"CAS_REFUSAL: non-regular object: {path}")
        return path.read_bytes()

    @staticmethod
    def _immutable_write(path: Path, content: bytes) -> bool:
        existing = FileHarvestVault._regular_bytes(path)
        if existing is not None:
            if existing != content:
                raise ValueError(f"CAS_REFUSAL: existing content differs: {path}")
            return False
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        try:
            try:
                os.link(temporary, path)
            except FileExistsError:
                if FileHarvestVault._regular_bytes(path) != content:
                    raise ValueError(f"CAS_REFUSAL: concurrent content differs: {path}")
                return False
            return True
        finally:
            temporary.unlink()

    def _object_path(self, digest: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("CAS_REFUSAL: expected a lowercase SHA-256 digest")
        parent = self.vault_dir / digest[:2]
        if parent.exists():
            for directory in (self.vault_dir, parent):
                info = directory.lstat()
                if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                    raise ValueError("CAS_REFUSAL: non-regular vault directory")
        return parent / digest

    def _snapshot_path(self, snapshot_id: str, *, archived: bool = False) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", snapshot_id):
            raise ValueError("CAS_REFUSAL: invalid snapshot ID")
        target = self.snapshots_dir / f"{snapshot_id}.json"
        if archived and not target.exists():
            archive_target = self.archive_snapshots_dir / f"{snapshot_id}.json"
            if archive_target.exists():
                info = self.archive_snapshots_dir.lstat()
                if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                    raise ValueError("CAS_REFUSAL: non-regular archive snapshot directory")
                return archive_target
        info = self.snapshots_dir.lstat()
        if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("CAS_REFUSAL: non-regular snapshot directory")
        return target

    def put_file(self, content_bytes: bytes, expected_sha256: str) -> bool:
        """Stores content in CAS if not already present. Returns True if newly written."""
        if hashlib.sha256(content_bytes).hexdigest() != expected_sha256:
            raise ValueError("CAS_REFUSAL: content digest mismatch")
        target_path = self._object_path(expected_sha256)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return self._immutable_write(target_path, content_bytes)

    def get_file(self, sha256: str) -> bytes | None:
        """Retrieves raw content from CAS by SHA-256 digest."""
        content = self._regular_bytes(self._object_path(sha256))
        if content is None:
            zf = self._get_archive_zip()
            if zf is not None and self._zip_namelist is not None:
                member_path = f"{sha256[:2]}/{sha256}"
                if member_path in self._zip_namelist:
                    raw_zip_bytes = zf.read(member_path)
                    if hashlib.sha256(raw_zip_bytes).hexdigest() == sha256:
                        content = raw_zip_bytes
                    elif hashlib.sha256(raw_zip_bytes.replace(b"\n", b"\r\n")).hexdigest() == sha256:
                        content = raw_zip_bytes.replace(b"\n", b"\r\n")
                    elif hashlib.sha256(raw_zip_bytes.replace(b"\r\n", b"\n")).hexdigest() == sha256:
                        content = raw_zip_bytes.replace(b"\r\n", b"\n")
        if content is not None and hashlib.sha256(content).hexdigest() != sha256:
            raise ValueError("CAS_REFUSAL: stored object digest mismatch")
        return content

    def save_snapshot(self, snapshot: HarvestSnapshot) -> Path:
        """Persists the snapshot manifest and returns its path."""
        target_path = self._snapshot_path(snapshot.snapshot_id)
        self._immutable_write(
            target_path, json.dumps(snapshot.to_dict(), indent=2, sort_keys=True).encode("utf-8")
        )
        return target_path

    def list_snapshots(self) -> Sequence[str]:
        """Lists all registered snapshot IDs."""
        snaps = {p.stem for p in self.snapshots_dir.glob("*.json")}
        snaps.update(p.stem for p in self.archive_snapshots_dir.glob("*.json"))
        return sorted(snaps)

    def get_snapshot(self, snapshot_id: str) -> HarvestSnapshot | None:
        """Loads a snapshot by ID."""
        raw = self._regular_bytes(self._snapshot_path(snapshot_id, archived=True))
        if raw is None:
            return None
        data = json.loads(raw.decode("utf-8"))
        records = [
            HarvestRecord(
                relative_path=r["relative_path"],
                sha256=r["sha256"],
                byte_size=r["byte_size"],
                file_type=r["file_type"],
                metadata=r.get("metadata", {}),
            )
            for r in data.get("records", [])
        ]
        rebuilt = HarvestSnapshot.create(
            snapshot_id, data["source_name"], records, data["created_at"]
        )
        if (
            data["snapshot_id"] != snapshot_id
            or data["merkle_root"] != rebuilt.merkle_root
            or data["record_count"] != len(records)
        ):
            raise ValueError("CAS_REFUSAL: snapshot binding mismatch")
        return HarvestSnapshot(
            snapshot_id=data["snapshot_id"],
            source_name=data["source_name"],
            created_at=data["created_at"],
            records=tuple(records),
            merkle_root=data["merkle_root"],
        )
