"""Shared Kernel Value Objects.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    GitBlobOid = Digest
    GitTreeOid = Digest
    GitCommitOid = Digest
    GitOid = Digest
    ManifestDigest = Digest
    SignatureDigest = Digest
    PolicyDigest = Digest
    Sha256Digest = Digest
    Nonce = Identifier
    OneUseToken = Identifier
    PublicKeyRef = Identifier
    RepoWorktreeId = Identifier
    EventId = Identifier
    ReceiptId = Identifier
    PrincipalId = Identifier
    OwnerId = Identifier
    LeaseId = Identifier
    PacketId = Identifier
    EvidenceId = Identifier
    ProposalId = Identifier
    ProblemId = Identifier
    CandidateId = Identifier
    DecisionId = Identifier
    from .digest import Digest
    from .digest_kind import DigestKind
    from .domain_invariant_error import DomainInvariantError
    from .epoch import Epoch
    from .fence_token import FenceToken
    from .id_kind import IdKind
    from .identifier import Identifier
    from .mutation_action import MutationAction
    from .mutation_item_v1 import MutationItemV1
    from .mutation_manifest_v1 import MutationManifestV1, compute_manifest_sha256
    from .path import RepoPath, RepositoryPath
    from .sequence_number import SequenceNumber
    from .temporal import TimestampUtc, UtcTimestamp
























__all__ = ['DomainInvariantError', 'IdKind', 'Identifier', 'DigestKind', 'Digest', 'RepoPath', 'RepositoryPath', 'UtcTimestamp', 'TimestampUtc', 'FenceToken', 'Epoch', 'SequenceNumber', 'MutationAction', 'MutationItemV1', 'MutationManifestV1', 'compute_manifest_sha256', 'DecisionId', 'CandidateId', 'ProblemId', 'ProposalId', 'EvidenceId', 'PacketId', 'LeaseId', 'OwnerId', 'PrincipalId', 'ReceiptId', 'EventId', 'RepoWorktreeId', 'PublicKeyRef', 'OneUseToken', 'Nonce', 'Sha256Digest', 'PolicyDigest', 'SignatureDigest', 'ManifestDigest', 'GitOid', 'GitCommitOid', 'GitTreeOid', 'GitBlobOid']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'GitBlobOid': ('.digest', 'Digest'),
    'GitTreeOid': ('.digest', 'Digest'),
    'GitCommitOid': ('.digest', 'Digest'),
    'GitOid': ('.digest', 'Digest'),
    'ManifestDigest': ('.digest', 'Digest'),
    'SignatureDigest': ('.digest', 'Digest'),
    'PolicyDigest': ('.digest', 'Digest'),
    'Sha256Digest': ('.digest', 'Digest'),
    'Nonce': ('.identifier', 'Identifier'),
    'OneUseToken': ('.identifier', 'Identifier'),
    'PublicKeyRef': ('.identifier', 'Identifier'),
    'RepoWorktreeId': ('.identifier', 'Identifier'),
    'EventId': ('.identifier', 'Identifier'),
    'ReceiptId': ('.identifier', 'Identifier'),
    'PrincipalId': ('.identifier', 'Identifier'),
    'OwnerId': ('.identifier', 'Identifier'),
    'LeaseId': ('.identifier', 'Identifier'),
    'PacketId': ('.identifier', 'Identifier'),
    'EvidenceId': ('.identifier', 'Identifier'),
    'ProposalId': ('.identifier', 'Identifier'),
    'ProblemId': ('.identifier', 'Identifier'),
    'CandidateId': ('.identifier', 'Identifier'),
    'DecisionId': ('.identifier', 'Identifier'),
    'Digest': ('.digest', 'Digest'),
    'DigestKind': ('.digest_kind', 'DigestKind'),
    'DomainInvariantError': ('.domain_invariant_error', 'DomainInvariantError'),
    'Epoch': ('.epoch', 'Epoch'),
    'FenceToken': ('.fence_token', 'FenceToken'),
    'IdKind': ('.id_kind', 'IdKind'),
    'Identifier': ('.identifier', 'Identifier'),
    'MutationAction': ('.mutation_action', 'MutationAction'),
    'MutationItemV1': ('.mutation_item_v1', 'MutationItemV1'),
    'MutationManifestV1': ('.mutation_manifest_v1', 'MutationManifestV1'),
    'compute_manifest_sha256': ('.mutation_manifest_v1', 'compute_manifest_sha256'),
    'RepoPath': ('.path', 'RepoPath'),
    'RepositoryPath': ('.path', 'RepositoryPath'),
    'SequenceNumber': ('.sequence_number', 'SequenceNumber'),
    'TimestampUtc': ('.temporal', 'TimestampUtc'),
    'UtcTimestamp': ('.temporal', 'UtcTimestamp'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
