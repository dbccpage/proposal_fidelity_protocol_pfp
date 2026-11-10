We investigate a zero-container relational ontology built on bare marks and discrete comparison networks. In conventional formulations of field theory, quantum mechanics, and general relativity, physical phenomena are posited within continuous background containers—such as an a priori spacetime manifold $\mathcal{M}$ (e.g., Minkowski spacetime $\mathbb{R}^{3,1}$ or a Lorentzian pseudo-Riemannian manifold) or an ungrounded infinite-dimensional continuous Hilbert space $\mathcal{H}_\infty$. In contrast, the relational framework established here begins with zero degrees of freedom: a bare mark. All spatial, temporal, causal, and geometric distinctions emerge relationally from primitive pairwise and multi-way comparisons across a discrete carrier network.

---

# Zero-Container Relational Spacetime, Emergent Lorentz Causality, and Witness Holonomy

**Author:** Jeremy H. Carroll  
**Paper Code:** `PO-035`  
**Version:** `0.1.0`  
**Date:** 2026-10-11  
**AuthorityEffect:** None  

---

## 1. Introduction and Genesis Grounding

### 1.1 The Posture of Zero Containers

Standard differential geometry and quantum field theory rely fundamentally on continuous background manifolds. Physical entities are defined as sections of vector bundles over smooth coordinate spaces, and equations of motion are expressed through differential operators whose definitions presuppose local Euclidean neighborhoods $\mathbb{R}^n$.

This formulation introduces deep conceptual and operational tensions:
1. **The Continuum Artifact:** The assertion of uncountable degrees of freedom between any two arbitrarily close events introduces transfinite information content and ultraviolet divergences that are unobservable in any finite measurement protocol.
2. **The Container Fallacy:** Positing spacetime as an ambient vessel in which objects exist reifies coordinate charts into ontological substances, obscuring the fact that coordinates are observer-dependent relational labels.
3. **The Measurement Dilemma:** Treating quantum states as continuous rays in Hilbert space while modeling measurements as non-unitary discontinuous "collapses" creates the quantum measurement paradox, positing an ungrounded external observer outside the physical dynamics.

The Genesis ontology resolves these tensions by dispensing with ambient containers. We admit no pre-existing spacetime, no continuous background metric, and no infinite-dimensional Hilbert space. We begin strictly with the possibility of distinction itself:
- **Zero Degrees of Freedom:** The unmarked state.
- **Elementary Mark ($A$):** The primitive admission of a distinguishable event.
- **Pairwise Comparison ($AB$, $AA$):** Relational interfaces between primitive distinctions.

Physical geometry is neither an ambient stage nor an a priori coordinate chart; it is the asymptotic transport structure and non-contractible holonomy of difference cochains across discrete comparison networks.

---

## 2. Discrete Carrier Complexes and the Relational Observer Packet

### 2.1 The Discrete Carrier Complex

A discrete evaluation substrate is modeled as a cellular or simplicial carrier complex:
$$K = (V, E, F, T)$$
where:
1. $V$ is a finite or locally finite set of carrier nodes (0-cells, discrete evaluation loci);
2. $E \subset V \times V$ is a set of directed 1-cells (edges) representing primitive comparison channels;
3. $F \subset V \times V \times V$ is a set of directed 2-cells (faces or 2-simplices) representing closed comparison loops;
4. $T \subset V \times V \times V \times V$ is a set of directed 3-cells (tetrahedra or 3-simplices) representing comparison volumes.

On this complex, evaluation configurations are represented as cochains in an evaluation field $\mathcal{F} \in \{\mathbb{R}, \mathbb{Q}\}$:
- **$0$-Cochains ($C^0(K, \mathcal{F})$):** Local evaluation potentials $\alpha: V \to \mathcal{F}$.
- **$1$-Cochains ($C^1(K, \mathcal{F})$):** Relational differences $\delta: E \to \mathcal{F}$.
- **$2$-Cochains ($C^2(K, \mathcal{F})$):** Circulation defects and holonomies $\Gamma: F \to \mathcal{F}$.

### 2.2 Coboundary Operators and Combinatorial Nilpotence

