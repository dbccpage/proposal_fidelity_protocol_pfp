---
documentation_contract: symbol-game-documentation/v1
title: "study_guide: The Theoretical Minimum Study Guide — Discrete Cochain Retraction, Primal-Dual Obstruction, and Toy Involutions"
kind: educational-study-guide
audience:
  - researchers
  - theoretical-physicists
  - discrete-mathematicians
  - coding-agents
status: proposed-revision
maturity: draft
claim_status: proposed
authority_effect: "None"
source_paths:
  - atlas/coda_atlas/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper.md
prerequisites:
  - 00_preface_at_apartment_50.md
  - ../paper.md
last_verified: 2026-10-02
---

# The Theoretical Minimum Study Guide: Paper 001
## Discrete Cochain Retraction, Primal-Dual Obstruction, and Toy Involutions

**AuthorityEffect:** None.  
**Presiding Tribunal:** The Adversary Panel & Examiner.  
**Author of Baseline Paper:** Jeremy H. Carroll.  
**Location:** the city, Sadovaya 302-bis, Apartment 50.  
**Companion Documents:**
- Staging and Tribunal Lore: [00_preface_at_apartment_50.md](./00_preface_at_apartment_50.md)
- Examination Paper: [quiz.md](./quiz.md)
- Core Paper: [paper.md](../paper.md)

---

## 0. The Examiner Warning: Why Proposing Is Not Proving

Before you sit for the examination in [quiz.md](./quiz.md), you must discard the most pervasive and dangerous fallacy in modern computational science: **confusing an optimization proposal with an exact certificate**.

Professor Examiner stands before the blackboard, snapping his chalk against the slate:

> *"Look at how an amateur approaches an optimization problem! He takes a function, guesses an input vector, runs twenty iterations of an approximation heuristic, and when the objective value stops moving, he proudly declares: 'The minimum is 3!'  
>
> That is not mathematics; that is astrology. A proposed candidate vector gives you only an **upper bound** on the minimum: $\Phi \le D(s)$. If you tell me you found a potential that costs 3, you have established that the minimum cannot exceed 3. But how do you know there is not another potential—perhaps fractional, perhaps subtle—that achieves cost $2.99$ or $1$?  
>
> Heuristic failure does not prove a minimum. In this examination, construct an independent **lower-bound witness**: an object from the dual space that puts an immovable geometric floor underneath the cost function. When your upper bound from the primal proposal matches your lower bound from the dual certificate, the duality gap collapses to zero. The matching bounds prove optimality by weak duality. A complete exact search can also prove a minimum when a theorem justifies its search set; the native spanning-forest solver uses that route. Here, dual witnesses make the lower bound independently checkable."*

This study guide develops the exact discrete geometry, linear algebra, and combinatorial graph theory needed to pass the Paper 001 Theoretical Minimum.

---

## 1. The Discrete Graph Model

### 1.1 Vertices, Edges, and Cochains
Let $G = (V, E)$ be a finite, connected or disconnected directed graph without self-loops.
- **Vertices (0-cells):** Finite set $V = \{v_1, v_2, \dots, v_n\}$ with $|V| = n$.
- **Edges (1-cells):** Finite set $E = \{e_1, e_2, \dots, e_m\}$ with $|E| = m$. Each directed edge $e = u \to v$ has source $u \in V$ and target $v \in V$ with $u \ne v$.
- **0-cochains $C^0(G; \mathbb{Q})$:** Rational functions assigning a height or level to each vertex: $s: V \to \mathbb{Q}$, represented as a column vector $s \in \mathbb{Q}^V$.
- **1-cochains $C^1(G; \mathbb{Q})$:** Rational functions assigning a value to each directed edge: $c: E \to \mathbb{Q}$, represented as a column vector $c \in \mathbb{Q}^E$.
- **Absence of 2-cells ($C^2 = 0$):** The graph contains no filled polygonal faces. Therefore, there is no discrete 2-form curvature $d_1 c$. All obstruction in Paper 001 lives entirely in 1-cycles (the 1-homology $H_1(G; \mathbb{Q})$).

