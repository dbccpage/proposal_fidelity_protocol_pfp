---
documentation_contract: symbol-game-documentation/v1
title: "PFP II study guide: from a sign equation to a scoped obstruction"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - omega_engine_atlas/coda_atlas/omega_engine_pfp/002_pfp_signed_presentations_and_search_frontier/paper.md
---

# Study guide: PFP II

**AuthorityEffect:** None. Start with the fictional
[Apartment 50 preface](00_preface_at_apartment_50.md). This guide prepares the
[14-problem quiz](quiz.md); complete an attempt before opening the separate
[worked instructor key](instructor_key.md). All required readings and checks
are included in this deposit.

## What you need and what you should be able to do

Prerequisites are addition modulo two, finite graph walks, matrix
multiplication, exact fractions, a spanning-tree argument, factorials, and
the power series for the exponential. For the Fock example, use the
manuscript's explicit occupation and hopping rules; no prior many-body
simulation experience is required. Review those rules before attempting the
integration and length bounds.

By the end, produce and independently check both witness types; derive the
matrix adapter; distinguish a complete classifier from an unfinished
enumeration; replay a contiguous receipt chain; and explain exactly which
pairing operation the Fock example excludes.

## Notation and the objects being checked

| Object | Meaning | Typical mistake |
| --- | --- | --- |
| $c_e\in\mathbb Z_2$ | An edge's endpoint constraint | Treating XOR as rational addition |
| $\alpha_v$ | A vertex bit; sign $(-1)^{\alpha_v}$ | Assuming the chosen root removes candidates from the implementation |
| Odd closed walk | Indexed traversals, closure, parity one | Checking parity without adjacency or closure |
| Exact matrix | Integers or `Fraction` values in a fixed basis | Silently rounding a floating input |
| Presentation key | Full declared context for retrieval and replay | Matching only the Hamiltonian digest |
| Receipt frontier $[s,t)$ | The suffix outside the recorded checks | Treating an unfinished suffix as a negative proof |
| Integrated rooted path | A state sequence whose jump times were integrated out | Equating finite state count with finite sequence count |

An arrow records a traversal in a walk. A graph edge does not attach a
two-dimensional cell. A bracket-wire encoding, if used, needs its own
declared interpretation and parsing rules.

## Route through Levels 0-7

| Level | Read in the manuscript | Practice | Completion check |
| --- | --- | --- | --- |
| 0 | Sections 1-2 | Q1 | State the carrier and exact move grammar |
| 1 | Section 2 | Q2-Q3 | Check a gauge and construct indexed obstructions |
| 2 | Section 2 | Q4-Q5 | Separate coefficients and prove both directions |
| 3 | Sections 1 and 3 | Q6-Q7 | Compute $DHD$ and prove exponential positivity |
| 4 | Section 4 | Q8-Q10 | Account for cursor, batch, key, and prior coverage |
| 5 | Section 5 | Q11 | Check an actual pairing map, not just its sum |
| 6 | Section 6 | Q12-Q13 | Derive the target and cover every length class |
| 7 | Sections 7-8 and the claim ledger | Q14 | Match an exact claim to its evidence and limit |

## 1. Local equations and the global witness

Practice first on a tree: root one vertex at zero and propagate its bits.
There is no cycle constraint to violate. Add a closing edge and compare the
required endpoint bit with the propagated bit. A disagreement supplies an
odd closed walk through the tree.

For a gauge, check every edge equation, including loops and repeated
endpoints. For an obstruction, check every edge ID and endpoint, continuity
between steps, final closure, and the XOR of its bits. Reversing a traversal
does not change a binary edge bit. Give each parallel edge its own identity.

Then change coefficients. Rational reports on an oriented cycle require a
telescoping sum of zero. Modulo-two parity can vanish while that rational
sum does not. Keep the coefficient system and allowed report repairs in
the statement.

## 2. The matrix bridge

The adapter assigns a bit one to a positive nonzero off-diagonal entry
and zero to a negative one. This bit is the constraint needed to make the
transformed matrix entry negative; the graph sign $(-1)^{c_e}$ follows
that convention. Zero entries impose no equation.

Compute an entry of $DHD$ as $D_{ii}H_{ij}D_{jj}$ before applying a
general rule. A successful gauge proves stoquasticity under those diagonal
signs in the declared basis. Other basis changes require a different grammar.

