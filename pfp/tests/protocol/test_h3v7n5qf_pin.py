"""The education pin matches the vendored package."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load():
    repo = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists() or (p / 'education').is_dir())
    path = (
        repo
        / "education"
        / "documentation"
        / "005_genesis_ongoing"
        / "code"
        / "check_h3_pin.py"
    )
    spec = importlib.util.spec_from_file_location("check_h3_pin", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_h3_pin_matches_vendored_package() -> None:
    module = _load()
    assert module.differences() == []
    assert len(module.load_pin()) == 1896
    assert module.PIN_COMMIT == "5d9488324ce976817987bd83a28d901371cfc073"


def test_pin_parser_rejects_a_line_without_a_tab() -> None:
    module = _load()
    try:
        module.parse_pin("not-a-pin-row\n")
    except module.PinError as exc:
        assert str(exc) == "pin line 1 is not sha<TAB>path"
    else:
        raise AssertionError("a pin line without a tab was accepted")


def test_pin_parser_rejects_a_duplicate_path() -> None:
    module = _load()
    text = ("a" * 40) + "\tcode/xry/state.py\n" + ("b" * 40) + "\tcode/xry/state.py\n"
    try:
        module.parse_pin(text)
    except module.PinError as exc:
        assert str(exc) == "duplicate pin path code/xry/state.py"
    else:
        raise AssertionError("duplicate pin path was accepted")
