"""Finite reference model for the greenfield derivation.

Everything in this package is metatheory apparatus: Python data structures,
tokens, and indices are external bookkeeping.  The object language consists
only of what a regime admits (data, judgment forms, judgment instances,
uniform rules) plus externally imposed separation requirements.
"""

__all__ = [
    "model",
    "observe",
    "candidates",
    "iso",
    "engine",
    "export",
]