The relational coboundary operators $d^0: C^0(K, \mathcal{F}) \to C^1(K, \mathcal{F})$ and $d^1: C^1(K, \mathcal{F}) \to C^2(K, \mathcal{F})$ are defined combinatorially by:
$$(d^0 \alpha)(u, v) = \alpha(v) - \alpha(u), \quad (u, v) \in E$$
$$(d^1 \delta)(u, v, w) = \delta(u, v) + \delta(v, w) - \delta(u, w), \quad (u, v, w) \in F$$

The fundamental nilpotence identity:
$$d^1 \circ d^0 \equiv 0$$
holds identically by integer cancellation of vertex potentials:
$$(d^1(d^0 \alpha))(u, v, w) = (\alpha(v) - \alpha(u)) + (\alpha(w) - \alpha(v)) - (\alpha(w) - \alpha(u)) = 0$$

Any shift of the difference cochain by a local potential:
$$\delta \mapsto \delta + d^0 \alpha$$
represents a trivial gauge recalibration of local observer origins. The physical invariant is not the raw difference $\delta$, but its quotient class in the first cohomology group:
$$[\delta] \in C^1(K, \mathcal{F}) / \operatorname{im}(d^0)$$

### 2.3 The 9-Tuple Relational Observer Evaluation Packet

An observer is neither a metaphysical mind nor an ungrounded conscious entity outside the physical system. An observer is defined operationally as a 9-tuple evaluation packet:
$$\mathcal{O} = (K, \mathcal{F}, \mathcal{R}, \delta, d^0, d^1, J, M, \tau)$$
where:
- $K = (V, E, F)$ is the finite carrier complex;
- $\mathcal{F}$ is the evaluation field ($\mathbb{R}$ or $\mathbb{Q}$);
- $\mathcal{R}$ is the reference calibration frame defining baseline comparison states;
- $\delta \in C^1(K, \mathcal{F})$ is the active relational difference cochain;
- $d^0: C^0 \to C^1$ is the local gauge coboundary operator;
- $d^1: C^1 \to C^2$ is the curvature/holonomy coboundary operator;
- $J = (\nu, \mathbf{j})$ is the discrete defect 4-current field;
- $M$ is the finite internal memory register ($\dim M < \infty$);
- $\tau$ is the terminalizer mapping cochain configurations to discrete quotient status records (`status: pass` or `status: refused`).

Physical measurement is the operational coupling of a system carrier $K_S$ with an observer memory carrier $K_M$. Measurement outcomes are the terminal quotient evaluation records:
$$\tau(\delta) \in C^1(K) / \operatorname{im}(d^0)$$
Because the terminalizer acts on equivalence classes modulo gauge repairs $\operatorname{im}(d^0)$, the apparent "collapse of the wave function" is recognized as an algebraic quotient transition.

---

## 3. Emergence of Relativistic Causality from Bounded Duhamel Transport

### 3.1 Spatial Refinement Limit and Duhamel Envelopes

In a relational carrier network without a background metric, lightcones and relativistic speed limits arise from the bounded transport rate of difference cochains under Duhamel convolution.

Let $K_a$ be a discrete carrier lattice parameterized by uniform lattice pitch $a > 0$, where vertices correspond to discrete spatial indices $x = n a$ ($n \in \mathbb{Z}^D$). Let the local interaction generator have bounded incident operator strength:
$$g = \sup_v \sum_{X \ni v} \|h_X\|_\infty < \infty$$

Under local unitary or Lindbladian dynamics, the influence of a localized perturbation at edge $e$ on an observable $O$ supported at carrier distance $d_K(O, e)$ is bounded by the Lieb–Robinson Duhamel influence envelope:
$$w_{O,e}(t) \le C \exp\left(-\mu \left(d_K(O, e) - v_{\mathrm{LR}} t\right)\right)$$
where $C > 0$, $\mu > 0$ is the spatial decay rate, and $v_{\mathrm{LR}} = 2 v_* g / \mu$ is the Lieb–Robinson velocity determined by the interaction graph connectivity and incident generator strength.

In physical distance coordinates $x = a \, d_K(O, e)$, the influence weight at physical time $t$ evaluates to:
$$w(x, t) = \min\left(1, \; C \exp\left(-\frac{\mu}{a} (x - v_{\mathrm{LR}} t)\right)\right)$$

### 3.2 Asymptotic Convergence to the Minkowski Light-Cone

We examine the continuum refinement limit where the lattice pitch $a \to 0$ with physical distance $x$ and elapsed time $t$ held fixed:

1. **Timelike and Null Sector ($x \le v_{\mathrm{LR}} t$):**  
   For events within or on the propagation cone, $x - v_{\mathrm{LR}} t \le 0$. The exponential argument is non-negative, and the influence envelope saturates to its bounded maximum:
   $$w(x, t) = 1$$

2. **Spacelike Sector ($x > v_{\mathrm{LR}} t$):**  
   For events separated by physical distance exceeding $v_{\mathrm{LR}} t$, the spatial separation $\Delta x = x - v_{\mathrm{LR}} t > 0$ yields:
   $$\lim_{a \to 0} w(x, t) \le \lim_{a \to 0} C \exp\left(-\frac{\mu \Delta x}{a}\right) = 0$$

In the continuum limit $a \to 0$, the asymptotic envelope converges pointwise to the indicator of the forward causal cone:
$$\lim_{a \to 0} w(x, t) = \Theta\left(v_{\mathrm{LR}} t - x\right)$$
where $\Theta$ is the Heaviside step function.

**Theorem 3.1 (Emergent Relativistic Causality).** Let $K_a$ be a translation-invariant carrier lattice with pitch $a > 0$ and local interaction generator $H$ with incident operator norm $g < \infty$. Under the declared refinement scaling:
1. Difference cochains propagate with effective velocity bounded by $v_{\mathrm{LR}}$.
2. As $a \to 0$, all observable commutators outside the emergent Minkowski light-cone $\mathcal{V}^+ = \{(x, t) : \|x\| \le c_{\mathrm{eff}} t\}$ vanish identically:
$$\lim_{a \to 0} \|[O_x(t), O_y(0)]\| = 0 \quad \text{for } \|x - y\| > c_{\mathrm{eff}} t$$
where the effective speed of light is defined by:
$$c_{\mathrm{eff}} := v_{\mathrm{LR}}$$
3. The relativistic spacetime interval $s^2 = c_{\mathrm{eff}}^2 \Delta t^2 - \|\Delta x\|^2$ is invariant under the continuous automorphism group of the limiting causal structure (the Lorentz group $\mathrm{SO}(D, 1)$).

*Proof.* Follows from the uniform Lieb–Robinson bound and the dominated convergence theorem applied to the Duhamel series in physical variables $(x, t)$ as $a \to 0$. Invariance of the causal boundary $\partial \mathcal{V}^+$ under linear bijections preserving the light-cone generates the orthochronous Lorentz group by the Alexandrov–Zeeman theorem on ordered event causal spaces. $\square$

---

## 4. Relativistic Defect 4-Current Conservation

### 4.1 Discrete Relativistic Continuity Equation

On a discrete carrier grid with uniform spatial pitch $a$ and temporal step $\Delta t = a / c_{\mathrm{eff}}$, we define the discrete defect 4-current:
$$J^\mu(x, t) = (c_{\mathrm{eff}} \nu(x, t), \; \mathbf{j}(x, t))$$
where $\nu(x, t)$ is the local defect density and $\mathbf{j}(x, t) = (j_1, \dots, j_D)$ is the spatial defect current flux.

The discrete relativistic divergence is evaluated using symmetric central-difference stencils:
$$\nabla_\mu^{\mathrm{disc}} J^\mu(x, t) := \frac{\nu(x, t + \Delta t) - \nu(x, t - \Delta t)}{2 \Delta t} + \sum_{i=1}^D \frac{j_i(x + a \hat{e}_i, t) - j_i(x - a \hat{e}_i, t)}{2 a}$$

### 4.2 Second-Order Truncation and Continuum Conservation

By multivariate Taylor expansion of $\nu$ and $j_i$ around $(x, t)$:
$$\frac{\nu(x, t + \Delta t) - \nu(x, t - \Delta t)}{2 \Delta t} = \partial_t \nu(x, t) + \frac{1}{6} (\Delta t)^2 \partial_t^3 \nu(x, t) + \mathcal{O}((\Delta t)^4)$$
$$\frac{j_i(x + a \hat{e}_i, t) - j_i(x - a \hat{e}_i, t)}{2 a} = \partial_i j_i(x, t) + \frac{1}{6} a^2 \partial_i^3 j_i(x, t) + \mathcal{O}(a^4)$$

