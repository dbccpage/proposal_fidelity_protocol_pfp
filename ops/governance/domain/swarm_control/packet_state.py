"""Packet State Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class PacketState(str, Enum):
    ADMITTED = "ADMITTED"
    DEVELOPING = "DEVELOPING"
    CANDIDATE_BOUND = "CANDIDATE_BOUND"
    AWAITING_HUMAN = "AWAITING_HUMAN"
    READY_FOR_LICENSE = "READY_FOR_LICENSE"
    MERGED = "MERGED"
    PRUNED = "PRUNED"
