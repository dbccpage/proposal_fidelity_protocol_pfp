# Paper 001 notebook learning worksheet

Teaching companion for the v0.1 preprint. Attempt each exercise before reading the answers below. All assessed arithmetic uses exact integers and fractions. The original Examiner examination remains the main course; these exercises connect its ideas to the actual notebooks and Lean source.

Examiner puts the three notebooks on the table. "A printed PASS is the beginning of your inspection, not the end. Tell me what was checked." This dialogue is fictional.

## Six exercises

### 1 Certify the second triangle

Demo 1 uses reports `(1,2,2)` and penalties `(1,2,2)`, in edge order `ab,bc,ca`. Compute the zero-potential cost. Find a potential with minimum cost, give its residual, and supply a balanced capacity-bounded dual with the same objective. Explain why its answer differs from the manuscript's `3`.

Hint: keep the last two reports exact and put the residual on the cheapest edge.

### 2 Protect the fractional potential

Change the reports to `(1,1/2,2)` while retaining penalties `(1,2,2)`. Construct a matching primal/dual pair. Convert your potential values with `int(v)` and recompute the cost. Explain what information was lost and replace the notebook's proposal serialization with an exact alternative.

Hint: the two non-cheapest edges force `s_c=-2` and `s_b=-5/2` when `s_a=0`.

### 3 Four laws are not coverage

The host declares weights `n1=-1/2`, `p1=1/2`, `n2=-3/4`, and `residue=2`. A proposer pairs `n1` with `p1` and leaves the other IDs unpaired.

Check involution, absence of fixed points, sign reversal, and equal magnitude on that paired subset. Should the gate admit this as a cancellation certificate for the whole host carrier? Repair the host example by adding one positive weight and extending the pairing. What weight remains after cancellation?

Hint: inspect `negative_coverage` separately from the four pair laws.

### 4 Read the Lean hypotheses

In `InvolutionLaws.lean`, identify the four fields of `InvolutionWitness`. Which two are actually used by `pair_cancellation`? Does this theorem exhibit a physical involution or establish a global finite-carrier sum? Is the type `SignedConfig` finite?

Challenge: explain why a two-term cancellation calculation is weaker than a proof that a finite carrier is partitioned into valid pairs.

### 5 Inspect the policy theorem

`AuthorityEffect` has a single constructor, `none`. The theorem accepts a packet and a premise that it was admitted. Does the proof use that premise? Could the packet type represent an admitted packet with a different authority effect? State a stronger proposition that follows from the type definition, and name the separate runtime obligation.

Hint: look at `cases p.authority`, then inspect the constructors.

### 6 Audit the debate receipt

The ten stored trials have TP=6, FP=2, TN=2, and FN=0 against historical verifier labels. Compute precision, recall, and accuracy as fractions. On fresh replay, the current gate refuses all ten proposals. Does either result establish physical ground truth or show the proposer false?

The recovered source trace has CRLF line endings. Its raw hash differs from the notebook's recorded hash, but converting only CRLF to LF in an isolated copy exactly recovers that recorded hash. Explain what this establishes, what should remain unchanged, and which bytes a release receipt must identify.

## Worked answers

### 1 Second triangle

The zero-potential residual is `(1,2,2)`, so the cost is `1+4+4=9`. Potential `(0,-4,-2)` has fitted differences `(-4,2,2)` and residual `(5,0,0)`, costing `5`. The dual `(1,1,1)` is balanced, fits capacities `(1,2,2)`, and has objective `1+2+2=5`. Equal bounds give the minimum `5`. The manuscript uses different reports and weights; it is a separate minimum-3 instance.

### 2 Fractional potential

Potential `(0,-5/2,-2)` has differences `(-5/2,1/2,2)` and residual `(7/2,0,0)`, costing `7/2`. The feasible unit circulation has objective `1+1/2+2=7/2`.

Integer conversion truncates `-5/2` toward zero, giving `(0,-2,-2)`. Its residual is `(3,1/2,0)`, costing `3+2(1/2)=4`. The conversion loses a half-unit in the potential.

Use integer/fraction strings at the proposal boundary:

```python
good_cut = gov.execute_move(
    MoveType.CUT,
    {"potentials": {k: str(v) for k, v in best_pot.items()}},
)
```

This preserves exact values, including after rational edits. For a complete lesson, obtain the primal/dual certificate and verify its coverage, balance, capacities, and matching objectives. A computed minimum and a zero obstruction remain different claims.

### 3 Coverage

The supplied pair satisfies all four laws on `{n1,p1}`. It fails negative coverage because `n2` is an unpaired negative weight. The current gate refuses it. Add `p2=3/4` and pair `n2` with `p2` in both directions. Both pairs cancel, leaving the nonnegative residue `2`. Do not invent an undeclared weight in a real host carrier: this repair is a new host-owned toy example, not authorization for a proposer to alter the original instance.

### 4 Conditional pair theorem

The fields are `involution_law`, `fixed_point_free`, `sign_reversing`, and `weight_preserving`. The arithmetic proof uses the latter two. It assumes a supplied witness; it does not construct one for a physical representation.

`SignedConfig` has natural-number IDs and weights and therefore is not a finite type. The theorem adds two terms, not a total carrier sum. A global pair-partition result needs a declared carrier, closure and involution evidence, and coverage of the configurations whose signs are being canceled. The Python finite gate additionally checks that every negative host weight is covered and that the unpaired residue is nonnegative.

### 5 By construction

The admission premise `_h` is unused. Every packet representable by this type has authority `none`, regardless of its admission Boolean. The stronger proposition is `for every p : PacketEnvelope, p.authority = AuthorityEffect.none`. The single-constructor definition gives this equality; it cannot establish that a separate runtime never performs an authorized external action. That requires a correspondence between the implementation, its transitions, and the stated policy.

### 6 Labels and custody

Precision is `6/(6+2)=3/4`, recall is `6/(6+0)=1`, and accuracy is `(6+2)/10=4/5`. These quantities describe agreement with historical labels. Ten present refusals establish that the proposals do not meet the current checks; refusal is not a theorem that the proposed physical conclusion is false. Neither set of labels is independent physical ground truth.

The line-ending conversion recovers the exact byte stream named by the stored hash. Preserve the original source and describe the recovered copy. A receipt must hash the actual bytes it claims to identify; mathematical equivalence of parsed records does not make two byte streams identical. No live model call is needed to replay this deposited trace.
