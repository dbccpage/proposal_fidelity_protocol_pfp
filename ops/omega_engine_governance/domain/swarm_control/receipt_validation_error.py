"""Receipt Validation Error.

AuthorityEffect: None.
"""

from __future__ import annotations


class ReceiptValidationError(ValueError):
    """Refusal for receipt validation failure."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}" if detail else code)
