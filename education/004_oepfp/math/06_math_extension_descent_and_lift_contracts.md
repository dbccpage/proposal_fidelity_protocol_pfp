---
documentation_contract: symbol-game-documentation/v1
title: 'Chapter 06: Extension, Retraction, Partial Descent, and Lift Obligations'
kind: mathematical-reference
audience:
- researchers
- category-theorists
- compiler-engineers
- coding-agents
status: active
maturity: canonical
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - lift_contract_tuple
    - syntax_retraction_functor
    - partial_descent_operator
    - invariant_skeleton
    - naming_pressure_recurrence
    - four_phase_lift_lifecycle
  prose_theorems:
    - syntax_retraction_preservation
    - cohomological_non_retraction
    - invariant_skeleton_characterization
  lean_theorems: []
  finite_computations: []
  declared_policies:
    - external_authorization_gate
    - typed_refusal_for_orphan_terms
  applications: []
  open_conjectures: []
coefficient_domain: "Discrete Syntactic Categories / ℚ"
runtime_dependency: "Chapter 05 (Contexts, Observers, Contextual Distinguishability, and Detector Adequacy)"
governance_dependency: "governance-pfp"
---

# Chapter 06: Extension, Retraction, Partial Descent, and Lift Obligations

**Status:** Canonical Mathematics Specification (Spine Chapter 06)
**Authority:** None. Categorical extensions, conservative embeddings, and partial descent contracts.

---

## 1. The Four-Phase Lift Lifecycle: Not Inevitable Growth

An ontological lift is an auditable **contractual obligation**, not an automatic mathematical inevitability. An obstruction or contextual non-congruence does not spontaneously generate new vocabulary. The transition from stage $n$ to stage $n+1$ must strictly distinguish four stages:

```text
1. Lift Proposal:
   An untrusted candidate generator set and syntax extension proposed to resolve an obstruction.

2. Lift Witness:
   A verified contextual non-congruence witness w = (x, y, c) accompanied by an exact
   exhaustion certificate E proving all allowable same-level repairs in W_n were exhausted.

3. External Authorization:
   An independent administrative or human authority decision licensing the extension.
   (Proposals cannot self-authorize or self-inhabit authority types).

4. Accepted Extension:
   The frozen stage n+1 presentation satisfying the full lift contract Λ_n.
```

---

## 2. The Formal Lift Contract: $\Lambda_n$

An admitted extension must satisfy an auditable 7-tuple contract:

$$\Lambda_n = (w, E, m, F_n, U_n, I_n^\bullet, \pi)$$

| Component | Mathematical Role | Verification Condition |
| :--- | :--- | :--- |
| **$w$** | Context Witness | Certified non-congruence: $\exists c \in \mathcal{C}_n, \; x \sim_n y \;\wedge\; \rho(c)x \not\sim_n \rho(c)y$. |
| **$E$** | Exhaustion Certificate | Verified proof that all existing repair paths in $W_n = \operatorname{im}(d_{0,n})$ failed. |
| **$m$** | Minimality Witness | Verification that proposed $\mathsf{G}$ is inclusion-minimal (no proper subset resolves $w$) AND cardinality-minimal over declared universe $\mathcal{U}_n$, supported by a lower bound certificate against all smaller admitted candidate sets. |
| **$F_n$** | Extension Morphism | Conservative functor $F_n: \mathcal{T}_n \to \mathcal{T}_{n+1}$ embedding valid old syntax. |
| **$U_n$** | Syntax Retraction | Retraction functor on the image subcategory: $U_n: F_n(\mathcal{T}_n) \to \mathcal{T}_n$. |
| **$I_n^\bullet$** | Graded Cochain Map | Algebraic cochain map $I_n^k: C_n^k \to C_{n+1}^k$ satisfying $d_{n+1}^k I_n^k = I_n^{k+1} d_n^k$, commuting with evaluation. |
| **$\pi$** | Partial Descent | Partial map returning predecessor terms or emitting typed non-descent receipts. |

---

## 3. Conservative Syntax Embedding vs. Cohomological Non-Retraction

A sound lift must never rewrite historical facts: every valid term and certified receipt in $\mathcal{T}_n$ must remain valid when embedded into $\mathcal{T}_{n+1}$.

### 3.1 Strict Syntax Retraction
The upward functor $F_n: \mathcal{T}_n \to \mathcal{T}_{n+1}$ admits an exact retraction on the subcategory of old syntax:

$$\boxed{U_n \circ F_n = \mathrm{id}_{\mathcal{T}_n}}$$

