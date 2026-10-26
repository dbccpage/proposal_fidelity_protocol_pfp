---
documentation_contract: symbol-game-documentation/v1
title: 'Chapter 09: Reversal, Dynamical Zeta, Arithmetic Shadows, and Epistemic Quarantine'
kind: mathematical-reference
audience:
- researchers
- spectral-theorists
- evaluators
- coding-agents
status: active
maturity: exploratory
claim_status: exploratory-research-program
authority_effect: "None"
mathematical_status:
  definitions:
    - graph_orientation_reversal
    - free_dagger_path_profunctor
    - tripartite_zeta_separation
    - ihara_zeta_euler_product
    - bass_ihara_determinant_formula
    - ramanujan_spectral_bound
  prose_theorems:
    - orientation_reversal_preserves_cohomology_isomorphism
    - orbit_reversal_preserves_length_and_weight
    - functional_reflection_fallacy_refutation
    - ihara_reciprocal_polynomial_roots
    - ramanujan_graph_pole_modulus
  lean_theorems: []
  finite_computations:
    - debruijn_negative_control_reflection_failure
  declared_policies:
    - strict_epistemic_quarantine_fence
  applications: []
  open_conjectures:
    - signed_complex_spectral_reflection_conditions
coefficient_domain: "ℂ"
runtime_dependency: "Chapter 08 (Transfer Operators, Primitive Periodic Orbits, and Dynamical Zeta)"
governance_dependency: "governance-pfp"
---

# Chapter 09: Reversal, Dynamical Zeta, Arithmetic Shadows, and Epistemic Quarantine

**Status:** Exploratory Research Program (Spine Chapter 09)
**Authority:** None. This chapter investigates research conjectures and establishes strict epistemic quarantine fences separating discrete toy dynamics from classical arithmetic conjectures. It is **not** a normative operational ascent step.

---

## 1. Graph Orientation and Reversal

In discrete relational systems, directed transitions are oriented:
$$a \xrightarrow{\quad e \quad} b$$

- **Boundary Column Negation:** The boundary operator $\partial_1: C_1 \to C_0$ has matrix dimension $|V| \times |E|$. Reversing the orientation of all edges ($e = (a \to b) \mapsto e^{\mathrm{rev}} = (b \to a)$) negates each edge boundary:
  $$\partial_1(e^{\mathrm{rev}}) = a - b = -\partial_1(e)$$
  Thus, orientation reversal negates the boundary matrix: $\partial_1 \mapsto -\partial_1$ and $d_0 \mapsto -d_0$.
- **Cohomology Invariance:** In contrast to informal assertions, reversing edge orientations does **not** destroy cohomology: replacing edges with their opposites yields an isomorphic cohomology group on the opposite graph complex ($H^1(G^{\mathrm{op}}) \cong H^1(G)$).
- **Free Dagger Categories vs. Groupoids:** On an arbitrary directed graph, opposite edges do not automatically exist. Formally adjoining reversed arrows defines a **free dagger category** (equipped with an identity-on-objects contravariant involution $(-)^\dagger$ with $f^{\dagger\dagger} = f$). A dagger category must not be confused with a **groupoid**: in a dagger category, $f^\dagger \circ f$ is a self-adjoint endomorphism and is generally not the identity, whereas in a groupoid every arrow is invertible ($f^{-1} \circ f = \mathrm{id}$).

---

## 2. Orbit Reversal and Weight Invariance

Let $p = (v_1 \to v_2 \to \cdots \to v_k \to v_1)$ be a closed primitive periodic orbit.
- Traversal reversal yields $p^\dagger = (v_1 \to v_k \to \cdots \to v_2 \to v_1)$.
- **Length Invariant:** The discrete length of the reversed orbit is identical to the forward length:
  $$|p^\dagger| = |p|$$
- **Weight Invariance:** Under the generating weight $z^{|p|}$, orbit reversal preserves the term:
  $$z^{|p^\dagger|} = z^{|p|}$$

