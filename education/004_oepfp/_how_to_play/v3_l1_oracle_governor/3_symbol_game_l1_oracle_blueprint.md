---
title: "Architectural Blueprint: The Symbol Game as an L1 Oracle Governor vs. L2 Softmax Parrot"
document_id: "CODA-TOWER-M3-R3-SG-L1-BLUEPRINT"
document_class: "Technical Architecture Blueprint & Systems Specification"
version: "1.0.0"
date: "2026-09-04"
status: "Specification & Architectural Contract"
author: "Teamwork Systems Architecture & Formal Verification Group"
milestone: "Milestone 3 (R3)"
authority_effect: "None"
---

# Architectural Blueprint: The Symbol Game as an $L_1$ Oracle Governor vs. $L_2$ Softmax Parrot

## Authority Notice

`AuthorityEffect: None.`
This document specifies an apparatus and architectural contract for discrete reasoning governance over language models within the CODA living planning framework. It does not certify physical continuum limits, does not assert empirical quantum chromodynamic (QCD) proofs, and does not alter sealed derivation artifacts. All formal properties declared herein hold strictly under the stated discrete relational and algebraic assumptions.

---

## 1. Executive Architectural Overview

### 1.1 The Continuous-Discrete Impedance Mismatch

Modern autoregressive large language models (LLMs) based on the Transformer architecture generate token sequences through continuous latent representations and normalized exponential distributions (the softmax operator). The finite vector example below demonstrates that opposite coordinates can cancel under continuous mixing. It does not establish that arbitrary transformer activations encode propositions on those coordinates or that every logical error is hidden this way.

In the declared finite edge-difference model, a nonzero residual contributes its absolute value to the $L_1$ defect. By contrast, the illustrative continuous-vector encoding permits:

1. Attention weights form a continuous probability simplex ($L_2$ normalized inner products mapped via softmax).
2. Latent representations of conflicting statements can form convex combinations that cancel opposing vector components.
3. The resulting blended vector is decoded into fluent, plausible-sounding connective prose that conceals the underlying logical defect.

This failure mode is termed **Cancellation Laundering**.

```
+----------------------------------------------------------------------------------------------------+
|                               THE DUAL-SPACE GOVERNANCE ARCHITECTURE                               |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|   CONTINUOUS HEURISTIC PROPOSER (LLM)                  DISCRETE ORACLE GOVERNOR (HOST)             |
|   (Unconstrained Latent Space B_continuous)           (Algebraic State Space A_discrete)           |
|                                                                                                    |
|   +---------------------------------------+            +---------------------------------------+   |
|   | Transformer Layers                    |            | Context Specification C               |   |
|   | - Query, Key, Value Projections       |            | - Pinned Carrier V_C (Unicode Codepoints)  |
|   | - Continuous Attention: A = softmax(S)|            | - Declared Rule Set T                 |   |
|   | - Latent Mixing: Z = sum A_ij V_j     |            | - Relational Signatures R_C           |   |
|   +---------------------------------------+            +---------------------------------------+   |
|                       |                                                    |                       |
|                       v [Proposal Stream]                                  v                       |
|   +---------------------------------------+            +---------------------------------------+   |
|   | JSON Output Envelope ($TAU_SG_V1)     |            | Defect Register (Phi_1 Cochain)       |   |
|   | - Move Type: ASSERT | CUT | VERIFY    | ---------> | - Active Boundary Defects             |   |
|   | - Redex Key: (position, rule_id)      |            | - L1 Defect Norm: ||Phi_1||_{L1}      |   |
|   | - Expected Defect Delta Delta_Phi     |            +---------------------------------------+   |
|   +---------------------------------------+                                |                       |
|                                                                            v                       |
|                                                        +---------------------------------------+   |
|                                                        | Idempotent Projection P_S             |   |
|                                                        | - Host Replay & Step Verification     |   |
|                                                        | - Monotonic Descent Check:            |   |
|                                                        |   ||Phi_1(s_{t+1})|| <= ||Phi_1(s_t)||  |
|                                                        | - Non-Leakage / Pareto Gate           |   |
|                                                        +---------------------------------------+   |
|                                                                            |                       |
|                                                        +-------------------+-------------------+   |
|                                                        | Admitted                              | Refused
|                                                        v                                       v   |
|                                        +-------------------------------+       +---------------+   |
|                                        | Commit to Derivation History  |       | Emit Refusal  |   |
|                                        | - Content-Addressed DAG (DDA) |       | - Trigger     |   |
|                                        | - Advance State s_t -> s_{t+1}|       |   RETRACT     |   |
|                                        +-------------------------------+       +---------------+   |
+----------------------------------------------------------------------------------------------------+
```

### 1.2 The Dual-Space Architecture

To establish deductive integrity without attempting the intractable task of modifying frozen neural network weights via prompt text, we define a dual-space architecture that partitions the system into two distinct operational components:

