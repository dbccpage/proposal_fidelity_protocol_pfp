---
documentation_contract: symbol-game-documentation/v1
title: "PFP II Landau theoretical minimum: worked instructor key"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/paper.md
---

# Worked instructor key: PFP II

**AuthorityEffect:** None. Attempt the [quiz](quiz.md) first. The key explains
the expected reasoning and a 100-point rubric. It is an educational companion
to the scoped proofs and implementation, not an additional publication claim.

## Q1. Declaration (6 points)

The carrier is the ordered finite vertices $(a,b,c)$ with the three
indexed undirected edges specified in the quiz. Coefficients are
$\mathbb Z_2$; allowed moves assign one sign to each vertex, equivalently
one bit $\alpha_v$. Acceptance requires
$\alpha_u\oplus\alpha_v=c_e$ on every edge.
Bit zero requires equal bits and bit one opposite bits.

A name or drawing supplies no face, orientation-dependent rational report,
or physical Hamiltonian. A bracket encoding needs an interpretation before
it denotes any of these objects.

**Credit:** carrier and edge identity 2; coefficients and moves 2;
acceptance equation and no undeclared structure 2.

## Q2. All gauges (6 points)

With $\alpha_a=0$, the first edge forces $\alpha_b=1$, and the second
forces $\alpha_c=0$. The closing edge checks $0\oplus0=0$.
The three equations are $0\oplus1=1$, $1\oplus0=1$, and $0\oplus0=0$.

Without root-fixing, the gauges are $010$ and $101$. XORing two valid
assignments gives a bit constant on each connected component, so these
are the only two on this connected graph. Each additional consistent
connected component supplies an independent global flip. In general a
consistent graph with $k$ components has $2^k$ gauges, including the
empty graph's one empty assignment.

**Credit:** rooted calculation and all edge checks 3; two gauges and
component freedom 3.

## Q3. Indexed obstructions (6 points)

For the modified triangle, use
`((0,a,b),(1,b,c),(2,c,a))`. It is continuous and closed, and its parity
is $1\oplus1\oplus1=1$. XORing the three endpoint equations would give
zero on the left and one on the right.

For one vertex $a$, a parity-one edge $a a$ has witness
`((0,a,a),)` and asks $\alpha_a\oplus\alpha_a=1$.
For two vertices, let edge 0 join $a,b$ with parity zero and edge 1
join them with parity one. The witness `((0,a,b),(1,b,a))` has parity one.
Distinct edge IDs are essential: the same undirected edge traversed out
and back contributes its bit twice and cannot be this obstruction.

Removing loops excludes a valid declared input and changes the grammar.

**Credit:** triangle witness and contradiction 2; loop 2; parallel-edge
witness and grammar distinction 2.

## Q4. Rational near miss (8 points)

The binary parity of $(1,1,0)$ is zero. Its rational cycle sum is two.
An exact potential would require
$$
(p_b-p_a)+(p_c-p_b)+(p_a-p_c)=0,
$$
so these rational reports are not exact.

If the changes are $\delta_0,\delta_1,\delta_2$, their sum must be $-2$.
The triangle inequality gives
$\sum_i|\delta_i|\geq|\sum_i\delta_i|=2$.
Change the closing report from zero to $-2$, leaving reports
$(1,1,-2)$. The potential $(p_a,p_b,p_c)=(0,1,2)$ attains this repair
with cost two. No two-dimensional filling was needed.

**Credit:** parity versus rational sum 2; telescoping obstruction 2;
lower bound 2; attaining reports and potential 2.

## Q5. Balance theorem and construction (10 points)

**Necessity.** XOR the endpoint equations around any closed walk, counting
occurrences with multiplicity. Every arrival matches a departure around
the closed walk, so the vertex terms cancel, including for a loop or a
repeated edge. The edge XOR must be zero.

**Sufficiency.** Choose a root in each component and set its bit to zero.
For each other vertex, define its bit as the parity of a root-to-vertex
path. Any two such paths give a closed walk by reversing the second, so
their parities agree. Append an edge $u v$ to a root-to-$u$ path;
path independence proves $\alpha_v=\alpha_u\oplus c_{uv}$.
This proves every edge equation. Isolated vertices are free; an odd loop
or disagreeing parallel edges contradict the premise directly.

Breadth-first construction stores adjacency, assigned bits, and tree
parents. Process each vertex and edge a bounded number of times. The
first conflicting edge plus the tree paths supplies a closed odd walk;
if none conflicts, return the assignment. Producing that one walk costs
at most linear extra work. Independent verifiers check the returned
witness. The resulting $O(|V|+|E|)$ algorithm is the baseline; enumerating
$2^{|V|}$ assignments exercises receipts rather than improving this
classification algorithm.

**Credit:** necessity 3; sufficiency with path independence and components 4;
constructive witnesses and linear versus exponential baseline 3.

## Q6. Matrix (8 points)

