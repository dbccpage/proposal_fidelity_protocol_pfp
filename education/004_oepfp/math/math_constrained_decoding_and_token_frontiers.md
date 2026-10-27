---
documentation_contract: symbol-game-documentation/v1
title: 'Application Note: Constrained Decoding, Attention-Sparse Output Boundaries, and Token Frontiers'
kind: application-reference
audience:
  - researchers
  - ml-engineers
  - logicians
  - coding-agents
status: active
maturity: emerging
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - autoregressive_token_simplex
    - simplex_l1_invariance
    - token_frontier_admissible_set
    - bayesian_logit_mask_projection
    - retained_probability_mass
    - fail_stop_zero_mass_refusal
    - three_layer_sovereignty_boundary
  prose_theorems:
    - l1_norm_constant_on_probability_simplex
    - exact_mass_conservation_and_renormalization
    - token_membership_insufficient_for_witness_validity
  lean_theorems: []
  finite_computations:
    - demo_token_frontier_5_tests
    - demo_token_frontier_8_point_mutation
    - attention_entropy_kv_norm_receipt
  declared_policies:
    - zero_float_in_rational_probabilities
    - fail_stop_zero_retained_mass
  applications:
    - syntax_directed_constrained_generation
    - grammar_enforced_wire_decoding
    - layer_separated_evaluation_fences
  open_conjectures: []
coefficient_domain: "ℚ ∩ [0, 1] / ℝ"
runtime_dependency: "Chapter 00 (Scope & Notation), Chapter 03 (Obstruction Mass & LP Duality)"
governance_dependency: "None"
---

# Application Note: Constrained Decoding, Attention-Sparse Output Boundaries, and Token Frontiers

**Status:** Downstream Mathematical Application  
**Context:** Formulates the mathematical foundations of constrained neural decoding, dynamic logit masking, Bayesian re-normalization, the $\ell_1$ norm invariance theorem on the probability simplex, and the Three-Layer Sovereignty Boundary. Grounded in `attention_sparse_output_boundary.md` (not found at source pin `c419cc6beb`, 2026-10-20), `demo_token_frontier` (now at `atlas/coda_atlas/F004_papers/015_pfp/003_pfp_host_admitted_failure_detectors/demos/demo_token_frontier/`), and Challenges C001–C010.  
**Authority:** None. Probability theory, discrete optimization, and runtime boundary contracts.

---

## 1. Autoregressive Generation & The Probability Simplex

Let $V$ be a finite token vocabulary of size $|V| = N$. Let $x_{<t} = (x_1, x_2, \ldots, x_{t-1}) \in V^*$ be an admitted prompt prefix.

### 1.1 Unconstrained Model Distribution
An autoregressive model parameterized by weights $\theta$ maps prefix $x_{<t}$ to an unnormalized logit vector $z_t \in \mathbb{R}^{|V|}$. The standard softmax operator produces a probability distribution over the standard probability simplex:

$$\Delta(V) = \left\{ p \in \mathbb{R}^{|V|} : p_v \ge 0 \; \forall v \in V, \; \sum_{v \in V} p_v = 1 \right\}$$

defined by:
$$p(v \mid x_{<t}) = \frac{\exp(z_t(v))}{\sum_{u \in V} \exp(z_t(u))}$$

---

## 2. Mathematical Correction: The Simplex $\ell_1$ Invariance Theorem

A common informal heuristic in machine learning suggests adding an $\ell_1$ penalty to an output distribution $\lambda \|p\|_1$ to "induce sparsity in the output token distribution". This claim contains a mathematical contradiction:

### 2.1 The Invariance Theorem
**Theorem ($\ell_1$ Constant on Probability Simplex):**  
For any vector $p \in \Delta(V)$, its $\ell_1$ norm satisfies:
$$\|p\|_1 = \sum_{v \in V} |p_v| = \sum_{v \in V} p_v = 1$$
identically.

*Corollary (Ineffectiveness of $\ell_1$ Penalty on Simplex):*  
Adding an $\ell_1$ penalty $\lambda \|p\|_1$ to any objective over $\Delta(V)$ produces:
$$\min_{p \in \Delta(V)} \mathcal{L}(p) + \lambda \|p\|_1 \equiv \min_{p \in \Delta(V)} \mathcal{L}(p) + \lambda$$
Because $\lambda$ is a constant independent of $p$, its gradient $\nabla_p (\lambda \|p\|_1) = \mathbf{0}$ on the tangent space of the simplex. It cannot alter the optimum, cannot collapse entropy, and cannot induce token support sparsity.

