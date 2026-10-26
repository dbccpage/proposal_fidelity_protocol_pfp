---
documentation_contract: symbol-game-documentation/v1
title: 'Chapter 04: Minimal Representatives, Hodge Decomposition, and the Difference Between Them'
kind: mathematical-reference
audience:
- researchers
- topologists
- optimization-engineers
- coding-agents
status: active
maturity: canonical
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - l1_minimal_representative
    - canonical_selector_pi1
    - graded_inner_products
    - discrete_hodge_decomposition
    - discrete_1_laplacian
    - harmonic_cochain_space
  prose_theorems:
    - l1_counterexample_non_uniqueness_non_sparsity
    - pi1_well_definedness_rational_existence_uniqueness
    - discrete_hodge_orthogonal_direct_sum
    - primal_vs_dual_uniqueness_separation
  lean_theorems: []
  finite_computations:
    - three_cycle_l1_minimizer_counterexample
  declared_policies:
    - rational_lexicographic_tie_breaking
  applications: []
  open_conjectures: []
coefficient_domain: "ℚ (with Positive Diagonal Weights)"
runtime_dependency: "Chapter 02 (Cochain Complexes, Repairs, and Quotients)"
governance_dependency: "None"
---

# Chapter 04: Minimal Representatives, Hodge Decomposition, and the Difference Between Them

**Status:** Canonical Mathematics Specification (Spine Chapter 04)
**Authority:** None. Polyhedral $\ell^1$ optimization and discrete Hodge theory on finite cell complexes.

---

## 1. Two Different Reduction Philosophies

When a cochain $c \in C^1$ has a non-trivial quotient class $[c] \in Q^1 = C^1 / \operatorname{im}(d_0)$, we seek a canonical representative inside the affine coset $c + \operatorname{im}(d_0)$. There are two different mathematical ways to select such a representative:

1. **$\ell^1$ Polyhedral Minimization:** Minimize the discrete sum of absolute discrepancies $\|c - d_0 \alpha\|_{1, \omega_1}$. This preserves sparsity and polyhedral boundaries, but is non-linear and not inherently orthogonal.
2. **$\ell^2$ Least-Squares Projection onto $(\operatorname{im} d_0)^\perp$:** Project orthogonally with respect to an inner product onto the orthogonal complement of the coboundary image: $(\operatorname{im} d_0)^\perp = \mathcal{H}^1 \oplus \operatorname{im}(d_1^*)$. The least-squares representative inside $c + \operatorname{im}(d_0)$ is:
   $$c_{\mathrm{LS}} = \operatorname{proj}_{(\operatorname{im} d_0)^\perp}(c) = h + d_1^* \beta$$
   where $c = d_0 \alpha + h + d_1^* \beta$. This least-squares coset representative is **harmonic** ($c_{\mathrm{LS}} = h \in \mathcal{H}^1$) **if and only if the input cochain is closed** ($d_1 c = 0$, meaning $[c] \in H^1 = \ker(d_1) / \operatorname{im}(d_0)$). When $c$ is not closed ($d_1 c \ne 0$), projecting purely into $\mathcal{H}^1$ discards the non-zero coexact component $d_1^* \beta$ and can leave the affine coset $c + \operatorname{im}(d_0)$ entirely.

> **Filled-Triangle Counterexample (Harmonic Projection Leaves the Coset):**
> Consider the filled oriented triangle with 3 vertices, 3 edges, and 1 face:
> $$d_0 = \begin{pmatrix}-1&1&0\\0&-1&1\\1&0&-1\end{pmatrix}, \qquad d_1 = (1, 1, 1), \qquad c = (1, 1, 1)$$
> Here $d_1 c = 3 \ne 0$. Because the 2-cell fills the 1-cycle, the harmonic space is trivial: $\mathcal{H}^1 = \{0\}$. Harmonic projection yields $0$, which does **not** belong to the coset $c + \operatorname{im}(d_0)$ (since $c \notin \operatorname{im}(d_0)$). The true least-squared-norm representative in $c + \operatorname{im}(d_0)$ is the projection onto $(\operatorname{im} d_0)^\perp$, which here is $c$ itself (which is entirely coexact: with unit weights $d_1^* = d_1^T$, so $c = d_1^T(1) = (1, 1, 1)$).
>
> *Correction (2026-10-20):* an earlier version wrote $c = d_1^*(1/3)$. That is wrong for unit weights, because $d_1^T(1/3) = (1/3, 1/3, 1/3) \ne c$. The coefficient $1/3$ appears in the projection formula $\beta = (d_1 d_1^T)^{-1} d_1 c = 3/3 = 1$, which gives $\beta = 1$.
>
> **Crucial Distinction:** Minimizing the coset's squared norm $\|c - d_0 \alpha\|_2^2$ over $\alpha \in C^0$ is distinct from minimizing Laplacian energy $\langle x, \Delta_1 x \rangle$; every harmonic cochain has zero Laplacian energy, but only closed cochains admit harmonic representatives within their quotient cosets.

