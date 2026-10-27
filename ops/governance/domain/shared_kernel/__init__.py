from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .commands import Command, CommandStatus, CommandVerdict
    from .entities import AggregateRoot, Entity
    from .events import DomainEvent, EventRecorder, EventStream
    from .result import Err, Ok, Result
    from .value_objects import Digest, DigestKind, DomainInvariantError, Epoch, FenceToken, IdKind, Identifier, MutationAction, MutationItemV1, MutationManifestV1, RepoPath, RepositoryPath, SequenceNumber, TimestampUtc, UtcTimestamp

__all__ = ['AggregateRoot', 'Command', 'CommandStatus', 'CommandVerdict', 'Digest', 'DigestKind', 'DomainEvent', 'DomainInvariantError', 'Entity', 'Epoch', 'Err', 'EventRecorder', 'EventStream', 'FenceToken', 'IdKind', 'Identifier', 'MutationAction', 'MutationItemV1', 'MutationManifestV1', 'Ok', 'RepoPath', 'RepositoryPath', 'Result', 'SequenceNumber', 'TimestampUtc', 'UtcTimestamp']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'Command': ('.commands', 'Command'),
    'CommandStatus': ('.commands', 'CommandStatus'),
    'CommandVerdict': ('.commands', 'CommandVerdict'),
    'AggregateRoot': ('.entities', 'AggregateRoot'),
    'Entity': ('.entities', 'Entity'),
    'DomainEvent': ('.events', 'DomainEvent'),
    'EventRecorder': ('.events', 'EventRecorder'),
    'EventStream': ('.events', 'EventStream'),
    'Err': ('.result', 'Err'),
    'Ok': ('.result', 'Ok'),
    'Result': ('.result', 'Result'),
    'Digest': ('.value_objects', 'Digest'),
    'DigestKind': ('.value_objects', 'DigestKind'),
    'DomainInvariantError': ('.value_objects', 'DomainInvariantError'),
    'Epoch': ('.value_objects', 'Epoch'),
    'FenceToken': ('.value_objects', 'FenceToken'),
    'IdKind': ('.value_objects', 'IdKind'),
    'Identifier': ('.value_objects', 'Identifier'),
    'MutationAction': ('.value_objects', 'MutationAction'),
    'MutationItemV1': ('.value_objects', 'MutationItemV1'),
    'MutationManifestV1': ('.value_objects', 'MutationManifestV1'),
    'RepoPath': ('.value_objects', 'RepoPath'),
    'RepositoryPath': ('.value_objects', 'RepositoryPath'),
    'SequenceNumber': ('.value_objects', 'SequenceNumber'),
    'TimestampUtc': ('.value_objects', 'TimestampUtc'),
    'UtcTimestamp': ('.value_objects', 'UtcTimestamp'),
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
