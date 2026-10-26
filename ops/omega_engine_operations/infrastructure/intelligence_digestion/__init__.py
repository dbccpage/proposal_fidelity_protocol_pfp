"""Concrete adapters for intelligence digestion.

AuthorityEffect: None.
"""

from .collection import DurableIntelligenceCollector, IntelligenceCollectionError
from .native_lifecycle import NativeIntelligenceLifecycle, NativeLifecycleError

__all__ = [
    "DurableIntelligenceCollector",
    "IntelligenceCollectionError",
    "NativeIntelligenceLifecycle",
    "NativeLifecycleError",
]
