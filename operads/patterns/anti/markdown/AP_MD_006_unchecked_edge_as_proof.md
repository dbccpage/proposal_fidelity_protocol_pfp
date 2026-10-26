---
pattern_id: AP_MD_006
name: unchecked_edge_as_proof
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_006_scoped_edge_not_proof
language: markdown
authority_effect: None
---

# Anti-Pattern: Unchecked Edge As Proof (`AP_MD_006`)

## Description

Research-programme graph prose attributes a named theorem or certified guarantee to a paper, or it presents a missing path or a background pointer as a checked proof witness.

## Detection Signature

- A node or edge sentence names a Lyapunov theorem, a certified adaptive tolerance guarantee, or an operadic quantum/cochain dynamics bridge that the cited paper does not state.
- An evidence path that is absent on disk is still called a checked witness.
- A literature or background pointer is the only support for a proof-shaped sentence.
- A count of scoped reviewed edges is written as if it covered the unreviewed edges.

## Witness

Historical source, not a fresh graph inspection or a fresh DAG test: `C:\Users\a343o\source\repos\the_symbol_game\_ic\inr\omega_paper_reviews\po033_po034_po000_wdp_2026-10-11\review.md` (scoped review dated 2026-10-11, source baseline `cd6205a80`).

> The graph no longer attributes a Lyapunov theorem or certified adaptive tolerance guarantee to PO-033, or an operadic quantum/cochain dynamics bridge to PO-034.
>
> Eleven former evidence paths do not exist. They are preserved as unresolved pointers, not presented as checked witnesses. Existing literature or background pointers on other edges are not upgraded to proof evidence.
>
> Five edges have this scoped source review; fifteen are explicitly unreviewed research links.

`validation.json` in the same folder records the same limit: "DAG has 15 unreviewed relationships, including 11 missing former evidence paths; no whole-programme functor certification." `logs/paper-dag-tests.log` is a historical PASS of the repaired graph, not a fresh run.

## Hazard & Failure Mode

- A reader treats the diagram as a proof of Lyapunov stability, certified adaptive tolerance, or an operadic quantum bridge.
- A missing file is cited later as if this review checked it.
- Fifteen unreviewed links are inherited as certified by five scoped edges.

## Dual Healthy Pattern

See [HP_MD_006_scoped_edge_not_proof](../../helpful/markdown/HP_MD_006_scoped_edge_not_proof.md).
