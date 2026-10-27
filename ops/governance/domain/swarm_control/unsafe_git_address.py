"""Unsafe Git Address Error.

AuthorityEffect: None.
"""

from __future__ import annotations


class UnsafeGitAddress(ValueError):
    def __init__(self, message: str = "Unsafe git address", residual: str = "UNSAFE_REV_PATH_ARGV") -> None:
        super().__init__(message)
        self.residual = residual
