"""Targeted pytest suite for pfp.ebnf conformance verification.

AuthorityEffect: None. GenesisEffect: None.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Dynamic search for pfp.ebnf
HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / '.git').exists() or (p / 'omega_engine_education').is_dir())
cand_pfp = REPO / 'omega_engine_education' / 'documentation' / '004_oepfp' / 'grammar'
cand_legacy = REPO / 'omega_engine_education' / 'documentation' / '030_the_symbol_game_proposal_fidelity_protocol_pfp' / 'grammar'
EBNF_DIR = cand_pfp if cand_pfp.is_dir() else cand_legacy
if str(EBNF_DIR) not in sys.path:
    sys.path.insert(0, str(EBNF_DIR))
PFP_EBNF_PATH = EBNF_DIR / "pfp.ebnf"
CASES_PATH = EBNF_DIR / "pfp_conformance_cases.json"
GRAMMAR_DIR = EBNF_DIR

sys.path.insert(0, str(GRAMMAR_DIR))
from check_grammars import Grammar


@pytest.fixture(scope="module")
def pfp_grammar() -> Grammar:
    ebnf = PFP_EBNF_PATH.read_text(encoding="utf-8")
    return Grammar(ebnf)


def test_pfp_conformance(pfp_grammar: Grammar):
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    for c in cases:
        start = c["start"]
        text = c["text"]
        expected = c["accept"]
        actual = pfp_grammar.accepts(start, text)
        assert actual == expected, (
            f"Case {c['id']} failed: text={text!r}, expected={expected}, got={actual}"
        )