1. **The Heuristic Proposer ($\mathcal{B}_{\text{continuous}}$):** The autoregressive LLM, prompted through a strict carrier and move contract, acts solely as a high-entropy proposal generator. It proposes candidate derivation steps, redex identifications, and relational cuts. It possesses zero verification authority; its internal self-assessments (such as asserting `"verified": true`) are treated by the host as unverified proposals.
2. **The Discrete Oracle Governor ($\mathcal{A}_{\text{discrete}}$):** An external, deterministic host state machine operating as an $L_1$ projection governor ($\mathcal{P}_S$). The governor maintains a discrete relational store, records unresolved verification obligations as an algebraic boundary cochain $\Phi_1$, recomputes supported moves against deterministic rules, and enforces monotonic non-increase of the declared $L_1$ defect norm $\|\Phi_1\|_{L_1}$.

---

## 2. The $L_2$ Softmax Parrot Failure Mode

### 2.1 Mathematical Formulation of Continuous Softmax Attention

In standard transformer architectures (Vaswani et al., 2017), the core sequence mixing mechanism is multi-head self-attention operating over continuous latent representations. Let $X \in \mathbb{R}^{T \times d}$ denote the sequence of $T$ token representations in the residual stream at hidden dimension $d$. For an attention head with projection matrices $W_Q, W_K, W_V \in \mathbb{R}^{d \times d_k}$, the query, key, and value matrices are:
$$Q = X W_Q, \quad K = X W_K, \quad V = X W_V$$

The unnormalized attention score matrix $S \in \mathbb{R}^{T \times T}$ is computed via scaled inner products with a causal mask $M \in \{0, -\infty\}^{T \times T}$:
$$S_{i, j} = \frac{Q_i K_j^T}{\sqrt{d_k}} + M_{i, j}$$

The attention weight matrix $A \in \mathbb{R}^{T \times T}$ is obtained by applying the row-wise softmax operator:
$$A_{i, j} = \operatorname{softmax}(S_{i, :})_j = \frac{\exp(S_{i, j})}{\sum_{m=1}^T \exp(S_{i, m})}$$

The output of the attention head at sequence position $i$ is the linear combination of value vectors:
$$Z_i = \sum_{j=1}^T A_{i, j} V_j$$

At the terminal generation layer, a linear unembedding matrix $W_U \in \mathbb{R}^{d \times |V|}$ maps the final residual state $h_T \in \mathbb{R}^d$ to logit vector $z \in \mathbb{R}^{|V|}$ over vocabulary $V$. The predictive distribution over next tokens is given by:
$$p_k = \frac{\exp(z_k / T_{\text{temp}})}{\sum_{m=1}^{|V|} \exp(z_m / T_{\text{temp}})}$$

#### Proposition 2.1 (Strict Positivity and Simplex Interior Confinement)

*Let $z \in \mathbb{R}^{|V|}$ be any finite real logit vector produced by a transformer network, and let $T_{\text{temp}} \in (0, \infty)$. Then for all vocabulary tokens $k \in \{1, \dots, |V|\}$,*
$$0 < p_k < 1 \quad \text{and} \quad \sum_{k=1}^{|V|} p_k = 1$$

*Proof.* For every $k \in \{1, \dots, |V|\}$, because $z_k$ is finite and $T_{\text{temp}} > 0$, the exponential $\exp(z_k / T_{\text{temp}})$ is strictly positive and finite: $0 < \exp(z_k / T_{\text{temp}}) < \infty$. The denominator $\sum_{m=1}^{|V|} \exp(z_m / T_{\text{temp}})$ is a finite sum of strictly positive terms. Because $|V| \ge 2$, the denominator is strictly greater than any individual numerator term:
$$\sum_{m=1}^{|V|} \exp(z_m / T_{\text{temp}}) > \exp(z_k / T_{\text{temp}}) > 0$$
Dividing numerator by denominator yields $0 < p_k < 1$. The sum equals $1$ by construction. Thus, the output distribution $p$ lies strictly in the relative interior of the standard probability simplex: $p \in \operatorname{relint}(\Delta^{|V|-1})$. $\blacksquare$

#### Corollary 2.1.1 (Impossibility of Prompt-Induced Discrete Step Collapse)

No sequence of natural language prompt tokens can collapse the continuous softmax operator into an exact discrete Kronecker delta indicator function ($\delta_{k, k^*} \in \{0, 1\}$) over finite real logits. An unconstrained transformer always assigns non-zero probability mass to alternative continuations.

### 2.2 The Mechanism of Cancellation Laundering

In a deductive calculus, two propositions $P_1$ and $P_2$ that assert contradictory relations (such as $P_1: a \mathrel{R} b$ and $P_2: \neg(a \mathrel{R} b)$) create a boundary obstruction:
$$P_1 \wedge P_2 \vdash \bot$$

In an autoregressive transformer, the following sequential failure occurs:

```
+-------------------------------------------------------------------------+
|                  CANCELLATION LAUNDERING IN ATTENTION                   |
|                                                                         |
|  Context Token: Premise P1 --------> Value Vector V_1                   |
|                                          \                              |
|                                           \   Convex Combination        |
|                                            +-> Z_i = a_1 V_1 + a_2 V_2  |
|                                           /    (Opposing components     |
|                                          /      cancel vectorially)     |
|  Context Token: Premise P2 --------> Value Vector V_2                   |
|                                                         |               |
|                                                         v               |
|                                               Blended Latent Vector     |
|                                               z_mixed in null-space     |
|                                                         |               |
|                                                         v               |
|                                               Unembedding W_U           |
|                                                         |               |
|                                                         v               |
|                                               High-Probability Output:  |
|                                               "Therefore, in general..."|
|                                               (Grammatically fluent;    |
|                                                deductive defect hidden) |
+-------------------------------------------------------------------------+
```

