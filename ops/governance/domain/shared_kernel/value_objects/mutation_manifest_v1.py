"""Mutation Manifest Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Sequence

from .domain_invariant_error import DomainInvariantError
from .mutation_item_v1 import MutationItemV1


def compute_manifest_sha256(items: Sequence[MutationItemV1]) -> str:
    hasher = hashlib.sha256()
    for item in sorted(items, key=lambda x: str(x.path)):
        hasher.update(str(item.path).encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(item.action.value.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(item.expected_old_blob_oid.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(item.new_blob_oid.encode("utf-8"))
        hasher.update(b"\0")
        hasher.update(item.content_sha256.encode("utf-8"))
        hasher.update(b"\0")
    return hasher.hexdigest()


@dataclass(frozen=True, slots=True, eq=False)
class MutationManifestV1:
    """Canonical collection of exact file mutations."""

    items: tuple[MutationItemV1, ...]
    manifest_sha256: str

    def __init__(
        self,
        items: tuple[MutationItemV1, ...] | list[MutationItemV1],
        manifest_sha256: str | None = None,
    ) -> None:
        items_tuple = tuple(items)
        if not items_tuple:
            raise DomainInvariantError("EMPTY_MUTATION_MANIFEST", "Manifest must contain at least one item")
        paths = [item.path.value for item in items_tuple]
        if len(paths) != len(set(paths)):
            raise DomainInvariantError("DUPLICATE_MUTATION_PATHS", f"Duplicate paths found: {paths}")

        computed = compute_manifest_sha256(items_tuple)
        if manifest_sha256 is not None and manifest_sha256 != computed:
            raise DomainInvariantError(
                "MANIFEST_SHA256_MISMATCH",
                f"expected {computed} got {manifest_sha256}",
            )

        object.__setattr__(self, "items", items_tuple)
        object.__setattr__(self, "manifest_sha256", computed)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.items == other.items and self.manifest_sha256 == other.manifest_sha256

    def __hash__(self) -> int:
        return hash((type(self), self.items, self.manifest_sha256))

    def __repr__(self) -> str:
        return f"MutationManifestV1(items={len(self.items)}, sha={self.manifest_sha256[:8]}...)"
