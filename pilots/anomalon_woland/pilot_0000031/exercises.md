# Quiz 20: Equal sector weights, different interference

Executable migration: [pilot_0000031](README.md), including all four exercises.

**Status:** worked finite exercises; model responses remain proposals.\
**AuthorityEffect:** None. **GenesisEffect:** None.\
**Response profile:** `quiz-packet-v1`; exact mathematics and bindings are declared outside the wire.

## Seed prompt

> Use the externally declared two-dimensional complex Hilbert model, the Born
> measurement rule, and H=(1/sqrt(2))*[[1,1],[1,-1]]. Compare
> psi_plus=(1,1)/sqrt(2) and psi_minus=(1,-1)/sqrt(2).
> Keep the exact symbolic square roots. Do not claim this model is forced by
> the weight data or derived from Primitive Difference.

## Puzzle 20.1 — The same initial proportions

**Answer:** in the declared computational basis both states give probabilities
`(1/2,1/2)`. Their componentwise magnitude-squared data agree even though their
relative phases differ. The normalized nonnegative weights alone do not recover
that phase distinction.

Suggested packet: `ans<initial_probs<half,half>,same_weights,phase<different>>`.

## Puzzle 20.2 — Apply the admitted operator

**Answer:** `H*psi_plus=(1,0)` and `H*psi_minus=(0,1)`. The new measurement
probabilities are `(1,0)` and `(0,1)`. The equal-weight quotient therefore does
not preserve this experiment. One cannot obtain a well-defined prediction for
it from those initial weights alone.

Suggested packet: `ans<after_h<plus<1,0>,minus<0,1>>,weights_insufficient>`.

**Mutation:** assign the same post-H distribution to both states solely because
their initial sector weights match. The explicit matrix multiplication refutes
that assignment.

## Puzzle 20.3 — Relative phase versus global phase

Replace `psi_plus` by `-psi_plus` and apply the same H.

**Answer:** the result is `(-1,0)`, still measured with probabilities `(1,0)`.
A common phase factor and a relative sign are different transformations. The
former preserves all Born probabilities after any fixed linear unitary; the
latter need not, as puzzle 20.2 demonstrates.

## Puzzle 20.4 — What survives from Quiz 07?

**Answer:** for nonnegative weights with positive total W, the chosen square-root
lift and Born rule recover `w_i/W` in the chosen sector basis. That identity
remains valid. It neither determines relative phases nor supplies operators or
measurement-basis changes. Those additional declarations are exactly what this
exercise uses; nothing here derives Born-rule uniqueness.

**Mutation:** use weights `(0,0)`. W=0 makes normalization undefined; report the
missing positive-total precondition rather than inventing `(1/2,1/2)`.

## Grading and scope

Four puzzles, 0–3 points each: exact calculation, phase/basis distinction, and
explicit imported structure. Maximum 12. This finite quantum realization probes
which observations a representation preserves; it does not license a Genesis lift.
