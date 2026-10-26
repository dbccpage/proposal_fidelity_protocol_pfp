---
id: ENC-0103
kind: theorem
name: "Normal-Form Compression"
status: CONDITIONAL
conditional_on: ["IX-REWRITE"]
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IX.3"]
sources:
  - "canonical_omega_math_spine.md v1.5.2 §IX.1 'Theorem IX.3'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0103 — Normal-Form Compression

## Statement

Every
**distinct-class** admissible word over $\{E,I,C,R\}$ (at most one occurrence per class)
compresses to the canonical skeleton

$$
E \circ I \circ C \circ R, \qquad \text{length} \le 4 .
$$

The compression is the class-monoid normalization; the invariant preserved at every step
is $\Phi_n([x])$ (preserved by $E$ and $I$, computed by $R$, tested by $C$, damaged only by
the refused $M$). This is a **conditional single-excursion shape**, NOT a universal length
bound for arbitrary maps, **and NOT a bound for multi-occurrence words**: a word containing
two distinct-context $C$ operators (or two non-collapsing $I$ operators) cannot reach
length $\le 4$, because §IV.5 supplies no $C\circ C$ or $I\circ I$ collapse rule. Supplying
those rules together with a termination order and confluence is obligation IX-REWRITE; until
then the reduction is asserted only for distinct-class words relative to the declared rewrite
table.

## Hypotheses

- **IX-REWRITE**: the operator rewrite system is terminating and confluent with
  per-class collapse for $C,I$. The source tag records these assumptions as
  "**undischarged** (obligation IX-REWRITE; see §IV.5 note)".

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| distinct-class word normalization to $E \circ I \circ C \circ R$ (length $\le 4$) relative to the declared rewrite table, conditional on IX-REWRITE | local | none identified | NOT-STARTED |

## Notes

- The source tag is the non-standard `[PROVED-CONDITIONAL — assumes the operator rewrite
  system is terminating and confluent with per-class collapse for $C,I$; these assumptions
  are **undischarged** (obligation IX-REWRITE; see §IV.5 note)]`; normalized to
  CONDITIONAL on IX-REWRITE (not upgraded).
- **Superseded in part:** §IX.1a ("Exhaustiveness & composition — corrected status
  (P1 + IX-REWRITE, 2026-06-05)") states (verbatim): "**Composition (IX-REWRITE
  refinement, `ix_rewrite_settlement.md`)** — supersedes the "`E∘I∘C∘R` distinct-class"
  phrasing of Thm IX.3 above." — there, $C$ is diagnostic (not part of the normal form),
  the action algebra of $\{E,I,R\}$ is closed (unconditional), and the
  representative-wise normal form is $E\circ I\circ R$ (length $\le 3$) under declared
  witnesses W1/W2/W2′. This entry records Theorem IX.3 as stated; the refinement is a
  separate source statement.

## Provenance

- Extracted 2026-06-09 from `canonical_omega_math_spine.md` v1.5.2, §IX.1
  (statement copied verbatim; no *Proof.* block in the source). Original header line
  (wraps across three source lines, joined here with single spaces):
  `**Theorem IX.3 (Normal-Form Compression).** [PROVED-CONDITIONAL — assumes the operator rewrite system is terminating and confluent with per-class collapse for $C,I$; these assumptions are **undischarged** (obligation IX-REWRITE; see §IV.5 note)] Every`

## Changelog

- 2026-06-09: ENC-0103 created (M2 E1 extraction).
