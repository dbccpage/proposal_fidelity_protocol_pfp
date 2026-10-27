---
pattern_id: HP_MD_002
name: executable_listing_matches_source
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_002_prose_spaces_in_lean_listing
language: markdown
authority_effect: None
---

# Healthy Pattern: Executable Listing Matches Source (`HP_MD_002`)

## Description

A Lean listing offered as source or replay copies identifiers from an accessible source. Each namespace and qualified name is one token. Prose words, including words that contain spaces, stay outside the listing.

## Construction

- Copy namespace names, `end` names, and qualified names from the source bytes. Do not rewrite them as spaced exposition.
- Put short evidence and authority terms only in the surrounding prose.
- If the cited file does not resolve, say the listing is unavailable. Do not invent a spaceless namespace, toolchain, or axiom report.
- When a source is actually quoted, the listing and the replay command use the same identifiers.

## Example

The healthy listing is whatever single tokens the accessible file contains. It is not a cleaned paraphrase of this historical failure:

`namespace Residual Closure Layer`

`end Residual Closure Layer`

`CoreCore.Residual Closure Layer.residual_not_auth`

No substitute namespace is supplied here. The 2026-10-08 review says to restore identifiers from the source and not to guess one.

## Limit

- Matching a listing to source bytes is not a fresh Lean build. Lake was not run for this digest.
- An unresolved path or commit remains a separate receipt. It does not prove a historical build never happened, and it does not show that the current tree still contains these spaced identifiers.
- A narrower coproduct claim, and a refusal of overbroad prevention wording, belong to their existing owners. A faithful listing does not discharge those claims.
- Comments may be trimmed only when every executable token is unchanged and the block is labeled an excerpt, not a full verbatim replay.

## Dual Anti-Pattern

See [AP_MD_002_prose_spaces_in_lean_listing](../../anti/markdown/AP_MD_002_prose_spaces_in_lean_listing.md).