Every old term $x \in \mathcal{T}_n$ is identically recovered: $U_n(F_n(x)) = x$.

### 3.2 Commuting Cochain Maps & Cohomological Non-Retraction
A bare linear inclusion of cochains does **not** automatically induce a forward map on cohomology. (For example, consider the inclusion of $0 \to \mathbb{Q} \to 0$ into $0 \to \mathbb{Q} \xrightarrow{\mathrm{id}} \mathbb{Q}$; sending degree 1 by identity maps the old cocycle $1$ to a non-cocycle, failing to define any forward cohomology map).

> **Forward Cohomology Invariant:**
> The forward cohomology map $[c] \mapsto [I_n^1 c]$ is well-defined when $I_n^\bullet$ is a graded **algebraic cochain map** commuting with differentials:
> $$d_{n+1}^k \circ I_n^k = I_n^{k+1} \circ d_n^k$$
> *Correction (2026-10-20):* an earlier version said "if and only if". The cochain-map condition is sufficient, not necessary. The exact requirement for $[c] \mapsto [I_n^1 c]$ to be well-defined on $H^1$ is that $I_n^1$ sends cocycles to cocycles, $I_n^1(\ker d_{1,n}) \subseteq \ker d_{1,n+1}$, and coboundaries to coboundaries, $I_n^1(\operatorname{im} d_{0,n}) \subseteq \operatorname{im} d_{0,n+1}$. A cochain map satisfies both: if $d_{1,n} c = 0$ then $d_{1,n+1} I^1 c = I^2 d_{1,n} c = 0$, and $I^1 d_{0,n}\alpha = d_{0,n+1} I^0 \alpha$.
> (In geometric subcomplex embeddings, ordinary cohomology naturally yields contravariant pullbacks in the opposite direction; forward persistence is conditional on this explicitly supplied algebraic cochain map $I_n^\bullet$).
>
> If $I_n^\bullet$ and a hypothetical downward map admitted a chain homotopy retraction $U_n^* \circ I_n^* = \mathrm{id}_{H^1_n}$, then $I_n^*: H^1_n \to H^1_{n+1}$ would be forced to be injective. That would mathematically prevent any non-zero obstruction class $[q] \in H^1_n$ from ever being resolved!
> In reality, an ontological lift adjoins new 0-cochains (new repair degrees of freedom in $C^0_{n+1}$), enlarging the coboundary image $\operatorname{im}(d_{0,n+1})$. Consequently, the forward map $I_n^*$ can have a non-trivial kernel: classes can die when resolved by newly admitted repairs.

---

## 4. Typing Discipline: Functorial Embedding vs. Partial Descent

To avoid breaking category axioms by defining functors into disconnected coproducts, downward operations are factored into two distinct mathematical entities:

### 4.1 Syntax Retraction Functor
The functor $U_n: F_n(\mathcal{T}_n) \to \mathcal{T}_n$ is defined strictly on the image subcategory of embedded terms, where it satisfies $U_n \circ F_n = \mathrm{id}_{\mathcal{T}_n}$.

### 4.2 The Partial Descent Operator
For arbitrary terms in $\mathcal{T}_{n+1}$ (which may include newly created vocabulary with no lower-level counterpart), descent is governed by the typed partial evaluation operator:

$$\operatorname{descend}_n : \operatorname{Ob}(\mathcal{T}_{n+1}) \longrightarrow \operatorname{Ob}(\mathcal{T}_n) \cup \mathcal{R}_n$$

defined explicitly by:

$$\operatorname{descend}_n(z) = \begin{cases}
x & \text{if } z = F_n(x) \text{ for some } x \in \operatorname{Ob}(\mathcal{T}_n) \\
\mathsf{Refusal}(\mathtt{NoLowerPreimage}, z) \in \mathcal{R}_n & \text{if } z \notin F_n(\operatorname{Ob}(\mathcal{T}_n))
\end{cases}$$

Terms created specifically at stage $n+1$ do not possess a phantom lower representation; they deterministically emit a typed refusal receipt $\mathsf{Refusal}(\mathtt{NoLowerPreimage}, z)$.

---

## 5. The Invariant Skeleton: $\operatorname{Skel}_n$

The invariant skeleton of stage $n$ is not defined by checking $U_n F_n(x) = x$ (which holds trivially on all old terms by syntax retraction).
Rather, a cohomology class $[q] \in H^1_n$ is an **invariant survivor** across the lift if its pushforward $I_n^*([q]) = [I_n^1(q)]$ remains un-repaired at stage $n+1$:

$$\boxed{\operatorname{Skel}_n = \{[q] \in H^1_n \setminus \{0\} : [I_n^1(q)] \neq [0] \in H^1_{n+1}\}}$$

- **Killed Obstructions ($[I_n^1(q)] = [0]$):** The defect was resolved at stage $n+1$ by new local repairs ($I_n^1(q) \in \operatorname{im}(d_{0,n+1})$).
- **Surviving Obstructions ($[I_n^1(q)] \neq [0]$):** The defect persists across the lift, representing a robust topological feature of the system.

---

## 6. Generator Accounting & Naming Pressure: $NP(n)$

Let $W_n$ be an admitted family of contextual non-congruence witnesses at stage $n$, evaluated over a declared candidate generator universe $\mathcal{U}_n$.

### 6.1 Inclusion-Minimality vs. Minimum Cardinality
A critical distinction must be maintained between local non-redundancy and global cardinality minimality:
1. **Inclusion-Minimality (Local Receipt):** A generator set $\mathsf{G} \subseteq \mathcal{U}_n$ is inclusion-minimal for $W_n$ if $\mathsf{G}$ resolves $W_n$, but no proper subset $\mathsf{G}' \subsetneq \mathsf{G}$ resolves $W_n$.
2. **Cardinality-Minimality (Global Optimum):** The joint constructor increment $\Delta(W_n)$ is the global minimum cardinality:
   $$\Delta(W_n) = \min \{ |\mathsf{G}| : \mathsf{G} \subseteq \mathcal{U}_n \text{ resolves } W_n \}$$
   If no candidate set in $\mathcal{U}_n$ resolves $W_n$, the operator emits $\mathsf{Refusal}(\mathtt{NoResolvingGeneratorSet})$ rather than taking the minimum of an empty family.

> **Minimality Counterexample:**
> Suppose candidate universe $\mathcal{U}_n = \{a, b, c\}$. Suppose either the pair $\{a, b\}$ or the singleton $\{c\}$ resolves $W_n$, but neither $\{a\}$ nor $\{b\}$ alone does. Then $\{a, b\}$ passes the inclusion-minimality test, but its cardinality is $2$, whereas the true minimum cardinality is $\Delta(W_n) = 1$.
> Reporting $\Delta(W_n) = |\mathsf{G}|$ therefore requires two distinct audit receipts:
> - An **Inclusion-Minimality Receipt** for $\mathsf{G}$, and
> - A **Lower-Bound Certificate** proving that all candidate subsets $\mathsf{G}' \subseteq \mathcal{U}_n$ with $|\mathsf{G}'| < |\mathsf{G}|$ fail the resolution predicate.

### 6.2 Subadditivity and Naming Pressure Recurrence
When resolution is monotonic under set enlargement (adding admitted generators does not destroy resolution of already-resolved witnesses) and the union $\bigcup_{w \in W_n} \mathsf{G}_w$ belongs to $\mathcal{U}_n$, constructor increment is subadditive:
$$\Delta(W_n) \le \sum_{w \in W_n} \Delta(\{w\})$$

This also needs the resolution predicate to be witness-wise: a set $\mathsf{G}$ resolves $W_n$ exactly when it resolves each $\{w\}$. Then pick a minimum set $\mathsf{G}_w$ for each $w$. The union $\bigcup_w \mathsf{G}_w$ resolves every $w$ by monotonicity, hence resolves $W_n$, and $|\bigcup_w \mathsf{G}_w| \le \sum_w |\mathsf{G}_w| = \sum_w \Delta(\{w\})$. In the Section 6.1 counterexample with $W_n = \{w\}$ the bound is an equality, $1 \le 1$.

The **Naming Pressure** recurrence is:

$$\boxed{NP(n+1) = NP(n) + \Delta(W_n)}$$

*(Under Chapter 00 discipline, this metric is denoted strictly by $NP(n)$ and is never conflated with Genesis $S(n)$).*

### 6.3 Canonical Width-Two Free Tower Segment
When each step in a free tower adjoins an independent directed distinction requiring two distinct new endpoints:
$$\Delta(W_n) = 2 \implies NP(n+1) = NP(n) + 2$$
where each level admits exactly two new generators $\{2n, 2n+1\}$.

> **Claim Hygiene Note:** $NP(n)$ is generator accounting for declared, bounded tower segments under explicit resolution rules. It does not constitute an unrestricted complexity measure of all possible computational systems.
