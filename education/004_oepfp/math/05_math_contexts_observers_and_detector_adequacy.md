---
documentation_contract: symbol-game-documentation/v1
title: 'Chapter 05: Contexts, Observers, Contextual Distinguishability, and Detector Adequacy'
kind: mathematical-reference
audience:
- researchers
- category-theorists
- evaluator-architects
- coding-agents
status: active
maturity: canonical
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - context_category_action
    - de_overloaded_observer_tuple
    - evaluation_cochain_map
    - contextual_non_congruence_witness
    - detector_adequacy_receipt
  prose_theorems:
    - non_congruence_characterization
    - detector_trivialization_modes
  lean_theorems: []
  lean_statements_not_elaborated:
    - PaperER007.lggr_global_green_does_not_descend
    - PaperER007.lggr_evaluator_defect_does_not_descend
    - PaperER007.local_consistency_without_bridge_maps_is_not_ready
  finite_computations: []
  declared_policies:
    - five_cardinal_evaluation_questions
    - genesis_audit_invariants
    - repair_extend_promote_separation
  applications: []
  open_conjectures: []
coefficient_domain: "ℚ (Cochain Evaluation Spaces)"
runtime_dependency: "Chapter 03 (Obstruction Mass, Duality, and Exact LP)"
governance_dependency: "governance-pfp"
---

# Chapter 05: Contexts, Observers, Contextual Distinguishability, and Detector Adequacy

**Status:** Canonical Mathematics Specification (Spine Chapter 05)
**Authority:** None. Category theory, evaluation semantics, and measurement boundary formalization.

---

## 1. Why Pure Homological Obstruction is Not Enough

A discrete system can contain an un-repairable cochain obstruction ($\Phi_1([c]) > 0$) without needing to expand its ontology or vocabulary. For example, in a maze with a closed boundary wall, the obstruction is part of the state space; one does not invent new grammatical primitives only because an obstacle is present.

In the Symbol Game and Minimal Symbol System architecture, an ontological upgrade is considered only when the system's **internal equivalence relation** fails to remain a congruence under external observational tests.

---

## 2. Ambient Categories and Context Actions

At stage $n$, an evaluation presentation is structured by two categories and their interaction:

1. **Term Category ($\mathcal{T}_n$):** A finite category whose objects are internal system states, expressions, or terms, and whose morphisms represent internal transitions.
2. **Context Category ($\mathcal{C}_n$):** A finite category whose objects are external testing environments, surrounding frames, or observers.
3. **Context Action ($\rho_n$):** A bifunctor $\rho_n: \mathcal{C}_n \times \mathcal{T}_n \to \mathcal{T}_n$ specifying how an external context acts on an internal term.

---

## 3. The De-Overloaded Observer Formalization

To eliminate symbol collisions in earlier literature (where $\tau$ was used simultaneously for the observation assignment and the final terminalizer), the observer is formalized as a clean **6-tuple**:

$$\boxed{\mathcal{O} = (C, p, \sim, W, V, \tau)}$$

| Component | Symbol | Type & Signature | Role in Evaluation |
| :--- | :---: | :--- | :--- |
| **Carrier** | $C$ | Finite locus set $V \cup E$ | The discrete domain of loci and cells being evaluated. |
| **Evaluation Map** | $p$ | $p: \operatorname{Ob}(\mathcal{T}_n) \to C^1_n$ | Assigns to each term a concrete 1-cochain against a declared ground state $x_0$. |
| **Comparison Relation** | $\sim$ | Binary relation on $\operatorname{Ob}(\mathcal{T}_n)$ | Quotient equivalence: $x \sim y \iff p(x) - p(y) \in W$. |
| **Repair Gauge** | $W$ | Subspace $W = \operatorname{im}(d_{0,n}) \subseteq C^1_n$ | Admitted exact potential adjustments that can absorb discrepancies. |
| **Deterministic Verifier** | $V$ | $V: C^1_n \to \operatorname{Receipt}$ | Computes certified primal distance and dual witness certificates. |
| **Terminalizer Policy** | $\tau$ | $\tau: \operatorname{Receipt} \to \mathbb{T}$ | Deterministic decision rule mapping verification receipts into terminal states. |

