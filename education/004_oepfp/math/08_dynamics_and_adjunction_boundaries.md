# 08. Engine Dynamics & Adjunction Boundaries

**AuthorityEffect:** None.
**Classification:** Exploratory Theory / Operator Dynamics.
**Status:** [EXPLORATORY / CONJECTURE-GRADE].

> **Status Caveat:** Operator genesis from a lift $\dashv$ forget adjunction (unit $\eta$, counit $\varepsilon$) is CONJECTURED, not proved. Only SINGLE-STEP transport invariance is described as Lean-certified (`GTMUR-T07`, $q_F=0 \iff \text{certificate}$). *(Source check 2026-10-20 at `c419cc6beb`: the identifier `GTMUR-T07` does not occur in any `.lean` file; it appears only in the encyclopedia generator `.agents/skills/panep-math-and-physics-prof/regen_encyclopedia.py` and one atlas prompt. Treat the Lean certification as unverified until a named Lean declaration is cited. The "canonical math spine §III.6" is not a file in this folder.)* Round-trip / composite ($\text{lift} \circ \text{forget}$) conservation rests on the conjectured adjunction. Do not cite this file as proved authority. See canonical math spine §III.6.

---

## 1. The Generating Mechanism: Operators from Adjunction Boundaries

### 1.1 The Tower as a Sequence of Adjunctions

The Core tower is structured as:

$$
\Omega_\partial \xrightarrow{i_0} \Omega_{\mathbb{A}} \xrightarrow{i_1} \Omega_\chi \xrightarrow{i_2} \Omega_{\mathfrak{O}} \xrightarrow{i_3} \Omega_\kappa \xrightarrow{i_4} \Omega_{\Lambda\Omega}
$$

Each transition $i_k$ has a forgetful direction $U_k$. The pair $(i_k, U_k)$ forms an adjunction:

| Component | Formula | Operational Meaning |
|---|---|---|
| **Unit** $\eta$ | $\eta_X : X \to U(F(X))$ | Measures what is lost by round-tripping through the higher layer. |
| **Counit** $\varepsilon$ | $\varepsilon_Y : F(U(Y)) \to Y$ | Measures what is redundant in the higher layer's view. |

---

## 2. Derivation of the Five Operator Classes (E/I/C/R/M)

From the adjunction unit $\eta$ and counit $\varepsilon$, the five operator classes arise naturally:

1. **Expansion ($E$):** $\operatorname{ker}(\eta_X) \neq 0$ (this and the conditions below presuppose additive categories, in which kernels and images exist; the tower is not shown to be one). The lower representation cannot express the newly witnessed structure; dimensionality or carrier size must expand.
2. **Internal Permutation ($I$):** $\eta_X$ is an isomorphism on carrier volume, but coordinate orientation changes.
3. **Boundary Contraction ($C$):** $\operatorname{im}(\varepsilon_Y) \subset Y$. Redundant boundary faces or cochains are collapsed.
4. **Redundancy Elimination ($R$):** Quotienting out duplicate identical semantic payloads while preserving topological connectivity.
5. **Stationary Refusal ($M$):** Obstruction is unresolvable within the current algebraic carrier budget without violating conservation laws.
