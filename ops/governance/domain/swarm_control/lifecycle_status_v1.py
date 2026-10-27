"""Lifecycle Status V1 Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class LifecycleStatusV1(Enum):
    DECLARED = "DECLARED"
    NORMALIZED = "NORMALIZED"
    DIAGNOSED = "DIAGNOSED"
    PROPOSED = "PROPOSED"
    VERIFIED = "VERIFIED"
    HANDED_OFF = "HANDED_OFF"
