# Round E0.5: predictions scored

AuthorityEffect: None.

The plaintext `E0_5_predictions.md` is byte-identical to the digest frozen in
`FROZEN_E0_5.json` (commit `f0ecdca7`). That commit touches no record, and it
precedes the Lean library and every E0.5 record. It is scored here without
editing it.

| id | verdict | evidence |
| --- | --- | --- |
| Q1 | HIT | `engine/lean/ExactRat`: `QN` is the quotient of numerator/denominator pairs by cross-multiplication. Proved: the commutative-ring laws, `mul_inv_cancel` and `inv_zero`, `instDecidableEq`, a decidable `<`, and the positive-cone laws (`pos_add`, `pos_mul`, `trichotomy`, `not_pos_and_pos_neg`) with `lt_trans`, `lt_trichotomy`, `add_lt_add_right` and `mul_pos`. All 49 reported declarations depend on at most `propext` and `Quot.sound` (`lean/axioms.txt`). |
| Q2 | HIT | The 15 kernel certificates in `payload/distance_form/lean/DistanceForm.lean` all check. `pos` passes both clauses; `own_neg` has its first non-positive minor at 2; `near_degenerate` at 3; `near_diagonal` fails only the diagonal; `mut` at 2. |
| Q3 | HIT | Level 005's status is `EXPECTED` and it has no missing component. `CAP-SUPPLIED` stays on both value clauses, and the native share stays 4 of 6. Clause evidence: the value clauses are `LEAN`, the relational clauses `COMPUTED`. |
| Q4 | HIT | I15 `FORBIDDEN TOKEN`, I16 `RR-AXIOM`, I17 `LEAN_BUILD_FAILED` (`INJECTIONS.md`); each recovers. |

Tally: 4 hits, no miss.

A finding made while building, not a prediction: core Lean's `grind` closes
the ring identities, but its proofs depend on `Classical.choice`. So the
library does not use it. It expands products by distributivity and closes
goals with `ac_rfl`, and uses `omega`, which treats products as atoms, for
the linear steps.
