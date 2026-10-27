"""Package documentation claims only what the code does (study defect D19).

Counterexamples removed on 2026-09-29, each checked here so it cannot return:

- the package docstring claimed "exponential half-life decay", "Regulatory
  T-Cell supervision" (which lives in OEWAS) and "phagocytic formulary
  regeneration";
- `immune_bench.py` said it phagocytoses refused turns from CemeterySink; it
  only escapes caller-supplied phrases;
- `mssn_ports.py` evaluated "the 7 frozen Demo 3 failure detectors" with three
  codes;
- `mssn_classifier.py` listed AM-FSP-6 as a classified failure mode, but no
  detector emits it;
- `mssn_pharmacy.py` called itself a "Faithful Python port" of `pharmacy.rs`.
"""

from __future__ import annotations

from pathlib import Path

import eis as package
from eis.infrastructure import mssn_classifier
from eis.infrastructure.mssn_ports import FARM_CODES

ROOT = Path(package.__file__).resolve().parent

# Phrases of the old claims. Case-sensitive where a corrected sentence reuses
# the words in lower case ("not an exponential half-life", "Regulatory T-cell
# supervision lives in OEWAS").
BANNED = (
    "exponential half-life decay",
    "Regulatory T-Cell supervision",
    "and phagocytic formulary regeneration",
    "Phagocytoses refused candidate turns from",
    "7 frozen Demo 3",
    "Faithful Python port",
    "Faithful Python domain implementation",
)


def test_no_source_repeats_a_removed_overclaim() -> None:
    sources = sorted(path for path in ROOT.rglob("*.py") if "tests" not in path.parts)
    offenders = [
        (path.relative_to(ROOT).as_posix(), phrase)
        for path in sources
        for phrase in BANNED
        if phrase in path.read_text(encoding="utf-8")
    ]
    assert offenders == []


def test_am_fsp_6_is_documented_as_having_no_farm_detector() -> None:
    doc = mssn_classifier.__doc__ or ""
    assert "AM-FSP-6" in doc and "no detector" in doc
    assert not any(code.startswith("AM-FSP-6") for code in FARM_CODES)


def test_the_package_names_where_tregs_live() -> None:
    doc = package.__doc__ or ""
    assert "Regulatory T-cell supervision lives in OEWAS" in doc
