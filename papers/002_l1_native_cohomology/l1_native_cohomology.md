---
title: "$\\ell^1$-Native Cohomology of Finite Defect Fields"
subtitle: "Quotient Norms, Dual Circulations, Sparse Representatives, and the $L^p$ Geometric Family"
author: "Jeremy H. Carroll"
date: "2026-10-15"
version: "6.5.2"
---

<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD025 MD024 -->

```{=latex}
\begingroup
\raggedright
\noindent\textbf{License:} Creative Commons Attribution 4.0 International (CC-BY-4.0)\\[0.4em]
\noindent\textbf{Scope:} Finite-dimensional convex and combinatorial graph cohomology.\\[0.4em]
\noindent\textbf{Version:} 6.5.2 (2026-10-15)
\endgroup
```

## Notation and Mathematical Setup {-}

We fix standard notation for finite cell complexes and convex analysis used throughout this monograph:

- $G = (V,E)$: A finite directed graph with $n = |V|$ vertices and $m = |E|$ edges. Edge orientations are fixed for bookkeeping.
- $C^0 = \mathbb{R}^V$, $C^1 = \mathbb{R}^E$: Finite-dimensional vector spaces of 0-cochains (vertex potentials) and 1-cochains (edge differences).
- $d_0: C^0 \to C^1$: Incidence coboundary operator, $(d_0 f)(u,v) = f(v) - f(u)$ for directed edge $e = (u,v) \in E$, represented by the $m \times n$ incidence matrix $\mathbf{B}$.
- $B^1 = \operatorname{im} d_0$: The subspace of exact 1-cochains (pure gradient potentials).
- $Q^1 = C^1 / B^1$: The first cochain quotient space of dimension $\beta = m - n + c$, where $c$ is the number of connected components (the cycle rank or first Betti number of $G$).
- $\mathbf{w} \in \mathbb{R}_{>0}^E$: A strictly positive edge weight vector.
- $\Phi_p([\omega]) = \inf_{f \in C^0} \|\omega + d_0 f\|_{p,\mathbf{w}}$: The weighted quotient $L^p$ norm for $p \in [1, \infty]$.
- $Z_1(G;\mathbb{R}) = \ker(\mathbf{B}^\top)$: Real divergence-free circulations, used for the LP dual. Integral cycles $Z_1(G;\mathbb{Z}) = \ker(\mathbf{B}^\top)\cap\mathbb{Z}^E$ are used for branch-independent multiplicative holonomy.
- For 2-simplicial complexes $K = (V,E,F)$, $d_1: C^1 \to C^2$ denotes the face coboundary operator, satisfying discrete Bianchi nilpotency $d_1 \circ d_0 = 0$.

# Abstract {-}

For a finite directed graph with strictly positive edge weights, we study the
family of weighted $L^p$ norms ($p \in [1, \infty)$, complemented by the separate weighted Chebyshev endpoint norm at $p = \infty$) induced on the first cochain
quotient space $Q^1 = C^1 / \operatorname{im} d_0$. The quotient infimum is attained for all $p \in [1, \infty]$,
defines a genuine quotient norm $\Phi_p$, and satisfies Fenchel-Rockafellar duality with
conjugate exponent $q = p/(p-1)$, characterizing the quotient norm as a maximum
circulation pairing subject to dual $L^q$ capacity bounds. We establish the
geometric transition across regimes: (i) $p = 1$ is polyhedral and non-strictly
convex, may admit non-unique primal minimizers, exhibits sparse cycle-rank support
bounds ($|\operatorname{supp}(r)| \le \beta$), and admits exact rational linear programming
duality; (ii) for $p \in (1, \infty)$ the weighted cochain normed space is uniformly convex, and the powered objective $J_p(f)=\frac1p\sum_e w_e|\omega_e+(\mathbf{B}f)_e|^p$ is strictly convex on gauge-fixed potentials (one zero potential per connected component), ensuring a strictly unique optimal residual $\mathbf{r}_p^* = \boldsymbol{\omega} + \mathbf{B}\mathbf{f}_p^*$ and unique gauge-fixed potential $\mathbf{f}_p^*$ characterized by nonlinear graph
$p$-Laplacian optimality $\mathbf{B}^\top (\mathbf{w} \odot |\mathbf{r}|^{p-1} \odot \operatorname{sgn}\mathbf{r}) = \mathbf{0}, \mathbf{r} = \boldsymbol{\omega} + \mathbf{B}\mathbf{f}$;
(iii) $p = 2$ recovers classical Hilbertian Hodge-Helmholtz orthogonal
decomposition with Moore-Penrose graph Laplacian solutions and weighted dual
circulation witnesses $\mathbf{z}_2^* = \mathbf{W}\mathbf{r}_2^* / \|\mathbf{r}_2^*\|_{2,\mathbf{w}}$, where $\mathbf{W}=\operatorname{diag}(\mathbf{w})$, when $\mathbf{r}_2^* \ne \mathbf{0}$ (with $\mathbf{z}_2^* = \mathbf{0}$ at zero residual); (iv) $p = \infty$ corresponds to discrete Chebyshev
approximation governed by active-edge subgradient pairing under its separate weighted endpoint convention $\|x\|_{\infty,\mathbf{w}} = \max_e w_e |x_e|$ (with the general Aronsson equation withdrawn for arbitrary cochains); and (v) the $p \to 1^+$
limit is characterized via unconditional secondary entropy minimization over the optimal $L^1$ face. We also show that
simplicial coboundary operators satisfy discrete Bianchi nilpotency with
gauge-orbit circulation invariance, that off-diagonal quantum state coherence is bounded under Schatten trace norms, and that additive real flux $\Phi_1([\omega])$ of a chosen real lift is distinguished from branch-independent $U(1)$ phase holonomy and period-minimized quotient defect. These general finite-dimensional statements have prose proofs in the manuscript and are classified as classical background. Lean mechanizes the conditional finite integer certificate L1C-TG and the specified finite-model lemmas for L1C-T1, L1C-T2, L1C-T3, L1C-T4, L1C-T5, and L1C-T7; this formalization scope is distinct from mathematical proof and originality.

Jiang, Lim, Yao, and Ye [9, preprint v2, §6.1] already formulate weighted $L^1$ projection of edge flows onto gradients and its dual over bounded divergence-free flows. Here the contribution is a presentation through weighted finite-graph quotient optimization and exact, independently checkable certificates, a rational computational companion, and mechanization of specified finite integer certificate statements in Lean. The bounded-circulation dual is classical background.


# Why a researcher should care {-}

Least squares ($p=2$) spreads error globally over all edges. $L^1$ quotient
minimization instead localizes defect on sparse cycle representatives while
retaining an exact rational dual certificate. The complete $L^p$ family connects
sparse polyhedral localization ($p=1$), strictly unique nonlinear
$p$-Laplacian projections ($p \in (1, \infty)$), classical Hilbertian Hodge theory
($p=2$), and maximal-error Chebyshev suppression ($p=\infty$, under its separate weighted endpoint convention). The certificate presentation connects these classical graph and convex constructions with machine-checkable finite witnesses.

# Falsifiability {-}

The prose propositions and the separately scoped Lean theorems have the hypotheses stated in their sections and claim records. A mathematical conclusion would fail if a positive-weight finite instance has no attained
minimum for some $p \in [1, \infty]$, if primal and dual values differ for an
optimal pair, if data satisfying all stated hypotheses of Theorem L1C-T4 or
LpC-T3 fail their conclusions, if for $p \in (1, \infty)$ two distinct gauge-fixed potentials (one fixed vertex per component)
both minimize the quotient objective, if the nonlinear $p$-Laplacian Euler-Lagrange
equation fails at an optimal potential, if some class lacks an $L^1$ optimum with
support at most the cycle rank, if an integral instance has no integral $L^1$ optimum,
if the $p \to 1^+$ trajectory fails to converge to an $L^1$ minimizer, if a
2-simplicial complex has non-vanishing field curvature $d_1(d_0 f) \ne 0$ for a
pure gauge potential, or if a finite quantum state violates the off-diagonal
Schatten-$p$ or trace coherence bound. The companion code and tests check solver
success, primal/dual conditions, support bounds, exact-shift invariance,
nilpotency, and quantum coherence bounds across enumerated instances; it also
includes an instance on which an $L^2$ surrogate reports the wrong $L^1$ value.

# 1. Finite graph cochains and $L^p$ norms

Let $G = (V,E)$ be a finite directed graph. Orientation is bookkeeping: reversing
an edge negates its cochain coordinate. Put

$$C^0 = \mathbb{R}^V, \quad C^1 = \mathbb{R}^E, \quad \text{and} \quad (d_0 f)(u,v) = f(v) - f(u).$$

When considering 1-dimensional graph carriers without higher faces, $d_1 = 0$, so every edge cochain is closed, while exact
cochains form $B^1 = \text{im } d_0$. The first cochain quotient is

$$Q^1 = C^1 / B^1.$$

