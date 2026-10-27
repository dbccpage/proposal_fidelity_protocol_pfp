"""Identity Contract Error.

AuthorityEffect: None.
"""

from __future__ import annotations


class IdentityContractError(ValueError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)
