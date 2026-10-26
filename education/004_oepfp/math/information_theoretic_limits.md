---
documentation_contract: symbol-game-documentation/v1
title: 'Appendix: Information-Theoretic Limits and Fano Equivocation Bounds'
kind: mathematical-appendix
audience:
- researchers
- information-theorists
- coding-agents
status: active
maturity: emerging
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - joint_task_proposal_terminal_model
    - equivocation_entropy
  prose_theorems:
    - fano_error_lower_bound
    - positive_equivocation_implies_positive_error
  lean_theorems: []
  finite_computations: []
  declared_policies: []
  applications:
    - proposal_fidelity_evaluation
  open_conjectures: []
coefficient_domain: "ℝ / [0, 1]"
runtime_dependency: "None"
governance_dependency: "bounded_execution_and_authority_separation.md"
---

# Appendix: Information-Theoretic Limits and Fano Equivocation Bounds

**Status:** Mathematical Appendix (Optional Context)  
**Authority:** None. Classical information theory applied to proposal-verifier channels.  
**Admissibility Precondition:** This appendix explicitly begins **after** a joint probability distribution $P(X, Y, T)$ over task instances, proposals, and terminal outcomes has been formally admitted.

---

## 1. Joint Probability Model Definition

Let:
1. $X$ be a finite or discrete set of input task specifications,
2. $Y \in \Gamma$ be a model proposal generated according to conditional probability distribution $P_\theta(Y \mid X)$,
3. $T \in \mathbb{T}_S$ be the true underlying deterministic evaluation terminal status, where $\mathbb{T}_S$ is a finite terminal alphabet ($|\mathbb{T}_S| \ge 2$).

The joint system is modeled by the joint distribution:
$$P(X = x, Y = y, T = t) = P(X = x) P_\theta(Y = y \mid X = x) P(T = t \mid X = x, Y = y)$$

---

## 2. Fano Equivocation and Decision Error

Let $\hat{T}: \Gamma \to \mathbb{T}_S$ be any estimator or decision rule that predicts the terminal status $T$ solely from the generated proposal $Y$, without executing the independent deterministic verifier.

Let $P_e = P(\hat{T}(Y) \ne T)$ be the probability of prediction error.

### 2.1 The Exact Fano Bound
By classical information theory (Fano's Inequality), the conditional entropy (equivocation) $H(T \mid Y)$ satisfies:

$$H(T \mid Y) \le H_2(P_e) + P_e \log_2 (|\mathbb{T}_S| - 1)$$

where $H_2(p) = -p \log_2 p - (1-p) \log_2 (1-p)$ is the binary entropy function (measured in bits).

### 2.2 Mathematical Consequences

1. **Zero-Error Implication:**  
   If $H(T \mid Y) > 0$ (meaning the proposal tokens $Y$ do not completely determine the underlying verifier verdict $T$), then $P_e > 0$. An unverified proposal generator cannot achieve zero decision error whenever task verification invariants carry unobserved conditional entropy.
2. **High-Equivocation Linear Relaxation:**  
   When the equivocation exceeds 1 bit ($H(T \mid Y) > 1$), using the general bound $H_2(P_e) \le 1$ yields the linear lower bound:
   $$P_e \ge \frac{H(T \mid Y) - 1}{\log_2 |\mathbb{T}_S|}$$
   *(Derivation and example, added 2026-10-20.)* Fano with $H_2(P_e) \le 1$ gives $P_e \ge (H(T \mid Y) - 1)/\log_2(|\mathbb{T}_S| - 1)$; replacing $|\mathbb{T}_S| - 1$ by the larger $|\mathbb{T}_S|$ weakens the bound to the displayed form. Example: with $|\mathbb{T}_S| = 8$ and $H(T \mid Y) = 2$ bits, the displayed bound gives $P_e \ge 1/3$, and the sharper form gives $P_e \ge 1/\log_2 7 \approx 0.356$. For $|\mathbb{T}_S| = 2$ Fano gives $H(T \mid Y) \le H_2(P_e) \le 1$, so the relaxation never applies.
   *(Note: when $H(T \mid Y) \le 1$, this linear relaxation can become nonpositive; the exact nonlinear Fano inequality must be utilized in that regime).*

---

## 3. Claim Hygiene

1. **What this supports:** Demonstrates that under a declared joint probability distribution $P(X, Y, T)$, unverified candidate proposals cannot achieve error-free terminal prediction when conditional entropy $H(T \mid Y)$ is strictly positive.
2. **What this does not support:** Does not establish empirical error rates for uncharacterized commercial models without an empirically measured joint distribution; does not replace deterministic verifier execution.
