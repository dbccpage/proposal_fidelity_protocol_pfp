"""Content-addressed, thread/process-safe execution trace recording.

The ledger is diagnostic observation only. Recording an event does not certify
the skill, authorize a transition, establish semantic contraction, prove
equivalence, or support promotion.

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

TRACE_SCHEMA = "omega.operad.execution_trace.v1"
_THREAD_LOCK = threading.Lock()


class TraceLedgerError(RuntimeError):
    """Typed boundary failure for malformed or unavailable trace storage."""


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _entry_payload(
    skill_id: str,
    run_id: str,
    phi_before: float,
    phi_after: float,
) -> dict[str, Any]:
    if not isinstance(skill_id, str) or not skill_id.strip():
        raise TraceLedgerError("skill_id must be a non-empty string")
    if not isinstance(run_id, str) or not run_id.strip():
        raise TraceLedgerError("run_id must be a non-empty string")
    before = float(phi_before)
    after = float(phi_after)
    if not math.isfinite(before) or not math.isfinite(after):
        raise TraceLedgerError("phi values must be finite")
    if before < 0.0 or after < 0.0:
        raise TraceLedgerError("phi values must be non-negative")
    return {
        "schema": TRACE_SCHEMA,
        "skill_id": skill_id.strip(),
        "run_id": run_id.strip(),
        "phi_before": before,
        "phi_after": after,
        "authority_effect": "None",
    }


@contextmanager
def _exclusive_lock(lock_path: Path, timeout_seconds: float) -> Iterator[None]:
    """Acquire a cross-process lock by atomically creating one lock file."""

    deadline = time.monotonic() + timeout_seconds
    descriptor: int | None = None
    while descriptor is None:
        try:
            descriptor = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o600,
            )
            os.write(descriptor, str(os.getpid()).encode("ascii"))
            os.fsync(descriptor)
        except (FileExistsError, PermissionError):
            if time.monotonic() >= deadline:
                raise TraceLedgerError(
                    f"timed out acquiring trace lock {lock_path}"
                )
            time.sleep(0.01)
    try:
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            lock_path.unlink(missing_ok=True)
        except PermissionError as exc:
            # On Windows, lock file might still be held briefly by another process
            _cleanup_err = str(exc)


def _load_records(trace_path: Path) -> list[dict[str, Any]]:
    if not trace_path.exists():
        return []
    try:
        value = json.loads(trace_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise TraceLedgerError(f"cannot replay trace ledger {trace_path}: {exc}") from exc
    if not isinstance(value, list) or any(type(row) is not dict for row in value):
        raise TraceLedgerError("trace ledger must be a JSON array of exact objects")
    return value


def record_execution(
    skill_id: str,
    run_id: str,
    phi_before: float,
    phi_after: float,
    *,
    trace_path: str | os.PathLike[str] | None = None,
    timeout_seconds: float = 30.0,
    verbose: bool = False,
) -> dict[str, Any]:
    """Append one idempotent event and return the stored event.

    ``entry_id`` binds the semantic payload but deliberately excludes the wall
    clock. ``observed_at`` records custody time without making replay IDs vary.
    The same payload is idempotent; conflicting data never replaces old data.
    """

    payload = _entry_payload(skill_id, run_id, phi_before, phi_after)
    entry_id = "sha256:" + hashlib.sha256(_canonical_bytes(payload)).hexdigest()
    event = {
        **payload,
        "entry_id": entry_id,
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "classification": "RecordedResidualObservation",
        "claim_effect": "None",
    }
    destination = (
        Path(trace_path).resolve()
        if trace_path is not None
        else Path(__file__).resolve().with_name("evidence_trace.json")
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock_path = destination.with_name(destination.name + ".lock")

    with _THREAD_LOCK:
        with _exclusive_lock(lock_path, timeout_seconds):
            records = _load_records(destination)
            existing = [row for row in records if row.get("entry_id") == entry_id]
            if existing:
                if len(existing) != 1:
                    raise TraceLedgerError(f"duplicate entry_id already present: {entry_id}")
                stored_payload = {
                    key: existing[0].get(key)
                    for key in payload
                }
                if stored_payload != payload:
                    raise TraceLedgerError(f"entry_id collision for {entry_id}")
                return existing[0]

            conflicting_run = [
                row
                for row in records
                if row.get("skill_id") == payload["skill_id"]
                and row.get("run_id") == payload["run_id"]
            ]
            if conflicting_run:
                raise TraceLedgerError(
                    f"run_id {payload['run_id']!r} already binds different evidence "
                    f"for skill {payload['skill_id']!r}"
                )

            records.append(event)
            temporary = destination.with_name(
                f".{destination.name}.{os.getpid()}.{threading.get_ident()}."
                f"{uuid.uuid4().hex}.tmp"
            )
            try:
                with temporary.open("x", encoding="utf-8", newline="\n") as stream:
                    json.dump(records, stream, indent=2, ensure_ascii=False, allow_nan=False)
                    stream.write("\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                for retry in range(50):
                    try:
                        os.replace(temporary, destination)
                        break
                    except PermissionError:
                        if retry == 49:
                            raise
                        time.sleep(0.002)
            finally:
                if temporary.exists():
                    temporary.unlink()

    if verbose:
        print(
            f"[RECORDED_NOT_CERTIFIED] '{payload['skill_id']}' "
            f"run='{payload['run_id']}' delta={payload['phi_after'] - payload['phi_before']:.4f}"
        )
    return event


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 4:
        print("Usage: python record_trace.py <skill_id> <run_id> <phi_before> <phi_after>")
        return 2
    try:
        record_execution(args[0], args[1], float(args[2]), float(args[3]), verbose=True)
    except (TraceLedgerError, ValueError) as exc:
        print(f"[REFUSED] {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
