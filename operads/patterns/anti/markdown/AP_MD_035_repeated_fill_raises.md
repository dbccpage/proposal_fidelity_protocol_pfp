---
pattern_id: AP_MD_035
name: repeated_fill_raises
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_035_repeated_fill_returns_the_state
language: markdown
authority_effect: None
---

# Anti-Pattern: A Repeated Fill Raises (`AP_MD_035`)

## Description

A chosen reading says that filling a triple which is already filled changes nothing and is not a change. The function in the same excerpt raises on that case, and the error text repeats the no-op sentence.

## Detection Signature

- The reading says the repeated act changes nothing.
- The function raises instead of returning the same state.
- The error text restates the no-op reading.

## Witness

Historical excerpt, not a fresh run. `_ic/darpa/research/briefs/sources/twentyfifth_state_lines_1_230.txt`. The module docstring, reading C-F1, says filling a triple already filled changes nothing and is not a change. `perform` raises `ValueError` with that same sentence when the triple is already in `fs.filled`. `balances` is named in `__all__` and is not defined in this excerpt. The companion paper excerpt ends inside the rank sentence. Nothing was rerun.

## Hazard & Failure Mode

- A later note cites the reading and treats the raise as the unchanged state.
- A caller that expected the same state receives an exception.

## Rationale

"Changes nothing" and "refused" are different outcomes. Putting the no-op sentence on the exception does not make the raise a no-op.
