"""Digest Kind Enumeration.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class DigestKind(str, Enum):
    """Domain taxonomy discriminating cryptographic digest types."""

    SHA256 = "SHA256"
    POLICY = "POLICY"
    SIGNATURE = "SIGNATURE"
    MANIFEST = "MANIFEST"
    GIT_OID = "GIT_OID"
    GIT_COMMIT = "GIT_COMMIT"
    GIT_TREE = "GIT_TREE"
    GIT_BLOB = "GIT_BLOB"
    BLAKE3 = "BLAKE3"
    IDENTITY_REF = "IDENTITY_REF"
    IDENTITY_LINKS = "IDENTITY_LINKS"
    MERKLE_ROOT = "MERKLE_ROOT"
    PACKET_PAYLOAD = "PACKET_PAYLOAD"
    AST_HASH = "AST_HASH"
