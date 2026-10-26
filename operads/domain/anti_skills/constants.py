"""Constants the anti-skill domain carried over from prompt_civilization.

The three values the relocated anti-skill types use, unchanged from
`omega_engine/crates/prompt_civilization/domain/constants.py` (retired in
39c9deb75).

AuthorityEffect: None.
"""

from __future__ import annotations

import re

AUTHORITY_EFFECT_NONE = "None"

DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")

__all__ = ["AUTHORITY_EFFECT_NONE", "DIGEST_PATTERN", "IDENTIFIER_PATTERN"]
