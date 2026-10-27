"""Immutable JSON/byte evidence shared by bounded PFP campaigns."""

import hashlib
import json
import os
from pathlib import Path


def canonical(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def digest(raw: bytes):
    return hashlib.sha256(raw).hexdigest()


def write_once(path: Path, value):
    raw = value if isinstance(value, bytes) else canonical(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("IMMUTABLE_EVIDENCE_CONFLICT: " + str(path))
        return
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


_INSTALL_PACKAGES = frozenset(
    {"pfp", "adversary", "education", "atlas"}
)


def _git_root(path: Path):
    resolved = path.resolve()
    for parent in (resolved, *resolved.parents):
        if (parent / ".git").exists():
            return parent
    return None


def _install_prefix(path: Path):
    resolved = path.resolve()
    for parent in (resolved, *resolved.parents):
        if parent.name in _INSTALL_PACKAGES:
            return parent.parent
    raise ValueError("PFP_PACKAGE_RESOURCES_UNAVAILABLE")


def repository_root(path: Path):
    """Checkout root, or the install prefix when this package is not in a checkout.

    The pinned relational-spacetime tasks module calls this at import. A checkout
    still wins. An installed copy resolves beside the package instead of raising.
    """
    found = _git_root(path)
    return found if found is not None else _install_prefix(path)


def resource_root(path: Path):
    """Resolve current root-relative resources in a checkout or installed wheel."""
    return repository_root(path)


def require_checkout(root: Path):
    """Historical campaign evidence and dispatch require their repository context."""
    found = _git_root(root)
    if found is None:
        raise ValueError("REPOSITORY_CONTEXT_REQUIRED")
    return found
