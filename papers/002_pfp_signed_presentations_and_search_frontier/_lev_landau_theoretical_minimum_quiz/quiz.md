---
documentation_contract: symbol-game-documentation/v1
title: "PFP II theoretical minimum: signed certificates, search, and path pairing"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/paper.md
---

# Landau theoretical minimum: PFP II

**AuthorityEffect:** None. The [Apartment 50 preface](00_preface_at_apartment_50.md)
is fictional examination staging. Use the [study guide](study_guide.md) to
prepare and keep the separate [instructor key](instructor_key.md) closed
during an attempt. The [manuscript](../paper.md) defines the claims.

This is a written and oral problem set, not a historical Landau examination.
Show equations, witnesses, and the scope of each conclusion. Use exact
integers and fractions; numerical plots or a solver's verdict alone do not
replace the requested argument.

## Common instance and conventions

For Q1-Q4 and Q8-Q10, the ordered vertices are `(a,b,c)` and the
undirected edges are indexed as follows:

| Edge ID | Endpoints | Parity bit |
| --- | --- | --- |
| 0 | a, b | 1 |
| 1 | b, c | 1 |
| 2 | c, a | 0 |

The gauge equation is \(\alpha_u\oplus\alpha_v=c_e\). A walk step is
`(edge_id, departure, arrival)`. Multiple edges and self-loops are allowed.
An arrow in a walk records traversal; it does not make the edge directed or
attach a face.

The search uses all \(2^3=8\) assignments in zero-based lexicographic order:
`000,001,010,011,100,101,110,111`. Intervals are half-open: \([s,t)\)
includes \(s\) and excludes \(t\). Root-fixing in a proof does not change this
implemented search space.

## Level 0: Declare the question

**Q1. Carrier and move grammar (6 points).** Specify the carrier, coefficient
system, allowed transformation, and acceptance equation for the common
instance. What do bits zero and one require? Explain why a vertex name, a
bracket-wire encoding, or an unfilled graph drawing supplies no extra
mathematical structure.

## Level 1: Produce and attack a witness

**Q2. Gauge and its freedom (6 points).** Find a gauge with \(\alpha_a=0\)
and check all three equations. Find every gauge without that root condition.
Explain what changes if a second connected component is added.

**Q3. Three minimal failures (6 points).** Change edge 2 to parity one.
Give an indexed odd closed walk and prove that a gauge is impossible.
Then give an obstruction on one vertex and on two vertices joined by two
parallel edges. State the parity bits in each case. Explain why forbidding
loops would change the declared input grammar.

## Level 2: Prove the criterion and respect coefficients

**Q4. Same displayed numbers, different coefficients (8 points).** Instead
interpret the reports \((1,1,0)\) as rational numbers on the directed cycle
\(a\to b\to c\to a\), with an exact potential requiring
\(r_{uv}=p_v-p_u\). Compute the rational cycle sum and the binary parity.
Does a rational potential exist? Find the minimum uniform \(\ell^1\) change
to the three reports needed to make them exact, with both a lower bound and
an attaining repair. Do not import a filled triangle.

**Q5. Both directions of balance (10 points).** Prove that a finite graph
admits a gauge exactly when every closed walk has parity zero. Handle
disconnected components, loops, and parallel edges. Explain how a spanning
forest produces either witness in \(O(|V|+|E|)\), and why that algorithm is
the appropriate baseline for this grammar.

## Level 3: Transfer the witness to an exact matrix

**Q6. Work the adapter (8 points).** For
$$
H=\begin{pmatrix}0&1&-1\\1&0&1\\-1&1&0\end{pmatrix},
\qquad D=\operatorname{diag}(1,-1,1),
$$
derive the three graph bits and compute \(DHD\). Explain how zero
off-diagonal entries are treated. Give the input-contract response to a
float entry, a nonsquare matrix, and a nonsymmetric matrix. Does the
all-positive triangle obstruct an unrestricted global eigenbasis?

