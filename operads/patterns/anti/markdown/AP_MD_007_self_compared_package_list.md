---
pattern_id: AP_MD_007
name: self_compared_package_list
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_007_independent_closure_inventory
language: markdown
authority_effect: None
---

# Anti-Pattern: Self-Compared Package List (`AP_MD_007`)

## Description

A custody receipt or review treats agreement between a submitted package list and an inventory built from that same list as evidence that the local dependency closure is complete. Deleting a whole package deletes it from both sides, so the comparison still accepts.

## Detection Signature

- The packages inspected are the manifest list inside the receipt under test.
- Omitting every file of one local package, including its manifest, leaves both sides equal.
- That acceptance is reported as source-custody success.
- A later mathematical PASS is then read as if it had shown the inventory was sensitive.

## Witness

Historical. The current custody checker was not opened, and the cited reproduction was not rerun.

Source: `C:\Users\a343o\source\repos\the_symbol_game\_ic\inr\omega_paper_reviews\2026-10-06_glm_d\independent_review.md`

> A copied native build receipt omitted all 13 files under the local kernel package, including its manifest. `NativeCustody` accepted the copy. Its inventory loop used the submitted manifest list as the list of packages to inspect, so removing a whole package removed it from both sides of the inventory comparison. This is a source-custody defect, not a counterexample to the finite mathematics.

The same review says a later run on the retained pre-repair source accepted both the valid receipt and the omitted-dependency receipt. `README.md` in that folder summarizes the finding as receipt-selected dependency discovery that could omit an entire local package. Those execution records stay historical.

## Hazard & Failure Mode

- An incomplete local closure receives a custody acceptance.
- A reader treats that acceptance as evidence the binary was built from the declared package set.
- The bounded mathematical statement is neither established nor refuted by this acceptance.

## Dual Healthy Pattern

See [HP_MD_007_independent_closure_inventory](../../helpful/markdown/HP_MD_007_independent_closure_inventory.md).