Fix weights $w_e > 0$ for all $e \in E$. For $p \in [1, \infty)$, the weighted $L^p$ norm on $C^1$ is

$$\|x\|_{p,\mathbf{w}} = \left( \sum_{e \in E} w_e |x_e|^p \right)^{1/p},$$

and for $p = \infty$, the weighted $L^\infty$ norm is defined under the Chebyshev convention

$$\|x\|_{\infty,\mathbf{w}} = \max_{e \in E} w_e |x_e|.$$

**Remark on the $p=\infty$ endpoint weighting convention.** For non-uniform weights $\mathbf{w}$, the Chebyshev endpoint norm $\|x\|_{\infty,\mathbf{w}} = \max_{e \in E} w_e |x_e|$ is a separate weighted endpoint convention chosen for maximal weighted coordinate error suppression (standard in discrete Chebyshev approximation and computational engineering). It does not coincide with the point-wise analytic limit $\lim_{p \to \infty} \|x\|_{p,\mathbf{w}} = \max_{e \in E} |x_e|$ of the finite-$p$ weighted norms $(\sum w_e |x_e|^p)^{1/p}$. On an unweighted graph ($w_e = 1$ for all $e$), the two conventions coincide and the finite-$p$ norms interpolate continuously to $\ell^\infty$. For non-uniform weights (for example, on a triangle with cycle flux 1 and weights $(1,2,3)$, where $\lim_{p\to\infty}\Phi_p = 1/3$ whereas the defined Chebyshev defect is $\Phi_\infty = 6/11$), the $p = \infty$ problem is treated as a separate polyhedral endpoint convention with its own active-edge subgradient pairing (see §4.4).

For $p = 1$, this specializes to the polyhedral weighted $L^1$ norm $\|x\|_{1,\mathbf{w}} = \sum_{e \in E} w_e |x_e|$.
For a quotient class $[\omega] \in Q^1$ and $p \in [1, \infty]$, set

$$\Phi_p([\omega]) = \inf_{f \in C^0} \|\omega + d_0 f\|_{p,\mathbf{w}}.$$

All results extend componentwise to disconnected graphs. For concise proofs we
assume $G$ is connected and write $n = |V|$, $m = |E|$, and
$\beta = m - n + 1 = \dim Q^1$.

# 2. Attainment and quotient norm

## Theorem LpC-T1 — Lp quotient attainment

For every $p \in [1, \infty]$ and every $\omega \in C^1$, the infimum defining $\Phi_p([\omega])$ is attained.

**Proof.** Fix a root vertex $v_0 \in V$ and restrict to the gauge-fixed subspace
$F = \{f \in C^0 : f(v_j) = 0\text{ for one root }v_j\text{ per component}\}$. Connectedness makes $d_0|_F$ injective. In finite dimension,
all norms are equivalent and an injective linear map is bounded below: for any $p \in [1, \infty]$,
there exists $c_p > 0$ such that $\|d_0 f\|_{p,\mathbf{w}} \ge c_p \|f\|$ for all $f \in F$. Hence
$$\|\omega + d_0 f\|_{p,\mathbf{w}} \ge c_p \|f\| - \|\omega\|_{p,\mathbf{w}},$$
so the objective is coercive on $F$. Because $f \mapsto \|\omega + d_0 f\|_{p,\mathbf{w}}$ is continuous
on the finite-dimensional space $F$, it attains its minimum. Attainment on $F$ implies attainment
on $C^0$ because $C^0 = F \oplus \ker(d_0)$. $$\square$$

## Theorem L1C-T1 — attainment (p = 1 base case)

For every $\omega \in C^1$, the infimum defining $\Phi_1([\omega])$ is attained.

**Proof.** Specializing the classical argument of Theorem LpC-T1 to $p = 1$ yields coercivity of $f \mapsto \|\omega + d_0 f\|_{1,\mathbf{w}}$
on $F$. Lean 4 elaborates the integer 3-cycle bound in `lean4/l1c_t01_attainment.lean`. $$\square$$

## Theorem LpC-T2 — Lp quotient norm

For every $p \in [1, \infty]$, $\Phi_p$ is a norm on $Q^1 = C^1 / \text{im } d_0$.