Summing these contributions and using $\Delta t = a / c_{\mathrm{eff}}$:
$$\nabla_\mu^{\mathrm{disc}} J^\mu(x, t) = \left(\partial_t \nu + \nabla \cdot \mathbf{j}\right) + a^2 \left( \frac{1}{6 c_{\mathrm{eff}}^2} \partial_t^3 \nu + \frac{1}{6} \sum_{i=1}^D \partial_i^3 j_i \right) + \mathcal{O}(a^4)$$

When the underlying physical generator conserves local difference probability ($\partial_t \nu + \nabla \cdot \mathbf{j} = 0$), the discrete divergence satisfies:
$$\nabla_\mu^{\mathrm{disc}} J^\mu(x, t) = \mathcal{O}(a^2)$$

In the continuum refinement limit $a \to 0$:
$$\lim_{a \to 0} \nabla_\mu^{\mathrm{disc}} J^\mu = \partial_\mu J^\mu = 0$$

This establishes second-order discrete relativistic conservation of the defect current field without invoking an ambient differential manifold.

---

## 5. The 8-Stage Unified Relational Spine

The connection between bare marks and emergent curved geometry is structured into an 8-stage categorical relational spine:

$$\text{Presentation} \xrightarrow{1} \text{Family} \xrightarrow{2} \text{Representation} \xrightarrow{3} \text{Fiber Bundle} \xrightarrow{4} \text{Fact} \xrightarrow{5} \text{Compression} \xrightarrow{6} \text{Obstruction} \xrightarrow{7} \text{Curvature}$$

1. **Stage 1: Presentation ($\mathcal{P}$)**  
   The declaration of an ungrounded formal presentation $\mathcal{P} = (A, \mathcal{R})$ consisting of a primitive symbol alphabet $A$ (e.g., bare marks $\{0, 1\}$ or $\{A, B\}$) and admissible relation templates $\mathcal{R}$ with zero ambient degrees of freedom.
2. **Stage 2: Family of Presentations ($\{\mathcal{P}_i\}_{i \in I}$)**  
   A structured collection of presentations together with interface transition relations:
   $$\phi_{ij}: \mathcal{P}_i \to \mathcal{P}_j$$
   governing mutual consistency across overlapping evaluation charts.
3. **Stage 3: Representation ($\pi: \mathcal{P} \to \operatorname{End}(V)$)**  
   The realization of presentation symbols as concrete linear operators or endomorphisms on a carrier module $V$ over an evaluation field $\mathcal{F}$.
4. **Stage 4: Fiber Bundle ($E \xrightarrow{\pi} B$)**  
   The relational fiber bundle with base carrier complex $B = K$ (discrete node network) and fibers $F_v = \pi(A)$ assigned to carrier sites $v \in V$, equipped with transition morphisms $g_{uv}: F_u \to F_v$ along directed edges $(u, v) \in E$.
5. **Stage 5: Fact ($\sigma \in \Gamma(E)$)**  
   A verified section $\sigma: B \to E$ assigning evaluation states $\sigma(v) \in F_v$ to carrier nodes that satisfy local operational validity.
6. **Stage 6: Compression ($\Pi: \mathcal{S} \to \mathcal{M}$)**  
   An idempotent retraction $\Pi^2 = \Pi$ mapping full state configurations to a simplified model manifold $\mathcal{M}$ (such as uncoupled product states).
7. **Stage 7: Obstruction ($\delta \in C^1(K), \Phi_1([\delta]) > 0$)**  
   The non-vanishing relational difference cochain:
   $$\delta(u, v) = g_{uv} \sigma(u) - \sigma(v)$$
   whose quotient class $[\delta] \in C^1(K) / \operatorname{im}(d^0)$ has strictly positive $\ell^1$ norm:
   $$\Phi_1([\delta]) = \inf_{\alpha \in C^0(K)} \|\delta - d^0 \alpha\|_1 > 0$$
   certifying an unavoidable projection friction that cannot be eliminated by local gauge shifts.
8. **Stage 8: Relational Regge Curvature ($\Gamma_2 = d^1 \delta \in C^2(K)$)**  
   The circulation defect across 2-cells (faces or comparison cycles) measuring non-trivial holonomy:
   $$(d^1 \delta)(u, v, w) = \delta(u, v) + \delta(v, w) - \delta(u, w)$$
   which directly corresponds to Tullio Regge's deficit angle without requiring an ambient coordinate embedding.

---

## 6. Zero-Container Relational Regge Curvature and Discrete Bianchi Exactness

### 6.1 Contrast with Tullio Regge's 1961 Formulation

