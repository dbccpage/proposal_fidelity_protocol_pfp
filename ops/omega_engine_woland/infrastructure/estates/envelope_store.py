"""File custody for sealed research evidence envelopes.

An envelope is written once to ``<runs root>/<task_id>/research_evidence_envelope.json``
under the intelligence root that the operating system resolves. Writing identical bytes
again is a no-op; different bytes for the same path are refused, so a sealed envelope is
never overwritten.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from omega_engine_woland.domain.specialization import PortName
from omega_engine_woland.domain.swarm_models import ResearchEvidenceEnvelopeV1

from .probe_support import observed, refusal, run_probe

_LOCUS = "omega_engine_woland.infrastructure.estates.envelope_store"
_TASK_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
ENVELOPE_FILE = "research_evidence_envelope.json"


def _envelope_bytes(envelope: ResearchEvidenceEnvelopeV1) -> bytes:
    return (json.dumps(envelope.to_dict(), indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_once(path: Path, data: bytes) -> Result[str, Refusal]:
    """Publish ``data`` at ``path`` exactly once.

    The bytes go to a temporary file first and are then hard-linked into place. Linking
    fails if the path exists, so two concurrent writers cannot replace each other; the
    loser compares bytes and either agrees or refuses.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temp = tempfile.mkstemp(dir=path.parent, prefix=".envelope-", suffix=".tmp")
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temp, path)
        except FileExistsError:
            raise
        except OSError:
            # No hard links on this filesystem: exclusive create is still write-once.
            with open(path, "xb") as stream:
                stream.write(data)
    except FileExistsError:
        if path.read_bytes() == data:
            return Ok(str(path))
        return Err(
            Refusal("ENVELOPE_CONFLICT", f"{path} already holds a different envelope", _LOCUS)
        )
    finally:
        os.unlink(temp)
    return Ok(str(path))


class FileEnvelopeStore:
    estate = EstateName.INTELLIGENCE_CUSTODY
    port = PortName.ENVELOPE_STORE
    adapter_id = "woland.file_envelope_store"

    def __init__(self, runs_root: Path) -> None:
        self.runs_root = Path(runs_root)

    def persist(
        self, envelope: ResearchEvidenceEnvelopeV1, output_dir: str | None = None
    ) -> Result[str, Refusal]:
        task_id = envelope.contract.task_id
        if output_dir is None and (_TASK_ID.match(task_id) is None or ".." in task_id):
            return Err(
                Refusal("ENVELOPE_TASK_ID_UNSAFE", f"task id {task_id!r} is not a path segment", _LOCUS)
            )
        directory = Path(output_dir) if output_dir is not None else self.runs_root / task_id
        try:
            return _write_once(directory / ENVELOPE_FILE, _envelope_bytes(envelope))
        except (OSError, TypeError, ValueError) as exc:
            return Err(refusal("ENVELOPE_PERSIST_FAILED", exc, _LOCUS))

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            path = Path(scratch_root) / ENVELOPE_FILE
            data = b'{"authority_effect": "None", "probe": true}\n'
            written = _write_once(path, data)
            if isinstance(written, Err):
                return disconnected(self.estate, self.port, self.adapter_id, written.error.code)
            if path.read_bytes() != data:
                return disconnected(self.estate, self.port, self.adapter_id, "bytes not read back")
            if not isinstance(_write_once(path, b"{}\n"), Err):
                return disconnected(
                    self.estate, self.port, self.adapter_id, "a sealed file was overwritten"
                )
            return observed(
                self.estate,
                self.port,
                self.adapter_id,
                path.read_bytes(),
                "wrote one file, read it back, and was refused a rewrite",
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)


__all__ = ["ENVELOPE_FILE", "FileEnvelopeStore"]
