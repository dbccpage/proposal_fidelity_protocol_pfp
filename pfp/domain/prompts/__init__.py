"""PFP Prompts, Templates, and Packets Bounded Context.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .packets import PacketEnvelope, PacketVerificationReceipt, canonical_json_bytes, sha256_canonical_hex
    from .pfp_prompt import PfpPrompt
    from .prompts import PromptAssemblyError, PromptPacket, PromptSlot, PromptTemplate

__all__ = ['PacketEnvelope', 'PacketVerificationReceipt', 'PfpPrompt', 'PromptAssemblyError', 'PromptPacket', 'PromptSlot', 'PromptTemplate', 'canonical_json_bytes', 'sha256_canonical_hex']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'PacketEnvelope': ('.packets', 'PacketEnvelope'),
    'PacketVerificationReceipt': ('.packets', 'PacketVerificationReceipt'),
    'canonical_json_bytes': ('.packets', 'canonical_json_bytes'),
    'sha256_canonical_hex': ('.packets', 'sha256_canonical_hex'),
    'PfpPrompt': ('.pfp_prompt', 'PfpPrompt'),
    'PromptAssemblyError': ('.prompts', 'PromptAssemblyError'),
    'PromptPacket': ('.prompts', 'PromptPacket'),
    'PromptSlot': ('.prompts', 'PromptSlot'),
    'PromptTemplate': ('.prompts', 'PromptTemplate'),
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