**Q7. Positivity without an efficiency claim (10 points).** Let \(H'\) be
a finite real symmetric stoquastic matrix. For \(\beta\geq0\), prove that
\(e^{-\beta H'}\) is entrywise nonnegative by choosing \(B=aI-H'\).
State why the series converges, what happens at \(\beta=0\), and what
additional evidence is needed before claiming efficient sampling or
low-variance estimates for observables.

## Level 4: Account for every tested candidate

**Q8. Exact frontier trace (8 points).** The common instance receives
budget two from cursor zero. List the tested assignments and their verdicts,
the receipt status, the witness field, and the remaining interval. Resume
with budget one and the first receipt. Give the new checks, status, witness,
and cursor. What does checking that second receipt require besides its own
digest?

**Q9. Adversarial continuation (6 points).** Explain the result of each
attempt: starting at index two with no prior receipts; flipping a recorded
verdict and recomputing its digest; reusing an old receipt after changing
the declared basis while retaining the Hamiltonian bytes. Name the evidence
that makes a valid continuation possible. Explain why an exact retrieval
key still does not certify a retrieved gauge or a physical adapter.

**Q10. Batches are part of the trace (6 points).** Run the common instance
from zero with budget eight. The implementation checks fixed batches of at
most eight and finishes a batch before stopping. Which witness is selected,
how many checks are recorded, and what is the cursor? Would workers one
and four change these answers? Contrast this with Q8 and state what a
zero-budget initial call establishes.

## Level 5: Check cancellation, not just the total

**Q11. Pairing obligations (4 points).** State the four requirements for a
sign-reversing equal-magnitude pairing on its paired subset. Explain why
the carrier with contributions \(+2,-1,-1\) has nonnegative total but no
positive equal-magnitude partner for either negative term. Does allowing a
collective regrouping ask the same question? Why can an absolutely convergent
thermal expansion of a nonzero finite-dimensional Hermitian system not have
every term canceled in such pairs?

## Level 6: Close the unbounded length argument

**Q12. Derive the target weight (8 points).** Use the six-mode order,
parameters, and hopping-sign rule of manuscript Section 6 for
$$
110;111\longrightarrow101;111\longrightarrow011;111
\longrightarrow110;111.
$$
Compute the three hopping signs, each visited energy, the simplex volume,
and the signed integrated weight. Explain why 64 occupation states do not
make the carrier of all rooted closed hopping sequences finite.

**Q13. Exclude a partner at every length (8 points).** Use the exact finite
facts: 192 rooted three-hop sequences, 96 positive and 96 negative; positive
three-hop paths visit energies at most two; all energies lie in \([0,6]\);
hops have magnitude one; and no one-hop closure exists. Derive the bounds
for lengths \(0,1,2,3,\geq4\) and the strict gap around
\(W_\star=e^{-1}/384\). Explain how alternating rational partial sums
certify the comparisons, why the long-path bound decreases, and why it
bounds one path rather than the total tail.

## Level 7: Defend the publication claim

**Q14. Evidence audit (6 points).** Write a short audit with one exact claim,
its declared domain, a relevant package test or checker, and the limit of
that evidence. Address these proposed conclusions:

- “Two failures prove there is no gauge.”
- “The path gap proves that this Hamiltonian has no sign-free representation.”
- “The manifest verifies the mathematics.”
- “A Python fallback test verifies the native executable.”

State the narrower conclusion, missing evidence, or refusal in each case.
Do not require a general physical adapter as a prerequisite for the already
scoped mathematical result.

## Scoring and oral defense

The points sum to 100. The key allocates partial credit to calculations and
arguments; a bare correct label receives no calculation or proof credit.
A score of at least 80 with no unresolved scope error is the instructional
competence target, not a validated learner metric.

After marking, defend three answers orally: Q5's sufficiency proof, Q8's
continuation, and Q13's all-length gap. Correct any promotion of UNKNOWN to
an obstruction, of a digest to truth, or of a restricted obstruction to a
general physical classification before recording mastery.
