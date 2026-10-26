---
documentation_contract: symbol-game-documentation/v1
title: 'Runtime Governance: Bounded Execution, Operational Cycle Breaking, and Authority Separation'
kind: governance-reference
audience:
- researchers
- runtime-engineers
- coding-agents
status: active
maturity: emerging
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - standing_dependent_type
    - godel_break_operational_policy
    - rbg_terminal_partition
  prose_theorems:
    - sufficient_guarantee_composite_bounded_execution
    - proposal_non_authority_type_isolation
  lean_theorems: []
  finite_computations: []
  declared_policies:
    - godel_break_on_ancestor_call_collision
    - rbg_master_horizon_routing
  applications:
    - proposal_fidelity_protocol_runtime
  open_conjectures: []
coefficient_domain: "None (Typed AST / Operational States)"
runtime_dependency: "Chapter 05 (Contexts, Observers, Contextual Distinguishability, and Detector Adequacy)"
governance_dependency: "governance-pfp"
---

# Runtime Governance: Bounded Execution, Operational Cycle Breaking, and Authority Separation

**Status:** Runtime Governance & Evaluator Architecture Protocol
**Context:** Operational realization of proposer/verifier separation, execution bounds, and cycle-breaking policies for the Symbol Game runtime.
**Authority:** None. Operational host policy.

---

## 1. Canonical Terminal Sum Type & Composite Bounded Execution

Let an evaluation pipeline $\Pi_S$ for task specification $S$ be composed of finitely many sequential stages:
$$\Pi_S(x, y) = \tau_S(V_S(x, E(D(y))))$$
where $D$ is decoding, $E$ is evaluation, $V_S$ is deterministic verification against task input $x$, and $\tau_S$ is terminalization.

### 1.1 The Canonical Terminal Sum Type $\mathbb{T}_S$
To prevent semantic ambiguity and inconsistent status strings across runtime engines, all terminal outputs inhabit a single canonical sum type. *(Source note, 2026-10-20: $\mathbb{T}_S$ is a teaching type; no enum with exactly these three constructors was found in source. The source terminal vocabularies are `RoutingTerminal` in [`omega_types/src/routing.rs`](../../../../omega_engine/crates_rs/omega_types/src/routing.rs), with seven values, and `CodaTerminal` in [`omega_state/src/coda_gtla_protocol.rs`](../../../../omega_engine/crates_rs/omega_state/src/coda_gtla_protocol.rs), with eight. A mapping from $\mathbb{T}_S$ to either is not declared in source and is proposed only; note that `BudgetExhausted` here corresponds to the routing value `BudgetUnknown`, which is a resource record and never an obstruction class.)*
$$\boxed{\mathbb{T}_S := \mathtt{Certified}(R_{\mathrm{cert}}) \;\big|\; \mathtt{Refusal}(R_{\mathrm{ref}}) \;\big|\; \mathtt{BudgetExhausted}(R_{\mathrm{bdg}})}$$

### 1.2 Theorem (Sufficient Bounded Execution Condition)
If every constituent stage $k \in \{D, E, V_S, \tau_S\}$ enforces a finite step budget $B_k < \infty$ and finite recursion depth limit $D_k < \infty$, then the composite pipeline terminates within a deterministic global step bound:
$$B_{\mathrm{total}} \le \sum_{k} B_k < \infty$$
yielding a typed terminal outcome:
$$\tau_S(s) \in \mathbb{T}_S$$

> **Claim Discipline Posture:**
> This theorem provides a *sufficient operational condition*: enforcing finite budgets at every constituent stage ensures termination of the composition. It does not assert that a system can terminate *only if* every component has a global uniform bound, nor does it make claims regarding general unbounded Turing computability or undecidability.

---

## 2. Operational Cycle Breaking: The Cycle Interruption Policy

When evaluating recursive AST structures or candidate self-referential definitions ($s = \phi(s)$), cyclic substitution dependencies can arise within computational graphs.

### 2.1 Cycle Detection Protocol via Dynamic Ancestor Stack
An append-only set of visited nodes incorrectly reports cycles on acyclic shared DAG subexpressions or repeated sibling evaluations. The cycle detector must therefore evaluate membership in the **current active ancestor stack**:

1. **Evaluation-State Key:** Each evaluation call is identified by a complete state key:
   $$\kappa = (u_{\mathrm{id}}, \mathrm{args}, \mathrm{env}, \mathrm{stage})$$
   combining canonical AST node structure/ID, evaluated arguments, lexical environment, and active stage/manifest. Recursive calls on strictly decreasing arguments with the same node template produce distinct state keys and must not be rejected.
2. **Dynamic Ancestor Stack ($\mathcal{S}_{\mathrm{ancestors}}$):**
   - On call entry: check if $\kappa \in \mathcal{S}_{\mathrm{ancestors}}$. If a hash collision is possible, verify structural equality of the state tuples.
   - If $\kappa \in \mathcal{S}_{\mathrm{ancestors}}$, an active ancestor collision is detected.
   - Otherwise, push $\kappa$ onto $\mathcal{S}_{\mathrm{ancestors}}$.
   - On call exit (normal return, budget halt, or unwound error): pop $\kappa$ from $\mathcal{S}_{\mathrm{ancestors}}$.
