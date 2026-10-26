"""Atomic encrypted content-addressed custody for raw OEOS artifacts.

Only canonical encrypted envelopes are written beneath the supplied root.
Plaintext exists transiently in the caller and protector and is never used as
a filename or serialized by this adapter. AuthorityEffect: None.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from collections.abc import Mapping
from typing import Final

from ..application import KeyProtectorPort, SecurityPortError
from ..domain import (
    EncryptedArtifactRefV1,
    canonical_json,
    require_identifier,
)

SCHEMA_ENCRYPTED_ENVELOPE: Final = "omega.oeos.encrypted-envelope.v1"
_MAX_ARTIFACT_BYTES: Final = 64 * 1024 * 1024
_REPARSE_ATTRIBUTE: Final = 0x400


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _is_reparse(path: Path) -> bool:
    try:
        value = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(value.st_mode) or bool(
        getattr(value, "st_file_attributes", 0) & _REPARSE_ATTRIBUTE
    )


def _canonical_envelope(value: dict[str, object]) -> bytes:
    return canonical_json(value).encode("utf-8")


class EncryptedArtifactCas:
    """Encrypt, atomically commit, and independently replay raw artifact bytes."""

    def __init__(self, root: Path, protector: KeyProtectorPort) -> None:
        if not isinstance(root, Path):
            raise SecurityPortError("INVALID_CAS_ROOT", "CAS root must be pathlib.Path")
        if getattr(protector, "fixture_only", None) not in {True, False}:
            raise SecurityPortError(
                "INVALID_KEY_PROTECTOR", "protector must expose fixture-only state"
            )
        protector_id = getattr(protector, "protector_id", None)
        require_identifier(protector_id, "protector_id")
        self._root = root.absolute()
        self._protector = protector
        self._prepare_directory(self._root)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def protector(self) -> KeyProtectorPort:
        return self._protector

    @staticmethod
    def _prepare_directory(path: Path) -> None:
        existing = path
        missing = []
        while not existing.exists():
            missing.append(existing)
            if existing.parent == existing:
                break
            existing = existing.parent
        if _is_reparse(existing):
            raise SecurityPortError(
                "CAS_REPARSE_PATH_REFUSED", "CAS path is reparse-backed"
            )
        for candidate in reversed(missing):
            candidate.mkdir()
            if _is_reparse(candidate):
                raise SecurityPortError(
                    "CAS_REPARSE_PATH_REFUSED", "CAS directory became reparse-backed"
                )
        if not path.is_dir() or _is_reparse(path):
            raise SecurityPortError(
                "INVALID_CAS_ROOT", "CAS root is not a plain directory"
            )

    def _path_for_digest(self, digest: str) -> Path:
        if (
            type(digest) is not str
            or not digest.startswith("sha256:")
            or len(digest) != 71
            or any(character not in "0123456789abcdef" for character in digest[7:])
        ):
            raise SecurityPortError(
                "INVALID_ENVELOPE_DIGEST", "digest is not canonical"
            )
        suffix = digest[7:]
        parent = self._root / suffix[:2]
        return parent / f"{suffix[2:]}.oeos-envelope"

    @staticmethod
    def _entropy(
        *,
        artifact_schema: str,
        byte_length: int,
        plaintext_sha256: str,
        protector_id: str,
    ) -> bytes:
        return canonical_json(
            {
                "artifact_schema": artifact_schema,
                "byte_length": byte_length,
                "plaintext_sha256": plaintext_sha256,
                "protector_id": protector_id,
                "schema": SCHEMA_ENCRYPTED_ENVELOPE,
            }
        ).encode("utf-8")

    @staticmethod
    def _validate_payload(payload: object) -> bytes:
        if type(payload) is not bytes:
            raise SecurityPortError("INVALID_ARTIFACT", "artifact must be exact bytes")
        if len(payload) > _MAX_ARTIFACT_BYTES:
            raise SecurityPortError(
                "ARTIFACT_TOO_LARGE", "artifact exceeds local ceiling"
            )
        return payload

    def put(self, payload: bytes, *, artifact_schema: str) -> EncryptedArtifactRefV1:
        payload = self._validate_payload(payload)
        require_identifier(artifact_schema, "artifact_schema")
        plaintext_sha256 = _sha256(payload)
        protector_id = self._protector.protector_id
        entropy = self._entropy(
            artifact_schema=artifact_schema,
            byte_length=len(payload),
            plaintext_sha256=plaintext_sha256,
            protector_id=protector_id,
        )
        protected = self._protector.protect(payload, entropy=entropy)
        if type(protected) is not bytes or not protected:
            raise SecurityPortError(
                "INVALID_PROTECTED_PAYLOAD", "protector returned no exact bytes"
            )
        envelope = _canonical_envelope(
            {
                "artifact_schema": artifact_schema,
                "authority_effect": "None",
                "byte_length": len(payload),
                "ciphertext_base64": base64.b64encode(protected).decode("ascii"),
                "plaintext_sha256": plaintext_sha256,
                "protector_id": protector_id,
                "schema": SCHEMA_ENCRYPTED_ENVELOPE,
            }
        )
        reference = EncryptedArtifactRefV1(
            plaintext_sha256=plaintext_sha256,
            encrypted_envelope_digest=_sha256(envelope),
            artifact_schema=artifact_schema,
            protector_id=protector_id,
            byte_length=len(payload),
        )
        destination = self._path_for_digest(reference.encrypted_envelope_digest)
        self._prepare_directory(destination.parent)
        if destination.exists():
            if (
                _is_reparse(destination)
                or not destination.is_file()
                or destination.read_bytes() != envelope
            ):
                raise SecurityPortError(
                    "CAS_EXISTING_OBJECT_MISMATCH", "existing envelope differs"
                )
            self.get(reference)
            return reference

        descriptor, name = tempfile.mkstemp(
            prefix=".oeos-envelope-", suffix=".tmp", dir=destination.parent
        )
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(envelope)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, destination)
            except FileExistsError:
                if (
                    _is_reparse(destination)
                    or not destination.is_file()
                    or destination.read_bytes() != envelope
                ):
                    raise SecurityPortError(
                        "CAS_EXISTING_OBJECT_MISMATCH", "racing envelope differs"
                    ) from None
            except OSError as exc:
                raise SecurityPortError(
                    "CAS_ATOMIC_COMMIT_FAILED", "unable to atomically publish envelope"
                ) from exc
            if os.name != "nt":
                directory = os.open(destination.parent, os.O_RDONLY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            self.get(reference)
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError as exc:
                raise SecurityPortError(
                    "CAS_TEMP_CLEANUP_FAILED", "owned temporary could not be removed"
                ) from exc
        return reference

    def get(self, reference: EncryptedArtifactRefV1) -> bytes:
        if type(reference) is not EncryptedArtifactRefV1:
            raise SecurityPortError(
                "INVALID_ARTIFACT_REFERENCE", "exact EncryptedArtifactRefV1 required"
            )
        path = self._path_for_digest(reference.encrypted_envelope_digest)
        if _is_reparse(path) or not path.is_file():
            raise SecurityPortError("CAS_ENVELOPE_MISSING", "envelope is unavailable")
        raw = path.read_bytes()
        if _sha256(raw) != reference.encrypted_envelope_digest:
            raise SecurityPortError(
                "CAS_ENVELOPE_DIGEST_MISMATCH", "envelope digest replay failed"
            )
        try:
            value = json.loads(raw)
        except (UnicodeDecodeError, ValueError) as exc:
            raise SecurityPortError(
                "CAS_ENVELOPE_INVALID", "envelope is not canonical JSON"
            ) from exc
        expected_fields = {
            "artifact_schema",
            "authority_effect",
            "byte_length",
            "ciphertext_base64",
            "plaintext_sha256",
            "protector_id",
            "schema",
        }
        if (
            type(value) is not dict
            or set(value) != expected_fields
            or _canonical_envelope(value) != raw
            or value["schema"] != SCHEMA_ENCRYPTED_ENVELOPE
            or value["authority_effect"] != "None"
            or value["artifact_schema"] != reference.artifact_schema
            or value["byte_length"] != reference.byte_length
            or value["plaintext_sha256"] != reference.plaintext_sha256
            or value["protector_id"] != reference.protector_id
            or reference.protector_id != self._protector.protector_id
        ):
            raise SecurityPortError(
                "CAS_ENVELOPE_METADATA_MISMATCH", "envelope metadata differs"
            )
        encoded = value["ciphertext_base64"]
        if type(encoded) is not str:
            raise SecurityPortError(
                "CAS_ENVELOPE_INVALID", "ciphertext representation differs"
            )
        try:
            protected = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise SecurityPortError(
                "CAS_ENVELOPE_INVALID", "ciphertext representation is invalid"
            ) from exc
        if base64.b64encode(protected).decode("ascii") != encoded:
            raise SecurityPortError(
                "CAS_ENVELOPE_INVALID", "ciphertext representation is non-canonical"
            )
        entropy = self._entropy(
            artifact_schema=reference.artifact_schema,
            byte_length=reference.byte_length,
            plaintext_sha256=reference.plaintext_sha256,
            protector_id=reference.protector_id,
        )
        plaintext = self._protector.unprotect(protected, entropy=entropy)
        if type(plaintext) is not bytes:
            raise SecurityPortError(
                "INVALID_UNPROTECTED_PAYLOAD", "protector returned a different type"
            )
        if len(plaintext) != reference.byte_length:
            raise SecurityPortError(
                "ARTIFACT_LENGTH_MISMATCH", "plaintext length replay failed"
            )
        if _sha256(plaintext) != reference.plaintext_sha256:
            raise SecurityPortError(
                "ARTIFACT_DIGEST_MISMATCH", "plaintext digest replay failed"
            )
        return plaintext

    def get_canonical(self, value: Mapping[str, object]) -> bytes:
        """Replay a wire reference through the exact OEOS contract and protector."""

        if type(value) is not dict:
            raise SecurityPortError(
                "INVALID_ARTIFACT_REFERENCE", "canonical reference must be a dict"
            )
        return self.get(EncryptedArtifactRefV1.from_canonical(value))

    def object_path(self, reference: EncryptedArtifactRefV1) -> Path:
        if type(reference) is not EncryptedArtifactRefV1:
            raise SecurityPortError(
                "INVALID_ARTIFACT_REFERENCE", "exact EncryptedArtifactRefV1 required"
            )
        return self._path_for_digest(reference.encrypted_envelope_digest)

    def diagnostic(self) -> dict[str, object]:
        return {
            "encrypted_only": True,
            "fixture_only": self._protector.fixture_only,
            "protector_id": self._protector.protector_id,
            "status": "HEALTHY",
        }


__all__ = ["EncryptedArtifactCas", "SCHEMA_ENCRYPTED_ENVELOPE"]