For exponential positivity, shift the diagonal so $B=aI-H'$ is
entrywise nonnegative. Powers of $B$ remain nonnegative, and the convergent
power series gives the result for nonnegative $\beta$. This establishes
matrix-entry positivity; sampling cost and observable-estimator variance
require additional analysis.

## 3. Complete classification and incomplete search

The graph classifier is linear in the finite input size. Exhaustive
enumeration is retained to exercise a protocol for future grammars; its
worst-case candidate count is exponential.

| Search status | Evidence required | What follows |
| --- | --- | --- |
| `GAUGE_VERIFIED` | A gauge passes all equations | That gauge works in this grammar |
| `UNKNOWN` | The recorded segment has no valid gauge and a suffix remains | Continue only with a verified prior prefix |
| `RESTRICTED_OBSTRUCTION` | Replayed exhaustive coverage and a checked odd walk | No vertex gauge exists for this graph |

The direct graph classifier can supply an odd walk without exhaustive
enumeration. The search function issues its restricted terminal status
only after its own finite grammar is exhausted.

For the three-vertex example the implementation has eight candidates,
indexed zero through seven, even when a proof fixes a root. Track
`start_index`, ordered checks, `next_index`, and `stop_index`.
The cursor advances by the full consumed batch, not necessarily to one
past the first valid candidate.

A digest binds bytes; replay checks their asserted equations. Continuation
requires a contiguous chain of UNKNOWN segments beginning at zero, with
the same graph and presentation digests. Changing the basis, grammar,
estimator, adapter, or another key field changes the declared context.
A retrieved bit vector must be checked again even after a full-key match.

## 4. Cancellation and the infinite family of lengths

A pairing is a map on a closed paired subset. Check involution,
absence of fixed points, opposite signs, and equal magnitudes. Separate
unpaired survivors from that subset. A nonnegative total does not by
itself supply a pairing.

For the Fock example, keep the six-mode order fixed. Count occupied modes
strictly between a hop's endpoints for its sign and doubly occupied sites
for its energy. A constant-energy three-hop sequence has magnitude
$e^{-\beta E}\beta^3/3!$.

The proof has two different parts: exact enumeration establishes the
special facts for length three, while inequalities cover every other
length. For $n\geq4$, use

$$
\frac{\beta^{n+1}/(n+1)!}{\beta^n/n!}=\frac{\beta}{n+1}<1
\quad(\beta=1/4).
$$

This controls an individual sequence. Counting and summing many sequences
is a separate task.

For $x\in[0,1]$, odd truncations of the alternating series for $e^{-x}$
are lower bounds and even truncations are upper bounds. Compare rational
enclosures instead of rounded decimals. The target lies above every
long-path upper bound and below every relevant positive short-path lower
bound, excluding an equal-magnitude partner.

## 5. Replay the package and describe the evidence

From the package root, use the [README commands](../README.md#running-the-checks).
On Windows use `py -3.12`; elsewhere substitute your Python 3.12 interpreter.
The runtime checkers use the standard library. Tests require pytest;
notebook replay additionally requires nbclient, nbformat, and ipykernel.

| Replay | Supports | Does not establish |
| --- | --- | --- |
| `code/tests/test_sign_graph.py` | Input and signed-witness checks | A new graph theorem |
| `code/tests/test_manuscript_examples.py` | Displayed matrix and 2-then-1 search trace | General physical adapter validity |
| `code/tests/test_frontier_search.py` | Coverage, ordering, key, and snapshot controls | Sampling speedup |
| `code/exact_fock_gap.py` and its test file | Exact counts and rational gap checks | Exclusion of every representation |
| Native-adapter tests | Adapter behavior; fallback if no executable exists | A native build when binary discovery skips |
| Fresh notebook replay | The deposited notebook executes under the recorded environment | Independent experimental data |
| `verify_deposit.py` and release ZIP check | File census, hashes, archive identity | Truth of a theorem |

The [claim ledger](../paper_claim_ledger.md) maps the paper's statements to
proofs and named checks. Consult the current dated review receipt for actual
execution, versions, and skips; historical counts keep their original scope.

## Finish with a defense

Complete the quiz, mark it against the separate key, and write down the
reason for each error: wrong carrier, wrong coefficients, invalid witness,
missing coverage, or overextended claim. Rework the associated example
before the oral defense. The score and mastery target are teaching
conventions; no learner study or automatic authority is claimed.
