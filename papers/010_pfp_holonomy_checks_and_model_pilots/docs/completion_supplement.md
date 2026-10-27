# Companion note: implementation and replay scope

PFP X, version 0.1.0, 2026-10-02. Source baseline:
`a623568eb0f853b968bc419bf06dfc6af256ab02`.

The [manuscript](../paper.md) states the claims; this note says what the package's
code does and does not do.

## What the code does

- `code/holonomy.py` reads a finite group from a full multiplication table and an
  inverse map and refuses the table unless the identity, inverse and associative
  laws hold. It builds $S_3$ from permutations and $Q_8$ from integer quaternions.
  It represents open and periodic square lattices and connections on them, computes
  path and plaquette products (reversed edges use inverses), applies gauge
  transformations, builds a spanning-tree gauge, decides `FLAT_TRIVIAL`,
  `FLAT_NONTRIVIAL` or `NOT_FLAT`, and checks a stated verdict and certificate.
- `code/replay_c017.py` runs the check on the five C017 case files in
  `code/data/c017/` and re-checks the model certificates in
  `code/data/c017/model_claims.json`.
- The tests in `code/tests/` cover the group constructions, the refusal of malformed
  input, the verdicts on trivial, gauge-trivial, flat nontrivial and non-flat
  connections, an exhaustive check over all pairs of seam elements in $S_3$ and
  $Q_8$, orientation and gauge behaviour, the identity-skipping remark, and the
  C017 replay.

## What the code does not do

- It makes no model or network call and does not repeat any model run.
- It does not rerun the C045 to C050 checkers. `code/recount_pilots.py` checks
  bundled source bytes and C017 extraction, recounts Table 3 flags, and checks
  Table 4 author categories and prior baseline counts. This is not fresh
  formal-checker execution.
- It builds only $S_3$ and $Q_8$ itself. A table for $\mathrm{SL}(2, \mathbb{F}_3)$,
  which the C017 specification also names, would be read like any other group
  table, but none of the retained runs used that group and the tests do not cover
  it.
- The Lean project formalizes only the remark of Section 2.3.

Run the checks from the package root as described in the [README](../README.md).

## Current publication review

The current execution record is `v01_review_2026_10_02.json`. The historical Lean
reports remain unchanged; this review did not run the pinned compiler. The
[Examiner companion](../_lev_examiner_theoretical_minimum_quiz/study_guide.md) includes
a separate key, 24 questions and `tools/study_capstone.py`, which reuses the host
and retained evidence. No provider calls or learner measurements were made.
