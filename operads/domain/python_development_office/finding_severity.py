"""FindingSeverity enumeration for python_development_office domain."""

from __future__ import annotations

from enum import Enum


class FindingSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