1. **Convex Latent Blending:** When the model attends to both $P_1$ and $P_2$, the attention layer computes a convex combination of value vectors:
   $$Z_i = A_{i, P_1} V_{P_1} + A_{i, P_2} V_{P_2} + \sum_{j \notin \{P_1, P_2\}} A_{i, j} V_j$$
   where $A_{i, P_1}, A_{i, P_2} \in (0, 1)$.
2. **Euclidean Vector Cancellation:** Because latent spaces $\mathbb{R}^d$ are optimized under Euclidean ($L_2$) inner products, semantic opposition is frequently embedded as antipodal or negative directional correlation along specific feature subspaces ($V_{P_1} \approx - V_{P_2}$ along the relevant predicate direction). When weighted by similar attention coefficients ($A_{i, P_1} \approx A_{i, P_2}$), the opposing components cancel out in vector addition:
   $$A_{i, P_1} V_{P_1} + A_{i, P_2} V_{P_2} \approx \mathbf{0}$$
3. **Spurious Continuation Generation:** Rather than signaling an irreconcilable boundary obstruction, the resulting latent state $Z_i$ lands in a generic intermediate region of representation space. The subsequent feed-forward layers and unembedding matrix $W_U$ map this attenuated state onto high-frequency connective tokens (such as *"However"*, *"Furthermore"*, *"In balance"*, or *"Therefore"*), synthesizing fluent prose that silently circumvents the contradiction.
4. **Formal Definition:**
   > **Cancellation Laundering:** *The mathematical process whereby a continuous attention mechanism conceals a discrete logical contradiction by convexly blending opposing latent vectors, producing an output sequence that satisfies statistical token fluency while silently violating formal relational consistency.*

### 2.3 Smooth Loss Aggregation and Fluency Masking

During training and generation, the loss function aggregates cross-entropy over all sequence tokens:
$$\mathcal{L}_{\text{seq}} = -\frac{1}{T} \sum_{t=1}^T \log p(y_t \mid y_{<t})$$

If a sequence contains $T = 500$ tokens where a single deduction step at $t = 120$ introduces a catastrophic logical error (e.g., asserting an invalid transitive link), the negative log-likelihood of that specific token might contribute a local loss penalty of $\Delta \mathcal{L} \approx 4.5$. However, the surrounding $499$ tokens of highly predictable grammar, boilerplate reasoning phrases, and syntactic scaffolding contribute small losses ($\approx 0.1$).

The average loss over the sequence remains low ($\approx 0.11$), and an $L_2$ or cross-entropy evaluator classifies the sequence as high-quality. Smooth loss aggregation masks discrete local failures.

---

## 3. The $L_1$ Oracle Governor

### 3.1 The External Discrete Symbol Game as an $L_1$ Projection Governor

To eliminate cancellation laundering, verification authority is externalized to a discrete state machine: the **Symbol Game Governor** $\mathcal{S}$.

Let $\mathcal{B}_{\text{continuous}}$ represent the space of unconstrained token sequences emitted by the continuous model, and let $\mathcal{A}_{\text{discrete}}$ represent the space of verified, well-formed relational presentations over a declared finite carrier.

The governor operates as a projection operator:
$$\mathcal{P}_S : \mathcal{B}_{\text{continuous}} \to \mathcal{A}_{\text{discrete}} \cup \{\operatorname{Refused}\}$$
satisfying the projection identity on all admitted configurations:
$$\mathcal{P}_S \circ \mathcal{P}_S = \mathcal{P}_S$$

#### Proposition 3.1 (Idempotence and Non-Drift)

*Let $x \in \mathcal{A}_{\text{discrete}}$ be an admitted symbolic state. Then $\mathcal{P}_S(x) = x$. Repeated validation passes introduce zero semantic drift.*

*Proof.* By construction, $\mathcal{A}_{\text{discrete}} = \operatorname{im}(\mathcal{P}_S)$. An element $x \in \mathcal{A}_{\text{discrete}}$ satisfies all declared syntactic, structural, and relational invariants of the governor context $\mathcal{C}$. Applying $\mathcal{P}_S$ to $x$ re-evaluates the invariant predicates against the identical static rule set $\mathcal{T}$. Because the evaluation is a deterministic function without side effects, every invariant check passes, and $x$ is returned unchanged. Thus, $\mathcal{P}_S(\mathcal{P}_S(x)) = \mathcal{P}_S(x)$. $\blacksquare$

#### Decoding Logit Masking vs. True Verification

It is vital to distinguish between two mechanisms often conflated in literature:

1. **Local Logit Masking (Carrier Projection):** Setting non-carrier token logits to $-\infty$ prior to softmax:
   $$(P_{\text{mask}} z)_k = \begin{cases} z_k & \text{if token } k \in \mathcal{V}_{\text{allowed}} \\ -\infty & \text{otherwise} \end{cases}$$
   This acts as a projection on token syntax, ensuring the emitted string belongs to the regular grammar $\mathcal{V}_{\text{allowed}}^*$.
