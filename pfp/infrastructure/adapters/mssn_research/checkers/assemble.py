"""Splice the one checker preamble in front of an obligation module.

The stage files are the pinned obligation. Historical checker bytes that still
carry the preamble marker are executed unchanged.

AuthorityEffect: None.
"""

from __future__ import annotations

from importlib.resources import files

_MARK = b"# ---- shared preamble:"


def preamble_bytes() -> bytes:
    return files(__package__).joinpath("preamble.py").read_bytes()


def assemble_checker_source(obligation: bytes) -> bytes:
    if _MARK in obligation:
        return obligation
    preamble = preamble_bytes()
    if not preamble.endswith(b"\n"):
        preamble += b"\n"
    return preamble + obligation
