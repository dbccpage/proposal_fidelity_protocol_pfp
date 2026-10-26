# Prompt Representations: Typed Pydantic & YAML Inventory

**AuthorityEffect:** `None`  
**Governing Standard:** Proposal Fidelity Protocol (PFP)  
**Empirical Evidence Base:** [`../../pilots/pilot_output/results.md`](../../pilots/pilot_output/results.md)  
**Test Suite Register:** [`../../pilots/pilot_output/tests.md`](../../pilots/pilot_output/tests.md)  

This directory contains typed Pydantic models (`.py`) and authoritative YAML specifications (`.yaml`) for each of the four prompt wire representations empirically evaluated in the PFP single-turn prompt rewriting pilot.

---

## 1. Overview of Evaluated Representations

As recorded in [`results.md`](../../pilots/pilot_output/results.md), four prompt representations were evaluated across 64 dispatches across four models (`openai/gpt-4o-mini`, `google/gemini-2.5-flash`, `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-chat`):

| Representation | Format Posture | Python / Pydantic Model | YAML Specification | Avg Tokens | Validation Rate | Marginal Overhead |
|---|---|---|---|---|---|---|
| **Raw** | Plain unpartitioned prose | [`raw_prompt_representation.py`](raw_prompt_representation.py) | [`raw_prompt_representation.yaml`](raw_prompt_representation.yaml) | 86.1 tok | 93.8% (15/16) | +0.0 tok (Baseline) |
| **Structured** | Canonical JSON partition | [`structured_prompt_representation.py`](structured_prompt_representation.py) | [`structured_prompt_representation.yaml`](structured_prompt_representation.yaml) | 186.9 tok | 75.0% (12/16) | +100.8 tok |
| **Relational** | SQLite DDL & `prompt_spans` | [`relational_prompt_representation.py`](relational_prompt_representation.py) | [`relational_prompt_representation.yaml`](relational_prompt_representation.yaml) | 218.5 tok | 75.0% (12/16) | +132.4 tok |
| **Symbolic** | MSS-N boundary wire & codebook | [`symbolic_prompt_representation.py`](symbolic_prompt_representation.py) | [`symbolic_prompt_representation.yaml`](symbolic_prompt_representation.yaml) | 211.7 tok | 81.2% (13/16) | +125.6 tok |

---

## 2. Representation Duos & Invariants

### 2.1 Raw Duo
- **Specification:** [`raw_prompt_representation.yaml`](raw_prompt_representation.yaml)
- **Model:** [`RawPromptRepresentation`](raw_prompt_representation.py)
- **Invariant:** Lossless byte equivalence with the source text. Zero framing overhead. Cryptographic equality `source_sha256 == prompt_sha256`.

### 2.2 Structured Duo
- **Specification:** [`structured_prompt_representation.yaml`](structured_prompt_representation.yaml)
- **Model:** [`StructuredPromptRepresentation`](structured_prompt_representation.py)
- **Invariant:** RFC 8785 canonical JSON formatting. Slot monotonicity (`s0, s1, ...`). Mandatory `role='task'` segment.

### 2.3 Relational Duo
- **Specification:** [`relational_prompt_representation.yaml`](relational_prompt_representation.yaml)
- **Model:** [`RelationalPromptRepresentation`](relational_prompt_representation.py)
- **Wire/execution boundary:** Historical `sqlite_strict_text_set_v1` retains the
  recorded PostgreSQL-style casts and JSON-quoted text. It is a prompt wire
  format, not executable SQLite. `SqlitePromptRepresentation` provides the
  separate `sqlite_strict_utf8_v2` executable profile: fixed STRICT DDL and table
  names, with UTF-8 data literals that preserve quotes, Unicode and NULs. The
  historical benchmark numbers above do not measure this new profile. Execute
  only host-rendered SQL; this profile grants no authority to model-supplied SQL.
- **Invariant:** Declared STRICT DDL, sequential slots, a mandatory task row and
  roles restricted to `{'task', 'constraint', 'context', 'output', 'unresolved'}`.
  Executable SQL roundtrip is checked separately for v2.

### 2.4 Symbolic Duo
- **Specification:** [`symbolic_prompt_representation.yaml`](symbolic_prompt_representation.yaml)
- **Model:** [`SymbolicPromptRepresentation`](symbolic_prompt_representation.py)
- **Invariant:** Strict conformance to `boundary.ebnf` grammar. Wire slot references and codebook keys in `bindings` maintain exact set equality.
- **Optional input pattern:** [Symbolic constraint binding v001](symbolic_constraint_binding_v001.md)
  uses the existing compiler with an inline codebook and complete active constraints.
  Its host controls distinguish binding integrity from protected-query preservation;
  no chemistry, physics or model-performance improvement is certified.

---

## 3. Claim Hygiene Summary

In accordance with repository claim discipline:
1. **What this artifact supports:** Provides strict Pydantic and YAML type contracts for the four wire representations studied in the empirical pilot, guaranteeing schema validation under declared assumptions.
2. **What this artifact does not support:** Does not claim that structured, relational, or symbolic encodings enhance model reasoning or decrease token cost in single-turn unbatched settings.
3. **Narrowest defensible claim:** *These models and YAML schemas provide typed structural validation and serialization parity for the four empirical prompt variants evaluated in results.md.*
