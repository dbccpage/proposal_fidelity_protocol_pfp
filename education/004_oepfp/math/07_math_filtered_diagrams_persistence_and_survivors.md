---
documentation_contract: symbol-game-documentation/v1
title: 'Chapter 07: Filtered Diagrams, Persistence, and Survivor Generating Functions'
kind: mathematical-reference
audience:
- researchers
- category-theorists
- spectral-theorists
- coding-agents
status: active
maturity: canonical
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - conditional_filtered_diagram
    - formal_ind_object_presentation
    - colimit_cohomology_module
    - free_commutative_survivor_monoid
    - formal_survivor_generating_function
    - analytic_convergence_condition
  prose_theorems:
    - formal_power_series_well_definedness
    - analytic_convergence_distinction
  lean_theorems: []
  finite_computations: []
  declared_policies:
    - conditional_tower_existence_fence
    - terminal_taxonomy_runtime_delegation
  applications: []
  open_conjectures:
    - analytic_meromorphic_continuation_conditions
coefficient_domain: "Formal Power Series ℤ[[z]] / ℂ"
runtime_dependency: "Chapter 06 (Extension, Retraction, Partial Descent, and Lift Obligations)"
governance_dependency: "governance-pfp"
---

# Chapter 07: Filtered Diagrams, Persistence, and Survivor Generating Functions

**Status:** Canonical Mathematics Specification (Spine Chapter 07)
**Authority:** None. Filtered colimits, ind-completions, and formal generating functions.

---

## 1. Filtered Systems: Conditional Framework, Not an Inevitable Tower

In formal mathematical modeling, infinite towers are treated not as completed actual infinities, but as **conditional filtered diagrams**:

> **Conditional Tower Invariant:**
> **If** an infinite compatible family of admitted finite presentations $\mathcal{M}_n$ and conservative transition morphisms $F_{n, n+1}$ is supplied, it determines a filtered diagram indexed by the poset $(\mathbb{N}, \le)$. The system does **not** assert that MSS-N already possesses a licensed, pre-existing infinite ascending tower; each extension step requires its own independent certificate and external authorization.

### 1.1 The Filtered Diagram in $\mathbf{FinSym}$

Let $\mathbf{FinSym}$ be the category whose objects are finite symbolic presentation stages $\mathcal{M}_n = (\mathcal{T}_n, \mathcal{C}_n, p_n, C^*_n)$ and whose morphisms $F_{n, m}: \mathcal{M}_n \to \mathcal{M}_m$ are conservative embeddings. A family of stages forms a filtered diagram:

$$D : (\mathbb{N}, \le) \longrightarrow \mathbf{FinSym}$$
$$\mathcal{M}_0 \xrightarrow{\;F_{0,1}\;} \mathcal{M}_1 \xrightarrow{\;F_{1,2}\;} \mathcal{M}_2 \xrightarrow{\;F_{2,3}\;} \cdots$$

equipped with syntax retractions on old terms ($U_n \circ F_{n, n+1} = \mathrm{id}_{\mathcal{T}_n}$) and typed partial descent operators.

### 1.2 Ind-Objects vs. Presheaf Colimits

Because infinite objects do not exist inside the category of strictly finite presentations $\mathbf{FinSym}$, asymptotic limits are characterized via standard category-theoretic completions:

1. **Formal Ind-Object:** In the ind-completion $\operatorname{Ind}(\mathbf{FinSym})$ (the free category obtained by adjoining filtered colimits), the formal limit is the **ind-object**:
   $$\mathrm{MSS}_\infty = (\mathcal{M}_n)_{n \in \mathbb{N}} \in \operatorname{Ind}(\mathbf{FinSym})$$
