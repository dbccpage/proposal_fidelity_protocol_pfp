"""The stage table pin and per-row digests (document 07 section 1).

AuthorityEffect: None.

MSS-N is row N of ``research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/stages.tsv`` at commit
``e28f49ab``. A row is identified by the SHA-256 of its bytes in the table,
excluding the LF that terminates it. The registry names levels by integer and
digest only; it copies no text from the table.

Stage data is read through the existing interface in ``registry.py``
(``load_stages`` and ``STAGES_FILE``). This module does not compute or read
any stage status.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import canonical_bytes, digest, sha256_hex

from pfp.domain.tower import registry as _registry
from importlib.resources import files

TABLE_PATH = "research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/stages.tsv"
TABLE_PIN_COMMIT = "e28f49abea3310ae4a9dc3d17ecb9ab55b267938"
TABLE_SHA256_HEX = "3cdcabe424ac12a11d70db3dfd697239f8a6f93b98f059cacf511553e14698e7"
REGISTRY_VERSION = 1
LEVELS = tuple(range(101))
ROW_DIGEST_RULE = "sha256 of the row's bytes in the table, excluding its LF terminator"


class StageRegistryError(ValueError):
    pass


def table_bytes() -> bytes:
    """The table's bytes through the existing interface, checked against the pin."""
    data = files(__package__).joinpath("data/stages.tsv").read_bytes()
    if sha256_hex(data) != TABLE_SHA256_HEX:
        raise StageRegistryError(
            f"stage table digest {sha256_hex(data)} differs from the pin {TABLE_SHA256_HEX}; "
            "a changed table is a new registry version"
        )
    return data


def row_digests(data: bytes) -> dict[int, str]:
    if b"\r" in data:
        raise StageRegistryError("the stage table must be LF-only")
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines = lines[:-1]
    body = lines[1:]
    if len(body) != len(LEVELS):
        raise StageRegistryError(f"expected {len(LEVELS)} rows, found {len(body)}")
    out: dict[int, str] = {}
    for level, row in zip(LEVELS, body):
        if not row.startswith(f"{level}|".encode("ascii")):
            raise StageRegistryError(f"row {level} does not start with its level")
        out[level] = digest(row)
    return out


def build() -> dict[str, Any]:
    data = table_bytes()
    stages = _registry.STAGES
    if tuple(stage.level for stage in stages) != LEVELS:
        raise StageRegistryError("the existing interface does not return levels 0..100")
    digests = row_digests(data)
    return {
        "authority_effect": "None",
        "levels": [{"level": level, "row_sha256": digests[level]} for level in LEVELS],
        "registry_version": REGISTRY_VERSION,
        "row_digest_rule": ROW_DIGEST_RULE,
        "schema": "mssn.stage-registry.v1",
        "table": {
            "path": TABLE_PATH,
            "pin_commit": TABLE_PIN_COMMIT,
            "sha256": "sha256:" + TABLE_SHA256_HEX,
        },
    }


def build_bytes() -> bytes:
    return canonical_bytes(build())


def level_texts() -> dict[int, tuple[str, ...]]:
    """Per level, the strings a blind derivation must not contain (K13 a).

    Used only for the leak scan; never written into any record.
    """
    out: dict[int, tuple[str, ...]] = {}
    for stage in _registry.STAGES:
        words = [stage.title, stage.obligation, stage.counterexample]
        for capability in (stage.capability_a, stage.capability_b):
            words.append(capability)
            words.append(capability.replace("_", " "))
        out[stage.level] = tuple(word for word in words if word)
    return out
