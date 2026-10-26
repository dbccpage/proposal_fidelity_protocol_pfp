"""Capture and evaluate learning without treating the producer as an oracle."""

from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path

from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost
from omega_engine_operations.domain.rop.result import Err
from omega_engine_operads.domain.autopoiesis.learning import (
    EvidenceSource,
    LearningBlocked,
    LearningEpisodeV1,
    canonical,
)


def extract_signals(value: object) -> dict[str, tuple[str, ...]]:
    """Marshal ordered source values to the compiled signal policy."""

    def wire(item: object) -> dict:
        if isinstance(item, dict):
            return {
                "kind": "object",
                "members": [[key, wire(child)] for key, child in item.items()],
                "canonical": canonical(item).decode("utf-8"),
            }
        if isinstance(item, list):
            return {"kind": "array", "items": [wire(child) for child in item]}
        if isinstance(item, float):
            return {"kind": "number", "canonical": canonical(item).decode("utf-8")}
        return {"kind": "scalar", "value": item}

    result = RustSymbolGameHost().invoke_runtime_with_file(
        "learning_signals", {"tree": wire(value)}, file_action="learning_signals_file"
    )
    if isinstance(result, Err):
        raise ValueError(result.error.message)
    envelope = result.value
    if not envelope["success"]:
        raise ValueError(str(envelope["error"]))
    response = envelope["result"]
    if response["refusal"] is not None:
        raise ValueError(response["refusal"]["message"])
    return {key: tuple(values) for key, values in response["outcome"].items()}


def capture_episode(
    paths: tuple[Path, ...],
    host: str,
    revision: str,
    vault,
    *,
    outcome: str = "UNKNOWN",
    origin: str = "session",
) -> LearningEpisodeV1:
    if not paths:
        raise LearningBlocked("SOURCE_EVIDENCE_MISSING")
    if host not in {"woland", "codex", "claude", "antigravity", "autop"}:
        raise ValueError("unsupported source host")
    if not revision:
        raise LearningBlocked("REPOSITORY_REVISION_MISSING")
    sources = []
    signals = {"corrections": [], "successes": [], "errors": []}
    for path in paths:
        for part in (path, *path.absolute().parents):
            if part.is_symlink() or (
                part.exists() and getattr(part.lstat(), "st_file_attributes", 0) & 0x400
            ):
                raise ValueError(f"linked learning source: {path}")
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"non-regular learning source: {path}")
        raw = path.read_bytes()
        if not raw.strip():
            raise LearningBlocked("SOURCE_EVIDENCE_EMPTY")
        sha = hashlib.sha256(raw).hexdigest()
        vault.put_file(raw, sha)
        sources.append(EvidenceSource(str(path.resolve()), sha))
        text = raw.decode("utf-8")
        if path.suffix == ".json":
            value = json.loads(text)
            if not isinstance(value, (dict, list)):
                raise ValueError("receipt must be an object or array")
        elif path.suffix == ".jsonl":
            value = [json.loads(line) for line in text.splitlines() if line.strip()]
        else:
            value = {}
        if isinstance(value, dict):
            if (
                str(value.get("schema", "")).startswith("omega.autop.")
                or value.get("origin") == "autop"
            ):
                origin = "autop"
            outcome = str(value.get("terminal_verdict", value.get("status", outcome)))
        for key, values in extract_signals(value).items():
            signals[key].extend(values)
    return LearningEpisodeV1(
        host,
        revision,
        outcome,
        tuple(sources),
        **{key: tuple(dict.fromkeys(values)) for key, values in signals.items()},
        origin=origin,
    )
