"""Read the Rust DDC alphabet from the operad canon and install it into the stage domain.

The alphabet is `DdcOp::letter` in `code/rust/core_operad_canon/src/lib.rs`, its one definition.

The domain parser does not open this file. AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path


def read_ddc_alphabet_source() -> str:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "code" / "rust" / "core_operad_canon" / "src" / "lib.rs"
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    raise FileNotFoundError("code/rust/core_operad_canon/src/lib.rs was not found")


def install_ddc_alphabet() -> None:
    from adversary.stage.domain.ddc import bind_ddc_alphabet

    bind_ddc_alphabet(read_ddc_alphabet_source())