---

## 2. $\ell^1$-Minimal Representatives and Polyhedral Geometry

Let $C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2$ be a finite cochain complex over $\mathbb{Q}$ with positive rational edge weights $\omega_e > 0$.

A cochain $c^* \in [c]$ is an **$\ell^1$-minimal representative** if it achieves the minimal quotient defect mass:
$$\|c^*\|_{1, \omega_1} = \Phi_1([c]) = \min_{\alpha \in C^0} \|c - d_0 \alpha\|_{1, \omega_1}$$

### 2.1 The 3-Cycle Counterexample: Non-Uniqueness and Fractional Density

A common misconception is that $\ell^1$ minimization always forces sparse, unique, or integer solutions. This is refuted by an explicit finite computation:

> **Finite Counterexample:**
> Consider an oriented 3-cycle with vertices $\{a, b, c\}$, uniform weights $\omega_e = 1$, and edge values:
> $$c(a \to b) = 1/3, \quad c(b \to c) = 1/3, \quad c(c \to a) = 1/3$$
> The directed cycle sum is $1/3 + 1/3 + 1/3 = 1$. Since any exact repair $d_0 \alpha$ sums to zero around the closed cycle, the minimal $\ell^1$ defect mass is:
> $$\Phi_1([c]) = 1$$
>
> - **Dense Candidate ($c_1^*$):** Choosing $\alpha = (0, 0, 0)$ gives $c_1^* = (1/3, 1/3, 1/3)$ with $\|c_1^*\|_1 = 1$. This minimizer is completely dense and fractional.
> - **Sparse Candidate ($c_2^*$):** Choosing $\alpha(a)=0, \alpha(b)=-2/3, \alpha(c)=-1/3$ gives $c_2^* = (1, 0, 0)$ with $\|c_2^*\|_1 = 1$. This minimizer is sparse.
> - **Entire Continuum of Minimizers:** Any convex combination $\lambda c_1^* + (1-\lambda) c_2^*$ for rational $\lambda \in [0, 1] \cap \mathbb{Q}$ achieves exact norm $1$. The full minimizer set is larger than this segment. Every representative $x$ in the coset satisfies $x_1 + x_2 + x_3 = 1$, so $\|x\|_1 \ge |x_1 + x_2 + x_3| = 1$, with equality exactly when every coordinate is non-negative. Hence the minimizer set is the whole triangle $M_0([c]) = \{x \ge 0 : x_1 + x_2 + x_3 = 1\}$, the convex hull of $(1,0,0)$, $(0,1,0)$ and $(0,0,1)$. The segment from $c_1^*$ to $c_2^*$ is one line inside it.
>
> *Conclusion:* $\ell^1$ minimizers in discrete complexes need not be unique, need not be sparse, and need not be integral.

---

## 3. The Canonical $\ell^1$ Selection Operator: $\Pi_1$

Because the set of minimizers forms a multi-dimensional rational convex polyhedron, a single-valued representative operator requires an explicit **deterministic selection rule** over $\mathbb{Q}$.

### 3.1 Nonconvexity of Maximum-Sparsity Subsets & Finite-Face Selection

Let $[c] \in Q^1(\mathbb{Q})$.
1. **The Minimal Polyhedron $M_0([c])$:**
   $$M_0([c]) = \{ x \in [c] : \|x\|_{1, \omega_1} = \Phi_1([c]) \} \subset C^1(\mathbb{Q})$$
   $M_0([c])$ is a non-empty, bounded rational polyhedron.
