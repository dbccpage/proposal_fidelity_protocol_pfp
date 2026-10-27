"""Verify pfp.ebnf against conformance test cases.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = next((p for p in HERE.parents if (p / ".git").exists() or (p / "education").is_dir()), HERE.parents[2])
PFP_EBNF_PATH = (
    REPO
    / "education"
    / "documentation"
    / "030_the_symbol_game_proposal_fidelity_protocol_pfp"
    / "grammar"
    / "pfp.ebnf"
)
CASES_PATH = (
    REPO
    / "education"
    / "documentation"
    / "030_the_symbol_game_proposal_fidelity_protocol_pfp"
    / "grammar"
    / "pfp_conformance_cases.json"
)

# Import Grammar recognizer from 030_the_symbol_game_proposal_fidelity_protocol_pfp/grammar/check_grammars.py
GRAMMAR_DIR = (
    REPO
    / "education"
    / "documentation"
    / "030_the_symbol_game_proposal_fidelity_protocol_pfp"
    / "grammar"
)
if not GRAMMAR_DIR.is_dir():
    GRAMMAR_DIR = REPO / "ow" / "pfp_v0.2" / "grammar"
sys.path.insert(0, str(GRAMMAR_DIR))
from check_grammars import Grammar


def main() -> int:
    ebnf_source = PFP_EBNF_PATH.read_text(encoding="utf-8")
    grammar = Grammar(ebnf_source)
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    failures = []
    for c in cases:
        case_id = c["id"]
        start = c["start"]
        text = c["text"]
        expected = c["accept"]
        actual = grammar.accepts(start, text)
        if actual != expected:
            failures.append((case_id, start, text, expected, actual))

    if failures:
        print(f"FAILED: {len(failures)} cases failed:")
        for fid, start, text, exp, act in failures:
            print(f"  [{fid}] start={start} text={text!r} expected={exp} got={act}")
        return 1

    print(f"PASS: {len(cases)} cases accepted/refused across starts in pfp.ebnf")
    print(f"Grammar source: {PFP_EBNF_PATH}")
    print("AuthorityEffect: None.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
