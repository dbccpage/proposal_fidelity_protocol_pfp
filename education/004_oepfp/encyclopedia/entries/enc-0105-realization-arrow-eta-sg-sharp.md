---
id: ENC-0105
kind: definition
name: "Realization Arrow eta_SG-sharp"
status: DEFINED
conditional_on: []
layer: symbol-game
tower_level: null
primitive: null
aliases: ["spine:X.1"]
sources:
  - "canonical_core_math_spine.md v1.5.2 §X.1 'Definition X.1'"
uses: []
lean_status: NOT-STARTED
lean_refs: []
extracted: 2026-06-09
migration: VERIFIED
---

# ENC-0105 — Realization Arrow eta_SG-sharp

## Statement

The Symbol-Game realization arrow is the Kleisli
arrow of the refusal monad $M(X)=X+\mathbb{F}$

$$
\eta_{SG}^\sharp : \mathsf{RawLLMOutput} \longrightarrow \mathsf{TypedCorePacket}+\mathbb{F},
$$

which produces a typed Core packet (or a typed refusal) from raw output. Under the
canonical pipeline $\Pi_S^\sharp$ (Def I.4) it is the **realize stage** $\eta^\sharp$
(`Realize in carrier representation`); the glyph $\eta$ here is the realize-stage name, NOT
the refusal-monad unit.

**Honest status — `[DEFINED]`, NOT a functor (PO-10 OPEN).** $\eta_{SG}^\sharp$ is a Kleisli
arrow, not a functor: it carries no input category and no proven identity/composition
preservation. The label "realization functor" is loose. Genuine input-category functoriality
(identity + composition preservation into $\mathbf{Kl}(M)$ over the admissible-equivalence
quotient hom-set) is the **undischarged obligation PO-10** (backlog §5; this section claims
no functoriality).

## Lean Obligations

| target | ref | blocker | status |
|---|---|---|---|
| type the realization arrow $\eta_{SG}^\sharp$ as a Kleisli arrow of the refusal monad $M(X)=X+\mathbb{F}$ (no functoriality claimed) | local | none identified | NOT-STARTED |

## Notes

- The source carries no status bracket on the header line; the honest-status paragraph
  inside the statement region declares `[DEFINED]` and records the open obligation PO-10
  (input-category functoriality, backlog §5). Status here is DEFINED accordingly; this
  entry claims no functoriality.
- The section heading reads "### X.1 The Realization Arrow $\eta_{SG}^\sharp$ (Kleisli
  arrow, NOT a functor)".

## Provenance

- Extracted 2026-06-09 from `canonical_core_math_spine.md` v1.5.2, §X.1
  (statement, including the source's honest-status paragraph, copied verbatim).
  Original header line:
  `**Definition X.1 ($\eta_{SG}^\sharp$).** The Symbol-Game realization arrow is the Kleisli`

## Changelog

- 2026-06-09: ENC-0105 created (M2 E1 extraction).
