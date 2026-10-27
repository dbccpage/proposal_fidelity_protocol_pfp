# Prompt Representations: Typed Pydantic & YAML Inventory

**AuthorityEffect:** `None`  
**Governing Standard:** Proposal Fidelity Protocol (PFP)  
**Empirical Evidence Base:** [`../../pilots/pilot_output/results.md`](../../pilots/pilot_output/results.md) & [`../../../../atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md`](../../../../atlas/coda_atlas/prompts/pilot_031_050_master_review_and_operad_findings.md)  
**Test Suite Register:** [`pfp/tests/test_prompt_representations.py`](../../../../tests/test_prompt_representations.py)  

This directory contains authoritative YAML specifications (`template_repr_<slug>.yaml`) for each of the eight prompt wire representations supported in the PFP and Symbol Game ecosystem, paired with sovereign typed Pydantic models in `pfp/domain/prompt_representations/`.

---

## 1. Overview of Supported Representations

The inventory spans two complementary quartets:

### 1.1 Empirical Baseline Quartet (Pilots 001–005)

| Representation | Format Posture | Python / Pydantic Model | YAML Specification | Avg Tokens | Validation Rate | Marginal Overhead |
|---|---|---|---|---|---|---|
| **Raw** | Plain unpartitioned prose | [`raw_prompt_representation.py`](../../domain/prompt_representations/raw_prompt_representation.py) | [`template_repr_raw.yaml`](template_repr_raw.yaml) | 86.1 tok | 93.8% (15/16) | +0.0 tok (Baseline) |
| **Structured** | Canonical JSON partition | [`structured_prompt_representation.py`](../../domain/prompt_representations/structured_prompt_representation.py) | [`template_repr_structured.yaml`](template_repr_structured.yaml) | 186.9 tok | 75.0% (12/16) | +100.8 tok |
| **Relational** | SQLite DDL & `prompt_spans` | [`relational_prompt_representation.py`](../../domain/prompt_representations/relational_prompt_representation.py) | [`template_repr_relational.yaml`](template_repr_relational.yaml) | 218.5 tok | 75.0% (12/16) | +132.4 tok |
| **Symbolic** | MSS-N boundary wire & codebook | [`symbolic_prompt_representation.py`](../../domain/prompt_representations/symbolic_prompt_representation.py) | [`template_repr_symbolic.yaml`](template_repr_symbolic.yaml) | 211.7 tok | 81.2% (13/16) | +125.6 tok |

### 1.2 Advanced Algebraic & Geometric Quartet (Pilots 006–050)

| Representation | Format Posture | Python / Pydantic Model | YAML Specification | Mathematical Domain & Source | Primary Invariant |
|---|---|---|---|---|---|
| **Operadic** | 3-Layer compact operad | [`operadic_prompt_representation.py`](../../domain/prompt_representations/operadic_prompt_representation.py) | [`template_repr_operadic.yaml`](template_repr_operadic.yaml) | Multi-turn continuation & MUB(6) pilots (001–050) | Exact ring closure in $\mathbb{Q}$, typed signatures, and congruence ideals |
| **E-Graph** | Equational saturation & normal forms | [`egraph_prompt_representation.py`](../../domain/prompt_representations/egraph_prompt_representation.py) | [`template_repr_egraph.yaml`](template_repr_egraph.yaml) | Mode 13 confluent chase & Gate 03 saturation | Disjoint e-class partitions & 100% constraint span preservation |
| **Diagram** | Monoidal category string diagram | [`diagram_prompt_representation.py`](../../domain/prompt_representations/diagram_prompt_representation.py) | [`template_repr_diagram.yaml`](template_repr_diagram.yaml) | Colored multicategory operad wire-and-box syntax | Planar DAG acyclicity, color matching across ports, no dangling wires |
| **Cochain** | Simplicial complex exterior calculus | [`cochain_prompt_representation.py`](../../domain/prompt_representations/cochain_prompt_representation.py) | [`template_repr_cochain.yaml`](template_repr_cochain.yaml) | Discrete Hodge theory (006) & Bianchi contractions (041-042) | Coboundary nilpotence ($d \circ d = 0$) & exact rational potentials |

---

## 2. Representation Duos & Invariants

### 2.1 Raw Duo
- **Specification:** [`template_repr_raw.yaml`](template_repr_raw.yaml)
- **Model:** `RawPromptRepresentation`
- **Invariant:** Lossless byte equivalence with the source text. Zero framing overhead. Cryptographic equality `source_sha256 == prompt_sha256`.

### 2.2 Structured Duo
- **Specification:** [`template_repr_structured.yaml`](template_repr_structured.yaml)
- **Model:** `StructuredPromptRepresentation`
- **Invariant:** RFC 8785 canonical JSON formatting. Slot monotonicity (`s0, s1, ...`). Mandatory `role='task'` segment.

### 2.3 Relational Duo
- **Specification:** [`template_repr_relational.yaml`](template_repr_relational.yaml)
- **Model:** `RelationalPromptRepresentation`
- **Invariant:** SQLite `STRICT` table DDL compliance. Role domain restricted to `{'task', 'constraint', 'context', 'output', 'unresolved'}`. Mandatory task row.

### 2.4 Symbolic Duo
- **Specification:** [`template_repr_symbolic.yaml`](template_repr_symbolic.yaml)
- **Model:** `SymbolicPromptRepresentation`
- **Invariant:** Strict conformance to `boundary.ebnf` grammar. Wire slot references and codebook keys in `bindings` maintain exact set equality.

### 2.5 Operadic Duo
- **Specification:** [`template_repr_operadic.yaml`](template_repr_operadic.yaml)
- **Model:** `OperadicPromptRepresentation`
- **Invariant:** 3-Layer partition into Layer 0 (Environment ring in $\mathbb{Q}$), Layer 1 (TreeSkeleton typed operations), Layer 2 (SpanTable bound spans, congruence ideals, and antibodies).

### 2.6 E-Graph Duo
- **Specification:** [`template_repr_egraph.yaml`](template_repr_egraph.yaml)
- **Model:** `EgraphPromptRepresentation`
- **Invariant:** Saturated equivalence classes (`e0, e1, ...`) over declared normal form levels (0NF-6NF, ENF). 100% preservation of constraint spans.

### 2.7 Diagram Duo
- **Specification:** [`template_repr_diagram.yaml`](template_repr_diagram.yaml)
- **Model:** `DiagramPromptRepresentation`
- **Invariant:** Monoidal category planar wire-and-box syntax. Typed wire colors, explicit input/output port wiring to declared boxes or boundary ports (`IN`/`OUT`), and acyclic structure.

### 2.8 Cochain Duo
- **Specification:** [`template_repr_cochain.yaml`](template_repr_cochain.yaml)
- **Model:** `CochainPromptRepresentation`
- **Invariant:** Simplicial complex boundary representation with 0-simplices, 1-simplices, and 2-simplices. Coboundary nilpotence and exact rational coefficients over $\mathbb{Q}$.

---

## 3. Claim Hygiene Summary

In accordance with repository claim discipline:
1. **What this artifact supports:** Provides typed Pydantic and YAML type contracts for the eight wire representations studied and utilized in empirical pilots and algebraic derivations.
2. **What this artifact does not support:** Does not claim that any single representation outperforms all others universally or eliminates model errors across arbitrary unconstrained domains.
3. **Narrowest defensible claim:** *These models and YAML schemas provide typed structural validation, invariant enforcement, and wire rendering parity for the eight prompt representations defined in this directory.*
