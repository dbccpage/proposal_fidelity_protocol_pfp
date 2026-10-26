"""Shared Kernel: KeyType and WireKey enumerations for structured wire and domain keys.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class KeyType(str, Enum):
    """Classification of key types across domain and wire contracts."""

    WIRE = "wire"
    FIELD = "field"
    SCHEMA = "schema"
    CONTEXT = "context"
    HEADER = "header"


KeyTypeKind = KeyType


class CommonWireKeyKind(str, Enum):
    """Common wire dictionary keys shared across multiple bounded contexts."""

    SCHEMA_VERSION = "schema_version"
    AUTHORITY_EFFECT = "authority_effect"
    TASK_ID = "task_id"
    OBJECTIVE = "objective"
    STATUS = "status"
    DISPOSITION = "disposition"
    PAYLOAD = "payload"
    CANDIDATE_BUDGET = "candidate_budget"
    OPERATION_BUDGET = "operation_budget"
    RECEIPT_ID = "receipt_id"
    SOURCE_DIGEST = "source_digest"
    PRODUCER_ID = "producer_id"
