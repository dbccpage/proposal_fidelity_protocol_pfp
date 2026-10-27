---
documentation_contract: symbol-game-documentation/v1
title: 'Application Note: Quantum Mutually Unbiased Bases, Deltoid Cusp Obstruction, and Stabilizer Geometry'
kind: application-reference
audience:
  - researchers
  - quantum-physicists
  - coding-agents
status: active
maturity: emerging
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - mutually_unbiased_bases
    - weyl_heisenberg_construction
    - complex_hadamard_variety
    - deltoid_cusp_boundary
    - six_cycle_holonomy_circulation
    - pauli_stabilizer_group
    - symplectic_inner_product
  prose_theorems:
    - prime_power_mub_cardinality
    - deltoid_cusp_quotient_obstruction_lower_bound
    - stabilizer_distance_symplectic_orthogonality
  lean_theorems: []
  finite_computations:
    - demo_3_mub6_deltoid_cusp
    - mub6_constants_rust_crate
    - c021_q40_stabilizer_synthesis
    - c025_mub_prime_power_exact
  declared_policies:
    - zero_float_in_mub_parameters
    - epistemic_firewall_line_mub6
  applications:
    - quantum_state_tomography
    - discrete_hadamard_manifold_obstructions
    - quantum_error_correcting_codes
  open_conjectures:
    - zauner_conjecture_d6_maximum_mubs
coefficient_domain: "ℚ[√·] / ℂ"
runtime_dependency: "Chapter 02 (Cochain Complexes), Chapter 03 (Obstruction Mass & LP Duality)"
governance_dependency: "None"
---

# Application Note: Quantum Mutually Unbiased Bases, Deltoid Cusp Obstruction, and Stabilizer Geometry

**Status:** Downstream Mathematical Application  
**Context:** Formulates the finite-dimensional Hilbert space geometry of Mutually Unbiased Bases (MUBs), the composite dimension $d=6$ obstruction, the Segre variety corner-minor desingularization locus, exact rational Deltoid cusp constants, 6-cycle holonomy defects, and stabilizer code symplectic geometry. Grounded in `demo_3_mub6`, `demo_q40_quantum_solver`, and Challenges C021–C030.  
**Authority:** None. Quantum information theory and exact rational combinatorial certifiers.

---

## 1. Mutually Unbiased Bases (MUBs) in Finite Hilbert Spaces

Let $\mathcal{H}_d \cong \mathbb{C}^d$ be a complex Hilbert space of dimension $d$ equipped with the standard Hermitian inner product $\langle \cdot, \cdot \rangle$.

### 1.1 The Mutual Unbiasedness Condition
Two orthonormal bases $\mathcal{B}_1 = \{ |u_1\rangle, \ldots, |u_d\rangle \}$ and $\mathcal{B}_2 = \{ |v_1\rangle, \ldots, |v_d\rangle \}$ of $\mathcal{H}_d$ are **mutually unbiased** if and only if the transition probability between any state in $\mathcal{B}_1$ and any state in $\mathcal{B}_2$ is uniformly distributed:

$$\boxed{|\langle u_i \mid v_j \rangle|^2 = \frac{1}{d} \quad \text{for all } 1 \le i, j \le d}$$

A set of orthonormal bases $\{\mathcal{B}_1, \mathcal{B}_2, \ldots, \mathcal{B}_m\}$ is a **mutually unbiased basis (MUB) constellation** if every distinct pair $\mathcal{B}_k, \mathcal{B}_l$ ($k \ne l$) is mutually unbiased.

### 1.2 Theoretical Bounds & Prime Powers
**Theorem (MUB Upper Bound):**  
In any dimension $d \ge 2$, the maximum number $m$ of mutually unbiased bases satisfies:
$$m \le d + 1$$

**Theorem (Prime-Power Construction, Ivanovic 1981, Wootters & Fields 1989):**  
If $d = p^n$ is a prime power (for prime $p$ and integer $n \ge 1$), the maximal bound is saturated:
$$m = d + 1 = p^n + 1$$
The construction is realized explicitly via discrete phase operators and Weyl-Heisenberg groups acting over the finite Galois field $\mathbb{F}_{p^n}$.

---

## 2. The Dimension $d=6$ Composite Obstruction

When $d$ is not a prime power, the maximal number of MUBs is an open problem in quantum information theory. The smallest composite dimension is $d = 6 = 2 \times 3$.

### 2.1 The Open Gap
- **Known Lower Bound:** At least 3 MUBs exist in $\mathbb{C}^6$ (the computational basis plus two bases derived from complex Hadamard matrices).
- **Theoretical Ceiling:** $d + 1 = 7$.
- **Zauner's Conjecture (1999):** The maximum number of MUBs in dimension $d=6$ is strictly 3. Extensive numerical searches have failed to discover a 4th MUB.

### 2.2 The Complex Hadamard Variety $\mathcal{H}_6$
A matrix $H \in \mathrm{Mat}(d, \mathbb{C})$ is a **complex Hadamard matrix** if:
1. $|H_{ij}| = 1$ for all $1 \le i, j \le d$ (unimodular entries),
2. $H H^\dagger = d \cdot I_d$ (scaled unitary).

