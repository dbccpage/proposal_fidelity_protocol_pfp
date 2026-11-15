# PAPER002-WORKED-FRONTIER-TRACE: Worked Frontier Trace

AuthorityEffect: None.

- Archive claim: [ATL-P002-007](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("The introductory matrix accepts gauge 010; its first two candidates fail, so a budget of two ends UNKNOWN with interval [2, 8) and a resumed budget of one verifies 010 at index 2.", [paper_claim_ledger.md:22](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L22))
- Audit derivation node: [PAPER002-WORKED-FRONTIER-TRACE](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER002-WORKED-FRONTIER-TRACE`)
- Review verdict: `matched` (`states_same_claim_as`)

## 1. Claim Statement

For the introductory matrix, candidates 000 and 001 fail, budget 2 yields UNKNOWN with interval [2, 8), and resume with budget 1 verifies gauge 010 at candidate index 2.

## 2. Context & Hypotheses

- **Matrix Carrier**:
  The introductory 3-state real symmetric matrix $H_{\text{run}} \in \mathbb{R}^{3 \times 3}$:
  $$H_{\text{run}} = \begin{pmatrix} 0 & 1 & -1 \\ 1 & 0 & 1 \\ -1 & 1 & 0 \end{pmatrix}.$$
- **Declared Basis & Grammar**:
  The transformation grammar is diagonal sign transformation ($s_i \in \{-1, +1\}$), parameterized by binary bits $b_i \in \{0, 1\}$ via $s_i = (-1)^{b_i}$.
- **Candidate Ordering**:
  Candidates are evaluated in lexicographic bit-string order:
  `000`, `001`, `010`, `011`, `100`, `101`, `110`, `111`.
  Total candidate space size is $2^3 = 8$.
- **Off-Diagonal Stoquastic Condition**:
  A candidate gauge $s$ satisfies the condition if $s_i H_{ij} s_j \le 0$ for all off-diagonal pairs $i < j$.

## 3. Derivation / Evidence

### 3.1 Endpoint Sign Equations
For matrix $H_{\text{run}}$, the off-diagonal entries are:
- $(0, 1)$: $H_{01} = 1 > 0$, requiring $s_0 s_1 \le -1 \implies s_0 s_1 = -1$.
- $(0, 2)$: $H_{02} = -1 < 0$, requiring $s_0 s_2 (-1) \le 0 \implies s_0 s_2 = +1$.
- $(1, 2)$: $H_{12} = 1 > 0$, requiring $s_1 s_2 \le -1 \implies s_1 s_2 = -1$.

### 3.2 Evaluation of Candidate 0 (`000`)
- Bits: $(b_0, b_1, b_2) = (0, 0, 0) \implies s = (+1, +1, +1)$.
- For $(0, 1)$: $s_0 s_1 H_{01} = (1)(1)(1) = 1 > 0$ (fails condition).
- Check outcome: `(0, (0, 0, 0), False)`.

### 3.3 Evaluation of Candidate 1 (`001`)
- Bits: $(b_0, b_1, b_2) = (0, 0, 1) \implies s = (+1, +1, -1)$.
- For $(0, 1)$: $s_0 s_1 H_{01} = (1)(1)(1) = 1 > 0$ (fails condition).
- For $(0, 2)$: $s_0 s_2 H_{02} = (1)(-1)(-1) = 1 > 0$ (fails condition).
- Check outcome: `(1, (0, 0, 1), False)`.

### 3.4 Bounded Search with Budget 2
- With `node_budget = 2`, the search checks indices 0 and 1 and exhausts its budget.
- Returns `status = "UNKNOWN"`, `witness = None`, and `frontier = (next_index=2, stop_index=8)`.

### 3.5 Resumption with Budget 1
- Resuming from frontier `[2, 8)` with `node_budget = 1` and supplying prior receipt:
- Evaluates Candidate 2: $(b_0, b_1, b_2) = (0, 1, 0) \implies s = (+1, -1, +1)$.
  - $(0, 1)$: $(1)(-1)(1) = -1 \le 0$ (satisfied).
  - $(0, 2)$: $(1)(1)(-1) = -1 \le 0$ (satisfied).
  - $(1, 2)$: $(-1)(1)(1) = -1 \le 0$ (satisfied).
- All off-diagonal entries are nonpositive.
- Returns `status = "GAUGE_VERIFIED"`, `checks = [(2, (0, 1, 0), True)]`, and `witness = GaugeWitness(vertices=('0', '1', '2'), bits=(0, 1, 0))`.
- Receipt verification confirms that `verify_search_receipt` succeeds when the prior receipt is included and fails when it is omitted.

## 4. Limits and Non-Claims

- **Fixed Matrix and Order Only**:
  The trace applies specifically to $H_{\text{run}}$ under lexicographic bit ordering.
- **Protocol Illustration, Not General Algorithm**:
  Brute-force candidate enumeration is an illustrative protocol for frontier resumption and receipt chaining; it does not replace $O(|V|+|E|)$ BFS or GF(2) parity classification on general graphs.
- **No Physical Sign-Problem Elimination**:
  Finding a sign gauge for this 3-state matrix does not eliminate fermion sign problems in arbitrary physical Hamiltonians.

## 5. Claim Hygiene Summary

1. **What it supports**:
   Supports the precise search trace of $H_{\text{run}}$: candidate 000 and 001 fail off-diagonal nonpositivity; budget 2 returns UNKNOWN with interval [2, 8); and resumed budget 1 verifies gauge 010 at candidate index 2.
2. **What it does not support**:
   Does not support polynomial-time search on general graphs or physical sign-problem elimination for arbitrary quantum models.
3. **Narrowest defensible claim**:
   Under lexicographic gauge enumeration on $H_{\text{run}}$, candidates 0 and 1 fail, budget 2 halts at UNKNOWN on [2, 8), and resuming with budget 1 identifies gauge 010 at index 2.
4. **Next test needed**:
   Verification of larger graph frontier continuations and receipt chaining across multi-worker schedules.

## 6. Cross-References & Provenance

- Archive Claim: [ATL-P002-007](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP002-07](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L22)
- Manuscript Source: Section 4 ("The search frontier, candidate enumeration, and receipts")
- Verification Test: `tests/test_paper_002_search_trace.py`