### 3.1 Functorial Cochain Assignment

The observation map $p: \mathcal{T}_n \to \mathbf{Ch}^1(C^1_n)$ maps internal terms and transitions into the difference groupoid:
- **On Objects:** $x \mapsto p(x) \in C^1_n$,
- **On Morphisms:** For transition $f: x \to y$, $p(f) = p(y) - p(x) \in C^1_n$.

Two terms $x, y \in \mathcal{T}_n$ are defined to be **homologically indistinguishable** at stage $n$ if their difference is an exact repair:
$$x \sim_n y \iff p(x) - p(y) \in \operatorname{im}(d_{0,n}) \iff [p(x)] = [p(y)] \in Q^1_n$$

---

## 4. Contextual Distinguishability & Non-Congruence Witnesses

In algebra, an equivalence relation $\sim$ is a **congruence** if it is preserved by all allowable operations:
$$\forall c \in \mathcal{C}_n, \quad x \sim_n y \implies \rho_n(c)x \sim_n \rho_n(c)y$$

When this holds, the quotient space is clean: replacing $x$ with $y$ in any context produces indistinguishable behavior.

### 4.1 The Contextual Non-Congruence Witness

A **Contextual Non-Congruence** occurs when the internal vocabulary asserts that $x$ and $y$ are equivalent, yet an allowed external context distinguishes them:

$$\boxed{x \sim_n y \quad \wedge \quad \rho_n(c)x \not\sim_n \rho_n(c)y \quad \text{for some } c \in \mathcal{C}_n}$$

The triple $w = (x, y, c)$ is called a **contextual non-congruence witness** *(formerly termed a "critical pair")*.

### 4.2 Semantic Collapse
Contextual non-congruence reveals a **semantic collapse** in the level-$n$ vocabulary:
- Internally, stage $n$ lacks the expressive degree of freedom to tell $x$ and $y$ apart ($p(x) - p(y) \in \operatorname{im}(d_0)$).
- Externally, context $c$ extracts an observable defect ($p(\rho(c)x) - p(\rho(c)y) \notin \operatorname{im}(d_0)$).

Under Symbol Game governance, this certified failure of congruence constitutes the formal trigger for proposing an ontological extension.

### 4.3 Finite Non-Factorization Statements in Lean (Global Query vs. Local Observation)

A mathematical example of contextual non-congruence is the failure of global evaluation queries to factor through local quotient observations. Stated in [`lean4/LggrNonFactorization.lean`](../../../../lean4/LggrNonFactorization.lean).

> **Build status (read 2026-10-20 at `c419cc6beb`):** the three names below are wrapper aliases of theorems in [`lean4/LGGR.lean`](../../../../lean4/LGGR.lean). The header of `LggrNonFactorization.lean` says that `LGGR` is not a package root, `LGGR.olean` is not in the build library, and `LGGR.lean`'s own imports are absent, so the import does not load. Neither file is a root of [`lean4/lakefile.lean`](../../../../lean4/lakefile.lean). These are source-visible Lean statements, not checked theorems at this pin; no Lean build was run in this check.

$$\boxed{\text{Global query does not factor through local observation quotient}}$$

1. **`PaperER007.lggr_global_green_does_not_descend`:** States that global classifier truth on finite boolean triples cannot factor through a local dashboard quotient without loss of information.
2. **`PaperER007.lggr_evaluator_defect_does_not_descend`:** States that integer evaluator defect cannot descend to the local quotient.
3. **`PaperER007.local_consistency_without_bridge_maps_is_not_ready`:** States that local consistency without declared bridge maps fails equivalence readiness.

> **Epistemic Scope Fence:**
> These Lean statements are finite combinatorial non-factorization theorems over explicit boolean state vectors. They demonstrate the obstruction to factoring global queries through local projections without asserting that the Symbol Game is a sheaf or that LGGR constitutes a topological cohomology class.

---

## 5. The Five Cardinal Evaluation Questions

