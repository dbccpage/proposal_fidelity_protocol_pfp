---
id: ENC-0090
kind: theorem
name: "Packet-Family Soundness Schema"
status: PROVED-PROSE
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.11"]
sources:
  - "canonical_omega_math_spine.md v1.5.2 §IV.4 'Theorem IV.11'"
  - "symbol_game_math_spine.md math_spines_v002 §1.5 'Theorem: Packet-Family Soundness Schema'"
  - "proof_obligations.md v1.3.5 §13 'Theorem (schema; unconditional given (D),(L),(E))' (section 'PO-PFVS — Packet-Family Verifier Soundness Schema (SG-VAL-001 schema half)')"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0090 — Packet-Family Soundness Schema

## Statement

For a packet family $F$ with verifier $V_F$ decomposing as $V_F(x,P) = 1 \iff \bigwedge_{i=1}^n C_i(x,P) = 1$, if each $C_i$ has a proved local soundness lemma $C_i(x,P) = 1 \Rightarrow \varphi_i(x,P)$ and $\bigwedge_i \varphi_i \Rightarrow S_F(x,P)$, then $V_F$ is sound for $S_F$.

## Proof

*Proof.* Acceptance implies all $C_i$ accept; local soundness implies all $\varphi_i$; semantic entailment yields $S_F$. $\square$

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| schema: conjunctive verifier soundness from per-conjunct local soundness lemmas plus semantic entailment | local | none identified | NOT-STARTED |

## Notes

- §IV.4 is titled "Compliance with the GTLA Finite Authority Axioms". The
  source follows the proof with an instantiation table, copied verbatim:

  | Packet Family | Status |
  |:---|:---|
  | LP Optimality (weak duality) | [PROVED] |
  | Code Rewrite Boundary | [PROVED, within protected Rust subset] |
  | Operator Classification | [PROVED] |
  | Cochain Obstruction | [PROVED] |
  | Graph Incidence | [PROVED] |

- The source then adds a "**Compliance with GTLA:**" paragraph: the Symbol
  Game verification functor \(\mathcal{V}\) produces evidence consumed by the
  GTFDA pipeline and "does not itself produce authority"; \(\mathcal{V}\) and
  \(F\) are consistent with axioms A1, A3, A4 "but they do not independently
  satisfy A0–A7 — those require the full pipeline \(\Pi_S^\sharp\)".

- Variant statement in symbol_game_math_spine.md §1.5 (same content); proof body there if any is NOT merged.
- Variant statement in proof_obligations.md v1.3.5 §13 "PO-PFVS — Packet-Family
  Verifier Soundness Schema (SG-VAL-001 schema half)": the same schema theorem
  ("Theorem (schema; unconditional given (D),(L),(E))",
  \(V_F(x,P)=1 \Rightarrow S_F(x,P)\)) with the three ingredients displayed as
  **(D)** faithful decomposition, **(L)** per-clause local soundness, **(E)**
  semantic entailment, and a modus-ponens-chain proof. The catalog itself
  equates them: "Schema: PROVED (this catalog; = canonical Theorem IV.11)."
  NOT merged into the Statement.
- The PO-PFVS variant carries a **reconciled instantiation table that
  contradicts the bare [PROVED] labels** quoted from canonical IV.11 above:
  per the catalog's §8 Master Audit #4 / §10 demotions, only "LP Optimality
  (weak duality)" and "Operator Classification" remain PROVED; "Code Rewrite
  Boundary" and "Graph Incidence" are CONDITIONAL (`REQUIRES_REVALIDATION` vs
  `symbol_game_proofs.md`) and "Cochain Obstruction" is per-carrier
  CONDITIONAL (= PO-D1, \(d_1 d_0 = 0\) per carrier). The catalog warns the
  IV.11 labels "must not be cited as unconditional". Schema validity is
  unaffected (instantiations merely supply (D),(L),(E) per family).
- The `po:PO-PFVS` alias is held by [[ENC-0099]] (GlobalValid Specification
  Gate), which extracts the PO-PFVS section's *done-condition* half; this
  entry is the section's *schema-theorem* half.

## Provenance

- Extracted 2026-06-09 from `canonical_omega_math_spine.md` v1.5.2, §IV.4
  (statement and proof copied verbatim; the instantiation table and GTLA
  compliance paragraph are recorded under Notes). Original header line:
  `**Theorem IV.11 (Packet-Family Soundness Schema).** [PROVED] For a packet family $F$ with verifier $V_F$ decomposing as $V_F(x,P) = 1 \iff \bigwedge_{i=1}^n C_i(x,P) = 1$, if each $C_i$ has a proved local soundness lemma $C_i(x,P) = 1 \Rightarrow \varphi_i(x,P)$ and $\bigwedge_i \varphi_i \Rightarrow S_F(x,P)$, then $V_F$ is sound for $S_F$.`

## Changelog

- 2026-06-09: ENC-0090 created (M2 E1 extraction).
- 2026-06-09: variant provenance appended (M2 E3): proof_obligations.md §13
  PO-PFVS schema theorem recorded as duplicate variant; reconciled
  instantiation-table conflict noted (Notes + sources only; Statement
  untouched).
