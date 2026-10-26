# Round E0.5 predictions (frozen before the Lean library or any E0.5 record)

- Q1. A Lean exact-rational type whose values are numerator/denominator pairs
  identified by cross-multiplication carries proved commutative-ring and field
  laws, decidable equality and a decidable strict order; every reported
  declaration depends on at most propext and Quot.sound (no Classical.choice).
- Q2. For level 005's value clauses, kernel evaluation in Lean agrees with the
  Python verdicts on all five evaluated fixtures: pos passes both clauses;
  own_neg fails the form at leading minor 2; near_degenerate fails it at
  minor 3; near_diagonal fails the diagonal clause only; mut fails the form at
  minor 2.
- Q3. Level 005 moves from UNRESOLVED to EXPECTED. Its value clauses stay
  decoded (CAP-SUPPLIED; native clauses stay 4 of 6); only their evidence
  rises, from Python computation to per-fixture Lean kernel certificates.
- Q4. Injections: a forbidden token in the library fails the Lean step; a
  declaration that uses Classical.choice fails the axiom audit with RR-AXIOM;
  a flipped expected verdict in a generated certificate fails the build.
