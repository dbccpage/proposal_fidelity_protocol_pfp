# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Digests as exact values: SHA-256 over a declared canonical serialization.

A digest is 32 bytes, compared byte for byte.  The serialization is a
declared convention, never inferred: canonical JSON with sorted keys, no
white space and ASCII escapes, the form the receiving side's checkers use.
What a level hashes (which hosted content, in which shape) is stated in its
restatement; this module only fixes the two operations.

Nothing here reaches the kernel: SHA-256 is decided in the metatheory, so a
clause that reads a digest stays COMPUTED.  The same holds for the textbook
signature check added in round P7B (modular exponentiation of naturals).

AuthorityEffect: None
"""

from __future__ import annotations

import hashlib
import json


def canonical_json(value: object) -> bytes:
    """Sorted keys, separators without white space, ASCII only."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def digest_of(value: object) -> bytes:
    """The digest of a value's canonical JSON."""
    return sha256(canonical_json(value))


def as_number(d: bytes) -> int:
    """A digest read as a natural, most significant byte first."""
    return int.from_bytes(d, "big")


def signature_verifies(n: int, e: int, s: int, message: bytes) -> bool:
    """Textbook signature check over SHA-256 (round P7B): key ``(n, e)``
    verifies ``s`` on ``message`` exactly when ``0 < s < n`` and ``s^e mod n``
    is the message's SHA-256, read as a natural, mod ``n``.  Only checking is
    done here; nothing signs.  It says the arithmetic holds under the declared
    scheme, nothing about unforgeability (no padding is modelled)."""
    if n <= 1 or e <= 0 or not 0 < s < n:
        return False
    return pow(s, e, n) == as_number(sha256(message)) % n
