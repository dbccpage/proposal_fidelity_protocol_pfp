"""Discriminating regressions for the separately retained G01 lexical guard."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("g01_lexical_supplement", ROOT / "genesis_g01_lexical_supplement.py")
assert SPEC is not None and SPEC.loader is not None
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


@pytest.mark.parametrize("text", ["-- axiom fabricated : True", "/- axiom fabricated : True -/", "/- /- axiom fabricated : True -/ -/", "-- sorry", "/- partial def forged := 1 -/"])
def test_raw_comment_tokens_are_rejected(text):
    assert GUARD.violations(text)


@pytest.mark.parametrize("name", ["ResearchG01.lean", "G01Targets.lean", "G01Mutation_theorem_run_v3_VALID_CONTROL.lean"])
def test_actual_previously_valid_sources_remain_lexically_valid(name):
    assert GUARD.violations((ROOT / "native_genesis_g01" / name).read_text(encoding="utf8")) == []