2. **Concrete Presheaf Colimit:** Via the Yoneda embedding $\mathbf{y}: \mathbf{FinSym} \hookrightarrow \operatorname{PSh}(\mathbf{FinSym}) = \mathbf{Set}^{\mathbf{FinSym}^{\mathrm{op}}}$, the colimit exists in the presheaf topos:
   $$\mathrm{MSS}_\infty \cong \varinjlim_{n \to \infty} \mathbf{y}(\mathcal{M}_n)$$
   evaluated on any finite test context $K \in \mathbf{FinSym}$ as the filtered colimit of sets:
   $$\mathrm{MSS}_\infty(K) \cong \varinjlim_{n \to \infty} \operatorname{Hom}_{\mathbf{FinSym}}(K, \mathcal{M}_n)$$
   *(Note: A single sufficiently large stage need not suffice to stabilize the hom-set; even maps from a singleton into an increasing family of finite structures do not generally attain a single terminal constant).*

---

## 2. Directed Colimit Cohomology and the Survivor Monoid

A bare set union of cohomology groups carries no intrinsic multiplication. The persistent cohomology space across an admitted sequence of stages is the directed colimit under induced forward morphisms $(I_n^1)^*: H^1_n \to H^1_{n+1}$ (which are well-defined because $I_n^\bullet$ is a graded algebraic cochain map commuting with differentials, $d_{n+1}^k I_n^k = I_n^{k+1} d_n^k$):

$$H^1_\infty = \varinjlim (H^1_n, (I_n^1)^*)$$

The directed colimit $H^1_\infty$ (which includes zero) is the persistent cohomology $\mathbb{Q}$-module (the **survivor module**). Classes that are eventually repaired at some finite stage ($(I_{n+k-1}^1)^* \cdots (I_n^1)^*([c]) = [0]$) vanish in the colimit; the non-zero elements $[c] \ne 0 \in H^1_\infty$ are the non-trivial persistent survivor classes.

### 2.1 The Free Commutative Survivor Monoid $\mathcal{H}$

To form a multiplicative generating function, an explicit generating family of primitive cycles must be declared:

$$\mathcal{H} = \operatorname{FreeComm}(\mathcal{P})$$

1. **Declared Primitive Cycles ($\mathcal{P}$):** A selected family of non-zero cycle generators representing distinct basis rays in $H^1_\infty$.
2. **Additive Discrete Degree ($\deg$):** Each generator $p \in \mathcal{P}$ carries an additive degree $\deg(p) \in \mathbb{N}_{\ge 1}$ (measuring minimal edge-cycle length or support).
3. **Local Finiteness:** For every degree $d \in \mathbb{N}_{\ge 1}$, the fiber $\{p \in \mathcal{P} : \deg(p) = d\}$ is finite.
4. **Additive Extension:** The degree extends additively over formal monoid words:
   $$\deg(p_1^{k_1} \cdots p_r^{k_r}) = \sum_{i=1}^r k_i \deg(p_i)$$

---

## 3. Survivor Generating Functions vs. Analytic Dirichlet Functions

Under the additive grading and local finiteness of $\mathcal{P}$, the formal generating function is well-defined:

$$\zeta_{\mathrm{surv}}(z) = \sum_{h \in \mathcal{H}} z^{\deg(h)} = \prod_{p \in \mathcal{P}} \frac{1}{1 - z^{\deg(p)}} \in \mathbb{Z}[[z]]$$

### 3.1 Strict Epistemic Fence: Formal Series vs. Analytic Functions

A critical claim hygiene boundary must be enforced:

$$\boxed{\text{Formal Survivor Generating Function } \zeta_{\mathrm{surv}}(z) \;\neq\; \text{Analytic Dirichlet Function } \zeta(s)}$$

1. **Formal Power Series Status:**
   Local finiteness in each degree ensures that for every $n$, the coefficient of $z^n$ in the expanded product $\prod_{p \in \mathcal{P}} (1 - z^{\deg(p)})^{-1}$ is a **finite integer**. Hence, $\zeta_{\mathrm{surv}}(z)$ is a mathematically well-defined element of the formal power series ring $\mathbb{Z}[[z]]$.
