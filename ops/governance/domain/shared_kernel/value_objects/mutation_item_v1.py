"""Mutation Item Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .digest import Digest
from .domain_invariant_error import DomainInvariantError
from .mutation_action import MutationAction
from .path import RepoPath


@dataclass(frozen=True, slots=True, eq=False)
class MutationItemV1:
    """Decomposed single file mutation Value Object."""

    path: RepoPath
    action: MutationAction
    expected_old_blob_oid: str
    new_blob_oid: str
    content_sha256: str

    def __init__(
        self,
        *,
        path: RepoPath | str,
        action: MutationAction | str,
        expected_old_blob_oid: str = "",
        new_blob_oid: str = "",
        content_sha256: str = "",
    ) -> None:
        try:
            p = RepoPath.from_str(path)
        except DomainInvariantError as exc:
            raise DomainInvariantError("NON_CANONICAL_MUTATION_PATH", str(exc)) from exc

        act = MutationAction(action) if isinstance(action, str) else action

        if act in (MutationAction.MODIFY, MutationAction.DELETE):
            try:
                Digest.git_blob(expected_old_blob_oid)
            except DomainInvariantError as exc:
                raise DomainInvariantError("INVALID_OLD_BLOB_OID", str(exc)) from exc
        if act in (MutationAction.CREATE, MutationAction.MODIFY):
            try:
                Digest.git_blob(new_blob_oid)
            except DomainInvariantError as exc:
                raise DomainInvariantError("INVALID_NEW_BLOB_OID", str(exc)) from exc
            try:
                Digest.sha256(content_sha256)
            except DomainInvariantError as exc:
                raise DomainInvariantError("INVALID_CONTENT_SHA256", str(exc)) from exc

        object.__setattr__(self, "path", p)
        object.__setattr__(self, "action", act)
        object.__setattr__(self, "expected_old_blob_oid", expected_old_blob_oid)
        object.__setattr__(self, "new_blob_oid", new_blob_oid)
        object.__setattr__(self, "content_sha256", content_sha256)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return (
            self.path == other.path
            and self.action == other.action
            and self.expected_old_blob_oid == other.expected_old_blob_oid
            and self.new_blob_oid == other.new_blob_oid
            and self.content_sha256 == other.content_sha256
        )

    def __hash__(self) -> int:
        return hash((type(self), self.path, self.action, self.expected_old_blob_oid, self.new_blob_oid, self.content_sha256))

    def __repr__(self) -> str:
        return f"MutationItemV1(path={self.path!r}, action={self.action.value!r})"
