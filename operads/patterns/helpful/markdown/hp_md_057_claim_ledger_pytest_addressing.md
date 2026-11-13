---
pattern_id: HP_MD_057
name: claim_ledger_pytest_addressing
category: helpful_pattern
operad_type: PatternMorphism
operad_source_colours: ["Code", "Witness"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
language: markdown
authority_effect: None
---

# Helpful Pattern: Claim Ledger Pytest Addressing (`HP_MD_057`)

## Description

In research paper claim ledgers (`<slug>_claim_ledger.md` and `<slug>_claim_ledger.yaml`), empirical and computational claims must link directly to sovereign executable test functions using explicit `test_<file>.py::test_<function>` identifiers.

## Pattern Definition

- Instead of citing test modules generally (e.g. `tests/test_spin_chains.py`), cite the exact test function name:
  `test_spin_chains.py::test_transverse_field_residual_scaling`.
- This enables automatic discovery, cross-reference auditing, and execution by the republication gate (Channel D check `D03`).

## Example Usage

```markdown
| Claim ID | Proposition | Status | Scope | Section | Support | Target |
| E4 | Theorem 5.1 | PROVEN | Exact Taylor remainder | §5.1 | `test_theorem_falsification.py::test_theorem_5_1_survives_randomised_search_inside_its_window` | None |
```

## Benefits

- Unambiguous traceability between paper claims and machine-checked pytest receipts.
- Satisfies Channel D check `D03` with 0 unresolved references.
