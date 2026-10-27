# EBNF Grammars & Syntax Verification Recognizers

**AuthorityEffect:** `None`  
**Governing Standard:** ISO/IEC 14977 EBNF, Fail-Closed Byte-Exact Parsing  
**Architectural Synthesis:** [`../docs/06_prompt_packet_stage_synthesis.md`](../docs/06_prompt_packet_stage_synthesis.md)  
**Detailed Contracts Monograph:** [`grammars_readme.md`](grammars_readme.md)  

This directory houses the authoritative EBNF grammar specifications, syntax profiles, conformance test cases, and the Python EBNF parsing engine (`check_grammars.py`) for the Proposal Fidelity Protocol (PFP v0.2).

---

## 1. Grammars Inventory

| Grammar File | Profile ID | Canonical Start Symbol | Focus & Scope |
|---|---|---|---|
| [`pfp.ebnf`](pfp.ebnf) | `pfp-v0.2` | `pfp_packet` | Proposal Fidelity Protocol wire envelope, 6 frozen slots, and 8 canonical PFP terminals. |
| [`cycle_repair.ebnf`](cycle_repair.ebnf) | `pkt00-k0-v1` | `cycle_repair` | K0 simplicial cycle repair candidate wire expressions with fixed incidence matrices. |
| [`ddc_trace.ebnf`](ddc_trace.ebnf) | `ddc-tape-shape-v1` | `ddc_trace` | Discrete Deformation Calculus 8-letter operational alphabet trace tapes. |
| [`glyph_graph.ebnf`](glyph_graph.ebnf) | `glyph-graph-v1` | `glyph_graph` | Single-glyph vertices, directed edges, and simplicial 1-complex graphs. |
| [`historical_packet.ebnf`](historical_packet.ebnf) | `historical-packet-v1` | `packet` | Postnikov tower historical packets: ground, atom, or `op<…>` application. |
| [`quiz_packet.ebnf`](quiz_packet.ebnf) | `quiz-packet-v1` | `quiz_message` | Educational `ask`, `ans`, and `ref` quiz packets. |

---

## 2. Conformance Test Suites & Recognizers

- **[`check_grammars.py`](check_grammars.py):** The canonical recursive descent parser engine validating inputs against arbitrary ISO/IEC 14977 EBNF grammars.
- **[`pfp_conformance_cases.json`](pfp_conformance_cases.json):** 28 positive and negative conformance test cases validating `pfp.ebnf`.
- **[`conformance_cases.json`](conformance_cases.json):** Multi-profile test vectors covering `cycle_repair.ebnf`, `ddc_trace.ebnf`, `glyph_graph.ebnf`, `historical_packet.ebnf`, and `quiz_packet.ebnf`.

---

## 3. Running Conformance Tests

To run the PFP grammar conformance tests locally:
```bash
py -3.12 -m pytest pfp/tests/protocol/test_pfp_grammar.py pfp/tests/types/test_grammar_types.py
```

The cross-grammar checker is at
`education/documentation/004_oepfp/grammar/check_grammars.py`:
```bash
py -3.12 education/documentation/004_oepfp/grammar/check_grammars.py
```

> **Status at `201dc8d` (2026-10-15).** The pytest command above passes (14
> tests). `check_grammars.py` fails: it reads `../python/domain/boundary.ebnf`,
> which does not exist. `pfp/scripts/check_pfp_grammar.py` also
> fails, with `ModuleNotFoundError: check_grammars`. Earlier versions of this
> page named `education/code/check_pfp.py` and a
> `030_the_symbol_game_proposal_fidelity_protocol_pfp/` path; neither exists.

---

## 4. Typed Contracts

- [`grammar_types.py`](grammar_types.py): Pydantic v2 models (`GrammarProfileEntry`, `GrammarRegistry`, `PfpConformanceCase`, `ProfileConformanceCase`, `ConformanceVerdict`).
- [`grammar_types.yaml`](grammar_types.yaml): the inventory table and alphabets as data.
