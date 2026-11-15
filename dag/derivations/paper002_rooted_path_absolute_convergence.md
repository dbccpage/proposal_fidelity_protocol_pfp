# PAPER002-ROOTED-PATH-ABSOLUTE-CONVERGENCE: Rooted-Path Absolute Convergence

AuthorityEffect: None.

- Archive claim: [ATL-P002-012](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("The specified integrated rooted-path expansion converges absolutely.", [paper_claim_ledger.md:27](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L27))
- Audit derivation node: [PAPER002-ROOTED-PATH-ABSOLUTE-CONVERGENCE](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER002-ROOTED-PATH-ABSOLUTE-CONVERGENCE`)
- Review verdict: `matched` (`states_same_claim_as`)

## 1. Claim Statement

The integrated rooted-path expansion on the specified triangle carrier converges absolutely for $\beta \ge 0$, with total absolute weight bounded by $64e^{4\beta}$.

## 2. Context & Hypotheses

- **Triangle Fock Space**:
  Three sites with spin-up modes followed by spin-down modes in the declared ordering $(\uparrow 0, \uparrow 1, \uparrow 2, \downarrow 0, \downarrow 1, \downarrow 2)$.
  The occupation state space has cardinality $2^6 = 64$.
- **Hamiltonian Parameters**:
  Hopping amplitude $t = 1$, on-site interaction $U = 2$, chemical potential $\mu = 0$, inverse temperature $\beta \ge 0$.
- **Diagonal Energy**:
  $$E(x) = 2 \sum_{i=0}^2 n_{\uparrow i} n_{\downarrow i}.$$
  Since $n_{\sigma i} \in \{0, 1\}$, $0 \le E(x) \le 6$ for all 64 states $x$.
- **Single-Particle Hopping Bound**:
  A spin species occupying $k \in \{0, 1, 2, 3\}$ sites has $k(3-k) \le 2$ allowed hops on the 3-site triangle. Summing over both spin species, every occupation state has at most $2 + 2 = 4$ outgoing single-particle hops.
- **Integrated Simplex Path Weight**:
  For an $n$-hop sequence with jump times $0 < \tau_1 < \dots < \tau_n < \beta$, the weight magnitude is:
  $$|w| \le \int_{0 < \tau_1 < \dots < \tau_n < \beta} \exp\left(-\sum_{j=0}^n E(x_j)(\tau_{j+1} - \tau_j)\right) d\tau_1 \dots d\tau_n.$$

## 3. Derivation / Evidence

### 3.1 Integrand and Simplex Volume Bound
Because $E(x_j) \ge 0$ and $\tau_{j+1} - \tau_j \ge 0$ for all $j \in \{0, \dots, n\}$, the exponent satisfies:
$$-\sum_{j=0}^n E(x_j)(\tau_{j+1} - \tau_j) \le 0 \implies \exp\left(-\sum_{j=0}^n E(x_j)(\tau_{j+1} - \tau_j)\right) \le 1.$$
The integrated weight of any $n$-hop sequence is therefore bounded by the volume of the standard $n$-simplex of length $\beta$:
$$|w| \le \int_{0 < \tau_1 < \dots < \tau_n < \beta} 1 \, d\tau_1 \dots d\tau_n = \frac{\beta^n}{n!}.$$

### 3.2 Combinatorial Sequence Count
- The carrier consists of rooted closed hopping sequences starting at any of the 64 states.
- Starting from any initial occupation state $x_0$, there are at most 4 choices for the first hop.
- From each intermediate state, there are at most 4 choices for the next hop.
- Thus, the number of rooted sequences of length $n$ is bounded by $64 \cdot 4^n$.

### 3.3 Absolute Convergence Summation
Summing the absolute magnitudes over all sequence lengths $n \ge 0$:
$$\sum_{n=0}^\infty \sum_{\text{seq of length } n} |w(\text{seq})| \le \sum_{n=0}^\infty (64 \cdot 4^n) \frac{\beta^n}{n!} = 64 \sum_{n=0}^\infty \frac{(4\beta)^n}{n!} = 64 e^{4\beta}.$$
For any real $\beta \ge 0$, $64 e^{4\beta} < \infty$. Therefore, the series converges absolutely.

For the manuscript's parameter value $\beta = 1/4$:
$$64 e^{4(1/4)} = 64 e^1 \approx 173.987 < \infty.$$

## 4. Limits and Non-Claims

- **Carrier Scope**:
  Applies to the specified 3-site Fermi-Hubbard triangle carrier and nonnegative $\beta$.
- **Not an Efficiency Claim**:
  This is a mathematical convergence bound for the path expansion; it does not establish polynomial-time sampling efficiency or uniform variance bounds for Monte Carlo estimators.
- **Not a Tail Bound of 1/6144**:
  The global bound $64 e^{4\beta}$ does not imply a total-tail bound of $1/6144$ without additional length-specific energy evaluations.

## 5. Claim Hygiene Summary

1. **What it supports**:
   Supports that the rooted-path expansion on the declared 3-site triangle carrier converges absolutely for all $\beta \ge 0$, bounded by $64 e^{4\beta}$.
2. **What it does not support**:
   Does not support rapid Monte Carlo mixing, bounded sign-problem variance, or general graph convergence.
3. **Narrowest defensible claim**:
   On the 3-site triangle carrier with 64 occupation states and maximum degree 4, the absolute path sum is bounded by $64 e^{4\beta}$.
4. **Next test needed**:
   Testing higher-order convergence bounds on 4-site and ladder geometries.

## 6. Cross-References & Provenance

- Archive Claim: [ATL-P002-012](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP002-12](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L27)
- Manuscript Source: Section 6 ("A restricted Fock-space obstruction with exact bounds")
- Verification Test: `tests/test_paper_002_native_and_convergence.py`