### 2.2 Genuine Support Restriction vs. Steering
- **Constant Penalty:** Soft $\ell_1$ on $p \in \Delta(V)$ is mathematically inert.
- **Finite Logit Bias:** A finite additive shift $z'(v) = z(v) + b_v$ (e.g. OpenAI `logit_bias`) perturbs the relative probabilities $p(v) \propto \exp(z(v) + b_v)$, acting as a steering parameter. However, because $\exp(z(v) + b_v) > 0$ for all finite $b_v \in \mathbb{R}$, the support remains full: $\operatorname{supp}(p) = V$.
- **Exact Support Projection:** True sparsity requires an exact face projection setting $z(v) = -\infty$ for all $v \notin K$, restricting the support strictly to a subset face $\Delta(K) \subset \Delta(V)$.

---

## 3. TokenFrontier: Syntax-Directed Dynamic Logit Masking

The `TokenFrontier` architecture implements exact support restriction guided by a deterministic formal grammar or automaton.

### 3.1 The Admissible Token Frontier
Let $S$ be the current operational state of a deterministic finite automaton (DFA) or pushdown automaton (PDA) tracking the parse tree of the generation prefix $x_{<t}$.

The **admissible token frontier** is the state-dependent subset:
$$V_{\mathrm{valid}}(S) \subseteq V$$
containing all tokens that can legally extend the prefix without violating the language syntax. The complement set:
$$V_{\mathrm{invalid}}(S) = V \setminus V_{\mathrm{valid}}(S)$$
has cardinality $|V| - |V_{\mathrm{valid}}(S)|$ and represents all syntactically forbidden continuations.

### 3.2 The Masked Logit Projection
The decoding engine applies an exact projection operator $\Pi_S: \mathbb{R}^{|V|} \to \overline{\mathbb{R}}^{|V|}$:

$$(\Pi_S z)_v = \begin{cases} z_v & \text{if } v \in V_{\mathrm{valid}}(S) \\ -\infty & \text{if } v \notin V_{\mathrm{valid}}(S) \end{cases}$$

Under softmax evaluation, $\exp(-\infty) = 0$, ensuring that all forbidden tokens receive probability identically zero.

---

## 4. Probability Mass Conservation & Bayesian Re-Normalization

When sampling from the constrained frontier, the base unconstrained probabilities must be conditioned on the event that the emitted token belongs to $V_{\mathrm{valid}}(S)$.

### 4.1 Retained Probability Mass
Let $P_{\mathrm{base}}(t)$ denote the base probability of token $t \in V$ emitted by the language model. The **retained probability mass** is:

$$M_{\mathrm{retained}} = \sum_{t \in V_{\mathrm{valid}}(S)} P_{\mathrm{base}}(t) \in [0, 1]$$

### 4.2 Bayesian Conditioning
By Bayes' rule, the conditional probability of token $t$ given admissibility is:

$$\boxed{P_{\mathrm{constrained}}(t) = P(t \mid t \in V_{\mathrm{valid}}(S)) = \begin{cases} \frac{P_{\mathrm{base}}(t)}{M_{\mathrm{retained}}} & \text{if } t \in V_{\mathrm{valid}}(S) \\ 0 & \text{if } t \notin V_{\mathrm{valid}}(S) \end{cases}}$$

**Conservation Theorem:**  
Under Bayesian conditioning with $M_{\mathrm{retained}} > 0$:
$$\sum_{t \in V_{\mathrm{valid}}(S)} P_{\mathrm{constrained}}(t) = \sum_{t \in V_{\mathrm{valid}}(S)} \frac{P_{\mathrm{base}}(t)}{M_{\mathrm{retained}}} = \frac{1}{M_{\mathrm{retained}}} \sum_{t \in V_{\mathrm{valid}}(S)} P_{\mathrm{base}}(t) = \frac{M_{\mathrm{retained}}}{M_{\mathrm{retained}}} = 1$$

### 4.3 Fail-Stop Boundary: Zero Retained Mass
If the base model places zero probability on every syntactically legal token ($M_{\mathrm{retained}} = 0$), division by zero occurs. The engine refuses to hallucinate or default to an unconstrained token. It halts immediately and returns a typed refusal:

$$\operatorname{Refusal}(\text{ZeroRetainedMassError: Retained probability mass is exactly zero})$$
with code `DecodingRefusalCode.ZERO_RETAINED_MASS` (defined in [`pfp/domain/decoding/errors.py`](../../../../pfp/domain/decoding/errors.py); the entity is `TokenFrontier` in [`token_frontier.py`](../../../../pfp/domain/decoding/token_frontier.py), read 2026-10-20).