**Proof.** Independence of representative follows by translating $f \mapsto f + g$.
Homogeneity holds because for $\lambda \in \mathbb{R}$,
$\Phi_p([\lambda \omega]) = \inf_f \|\lambda \omega + d_0 f\|_{p,\mathbf{w}} = |\lambda| \inf_{f'} \|\omega + d_0 f'\|_{p,\mathbf{w}} = |\lambda| \Phi_p([\omega])$.
Subadditivity follows from Minkowski's inequality: for $[\omega_1], [\omega_2] \in Q^1$ with respective minimizers $f_1, f_2$,
$$\Phi_p([\omega_1 + \omega_2]) \le \|\omega_1 + \omega_2 + d_0(f_1 + f_2)\|_{p,\mathbf{w}} \le \|\omega_1 + d_0 f_1\|_{p,\mathbf{w}} + \|\omega_2 + d_0 f_2\|_{p,\mathbf{w}} = \Phi_p([\omega_1]) + \Phi_p([\omega_2]).$$
Positive definiteness: If $\Phi_p([\omega]) = 0$, attainment (Theorem LpC-T1) provides $f^*$ such that $\|\omega + d_0 f^*\|_{p,\mathbf{w}} = 0$.
Because each $w_e > 0$, this implies $\omega + d_0 f^* = 0$, so $\omega \in \text{im } d_0$, meaning $[\omega] = 0$.
Conversely, if $\omega \in \text{im } d_0$, taking $f = -d_0^\dagger \omega$ gives norm zero. $$\square$$

## Theorem L1C-T2 — quotient norm (p = 1 base case)

$\Phi_1$ is a norm on $Q^1$.

**Proof.** Specialize Theorem LpC-T2 to $p = 1$. Lean 4 separately elaborates the scoped ambient weighted-norm algebra in `lean4/l1c_t02_quotient_norm.lean`. Strict positivity of every $w_e$
is essential: allowing a zero weight permits a nonzero quotient class to register value zero. $$\square$$

# 3. Fenchel-Rockafellar Hölder duality

Let $\mathbf{B}$ denote the $m \times n$ incidence matrix representing $d_0$. The primal problem for $p \in [1, \infty]$ is:

$$\inf_{\mathbf{f} \in \mathbb{R}^n} \|\boldsymbol{\omega} + \mathbf{B}\mathbf{f}\|_{p, \mathbf{w}}.$$

Define the conjugate exponent $q \in [1, \infty]$ by $1/p + 1/q = 1$ (with $q = \infty$ for $p = 1$, and $q = 1$ for $p = \infty$).
The dual norm on 1-chains $\mathbf{z} \in \mathbb{R}^E$ is defined by:
$$\|\mathbf{z}\|_{q, \mathbf{w}^*} = \left( \sum_{e \in E} w_e^{1 - q} |z_e|^q \right)^{1/q} \quad \text{for } 1 < q < \infty,$$
$$\|\mathbf{z}\|_{\infty, \mathbf{w}^*} = \max_{e \in E} \frac{|z_e|}{w_e} \quad \text{for } q = \infty \ (p = 1),$$
$$\|\mathbf{z}\|_{1, \mathbf{w}^*} = \sum_{e \in E} \frac{|z_e|}{w_e} \quad \text{for } q = 1 \ (p = \infty).$$

## Theorem LpC-T3 — Fenchel-Rockafellar Hölder duality

For every $p \in [1, \infty]$ and conjugate exponent $q = p/(p-1)$, strong duality holds:

$$\Phi_p([\omega]) = \max_{\mathbf{z} \in \mathbb{R}^E} \left\{ \mathbf{z}^\top \boldsymbol{\omega} : \mathbf{B}^\top \mathbf{z} = 0, \quad \|\mathbf{z}\|_{q, \mathbf{w}^*} \le 1 \right\}.$$

Both primal and dual extrema are attained.

**Proof.** Use the gauge-fixed subspace for primal attainment (Theorem LpC-T1). Let $F(\mathbf{u}) = \|\mathbf{u}\|_{p,\mathbf{w}}$ denote the weighted norm and $H(\mathbf{u}) = F(\boldsymbol{\omega} + \mathbf{u})$. Its Fenchel conjugate is $H^*(\mathbf{z}) = F^*(\mathbf{z}) - \mathbf{z}^\top \boldsymbol{\omega}$, where $F^*$ is the indicator function of the dual unit ball $\{\mathbf{z} \in \mathbb{R}^E : \|\mathbf{z}\|_{q,\mathbf{w}^*} \le 1\}$. Because $H$ is finite and continuous on $\mathbb{R}^E$, finite-dimensional Fenchel-Rockafellar duality [1] equates the primal minimum over $\mathbf{B}\mathbf{f}$ with the dual maximum of $\mathbf{z}^\top \boldsymbol{\omega}$ over $\mathbf{B}^\top \mathbf{z} = \mathbf{0}$ and $\|\mathbf{z}\|_{q,\mathbf{w}^*} \le 1$, using norm symmetry. Compactness of this dual feasible set yields attainment. $$\square$$

## Theorem L1C-T3 — dual circulation formula (p = 1 base case)

For $p = 1$, the dual norm constraint $\|\mathbf{z}\|_{\infty, \mathbf{w}^*} \le 1$ is equivalent to coordinate capacity bounds $|z_e| \le w_e$, yielding:

$$\Phi_1([\omega]) = \max_{\mathbf{z}} \left\{ \mathbf{z}^\top \boldsymbol{\omega} : \mathbf{B}^\top \mathbf{z} = 0, \quad |z_e| \le w_e \quad \forall e \in E \right\}.$$

Both extrema are attained.

**Proof.** The specialization of Theorem LpC-T3 to $p = 1$ gives strong LP duality over bounded circulations. Lean 4 elaborates the 3-cycle weak-duality inequality in `lean4/l1c_t03_weak_duality.lean`. $$\square$$

## Corollary LpC-C1 — Lp exactness criterion

For any $p \in [1, \infty]$, $\boldsymbol{\omega}$ is exact if and only if every circulation pairs to zero with $\boldsymbol{\omega}$.

**Proof.** If $\boldsymbol{\omega} = \mathbf{B}\mathbf{f}$, then for any $\mathbf{z}$ with $\mathbf{B}^\top \mathbf{z} = 0$, $\mathbf{z}^\top \boldsymbol{\omega} = \mathbf{z}^\top \mathbf{B}\mathbf{f} = (\mathbf{B}^\top \mathbf{z})^\top \mathbf{f} = 0$.
Conversely, if $\mathbf{z}^\top \boldsymbol{\omega} = 0$ for all circulations, the maximum dual value is 0, which by Theorem LpC-T3 implies $\Phi_p([\omega]) = 0$.
By Theorem LpC-T2, $[\omega] = 0$, so $\boldsymbol{\omega} \in \text{im } d_0$. $$\square$$

## Corollary L1C-C1 — exactness criterion (p = 1 base case)

$\boldsymbol{\omega}$ is exact if and only if every circulation pairs to zero with $\boldsymbol{\omega}$.

**Proof.** Specialize Corollary LpC-C1 to $p = 1$. $$\square$$

# 4. Geometric transition across regimes

The geometry of the quotient problem transitions across the parameter $p \in [1, \infty]$. We classify these into distinct regimes:

## 4.1 Polyhedral regime (p = 1)

At $p = 1$, the objective is piecewise linear and non-strictly convex. Primal minimizers may be non-unique, forming a convex polyhedral set. Optimal pairs satisfy checkable certificate properties:

### Theorem L1C-T4 — primal-dual certificate

Let $\mathbf{r} = \boldsymbol{\omega} + \mathbf{B}\mathbf{f}$. Suppose $\mathbf{B}^\top \mathbf{z} = 0$, $|z_e| \le w_e$, and:

- $z_e = w_e \text{ sgn}(r_e)$ whenever $r_e \ne 0$;
- $z_e \in [-w_e, w_e]$ when $r_e = 0$.

Then $\mathbf{r}$ is primal optimal, $\mathbf{z}$ is dual optimal, and
$$\Phi_1([\omega]) = \mathbf{z}^\top \boldsymbol{\omega} = \|\mathbf{r}\|_{1,\mathbf{w}}.$$

**Proof.** Feasibility gives $\mathbf{z}^\top \boldsymbol{\omega} = \mathbf{z}^\top (\boldsymbol{\omega} + \mathbf{B}\mathbf{f}) = \mathbf{z}^\top \mathbf{r}$.
The coordinate conditions give $\mathbf{z}^\top \mathbf{r} = \sum_{e \in E} w_e |r_e|$. Weak duality sandwiches
this common value between dual and primal optima, establishing optimality of both. Lean 4 formalizes cycle3 complementary slackness in `lean4/l1c_t04_complementary_slackness.lean`. $$\square$$

### Theorem L1C-TG — general finite matrix certificate

Let $m \in \mathbb{N}$ be an arbitrary finite dimension, $\mathbf{w} \in \mathbb{N}_{>0}^m$ positive integer weights, $\boldsymbol{\omega} \in \mathbb{Z}^m$ an input 1-cochain, and $\mathbf{D}: \mathbb{Z}^k \to \mathbb{Z}^m$ an arbitrary discrete coboundary operator.
If a candidate potential $\mathbf{p} \in \mathbb{Z}^k$, candidate dual vector $\mathbf{z} \in \mathbb{Z}^m$, and candidate primal residual $\mathbf{r} \in \mathbb{Z}^m$ satisfy:

1. Primal feasibility: $\mathbf{r}=\boldsymbol{\omega}+\mathbf{D}\mathbf{p}$;
2. Exact gauge annihilation: $\langle \mathbf{z}, \mathbf{D} \mathbf{p}' \rangle = 0$ for all potentials $\mathbf{p}' \in \mathbb{Z}^k$;
3. Capacity bounds: $|z_e| \le w_e$ for all $e \in \{1, \dots, m\}$;
4. Zero duality gap: $\|\mathbf{r}\|_{1, \mathbf{w}} = \langle \mathbf{z}, \boldsymbol{\omega} \rangle$;
Then $\mathbf{r}$ is globally optimal across all affine gauge choices:
$$\|\mathbf{r}\|_{1, \mathbf{w}} \le \|\boldsymbol{\omega} + \mathbf{D} \mathbf{p}'\|_{1, \mathbf{w}} \quad \forall \mathbf{p}' \in \mathbb{Z}^k.$$

**Proof.** For any $\mathbf{p}' \in \mathbb{Z}^k$, gauge annihilation yields $\langle \mathbf{z}, \boldsymbol{\omega} + \mathbf{D} \mathbf{p}' \rangle = \langle \mathbf{z}, \boldsymbol{\omega} \rangle + \langle \mathbf{z}, \mathbf{D} \mathbf{p}' \rangle = \langle \mathbf{z}, \boldsymbol{\omega} \rangle$.
The coordinate capacity bound $|z_e| \le w_e$ ensures $\langle \mathbf{z}, \mathbf{y} \rangle \le \|\mathbf{y}\|_{1, \mathbf{w}}$ for all $\mathbf{y} \in \mathbb{Z}^m$.
Setting $\mathbf{y} = \boldsymbol{\omega} + \mathbf{D} \mathbf{p}'$, we obtain:
$$\|\mathbf{r}\|_{1, \mathbf{w}} = \langle \mathbf{z}, \boldsymbol{\omega} \rangle = \langle \mathbf{z}, \boldsymbol{\omega} + \mathbf{D} \mathbf{p}' \rangle \le \|\boldsymbol{\omega} + \mathbf{D} \mathbf{p}'\|_{1, \mathbf{w}}.$$
Mechanized in Lean 4 (`lean4/l1c_general_certificate.lean`) for arbitrary dimension $m$ with zero `sorry` and kernel axioms `{propext, Classical.choice, Quot.sound}`. $$\square$$

## 4.2 Strictly and uniformly convex regime (p in (1, inf))

For $p \in (1, \infty)$, the $L^p$ norm is strictly convex and uniformly convex by Clarkson's inequalities.

### Theorem LpC-T4P — uniform convexity and nonlinear graph p-Laplacian

For any $p \in (1, \infty)$ and $\boldsymbol{\omega} \in C^1$:

1. The primal minimizer is strictly unique on the gauge-fixed subspace $F = \{f \in C^0 : f(v_j) = 0\text{ for one root }v_j\text{ per component}\}$, yielding a strictly unique optimal residual $\mathbf{r}_p^* = \boldsymbol{\omega} + \mathbf{B}\mathbf{f}_p^*$.
2. The optimal potential $\mathbf{f}_p^*$ is characterized by the nonlinear graph $p$-Laplacian equation:
   $$\mathbf{B}^\top \left( \mathbf{w} \odot |\mathbf{B}\mathbf{f} + \boldsymbol{\omega}|^{p-1} \odot \operatorname{sgn}(\mathbf{B}\mathbf{f} + \boldsymbol{\omega}) \right) = \mathbf{0}.$$
3. When the optimal residual is nonzero, its normalized dual witness is uniquely determined by:
   $$\mathbf{z}_p^* = \frac{\mathbf{w} \odot |\mathbf{r}_p^*|^{p-1} \odot \operatorname{sgn}(\mathbf{r}_p^*)}{\|\mathbf{r}_p^*\|_{p, \mathbf{w}}^{p-1}}.$$

**Proof.** For (1), uniform convexity of the $L^p$ norm on $\mathbb{R}^m$ for $p \in (1, \infty)$ establishes that for any $\mathbf{x} \ne \mathbf{y}$ with $\|\mathbf{x}\|_{p,\mathbf{w}} = \|\mathbf{y}\|_{p,\mathbf{w}} = 1$, $\|\frac{\mathbf{x}+\mathbf{y}}{2}\|_{p,\mathbf{w}} < 1$.
The powered objective is strictly convex on the gauge-fixed space: the coboundary is injective there and each positive-weight scalar function $|x|^p$ is strictly convex. Attainment therefore gives uniqueness.
For (2), for $p \in (1, \infty)$, the function $J_p(\mathbf{f}) = \frac{1}{p} \|\boldsymbol{\omega} + \mathbf{B}\mathbf{f}\|_{p,\mathbf{w}}^p = \frac{1}{p} \sum_{e \in E} w_e |(\boldsymbol{\omega} + \mathbf{B}\mathbf{f})_e|^p$ is strictly convex and continuously differentiable.
Its gradient with respect to $\mathbf{f}$ is:
$$\nabla J_p(\mathbf{f}) = \mathbf{B}^\top \left( \mathbf{w} \odot |\boldsymbol{\omega} + \mathbf{B}\mathbf{f}|^{p-1} \odot \operatorname{sgn}(\boldsymbol{\omega} + \mathbf{B}\mathbf{f}) \right).$$
Setting $\nabla J_p(\mathbf{f}) = \mathbf{0}$ yields the nonlinear graph $p$-Laplacian Euler-Lagrange equation.
For (3), setting $\mathbf{z}_p^*$ as displayed, we observe $\mathbf{B}^\top \mathbf{z}_p^* = \mathbf{0}$ (by the Euler-Lagrange equation), and direct evaluation confirms $\|\mathbf{z}_p^*\|_{q, \mathbf{w}^*} = 1$ and $\langle \mathbf{z}_p^*, \boldsymbol{\omega} \rangle = \|\mathbf{r}_p^*\|_{p, \mathbf{w}}$, satisfying the Fenchel-Rockafellar optimality conditions with zero duality gap. $$\square$$

## 4.3 Classical Hilbertian regime (p = 2)

At $p = 2$, the $L^2$ geometry coincides with the classical Hilbertian framework.

### Theorem LpC-T4H — Hilbertian L2 Hodge-Helmholtz decomposition

For $p = 2$ and uniform weights $w_e = 1$:

1. The cochain space admits an orthogonal Hodge-Helmholtz decomposition:
   $$C^1 = \text{im } d_0 \oplus \ker(d_0^*) = B^1 \oplus Z_1.$$
2. The primal minimizer is given explicitly by the Moore-Penrose pseudoinverse of the standard graph Laplacian $\mathbf{L}_0 = \mathbf{B}^\top \mathbf{B}$:
   $$\mathbf{f}_2^* = -\mathbf{L}_0^\dagger \mathbf{B}^\top \boldsymbol{\omega}.$$
3. The optimal residual is the harmonic component $\mathbf{r}_2^* = (\mathbf{I} - \mathbf{B}\mathbf{L}_0^\dagger \mathbf{B}^\top)\boldsymbol{\omega}$. When $\mathbf{r}_2^* \ne \mathbf{0}$, the dual circulation witness is self-dual:
   $$\mathbf{z}_2^* = \frac{\mathbf{r}_2^*}{\|\mathbf{r}_2^*\|_2};$$
   when $\mathbf{r}_2^* = \mathbf{0}$, the quotient norm vanishes $\Phi_2([\boldsymbol{\omega}]) = 0$ and $\mathbf{z}_2^* = \mathbf{0}$ trivially satisfies dual feasibility and zero duality gap.

**Proof.** At $p = 2$, the $p$-Laplacian becomes linear: $\mathbf{B}^\top(\mathbf{B}\mathbf{f} + \boldsymbol{\omega}) = \mathbf{L}_0 \mathbf{f} + \mathbf{B}^\top \boldsymbol{\omega} = \mathbf{0}$.
Because $\mathbf{B}^\top \boldsymbol{\omega}$ lies in the range of $\mathbf{L}_0$, the minimum-norm potential is $\mathbf{f}_2^* = -\mathbf{L}_0^\dagger \mathbf{B}^\top \boldsymbol{\omega}$.
Orthogonality of $\text{im } d_0$ and $\ker(d_0^*)$ gives Pythagoras' theorem: $\|\boldsymbol{\omega}\|_2^2 = \|\mathbf{B}\mathbf{f}_2^*\|_2^2 + \|\mathbf{r}_2^*\|_2^2$.
The dual exponent is $q = 2$, so dual circulations are measured in the same $L^2$ norm, making the dual witness $\mathbf{z}_2^*$ a direct scalar multiple of the primal harmonic residual when $\mathbf{r}_2^* \ne \mathbf{0}$. If $\mathbf{r}_2^* = \mathbf{0}$, the cochain is exact, $\Phi_2([\boldsymbol{\omega}]) = 0$, and $\mathbf{z}_2^* = \mathbf{0}$ satisfies $\mathbf{B}^\top \mathbf{0} = \mathbf{0}$ with $\langle \mathbf{0}, \boldsymbol{\omega} \rangle = 0$. $$\square$$


**Positive nonuniform weights.** Put $\mathbf{W}=\operatorname{diag}(w_e)$ and $\mathbf{L}_{\mathbf{w}}=\mathbf{B}^\top\mathbf{W}\mathbf{B}$. The minimum Euclidean-norm potential is $-\mathbf{L}_{\mathbf{w}}^\dagger\mathbf{B}^\top\mathbf{W}\omega$, and stationarity is $\mathbf{B}^\top\mathbf{W}r_2^*=0$. At nonzero residual the dual witness is
$$z_2^*=\frac{\mathbf{W}r_2^*}{\|r_2^*\|_{2,\mathbf{w}}},$$
with $\sum_e (z_e^*)^2/w_e=1$ and $\langle z_2^*,\omega\rangle=\|r_2^*\|_{2,\mathbf{w}}$. At zero residual use $z_2^*=0$. On the unit-flux directed triangle with weights $(1,2,3)$, $r_2^*=(6,3,2)/11$ is not a real circulation, whereas $\mathbf{W}r_2^*=(6,6,6)/11$ is. The weight factor is essential.

**Contrast between L1 and L2 localization.** While $L^2$ minimization distributes error across the entire graph to minimize squared Euclidean length (variance), $L^1$ minimization penalizes magnitude linearly, concentrating error onto sparse topological cycles. Section 8 provides an explicit instance where $L^2$ spreads defect across all edges while $L^1$ confines it to a single edge.

## 4.4 Chebyshev regime (p = inf)

At $p = \infty$, the quotient defect measures the minimal maximum-edge violation:
$$\Phi_\infty([\omega]) = \inf_f \max_{e \in E} w_e |(d_0 f + \omega)_e|.$$

### Theorem LpC-T4INF — discrete Chebyshev approximation and active-edge pairing

1. $\Phi_\infty([\omega])$ is attained and equals the Chebyshev approximation radius of $\boldsymbol{\omega}$ on the subspace $\text{im } d_0$.
2. An optimum admits an active-edge subgradient $\mathbf{z} \in \mathbb{R}^E$ satisfying $\mathbf{B}^\top \mathbf{z} = \mathbf{0}$, $\sum_{e \in E} |z_e|/w_e \le 1$, and $\mathbf{z}^\top (\boldsymbol{\omega} + \mathbf{B}\mathbf{f}_\infty^*) = \|\boldsymbol{\omega} + \mathbf{B}\mathbf{f}_\infty^*\|_{\infty, \mathbf{w}}$.

**Proof.** Writing the weighted maximum norm in epigraph form reduces the problem to a finite linear program; the stated active-edge subgradient conditions are its LP dual and complementary slackness optimality conditions (Theorem LpC-T3 at $p = \infty, q = 1$). The earlier assertion of a discrete Aronsson equation for arbitrary offset cochains does not follow from this argument and remains omitted. $$\square$$

## 4.5 The $p \to 1^+$ limit and secondary entropy minimization

Because the polyhedral $L^1$ quotient problem admits a non-strictly convex objective, the set of optimal primal potentials
$$\mathcal{M}_1 = \arg\min_{f \in F} \|\omega + d_0 f\|_{1, \mathbf{w}}$$
is in general a convex polytope rather than a singleton. In contrast, for every $p \in (1, \infty)$, strict convexity ensures that the $L^p$ minimizer $f_p^* \in F$ is strictly unique. This establishes a continuous primal trajectory $p \mapsto f_p^*$ for $p > 1$.

### Proposition LpC-P1 — secondary selection in the $p \to 1^+$ limit

Let $G = (V,E)$ be a connected finite graph with strictly positive weights $\mathbf{w}$, and let $\mathcal{M}_1 \subset F$ denote the non-empty compact convex set of gauge-fixed $L^1$ minimizers. For each $p \in (1, 2]$, let $f_p^* \in F$ be the unique minimizer of $J_p(f) = \frac{1}{p} \|\omega + d_0 f\|_{p, \mathbf{w}}^p$. Then:

1. Every accumulation point $f_1^* = \lim_{k \to \infty} f_{p_k}^*$ as $p_k \to 1^+$ belongs to $\mathcal{M}_1$.
2. On the relative interior of an optimal face where the active sign pattern $\operatorname{sgn}((\omega + d_0 f)_e)$ is invariant, the first-order asymptotic expansion of the objective as $p \to 1^+$ is:
   $$\frac{1}{p} \sum_{e \in E} w_e |r_f(e)|^p = \|\omega + d_0 f\|_{1, \mathbf{w}} + (p - 1)\left[E(f)-\|\omega + d_0 f\|_{1, \mathbf{w}}\right] + O((p-1)^2).$$
3. Accordingly, the trajectory $f_p^*$ selects among $L^1$ minimizers by minimizing the weighted entropy functional
   $$E(f) = \sum_{e \in E} w_e |r_f(e)| \log |r_f(e)|$$
   (with the standard continuous convention $0 \log 0 = 0$) over $\mathcal{M}_1$. The functional $E(f)$ is strictly convex on $\mathcal{M}_1$, ensuring that the entropy-selected minimizer $f_1^* = \lim_{p \to 1^+} f_p^*$ is unconditionally unique and that the entire trajectory converges.

**Proof.** Let $W=\sum_e w_e$ and $M_0=\max_e|\omega_e|$ (the empty-edge case is trivial). Weighted Hölder and optimality give, uniformly for $1<p\le2$,
$$\|r_p^*\|_{1,\mathbf{w}}\le W^{1-1/p}\|r_p^*\|_{p,\mathbf{w}}
\le W^{1-1/p}\|\omega\|_{p,\mathbf{w}}\le WM_0.$$
Thus $\|\mathbf{B}f_p^*\|_{1,\mathbf{w}}\le WM_0+\|\omega\|_{1,\mathbf{w}}$. The fixed inverse bound for $\mathbf{B}|_F$ controls $\|f_p^*\|$ independently of $p$. Together with compactness of $\mathcal{M}_1$, this places the trajectory and the optimal face in a common compact set $K\subset F$. On $K$, the residuals $r_f = \omega + d_0 f$ are uniformly bounded: $|r_f(e)| \le M < \infty$ for all $e \in E, f \in K$.
For any fixed scalar $x \in [-M, M]$, the Taylor expansion of $t \mapsto \frac{1}{p} |x|^p$ around $p = 1$ gives:
$$\frac{1}{p} |x|^p = |x| + (p - 1)\left[|x| \log |x| - |x|\right] + R(p, x),$$
under the standard continuous convention $0 \log 0 = 0$, where the remainder satisfies $|R(p, x)| \le C (p-1)^2$ uniformly for all $x \in [-M, M]$ for a uniform constant $C < \infty$. Summing over edges with weights $w_e > 0$, the expansion is uniform on $K$:
$$J_p(f) = \frac{1}{p} \|\omega + d_0 f\|_{p, \mathbf{w}}^p = \|\omega + d_0 f\|_{1, \mathbf{w}} + (p - 1)\left[E(f) - \|\omega + d_0 f\|_{1, \mathbf{w}}\right] + R_p(f),$$
where $\sup_{f \in K} |R_p(f)| \le C' (p-1)^2$ with $C' = C \sum_e w_e < \infty$.
Uniform convergence of $\|\cdot\|_{p,\mathbf{w}} \to \|\cdot\|_{1,\mathbf{w}}$ as $p \to 1^+$ implies $\Gamma$-convergence of the objectives, which ensures that all cluster points of $f_p^*$ minimize the $L^1$ quotient norm, establishing (1).
This uniform expansion on $K$ establishes (2).

For (3), let $g \in \mathcal{M}_1 \subset K$ be an arbitrary gauge-fixed $L^1$ minimizer. By optimality of $f_p^*$ for $J_p$ on $F$, we have:
$$J_p(f_p^*) \le J_p(g).$$
Substituting the uniform expansion for both $f_p^*$ and $g$:
$$\|\omega + d_0 f_p^*\|_{1, \mathbf{w}} + (p - 1)\left[E(f_p^*) - \|\omega + d_0 f_p^*\|_{1, \mathbf{w}}\right] + R_p(f_p^*) \le \|\omega + d_0 g\|_{1, \mathbf{w}} + (p - 1)\left[E(g) - \|\omega + d_0 g\|_{1, \mathbf{w}}\right] + R_p(g).$$
Because $g \in \mathcal{M}_1$, $\|\omega + d_0 g\|_{1, \mathbf{w}} = \Phi_1([\omega])$. Because $\Phi_1([\omega])$ is the minimum of $\|\cdot\|_{1, \mathbf{w}}$, we have $\|\omega + d_0 f_p^*\|_{1, \mathbf{w}} \ge \Phi_1([\omega]) = \|\omega + d_0 g\|_{1, \mathbf{w}}$, so the zeroth-order term $\|\omega + d_0 f_p^*\|_{1, \mathbf{w}} - \|\omega + d_0 g\|_{1, \mathbf{w}} \ge 0$ is non-negative. Subtracting this non-negative quantity preserves the inequality:
$$(p - 1)\left[E(f_p^*) - \|\omega + d_0 f_p^*\|_{1, \mathbf{w}}\right] + R_p(f_p^*) \le (p - 1)\left[E(g) - \Phi_1([\omega])\right] + R_p(g).$$
Dividing both sides by $p - 1 > 0$:
$$E(f_p^*) - \|\omega + d_0 f_p^*\|_{1, \mathbf{w}} + \frac{R_p(f_p^*)}{p - 1} \le E(g) - \Phi_1([\omega]) + \frac{R_p(g)}{p - 1}.$$
Because $|R_p(f)| \le C' (p-1)^2$ on $K$, the remainder quotients satisfy $\lim_{p \to 1^+} \frac{R_p(f)}{p-1} = 0$.
Now let $p_k \to 1^+$ be any sequence such that $f_{p_k}^* \to f_1^* \in K$. By (1), $f_1^* \in \mathcal{M}_1$, so $\|\omega + d_0 f_1^*\|_{1, \mathbf{w}} = \Phi_1([\omega])$.
Taking the limit $k \to \infty$ and using continuity of $E(f)$ and $\|\cdot\|_{1, \mathbf{w}}$ on $K$:
$$E(f_1^*) - \Phi_1([\omega]) \le E(g) - \Phi_1([\omega]).$$
Adding $\Phi_1([\omega])$ to both sides yields:
$$E(f_1^*) \le E(g) \quad \text{for all } g \in \mathcal{M}_1.$$
Thus, every cluster point $f_1^*$ minimizes $E(f)$ over the compact convex set $\mathcal{M}_1$.

Next, we establish unconditional strict convexity of $E(f)$ on $\mathcal{M}_1$. No two $L^1$-optimal residuals $r_1, r_2 \in \mathcal{R}_1 = \{\omega + d_0 f : f \in \mathcal{M}_1\}$ can have opposite nonzero signs in any coordinate: if $(r_1)_e > 0$ and $(r_2)_e < 0$, then $|\frac{1}{2}(r_1)_e + \frac{1}{2}(r_2)_e| < \frac{1}{2}|(r_1)_e| + \frac{1}{2}|(r_2)_e|$. With strictly positive weights $w_e > 0$, the midpoint $\frac{1}{2}(r_1 + r_2)$ would satisfy $\|\frac{1}{2}(r_1 + r_2)\|_{1,\mathbf{w}} < \Phi_1([\omega])$, contradicting the minimality of $\Phi_1([\omega])$. Therefore, the entire optimal residual set $\mathcal{R}_1$ lies within a single closed coordinate orthant.
On this closed orthant, the scalar function $\eta(t) = t \log t$ (with $0 \log 0 = 0$) is strictly convex on $[0, \infty)$ since $\eta''(t) = 1/t > 0$ for $t > 0$. Because the affine map $f \mapsto \omega + d_0 f$ is injective on the gauge-fixed subspace $F$, $E(f)$ is strictly convex on the compact convex set $\mathcal{M}_1$. A strictly convex function on a non-empty compact convex set attains its minimum at a unique point $f_{\text{ent}}^* \in \mathcal{M}_1$.
Because every cluster point $f_1^*$ satisfies $E(f_1^*) \le E(g)$ for all $g \in \mathcal{M}_1$, all cluster points coincide with $f_{\text{ent}}^*$. Because the trajectory $\{f_p^*\}_{p \in (1, 2]}$ is contained in the compact set $K$ and has only one possible cluster point $f_{\text{ent}}^*$, the entire trajectory converges: $\lim_{p \to 1^+} f_p^* = f_{\text{ent}}^*$. $$\square$$

# 5. Sparse optimal representatives

## Theorem L1C-T5 — cycle-rank support bound

Every quotient class has an optimal representative $\mathbf{r}$ with
$|\text{supp}(\mathbf{r})| \le \beta$.

**Proof.** Choose a full-row-rank matrix $\mathbf{A}$ whose row space is $\ker(\mathbf{B}^\top)$.
Two cochains represent the same class exactly when $\mathbf{A}\mathbf{r} = \mathbf{A}\boldsymbol{\omega}$. The problem is
therefore basis pursuit:

$$\min_{\mathbf{r}^+, \mathbf{r}^-} \mathbf{w}^\top (\mathbf{r}^+ + \mathbf{r}^-) \quad \text{subject to } \mathbf{A}(\mathbf{r}^+ - \mathbf{r}^-) = \mathbf{A}\boldsymbol{\omega}, \quad \mathbf{r}^+, \mathbf{r}^- \ge 0.$$

It has an optimal basic feasible solution. Since $\text{rank}(\mathbf{A}) = \beta$, at most $\beta$
variables among $\mathbf{r}^+$ and $\mathbf{r}^-$ are basic and positive. Positive weights exclude
simultaneously positive $r^+_e, r^-_e$, since decreasing both preserves feasibility
and lowers cost. Hence the resulting $\mathbf{r}$ has at most $\beta$ nonzero
coordinates. $$\square$$

This is an existential bound, not a genericity statement and not uniqueness.
Degenerate instances may have dense optima as well as a sparse one.

## Example — one directed cycle

For a consistently oriented $m$-cycle, the invariant is
$S = \sum_{e \in E} \omega_e$. Hence

$$\Phi_1([\omega]) = |S| \min_{e \in E} w_e.$$

An optimum concentrates $S$ on any minimum-weight edge. In the unweighted case
the value is $|S|$, and the support bound $\beta = 1$ is sharp.

# 6. Integral cut-lattice optimum

## Theorem L1C-T6 — integral attainment

If $\boldsymbol{\omega}$ is integral and the weights are integral, there exists an optimal
pair with integral $\mathbf{f}$ (after fixing one vertex gauge) and integral residual
$\mathbf{r} = \boldsymbol{\omega} + \mathbf{B}\mathbf{f}$.

**Proof.** Delete the root column of the incidence matrix. The resulting matrix
is totally unimodular [2, 3]. Adjoining signed identity columns and column negations
preserves total unimodularity, so the standard-form constraint matrix for the
primal LP is totally unimodular. With integral right-hand side, an optimal basic
feasible solution may be chosen integral. $$\square$$

This is a cochain/cut-lattice statement. It is not the minimum homologous-chain
problem, whose repair directions are boundaries from the next chain degree.

# 7. Discrete physics and simplicial Bianchi nilpotency

On a finite 2-dimensional simplicial complex $K = (V, E, F)$, edge cochains
model discrete gauge connections, while face cochains model discrete field
curvature. Let $D_1: C_1(K) \to C_0(K)$ and $D_2: C_2(K) \to C_1(K)$ denote the
standard signed simplicial boundary operators with respect to chosen orientations,
and let $d_0 = D_1^\top: C^0(K) \to C^1(K)$ and $d_1 = D_2^\top: C^1(K) \to C^2(K)$
denote their algebraic coboundaries.

## Theorem L1C-T7 — simplicial Bianchi nilpotency

Let $K = (V, E, F)$ be a finite 2-simplicial complex.

1. For every 0-cochain $f \in C^0(K)$, the composite coboundary vanishes identically:
   $$d_1(d_0 f) = 0.$$
   Consequently, pure gauge cochains have zero field curvature and lie in the
   cocycle subspace $Z^1(K) = \ker(d_1)$.
2. For every 1-cycle $z \in C_1(K)$ satisfying $D_1 z = 0$ (Kirchhoff circulation)
   and every 0-cochain $f \in C^0(K)$,
   $$\langle z, d_0 f \rangle = 0.$$
   The quotient norm $\Phi_1([\omega])$ is invariant under affine shifts along the
   gauge orbit: $\Phi_1([\omega + d_0 f]) = \Phi_1([\omega])$.

**Proof.**
For (1), by definition of the adjoint, $(d_1 \circ d_0)^\top = D_1 \circ D_2$.
For each oriented triangular face $\sigma = (u, v, w) \in F$, the boundary is
$D_2 \sigma = (u,v) + (v,w) - (u,w)$. Applying $D_1$ yields
$$D_1(D_2 \sigma) = (v - u) + (w - v) - (w - u) = 0.$$
Because $D_1 D_2 = 0$, its transpose $d_1 d_0 = (D_1 D_2)^\top = 0$.

For (2), the definition of the coboundary adjoint gives
$\langle z, d_0 f \rangle = \langle D_1 z, f \rangle$.
Because $D_1 z = 0$, this pairing evaluates to zero.
Invariance of $\Phi_1$ follows because $\omega + d_0 f + d_0 g = \omega + d_0 (f + g)$,
which parametrizes the identical coset $[\omega] \in Q^1$. $$\square$$

# 8. Quantum phase cocycles and Schatten-p operator extensions

Let $G = (V,E)$ be a finite directed graph whose vertices index an orthonormal
basis $\{|v\rangle\}_{v \in V}$ of an $n$-dimensional Hilbert space
$\mathcal{H} = \mathbb{C}^V$. Let $\omega \in C^1(G, \mathbb{R})$ denote a
phase 1-cochain assigning phase difference $\omega(u,v)$ to each directed edge
$(u,v) \in E$. A quantum state on $\mathcal{H}$ is described by a density matrix
$\rho = \sum_{u, v \in V} \rho_{uv} |u\rangle\langle v|$ satisfying $\rho = \rho^\dagger$,
$\operatorname{Tr}(\rho) = 1$, and $\rho \succeq 0$. Let
$\rho_{\text{diag}} = \sum_{v \in V} \rho_{vv} |v\rangle\langle v|$ denote the
dephased pointer state.

For operators on $\mathcal{H}$, the Schatten-$p$ norm for $p \in [1, \infty)$ is
$\|A\|_p = (\operatorname{Tr}(|A|^p))^{1/p}$, and for $p = \infty$, $\|A\|_\infty = \|A\|_{\mathrm{op}}$.
For $p = 1$, this specializes to the trace norm $\|A\|_1 = \operatorname{Tr}|A| = \operatorname{Tr}\sqrt{A^\dagger A}$.

## Theorem LpC-T8 — Schatten-p quantum defect and non-commutative Hölder bound

1. For any operator-valued cochain $H \in C^1(G, \mathcal{B}_p(\mathcal{H}))$, the Schatten-$p$ quotient defect is:
   $$\Phi_p([H]) = \inf_{F \in C^0(G, \mathcal{B}_p(\mathcal{H}))} \|H - d_0 F\|_{p, \mathbf{w}}.$$
   It satisfies non-commutative Fenchel-Rockafellar Hölder duality:
   $$\Phi_p([H]) = \max_{Z \in C_1(G, \mathcal{B}_q(\mathcal{H}))} \left\{ \operatorname{Re}\operatorname{Tr}\langle Z, H \rangle : d_0^* Z = 0, \quad \|Z\|_{q, \mathbf{w}^*} \le 1 \right\},$$
   where $1/p + 1/q = 1$ and non-commutative Hölder duality $|\operatorname{Tr}(A^\dagger B)| \le \|A\|_p \|B\|_q$ holds.
2. Let $A=\rho-\rho_{\mathrm{diag}}$ be a $d\times d$ off-diagonal matrix. For $1\le p\le2$,
   $$\|A\|_{S_p}\le \left(\sum_{u\ne v}|A_{uv}|^p\right)^{1/p};$$
   for $2\le p\le\infty$,
   $$\|A\|_{S_p}\le d^{1-2/p}\left(\sum_{u\ne v}|A_{uv}|^p\right)^{1/p}.$$
   The factor is interpreted as $d$ at $p=\infty$. At $p=1$ this recovers $\|\rho-\rho_{\mathrm{diag}}\|_1\le C_{l_1}(\rho)$.

**Proof.** For (1), non-commutative $L^p$ spaces over finite-dimensional matrix algebras satisfy standard Clarkson inequalities and uniform convexity for $p \in (1, \infty)$.
The dual space of the Schatten-$p$ class $\mathcal{B}_p(\mathcal{H})$ is isometrically isomorphic to $\mathcal{B}_q(\mathcal{H})$ under the trace pairing $\langle A, B \rangle = \operatorname{Tr}(A^\dagger B)$ (see Watrous [6]).
For (2), the $1\le p\le2$ bound follows by interpolation between the entrywise $\ell^1\to S_1$ triangle inequality and the Frobenius identity. For $p\ge2$, use $\|A\|_{S_p}\le\|A\|_{S_2}=\|A\|_{\ell^2}$ and $\|A\|_{\ell^2}\le d^{1-2/p}\|A\|_{\ell^p}$. $$\square$$

## Theorem L1C-T8 — quantum phase cocycle defect bound (p = 1 base case)

All phase lifts, gradients, cycles and phase pairings in this theorem use the support graph $G_\rho=(V,E_\rho)$, where $E_\rho=\{(u,v)\in E:\rho_{uv}\ne0\}$. Norms of the full density matrix and its coherence sum retain all matrix entries.

1. Let $\rho$ be a density matrix with representation in the orthonormal basis $\{|v\rangle\}_{v \in V}$.
   Under the incidence convention $(d_0 \theta)(u,v) = \theta_v - \theta_u$, the local diagonal unitary operator
   $U_\theta = \sum_{v \in V} e^{-i \theta_v} |v\rangle\langle v| = \operatorname{diag}(e^{-i \theta_v})$
   acts on matrix entries as:
   $$(U_\theta \rho U_\theta^\dagger)_{uv} = \langle u | U_\theta \rho U_\theta^\dagger | v \rangle = e^{-i \theta_u} \rho_{uv} e^{i \theta_v} = e^{i (\theta_v - \theta_u)} \rho_{uv} = e^{i (d_0 \theta)_{uv}} \rho_{uv}.$$
   Thus, $U_\theta$ shifts each edge phase factor by $+ (d_0 \theta)_{uv}$. If $\rho$ admits a chosen real phase lift
   $\boldsymbol{\omega}$ satisfying $d_0 \theta = -\boldsymbol{\omega}$ (that is, $[\boldsymbol{\omega}] = \mathbf{0} \in Q^1$), the gauge rotation $U_\theta$ eliminates
   all relative phase angles, yielding $(U_\theta \rho U_\theta^\dagger)_{uv} = |\rho_{uv}|$ without changing the spectrum
   or off-diagonal moduli $|\rho_{uv}|$.
2. The trace distance $\|\rho - \rho_{\text{diag}}\|_{\operatorname{tr}} = \frac{1}{2} \operatorname{Tr}|\rho - \rho_{\text{diag}}|$
   is bounded by the total off-diagonal $L^1$ coherence:
   $$\|\rho - \rho_{\text{diag}}\|_{\operatorname{tr}} \le \sum_{u < v} |\rho_{uv}| = \frac{1}{2} C_{l_1}(\rho),$$
   where $C_{l_1}(\rho) = \sum_{u \ne v} |\rho_{uv}|$ is the standard $l_1$-norm of coherence [5, 6].
   For every edge $(u,v) \in E$, the $2 \times 2$ principal minor condition of
   positive semidefiniteness enforces
   $$|\rho_{uv}| \le \sqrt{\rho_{uu} \rho_{vv}} \le \frac{1}{2}(\rho_{uu} + \rho_{vv}).$$
   For any nonzero real circulation $C \in Z_1(G;\mathbb{R})$, define its maximum weight-normalized capacity:
   $$M_C = \max_{e \in E: C_e \ne 0} \frac{|C_e|}{w_e}.$$
   Then the normalized circulation $\mathbf{z} = \mathbf{C} / M_C$ is dual-feasible, establishing the lower bound:
   $$\Phi_1([\omega]) \ge \frac{|\langle C, \omega \rangle|}{M_C} = \frac{|\langle C, \omega \rangle|}{\max_{e: C_e \ne 0} (|C_e| / w_e)}.$$
3. Explicit relationship between phase cochains and density operator $\rho$:
   Phase angle extraction is restricted to the support subgraph of non-vanishing coherences:
   $$E_\rho = \{(u,v) \in E : \rho_{uv} \ne 0\}.$$
   For $(u,v) \in E \setminus E_\rho$, the phase angle is undefined. On $E_\rho$, any matrix entry factors as $\rho_{uv} = |\rho_{uv}| e^{i \omega(u,v)}$ for a chosen real lift $\boldsymbol{\omega} \in C^1(E_\rho; \mathbb{R})$.
   Under diagonal unitary transformations $U_\theta = \operatorname{diag}(e^{-i \theta_v})$, entries transform as
   $$(U_\theta \rho U_\theta^\dagger)_{uv} = |\rho_{uv}| e^{i (\omega(u,v) + (d_0 \theta)_{uv})}.$$
   Crucially, taking principal arguments $\operatorname{Arg}(\cdot) \in (-\pi, \pi]$ edge-by-edge after a diagonal unitary rotation does not generally produce an exact gradient shift in $\mathbb{R}^E$, because branch wrapping introduces an integer period shift $\mathbf{k} \in \mathbb{Z}^E$:
   $$\operatorname{Arg}((U_\theta \rho U_\theta^\dagger)_{uv}) = \omega(u,v) + (d_0 \theta)_{uv} + 2\pi k_{uv}.$$
   On a triangle, start with positive real off-diagonal entries $\rho_{uv} > 0$, so initial edge phases and real quotient norm vanish ($\boldsymbol{\omega} = \mathbf{0}, \Phi_1([\omega]) = 0$). Applying $U_\theta$ with $\theta = (0, 3\pi/4, 3\pi/2)$ gives potential differences $d_0 \theta = (3\pi/4, 3\pi/4, -3\pi/2)$. Taking principal branch arguments wraps the third edge phase to $\pi/2 = -3\pi/2 + 2\pi$, producing principal phases $(3\pi/4, 3\pi/4, \pi/2)$. The sum around the directed cycle is $3\pi/4 + 3\pi/4 + \pi/2 = 2\pi$, so the re-extracted real quotient norm is $\Phi_1 = 2\pi$, even though the state underwent only a local diagonal unitary rotation and the physical $U(1)$ holonomy around the cycle remains $\exp(i \cdot 2\pi) = 1$.
   Therefore, three quantities must be distinguished:
   (a) **Chosen real lift quotient norm:** For a fixed real lift $\boldsymbol{\omega} \in C^1(E_\rho; \mathbb{R})$, $\Phi_1([\omega]) = \inf_{f \in C^0} \|\omega + d_0 f\|_{1,\mathbf{w}}$ is invariant under real gradient shifts $\omega \mapsto \omega + d_0 f$, measuring minimal $L^1$ effort to gauge-align that specific real lift.
   (b) **Gauge-invariant $U(1)$ cycle holonomy:** On the support graph $G_\rho=(V,E_\rho)$, for any integral cycle $C \in Z_1(G_\rho;\mathbb{Z})$, the multiplicative holonomy $\operatorname{hol}_{U(1)}(C) = \prod_{e\in E_\rho} (\rho_{uv} / |\rho_{uv}|)^{C_e} = \exp(i \langle C, \omega \rangle) \in U(1)$ is strictly invariant under all diagonal unitary transformations $U_\theta \rho U_\theta^\dagger$, since $\exp(i \langle C, d_0 \theta \rangle) = \exp(i \langle D_1 C, \theta \rangle) = 1$.
   (c) **Branch-independent $U(1)$ quotient defect:** To obtain a quotient distance from the identity on $U(1)$ connections that is invariant under diagonal unitaries without branch-cut artifacts, one minimizes over both vertex potentials and integer edge branch shifts ($2\pi \mathbb{Z}^{E_\rho}$):
   $$\Phi_1^{U(1)}(\rho) = \inf_{f \in C^0(G_\rho),\, \mathbf{k} \in \mathbb{Z}^{E_\rho}} \|\omega + d_0 f + 2\pi \mathbf{k}\|_{1, \mathbf{w}}.$$

   This is a length function on the quotient group $\mathbb{R}^{E_\rho}/(\operatorname{im}d_0+2\pi\mathbb{Z}^{E_\rho})$, inducing the distance $d([\omega],[\eta])=\Phi_1^{U(1)}([\omega-\eta])$. It is not a norm on a real vector space: on an unweighted cycle, flux $\pi$ has length $\pi$, while doubled flux $2\pi$ has length zero. Integral coefficients in (b) ensure independence of phase lift; a real half-cycle changes holonomy by $-1$ after a $2\pi$ lift change on one edge. Real circulations remain the domain of the linear LP dual in (a).
   For the triangle counterexample above, choosing $\mathbf{k} = (0, 0, -1)$ and $f = -\theta$ cancels the branch winding, giving $\Phi_1^{U(1)}(\rho) = 0$.

**Proof.** Specializing Theorem LpC-T8 to $p = 1$, direct evaluation under diagonal unitary conjugation yields (1). For (2), the triangle inequality across $2 \times 2$ off-diagonal blocks gives the trace distance bound. The capacity-normalized loop bound follows from weak LP duality with dual-feasible vector $\mathbf{z} = \mathbf{C} / M_C$, tested in `test_theorem_8_weighted_loop_bound_correction`. For (3), restricting phase extraction to $E_\rho$ avoids undefined arguments at zero coherences. The sign $+ (d_0 \theta)_{uv}$ follows from $(U_\theta \rho U_\theta^\dagger)_{uv} = e^{-i \theta_u} \rho_{uv} e^{i \theta_v} = e^{i (\theta_v - \theta_u)} \rho_{uv} = e^{i (d_0 \theta)_{uv}} \rho_{uv}$. The branch-cut wrapping and the distinction between real lifts and $U(1)$ holonomy are validated on the triangle counterexample $\theta = (0, 3\pi/4, 3\pi/2)$ in `test_quantum_phase_gauge_invariance_and_branch_winding` and `test_quantum_phase_additive_flux_vs_u1_holonomy`.
In this finite discrete setting, we emphasize that these combinatorial bounds on off-diagonal matrix entries are static geometric inequalities, separate from continuous unitary Hamiltonian time evolution. $$\square$$

# 9. Cohomological classification and topological obstructions

For a general cell complex, $H^1(K;\mathbb{R})=\ker(d_1)/\operatorname{im}(d_0)$. The quotient norm $\Phi_p$ is defined on $C^1/\operatorname{im}(d_0)$ and descends to $H^1$ only after restricting to closed cochains. On a graph, $C^2=0$ and this distinction disappears:

1. **Exact 1-Cochains ($[\omega] = 0$):**
   $\Phi_p([\omega]) = 0$ if and only if $\omega \in B^1 = \operatorname{im} d_0$. The cochain is a pure gradient potential ($r = 0$), corresponding to a trivial gauge connection with zero holonomy along all cycles.
2. **Closed Cohomology Defect ($[\omega] \ne 0$ on 1-graphs):**
   On a 1-dimensional graph complex ($d_1 = 0$), all cochains are cocycles ($Z^1 = C^1$). When $\Phi_p([\omega]) > 0$, $\omega$ represents a non-trivial cohomology class in $H^1(G; \mathbb{R}) \cong \mathbb{R}^\beta$. The defect represents a topological obstruction that cannot be eliminated by any choice of vertex potential.
3. **Simplicial Curvature Obstructions (2-complexes):**
   On a 2-simplicial complex $K$, the face coboundary $d_1 \omega \in C^2(K)$ measures discrete field curvature (magnetic flux). If $d_1 \omega \ne 0$, $\omega$ is not closed ($\omega \notin Z^1$), indicating localized curvature defect on 2-simplices. By Theorem L1C-T7 (simplicial Bianchi nilpotency), any exact gauge adjustment $d_0 f$ has zero curvature ($d_1(d_0 f) = 0$), so the curvature $d_1 \omega$ is strictly gauge-invariant.

This taxonomy classifies discrete difference fields by their topological obstructions, distinguishing exact gauge transformations, non-contractible cycle circulations, and non-vanishing face curvatures.

# 10. Computational companion & formal mechanization

The companion software implementation provides exact rational arithmetic for all
polyhedral and certificate decision paths ($p=1, 2, \infty$, $LDL^\dagger$ positive-semidefiniteness,
and simplicial complexes) under the Zero-Float Law, avoiding numerical tolerances and
floating-point ambiguities, while continuous interior-$p$ iterations and Schatten-$p$
singular values are evaluated via binary64 numerical diagnostics:

1. **Exact Two-Phase Simplex Solver**: An exact rational linear programming solver
   over `fractions.Fraction` implementing Bland's minimal-index pivot rule,
   guaranteeing cycle prevention for the $p = 1$ base case. It handles primal standard forms,
   artificial variable elimination, and dual variable extraction without floating-point error,
   and raises `SolverIterationLimitError` on budget exhaustion.
2. **Primal-Dual Certification**: Checks primal feasibility $r = \omega + d_0 f$,
   dual divergence-free annihilation $\mathbf{B}^\top \mathbf{z} = 0$, capacity bounds $|z_e| \le w_e$,
   and verifies exact zero duality gap $\Phi_1([\omega]) - \mathbf{z}^\top \boldsymbol{\omega} = 0$.
   Exposes standalone receipt validator `check_certificate_receipt`; its integrality flag concerns the primal potential and residual, not the dual. The Chebyshev path independently checks $r=h-\mathbf{B}f$, $t\ge0$, $w_e|r_e|\le t$, $\mathbf{B}^\top z=0$, $\sum_e|z_e|/w_e\le1$, and $\langle z,h\rangle=t$ through `check_linf_certificate_receipt` before returning `OPTIMAL_LINF`. The opposite residual sign is a solver convention and preserves the gauge quotient.
3. **Simplicial Complex & Bianchi Operators**: Implements boundary matrices $D_1, D_2$,
   coboundaries $d_0, d_1$, and automated verification of $d_1(d_0 f) = 0$, distinguishing
   closed graph residuals from curvature residuals.
4. **Quantum Density Matrix Engine**: Pure standard-library module verifying
   Hermiticity, trace normalization, and exact positive semidefiniteness via rational
   $LDL^\dagger$ decomposition with complete diagonal pivoting. Coherence values use exact fractions when all required complex moduli are rational, and binary64 square roots otherwise. The $L^2$ squared norm is exact; its displayed square root may be numerical.
5. **Interactive Notebooks**: Dual-track Jupyter notebooks (`001_conceptual_l1_cohomology.ipynb`
   and `002_formal_l1_cohomology.ipynb`) provide pedagogical visualizations, defect
   injection sandboxes, and tableau inspections.
6. **Formal Interactive Proof Mechanization**: Lean 4 mechanizes
   `general_finite_certificate_optimality` and the named finite-model theorems
   for L1C-T1, L1C-T2, L1C-T3, L1C-T4, L1C-T5, and L1C-T7. Integer 3-cycle
   lemmas in `l1c_lp_duality`, `l1c_lp_strict_uniqueness`, and
   `l1c_lp_hodge_decomposition` do not mechanize the general real $L^p$ propositions.
   The Lean estate compiles offline with `lake build`, with proof-placeholder
   commands absent and axiom reports inside `{propext, Classical.choice, Quot.sound}`.

The shipped pytest suite contains 91 test functions (producing 110 test cases) across trees, cycles,
complete graphs, disconnected graphs, zero-weight refusal, integer lattices,
simplex iteration limits, primal feasibility fault injections, exact
$LDL^\dagger$ PSD checks, quantum phase gauge invariance and branch-cut winding checks, and the $L^1/L^2$ counterexample
$\mathbf{B} = (1,1,1)^\top$, $\boldsymbol{\omega} = (0,0,10)^\top$.
Replay of the complete test suite and Lean proof verification is invoked explicitly via:
`python verify_deposit.py --run-tests --lean`.
Current replay of those tests requires the optional development dependencies
`pytest` and `pytest-cov`; source compilation and Lean replay are recorded
separately from any historical coverage receipt.

# 11. Scope and concluding remarks

This monograph investigates finite-dimensional quotient spaces of discrete cell complexes under the family of weighted $L^p$ norms. We summarize the precise boundaries of these results:

1. **Discrete vs. Continuum:** The results herein apply to finite directed graphs and finite 2-simplicial complexes. They do not constitute an infinite-dimensional Hodge-de Rham theorem on manifolds, nor do they address continuous Sobolev or $L^p$ cohomology on non-compact domains.
2. **Static vs. Dynamical:** The bounds on quantum density matrix coherence (Theorems LpC-T8 and L1C-T8) apply to fixed states in a chosen basis; they do not characterize continuous unitary time-evolution or open quantum system master equations.
3. **Formal Verification:** Lean 4 mechanizes `general_finite_certificate_optimality` and the named finite-model theorems for L1C-T1, L1C-T2, L1C-T3, L1C-T4, L1C-T5, and L1C-T7. The general $L^p$ results, exactness characterization, cycle-rank bound, total unimodularity, and Schatten statements have prose proofs and are classified as classical background. They are not mechanized at that generality. L1C-T2 mechanizes ambient integer three-edge weighted-norm axioms and residual-addition compatibility, without defining a minimized quotient norm. The conditional finite integer certificate establishes optimality from its hypotheses; it does not establish certificate existence or verify the Python implementation. The earlier general Aronsson assertion for arbitrary cochains remains withdrawn.

# References {-}

1. R. T. Rockafellar, *Convex Analysis*, Princeton University Press, 1970.
2. A. Schrijver, *Theory of Linear and Integer Programming*, Wiley, 1986.
3. T. K. Dey, A. N. Hirani, and B. Krishnamoorthy, “Optimal homologous cycles,
   total unimodularity, and linear programming,” *SIAM Journal on Computing*
   40(4), 2011, 1026–1044. <https://doi.org/10.1137/100800245>
4. S. Boyd and L. Vandenberghe, *Convex Optimization*, Cambridge University
   Press, 2004. <https://web.stanford.edu/~boyd/cvxbook/>
5. T. Baumgratz, M. Cramer, and M. B. Plenio, “Quantifying Coherence,” *Physical
   Review Letters* 113(14), 2014, 140401. <https://doi.org/10.1103/PhysRevLett.113.140401>
6. J. Watrous, *The Theory of Quantum Information*, Cambridge University Press, 2018. <https://doi.org/10.1017/9781316848142>
7. J. A. Clarkson, “Uniformly convex spaces,” *Transactions of the American
   Mathematical Society* 40(3), 1936, 396–414. <https://doi.org/10.1090/S0002-9947-1936-1501880-4>
8. G. Aronsson, “Extension of functions satisfying Lipschitz conditions,”
   *Arkiv för Matematik* 6(6), 1967, 551–561. <https://doi.org/10.1007/BF02591361>
9. X. Jiang, L.-H. Lim, Y. Yao, and Y. Ye, “Statistical ranking and combinatorial Hodge theory,” *Mathematical Programming* 127(1), 2011, 203–244. [DOI](https://doi.org/10.1007/s10107-010-0419-x) (preprint: [arXiv:0811.1067v2](https://arxiv.org/abs/0811.1067v2), §6.1).
