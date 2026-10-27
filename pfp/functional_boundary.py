"""Fail closed when legacy Python code would calculate named functionals.

Phi1, Gamma2, and Xi values must originate in
``engine/crates_rs/core_functional/src``. A caller may still use
Python for packets, proposals, and display; it may not mint these values.
"""

from __future__ import annotations


FUNCTIONAL_OWNER = "engine/crates_rs/core_functional/src"
REFUSAL_CODE = "RUST_FUNCTIONAL_REQUIRED"


class RustFunctionalRequired(ValueError):
    """A legacy Python metric producer has no Rust functional adapter."""

    code = REFUSAL_CODE

    def __init__(self, source: str) -> None:
        super().__init__(
            f"{REFUSAL_CODE}: {source} cannot calculate Phi1, Gamma2, or Xi "
            f"in Python; {FUNCTIONAL_OWNER} is the sole calculator. "
            "A Rust-backed adapter is required."
        )


def require_rust_functional(source: str) -> None:
    """Stop a legacy producer before it computes or writes named metrics."""
    raise RustFunctionalRequired(source)
