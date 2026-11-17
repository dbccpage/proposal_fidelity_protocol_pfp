"""RuleCategory enumeration for python_development_office domain."""

from __future__ import annotations

from enum import Enum


class RuleCategory(str, Enum):
    PITFALL = "pitfall"
    CLEAN_ARCH = "clean_arch"
    DDD = "ddd"
    MVC = "mvc"