2. **Stage 1 (Maximal Support Sparsity via Finite Faces):**
   Let $\operatorname{supp}_0(x) = \{e \in E : x(e) = 0\}$ denote the zero-coordinate set of $x$. The maximum number of zero coordinates is:
   $$z_{\max}([c]) = \max_{x \in M_0([c])} |\operatorname{supp}_0(x)|$$
   The subset $M_1([c]) = \{ x \in M_0([c]) : |\operatorname{supp}_0(x)| = z_{\max}([c]) \}$ of maximizers of zero count is generally **nonconvex** (for instance, in the 3-cycle example, $M_1 = \{(1,0,0), (0,1,0), (0,0,1)\}$; convex midpoints like $(1/2, 1/2, 0) \in M_0$ have strictly fewer zeros).
   To resolve this nonconvexity constructively over $\mathbb{Q}$, we enumerate all zero-index sets $Z \subseteq E$ of cardinality $|Z| = z_{\max}([c])$ for which the face
   $$F_Z([c]) = M_0([c]) \cap \{ x \in C^1(\mathbb{Q}) : x(e) = 0 \; \forall e \in Z \}$$
   is non-empty. Each non-empty face $F_Z([c])$ is a bounded rational convex polyhedron.
3. **Stage 2 (Lexicographic LP over Candidate Faces):**
   Fix a canonical edge ordering $e_1 < e_2 < \dots < e_{|E|}$. For each non-empty candidate face $F_Z([c])$, sequential linear programming over the coordinates $e_1, \dots, e_{|E|}$ yields a unique vertex $x_Z^* \in F_Z([c]) \cap \mathbb{Q}^{|E|}$.
   The canonical selector chooses the lexicographically minimal vector among this finite candidate set:
   $$\boxed{\Pi_1([c]) := \min_{Z} \left\{ \operatorname{lex-min}_{e_1, \dots, e_{|E|}} (F_Z([c])) \right\}}$$

### 3.2 Existence and Uniqueness Theorem

> **Theorem ($\mathbb{Q}$-Well-Definedness of $\Pi_1$):**
> For any $[c] \in Q^1(\mathbb{Q})$, the cochain $\Pi_1([c])$ exists, is unique, and has rational coordinates in $\mathbb{Q}$.
> *Proof:* The optimal value $\Phi_1([c])$ is attained in $\mathbb{Q}$ by the fundamental theorem of linear programming over ordered fields. The integer set $\{|\operatorname{supp}_0(x)| : x \in M_0([c])\}$ is non-empty and bounded above by $|E|$, so its maximum $z_{\max}$ exists and is achieved on at least one vertex of $M_0([c])$. The family of subsets $Z \subseteq E$ with $|Z| = z_{\max}$ is finite (bounded by $\binom{|E|}{z_{\max}} \le 2^{|E|}$). Each non-empty face $F_Z([c])$ is a closed, bounded rational polytope. Sequential LP over a non-empty rational polytope terminates at a unique rational vertex $x_Z^*$. The minimum of finitely many rational vectors under lexicographical order is uniquely attained in $\mathbb{Q}$.
> *Combinatorial Search Budget:* The maximum-sparsity objective requires solving linear feasibility and lexicographic LPs over at most $\binom{|E|}{z_{\max}}$ faces; it is not discharged by the initial LP certificate alone.

**Worked answer for the 3-cycle (2026-10-20).** Order the edges $e_1 = (a \to b)$, $e_2 = (b \to c)$, $e_3 = (c \to a)$.

1. $M_0([c])$ is the triangle found in Section 2.1.
2. No minimizer has three zeros, because the coordinates sum to 1. The three vertices have two zeros each, so $z_{\max} = 2$.
3. The three faces with two zeros are the single points $F_{\{e_2, e_3\}} = \{(1,0,0)\}$, $F_{\{e_1, e_3\}} = \{(0,1,0)\}$ and $F_{\{e_1, e_2\}} = \{(0,0,1)\}$.
4. Compare the three candidates lexicographically. $(0,0,1)$ and $(0,1,0)$ both start with 0, which is smaller than the 1 in $(1,0,0)$. Their second coordinates are 0 and 1, so $(0,0,1)$ is the smallest.

So $\Pi_1([c]) = (0, 0, 1)$: the selector puts the whole unit of circulation on edge $c \to a$. Changing the edge order changes the answer, which is why the ordering is part of the declared policy.

### 3.3 Primal vs. Dual Separation
Primal cochains $c \in C^1$ and dual witnesses $y \in (C^1)^*$ live in dual spaces. **Dual witness uniqueness does not imply primal minimizer uniqueness**. In the 3-cycle counterexample above, the normalized optimal dual cycle witness $y^* = (1, 1, 1)$ is unique ($d_0^* y^* = 0, \|y^*\|_\infty = 1, \langle y^*, c \rangle = 1$), whereas the primal problem has an entire segment of minimizers.