2. **Host-Side Oracle Verification:** Logit masking enforces syntactic support constraints, but provides no assurance of semantic truth. A model with constrained decoding can emit syntactically valid falsehoods. True governance requires host-side recomputation of derivation steps, where producer claims are verified by independent replay.

### 3.2 Boundary Obstruction Cochains and the $L_1$ Defect Norm

We model reasoning state verification in analogy with algebraic topology and simplicial cochain complexes. Let $G = (V, E)$ be a finite relational graph representing entities and relations.

```
       C_1 (1-Chains: Relations/Cuts)  --------\partial_1------->  C_0 (0-Chains: Vertices/Marks)
                     |                                                           |
                     |  Stokes Nilpotence: \partial_0 \circ \partial_1 = 0       |
                     v                                                           v
       C^1 (1-Cochains: Edge Defects)  <-------d_0 (Coboundary)---  C^0 (0-Cochains: Potentials)
```

Let $Q_C = \{q_1, q_2, \dots, q_m\}$ be a finite set of declared verification obligations for context $C$. For a candidate presentation $x$, the host evaluation map is:
$$\operatorname{check}_C : Q_C \times X_C \to \{\operatorname{Pass}\} \cup \{\operatorname{Fail}(w) : w \in \mathcal{W}\} \cup \{\operatorname{Unknown}(r) : r \in \mathcal{R}\}$$

The **Defect Register** (primary obstruction cochain) $\Phi_1(x)$ is the formal sum of witnessed failures:
$$\Phi_1(x) = \sum_{i : \operatorname{check}_C(q_i, x) = \operatorname{Fail}(w_i)} w_i \cdot q_i^*$$
where $q_i^*$ is the dual basis element corresponding to obligation $q_i$, and $w_i \in \mathbb{N}_{\ge 1}$ is the integer defect weight.

We define the **$L_1$ Defect Norm** as the sum of defect magnitudes:
$$\|\Phi_1(x)\|_{L_1} = \sum_{i=1}^m |w_i| \cdot \mathbf{1}[\operatorname{check}_C(q_i, x) = \operatorname{Fail}(w_i)]$$

#### Contrast: $L_1$ Discrete Metric vs. $L_2$ Continuous Loss

- **$L_2$ Loss Geometry ($\sqrt{\sum e_i^2}$):** In an $L_2$ metric space, error coordinates are coupled via spherical level sets. An increase in error on obligation $q_1$ from $0$ to $\epsilon$ can be compensated by a small decrease on obligation $q_2$, maintaining an equal or lower norm. This geometric property enables cancellation laundering.
- **$L_1$ Defect Geometry ($\sum |d_i|$):** In the discrete $L_1$ metric space, error coordinates are strictly orthogonal and separable. The level sets are cross-polytopes (hyper-octahedra). A defect on obligation $q_1$ contributes an independent, non-zero integer mass $|w_1| \ge 1$. It cannot be mitigated, cancelled, or hidden by progress on $q_2$.

### 3.3 Strict Monotonic Descent Requirement

Every valid deductive transition $\tau : s_t \to s_{t+1}$ evaluated by the governor must satisfy the following criteria:

1. **Weak Descent:**
   $$\|\Phi_1(s_{t+1})\|_{L_1} \le \|\Phi_1(s_t)\|_{L_1}$$
2. **Defect-Targeted Descent:** When a step purports to resolve a specific defect $q_{\text{target}} \in \operatorname{supp}(\Phi_1(s_t))$, the step must achieve strict decrease on that defect:
   $$\operatorname{check}_C(q_{\text{target}}, s_{t+1}) = \operatorname{Pass}$$
   yielding $\|\Phi_1(s_{t+1})\|_{L_1} < \|\Phi_1(s_t)\|_{L_1}$.
3. **Invariance of Protected Boundary Conditions (No Defect Leakage):**
   $$\operatorname{supp}(\Phi_1(s_{t+1})) \subseteq \operatorname{supp}(\Phi_1(s_t)) \setminus \{q_{\text{target}}\}$$
   No obligation that previously evaluated to $\operatorname{Pass}$ may transition to $\operatorname{Fail}$. If resolving $q_{\text{target}}$ introduces a new defect $q_{\text{new}}$, the transition violates the Pareto boundary condition and is immediately refused.
4. **Idempotent Stationary Transitions:** Steps that do not target defect resolution (such as structural equivalence adjustments modulo $\operatorname{Aut}$) must maintain exact invariant equality:
   $$\|\Phi_1(s_{t+1})\|_{L_1} = \|\Phi_1(s_t)\|_{L_1} \quad \text{and} \quad \operatorname{supp}(\Phi_1(s_{t+1})) = \operatorname{supp}(\Phi_1(s_t))$$

### 3.4 The Domain-of-Quantification Rule

A primary vector for subtle reasoning corruption in language models is ungrounded exhaustive quantification over all domain elements (claiming *"for all elements $x$, property $P(x)$ holds"* by checking only a selective, hallucinated subset of elements).

To ensure formal soundness, the governor enforces the **Domain-of-Quantification Rule**:
> **Domain-of-Quantification Rule:** *The governor must never evaluate an all-quantified ($\forall$) condition over a domain supplied or filtered by the claimant LLM. The governor must independently construct the domain of quantification directly from its verified relational store $\mathcal{R}_{\text{active}}$ and execute exhaustive bounded iteration over every member. Candidate domain lists provided in model output envelopes are admitted only as unverified advisory proposals and are discarded during host recomputation.*

