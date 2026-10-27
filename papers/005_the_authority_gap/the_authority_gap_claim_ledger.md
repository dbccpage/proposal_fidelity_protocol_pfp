# Claim ledger: The Authority Gap

Jeremy H. Carroll · Version 2.1.0 · 2026-10-16

This ledger records the current claim scope. A definition, design contract, written proof, finite test, and Lean theorem are different evidence types. Historical IDs are retained; retired claims do not contribute to a current supported-claim fraction. No overall correctness percentage is assigned.

| ID | Current claim and location | Type and evidence | Limits |
| --- | --- | --- | --- |
| CLM-005-001 | Unsupported evaluation status, Definition 2.1 | Definition | No inference of intent to deceive. |
| CLM-005-002 | Evaluation packet, section 2.1 | Proposed contract | A packet and digest do not authenticate its source. |
| CLM-005-003 | Evaluator sovereignty | Historical policy ID, scoped by sections 1 and 5 | Not a mathematical impossibility theorem. |
| CLM-005-004 | Self-critique and independent checking, section 6 | Scope distinction | Self-critique may be correct; checking depends on a declared procedure. |
| CLM-005-005 | Scaling non-transfer | Retired as a separate theorem claim | No empirical scaling law is asserted. |
| CLM-005-006 | Benchmark non-transfer | Scope discussion, section 1 | No universal deployment-performance claim. |
| CLM-005-007 | Local acceptance need not imply global acceptance, Examples 3.2–3.3 | Finite counterexamples; Python `calculate_ngd`; Lean `hidden_bit_counts`, `unconditional_red_ratio` | Exact finite populations, not a measured deployment rate. |
| CLM-005-008 | NGD is conditional global-failure rate, section 3.1 | Definition; exact rational implementation | Undefined when no trial is locally accepted. |
| CLM-005-009 | Cohort, window, and rate ratios, section 3.3 | Definitions and accounting | A window ratio can exceed one; completed evaluations need not support claims. |
| CLM-005-010 | Conditional backlog growth, section 3.3 | Written accounting; Lean `backlog_positive`, `verified_share`; Python finite examples | Constant actual rates, no removal/duplication, enough queued work. The Lean domain is natural numbers. |
| CLM-005-011 | Exactness-fraud Boolean diagnostic, section 5 | Lean `missing_descent_is_refuted`, `nonzero_residual_is_refuted`, `scoped_residual_is_outside_this_rule` | Contract-level consistency only; no legal finding or independent authentication. |
| CLM-005-012 | Seven responsibilities, section 5 | Proposed design | Seven is not a necessary number of services or roles. |
| CLM-005-013 | Content/authority separation | Design discussion in sections 1 and 6 | No general tool-security or rollback theorem. |
| CLM-005-014 | Observer packet | Reference implementation schema | A schema cannot establish correspondence with the world. |
| CLM-005-015 | Zero NGD iff almost-sure acceptance soundness, Proposition 3.1 | Written conditional-probability proof | Positive accepted probability; pointwise equivalence needs positive mass at every point. Not mechanized in general. |
| CLM-005-016 | Zero NGD does not require boundary factorization, Example 3.4 | Written counterexample; `test_composition_boundary.py`; Lean `restricted_acceptance_zero_defect`, `global_evaluation_does_not_factor` | Two Boolean trials, constant boundary, fixed continuation. |
| CLM-005-017 | Positive dual pairing bounds repair residual, section 2.2 | Written weak-duality proof | Declared finite linear encoding; source transport needs a preservation hypothesis. |
| CLM-005-018 | Typed paper review fraction, Example 4.1 | Reporting contract and illustrative arithmetic | An inventory fraction is not probability of whole-paper truth. |

## Correction of the earlier composition equivalence

Former Lemma 7.1 claimed that zero NGD required boundary information sufficiency together with local/global soundness. Example 3.4 refutes the necessity of information factorization. The revised Proposition 3.1 states only the conditional-probability equivalence that its proof establishes. This is a mathematical correction, not merely a change in wording.

## Spine and formalization correspondence

The Markdown math spine records expressions and persistent UUIDs. Its JSON registry links every source occurrence; `docs/paper_inventory.json` records context and byte coverage. An expression is not a proposition without domain, hypotheses, and quantifiers. The Lean correspondence in this table is manually reviewed and scoped. No automatic LaTeX-to-Lean proof translation is claimed.

## Named regression entry points

These executable checks have the finite scopes described above; they do not establish whole-paper truth.

- `code/tests/test_composition_boundary.py::test_zero_ngd_does_not_require_boundary_information_factorization`
- `code/tests/test_proved_rows.py::test_proved_rows_call_shipped_checkers`