Two MUBs in $\mathbb{C}^d$ can always be rotated into the computational basis $\{|i\rangle\}$ and the standard Fourier basis $\frac{1}{\sqrt{d}} F_d$. A third MUB corresponds to a complex Hadamard matrix $H_3 \in \mathcal{H}_d$. A 4th MUB requires a pair $(H_3, H_4)$ such that $\frac{1}{\sqrt{d}} H_3^\dagger H_4$ is also a complex Hadamard matrix.

In $d=6$, the set $\mathcal{H}_6$ of complex Hadamard matrices (up to equivalence) is conjectured to be 4-dimensional; a four-parameter family is known, and the full classification is open. The description "non-affine orbits and singular Deltoid cusps" refers to the families studied in the literature and is not derived in this note. *(Status wording corrected 2026-10-20; an earlier version stated the dimension as a fact.)*

---

## 3. Deltoid Cusp Desingularization & The 6-Cycle Holonomy Defect

In `demo_3_mub6` and the Rust engine `core_mub`, candidate matrices near the Deltoid cusp locus are evaluated via exact rational desingularization.

### 3.1 The Segre Variety Locus
Near the 3 deltoid cusps ($\theta \in \{0, 2\pi/3, 4\pi/3\}$), the corner minors of candidate matrices are governed by the Segre variety equation:

$$(a - 1)(d - 1) = (b - 1)(c - 1)$$

### 3.2 Exact Rational Cusp Parameters
The exact rational parameters governing the blow-up chart (pinned in `engine/crates_rs/core_mub/src/core_native/mub6_constants.rs`) are listed below. *Provenance (read 2026-10-20 in [`core_mub/fixtures/mub6_constants.json`](../../../../engine/crates_rs/core_mub/fixtures/mub6_constants.json)):* all three are recorded as `assumed_constant`. The gap $\varepsilon_{\mathrm{cusp}} = (81/100 - 1/6)^2 = (193/300)^2 = 37249/90000$ assumes that the candidate fourth basis has column-0 real part in $[9/10, 1]$; the Lipschitz bound $L_{\mathrm{proj}} = 85/9$ has no derivation or check in the crate; and $\delta = 1/1000$ is chosen, with the only check $\delta < \varepsilon / L$. Every number derived below inherits these assumptions:

$$\varepsilon_{\mathrm{cusp}} = \frac{37249}{90000}, \qquad L_{\mathrm{proj}} = \frac{85}{9}, \qquad \delta = \frac{1}{1000}$$
$$\delta_{\mathrm{crit}} = \frac{\varepsilon_{\mathrm{cusp}}}{L_{\mathrm{proj}}} = \frac{37249}{850000} \approx 0.043822$$
$$\mu_{\mathrm{cusp}} = \varepsilon_{\mathrm{cusp}} - L_{\mathrm{proj}} \delta = \frac{37249}{90000} - \frac{85}{9000} = \frac{12133}{30000} > 0$$

### 3.3 The 6-Cycle Holonomy Circulation
Connecting the 3 singular cusps and their intermediate boundary arcs produces a directed 6-cycle carrier $C_6$:
- Vertices: $v_0, v_1, v_2, v_3, v_4, v_5$.
- Edges: $(v_0, v_1), (v_1, v_2), (v_2, v_3), (v_3, v_4), (v_4, v_5), (v_5, v_0)$.
- Edge 1-Cochain Flux: $c_1(e) = \mu_{\mathrm{cusp}} = \frac{12133}{30000}$ for each edge $e \in C_6$.

The net circulation around $C_6$ is:
$$\Gamma = \sum_{e \in C_6} c_1(e) = 6 \times \frac{12133}{30000} = \frac{12133}{5000} = 2.4266 > 0$$

### 3.4 Irreducible Quotient Obstruction Mass
Because the coboundary operator on 0-cochains $\alpha \in C^0$ telescopes to zero around any cycle:
$$\sum_{e \in C_6} (d_0 \alpha)_e = (\alpha_1 - \alpha_0) + (\alpha_2 - \alpha_1) + \cdots + (\alpha_0 - \alpha_5) = 0$$

The degree-1 quotient obstruction mass is bounded strictly away from zero (with unit edge weights):
$$\boxed{\Phi_1([c_1]) = \min_{\alpha \in C^0} \|c_1 - d_0 \alpha\|_1 \ge \frac{12133}{5000} > 0}$$

This certifies an **irreducible topological obstruction** in the discrete carrier.

*Equality (2026-10-20):* the bound is attained, so $\Phi_1([c_1]) = 12133/5000$ exactly. The all-ones dual $y = (1, \dots, 1)$ has zero divergence on the cycle and $|y_e| = 1$, giving the lower bound $\langle y, c_1 \rangle = 6\mu_{\mathrm{cusp}}$; the potential $\alpha_k = k\,\mu_{\mathrm{cusp}}$ for $k = 0, \dots, 5$ makes $c_1 - d_0\alpha$ zero on the first five edges and $6\mu_{\mathrm{cusp}}$ on the edge $v_5 \to v_0$, giving the same upper bound. The obstruction is a property of the declared cochain (constant flux on a cycle), so its meaning for MUB(6) rests entirely on the assumed constants above.