---

## 4. Prompt Harness & State Machine Schema

### 4.1 State Machine Formal Schema

The external Symbol Game Governor operates as a discrete transition system:
$$\mathcal{M} = (\mathcal{S}, \Sigma_{\text{moves}}, \to, \mathcal{S}_0, \mathcal{S}_{\text{accept}}, \mathcal{S}_{\text{refuse}})$$

#### The 5-Tuple State Representation

A state $S \in \mathcal{S}$ is defined as a 5-tuple:
$$S = (\mathcal{C}, \mathcal{R}_{\text{active}}, \mathcal{D}_{\text{register}}, \mathcal{H}_{\text{trace}}, \mathcal{I}_{\text{invariants}})$$

1. **Context Specification $\mathcal{C}$:**
   - `carrier_symbols`: A finite set of admitted symbol tokens $V_C = \{s_1, \dots, s_n\}$, each bound to an exact Unicode codepoint (e.g., `U+0061` for `a`).
   - `carrier_digest`: SHA-256 digest of the canonical carrier bytes. When the host pins and compares it across turns, a mismatch detects carrier drift; the digest alone does not make producer-supplied state immutable.
   - `relation_signatures`: Declared predicate arities and typed domains (e.g., $\operatorname{edge} \subseteq V_C \times V_C$).
   - `licensed_rules`: Finite set of rewrite and inference rules $\mathcal{T} = \{r_1, \dots, r_k\}$.
2. **Active Relations $\mathcal{R}_{\text{active}}$:**
   - The set of currently active, verified ground relational tuples (e.g., $\{\operatorname{edge}(a, b), \operatorname{edge}(b, c)\}$).
3. **Defect Register $\mathcal{D}_{\text{register}}$:**
   - A mapping from declared obligations to their three-valued verification status:
     $$\mathcal{D}_{\text{register}} : Q_C \to \{\operatorname{Pass}\} \cup \{\operatorname{Fail}(w)\} \cup \{\operatorname{Unknown}(r)\}$$
   - Encodes the primary obstruction cochain $\Phi_1$.
4. **Derivation History $\mathcal{H}_{\text{trace}}$ (Proof-Relevant DDA Ledger):**
   - An append-only, content-addressed sequence of execution steps:
     $$e_t = \langle \operatorname{step\_id}, \operatorname{parent\_id}, \operatorname{move\_type}, \operatorname{rule\_id}, \operatorname{redex\_pos}, \operatorname{payload}, \Delta \Phi_1, \operatorname{step\_digest} \rangle$$
   - Keyed by exact redex position $(p, \rho)$ rather than rule name $\rho$ alone, ensuring total determinism.
5. **Protected Invariants $\mathcal{I}_{\text{invariants}}$:**
   - Closed set of integrity predicates that must hold globally across all transitions (e.g., irreflexivity: $\forall x, \neg \operatorname{edge}(x, x)$; acyclicity; arity bounds).

### 4.2 Vocabulary of Admissible Moves

Transitions in the state machine are restricted to a closed alphabet of four core operations:

| Move | Formal Signature | Preconditions | State Transformation | Post-Condition Check |
|---|---|---|---|---|
| **`ASSERT`** | $\operatorname{Assert}(p, \text{evidence\_id})$ | $p$ is well-formed over $V_C$; $\text{evidence\_id}$ resolves in trusted premise store. | $\mathcal{R}_{\text{active}} \gets \mathcal{R}_{\text{active}} \cup \{p\}$ | Verify no invariant in $\mathcal{I}$ is broken; recompute $\mathcal{D}_{\text{register}}$. |
| **`CUT`** | $\operatorname{Cut}(r, p, q_{\text{target}})$ | Rule $r \in \mathcal{T}$ matches redex at position $p$ in $\mathcal{R}_{\text{active}}$; $q_{\text{target}} \in \operatorname{supp}(\Phi_1)$. | $\mathcal{R}_{\text{active}} \gets (\mathcal{R}_{\text{active}} \setminus \operatorname{redex}) \cup \operatorname{apply}(r, \operatorname{redex})$ | Strict monotonic descent: $\|\Phi_1(S_{t+1})\|_{L_1} < \|\Phi_1(S_t)\|_{L_1}$; zero new defects. |
| **`VERIFY`** | $\operatorname{Verify}(q_i)$ | Obligation $q_i \in Q_C$. | Host executes mechanical verification check $\operatorname{check}_C(q_i, \mathcal{R}_{\text{active}})$. | Updates $\mathcal{D}_{\text{register}}[q_i]$ with host-computed status. |
| **`RETRACT`** | $\operatorname{Retract}(\operatorname{step\_id}, \text{reason})$ | Target step exists in $\mathcal{H}_{\text{trace}}$. | Reverts state to snapshot prior to $\operatorname{step\_id}$; marks subtree as failed path. | Restores ancestor state; increments exhaustion branch counter. |

### 4.3 Structural Exhaustion and Backtracking Protocols

When a proposed reasoning branch encounters a state where no licensed rule can reduce $\|\Phi_1\|_{L_1}$ without violating an invariant, the system has reached a local dead-end. The governor manages this state through an explicit backtracking protocol:

