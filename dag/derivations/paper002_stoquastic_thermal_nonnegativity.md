# PAPER002-STOQUASTIC-THERMAL-NONNEGATIVITY: Stoquastic Thermal Nonnegativity

AuthorityEffect: None.

- Archive claim: [ATL-P002-003](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("A finite stoquastic real matrix has an entrywise nonnegative thermal exponential for nonnegative beta.", [paper_claim_ledger.md:18](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L18))
- Audit derivation node: [PAPER002-STOQUASTIC-THERMAL-NONNEGATIVITY](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER002-STOQUASTIC-THERMAL-NONNEGATIVITY`)
- Review verdict: `matched` (`states_same_claim_as`)

## 1. Claim Statement

A finite stoquastic real matrix has an entrywise nonnegative thermal exponential for nonnegative beta.

## 2. Context & Hypotheses

- **Matrix Carrier & Field**:
  - $H \in \mathbb{R}^{n \times n}$ is a finite real matrix of dimension $n \ge 1$.
- **Declared Basis & Stoquasticity**:
  - In a declared fixed basis, all off-diagonal entries of $H$ are nonpositive:
    $$H_{ij} \le 0 \quad \text{for all } i \ne j \in \{1, \ldots, n\}.$$
  - In quantum physics, a finite Hamiltonian with real matrix entries satisfying $H_{ij} \le 0$ ($i \ne j$) in a chosen computational basis is called *stoquastic* (or a Z-matrix in linear algebra).
- **Thermal Parameter**:
  - The inverse temperature parameter $\beta \in \mathbb{R}$ satisfies $\beta \ge 0$.
- **Thermal Exponential**:
  - The unnormalized thermal density operator $e^{-\beta H}$ is defined via the standard matrix exponential power series.

## 3. Derivation / Evidence

### 3.1 Diagonal Shift Construction
1. Choose real scalar $c = \max_{1 \le i \le n} H_{ii}$ (or any real scalar $c \ge \max_i H_{ii}$).
2. Define the shifted matrix $M = c I_n - H \in \mathbb{R}^{n \times n}$.
3. Evaluate the entries of $M$:
   - For diagonal entries ($i = j$):
     $$M_{ii} = c - H_{ii} \ge \max_{1 \le k \le n} H_{kk} - H_{ii} \ge 0.$$
   - For off-diagonal entries ($i \ne j$):
     $$M_{ij} = (c I_n)_{ij} - H_{ij} = 0 - H_{ij} = -H_{ij}.$$
     Because $H_{ij} \le 0$, it follows that $M_{ij} = -H_{ij} \ge 0$.
4. Therefore, every entry of $M$ is real and nonnegative: $M \ge 0$ entrywise ($M_{ij} \ge 0$ for all $i, j \in \{1, \ldots, n\}$).

### 3.2 Commutativity and Exponential Factorization
1. The scalar matrix $c I_n$ commutes with every $n \times n$ matrix. In particular:
   $$[c I_n, M] = (c I_n) M - M (c I_n) = c M - c M = 0.$$
2. Multiplying by scalars preserves commutativity:
   $$[-\beta c I_n, \beta M] = 0.$$
3. Because $-\beta H = -\beta (c I_n - M) = -\beta c I_n + \beta M$, and the two summands commute, the matrix exponential factors:
   $$e^{-\beta H} = e^{-\beta c I_n + \beta M} = e^{-\beta c I_n} e^{\beta M} = (e^{-\beta c} I_n) e^{\beta M} = e^{-\beta c} e^{\beta M}.$$
4. The scalar factor $e^{-\beta c} > 0$ is strictly positive for all finite real values of $c$ and $\beta$.

### 3.3 Power Series Expansion and Nonnegativity
1. The matrix exponential $e^{\beta M}$ is given by the power series:
   $$e^{\beta M} = \sum_{k=0}^\infty \frac{\beta^k M^k}{k!}.$$
2. Matrix powers:
   - For $k = 0$, $M^0 = I_n \ge 0$ entrywise.
   - For two entrywise nonnegative matrices $A, B \ge 0$, their matrix product is entrywise nonnegative:
     $$(A B)_{ij} = \sum_{r=1}^n A_{ir} B_{rj} \ge 0.$$
   - By induction, $M^k \ge 0$ entrywise for every integer $k \ge 0$.
3. Scalar coefficients:
   - For $\beta \ge 0$, $\beta^k \ge 0$ for every $k \ge 0$.
   - Since $k! > 0$, the scalar factor $\frac{\beta^k}{k!} \ge 0$ is nonnegative.
4. Each matrix term in the expansion is entrywise nonnegative:
   $$\frac{\beta^k M^k}{k!} \ge 0 \quad \text{entrywise for each } k \ge 0.$$
5. For any finite truncation order $K \ge 0$, the partial sum:
   $$S_K = \sum_{k=0}^K \frac{\beta^k M^k}{k!} \ge 0 \quad \text{entrywise}.$$

### 3.4 Absolute Convergence and Limit Nonnegativity
1. In any submultiplicative matrix norm $\|\cdot\|$ on $\mathbb{R}^{n \times n}$, the series converges absolutely:
   $$\sum_{k=0}^\infty \left\| \frac{\beta^k M^k}{k!} \right\| \le \sum_{k=0}^\infty \frac{\beta^k \|M\|^k}{k!} = e^{\beta \|M\|} < \infty.$$
2. Because $\mathbb{R}^{n \times n}$ is finite-dimensional and complete, the series converges uniformly on bounded $\beta$ intervals to $e^{\beta M}$.
3. Coordinate projection $(A)_{ij}$ is a continuous linear functional in finite dimensions.
4. The entrywise limit of a sequence of nonnegative partial sums is nonnegative:
   $$(e^{\beta M})_{ij} = \lim_{K \to \infty} (S_K)_{ij} \ge 0 \quad \text{for all } i, j \in \{1, \ldots, n\}.$$
5. Scaling by the strictly positive scalar $e^{-\beta c} > 0$ preserves entrywise nonnegativity:
   $$(e^{-\beta H})_{ij} = e^{-\beta c} (e^{\beta M})_{ij} \ge 0 \quad \text{for all } i, j \in \{1, \ldots, n\}.$$

### 3.5 Empirical Verification and Test Witness Reference
The argument is supported by executable checks in `tests/test_paper002_stoquastic_thermal_nonnegativity.py`:
1. **Running Fixture from Paper 002**:
   - The manuscript evaluates the 3-state matrix `RUNNING = ((0, 1, -1), (1, 0, 1), (-1, 1, 0))`.
   - Applying diagonal sign gauge $S = \operatorname{diag}(1, -1, 1)$ produces the stoquastic Hamiltonian:
     $$H' = S H_{\text{run}} S = \begin{pmatrix} 0 & -1 & -1 \\ -1 & 0 & -1 \\ -1 & -1 & 0 \end{pmatrix}.$$
   - Shift scalar $c = 0$, shifted matrix $M = -H' = \begin{pmatrix} 0 & 1 & 1 \\ 1 & 0 & 1 \\ 1 & 1 & 0 \end{pmatrix} = J_3 - I_3 \ge 0$.
2. **Exact Closed-Form Solution**:
   - The matrix $M$ has eigenvalues $2$ (multiplicity 1) and $-1$ (multiplicity 2), yielding:
     $$e^{-\beta H'} = e^{\beta M} = \frac{1}{3} \begin{pmatrix} e^{2\beta} + 2e^{-\beta} & e^{2\beta} - e^{-\beta} & e^{2\beta} - e^{-\beta} \\ e^{2\beta} - e^{-\beta} & e^{2\beta} + 2e^{-\beta} & e^{2\beta} - e^{-\beta} \\ e^{2\beta} - e^{-\beta} & e^{2\beta} - e^{-\beta} & e^{2\beta} + 2e^{-\beta} \end{pmatrix}.$$
   - For all $\beta \ge 0$, $2\beta \ge -\beta$, so $e^{2\beta} \ge e^{-\beta}$, with strict inequality $e^{2\beta} > e^{-\beta}$ for $\beta > 0$. Every entry is strictly positive for $\beta > 0$.
3. **Negative Control (Ungauged Matrix)**:
   - Evaluating $e^{-\beta H_{\text{run}}}$ on the ungauged Hamiltonian with positive off-diagonal entries ($H_{01} = 1 > 0$) yields negative off-diagonal entries (e.g. entry $(0, 1) \approx -0.7039 < 0$ at $\beta = 0.5$).
   - This demonstrates that off-diagonal nonpositivity is necessary for general thermal entrywise nonnegativity.

## 4. Limits and Non-Claims

- **Fixed Declared Basis Only**:
  - The derivation applies solely in the declared basis where off-diagonal entries satisfy $H_{ij} \le 0$ ($i \ne j$).
  - It does not claim diagonal-sign stoquasticity under arbitrary basis rotations or general unitary transformations. Obtaining a stoquastic basis via general local or global unitary operations is computationally hard in general.
- **No Sampling-Time or Variance Guarantee**:
  - Entrywise nonnegativity of $e^{-\beta H}$ establishes that the thermal density operator has nonnegative matrix elements in the computational basis.
  - It does not establish rapid mixing of Markov chains, polynomial-time Quantum Monte Carlo (QMC) convergence, or a low-variance estimator for general observables.
- **Observables and Non-Diagonal Operators**:
  - Even when the unnormalized density matrix $e^{-\beta H}$ is entrywise nonnegative, evaluating expectation values $\langle O \rangle = \frac{\operatorname{Tr}(O e^{-\beta H})}{\operatorname{Tr}(e^{-\beta H})}$ for operators $O$ that are not positive and diagonal in the basis can still incur an exponential sign problem.
- **Finite Dimensionality**:
  - The proof operates on finite-dimensional real matrices ($n \times n$). Extension to unbounded operators, continuous field theories, or infinite-dimensional Hilbert spaces is outside this scope.
- **No Machine Learning Claims**:
  - Does not evaluate neural network weights, attention layers, token representations, or foundation models.

## 5. Claim Hygiene Summary

1. **What it supports**:
   Supports the mathematical statement that for any finite real matrix $H$ with nonpositive off-diagonal entries ($H_{ij} \le 0$ for $i \ne j$) in a declared basis, and any inverse temperature parameter $\beta \ge 0$, the matrix exponential $e^{-\beta H}$ is entrywise nonnegative. This conclusion follows from the diagonal shift $c = \max_i H_{ii}$, the entrywise nonnegativity of $M = cI - H \ge 0$, commutativity $[cI, M] = 0$, and the termwise nonnegativity and absolute convergence of the Taylor series $\sum_{k=0}^\infty \frac{\beta^k M^k}{k!}$. Supported empirically by exact analytical evaluation and pytest checks in `tests/test_paper002_stoquastic_thermal_nonnegativity.py`.

2. **What it does not support**:
   Does not support claims of efficient Quantum Monte Carlo sampling, rapid mixing of stochastic walkers, or polynomial-time estimation of physical observables; does not eliminate sign problems for non-diagonal observables; does not identify stoquastic bases under arbitrary local or global unitary transformations; does not extend to infinite-dimensional or continuous operators.

3. **Narrowest defensible claim**:
   For finite real matrices with nonpositive off-diagonal entries in a declared basis and $\beta \ge 0$, the matrix exponential $e^{-\beta H}$ has nonnegative entries in that same basis.

4. **Next test needed**:
   Derivation ATL-P002-007 (verification of the introductory matrix 3-state search trace with budget 2 reaching UNKNOWN on interval [2, 8) and resumed budget 1 finding witness 010 at index 2).

## 6. Cross-References & Provenance

- Archive Claim: [ATL-P002-003](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP002-03](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L18)
- Manuscript Context: [paper.md:140](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper.md?plain=1#L140) (Section 3: "Exact matrices and the boundary of stoquasticity")
- DAG Review Node: `PAPER002-STOQUASTIC-THERMAL-NONNEGATIVITY`
- Review Registry: `dag/reviews/additional_paper_002_support.json`
- Pull Request Target: `derivation/atl-p002-003`
``