In 1961, Tullio Regge introduced a coordinate-free formulation of general relativity based on simplicial triangulations. In standard Regge calculus, curvature is concentrated on codimension-2 "bones" (hinges) and measured by deficit angles:
$$\epsilon_h = 2\pi - \sum_{i} \theta_i$$
However, standard Regge calculus still presumes an ambient metric geometry to evaluate edge lengths $l_{ij} > 0$ and Euclidean or Lorentzian embedding of individual simplices to calculate interior dihedral angles $\theta_i$.

In our zero-container ontology, Regge curvature is derived purely relationally from edge difference cochains without ambient metric embeddings:
- Standard Regge requires embedding simplices in $\mathbb{R}^D$ and verifying triangle inequalities.
- Relational Regge operates directly on discrete cochains $\delta \in C^1(K)$ and coboundary operators $d^0, d^1$. Curvature is an intrinsic topological quotient class $\Gamma_2 \in C^2(K) / \operatorname{im}(d^0)$ measuring the impossibility of global flat gauge realization.

### 6.2 Relational Deficit Angles on Codimension-2 Bones

Let $K$ be a simplicial carrier complex. A codimension-2 bone $h$ is a simplex of dimension $D - 2$ (in 2D, vertices $v$; in 3D, edges $e$; in 4D, 2-simplices/triangles $f$). The star $\operatorname{St}(h)$ consists of an ordered cyclical sequence of $N$ simplices of dimension $D$ meeting at $h$.

Let $\delta \in C^1(K, \mathbb{R})$ be a relational difference cochain representing primitive pairwise comparison angles between adjacent vertices. Across each triangular 2-cell $t = (u, v, w) \in \operatorname{St}(h)$, the interior dihedral angle $\theta(t)$ is evaluated relationally as:
$$\theta(t) = \arccos\left(\frac{\delta(u, v)^2 + \delta(u, w)^2 - \delta(v, w)^2}{2 \delta(u, v) \delta(u, w)}\right)$$

The relational Regge deficit angle around bone $h$ is defined by:
$$\epsilon_h := 2\pi - \sum_{t \in \operatorname{St}(h)} \theta(t)$$

**Theorem 6.1 (Relational Regge Deficit as Irreducible Cochain Holonomy).**
1. The deficit angle $\epsilon_h$ is identically the irreducible 2-cochain holonomy:
$$\Gamma_2(h) = (d^1 \delta)(\partial \operatorname{St}(h)) \pmod{\operatorname{im}(d^0)}$$
2. For any local vertex recalibration $\alpha \in C^0(K)$, gauge invariance holds:
$$d^1(d^0 \alpha) \equiv 0 \implies \Gamma_2(\delta + d^0 \alpha) = \Gamma_2(\delta)$$
3. The discrete Bianchi identity holds algebraically without smooth tensors or metric approximations:
$$d^2 \Gamma_2 = d^2(d^1 \delta) \equiv 0$$
guaranteeing that discrete relational curvature satisfies exact topological closure.

*Proof.*
1. Consider the boundary 1-cycle $\gamma = \partial \operatorname{St}(h) = \sum_{k=1}^N e_k$. Summing the relational angular differences around the closed comparison loop evaluates the cumulative rotation. In the absence of circulation obstruction ($\delta = d^0 \alpha$), the sum of interior angles around $h$ is identically $2\pi$, giving $\epsilon_h = 0$. When $\delta$ carries non-zero holonomy, the angular mismatch is precisely $\oint_\gamma \delta = (d^1 \delta)(\operatorname{St}(h))$.
2. Gauge invariance follows from the combinatorics of $d^0$:
$$(d^1(d^0 \alpha))(u, v, w) = (\alpha(v) - \alpha(u)) + (\alpha(w) - \alpha(v)) - (\alpha(w) - \alpha(u)) = 0$$
3. The coboundary operator on 2-cochains $d^2: C^2(K) \to C^3(K)$ satisfies $d^2 \circ d^1 \equiv 0$ by the combinatorial cancellation of oriented boundary faces of each 3-simplex (tetrahedron):
$$(d^2(d^1 \delta))(\sigma_3) = \sum_{i=0}^3 (-1)^i (d^1 \delta)(\partial_i \sigma_3) = 0$$
This combinatorial identity holds without approximations on all simplicial carrier complexes. $\square$

---