### 1.2 The Discrete Boundary and Coboundary
The geometry of $G$ is governed by the edge-by-vertex incidence matrix $B \in \{-1, 0, 1\}^{|E| \times |V|}$.
For each directed edge $e = u \to v$ and each vertex $x \in V$:

$$
B_{e, x} = \begin{cases}
-1 & \text{if } x = u \text{ (source)}, \\
+1 & \text{if } x = v \text{ (target)}, \\
0 & \text{otherwise}.
\end{cases}
$$

When $B$ acts on a vertex potential vector $s \in \mathbb{Q}^V$, it computes the directed difference across each edge:

$$(Bs)_{u \to v} = s_v - s_u$$

The transpose $B^T \in \{-1, 0, 1\}^{|V| \times |E|}$ acts as the discrete divergence operator on edge flows $\lambda \in \mathbb{Q}^E$:

$$(B^T \lambda)_x = \sum_{e = u \to x} \lambda_e - \sum_{e = x \to v} \lambda_e$$

which computes the net inflow into vertex $x$.

---

## 2. The Two Costs: Proposal Cost vs. Quotient Minimum

In Paper 001, we are given:
1. **Edge Reports $c \in \mathbb{Q}^E$:** Inconsistent pairwise measurements (e.g. clock offsets, height differences, ranking advantages).
2. **Penalties / Weights $w \in \mathbb{Q}_{>0}^E$:** Strictly positive rational penalties for disagreeing with each edge report.

### 2.1 The Proposal Cost $D_c(s)$
Given a proposed vertex potential $s \in \mathbb{Q}^V$, the **residual 1-cochain** $r \in \mathbb{Q}^E$ measures the discrepancy between the report $c$ and the exact potential difference $Bs$:

$$r = c - Bs \in \mathbb{Q}^E, \qquad r_{u \to v} = c_{u \to v} - (s_v - s_u)$$

The **proposal cost** $D_c(s)$ is the weighted $\ell_1$ norm of the residual:

$$D_c(s) = \sum_{e \in E} w_e |r_e| = \sum_{e = u \to v} w_e |c_{u \to v} - (s_v - s_u)|$$

Key properties of $D_c(s)$:
- $D_c(s) \ge 0$ for all $s \in \mathbb{Q}^V$.
- If $G$ has connected components $G_1, \dots, G_k$, shifting $s$ by an additive constant on any component leaves $Bs$, and hence $D_c(s)$, completely invariant. Potentials have an irrelevant gauge freedom $\mathbb{Q}^k$.

### 2.2 The Quotient Minimum $\Phi(c)$
The **quotient minimum** $\Phi(c)$ (also denoted $\Phi_1(c)$) is the intrinsic topological obstruction of the fixed edge reports $c$:

$$\Phi(c) = \min_{s \in \mathbb{Q}^V} D_c(s) = \min_{s \in \mathbb{Q}^V} \sum_{e \in E} w_e |c_e - (Bs)_e|$$

- $D_c(s)$ is a property of a **specific candidate proposal** $s$.
- $\Phi(c)$ is a property of the **fixed edge dataset** $c$.
- By definition, for every proposed potential $s$:

$$\Phi(c) \le D_c(s)$$

A proposal $s$ provides an upper bound on $\Phi(c)$.

---

## 3. Gauge Invariance under Coboundary Shifts

### Theorem: Exact Coboundary Invariance
Let $\phi \in \mathbb{Q}^V$ be any vertex potential. If we shift the edge reports $c$ by the exact coboundary $B\phi$:

$$c' = c + B\phi$$

then the quotient minimum is strictly invariant:

$$\Phi(c') = \Phi(c)$$

### Proof of Exact Coboundary Invariance
For any test potential $s \in \mathbb{Q}^V$:

$$D_{c'}(s) = \sum_e w_e |c'_e - (Bs)_e| = \sum_e w_e |(c_e + (B\phi)_e) - (Bs)_e| = \sum_e w_e |c_e - (B(s - \phi))_e|$$

Setting $f = s - \phi$, as $s$ ranges over all of $\mathbb{Q}^V$, $f$ also ranges over all of $\mathbb{Q}^V$. Therefore:

$$\min_{s \in \mathbb{Q}^V} D_{c'}(s) = \min_{f \in \mathbb{Q}^V} D_c(f) = \Phi(c)$$

$$\tag*{$\blacksquare$}$$

**Consequence:** Edge reports that differ only by a coboundary belong to the same cohomology class in $C^1 / \operatorname{im} B$. For the same graph and weights, they have the same mathematical quotient minimum. Any physical interpretation needs a separately justified modeling map.

---

## 4. Primal-Dual Witness Certification

How do we certify that a candidate potential $s^*$ is globally optimal without exhaustive search over all of $\mathbb{Q}^V$? We construct a **dual circulation witness**.

### 4.1 The Dual Linear Program
The primal problem is:

$$\min_{s \in \mathbb{Q}^V} \sum_{e \in E} w_e |c_e - (Bs)_e|$$

We introduce the dual variable $\lambda \in \mathbb{Q}^E$, which represents an edge flow or circulation.

### Definition: Feasible Dual Witness
A vector $\lambda \in \mathbb{Q}^E$ is a **feasible dual witness** if and only if it satisfies two conditions:
1. **Flow Conservation (Circulation Condition):** At every vertex $x \in V$, the net divergence is zero:
   $$B^T \lambda = \mathbf{0} \iff \sum_{e = u \to x} \lambda_e = \sum_{e = x \to v} \lambda_e \quad \forall x \in V$$
2. **Capacity Bounds:** On every edge $e \in E$, the flow does not exceed the edge penalty:
   $$|\lambda_e| \le w_e \quad \forall e \in E$$

The **dual objective value** is the standard inner product of the circulation with the reports:

$$\langle \lambda, c \rangle = \sum_{e \in E} \lambda_e c_e$$

---

### 4.2 Theorem: Weak Duality (The Iron Floor)
For **any** proposed vertex potential $s \in \mathbb{Q}^V$ and **any** feasible dual witness $\lambda \in \mathbb{Q}^E$:

$$\langle \lambda, c \rangle \le D_c(s)$$

### Proof of Weak Duality
Since $B^T \lambda = \mathbf{0}$, taking the dot product with the potential vector $s$ gives:

$$s^T (B^T \lambda) = 0 \iff (Bs)^T \lambda = \sum_{e \in E} (Bs)_e \lambda_e = 0$$

Therefore, we can subtract zero without changing the value:

$$\langle \lambda, c \rangle = \sum_{e \in E} \lambda_e c_e - \sum_{e \in E} \lambda_e (Bs)_e = \sum_{e \in E} \lambda_e (c_e - (Bs)_e) = \sum_{e \in E} \lambda_e r_e$$

Applying the triangle inequality and the capacity bound $|\lambda_e| \le w_e$:

$$\langle \lambda, c \rangle = \sum_{e \in E} \lambda_e r_e \le \sum_{e \in E} |\lambda_e| |r_e| \le \sum_{e \in E} w_e |r_e| = D_c(s)$$

$$\tag*{$\blacksquare$}$$

---

### 4.3 Theorem: Certificate of Optimality (Zero Duality Gap)
If a proposer exhibits a candidate potential $s^* \in \mathbb{Q}^V$ and a referee exhibits a feasible dual witness $\lambda^* \in \mathbb{Q}^E$ such that:

$$\langle \lambda^*, c \rangle = D_c(s^*)$$

then $s^*$ is **certified by weak duality to be an exact global minimizer**, and the quotient minimum is:

$$\Phi(c) = D_c(s^*) = \langle \lambda^*, c \rangle$$

### Proof of Optimality Certificate
By weak duality, for every potential $s \in \mathbb{Q}^V$:

$$D_c(s) \ge \langle \lambda^*, c \rangle = D_c(s^*)$$

Thus no potential can achieve a cost strictly less than $D_c(s^*)$.

$$\tag*{$\blacksquare$}$$

---

## 5. The Manuscript Triangle: Complete Worked Example

Let us work through the foundational test case of Paper 001: the **Manuscript Triangle**.

### 5.1 The Graph Specification
- **Vertices:** $V = \{a, b, c\}$.
- **Edges:** Three directed edges forming a cycle:
  - $e_1 = a \to b$
  - $e_2 = b \to c$
  - $e_3 = c \to a$
- **Reports:** $c = (c_1, c_2, c_3) = (1, 1, 1)$.
- **Weights:** $w = (w_1, w_2, w_3) = (1, 2, 3)$.

The incidence matrix $B \in \{-1, 0, 1\}^{3 \times 3}$ is:

$$
B = \begin{pmatrix}
-1 & 1 & 0 \\
0 & -1 & 1 \\
1 & 0 & -1
\end{pmatrix}
$$

The cycle sum of reports is:

$$\sum_{e \in \text{cycle}} c_e = c_1 + c_2 + c_3 = 1 + 1 + 1 = 3 \ne 0$$

Because the cycle sum is nonzero, no potential $s$ can make all residuals zero. There is an intrinsic obstruction.

---

### 5.2 Evaluating Candidate Proposals

#### Candidate 1: The All-Zero Potential $s^{(0)} = (0, 0, 0)$
- Differences: $Bs^{(0)} = (0 - 0, 0 - 0, 0 - 0) = (0, 0, 0)$.
- Residual: $r = c - Bs^{(0)} = (1, 1, 1)$.
- Cost:
  $$D_c(s^{(0)}) = 1|1| + 2|1| + 3|1| = 1 + 2 + 3 = 6$$

#### Candidate 2: The Optimal Potential $s^* = (0, -2, -1)$
- Differences:
  - $(Bs^*)_{a \to b} = s_b - s_a = -2 - 0 = -2$
  - $(Bs^*)_{b \to c} = s_c - s_b = -1 - (-2) = 1$
  - $(Bs^*)_{c \to a} = s_a - s_c = 0 - (-1) = 1$
- Residuals:
  - $r_1 = c_1 - (s_b - s_a) = 1 - (-2) = 3$
  - $r_2 = c_2 - (s_c - s_b) = 1 - 1 = 0$
  - $r_3 = c_3 - (s_a - s_c) = 1 - 1 = 0$
  $$r = (3, 0, 0)$$
- Cost:
  $$D_c(s^*) = w_1 |r_1| + w_2 |r_2| + w_3 |r_3| = 1(3) + 2(0) + 3(0) = 3$$

We now have an upper bound: $\Phi(c) \le 3$.

---

### 5.3 Constructing the Dual Witness $\lambda^*$
We require a circulation $\lambda = (\lambda_1, \lambda_2, \lambda_3)$ such that:
1. Flow conservation at each vertex:
   - At $a$: incoming $e_3$, outgoing $e_1 \implies \lambda_3 - \lambda_1 = 0 \implies \lambda_1 = \lambda_3$.
   - At $b$: incoming $e_1$, outgoing $e_2 \implies \lambda_1 - \lambda_2 = 0 \implies \lambda_2 = \lambda_1$.
   - At $c$: incoming $e_2$, outgoing $e_3 \implies \lambda_2 - \lambda_3 = 0$.
   Therefore, any circulation on a simple directed cycle must have uniform flow:
   $$\lambda = (k, k, k) \quad \text{for some } k \in \mathbb{Q}$$
2. Capacity constraints $|\lambda_e| \le w_e$:
   - $|\lambda_1| \le 1 \implies |k| \le 1$
   - $|\lambda_2| \le 2 \implies |k| \le 2$
   - $|\lambda_3| \le 3 \implies |k| \le 3$
   The bottleneck capacity is the **minimum edge weight**:
   $$|k| \le \min(1, 2, 3) = 1$$
   To maximize the dual objective $\langle \lambda, c \rangle = k(1) + k(1) + k(1) = 3k$, we choose the largest feasible flow:
   $$k = 1 \implies \lambda^* = (1, 1, 1)$$

3. Evaluate the Dual Objective:
   $$\langle \lambda^*, c \rangle = 1(1) + 1(1) + 1(1) = 3$$

4. Duality Gap Verification:
   $$D_c(s^*) - \langle \lambda^*, c \rangle = 3 - 3 = 0$$

The duality gap is zero! The candidate $s^* = (0, -2, -1)$ is mathematically certified as an exact global minimizer, and the true quotient obstruction is $\Phi(c) = 3$.

---

## 6. The Directed Cycle Formula

The result on the Manuscript Triangle generalizes to any single directed cycle.

### Theorem: Single Directed Cycle Obstruction
Let $C = (V_C, E_C)$ be a simple directed cycle with edge reports $c_e$ and positive penalties $w_e > 0$. Then:

$$\Phi(c) = \left(\min_{e \in E_C} w_e\right) \left| \sum_{e \in E_C} c_e \right|$$

### Proof of Directed Cycle Formula
1. **Lower Bound (Dual):**
   Any circulation $\lambda$ on a simple cycle must be a constant flow along the cycle: $\lambda_e = k$ for all $e \in E_C$.
   Capacity requires $|\lambda_e| \le w_e$ for all $e \in E_C$, which forces:
   $$|k| \le \min_{e \in E_C} w_e$$
   The dual value is:
   $$\langle \lambda, c \rangle = \sum_{e \in E_C} k c_e = k \sum_{e \in E_C} c_e$$
   Choosing $k = \operatorname{sgn}\left(\sum_{e \in E_C} c_e\right) \min_{e \in E_C} w_e$, we obtain the lower bound:
   $$\Phi(c) \ge \left(\min_{e \in E_C} w_e\right) \left| \sum_{e \in E_C} c_e \right|$$

2. **Upper Bound (Primal):**
   Let $e^* = u^* \to v^*$ be the bottleneck edge that achieves the minimum penalty: $w_{e^*} = \min_{e \in E_C} w_e$.
   Remove $e^*$ from the cycle. The remaining edges $E_C \setminus \{e^*\}$ form a spanning tree (a path).
   On any tree, edge reports can be matched exactly by a vertex potential ($r_e = 0$ for all $e \ne e^*$).
   Solving for the potential on the path dumps the entire cycle discrepancy onto the single bottleneck edge $e^*$:
   $$|r_{e^*}| = \left| \sum_{e \in E_C} c_e \right|$$
   The cost of this potential is:
   $$D_c(s^*) = w_{e^*} |r_{e^*}| = \left(\min_{e \in E_C} w_e\right) \left| \sum_{e \in E_C} c_e \right|$$

Since the upper bound equals the lower bound, the formula is exact.

$$\tag*{$\blacksquare$}$$

---

## 7. Sparsity and Uniqueness

### 7.1 Sparsity of Optimal Residuals
In linear programming over polyhedra, extreme points (basic feasible solutions) exhibit structural sparsity.

#### Theorem: Residual Support Bound
For any finite graph $G = (V, E)$, there exists an optimal potential $s^*$ whose residual $r^* = c - Bs^*$ has support size bounded by:

$$|\operatorname{supp}(r^*)| \le |E| - \operatorname{rank}(B)$$

Since $\operatorname{rank}(B) = |V| - k$ (where $k$ is the number of connected components):

$$|\operatorname{supp}(r^*)| \le |E| - |V| + k = \dim H_1(G; \mathbb{Q})$$

The number of nonzero residual edges in a basic optimal solution is at most the **first Betti number** (the cycle rank of the graph).

- For the Manuscript Triangle: $|E| = 3$, $|V| = 3$, $k = 1 \implies \dim H_1 = 3 - 3 + 1 = 1$.
- Indeed, the optimal residual $r^* = (3, 0, 0)$ has $|\operatorname{supp}(r^*)| = 1 \le 1$.

---

### 7.2 Uniqueness and the Weighted Null-Space Property
A potential always has additive freedom on each connected component. Uniqueness here means a unique residual, or a unique potential after one vertex per component has been fixed.

Let $S=\operatorname{supp}(r^*)$. The relevant residual perturbations lie in $\operatorname{im}B$, because changing a potential changes a residual by a vector $Bh$. A sufficient condition is

$$\sum_{e\in S}w_e|z_e|<\sum_{e\notin S}w_e|z_e|\qquad\text{for every }0\ne z\in\operatorname{im}B.$$

Then any distinct feasible residual $r^*+z$ satisfies

$$\|r^*+z\|_{1,w}\ge\|r^*\|_{1,w}-\|z_S\|_{1,w}+\|z_{S^c}\|_{1,w}>\|r^*\|_{1,w}.$$

This condition is sufficient for the particular residual. Its failure alone does not prove nonuniqueness. The dual witnesses instead lie in $\ker(B^T)$; these two spaces serve different roles.

On the equal-weight triangle with reports $(1,1,1)$ and weights $(2,2,2)$, the residuals $(3,0,0)$ and $(0,3,0)$ both cost $6$. They correspond to potentials $(0,-2,-1)$ and $(0,1,-1)$. The feasible dual $(2,2,2)$ has objective $6$, proving both are optimal. For $S=\{e_1\}$, the cut vector $z=(1,-1,0)=B(0,1,0)$ gives equality in the two weighted sums, so the sufficient condition fails.

A useful error detector: every circulation on this directed triangle is $t(1,1,1)$. Substituting circulations into the displayed condition would give $2|t|<4|t|$ and incorrectly predict uniqueness. Always check the perturbation space.

### 7.3 A sparse optimum does not make every optimum sparse
With equal weights and positive cycle sum $h$, every same-sign residual split with $\sum r_e=h$ is optimal. On the triangle this is a two-dimensional simplex. It contains the three single-edge residuals and the dense residual $(1,1,1)$. Thus cycle rank $1$ bounds the support of **some** optimum, while the optimal face can have dimension $2$.

---

## 8. Halting Pitfalls and Zeno's Trap

### 8.1 The Counterexample: Strict Descent Without Termination
Consider a single edge with report $c = 1$, weight $w = 1$.
Suppose an optimization routine generates a sequence of potential differences such that the cost at step $t$ is:

$$D_t = 2^{-t}$$

Notice:
1. **Strict Monotonic Descent:** At every single step, $D_{t+1} = 2^{-(t+1)} < 2^{-t} = D_t$.
2. **Infinite Rational Sequence:** The sequence strictly decreases for all $t \in \mathbb{N}$ without ever reaching the infimum $0$ at any finite $t$.

#### The Cardinal Halting Law:
> **Strict rational descent alone does NOT imply finite termination.**

To make a stopping argument, state which quantity is bounded and which calls must return:

- If all costs lie on a fixed lattice $\delta\mathbb Z$ with $\delta>0$, are bounded below, and each admitted step strictly decreases cost, there are finitely many admitted descents from a finite starting cost. Rejected attempts still need their own limit.
- A finite exhaustive search terminates if it visits its finite candidate set without repetition and every candidate check returns. Searching extreme points without these conditions is not a halting proof.
- A finite fuel wrapper bounds attempted transitions. A timeout or a proved bound is separately needed for each parser, solver, or external call. Fuel exhaustion means an unfinished computation, not convergence.

In the supplied `SymbolGameGovernor`, `turn` counts calls; the class has no fuel limit. Demo 1 enforces fuel in its outer `for` loop and reports `UNFINISHED` while cost is still positive. There is no `FUEL_EXHAUSTED` member in the governor's verdict enum. The native adapter has a separate 30-second subprocess timeout. Its forest cap counts complete forests, not every recursive branch or elapsed time.

---

## 9. Software Implementations and the 100,000 Forest Cap

Paper 001 provides two reference implementations:

### 9.1 The Native Rust Solver (`../../../../../../../engine/crates_rs/core_solvers/src/graph_phi1.rs`)
- **Algorithm:** Bounded exact exhaustive enumeration over spanning forests.
- **Safety Ceiling:** Capped strictly at 100,000 forests.
- **Behavior:**
  - If the graph has $\le 100,000$ spanning forests, it computes the exact rational minimum $\Phi_1(c)$ and returns `phi1`, `gauge`, and `forests_checked`.
  - If the search exceeds 100,000 forests, it **refuses when the next complete forest would exceed the cap**, with typed error `EnumerationLimit`. It does **not** return a partial or approximate minimum.
- **Limitation:** Exponential in graph size; returns the primal potential, but does not construct the dual circulation certificate.

### 9.2 The Paper-Local Python Reference (`code/symbol_game_governor.py`)
- Constructs both the primal potential $s^*$ and the dual circulation $\lambda^*$.
- Independently verifies the zero duality gap: $\langle \lambda^*, c \rangle = D_c(s^*)$.
- Implements a governor whose `CUT` admission rule requires strict cost descent. `ASSERT` changes reports and `RETRACT` restores a state; neither is covered by the fixed-report descent rule.

---

## 10. Lean 4 Toy Involutions and Claim Hygiene
The manuscript describes these narrowly scoped local statements:

1. `OddCycleObstruction.lean`: no assignment of signs $\pm1$ to the three vertices of a triangle makes every edge product equal to $-1$.
2. `InvolutionLaws.lean`: a configuration and its image under a supplied sign-reversing, weight-preserving map have signed natural-number weights summing to zero. The map and its hypotheses are supplied.
3. `NonAuthority.lean`: a declared policy is encoded as a type with one value. Its theorem holds by construction and checks no runtime behavior.

These descriptions do not establish a general graph LP, production implementation correctness, termination of arbitrary rational descent, a polynomial-time algorithm, or a physical fermion sign-problem solution. Read the actual theorem statements, pinned toolchain, and axiom report before claiming a successful formal replay. Those files must travel with the deposit.

To bridge a finite cochain model to a physical representation, specify the physical carrier, the representation, the map to the graph data, and a theorem stating exactly what signs, weights, or observables the map preserves. Any runtime or complexity claim needs its own correspondence proof and cost model.

## 11. Triangle recap and complete instructor key

These lines recap the Manuscript Triangle. The worked derivation is in section 5. The separate [instructor key](./instructor_key.md) covers all thirteen examination problems, a 100-point rubric, and the optional final challenges.

1. The coefficients are rational, the edge order is ab, bc, ca, and this graph has no declared 2-cells. A displayed cycle does not attach a face.
2. For $f = (0, -2, -1)$, $df = Bs^* = (-2, 1, 1)$, the residual is $(3, 0, 0)$, and the weighted cost is $3$. A feasible potential gives an upper bound on the minimum.
3. $\lambda = (1, 1, 1)$ has zero divergence and satisfies $|\lambda| \le w$ for $w = (1, 2, 3)$. Its objective is $3$, matching the candidate. With $w = (2, 2, 2)$, $\lambda = (2, 2, 2)$ gives objective $6$ and the same $f$ has cost $6$. The answer $2$ contradicts the matching primal and dual values.
4. Translating the potential variable leaves the quotient minimum unchanged. Replacing $c$ with $df$ changes its cohomology class when the original cycle sum is nonzero; that is a different instance, not gauge erasure.
5. A physical modeling bridge, an independently checked carrier interpretation, and any requested complexity theorem are still owed. No general fermion sign-problem solution follows.

The manuscript section [A certificate for optimality](../paper.md#3-a-certificate-for-optimality) supplies the coefficient system and move grammar. The package [deposit verifier](../verify_deposit.py) checks file custody rather than the truth of every answer. The standalone companion needs no external worksheet to define its assessed graph model. If the shared repository worksheet is included later, use a release-pinned link and verify it from the exported package.