The graph bits for $a b,b c,c a$ are $1,1,0$, because the first two
matrix entries are positive and the third negative. Entrywise multiplication
gives
$$
DHD=\begin{pmatrix}0&-1&-1\\-1&0&-1\\-1&-1&0\end{pmatrix}.
$$
Multiplication by signs leaves zero unchanged, so a zero off-diagonal entry
imposes no constraint. The exact adapter refuses floats, nonsquare arrays,
and nonsymmetric arrays with an input-contract error; this is not an
odd-walk proof for a well-formed instance.

An all-positive triangle excludes diagonal vertex signs in the fixed basis.
It does not exclude an unrestricted global eigenbasis: every finite
Hermitian matrix has a unitary diagonalization. Finding and using that
basis can be computationally costly.

**Credit:** bits and computed matrix 4; zero and input refusals 2;
transformation boundary 2.

## Q7. Exponential (10 points)

Choose $a\geq\max_i H'_{ii}$. Then $B=aI-H'$ is entrywise
nonnegative: its off-diagonal entries are $-H'_{ij}\geq0$ and its
diagonal entries are $a-H'_{ii}\geq0$. Products of entrywise nonnegative
matrices remain entrywise nonnegative. Because $aI$ commutes with $B$,
$$
e^{-\beta H'}=e^{-\beta a}e^{\beta B}
=e^{-\beta a}\sum_{n=0}^{\infty}\frac{\beta^n B^n}{n!}.
$$
For $\beta\geq0$, all coefficients and the scalar factor are nonnegative.
In any submultiplicative matrix norm the terms are bounded by
$(\beta\|B\|)^n/n!$, whose sum converges. Thus the entrywise limit is
nonnegative. At $\beta=0$ it is the identity, so the statement is
nonnegativity, not strict positivity.

An efficiency claim needs a specified sampling procedure and its cost,
including relevant mixing or convergence behavior. Observable estimates
also require their preserved numerators and variance or error analysis.
Matrix-entry positivity alone supplies none of these guarantees.

**Credit:** correct shift and matrix powers 3; series identity and coefficients
3; convergence and beta-zero case 2; computational boundary 2.

## Q8. Two checks, then one (8 points)

| Call | Recorded candidate checks | Status | Witness | Remaining interval |
| --- | --- | --- | --- | --- |
| Initial budget 2 | `0:000 false; 1:001 false` | `UNKNOWN` | None | $[2,8)$ |
| Resume budget 1 | `2:010 true` | `GAUGE_VERIFIED` | Gauge $010$ | $[3,8)$ |

Candidate $000$ fails the first edge. Candidate $001$ also fails it;
it additionally disagrees with the closing parity. Candidate $010$
satisfies every edge equation. The resumed call starts at two and ends
at cursor three.

Verification of the second receipt requires the first UNKNOWN receipt,
bound to the same graph and key. Its earlier checks are replayed, and
the chain must begin at zero and reach the second start index without
gaps. The second segment is then checked, including its witness and digest.
A correct digest alone does not establish prior coverage.

**Credit:** initial trace 3; resumed trace 3; full prior-chain obligation 2.

## Q9. Continuation attacks (6 points)

Starting at two without prior receipts is refused: the verified prefix
cursor is zero. A caller-supplied count or frontier cannot supply coverage.
Flipping a verdict and rehashing is rejected when replay disagrees with
that verdict, even though the new digest matches the forged record.

Changing the basis changes the full presentation digest, so the old
receipt cannot certify continuation under the new key. Identical Hamiltonian
bytes are insufficient. The implementation also binds graph bytes and
checks checker version, transformation grammar, segment order, candidate
bits, verdicts, and frontier bounds.

A valid contiguous UNKNOWN chain beginning at zero supplies the prior
coverage. Retrieval compares the complete declared key but returns a
proposal; recheck its bits against the current graph. Neither successful
retrieval nor gauge verification proves that the declared physical adapter
preserves the Hamiltonian, measure, or observables.

**Credit:** missing prefix 2; rehashed false verdict 2; changed context and
retrieval/adapter boundary 2.

## Q10. Full batch and zero budget (6 points)

From zero with budget eight, the implementation completes all eight checks
in its first batch. The valid candidates are indices two ($010$) and five
($101$); it selects the first in canonical order, $010$. The status is
`GAUGE_VERIFIED`, cursor eight, and suffix $[8,8)$, an empty interval.
Finding a witness at index two does not make the cursor three for this call.

Workers one and four produce the same ordered checks, chosen witness, and
receipt. Scheduling does not enter the receipt's mathematical content.
Q8's smaller budgets limit its first batch to two checks and its next to
one, so its successful cursor is three.

An initial zero-budget call on this nonempty candidate space records no
checks, has no witness, returns UNKNOWN, and leaves $[0,8)$. It establishes
no negative result and supplies no advancing prefix for continuation.

**Credit:** witness, checks, and cursor 3; worker independence and Q8 contrast 2;
zero-budget limit 1.

## Q11. Pairing (4 points)

On a paired subset $P$, the map must take values in $P$ and satisfy
$I(I(x))=x$, $I(x)\ne x$, opposite signs, and equal magnitudes.
These give disjoint canceling two-element orbits; any unpaired survivors
must be assessed separately.

For $+2,-1,-1$, the total is zero but each negative magnitude is one
and the only positive magnitude is two. No required partner exists.
Regrouping both negative terms into a single contribution changes the
carrier and permitted operation.

For real finite beta and Hermitian $H$ on a nonzero finite-dimensional
space, $\operatorname{Tr}e^{-\beta H}=\sum_j e^{-\beta\lambda_j}>0$.
Pairing every term of an absolutely convergent expansion would instead
make its sum zero. Absolute convergence is needed to regroup infinitely
many terms this way.

**Credit:** map obligations 1; counterexample and regrouping boundary 2;
positive trace with convergence condition 1.

## Q12. Target path (8 points)

The modes are $(\uparrow0,\uparrow1,\uparrow2,\downarrow0,\downarrow1,
\downarrow2)$. Using zero-based mode indices:

| Hop | Changed modes | Occupied modes strictly between | Sign |
| --- | --- | --- | --- |
| `110;111 -> 101;111` | 1, 2 | 0 | $+1$ |
| `101;111 -> 011;111` | 0, 1 | 0 | $+1$ |
| `011;111 -> 110;111` | 0, 2 | 1 | $-1$ |

Each state has two doubly occupied sites, hence energy $2\cdot2=4$.
Including the final root again, the dwell times sum to $\beta$; the
integrand is the constant $e^{-4\beta}=e^{-1}$.
The ordered three-jump simplex has volume
$(1/4)^3/3!=1/384$. The sign product is negative, so the weight is
$-e^{-1}/384$.

There are 64 occupation states, but arbitrarily long closed hopping
sequences are possible. Repeating a nonzero two-hop out-and-back loop
already supplies unbounded lengths. Integrating times does not identify
these different state sequences.

**Credit:** hopping signs 3; energies and dwell-time integrand 2;
simplex and signed weight 2; finite states versus unbounded paths 1.

## Q13. All lengths (8 points)

For an $n$-hop sequence, $A$ is its positive time integral; each
nonzero hopping magnitude is one.

| Length | Bound or exclusion | Reason |
| --- | --- | --- |
| 0 | $A\geq e^{-3/2}$ | $E\leq6$, beta $1/4$ |
| 1 | No closed sequence | No diagonal hopping |
| 2 | $A\geq e^{-3/2}/32$ | Global energy bound and $\beta^2/2!=1/32$ |
| 3, positive | $A\geq e^{-1/2}/384$ | Enumerated positive paths have $E\leq2$ |
| $n\geq4$ | $A\leq\beta^n/n!\leq1/6144$ | $E\geq0$; ratio $\beta/(n+1)<1$ |

The target therefore satisfies
$$
\frac1{6144}<\frac{e^{-1}}{384}
<\frac{e^{-1/2}}{384},
\qquad
\frac{e^{-1}}{384}<\frac{e^{-3/2}}{32}<e^{-3/2}.
$$
The first lower comparison is $e^{-1}>1/16$; the short-path
comparisons follow from the stated strict rational enclosures, rather
than rounded decimal evaluations.

For $x\in[0,1]$, successive magnitudes in
$\sum_{k\geq0}(-x)^k/k!$ decrease and tend to zero. Odd truncations
bound $e^{-x}$ below; even truncations bound it above.
The checker encloses $e^{-1}$, $e^{-1/2}$, and $e^{-3/4}$.
Its positive lower bound for the last can be squared to bound
$e^{-3/2}$. Sufficiently tight rational bounds establish the strict
comparisons by fraction arithmetic.

This covers every length and excludes an individual positive path of
equal magnitude. It combines finite enumeration and analytic bounds.
The bound $1/6144$ concerns one sequence; multiplying by a sequence
count or proving convergence is required for a total-tail estimate.
Time-labelled maps, collective regroupings, other bases, and other
estimators require different arguments.

**Credit:** all five length classes and reasons 4; rational strict comparisons
and decreasing long bound 2; individual-path and representation boundaries 2.

## Q14. Audit (6 points)

One acceptable exact claim is: at the specified mode order and parameters,
the designated negative integrated rooted path has no positive individual
path of equal magnitude. Evidence is the Section 6 bounds plus
`code/exact_fock_gap.py` and
`code/tests/test_exact_fock_gap.py::test_exact_gap_covers_every_length_class`.
The execution receipt records what actually ran; neither test passage nor
the path obstruction classifies every physical representation.

| Proposed conclusion | Correct assessment |
| --- | --- |
| Two failures prove no gauge | UNKNOWN with the untested suffix; complete coverage or a directly verified odd walk is missing |
| The gap excludes every sign-free representation | It excludes the stated individual integrated-path pairing, under the fixed parameters |
| The manifest verifies mathematics | It checks hashes and file census; proofs and checkers address mathematical claims |
| Fallback verifies the native executable | It checks the Python route; native discovery may skip until a binary is built and exercised |

**Credit:** exact claim, domain, and named evidence 2; one point per corrected
conclusion 4. Retain the scoped result rather than demanding evidence for a
larger, unclaimed physical classification.
