"""Append-only observation and regrading records. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..domain.pilots import checker_registry, fail_closed_gate


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def checker_revision() -> str:
    return digest(b"".join(Path(module.__file__).read_bytes()
                           for module in (checker_registry, fail_closed_gate)))


def input_binding(pilot_dir: Path, request: dict[str, Any]) -> dict[str, str]:
    binding = {name: digest((pilot_dir / name).read_bytes())
               for name in ("spec.yaml", "seed.yaml", "p_star.yaml")}
    template = pilot_dir / "prompt_template.yaml"
    if template.is_file():
        binding["prompt_template.yaml"] = digest(template.read_bytes())
    binding["request_sha256"] = digest(canonical_bytes(request))
    binding["checker_revision"] = checker_revision()
    return binding


def write_once(path: Path, value: dict[str, Any]) -> Path:
    raw = canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(raw)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError(f"IMMUTABLE_ARTIFACT_CONFLICT: {path.name}") from None
    return path


def record_evaluation(
    pilot_dir: Path, observation: bytes, expected: Any, checker_id: str,
    received: Any, status: str, *, observation_mode: str,
    binding: dict[str, str] | None = None,
) -> Path:
    record = {
        "schema": "pfp.pilot-evaluation.v2", "authority_effect": "None",
        "observation_sha256": digest(observation), "checker_id": checker_id,
        "checker_version": checker_registry.CHECKER_VERSION,
        "checker_revision": checker_revision(), "expected": expected,
        "received": received, "status": status, "observation_mode": observation_mode,
        "spec_sha256": digest((pilot_dir / "spec.yaml").read_bytes()),
        "seed_sha256": digest((pilot_dir / "seed.yaml").read_bytes()),
        "input_binding": binding,
        "efficacy_eligible": False,
        "eligibility_reason": "P0_REGRADING_ONLY_NO_CLEAN_CAMPAIGN_PROVENANCE",
    }
    identity = digest(canonical_bytes(record))
    return write_once(pilot_dir / "evaluations" / f"{identity}.json", record)