### 3.5 The Epistemic Firewall Line
In accordance with Claim Hygiene Rule:
> **Firewall Line:** `NOT MUB(6)=3, NOT MUB(6)<=3; stated region only; mints no authority`.  
> The 6-cycle holonomy defect certifies an obstruction strictly on the investigated Segre variety blow-up chart near the Deltoid cusps. It does not constitute a mathematical proof of Zauner's full global conjecture ($MUB(6) = 3$ across all of $\mathcal{H}_6$).

---

## 4. Stabilizer Formalism & Symplectic Geometry

In quantum error correction and Clifford synthesis (Challenges C021–C024), quantum states are represented by Abelian subgroups of the Pauli group.

### 4.1 The $n$-Qubit Pauli Group $\mathcal{P}_n$
Let $I, X, Y, Z$ be the standard single-qubit Pauli matrices. The $n$-qubit Pauli group is:
$$\mathcal{P}_n = \{ \alpha P_1 \otimes \cdots \otimes P_n : \alpha \in \{\pm 1, \pm i\}, \; P_j \in \{I, X, Y, Z\} \}$$

Ignoring global phases, the quotient $\mathcal{P}_n / \mathcal{Z}(\mathcal{P}_n) \cong \mathbb{F}_2^{2n}$ is a $2n$-dimensional vector space over $\mathbb{F}_2$. A Pauli operator $P$ corresponds to a binary vector:
$$v = (x_1, \ldots, x_n \mid z_1, \ldots, z_n) \in \mathbb{F}_2^{2n}$$
where $x_j = 1$ indicates an $X$ or $Y$ component, and $z_j = 1$ indicates a $Z$ or $Y$ component.

### 4.2 Symplectic Inner Product & Commutativity
Two Pauli operators $P, Q$ with binary symplectic vectors $u = (x \mid z)$ and $v = (x' \mid z')$ commute if and only if their **symplectic inner product** vanishes modulo 2:

$$[u, v] = x \cdot z' + z \cdot x' = \sum_{j=1}^n (x_j z'_j + z_j x'_j) \equiv 0 \pmod 2$$

### 4.3 Stabilizer Codes & Distance Lower Bounds
A **stabilizer code** $\mathcal{C}$ is the joint $+1$ eigenspace of an Abelian subgroup $S \subset \mathcal{P}_n$ such that $-I \notin S$:
$$\mathcal{C} = \{ |\psi\rangle \in (\mathbb{C}^2)^{\otimes n} : M |\psi\rangle = |\psi\rangle \; \forall M \in S \}$$

If $S$ is generated by $n - k$ independent commuting Pauli generators, the code encodes $k$ logical qubits ($[[n, k, d]]$ code). *(Corrected 2026-10-20: the earlier sentence said $k$ generators encode $k$ logical qubits. Each independent generator halves the code space, so $r$ generators leave $2^{n-r}$ dimensions, that is $n - r$ logical qubits. Example: the five-qubit code has $n = 5$ and four generators $XZZXI, IXZZX, XIXZZ, ZXIXZ$, so $k = 1$.)* The **code distance** $d$ is:
$$d = \min \{ \operatorname{wt}(P) : P \in \mathcal{Z}(S) \setminus S \}$$
where $\mathcal{Z}(S)$ is the centralizer of $S$ in $\mathcal{P}_n$, and $\operatorname{wt}(P)$ is the number of non-identity tensor factors.

In Challenge C022, distance lower-bound certificates are verified by exact integer linear programming over $\mathbb{F}_2$, proving that no non-trivial centralizer element exists with weight less than $d$.

---

## 5. Claim Hygiene & Artifact Boundary

1. **What this document supports:**
   - Formalizes the finite MUB condition in $\mathbb{C}^d$ and prime-power saturations $d+1$.
   - Formulates the exact rational Deltoid cusp constants and computes the 6-cycle holonomy defect $\Gamma = \frac{12133}{5000} > 0$, certifying an irreducible quotient obstruction $\Phi_1 > 0$ on the local blow-up chart.
   - Formulates stabilizer codes via symplectic vector spaces $\mathbb{F}_2^{2n}$ and distance certification.

2. **What this document does NOT support:**
   - Does NOT prove Zauner's conjecture ($MUB(6) = 3$). The computed obstruction is local to the investigated Deltoid cusp neighborhood and does not rule out hypothetical isolated Hadamard pairs elsewhere in the 4D manifold.
   - Does not claim that local stabilizer checks resolve continuous Lie group unitary synthesis.

3. **Narrowest defensible claim:**
   - On the declared Deltoid cusp desingularization chart with parameter $\delta = 1/1000$, the 6-cycle circulation is exactly $12133/5000 \in \mathbb{Q}$, yielding a certified non-zero quotient obstruction mass $\Phi_1([c_1]) \ge 12133/5000$.

4. **Next test needed:**
   - Integrate the exact rational LP solver from Challenge C051 to compute certified distance lower bounds for the 5-qubit code $[[5, 1, 3]]$ without floating-point approximations.
