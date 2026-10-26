---
pattern_id: HP_MD_035
name: repeated_fill_returns_the_state
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_035_repeated_fill_raises
language: markdown
authority_effect: None
---

# Healthy Pattern: A Repeated Fill Returns The State (`HP_MD_035`)

## Description

If the chosen reading says a repeated filling changes nothing and is not a change, the function returns the same state. A refusal is a different reading and is named as a refusal.

## How To Construct

- Quote the reading and the return in the same sentence.
- When the triple is already filled, return the state that was passed in.
- If the implementation refuses, say refused, and do not describe the result as unchanged.
- Keep the error text from restating a no-op the function does not perform.

## Historical Limit

This repairs the split in the twenty-fifth state excerpt. It does not define `balances`, which that excerpt names and does not contain. It does not rerun the twenty-fifth derivation. `AP_MD_009` owns a nested pass on a failed exit. `woland-strict-input-pattern` owns a typed refusal at ingress. A refusal that is labeled as a refusal is not this defect.
