---
pattern_id: HP_MD_004
name: declared_family_acceptance
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_004_unfixed_comparison_class
language: markdown
authority_effect: None
---

# Healthy Pattern: Declared-Family Acceptance (`HP_MD_004`)

## Description

Acceptance is a statement about one declared finite family and one evidence record. The family is a parameter of the classifier. The claim does not choose it afterward by existential quantification.

## Construction

- Name a finite family $F$ and an evidence record $e$ in the acceptance notation.
- Keep the per-candidate verifier. Give the terminalizer the evidence, the family, and every member's receipt. Receipts include candidate identity and completeness, or those data are otherwise explicit in the domain.
- For complete inputs, let $A_{F,e}$ be the members of $F$ whose discrepancies lie inside the declared tolerances. State acceptance only as $A_{F,e}=\{s\}$.
- Call the result selection relative to that declared family and evidence. Keep that finite non-implication separate from any author-defined policy word such as "authority." Do not describe the label as exclusive physical authority, exhaustion of alternatives, or general empirical validity.

## Limit

- Fixing $F$ and $e$ as parameters, rather than as explicit arguments, is the same construction.
- A declared singleton is a legitimate input to that classifier. It does not show that competitors were removed by new evidence, and it does not show that the family exhausts alternatives.
- The selector replay and NO-GO verdict in `_ic/inr/core_paper_reviews/2026-10-08_representation_abundance_publication_review/review.md` are historical. This pattern does not claim that the current manuscript still omits the family or still uses an existential authority formula.
- Typing the classifier needs no new physics theorem. This pattern does not supply one.

## Dual Anti-Pattern

See [AP_MD_004_unfixed_comparison_class](../../anti/markdown/AP_MD_004_unfixed_comparison_class.md).
