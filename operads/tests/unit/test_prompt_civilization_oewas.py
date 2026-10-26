"""Unit tests verifying retirement of legacy prompt_civilization Python paths in favor of crates_rs.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
import pytest


def test_the_retired_duplicate_path_is_gone() -> None:
    """No second copy may reappear.

    Two byte-identical modules would pass every value comparison and still break
    `type(x) is not Foo` checks at every boundary, which is exactly how the
    duplicate hid for so long.
    """
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(
            "omega_engine_operads.prompt_civilization"
        )


def test_oewas_does_not_re_export_prompt_civilization() -> None:
    import omega_engine_operads as oewas

    assert "prompt_civilization" not in oewas.__all__
    with pytest.raises(AttributeError):
        _ = oewas.prompt_civilization


def test_the_retired_crates_path_is_gone() -> None:
    """Legacy omega_engine.crates.prompt_civilization is retired and superseded by crates_rs."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(
            "omega_engine.crates.prompt_civilization"
        )