3. **Separate Completed/Memoization Table ($\mathcal{M}_{\mathrm{completed}}$):**
   Completed evaluations can be cached in a separate memoization table $\mathcal{M}_{\mathrm{completed}}$ to return finished values for shared DAG subexpressions without re-evaluating or triggering ancestor stack alerts.

### 2.2 Operational Action
Upon detecting an active ancestor collision, the runtime immediately terminates the recursion and emits a typed refusal inside the canonical terminal sum type:
$$\tau_S(s) = \mathtt{Refusal}(\mathtt{CycleDetected}(\kappa))$$
*(formerly designated as `GODEL_BREAK`).*

> **Validation Cases:**
> 1. Repeated sibling calls and shared DAG children succeed without cycle flags.
> 2. True ancestor-state recurrence (identical $\kappa$ in $\mathcal{S}_{\mathrm{ancestors}}$) is interrupted deterministically.
> 3. Well-founded recursion with decreasing arguments remains admissible within the step budget.
>
> **Epistemic Scope:**
> Cycle interruption is an operational host safety mechanism that halts recursive infinite loops. It does not establish Gödel's First or Second Incompleteness Theorems, nor does it establish non-vanishing sheaf cohomology. It is a finite graph cycle-interruption rule.

---

## 3. Proposal Non-Authority & Standing Dependent Types

### 3.1 Architectural Type Isolation
Let $\Gamma$ be the set of expressions generatable by an untrusted proposer $P_\theta$, and let $\mathbb{T}_S$ be the declared terminal alphabet of task specification $S$.
By architectural construction, the proposal grammar and the authority terminal type are strictly disjoint:
$$\Gamma \cap \mathbb{T}_S = \varnothing$$
Unchecked proposal tokens cannot inhabit the authority type.

### 3.2 Cleaned-Up Standing Dependent Type
Let the full verification pipeline map into the sum type of authority terminals and host runtime exceptions:
$$\Pi_S^\sharp : X \times \Gamma \longrightarrow \mathbb{T}_S + \mathcal{E}$$
defined by $\Pi_S^\sharp(x, y) := \tau_S(V_S(x, E(D(y))))$, where input task $x \in X$ is explicitly evaluated by verifier $V_S$.

The formal standing relation is parameterized explicitly over both input task $x \in X$ and candidate proposal $y \in \Gamma$:

$$\mathsf{Standing}_S(x, y) := \sum_{t \in \mathbb{T}_S} \left( \Pi_S^\sharp(x, y) = \mathsf{inl}(t) \wedge \mathsf{IsAuth}_S(t) \right)$$

A proposal $y$ acquires operational standing only when the independent verifier $V_S$ and terminalizer $\tau_S$ execute over $(x, y)$ and certify satisfaction of specification $S$.

---

## 4. The Red-Blue-Green (R-B-G) Master Horizon Governance Protocol

The R-B-G master horizon is an explicit deterministic projection of the canonical terminal sum type:

$$\operatorname{Color} : \mathbb{T}_S \longrightarrow \{\mathtt{GREEN}, \mathtt{RED}, \mathtt{BLUE}\}$$

1. **GREEN ($\mathtt{Certified}$):**
   $$\operatorname{Color}(\mathtt{Certified}(R_{\mathrm{cert}})) = \mathtt{GREEN}$$
   Exact zero-defect quotient class $[c] = [0]$ verified by deterministic check ($c \in \operatorname{im}(d_0)$).
2. **RED ($\mathtt{Refusal}$):**
   $$\operatorname{Color}(\mathtt{Refusal}(R_{\mathrm{ref}})) = \mathtt{RED}$$
   Explicit refusal, typed by root cause:
   - `Refusal(InvalidIntake)`: Malformed syntax, out-of-vocabulary tokens, or manifest hash mismatches.
   - `Refusal(CertifiedObstruction)`: Syntactically valid intake with a certified non-zero quotient obstruction class $[c] \ne [0]$ backed by an exact dual witness ($d_0^* w = 0$, $|w_e| \le \omega_e$ for every edge, $\langle w, c \rangle = \Phi_1([c]) > 0$). *(Capacity condition added 2026-10-20: without $|w_e| \le \omega_e$ any balanced $w$ could be scaled to make the pairing arbitrarily large, so the pairing would bound nothing.)*
   - `Refusal(CycleDetected)`: Active ancestor call collision in $\mathcal{S}_{\mathrm{ancestors}}$ halted by cycle interruption.
3. **BLUE ($\mathtt{BudgetExhausted}$):**
   $$\operatorname{Color}(\mathtt{BudgetExhausted}(R_{\mathrm{bdg}})) = \mathtt{BLUE}$$
   Execution budget exhausted under declared limits $(B_{\mathrm{step}}, B_{\mathrm{depth}})$; awaiting non-forced external context review.
