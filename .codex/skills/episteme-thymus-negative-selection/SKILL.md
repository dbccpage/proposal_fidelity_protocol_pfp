---
name: episteme-thymus-negative-selection
description: "Test candidate anti-skills and detector rules against a sealed panel of clean code and proofs; drop self-reactive ones."
families: [oecog, immune]
operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# episteme-thymus-negative-selection

**Status:** `CANDIDATE`  
**AuthorityEffect:** `None`  
**Council:** `L3_logos_episteme`

## When to use

Use before admitting any newly mined, learned, or proposed anti-skill, regex detector, or
filter rule into the circulating active repertoire. This gate subjects candidate rules to
central tolerance negative selection, verifying that they do not fire on healthy "self" code.

## Inputs

- `candidate_rule`: The proposed `DetectorRule` (containing regex pattern and target epitope).
- `self_panel`: Sealed fixture collection of clean, verified proofs, Clean Architecture ports,
  and canonical prompt dialogues.

## Protocol

1. **Thymic Challenge Scan**:
   - Compile the rule's regex pattern.
   - Execute regex against every clean self-panel fixture.
2. **Apoptosis on Violation**:
   - If the rule triggers on $\ge 1$ self fixture, immediately purge the rule (`is_admitted = False`).
   - Log the violating self-fixture snippet.
3. **Certification of Self-Tolerance**:
   - If zero self fixtures trigger, certify the rule as self-tolerant (`is_admitted = True`).

## References

- Detailed negative selection theory: [`references/negative_selection_protocols.md`](references/negative_selection_protocols.md)

## Nonclaims

Passing thymic negative selection supports that a rule is non-reactive against the specific
declared self-panel. It does not prove that the rule will never produce a false positive
on unseen out-of-distribution code.