> **Key Observation:** Traversal reversal alone preserves orbit length. It does **not** invert the formal variable to $z^{-|p|}$, and cannot by itself generate a functional transformation $z \mapsto z^{-1}$ or $s \mapsto 1-s$.

---

## 3. Refuting the Functional Reflection Fallacy: A Grounded Negative Test

In speculative literature, it has been hypothesized that path reversal might automatically induce a functional reflection equation $s \leftrightarrow 1-s$ on the trace generating function $\zeta(s) = \operatorname{Tr}(\mathcal{P})$.

This hypothesis is **falsified by the exact computed benchmark of Chapter 08**:

> **Negative Control (Chapter 08 Full Binary Shift):**
> For the full binary de Bruijn shift, the dynamical zeta function was computed exactly:
> $$\zeta_A(z) = \frac{1}{1 - 2z}$$
> Under the standard spectral substitution $z = 2^{-s}$, this evaluates to:
> $$\zeta_A(s) = \frac{1}{1 - 2^{1-s}}$$
>
> - This function has a simple pole at $s = 1$ ($z = 1/2$).
> - It has **no finite zeros** anywhere in the complex plane $\mathbb{C}$.
> - It does **not** satisfy a functional reflection equation $\zeta(s) = \pm \zeta(1-s)$. In particular:
>   $$\zeta_A(0) = \frac{1}{1 - 2} = -1 \quad \neq \quad \zeta_A(1) = \infty$$

Periodic-orbit zeta functions in discrete dynamics exhibit poles determined by topological entropy ($h_{\mathrm{top}} = \log 2$); they do not inherit arithmetic functional equations without specialized arithmetic structures (e.g. Selberg trace formulas on compact hyperbolic Riemann surfaces).

---

## 4. The Tripartite Zeta Separation

To prevent conflation between discrete symbolic toy models and classical analytic number theory, the architecture enforces a strict tripartite separation:

$$\boxed{\text{Artin-Mazur Orbit Zeta} \quad \neq \quad \text{Tower Survivor Monoid Zeta} \quad \neq \quad \text{Classical Riemann Zeta}}$$

```text
+-------------------------------------------------------------------------+
| Tier 1: Discrete Dynamical Zeta (Checked Combinatorial Mechanics)      |
| - Finite graphs, wire grammar [a-z0-9<>], de Bruijn transfer matrix     |
| - Primitive periodic orbits with discrete length |p|                    |
| - Exact computed function: \zeta_A(z) = 1 / (1 - 2z)                    |
| - Single pole at z = 1/2; ZERO finite zeros in \mathbb{C}              |
+-------------------------------------------------------------------------+
                                 |  (speculative combinatorial abstraction)
                                 v
+-------------------------------------------------------------------------+
| Tier 2: Tower Survivor Monoid Zeta (Open Exploratory Program)           |
| - Free commutative monoid over persistent cohomology colimit H^1_\infty |
| - Formal Dirichlet series: \zeta_{surv}(s) = \prod (1 - e^{-s deg(p)})^{-1} |
| - Open Problem: Does any discrete cochain complex exhibit zeros or a    |
|   verified functional reflection s <-> 1-s?                             |
+-------------------------------------------------------------------------+
                                 |  (unsupported continuum leap)
                                 v
+-------------------------------------------------------------------------+
| Tier 3: Classical Riemann Zeta \zeta(s) (Unconnected Classical Math)   |
| - Continuous analytic continuation to the complex plane \mathbb{C}      |
| - Classical Riemann Hypothesis (Clay Millennium Problem)                |
| - Non-trivial zeros on the critical line \operatorname{Re}(s) = 1/2     |
+-------------------------------------------------------------------------+
```

---

## 5. Non-Backtracking Cycles, Ihara Zeta, and the Ramanujan Spectral Bound

