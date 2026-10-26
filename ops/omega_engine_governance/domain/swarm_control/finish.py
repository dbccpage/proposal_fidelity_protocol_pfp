"""Finish Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Finish:
    output: Any