*When can the mass be zero? (2026-10-20)* Under an exact softmax every token has probability $\exp(z_v)/\sum_u \exp(z_u) > 0$, so $M_{\mathrm{retained}} = 0$ happens only when $V_{\mathrm{valid}}(S) = \varnothing$ or when the base distribution has already been truncated or rounded (top-$k$, top-$p$, quantized probabilities). *Worked example:* base probabilities $(1/2, 1/3, 1/6)$ on tokens $(a, b, c)$ with $V_{\mathrm{valid}} = \{b, c\}$ give $M_{\mathrm{retained}} = 1/3 + 1/6 = 1/2$ and constrained probabilities $(0, 2/3, 1/3)$, which sum to 1. With $V_{\mathrm{valid}} = \{c\}$ after a top-2 truncation that zeroed $c$, the mass is 0 and the engine refuses.

### 4.4 Exact Rational Arithmetic
To prevent floating-point drift from violating probability conservation ($\sum p_i \ne 1$) or falsely triggering zero-mass errors, all probabilities in the canonical `TokenFrontier` implementation are represented as exact irreducible rational fractions (a softmax of rational logits is generally irrational, so these rationals are supplied or rounded base probabilities, and the exactness applies to the conditioning step):
$$P(t) = \frac{p_t}{q_t} \in \mathbb{Q} \cap [0, 1], \qquad \gcd(p_t, q_t) = 1, \quad q_t > 0$$

---

## 5. The Three-Layer Sovereignty Boundary

The relationship between neural model activations, decoding controls, and formal mathematical truth is governed by the **Three-Layer Sovereignty Boundary**:

```
+-----------------------------------------------------------------------------------+
| LAYER 1: Internal Model Computation (Hidden States, Attention Heads, KV Caches)   |
| Interventions: Attention key masking, activation patching, steering vectors.      |
| Epistemic Status: Heuristic internal routing. No proof or correctness claim.      |
+-----------------------------------------+-----------------------------------------+
                                          |
+-----------------------------------------v-----------------------------------------+
| LAYER 2: Token Selection & Decoding Frontier (Logits, Logit Biases, TokenFrontier)|
| Interventions: Logit masking (-inf), JSON schema projection, BNF grammar guards.  |
| Epistemic Status: Enforces surface syntax. A schema-valid output is still untrusted|
| candidate data (e.g. 3+4 -> 555555 under digit-only mask).                        |
+-----------------------------------------+-----------------------------------------+
                                          |
+-----------------------------------------v-----------------------------------------+
| LAYER 3: Sovereign Host Evaluation & Certifiers (Exact Rational Checks, Lean 4)  |
| Interventions: Obstruction mass Phi_k, Bianchi defect Gamma_k, duality certificates|
| Epistemic Status: SOVEREIGN. Recomputes all checks independently from scratch.     |
| Terminal Status: Only Layer 3 can assign ACCEPT, REJECT, or REFUSAL.              |
+-----------------------------------------------------------------------------------+
```

### 5.1 Token Membership Does Not Certify Correctness
A crucial consequence of Layer 2 / Layer 3 separation is that **surface syntax compliance is not mathematical truth**:
- In local tests (`attention_sparse_output_boundary.md`), restricting Qwen2.5-0.5B to digit tokens via an exact logit mask when queried on `3+4` caused the model to emit `555555`.
- The output was 100% syntactically valid under the token mask, but 100% false mathematically.
- Layer 3 alone parses the output, checks the witness arithmetic, and rejects the result.

---

## 6. Claim Hygiene & Artifact Boundary

1. **What this document supports:**
   - Shows that the $\ell_1$ norm is constant ($=1$) on the probability simplex $\Delta(V)$ and cannot induce probability support sparsity.
   - Demonstrates exact Bayesian re-normalization of language model output logits over dynamic grammar frontiers.
   - Formalizes the fail-stop refusal when retained mass reaches zero.
   - Establishes the Three-Layer Sovereignty Boundary.

2. **What this document does NOT support:**
   - Does not establish that attention key masking ensures reduced hidden state rank or dimensional collapse without explicit singular value spectrum measurements.
   - Does not claim that constrained decoding alone can solve undecidable or NP-hard search problems.

3. **Narrowest defensible claim:**
   - On a finite vocabulary $V$ and grammar state $S$, setting logits outside $V_{\mathrm{valid}}(S)$ to $-\infty$ strictly restricts the output support to $V_{\mathrm{valid}}(S)$, preserves exact conditional probability mass over $\mathbb{Q}$ when $M_{\mathrm{retained}} > 0$, and provides surface syntax adherence while leaving semantic validity to independent Layer 3 checking.

4. **Next test needed:**
   - Measure activation singular value spectra and effective ranks across 100 open-weights prompts to empirically test whether attention masking produces low-dimensional internal representations.