---

## 4. Discrete Hodge Decomposition

Now consider the $\ell^2$ quadratic formulation. To construct adjoints $d_0^*$ and $d_1^*$, **positive-definite inner products must be explicitly declared on every cochain degree**:

$$\langle \phi, \psi \rangle_{C^0} = \sum_{x \in V} \omega_0(x) \phi(x) \psi(x), \quad \langle x, y \rangle_{C^1} = \sum_{e \in E} \omega_1(e) x(e) y(e), \quad \langle \alpha, \beta \rangle_{C^2} = \sum_{f \in F} \omega_2(f) \alpha(f) \beta(f)$$
where $\omega_0, \omega_1, \omega_2$ are strictly positive rational weight vectors.

The adjoint coboundary operators are uniquely determined by:
$$\langle d_0 \alpha, x \rangle_{C^1} = \langle \alpha, d_0^* x \rangle_{C^0}, \qquad \langle d_1 x, \beta \rangle_{C^2} = \langle x, d_1^* \beta \rangle_{C^1}$$

### 4.1 The Orthogonal Direct Sum Theorem

For any finite cell complex over $\mathbb{Q}$, the 1-cochains decompose into three mutually orthogonal subspaces:

$$\boxed{C^1 = \operatorname{im}(d_0) \;\oplus\; \mathcal{H}^1 \;\oplus\; \operatorname{im}(d_1^*)}$$

where:
1. **$\operatorname{im}(d_0)$ (Exact Cochains / Gradient Flows):** $\{d_0 \alpha : \alpha \in C^0\}$,
2. **$\operatorname{im}(d_1^*)$ (Coexact Cochains / Curl Flows):** $\{d_1^* \beta : \beta \in C^2\}$,
3. **$\mathcal{H}^1$ (Harmonic Cochains):** The intersection $\ker(d_1) \cap \ker(d_0^*)$.

### 4.2 The Discrete 1-Laplacian

The discrete Hodge 1-Laplacian $\Delta_1: C^1 \to C^1$ is the self-adjoint, positive semi-definite operator:
$$\Delta_1 := d_0 d_0^* + d_1^* d_1$$
The harmonic space is precisely the null space of the Laplacian:
$$\mathcal{H}^1 = \ker(\Delta_1)$$
Every cohomology class $[c] \in H^1 = \ker(d_1) / \operatorname{im}(d_0)$ contains a **unique harmonic representative** $h \in \mathcal{H}^1$.

---

## 5. Summary Comparison

| Feature | $\ell^1$-Minimal Representative ($\Pi_1$) | Harmonic Representative ($\mathcal{H}^1$) / Coset Least-Squares |
| :--- | :--- | :--- |
| **Objective** | Minimize $\ell^1$ discrepancy $\|c - d_0 \alpha\|_1$ | Harmonic: minimize Laplacian energy $\langle x, \Delta_1 x \rangle = 0$.<br>Coset LS: minimize squared $\ell^2$ norm $\|c - d_0 \alpha\|_2^2$. |
| **Input Class Scope** | Any quotient class $[c] \in Q^1 = C^1 / \operatorname{im}(d_0)$ | Harmonic requires closed class $[c] \in H^1$ ($d_1 c = 0$).<br>Arbitrary $[c] \in Q^1$ projects to $h + d_1^* \beta \in (\operatorname{im} d_0)^\perp$. |
| **Coset Containment** | Always belongs to $c + \operatorname{im}(d_0)$ | Harmonic projection can leave $c + \operatorname{im}(d_0)$ if $d_1 c \ne 0$.<br>Projection onto $(\operatorname{im} d_0)^\perp$ stays in coset. |
| **Projection Nature** | Non-linear polyhedral selection | Linear orthogonal projection |
| **Sparsity** | Strongly favors sparse support | Tends to produce dense, fractional values |
| **Uniqueness** | Requires two-stage tie-breaking ($\Pi_1$) | Uniquely determined by orthogonal complement |
| **Higher Cells ($d_1$)** | Depends only on $C^0 \xrightarrow{d_0} C^1$ | Requires inner products on $C^0, C^1, C^2$ and $d_1$ |
