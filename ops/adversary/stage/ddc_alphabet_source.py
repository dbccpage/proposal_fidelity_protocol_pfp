"""Read the Rust DDC alphabet and install it into the stage domain.

The domain parser does not open this file. AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path


def read_ddc_alphabet_source() -> str:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = (
            parent
            / "engine"
            / "crates_rs"
            / "core_wdp"
            / "src"
            / "ddc"
            / "ddc_alphabet.rs"
        )
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    raise FileNotFoundError("ddc_alphabet.rs was not found")


def install_ddc_alphabet() -> None:
    from adversary.stage.domain.ddc import bind_ddc_alphabet

    bind_ddc_alphabet(read_ddc_alphabet_source())