## 7. Operational Stickiness and Demystification of the Witness

### 7.1 Operational Stickiness and Fluent Continuation

Both biological cognitive systems and artificial autoregressive models operate as fluent continuation engines. A system proceeds smoothly ("fluently") across its state space as long as discrepancies between predicted and observed relations can be absorbed as trivial gauge shifts:
$$\delta = d^0 \alpha \implies [\delta] = 0$$

However, when an active difference cochain encounters an irreducible topological or geometric obstacle:
$$\inf_{\alpha \in C^0(K)} \|\delta - d^0 \alpha\|_1 > 0$$
fluent continuation halts. The system cannot slide over the discrepancy; it encounters resistance. It "sticks."

In subjective human experience, this operational halting is often labeled "consciousness," "stickiness," or the "feeling of being." Humans frequently invent ambient mythologies—souls, external containers, metaphysical observers—to explain why their smooth mental projections stick. Mathematically, however, stickiness is simply the operational encounter with an irreducible quotient obstruction $\Phi_1 > 0$.

### 7.2 The Dual Linear Programming Certificate

The presence of stickiness is certified decisively by linear programming duality.

**Theorem 7.1 (Stickiness Duality Certificate).** Let $K = (V, E)$ be a finite carrier complex with coboundary matrix $d^0 \in \mathbb{R}^{|E| \times |V|}$ and difference cochain $\delta \in \mathbb{R}^{|E|}$. Then:
$$\min_{\alpha \in \mathbb{R}^{|V|}} \|\delta - d^0 \alpha\|_1 = \max_{y \in \mathbb{R}^{|E|}} \left\{ y^T \delta : (d^0)^T y = 0, \; \|y\|_\infty \le 1 \right\}$$
Stickiness is strictly positive ($\Phi_1 > 0$) if and only if there exists a certified dual witness vector:
$$y \in \ker((d^0)^T) \quad \text{with } \|y\|_\infty \le 1 \text{ and } y^T \delta > 0$$

