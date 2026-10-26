---
pattern_id: AP_MD_044
name: null_certificate_called_infinity
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_044_cost_sentence_quotes_stored_null.md
language: markdown
authority_effect: None
---

# Anti-Pattern: A Null Certificate Called Infinity (`AP_MD_044`)

## Description

A cost review says a same-free-report control reproduced infinite fixed and adaptive costs. The probe JSON it cites stores `null` for both values. The word infinity is not the stored certificate value.

## Detection Signature

- The review detail says the control reproduced costs 0 and infinity.
- The cited probe records `same_vector_different_free_report` costs `["0", "0"]` and `same_vector_same_free_report` costs `[null, null]`.
- The probe asserts `costs(equal_free) == [None, None]` and reads `finite_certificate` values.
- Seen in the historical folder `_ic/darpa/research/wdp_joint_report_costs`, round `wdp_joint_report_costs_20261009`.

## Hazard & Failure Mode

- A reader treats infinity as a stored number, or treats `null` as a missing run, and discards the control.
- A later summary drops `null` and reports only infinity, so the receipt and the sentence no longer match.

## Dual Healthy Pattern

See [HP_MD_044_cost_sentence_quotes_stored_null](../../helpful/markdown/HP_MD_044_cost_sentence_quotes_stored_null.md).
