"""Mutation Action Enum.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class MutationAction(str, Enum):
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"
