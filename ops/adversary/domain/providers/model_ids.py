"""model_ids.py — the one place that spells vendor model identifiers.

AuthorityEffect: None. Provider APIs reject unknown model names, so the exact identifiers
must exist somewhere. They live here and nowhere else; the rest of the code, its tests and
its records use the neutral labels below.

Labels: ``G`` is the OpenRouter/Google family, ``U`` the Sakana family, ``O``, ``S`` and
``H`` the three Anthropic tiers. ``FAST``, ``LITE`` and ``PRO`` name the size within a family.
"""

from __future__ import annotations

# OpenRouter slugs.
ROUTER_G_FAST = "google/gemini-2.5-flash"
ROUTER_G_LITE = "google/gemini-2.5-flash-lite"
ROUTER_G_PRO = "google/gemini-2.5-pro"
ROUTER_U_ULTRA = "sakana/fugu-ultra-v2"
ROUTER_O = "anthropic/claude-opus-5.5"

# Native provider identifiers.
NATIVE_G_FAST = "gemini-2.5-flash"
NATIVE_G_PRO = "gemini-2.5-pro"
ANTHROPIC_H = "claude-haiku-5-5"
ANTHROPIC_S = "claude-sonnet-5-5"
ANTHROPIC_O = "claude-opus-5-5"

#: Label -> exact identifier, for tools that resolve labels at run time.
MODEL_IDS: dict[str, str] = {
    "router-g-fast": ROUTER_G_FAST,
    "router-g-lite": ROUTER_G_LITE,
    "router-g-pro": ROUTER_G_PRO,
    "router-u-ultra": ROUTER_U_ULTRA,
    "router-o": ROUTER_O,
    "native-g-fast": NATIVE_G_FAST,
    "native-g-pro": NATIVE_G_PRO,
    "anthropic-h": ANTHROPIC_H,
    "anthropic-s": ANTHROPIC_S,
    "anthropic-o": ANTHROPIC_O,
}

__all__ = [
    "ANTHROPIC_H", "ANTHROPIC_O", "ANTHROPIC_S", "MODEL_IDS", "NATIVE_G_FAST", "NATIVE_G_PRO",
    "ROUTER_G_FAST", "ROUTER_G_LITE", "ROUTER_G_PRO", "ROUTER_O", "ROUTER_U_ULTRA",
]