```
                          +-------------------------------+
                          |     Active Defect Present     |
                          |      ||Phi_1||_{L1} > 0       |
                          +-------------------------------+
                                          |
                                          v
                          +-------------------------------+
                          | LLM Proposes Next Move (TAU)  |
                          +-------------------------------+
                                          |
                                          v
                          +-------------------------------+
                          | Host Verification Gate (P_S)  |
                          | - Redex Check at (p, rho)     |
                          | - Monotonic Descent Check     |
                          | - Invariant Preservation      |
                          +-------------------------------+
                                          |
                      +-------------------+-------------------+
                      | Move Valid                            | Invalid / Increase
                      v                                       v
        +---------------------------+           +---------------------------+
        | Commit Step to H_trace    |           | Refuse Move (FW-REPLAY)   |
        | State Advances s_t->s_t+1 |           | Retract to Parent State   |
        +---------------------------+           +---------------------------+
                      |                                       |
                      v                                       v
        +---------------------------+           +---------------------------+
        | Is ||Phi_1||_{L1} == 0 ?  |           | Are Candidates Remaining? |
        +---------------------------+           +---------------------------+
               |             |                                |             |
           Yes |          No |                            Yes |          No |
               v             v                                v             v
        +-------------+ +-----------+                  +-------------+ +-------------+
        | State       | | Continue  |                  | Try Next    | | Issue R1    |
        | ACCEPTED    | | Deduction |                  | Candidate   | | Exhaustion  |
        +-------------+ +-----------+                  | Branch      | | Certificate |
                                                       +-------------+ +-------------+
                                                                              |
                                                                              v
                                                                       +-------------+
                                                                       | R2 License  |
                                                                       | Gate        |
                                                                       +-------------+
```

#### Priority Law: Rule 1 (Repair) vs. Rule 2 (Extension)

The governor enforces strict operational priority between same-context repair and context enlargement:

- **Rule 1 (R1 - Same-Context Repair):** The governor requires all reasoning attempts to resolve active defects within the declared context $\mathcal{C}$ using licensed repair rules.
- **Rule 2 (R2 - Context Augmentation):** Context enlargement (adding carrier elements, attaching higher simplex cells $\Delta^k$, or introducing external axioms) is prohibited until an **R1 Structural Exhaustion Certificate** is produced.
- **Priority Law 3 ("Failure to find a repair is not exhaustion"):** The model cannot request context extension solely because its search heuristic failed. An R1 structural exhaustion certificate requires explicit host-recomputed verification that every path in the forward reachability graph $\operatorname{Reach}_C(S_0)$ terminates in a dead-end.

### 4.4 Concrete Prompt Harness & JSON Schema ($TAU_SG_V1$)

To operate an LLM under this governor, the interaction harness provides five explicit surfaces on every turn, and constrains the output using JSON Schema:

#### Interaction Turn Prompt Structure

```markdown
[SYSTEM: GOVERNOR CONTRACT]
AuthorityEffect: None.
Role: Relational Transition Proposer.
Output Format: Strict JSON conforming to Schema $TAU_SG_V1.
Verification: The host oracle recomputes every redex application. Unbacked claims are refused.

[K: CARRIER SPECIFICATION]
CarrierID: C_FINITE_TRIANGLE_01
CarrierDigest: SHA256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Members: [
  {"symbol": "a", "codepoint": "U+0061"},
  {"symbol": "b", "codepoint": "U+0062"},
  {"symbol": "c", "codepoint": "U+0063"}
]

[ACTIVE RELATIONAL STATE]
Current State ID: step_003
Verified Relations: [
  {"id": "r1", "pred": "edge", "args": ["a", "b"]},
  {"id": "r2", "pred": "edge", "args": ["b", "c"]}
]

[DEFECT REGISTER]
Active Defects (Norm = 1): [
  {
    "obligation_id": "q_transitive_closure",
    "status": "Fail",
    "witness": "missing_edge(a, c)",
    "target_defect_id": "defect_001",
    "weight": 1
  }
]

[ALLOWED MOVES]
1. CUT: rule_transitive_cut(edge(X, Y), edge(Y, Z)) -> edge(X, Z)
2. RETRACT: step_id
```

