"""Git Object Address Parsing Functions.

AuthorityEffect: None.
"""

from __future__ import annotations

from .blob_read_request import BlobReadRequest
from .unsafe_git_address import UnsafeGitAddress


def parse_blob_spec(spec: str) -> BlobReadRequest:
    """Parse a blob spec string. Rejects colon-separated revision:path strings."""
    s = str(spec).strip()
    if ":" in s:
        raise UnsafeGitAddress("Rev path string in parse_blob_spec is refused", residual="UNSAFE_REV_PATH_ARGV")
    raise UnsafeGitAddress(f"Invalid blob spec: {spec!r}", residual="UNSAFE_REV_PATH_ARGV")


def safe_blob_read(revision: str, path: str) -> BlobReadRequest:
    """Construct a safe BlobReadRequest from separate revision and path."""
    rev_str = str(revision).strip()
    path_str = str(path).strip()
    if ":" in rev_str or ":" in path_str:
        raise UnsafeGitAddress("Colon in revision or path is unsafe", residual="UNSAFE_REV_PATH_ARGV")
    return BlobReadRequest(revision=rev_str, path=path_str)