2. **Analytic Convergence Requirement:**
   Substituting $z = e^{-s}$ to produce a Dirichlet series $\sum_{h} e^{-s \deg(h)}$ does **not** automatically possess a non-empty half-plane of absolute convergence $\operatorname{Re}(s) > \sigma_0$. Analytic convergence requires an explicit growth condition on the primitive count, such as bounded exponential growth:
   $$|\{p \in \mathcal{P} : \deg(p) = d\}| \le C \cdot M^d$$
   Without an explicit proof of such a growth bound for a specific graph complex, $\zeta_{\mathrm{surv}}(z)$ must be handled strictly as a formal algebraic generating function, not an analytic complex function.

   *Why the bound is enough (2026-10-20):* if $|\{p : \deg(p) = d\}| \le C M^d$ and $|z| < 1/M$, then $\sum_p |z|^{\deg(p)} \le \sum_{d \ge 1} C (M|z|)^d = C M|z| / (1 - M|z|) < \infty$, and a product $\prod_p (1 - z^{\deg p})^{-1}$ whose terms satisfy $\sum_p |z|^{\deg p} < \infty$ converges absolutely. With $z = e^{-s}$ this gives absolute convergence for $\operatorname{Re}(s) > \log M$.

**Worked example (2026-10-20).**

1. *One survivor of degree 3* (for instance a single unfilled triangle that survives every lift): $\mathcal{P} = \{p\}$ with $\deg p = 3$, so $\zeta_{\mathrm{surv}}(z) = (1 - z^3)^{-1} = 1 + z^3 + z^6 + \cdots$. The coefficient of $z^n$ is 1 when $3 \mid n$ and 0 otherwise: the only monoid words are $p^k$.
2. *Two survivors of degrees 1 and 2*: $\zeta_{\mathrm{surv}}(z) = (1 - z)^{-1}(1 - z^2)^{-1} = 1 + z + 2z^2 + 2z^3 + 3z^4 + \cdots$. The coefficient of $z^4$ is 3 because the words of degree 4 are $p_1^4$, $p_1^2 p_2$ and $p_2^2$.
3. *A family that is not locally finite* fails the hypothesis: if infinitely many primitives had degree 1, the coefficient of $z$ would be infinite and the product would not define an element of $\mathbb{Z}[[z]]$.

---

## 4. Diagnostic Classes vs. Runtime Terminal Delegation

In mathematical specifications, cochain analysis identifies the **diagnostic class** of a configuration:
- Exact Repairable: $\Phi_n([x]) = 0$,
- Stabilized Survivor: $\Phi_n([h]) > 0$ and $\Gamma_2(h) = 0$,
- Open Higher Discrepancy: $\Phi_n([x]) > 0$ and $\Gamma_2(x) > 0$.

> **Governance Delegation Invariant:**
> Mathematical theory defines algebraic and topological diagnostic classes. The mapping of operational execution traces into execution terminals (`Certified`, `Refusal`, `Pending`, `BudgetExhausted`) is governed strictly by runtime host architecture and the parent skill `governance-pfp`. Mathematical documents do not establish standalone terminal execution state machines.

---

## 5. Epistemic Hygiene Ledger

### 5.1 What This Theory Supports
1. Demonstrates that an infinite family of compatible finite symbolic presentations forms a standard filtered diagram in $\operatorname{Ind}(\mathbf{FinSym})$ and a presheaf colimit in $\operatorname{PSh}(\mathbf{FinSym})$.
2. Establishes the persistent cohomology colimit $H^1_\infty$ and the formal algebraic Euler product $\prod_p (1 - z^{\deg p})^{-1}$ over a locally finite primitive monoid.

### 5.2 What This Theory Does NOT Support
1. **Does NOT prove that MSS-N forms an inevitable or pre-existing infinite tower:** Extensions require certified lift contracts and external authorization at every step.
2. **Does NOT establish analytic continuation or the Riemann Hypothesis:** The generating function is a formal series; analytic convergence and functional equations require separate, unproved geometric hypotheses.