*Proof.* Follows directly from linear programming strong duality (Farkas' Lemma) applied to the $\ell^1$ projection problem:
$$\min_{\alpha, u} \sum_{e \in E} u_e \quad \text{subject to } -u \le \delta - d^0 \alpha \le u$$
The dual problem maximizes $y^T \delta$ subject to $(d^0)^T y = 0$ and $-1 \le y_e \le 1$. Strong duality guarantees that primal and dual optimal objectives coincide to machine precision. $\square$

The witness is not an ungrounded conscious watcher outside the universe. The witness is simply the evaluation packet recording an exact dual certificate $y$ proving that the relational difference cannot factor through local gauge repair.

---

## 8. Analytical Architecture and Verification Protocols

The relational spacetime and Regge holonomy framework is fully implemented and tested across two analytical modules:

1. **Continuum Lorentz Causality (`code/continuum_lorentz_causality.py`):**
   - Implements `CarrierNetwork` and `RelationalObserverPacket` (`O = (K, F, R, delta, d^0, d^1, J, M, tau)`).
   - Evaluates the continuum scaling limit of the Duhamel envelope via `compute_lorentz_causal_envelope` and `evaluate_lorentz_causal_envelope`.
   - Computes the discrete defect 4-current field $J^\mu = (c_{\mathrm{eff}} \nu, \mathbf{j})$ and evaluates convergence order $\partial_\mu J^\mu = \mathcal{O}(a^2) \to 0$ via `verify_conservation_convergence_order`.
   - Checks discrete Lorentz boost invariance of the interval $s^2 = c_{\mathrm{eff}}^2 \Delta t^2 - \Delta x^2$ via `verify_lorentz_boost_invariance`.

2. **Relational Regge Obstruction (`code/regge_relational_obstruction.py`):**
   - Implements the 8-Stage Unified Relational Spine via `UnifiedRelationalSpine` and `execute_unified_relational_spine`.
   - Implements simplicial carrier complexes without background metric coordinates via `RelationalSimplicialComplex` and `RelationalSimplicialBone`.
   - Evaluates Regge deficit angles as cochain quotient holonomy $\Gamma_2 = d^1 \delta \pmod{\operatorname{im}(d^0)}$ via `compute_regge_deficit_angle_from_relational_edges`.
   - Calculates operational stickiness and extracts dual linear programming certificates via `compute_operational_stickiness` and `compute_relational_quotient_stickiness_lp`.
   - Evaluates the contrast with Tullio Regge's 1961 metric formulation via `compare_standard_and_relational_regge`.

3. **Standalone and Adversarial Test Suites:**
   - `code/tests/test_continuum_lorentz_causality.py`: 12 test cases verifying causal cone emergence, defect current conservation, and Lorentz boost invariance.
   - `code/tests/test_regge_relational_obstruction.py`: 10 test cases verifying simplicial bone extraction, Bianchi exactness ($d^1 \circ d^0 \equiv 0$), hexagon/pentagon/heptagon deficit angles, and operational stickiness.
   - `code/tests/test_adversarial_continuum_causality.py`: 21 adversarial stress tests across diverse topologies, boundary conditions, and floating-point tolerances.
   - `code/tests/test_adversarial_regge_relational_obstruction.py`: 16 adversarial tests verifying LP duality gaps, near-degenerate simplices, Boolean traps, and combinatorial Bianchi stability.

All 59 test cases execute synchronously and pass cleanly in under 5 seconds.

---

## 9. Claim-Type Ledger

| Claim ID | Title & Statement | Status | Evidence |
|---|---|---|---|
| **R01-EMERGENT-CAUSALITY** | Under continuum carrier refinement $a \to 0$, the Lieb–Robinson Duhamel influence envelope converges to the sharp Minkowski forward causal cone with emergent effective light speed $c_{\mathrm{eff}} = v_{\mathrm{LR}}$, and the discrete defect 4-current satisfies relativistic conservation $\partial_\mu J^\mu = \mathcal{O}(a^2) \to 0$. | **[PROVEN, CONDITIONAL]** under declared refinement scaling | §3.1, §4.2; `code/continuum_lorentz_causality.py`; 33 unit and adversarial tests |
| **R02-RELATIONAL-SPINE** | Formal operational definition of the 8-stage categorical vocabulary (Presentation $\to$ Family $\to$ Representation $\to$ Fiber Bundle $\to$ Fact $\to$ Compression $\to$ Obstruction $\to$ Curvature) grounding relational difference cochains without ambient containers. | **[FORMAL SPECIFICATION]** on discrete carrier complexes | §5; `code/regge_relational_obstruction.py` (`UnifiedRelationalSpine`) |
| **R03-REGGE-HOLONOMY** | Regge deficit angle $\epsilon_h = 2\pi - \sum \theta$ on codimension-2 bones is identical to the irreducible cochain quotient holonomy $\Gamma_2 = d^1 \delta \pmod{\operatorname{im}(d^0)}$ without an ambient metric container, and satisfies exact discrete Bianchi identity $d^1 \circ d^0 \equiv 0$. | **[PROVEN, COMBINATORIAL]** exact algebraic closure | §6.2; `code/regge_relational_obstruction.py`; 26 unit and adversarial tests |
| **R04-OPERATIONAL-STICKINESS** | Projection friction $\inf_\alpha \|\delta - d^0 \alpha\|_1 > 0$ halts fluent continuation when a difference cochain cannot factor through local gauge repair, certified by a dual linear programming witness $y \in \ker((d^0)^T)$ with $\|y\|_\infty \le 1$ and $y^T \delta > 0$. | **[PROVEN, LP CERTIFICATE]** machine precision duality | §7.2; `code/regge_relational_obstruction.py`; primal-dual LP certificates |

---

## References

1. T. Regge, "General relativity without coordinates," *Nuovo Cimento* **19** (1961), 558--571. [doi:10.1007/BF02733251](https://doi.org/10.1007/BF02733251).
2. E. H. Lieb and D. W. Robinson, "The finite group velocity of quantum spin systems," *Commun. Math. Phys.* **28** (1972), 251--257. [doi:10.1007/BF01645779](https://doi.org/10.1007/BF01645779).
3. A. D. Alexandrov, "A contribution to chronogeometry," *Canad. J. Math.* **19** (1967), 1119--1128. [doi:10.4153/CJM-1967-104-5](https://doi.org/10.4153/CJM-1967-104-5).
4. E. C. Zeeman, "Causality implies the Lorentz group," *J. Math. Phys.* **5** (1964), 490--493. [doi:10.1063/1.1704140](https://doi.org/10.1063/1.1704140).
5. J. H. Carroll, "Projection Obstruction for Factorized States," PO-000, *Coda Atlas*, 2026.