Before any proposition of the form *"the system observed $X$"* or *"the evidence supports $Y$"* is evaluable, the evaluation packet must explicitly answer:

```text
1. Under what observer?
   What is the cryptographic manifest hash and identifier of O = (C, p, ~, W, V, τ)?

2. What was compared?
   Which carrier loci and evaluation projections p(x) were evaluated?

3. What counted as defect?
   What objective norm ||·||_{1, ω} and closure diagnostic Γ_2 were computed?

4. What repairs were allowed?
   What exact gauge subspace W = im(d_0) was permitted to absorb differences?

5. Who terminalized the result?
   By what deterministic verifier V and policy τ was the terminal state emitted?
```

### 5.1 The Three Genesis Invariants
1. **$P_0$ (No View from Nowhere):** Every observation must carry an explicit observer manifest hash.
2. **$P_1$ (Carrier Identity):** The carrier manifest hash must remain frozen throughout evaluation.
3. **$P_2$ (No Retroactive Cochains):** Higher cochain degrees cannot be retroactively injected into lower evaluations.

### 5.2 The Threefold Operational Law
$$\boxed{\text{repair} \;\neq\; \text{extend} \;\neq\; \text{promote}}$$
- **Repair:** Adjustment along the existing gauge subspace $W = \operatorname{im}(d_0)$.
- **Extend:** Licensing new cochain degrees of freedom $W \to W \oplus \Delta W$ under certified contracts.
- **Promote:** Human operator elevation of a certified context transition.

---

## 6. Measurement Boundaries and Non-Collapsing Detector Adequacy

An observer packet $\mathcal{O}$ is mathematically sound only if its detector protects declared distinctions against trivialization:

### 6.1 Trivialization Failure Modes
1. **Zero Observation Collapse:** An evaluation mapping that maps all states to the zero cochain ($p(s) \equiv 0$). This trivially produces $\Phi_1 = 0$ by blinding the detector to actual state differences.
2. **Coboundary Saturation (Surjective Repair Gauge):** A repair gauge whose image spans the entire cochain space:
   $$\operatorname{im}(d_0) = C^1 \implies Q^1 = C^1 / \operatorname{im}(d_0) = \{0\}$$
   When this occurs, every 1-cochain is an exact coboundary, forcing $\Phi_1 = 0$ identically for all inputs and rendering the detector incapable of registering any obstruction.

   *Concrete test (2026-10-20):* on a finite graph with $|V|$ vertices, $|E|$ edges and $c$ connected components, $\operatorname{rank}(d_0) = |V| - c$, because $\ker(d_0)$ consists of the functions that are constant on each component. So $\operatorname{im}(d_0) = C^1$ exactly when $|E| = |V| - c$, that is, when the graph is a forest (it has no cycle). Example: the path $0 \to 1 \to 2$ has $|V| = 3$, $|E| = 2$, $c = 1$, so every edge assignment is a potential difference and no obstruction can be seen. Adding the edge $2 \to 0$ makes $|E| = 3 > 2$ and $\dim Q^1 = 1$.

### 6.2 Countermodel Separation Requirement
Non-zero matrix rank alone is insufficient to verify that an observer is functioning. An admitted observer $\mathcal{O}$ must be accompanied by an explicit **Detector Adequacy Receipt** evaluated against a declared test suite containing both positive models and negative countermodels:

- **Positive Calibration Test ($s_+$):** An admitted valid state $s_+ \in \operatorname{Ob}(\mathcal{T}_n)$ for which $p(s_+) \in \operatorname{im}(d_0)$, producing $[p(s_+)] = [0]$ and $\Phi_1 = 0$ (yielding terminal certification $\tau(s_+) = \mathtt{Certified}$).
- **Negative Countermodel Test ($s_-$):** An admitted distinction witness $s_- \in \operatorname{Ob}(\mathcal{T}_n)$ for which $p(s_-) \notin \operatorname{im}(d_0)$, producing a verified non-zero quotient class $[p(s_-)] \ne [0]$ with $\Phi_1 > 0$ backed by an exact dual witness (`Refusal`).

An observer lacking verified separation across $(s_+, s_-)$ is unadmitted.