#### JSON Output Schema ($TAU_SG_V1$)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TauSymbolGameMoveProposal_V1",
  "type": "object",
  "required": [
    "step_id",
    "parent_step_id",
    "move_type",
    "move_parameters",
    "expected_defect_delta"
  ],
  "additionalProperties": false,
  "properties": {
    "step_id": {
      "type": "string",
      "pattern": "^step_[0-9]{3,6}$"
    },
    "parent_step_id": {
      "type": "string",
      "pattern": "^step_[0-9]{3,6}$"
    },
    "move_type": {
      "type": "string",
      "enum": ["ASSERT", "CUT", "VERIFY", "RETRACT"]
    },
    "move_parameters": {
      "type": "object",
      "required": ["rule_id", "redex_position", "input_relation_ids", "produced_relation"],
      "additionalProperties": false,
      "properties": {
        "rule_id": {"type": "string"},
        "redex_position": {
          "type": "integer",
          "minimum": 0,
          "description": "Exact 0-indexed position of matching redex to guarantee deterministic application."
        },
        "input_relation_ids": {
          "type": "array",
          "items": {"type": "string"}
        },
        "produced_relation": {
          "type": "object",
          "required": ["pred", "args"],
          "additionalProperties": false,
          "properties": {
            "pred": {"type": "string"},
            "args": {
              "type": "array",
              "items": {"type": "string"}
            }
          }
        }
      }
    },
    "expected_defect_delta": {
      "type": "object",
      "required": ["target_defect_id", "projected_norm"],
      "additionalProperties": false,
      "properties": {
        "target_defect_id": {"type": "string"},
        "projected_norm": {
          "type": "integer",
          "minimum": 0
        }
      }
    }
  }
}
```

### 4.5 The Seven-Code Refusal Taxonomy

When a proposed step fails verification, the governor emits a typed refusal record. The refusal taxonomy is partitioned by host enforcement capability:

| Code | Name | Enforcement Stage | Trigger Condition | Host Action |
|---|---|---|---|---|
| `FW-CARRIER` | Carrier Violation | DECODE / PARSE | Emitted token contains a symbol outside pinned carrier $V_C$. | Logit mask at decode; parse-time rejection if bypass occurs. |
| `FW-OP` | Illegal Operation | PARSE | Move verb not in closed vocabulary (`ASSERT`, `CUT`, `VERIFY`, `RETRACT`). | JSON Schema rejection. |
| `FW-MOVE` | Invalid Redex | REPLAY | Proposed rule $r$ does not match redex at position $p$. | Host returns mismatch report; proposal discarded. |
| `FW-SCOPE` | Scope Breach | REPLAY | All-quantifier ($\forall$) evaluated over unverified or model-filtered domain. | Host enforces Domain-of-Quantification Rule; replaces with full carrier. |
| `FW-CHAIN` | Non-Monotonic Step | REPLAY | Transition yields $\|\Phi_1(S_{t+1})\|_{L_1} > \|\Phi_1(S_t)\|_{L_1}$ or introduces new defect. | Refuses transition; protects boundary invariant. |
| `FW-REPLAY` | Replay Divergence | REPLAY | Host recomputation of rule output does not match producer's claimed `produced_relation`. | Producer output discarded; divergence logged in audit trace. |
| `FW-LEAD` | Uncertified Exhaustion | REPLAY | Producer attempts context enlargement (Rule 2) without verified R1 exhaustion certificate. | Halts execution; demands explicit branch enumeration or retraction. |

---

## 5. Efficacy & Theoretical Limits

### 5.1 Expressivity and Auditability Gains

Operating an LLM under the $L_1$ Symbol Game Governor provides distinct architectural properties:

1. **Deterministic Linear-Time Replay:** By keying derivation steps by exact redex location $(p, \rho)$, host verification is a total deterministic function executing in linear time $\mathcal{O}(|l| + |s|)$ relative to term size.
2. **Unsigned Aggregation of Declared Residuals:** Because the defect register uses the $L_1$ norm ($\sum |w_i|$), opposite residual coordinates contribute positively to the current total rather than canceling by sign. The implemented CUT rule constrains only total non-increase; it does not require every coordinate to decrease, and it does not identify arbitrary logical contradiction.
3. **Content-Addressed Audit Trails:** The prototype records supported trace nodes as SHA-256 content addresses over canonical node data and ordered parents and verifies parent closure, hashes, edge projection, and acyclicity. This detects trace tampering inside the declared format; it is neither a digital signature nor evidence of semantic truth.

### 5.2 Fundamental Theoretical Limits

While the $L_1$ governor exposes opposite residuals in the declared finite encoding, it is bounded by strict mathematical limits:

#### 1. State Space Explosion

The host's capacity to certify Rule 1 structural exhaustion depends on traversing the forward reachability set:
$$\operatorname{Reach}_C(S_0) = \operatorname{lfp} \mathcal{X} . \left( \{S_0\} \cup \{\operatorname{apply}(r, s) : s \in \mathcal{X}, r \in \mathcal{T}\} \right)$$

For a relational system with $N$ carrier symbols, relations of arity $k$, and rule branching factor $b$, the worst-case size of $\operatorname{Reach}_C(S_0)$ scales exponentially with search depth $d$:
$$|\operatorname{Reach}_C(S_0)| \in \mathcal{O}(b^d)$$

When resource budgets impose a depth limit $d_{\max}$, the governor can only compute bounded reachability $\operatorname{Reach}_C^{\le d_{\max}}(S_0)$. Failing to find a solution within a depth-bounded search does not establish structural exhaustion.

#### 2. Undecidability of Semantic Reflection and Conservativity

When extending the Symbol Game from finite propositional relations to first-order relational structures with function symbols or unbounded context expansion (Rule 2):

- **Semantic Reflection (Conservativity):** Deciding whether a theory extension $C \subset C'$ is conservative ($C' \vdash \phi \iff C \vdash \phi$ for all $\phi \in \mathcal{L}_C$) is undecidable in general first-order logic (Rice's Theorem / Tarski's Undefinability).
- **Knuth-Bendix Non-Termination:** Attempting to complete a set of relational rewrite rules via Knuth-Bendix completion to obtain a convergent rewrite system can diverge into an infinite sequence of critical pairs.
- **Word Problem:** By the Novikov-Boone theorem, the word problem for finitely presented semigroups and groups is undecidable; verifying whether two relational expressions reduce to an identical normal form is non-computable in the general infinite case.

#### 3. The Semantic Grounding Boundary

The Symbol Game Governor is an internal deductive consistency verifier over declared symbolic presentations. It has no autonomous access to empirical reality:

- **Syntax vs. Grounding:** The governor verifies that `edge(a, b)` and `edge(b, c)` yield `edge(a, c)` according to rule $r_{\text{trans}}$. It cannot verify whether entity $a$ in the physical world bears relation `edge` to entity $b$.
- **Premise Dependence:** If false or contradictory premises are injected into the root state with status `declared`, the governor will faithfully preserve and propagate the errors through valid deduction steps. The governor ensures deductive validity ($\Gamma \vdash \psi$), not empirical truth.

#### 4. Locally-Masked Decoding Distortion

Applying step-wise grammar-constrained decoding (masking invalid token logits to $-\infty$ at each generation step) does **not** sample from the true conditional distribution $P(\text{string} \mid \text{string} \in \mathcal{L})$:

- Local logit masking eliminates dead-end paths only after the token prefix has already committed to them, transferring probability mass onto surviving siblings.
- This creates a systematic sampling distortion, over-weighting prefixes that happen to have large volumes of invalid continuation mass.
- While the emitted output is guaranteed to be syntactically well-formed, its distribution is skewed away from the base model's unconstrained conditional distribution.

---

## 6. Claim Hygiene Ledger

The following four-point summary defines the formal claim boundary for this architectural blueprint, in compliance with the Claim Hygiene Rule:

### 1. What this architecture supports:

- It supports a formal mathematical model demonstrating how continuous softmax attention over $L_2$ probability simplices permits convex combinations of contradictory latent vectors, producing cancellation laundering.
- It supports the formal specification of an external discrete projection governor $\mathcal{P}_S$ with verified idempotence ($\mathcal{P}_S^2 = \mathcal{P}_S$) on admitted relational presentations.
- It supports an algebraic cochain defect formulation $\Phi_1$ and $L_1$ defect norm $\|\Phi_1\|_{L_1}$ whose implemented CUT checks enforce monotonic defect non-increase on the declared finite edge surface.
- It supports a concrete 5-tuple state machine schema, a 4-move closed vocabulary (`ASSERT`, `CUT`, `VERIFY`, `RETRACT`), and a host-recomputed verification protocol that eliminates reliance on producer self-attestation.

### 2. What this architecture does not support:

- It does not support any claim that prompt wording alone can alter the internal continuous attention mechanisms or weight matrices of neural language models.
- It does not support any claim that grammar-constrained decoding ensures empirical truth, physical validity, or semantic grounding.
- It does not support a general decision procedure for the termination or confluence of arbitrary relational rewrite systems, which remains undecidable in the general case.
- It does not support any claim of physical quantum chromodynamics or continuum field limits from discrete combinatorial complexes.

### 3. The narrowest defensible claim:

Within the implemented finite edge-difference model, host recomputation, declared-carrier checks, monotonic $L_1$ defect-norm checks, and redex-keyed replay refuse unsupported moves and expose nonzero coboundary residuals. This is a syntactic consistency result for the declared model, not a general detector of logical contradiction or semantic truth.

### 4. The next test needed:

An executable Python prototype implementing the arity rewrite engine, the $L_1$ governor, and a cycle-consistency benchmark demonstrating the positive rejection of an $L_2$ cancellation error under pytest with $\ge 90\%$ statement and branch coverage.

---

## 7. Document Provenance & Citations

- **Sealed Derivation Reference:** Tag `sealed-derivation-v1` (`3100c4e`, cut 2026-08-17).
- **Core Repository Sources:**
  - `coda_all_universe/1_the_tower/3_observer_and_symbol_game/06_observer_treatise.md`
  - `coda_all_universe/1_the_tower/3_observer_and_symbol_game/07_symbol_game_fermion_sign.md`
  - `_ooutwire/symbol_game_review_20260901_opus_5_ultracoda/theory_research_20260901/01_fields/LLM_attention_and_parsing.md`
  - `_ooutwire/symbol_game_review_20260901_opus_5_ultracoda/theory_research_20260901/01_fields/OE_symbol_game_engine.md`
  - `_ooutwire/symbol_game_review_20260901_opus_5_ultracoda/symgam_full_review_opus_5_ultracode.md`
- **External Literature:**
  - Elhage, N., et al. (2021). *A Mathematical Framework for Transformer Circuits*. Anthropic Research.
  - Huet, G. (1980). *Confluent Reductions: Abstract Properties and Applications to Term Rewriting Systems*. Journal of the ACM, 27(4), 797-821.
  - Knuth, D. E., & Bendix, P. B. (1970). *Simple Word Problems in Algebraic Systems*. Computational Problems in Abstract Algebra, 263-297.
  - Newman, M. H. A. (1942). *On Theories with a Combinatorial Definition of "Equivalence"*. Annals of Mathematics, 43(2), 223-243.
  - Vaswani, A., et al. (2017). *Attention Is All You Need*. Advances in Neural Information Processing Systems, 30.
  - Willard, B. T., & Louf, R. (2023). *Efficient Guided Generation for Large Language Models*. arXiv:2307.09702.
