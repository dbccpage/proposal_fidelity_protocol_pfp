"""Run folders for the research loop: ``<root>/_ic/darpa/research/runs/<run_id>/``.

* ``mission.json`` is written once.
* ``state.json`` holds the controller checkpoint. A save names the state it replaces;
  a save over any other state is refused, so two writers cannot interleave.
* ``events.jsonl`` mirrors the checkpoint's event tape, appended in sequence order.
* ``rounds/<r>/raw/`` holds raw responses, each written once before it is parsed.
* ``execution_occurrences.jsonl`` and ``receipts.jsonl`` are append-only.
* The final bundle (``summary.json``, ``receipt.json``, ``adapter_loss_ledger.jsonl``) is
  written once when the run ends.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import intelligence_path
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.researcher.models import LoopSnapshotV1

_LOCUS = "omega_engine_woland.infrastructure.researcher.run_custody_store"
_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._-]{0,199}\Z")
_LEDGERS = frozenset({"execution_occurrences.jsonl", "receipts.jsonl"})
_BUNDLE = frozenset({"summary.json", "receipt.json", "adapter_loss_ledger.jsonl"})


def _refuse(code: str, message: str) -> Err[Refusal]:
    return Err(Refusal(code, message, _LOCUS))


def _json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode(
        "utf-8"
    )


def _write_once(path: Path, data: bytes) -> Result[str, Refusal]:
    """Create ``path`` with ``data``; the same bytes again are accepted, other bytes refused."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "xb") as stream:
            stream.write(data)
    except FileExistsError:
        if path.read_bytes() == data:
            return Ok(str(path))
        return _refuse("RUN_FILE_CONFLICT", f"{path} already holds different bytes")
    except OSError as exc:
        return _refuse("RUN_FILE_UNWRITABLE", f"{path}: {exc}")
    return Ok(str(path))


class FileRunCustody:
    def __init__(self, root: Path) -> None:
        # Absolute, so the raw directory handed to the native transport is absolute too.
        self.runs = intelligence_path(Path(root).absolute(), "_intelligence/research/runs")

    def _run(self, run_id: str) -> Path:
        if _NAME.fullmatch(run_id) is None:
            raise ValueError(f"run id {run_id!r} is not a safe folder name")
        return self.runs / run_id

    def create(
        self, run_id: str, mission: Mapping[str, Any], snapshot: LoopSnapshotV1
    ) -> Result[str, Refusal]:
        try:
            folder = self._run(run_id)
        except ValueError as exc:
            return _refuse("RUN_ID_INVALID", str(exc))
        if (folder / "state.json").exists():
            return _refuse("RUN_EXISTS", f"{folder} already holds a run")
        written = _write_once(folder / "mission.json", _json(dict(mission)))
        if isinstance(written, Err):
            return written
        state = _write_once(folder / "state.json", _json({"checkpoint": snapshot.checkpoint}))
        if isinstance(state, Err):
            return state
        mirrored = self._mirror_events(folder, snapshot)
        if isinstance(mirrored, Err):
            return mirrored
        return Ok(str(folder))

    def load(self, run_id: str) -> Result[Mapping[str, Any], Refusal]:
        try:
            path = self._run(run_id) / "state.json"
            return Ok(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            return _refuse("RUN_STATE_UNREADABLE", str(exc))

    def save(
        self, run_id: str, expected_state_sha256: str, snapshot: LoopSnapshotV1
    ) -> Result[str, Refusal]:
        try:
            folder = self._run(run_id)
        except ValueError as exc:
            return _refuse("RUN_ID_INVALID", str(exc))
        lock = folder / "state.lock"
        try:
            with open(lock, "x", encoding="utf-8"):
                pass
        except FileExistsError:
            return _refuse("RUN_STATE_LOCKED", f"{lock} exists: another writer holds this run")
        except OSError as exc:
            return _refuse("RUN_STATE_UNWRITABLE", str(exc))
        try:
            current = self.load(run_id)
            if isinstance(current, Err):
                return current
            if current.value["checkpoint"]["state_sha256"] != expected_state_sha256:
                return _refuse(
                    "RUN_STATE_CONFLICT", "the stored state is not the one this save replaces"
                )
            temp = folder / f"state.{os.getpid()}.tmp"
            temp.write_bytes(_json({"checkpoint": snapshot.checkpoint}))
            os.replace(temp, folder / "state.json")
            return self._mirror_events(folder, snapshot)
        except OSError as exc:
            return _refuse("RUN_STATE_UNWRITABLE", str(exc))
        finally:
            lock.unlink(missing_ok=True)

    def _mirror_events(self, folder: Path, snapshot: LoopSnapshotV1) -> Result[str, Refusal]:
        events = snapshot.checkpoint["state"]["events"]
        path = folder / "events.jsonl"
        try:
            have = path.read_text(encoding="utf-8").count("\n") if path.exists() else 0
            if have > len(events):
                return _refuse(
                    "RUN_EVENTS_DIVERGED", "events.jsonl holds more events than the state"
                )
            with open(path, "ab") as stream:
                for event in events[have:]:
                    stream.write(_json(event))
        except OSError as exc:
            return _refuse("RUN_EVENTS_UNWRITABLE", str(exc))
        return Ok(str(path))

    def raw_dir(self, run_id: str, round_id: int) -> str:
        return str(self._run(run_id) / "rounds" / str(round_id) / "raw")

    def write_raw(
        self, run_id: str, round_id: int, occurrence_id: str, raw: bytes
    ) -> Result[str, Refusal]:
        if _NAME.fullmatch(occurrence_id) is None:
            return _refuse("OCCURRENCE_ID_INVALID", f"{occurrence_id!r} is not a safe file name")
        return _write_once(Path(self.raw_dir(run_id, round_id)) / f"{occurrence_id}.txt", raw)

    def append(self, run_id: str, ledger: str, record: Mapping[str, Any]) -> Result[None, Refusal]:
        if ledger not in _LEDGERS:
            return _refuse("RUN_LEDGER_UNKNOWN", f"{ledger} is not an append-only ledger")
        try:
            with open(self._run(run_id) / ledger, "ab") as stream:
                stream.write(_json(dict(record)))
        except (OSError, ValueError) as exc:
            return _refuse("RUN_LEDGER_UNWRITABLE", str(exc))
        return Ok(None)

    def write_bundle(
        self, run_id: str, files: Mapping[str, Any]
    ) -> Result[tuple[str, ...], Refusal]:
        written = []
        for name, value in files.items():
            if name not in _BUNDLE:
                return _refuse("RUN_BUNDLE_UNKNOWN", f"{name} is not a bundle file")
            data = (
                b"".join(_json(row) for row in value) if name.endswith(".jsonl") else _json(value)
            )
            done = _write_once(self._run(run_id) / name, data)
            if isinstance(done, Err):
                return done
            written.append(done.value)
        return Ok(tuple(written))


__all__ = ["FileRunCustody"]
