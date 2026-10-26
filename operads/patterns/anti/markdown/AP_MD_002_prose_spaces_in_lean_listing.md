---
pattern_id: AP_MD_002
name: prose_spaces_in_lean_listing
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_002_executable_listing_matches_source
language: markdown
authority_effect: None
---

# Anti-Pattern: Prose Spaces In A Lean Listing (`AP_MD_002`)

## Description

A printed Lean listing replaces identifiers with prose words that contain spaces. The listing is not executable text: a namespace, `end` name, or qualified name is no longer one token.

## Detection Signature

- A block marked verbatim, replay, or source contains unescaped spaces inside a Lean namespace, `end` name, or dotted qualified identifier.
- Those spaced words are exposition vocabulary rather than the identifier in the cited source.
- Pasting the listing does not yield a legal Lean name. Guessing a spaceless namespace so the exposition looks cleaner is the same defect.

## Witness

Historical. This is the 2026-10-08 publication review, not a fresh compilation and not a reopened manuscript. Commit `c33fb25be7f7bb340eb7345d90134dc116bac244`. Source: `_ic/inr/omega_paper_reviews/2026-10-08_paper027_publication_review/review.md`.

> The “verbatim listing” contains:
> namespace Residual Closure Layer
> end Residual Closure Layer
> OmegaCore.Residual Closure Layer.residual_not_auth
> The unescaped spaces do not form the single namespace/qualified identifier required here. A prose vocabulary substitution has reached executable text.

The same review's missing paths and unresolved build receipt are not this witness. `AP_MD_001` owns advertised paths the package does not contain. This digest did not reopen the manuscript or run Lean.

## Hazard & Failure Mode

- A reader pastes the listing and the spaced name is rejected.
- Vocabulary cleanup is mistaken for a source edit. An invented namespace is unchecked proof text.
- The pointwise coproduct argument can stay valid while the printed listing cannot be replayed.

## Dual Healthy Pattern

See [HP_MD_002_executable_listing_matches_source](../../helpful/markdown/HP_MD_002_executable_listing_matches_source.md).