Within the spectral research branch ($\text{transfer operators} \to \text{Artin–Mazur zeta} \to \text{reversal negative result} \to \text{Ihara zeta / Ramanujan graphs} \to \text{arithmetic quarantine}$), we examine the discrete spectral properties of non-backtracking graph walks without unhedged promotion to continuum analytic number theory.

### 5.1 Prime Non-Backtracking Cycles & the Bass-Ihara Formula
Let $G = (V, E)$ be a finite, connected $(q+1)$-regular graph with $q \ge 2$, vertex count $N = |V|$, circuit rank $r = |E| - |V| + 1$, and adjacency matrix $A$.
*(Note: For $q = 1$, i.e. 2-regular polygon graphs like the 3-cycle $C_3$, $|E| - |V| = 0$, so $(1 - u^2)^0 = 1$ and $\zeta_{C_3}(u)^{-1} = (1 - u^3)^2$, which has roots at cube roots of unity with no pole at $u = -1$. Assuming $q \ge 2$ ensures $|E| - |V| = N(q - 1)/2 \ge 1$, so the trivial factor $(1 - u^2)$ is present).*

- **Prime Non-Backtracking Cycles:** In Ihara's zeta function, a cycle is not an unrestricted walk. An admissible closed cycle must be **tailless and non-backtracking** ($e_{i+1} \ne e_i^{-1}$), and is **prime** if it is not a positive power of a shorter non-backtracking cycle.
- **Euler Product:** The Ihara zeta function is defined for complex $u$ with $|u|$ sufficiently small:
  $$\zeta_G(u) := \prod_{[p]} \frac{1}{1 - u^{|p|}}$$
  taken over equivalence classes of prime, tailless, non-backtracking cycles $[p]$.

By the Bass–Ihara determinant formula, $\zeta_G(u)$ is a rational function whose reciprocal is an exact polynomial over $\mathbb{Z}$:
$$\zeta_G(u)^{-1} = (1 - u^2)^{|E| - |V|} \det(I - A u + q u^2 I)$$

### 5.2 The Ramanujan Bound: Adjacency Spectrum vs. Zeta Poles
For $q \ge 2$, the **poles of $\zeta_G(u)$** are the roots of the reciprocal polynomial $\zeta_G(u)^{-1} = 0$:
1. Trivial poles at $u = \pm 1$ (from $(1 - u^2)^{|E|-|V|}$),
2. The roots of the quadratic equation $q u^2 - \lambda u + 1 = 0$ for each eigenvalue $\lambda$ of the adjacency matrix $A$.

> **The Ramanujan Spectral Condition:**
> A $(q+1)$-regular graph is **Ramanujan** if every non-trivial adjacency eigenvalue $\lambda \ne \pm (q+1)$ satisfies the Ramanujan bound:
> $$|\lambda| \le 2\sqrt{q}$$
> *(Note: The Alon–Boppana theorem states that for any sequence of $(q+1)$-regular graphs $G_n$ with $|V_n| \to \infty$, the second largest adjacency eigenvalue $\lambda_2(G_n)$ satisfies $\liminf_{n \to \infty} \lambda_2(G_n) \ge 2\sqrt{q}$ [since the largest eigenvalue is identically $\lambda_1 = q+1$], proving the asymptotic optimality of this spectral bound).*
> When $|\lambda| \le 2\sqrt{q}$, the discriminant $\lambda^2 - 4q \le 0$ is non-positive. For $q \ge 2$, the roots of $q u^2 - \lambda u + 1 = 0$ are complex conjugates:
> $$u = \frac{\lambda \pm i\sqrt{4q - \lambda^2}}{2q}$$
> with exact modulus:
> $$|u| = \sqrt{\frac{\lambda^2 + (4q - \lambda^2)}{4q^2}} = \frac{1}{\sqrt{q}} = q^{-1/2}$$
> Under the spectral variable substitution $u = q^{-s}$ (well-defined for $q \ge 2$), the modulus condition $|u| = q^{-1/2}$ corresponds to $\operatorname{Re}(s) = 1/2$.

