"""Explicit historical Git pins or current package resources. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import re
import subprocess
from importlib import resources
from pathlib import Path, PurePosixPath

from pfp.domain.exceptions import SecurityPathViolationError
from pfp.domain.shared_kernel.path import validate_path_security


class EvidenceRefusal(ValueError):
    """A typed refusal, distinct from verified bytes."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


def _safe_path(path: str) -> PurePosixPath:
    try:
        validate_path_security(path)
    except SecurityPathViolationError as error:
        raise EvidenceRefusal("EVIDENCE_PATH_INVALID", "Expected a canonical relative resource path") from error
    # Windows also reserves device stems before extensions and intervening spaces.
    if any(re.fullmatch(
        r"(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|(?:COM|LPT)[1-9\u00b9\u00b2\u00b3])",
        part.partition(".")[0].rstrip(" "), re.IGNORECASE,
    ) for part in path.split("/")):
        raise EvidenceRefusal("EVIDENCE_PATH_INVALID", "Expected a canonical relative resource path")
    return PurePosixPath(path)


class LevelEngineEvidenceResolver:
    """v1 is recorded Git bytes; v2 is installed package data. No cross-version fallback."""

    def __init__(self, repository: Path | None = None) -> None:
        self.repository = repository.resolve() if repository is not None else None

    def read_bytes(
        self, version: str, path: str, revision: str | None = None, sha256: str | None = None
    ) -> bytes:
        relative = _safe_path(path)
        if version == "v1":
            if self.repository is None or revision is None or not re.fullmatch(r"[0-9a-f]{40}", revision):
                raise EvidenceRefusal("HISTORICAL_BYTES_UNAVAILABLE", "Historical evidence requires a repository and full recorded Git revision")
            try:
                result = subprocess.run(
                    ["git", "-C", str(self.repository), "cat-file", "blob", f"{revision}:{relative.as_posix()}"],
                    capture_output=True, check=False,
                )
            except OSError as error:
                raise EvidenceRefusal("HISTORICAL_BYTES_UNAVAILABLE", str(error)) from error
            if result.returncode != 0:
                raise EvidenceRefusal("HISTORICAL_BYTES_UNAVAILABLE", f"Recorded blob unavailable: {revision}:{path}")
            data = result.stdout
        elif version == "v2":
            if revision is not None:
                raise EvidenceRefusal("EVIDENCE_VERSION_INVALID", "v2 does not accept historical revisions")
            item = resources.files(__package__).joinpath("v2", *relative.parts)
            try:
                data = item.read_bytes()
            except OSError as error:
                raise EvidenceRefusal("ACTIVE_RESOURCE_UNAVAILABLE", path) from error
        else:
            raise EvidenceRefusal("EVIDENCE_VERSION_INVALID", f"Unsupported evidence version: {version}")
        if sha256 is not None:
            expected = sha256.removeprefix("sha256:")
            if not re.fullmatch(r"[0-9a-f]{64}", expected) or hashlib.sha256(data).hexdigest() != expected:
                raise EvidenceRefusal("EVIDENCE_DIGEST_MISMATCH", path)
        return data
