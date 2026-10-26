"""Code-change packet type.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .code_change_wire import (
    Any,
    CODE_CHANGE_PATCH_SCHEMA,
    MAX_PATCH_BYTES,
    Mapping,
    PATCH_DOMAIN,
    PATCH_ENCODINGS,
    _fail,
    _path_tuple_from_wire,
    _require_digest,
    _require_exact_dict,
    _require_fields,
    _require_nonnegative_int,
    _require_revision,
    _require_stable_id,
    _require_string,
    _validate_path_tuple,
    domain_digest,
    field,
)


@dataclass(frozen=True, slots=True)
class CodeChangePatchArtifactV1:
    """Immutable content-addressed patch binding for one candidate."""

    packet_id: str
    producer_id: str
    base_source_revision: str
    patch_encoding: str
    patch_sha256: str
    patch_byte_count: int
    touched_paths: tuple[str, ...]
    claimed_summary: str | None = None
    schema_version: str = field(default=CODE_CHANGE_PATCH_SCHEMA)
    authority_effect: str = field(default="None")
    explicit_task_id: str | None = None
    explicit_payload: Any = None

    def __post_init__(self) -> None:
        _require_digest(self.packet_id, "packet_id")
        _require_stable_id(self.producer_id, "producer_id")
        _require_revision(self.base_source_revision, "base_source_revision")
        _require_string(self.patch_encoding, "patch_encoding", nonempty=True)
        if self.patch_encoding not in PATCH_ENCODINGS:
            _fail("patch_encoding is unsupported")
        _require_digest(self.patch_sha256, "patch_sha256")
        _require_nonnegative_int(self.patch_byte_count, "patch_byte_count")
        if self.patch_byte_count > MAX_PATCH_BYTES:
            _fail("patch_byte_count exceeds the patch resource limit")
        paths = _validate_path_tuple(self.touched_paths, "touched_paths")
        if not paths:
            _fail("touched_paths must be nonempty")
        object.__setattr__(self, "touched_paths", paths)
        if self.claimed_summary is not None:
            _require_string(self.claimed_summary, "claimed_summary")
        if self.schema_version != CODE_CHANGE_PATCH_SCHEMA:
            _fail("code-change patch schema version is unsupported")
        if self.authority_effect != "None":
            _fail("code-change patches must carry AuthorityEffect None")

    def identity_fields(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "producer_id": self.producer_id,
            "base_source_revision": self.base_source_revision,
            "patch_encoding": self.patch_encoding,
            "patch_sha256": self.patch_sha256,
            "patch_byte_count": self.patch_byte_count,
            "touched_paths": list(self.touched_paths),
            "claimed_summary": self.claimed_summary,
            "authority_effect": self.authority_effect,
        }

    @property
    def patch_id(self) -> str:
        return domain_digest(PATCH_DOMAIN, self.identity_fields())

    def to_dict(self) -> dict[str, Any]:
        return {
            "patch_id": self.patch_id,
            **self.identity_fields(),
        }

    @classmethod
    def from_dict(cls, wire: Mapping[str, Any]) -> "CodeChangePatchArtifactV1":
        wire = _require_exact_dict(wire, "code-change patch artifact")
        _require_fields(
            wire,
            frozenset(
                {
                    "schema_version",
                    "patch_id",
                    "packet_id",
                    "producer_id",
                    "base_source_revision",
                    "patch_encoding",
                    "patch_sha256",
                    "patch_byte_count",
                    "touched_paths",
                    "claimed_summary",
                    "authority_effect",
                }
            ),
            "code-change patch artifact",
        )
        expected_patch_id = _require_digest(wire["patch_id"], "patch_id")
        artifact = cls(
            packet_id=_require_digest(wire["packet_id"], "packet_id"),
            producer_id=_require_stable_id(wire["producer_id"], "producer_id"),
            base_source_revision=_require_revision(
                wire["base_source_revision"], "base_source_revision"
            ),
            patch_encoding=_require_string(
                wire["patch_encoding"], "patch_encoding", nonempty=True
            ),
            patch_sha256=_require_digest(wire["patch_sha256"], "patch_sha256"),
            patch_byte_count=_require_nonnegative_int(
                wire["patch_byte_count"], "patch_byte_count"
            ),
            touched_paths=_path_tuple_from_wire(
                wire["touched_paths"], "touched_paths"
            ),
            claimed_summary=(
                None
                if wire["claimed_summary"] is None
                else _require_string(wire["claimed_summary"], "claimed_summary")
            ),
            schema_version=_require_string(
                wire["schema_version"], "schema_version", nonempty=True
            ),
            authority_effect=_require_string(
                wire["authority_effect"], "authority_effect", nonempty=True
            ),
        )
        if expected_patch_id != artifact.patch_id:
            _fail("patch_id does not match canonical wire content")
        return artifact