### 5.3 The Completed Regular-Graph Functional Equation
Let $P(u) = \det(I - A u + q u^2 I)$. By factoring $q u^2$ from the matrix argument:
$$P((qu)^{-1}) = \det\left(I - \frac{A}{qu} + \frac{q}{(qu)^2} I\right) = \det\left(\frac{q u^2 I - A u + I}{q u^2}\right) = (q u^2)^{-N} P(u)$$
Consequently, $u^{-N} P(u)$ (or its reciprocal $u^N / P(u)$) is invariant under $u \mapsto (qu)^{-1}$. Under the parameterization $u = q^{-s}$, the transformation $u \mapsto (qu)^{-1}$ maps $q^{-s} \mapsto q^{-(1-s)}$, exchanging $s \leftrightarrow 1-s$.
This is a mathematically established, completed functional reflection symmetry on regular graphs, distinct from the raw uncompleted shift reversal negative control.

---

## 6. Epistemic Quarantine Ledger

In strict adherence to the Claim Hygiene Rule:

### 6.1 What This Formalism Supports
1. Demonstrates that orientation reversal on directed graphs negates boundary operator matrices while preserving cohomology up to isomorphism.
2. Demonstrates that orbit reversal preserves discrete orbit length and weight, and refutes the conjecture that path reversal alone automatically forces an uncompleted $s \leftrightarrow 1-s$ functional reflection.
3. Formulates the Bass–Ihara determinant formula for non-backtracking cycles on $(q+1)$-regular graphs ($q \ge 2$), proving that the Ramanujan bound $|\lambda| \le 2\sqrt{q}$ forces non-trivial poles of $\zeta_G(u)$ onto the critical circle $|u| = q^{-1/2}$, and derives the completed regular-graph functional equation $P((qu)^{-1}) = (qu^2)^{-N} P(u)$.
4. Provides an exact tripartite separation between discrete dynamical zeta products, formal survivor monoid series, and classical arithmetic functions.

### 6.2 What This Formalism Does NOT Support
1. **Does NOT establish or prove the classical Riemann Hypothesis:** While the discrete dynamical zeta $\zeta_A(z) = (1-2z)^{-1}$ and the Ihara zeta $\zeta_G(u)$ are rational functions arising from finite matrix operators, rational graph zeta functions generally possess **infinitely many primitive orbit/cycle classes** (for example, the words $0^{n-1}1$ for $n \ge 2$ in the binary shift, or arbitrarily long tailless non-backtracking cycles on $K_4$). Rationality stems from finite matrix dimension, not a finite Euler product. These discrete graph rational functions carry no derivation chain to the classical Riemann zeta $\zeta(s) = \prod_p (1 - p^{-s})^{-1}$.
2. **Does NOT establish reflection symmetry for raw uncompleted shifts:** As verified by the Chapter 08 negative control, raw uncompleted path reversal on the binary shift yields $\zeta_A(z) = (1-2z)^{-1}$, which has no finite zeros and fails functional reflection ($\zeta_A(0) \ne \zeta_A(1)$).
3. **Does NOT derive continuum spacetime, quantum gravity, or fermion sign problem cancellation:** Such analogies remain unmechanized heuristic metaphors.

### 6.3 Narrowest Defensible Claim
> *On discrete $(q+1)$-regular graphs with $q \ge 2$, the Ihara zeta function is a rational function whose non-trivial poles lie on the circle $|u| = q^{-1/2}$ if and only if the graph satisfies the Ramanujan spectral bound $|\lambda| \le 2\sqrt{q}$, and its characteristic determinant satisfies the completed functional reflection equation $P((qu)^{-1}) = (qu^2)^{-N} P(u)$ ($s \leftrightarrow 1-s$ under $u = q^{-s}$). Raw path reversal on unrestricted shift systems does not force functional reflection, and these discrete graph identities do not prove or establish the classical Riemann Hypothesis for arithmetic zeta functions, which remains strictly quarantined.*
