"""Genealogy, Cemetery, and Antibody adapters for Prompt Civilization.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.stage.infrastructure.file_lock import AdvisoryFileLock

from ..domain.models import AntibodyEntryV1, CemeteryHeadstoneV1, GenealogyEntryV1
from ..domain.ports import CemeterySink, GenealogyStorePort


def _atomic_write_json(path: Path, data: Mapping[str, Any], replace_existing: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not replace_existing and path.exists():
        return
    encoded = json.dumps(data, indent=2, sort_keys=True).encode("utf-8")
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as tf:
        tf.write(encoded)
        tf.flush()
        os.fsync(tf.fileno())
        temp_path = Path(tf.name)
    temp_path.replace(path)


def strict_json_loads(data: bytes | str) -> Any:
    return json.loads(data)


def canonical_json_bytes(data: Mapping[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")


class FileCemeteryAdapter(CemeterySink):
    """Lossless storage for dead findings and killed candidates under cemetery directory."""

    def __init__(self, cemetery_dir: str | Path | None = None) -> None:
        self.cemetery_dir = Path(cemetery_dir or "_ic/darpa/woland/cemetery")
        self.headstones: list[CemeteryHeadstoneV1] = []
        self._lock = threading.RLock()

    def record_headstone(self, headstone: CemeteryHeadstoneV1) -> Result[None, Refusal]:
        try:
            if type(headstone) is not CemeteryHeadstoneV1:
                raise TypeError("headstone must be an exact CemeteryHeadstoneV1")
            record_digest = headstone.headstone_id.removeprefix("sha256:")
            filepath = self.cemetery_dir / f"{record_digest}.headstone.json"
            with self._lock:
                _atomic_write_json(
                    filepath,
                    headstone.to_dict(),
                    replace_existing=False,
                )
                if headstone not in self.headstones:
                    self.headstones.append(headstone)
            return Ok(None)
        except (OSError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="CEMETERY_RECORD_FAILED",
                    message=f"Failed to record headstone: {exc}",
                    locus="omega_engine_prompt_civilization.infrastructure.genealogy_adapter.FileCemeteryAdapter",
                )
            )


class FileGenealogyAdapter(GenealogyStorePort):
    """Parent-to-child lineage tracking recorded in prompt_genealogy.jsonl with SHA-256 chaining, file locking, and crash recovery."""

    def __init__(self, genealogy_file: str | Path | None = None) -> None:
        if genealogy_file is not None:
            self.genealogy_file = Path(genealogy_file)
        else:
            permanent = Path("_ic/nara/permanent_records/prompt_genealogy.jsonl")
            if permanent.exists():
                self.genealogy_file = permanent
            else:
                self.genealogy_file = Path("_ic/darpa/woland/prompt_genealogy.jsonl")
        self.entries: list[GenealogyEntryV1] = []
        self._head_sha256: str | None = None
        self._next_sequence: int = 0
        self._loaded = False
        self._lock = threading.RLock()
        self._last_file_size: int = -1

    @contextmanager
    def _file_lock(self, timeout: float = 15.0):
        """Acquire the shared dependency-free advisory lock with a deadline."""
        lock_path = self.genealogy_file.with_name(f"{self.genealogy_file.name}.lock")
        with AdvisoryFileLock(lock_path, timeout=timeout):
            yield

    def _load_entries(self, force_reload: bool = False) -> None:
        current_size = self.genealogy_file.stat().st_size if self.genealogy_file.exists() else 0
        if self._loaded and not force_reload and current_size == self._last_file_size:
            return
        by_child: dict[str, GenealogyEntryV1] = {}
        entries: list[GenealogyEntryV1] = []
        head_sha256: str | None = None
        next_sequence = 0

        if self.genealogy_file.exists():
            raw_bytes = self.genealogy_file.read_bytes()
            lines = raw_bytes.splitlines(keepends=True)
            last_valid_offset = 0
            current_offset = 0
            torn_tail_detected = False

            for idx, raw_line in enumerate(lines):
                line_len = len(raw_line)
                is_last_line = (idx == len(lines) - 1)
                stripped = raw_line.strip()

                if is_last_line and not raw_line.endswith(b"\n"):
                    torn_tail_detected = True
                    break

                if not stripped:
                    if is_last_line:
                        torn_tail_detected = True
                        break
                    raise ValueError(f"blank genealogy record at line {idx + 1}")

                try:
                    payload_dict = strict_json_loads(stripped)
                except Exception:
                    if is_last_line:
                        torn_tail_detected = True
                        break
                    raise ValueError(f"unparseable genealogy record at line {idx + 1}")

                if isinstance(payload_dict, dict) and "record_sha256" in payload_dict and "sequence" in payload_dict:
                    seq = payload_dict["sequence"]
                    parent = payload_dict.get("parent_sha256")
                    sealed_digest = payload_dict["record_sha256"]
                    inner_payload = payload_dict["payload"]

                    if seq == next_sequence - 1:
                        if is_last_line:
                            torn_tail_detected = True
                            break
                        else:
                            candidate_entry = GenealogyEntryV1.from_dict(inner_payload)
                            prior = by_child.get(candidate_entry.child_run_key)
                            if prior is not None and prior == candidate_entry:
                                current_offset += line_len
                                last_valid_offset = current_offset
                                continue

                    if seq != next_sequence:
                        raise ValueError(f"genealogy sequence gap: expected {next_sequence}, got {seq}")
                    if parent != head_sha256:
                        raise ValueError(f"genealogy hash chain broken at seq {seq}")

                    material = canonical_json_bytes({
                        "sequence": seq,
                        "parent_sha256": parent,
                        "payload": inner_payload,
                    })
                    recomputed = hashlib.sha256(material).hexdigest()
                    if recomputed != sealed_digest:
                        raise ValueError(f"genealogy record digest mismatch at seq {seq}")

                    entry = GenealogyEntryV1.from_dict(inner_payload)
                    head_sha256 = sealed_digest
                    next_sequence += 1
                elif isinstance(payload_dict, dict):
                    entry = GenealogyEntryV1.from_dict(payload_dict)
                    line_digest = hashlib.sha256(stripped).hexdigest()
                    head_sha256 = line_digest
                    next_sequence += 1
                else:
                    if is_last_line:
                        torn_tail_detected = True
                        break
                    raise ValueError(f"invalid genealogy entry payload at line {idx + 1}")

                by_child[entry.child_run_key] = entry
                entries.append(entry)
                current_offset += line_len
                last_valid_offset = current_offset

            if torn_tail_detected:
                with open(self.genealogy_file, "r+b") as fh:
                    fh.seek(last_valid_offset)
                    fh.truncate()
                    fh.flush()
                    os.fsync(fh.fileno())

        self.entries = entries
        self._head_sha256 = head_sha256
        self._next_sequence = next_sequence
        self._loaded = True
        self._last_file_size = self.genealogy_file.stat().st_size if self.genealogy_file.exists() else 0

    def record_lineage(self, entry: GenealogyEntryV1) -> Result[None, Refusal]:
        try:
            if type(entry) is not GenealogyEntryV1:
                raise TypeError("entry must be an exact GenealogyEntryV1")
            with self._lock, self._file_lock():
                self._load_entries(force_reload=True)
                prior = next(
                    (e for e in self.entries if e.child_run_key == entry.child_run_key),
                    None,
                )
                if prior is not None:
                    if prior == entry:
                        return Ok(None)
                    return Err(
                        Refusal(
                            code="COLLISION_DETECTED",
                            message=f"Conflicting genealogy entry for child_run_key={entry.child_run_key}",
                            locus="omega_engine_prompt_civilization.infrastructure.genealogy_adapter.FileGenealogyAdapter",
                        )
                    )

                self.genealogy_file.parent.mkdir(parents=True, exist_ok=True)
                seq = self._next_sequence
                parent_sha256 = self._head_sha256
                inner_payload = entry.to_dict()

                material = canonical_json_bytes({
                    "sequence": seq,
                    "parent_sha256": parent_sha256,
                    "payload": inner_payload,
                })
                record_digest = hashlib.sha256(material).hexdigest()

                envelope = {
                    "sequence": seq,
                    "parent_sha256": parent_sha256,
                    "record_sha256": record_digest,
                    "payload": inner_payload,
                }
                serialized = json.dumps(envelope, separators=(",", ":"), sort_keys=True) + "\n"
                with open(self.genealogy_file, "ab") as fh:
                    fh.write(serialized.encode("utf-8"))
                    fh.flush()
                    os.fsync(fh.fileno())

                self.entries.append(entry)
                self._head_sha256 = record_digest
                self._next_sequence += 1
                self._last_file_size = self.genealogy_file.stat().st_size
            return Ok(None)
        except (OSError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="GENEALOGY_RECORD_FAILED",
                    message=f"Failed to record genealogy entry: {exc}",
                    locus="omega_engine_prompt_civilization.infrastructure.genealogy_adapter.FileGenealogyAdapter",
                )
            )

    def get_lineage(self, child_run_key: str) -> Result[GenealogyEntryV1 | None, Refusal]:
        try:
            with self._lock, self._file_lock():
                self._load_entries()
                match = next(
                    (e for e in self.entries if e.child_run_key == child_run_key),
                    None,
                )
                return Ok(match)
        except (OSError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="GENEALOGY_READ_FAILED",
                    message=f"Failed to read genealogy: {exc}",
                    locus="omega_engine_prompt_civilization.infrastructure.genealogy_adapter.FileGenealogyAdapter",
                )
            )



class FileAntibodyAdapter:
    """Immune antibody store: loads antibodies from compost history and accumulates failures."""

    def __init__(self, antibody_dir: str | Path | None = None) -> None:
        self.antibody_dir = Path(antibody_dir or "_ic/darpa/woland/antibodies")
        self.failure_counts: dict[str, int] = {}
        self.antibodies: dict[str, AntibodyEntryV1] = {}
        self._records: dict[str, AntibodyEntryV1] = {}
        self._loaded = False
        self._lock = threading.RLock()

    def _load_state(self) -> None:
        if self._loaded:
            return
        if self.antibody_dir.exists():
            for path in sorted(self.antibody_dir.glob("ab_*.json")):
                wire = strict_json_loads(path.read_bytes())
                entry = AntibodyEntryV1.from_dict(wire)
                expected_name = f"{entry.antibody_id}.json"
                if path.name != expected_name:
                    raise ValueError(
                        f"antibody filename does not match payload: {path}"
                    )
                prior = self._records.get(entry.antibody_id)
                if prior is not None and prior != entry:
                    raise ValueError(
                        f"conflicting antibody identity: {entry.antibody_id}"
                    )
                self._records[entry.antibody_id] = entry
                self.failure_counts[entry.failure_pattern] = entry.occurrences
                if entry.status == "ACTIVE":
                    self.antibodies[entry.antibody_id] = entry
        self._loaded = True

    def load_antibodies(
        self, objective: str
    ) -> Result[tuple[AntibodyEntryV1, ...], Refusal]:
        try:
            if type(objective) is not str:
                raise TypeError("objective must be an exact string")
            with self._lock:
                self._load_state()
                return Ok(
                    tuple(self.antibodies[key] for key in sorted(self.antibodies))
                )
        except (OSError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="ANTIBODY_LOAD_FAILED",
                    message=f"Failed to load antibodies: {exc}",
                    locus="omega_engine_prompt_civilization.infrastructure.genealogy_adapter.FileAntibodyAdapter",
                )
            )

    def record_failure(
        self, failure_pattern: str, constraint_rule: str
    ) -> Result[AntibodyEntryV1 | None, Refusal]:
        try:
            if (
                type(failure_pattern) is not str
                or not failure_pattern
                or failure_pattern.strip() != failure_pattern
            ):
                raise ValueError("failure_pattern must be a normalized nonempty string")
            if (
                type(constraint_rule) is not str
                or not constraint_rule
                or constraint_rule.strip() != constraint_rule
            ):
                raise ValueError("constraint_rule must be a normalized nonempty string")
            with self._lock:
                self._load_state()
                ab_id = f"ab_{hashlib.sha256(failure_pattern.encode('utf-8')).hexdigest()[:16]}"
                prior = self._records.get(ab_id)
                if prior is not None and (
                    prior.failure_pattern != failure_pattern
                    or prior.constraint_rule != constraint_rule
                ):
                    raise ValueError(
                        "antibody identity collides with different failure data"
                    )
                count = 1 if prior is None else prior.occurrences + 1
                # A sighting count never activates an antibody: activation is an
                # admission act recorded outside this store. A judged record (ACTIVE,
                # or any status other than PENDING) keeps its status when seen again.
                status = (
                    prior.status if prior is not None and prior.status != "PENDING" else "PENDING"
                )
                entry = AntibodyEntryV1(
                    antibody_id=ab_id,
                    failure_pattern=failure_pattern,
                    occurrences=count,
                    constraint_rule=constraint_rule,
                    status=status,
                )
                _atomic_write_json(
                    self.antibody_dir / f"{ab_id}.json",
                    entry.to_dict(),
                    replace_existing=True,
                )
                self._records[ab_id] = entry
                self.failure_counts[failure_pattern] = count
                if entry.status == "ACTIVE":
                    self.antibodies[ab_id] = entry
                    return Ok(entry)
                return Ok(None)
        except (OSError, TypeError, ValueError) as exc:
            return Err(
                Refusal(
                    code="ANTIBODY_RECORD_FAILED",
                    message=f"Failed to record failure pattern: {exc}",
                    locus="omega_engine_prompt_civilization.infrastructure.genealogy_adapter.FileAntibodyAdapter",
                )
            )


__all__ = [
    "FileAntibodyAdapter",
    "FileCemeteryAdapter",
    "FileGenealogyAdapter",
]
