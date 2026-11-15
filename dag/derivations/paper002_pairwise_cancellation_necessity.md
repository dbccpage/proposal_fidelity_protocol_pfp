# PAPER002-PAIRWISE-CANCELLATION-NECESSITY: Pairwise Cancellation Necessity

AuthorityEffect: None.

- Archive claim: [ATL-P002-008](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("Equal-weight cancellation requires a closed involution, opposite signs, and equal magnitudes.", [paper_claim_ledger.md:23](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L23))
- Audit derivation node: [PAPER002-PAIRWISE-CANCELLATION-NECESSITY](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER002-PAIRWISE-CANCELLATION-NECESSITY`)
- Review verdict: `matched` (`states_same_claim_as`)

## 1. Claim Statement

Exact pairwise cancellation of a signed multiset into equal-weight zero-sum pairs requires a fixed-point-free involution pairing opposite signs with equal magnitudes; a nonnegative total sum alone does not suffice, as demonstrated by the counterexample multiset {+2, -1, -1}.

## 2. Context & Hypotheses

- **Finite Signed Carrier**:
  A discrete carrier $\Omega$ with weights $A(x) > 0$ and signs $\sigma(x) \in \{-1, +1\}$, defining the sum:
  $$Z = \sum_{x \in \Omega} \sigma(x) A(x).$$
- **Pairwise Cancellation Map**:
  A sub-carrier $P \subseteq \Omega$ and a mapping $I: P \to P$.
- **Cancellation Conditions**:
  1. $I(I(x)) = x$ (involution)
  2. $I(x) \ne x$ (fixed-point-free)
  3. $\sigma(I(x)) = -\sigma(x)$ (sign reversal)
  4. $A(I(x)) = A(x)$ (magnitude preservation)

## 3. Derivation / Evidence

### 3.1 Sufficiency of Equal-Weight Involution
Because $I$ is an involution without fixed points, the elements of $P$ partition into disjoint unordered pairs $\{x, I(x)\}$. For each pair:
$$\sigma(x) A(x) + \sigma(I(x)) A(I(x)) = \sigma(x) A(x) + (-\sigma(x)) A(x) = 0.$$
Summing over all disjoint pairs:
$$\sum_{x \in P} \sigma(x) A(x) = \sum_{\{x, I(x)\} \subseteq P} [\sigma(x) A(x) + \sigma(I(x)) A(I(x))] = 0.$$
If every remaining element $y \in \Omega \setminus P$ has positive sign $\sigma(y) = +1$, the residual sum is nonnegative:
$$Z = \sum_{y \in \Omega \setminus P} \sigma(y) A(y) = \sum_{y \in \Omega \setminus P} A(y) \ge 0.$$

### 3.2 Necessity of Sign Reversal and Magnitude Equality
Suppose a finite multiset of non-zero real signed contributions $S$ can be partitioned into disjoint zero-sum pairs $S = \bigsqcup_k \{a_k, b_k\}$ with $a_k + b_k = 0$:
1. For each pair, $b_k = -a_k$.
2. Because $a_k \ne 0$, $b_k$ and $a_k$ have opposite signs: $\operatorname{sgn}(b_k) = -\operatorname{sgn}(a_k)$.
3. Taking absolute values, $|b_k| = |-a_k| = |a_k|$.
4. Defining $I(a_k) = b_k$ and $I(b_k) = a_k$ specifies a fixed-point-free involution that reverses signs and preserves magnitudes.
Thus, zero-sum pairwise partition requires opposite signs and equal magnitudes.

### 3.3 Counterexample to Nonnegative Total Sufficiency
Consider the signed multiset:
$$S = \{+2, -1, -1\}.$$
1. **Total Sum**:
   $$\sum_{w \in S} w = (+2) + (-1) + (-1) = 0 \ge 0.$$
   The total sum is nonnegative (in fact, exactly zero).
2. **Cardinality Obstruction**:
   The cardinality $|S| = 3$ is odd. Any partition into 2-element pairs requires an even number of elements.
3. **Magnitude Mismatch**:
   Even if searching for a partial pairing $P \subset S$ to cancel negative terms:
   - The negative terms are $-1$ and $-1$.
   - Canceling either $-1$ in a zero-sum pair requires a positive counterpart of weight $+1$.
   - The only positive element in $S$ is $+2 \ne 1$.
   - Therefore, no equal-weight zero-sum pair can be formed from $S$.
This demonstrates that a nonnegative total sum alone does not imply the existence of an equal-weight pairwise cancellation certificate.

### 3.4 Thermal Partition Function Obstruction
For any Hermitian Hamiltonian $H$ on a finite-dimensional Hilbert space and real finite $\beta$:
$$\operatorname{Tr}(e^{-\beta H}) = \sum_i e^{-\beta \lambda_i} > 0.$$
A complete equal-weight pairwise cancellation of the full expansion would force the total sum to equal 0, which contradicts $\operatorname{Tr}(e^{-\beta H}) > 0$. Hence complete equal-weight pairwise cancellation is obstructed for thermal partition functions.

## 4. Limits and Non-Claims

- **Pairwise (2-Term) Scope**:
  Applies to pairwise equal-weight involution certificates. It does not rule out multi-term regroupings ($k \ge 3$) where several terms sum to zero.
- **No Algorithmic Complexity Claim**:
  Does not evaluate polynomial-time tractability of finding general cluster cancellations.
- **Finite Setting**:
  Formulated for finite multisets and discrete state expansions.

## 5. Claim Hygiene Summary

1. **What it supports**:
   Supports the mathematical necessity of opposite signs, equal magnitudes, and fixed-point-free involution for exact zero-sum pairwise cancellation; supports that nonnegative total sum is insufficient via counterexample {+2, -1, -1}; supports obstruction to complete cancellation for thermal partition functions.
2. **What it does not support**:
   Does not rule out multi-term regroupings or establish computational complexity for general cluster cancellations.
3. **Narrowest defensible claim**:
   Zero-sum pairwise partitioning requires opposite signs and equal magnitudes; nonnegative total does not imply pairability due to the {+2, -1, -1} counterexample.
4. **Next test needed**:
   Testing higher-order 3-term and cluster cancellation verification routines.

## 6. Cross-References & Provenance

- Archive Claim: [ATL-P002-008](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP002-08](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L23)
- Manuscript Source: Section 5 ("What an equal-weight pairing must establish")
- Verification Test: `tests/test_paper_002_search_trace.py`
