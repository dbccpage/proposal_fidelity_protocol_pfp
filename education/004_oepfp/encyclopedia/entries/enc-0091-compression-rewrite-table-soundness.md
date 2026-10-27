---
id: ENC-0091
kind: theorem
name: "Compression Rewrite Table Soundness"
status: SKETCH
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:IV.12"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §IV.5 'Theorem IV.12'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0091 — Compression Rewrite Table Soundness

## Statement

Every admitted rewrite preserves declared semantics $\llbracket - \rrbracket$. Un-witnessed rules are refused, not silently applied.

## Proof Pointer

No proof body accompanies this theorem in the source (§IV.5): the `[PROVED]`
tag is carried with no *Proof.* environment, sketch, or external pointer.
Verifier adjudication 2026-06-09: status set to SKETCH (see Notes). The
per-identity soundness facts it rests on are the
§IV.5 operator-algebra table rows (each individually tagged [PROVED] /
[PROVED, conditional on witness] in the source), but no in-spine derivation
assembling them is recorded.

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| semantics preservation of every admitted rewrite rule, with refusal of un-witnessed rules | local | none identified | NOT-STARTED |

## Notes

- §IV.5 ("Conditional Operator Algebra") opens with a blanket scope sentence,
  quoted verbatim: "All results below are conditional on: a fixed cochain
  layer, exact or declared-tolerance arithmetic, a declared action domain, and
  replayable witnesses."
- The source immediately follows the theorem with a scope blockquote, copied
  verbatim:

  > **Rewrite-table assumptions (undischarged — obligation IX-REWRITE).** Thm IV.12 establishes only *soundness*; it does NOT supply the three conditions the normal-form reduction needs. (i) **Termination:** the rule $I_C\circ E_\alpha=E_{T_I(\alpha)}\circ I_C$ is length-*preserving*, so word-length is not a termination measure and no well-founded order is given. (ii) **Confluence** (Church–Rosser) is assumed, not shown. (iii) **Per-class collapse for $C$ and $I$:** only $E\circ E$ and $R\circ R$ collapse; there is **no $C\circ C$ and no $I\circ I$ rule**, so a word with two distinct-context $C$ operators cannot reach the one-per-class form. Hence the "$\to E^?\circ I^?\circ C^?\circ R^?$, length $\le 4$" reduction holds only for **distinct-class** words until those collapse rules + a termination order + confluence are supplied (IX-REWRITE).

- Anomaly: `[PROVED]` tag without any recorded proof at this location.
  Verifier adjudication 2026-06-09: a `[PROVED]` tag with no proof body and no
  pointer to an actual proof artifact does not license PROVED-PROSE ("never
  stronger than the source supports") — status set to SKETCH (statement
  asserted, proof absent), consistent with [[ENC-0083]]/[[ENC-0087]]. The
  source tag is quoted verbatim under Provenance. Upgrading to PROVED-PROSE
  requires a recorded proof.

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §IV.5
  (statement copied verbatim; the §IV.5 blanket conditionality sentence and
  the IX-REWRITE blockquote are quoted under Notes). Original header line:
  `**Theorem IV.12 (Compression Rewrite Table Soundness).** [PROVED] Every admitted rewrite preserves declared semantics $\llbracket - \rrbracket$. Un-witnessed rules are refused, not silently applied.`

## Changelog

- 2026-06-09: ENC-0091 created (M2 E1 extraction).
- 2026-06-09: verification patch: status PROVED-PROSE → SKETCH (`[PROVED]` tag
  with no proof body does not license PROVED-PROSE; consistent with
  ENC-0083/ENC-0087).
