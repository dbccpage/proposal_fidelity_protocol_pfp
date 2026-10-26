# Detailed definition: Terminal Routing & Curved Witness Invariants (1)

**AuthorityEffect:** None.

Parent: [Terminal Routing & Curved Witness Invariants](../../../../../rules/math/rl_terminal_routing_and_curved_witness_invariants.md). Load for the matching predicate, not every task.

# Rule: Problem-Bound Terminal Routing, Authority Gating & Curved Witness Invariants

**AuthorityEffect:** None.

This rule codifies problem-bound terminal routing, zero-residual dual circulation feasibility, four-stage authority gating pipelines, and curved constrained witness coupled annihilators. Cross-reference exact verification and witness integrity: [`rl_exact_verification_and_witness_integrity_invariants.md`](../../../../../rules/math/rl_exact_verification_and_witness_integrity_invariants.md), and cochain defect and descent invariants: [`rl_cochain_defect_and_guarded_descent_invariants.md`](../../../../../rules/math/rl_cochain_defect_and_guarded_descent_invariants.md).

---

## Problem-Bound Terminal Route Verification Invariant

> **Problem-Bound Routing Rule:**
>
> 1. Terminal route dispatchers (`terminal_route`) must never accept `ExactRepair` based on declared certificate payloads alone.
> 2. **Universal Pre-Branch Problem Consistency:** Problem-bound consistency checks must execute before dispatching to *either* terminal branch (`EXACT_REPAIR` or `STABILIZED_SURVIVOR`). If an active registry is supplied alongside explicit `packet` or `defect` arguments, any mismatch between explicit arguments and the registry's declared problem data must immediately fail closed to `TerminalRoute.OPEN_OBSTRUCTION`.
> 3. **Exact Branch Verification:** In the exact branch, the dispatcher must verify input and observer digests, verify that the $\Phi_1$ certificate satisfies the exact repair equation ($x + d_0 f = 0$ with residual $= 0$), verify the $\Gamma_2$ boundary certificate, and independently recompute the diagnosis.
> 4. **Single-Pass Iterator Preservation:** Diagnostic recomputation must not re-consume single-pass input iterators or generator arguments. Solvers and verifiers must recompute diagnosis using the realized, validated exact column vector $x$ (e.g. `diagnose(bound_packet, x)`), ensuring iterators and sequences exhibit identical routing.
> 5. **Fail-Closed Default:** Any missing problem data, digest mismatch, conflicting argument, or unverified repair equation must fail closed to `TerminalRoute.OPEN_OBSTRUCTION`.

---

## Zero-Residual Dual Circulation Feasibility Invariant

> **Complementary Slackness & Zero-Residual Circulation Splitting:**
>
> 1. **Zero-Residual Flow Freedom:**
>    In primal-dual linear programming on graphs, complementary slackness requires non-zero edge flow only when $|r_e| = 0$ (so $|y_e| \le w_e$), but does NOT fix non-tree edge flows to zero. A valid optimum may require splitting circulation across multiple zero-residual paths.
> 2. **Exact Rational Feasibility Resolution:**
>    Solvers constructing dual certificates must employ exact rational linear feasibility (e.g. Fourier-Motzkin elimination or exact simplex) over the bounded cycle subspace when multiple zero-residual non-tree edges exist, rather than raising `ArithmeticError` or emitting incomplete certificates on valid inputs.

---

## Four-Stage Authority Gating, Cochain Information Sufficiency & Receipt Isolation Invariant

> **Linear Complex Defect Separation, Authority Gating Pipeline & Digest Envelope Isolation:**
>
> 1. **Four-Stage Authority Pipeline Separation:**
>    Engines must decouple operations into four stages:
>    $$\text{cochain evaluation} \longrightarrow \text{checked result} \longrightarrow \text{authorization decision} \longrightarrow \text{issued receipt}.$$
>    Classifiers return pure mathematical classifications and evidence; they must NEVER create registries or issue tokens. A separate gate evaluates evidence against contracts before issuing authority.
> 2. **Information Sufficiency & Exactness vs. Mass Separation:**
>    - Norms ($\|r\|, \|d_1 r\|$) cannot determine exactness or closure; evaluators must use actual operators ($d_0, d_1$) or certificates.
>    - Classifiers distinguish four disjoint conditions:
>      a. $r = 0$: Zero defect.
>      b. $r \ne 0 \land \operatorname{Exact}(r)$: Nonzero repairable exact defect ($\exists \alpha, d_0 \alpha = r$). Requires verified repair certificate before authority.
>      c. $\operatorname{Closed}(r) \land \neg\operatorname{Exact}(r)$: Closed non-exact residual ($d_1 r = 0 \land r \notin \operatorname{im} d_0$).
>      d. $\neg\operatorname{Closed}(r)$: Open residual ($d_1 r \ne 0$).
>    - Missing exactness data with $\|r\| > 0$ and $d_1 r = 0$ raises `ValueError` rather than defaulting to closed. Inconsistent states ($r = 0, d_1 r \ne 0$) fail closed.
> 3. **Proposal Digest Receipt Envelope Key Decoupling:**
>    Receipt registries must decouple receipt envelope keys (`{"token", "verified_token", "receipt_envelope"}`) from proposal body digests. The digest hashes payload and action metadata while ignoring carrier keys, preventing verification from invalidating its own binding.
> 4. **Lawvere Maximal Sound Authority Descent Adjunction:**
>    - Authority transport along a quotient map $q: X \to Y$ must use Lawvere universal quantification $\forall_q A(y) := \forall x, q(x) = y \Rightarrow A(x)$ ($q^{-1}(B) \subseteq A \iff B \subseteq \forall_q A$).
>    - Exact authority descent holds iff authority is constant on fibers ($q(x) = q(x') \implies (A(x) \iff A(x'))$). Mixed fibers constitute the exact obstruction to lossless transport.
>    - Quantifiers distribute across obligation conjunctions: $\forall_q (\bigwedge_i A_i) = \bigwedge_i \forall_q A_i$.

---

## Curved Constrained Witness Coupled Annihilator Invariant (`RULE_CURVED_CODA_COUPLED_WITNESS_PRESERVATION_001`)

> **Curved Locus Certificate Preservation:**
>
> 1. **Coupled Annihilator Condition:** On curved complexes where the coboundary composition is non-zero ($K = d_1 d_0 \ne 0$), representative repair optimization certificates must satisfy the coupled annihilator condition:
>    $$d_0^\top y + K^\top z = 0, \quad K = d_1 d_0$$
> 2. **Prohibition of Truncation:** Implementations and layer outcomes must never truncate the curved certificate by discarding the coupled multipliers $z$ and $\lambda$. Dual witness $y$ alone does NOT certify an annihilator when $K \ne 0$ ($d_0^\top y \ne 0$).
> 3. **Distinct Payload Variants:** CODA pipeline outcomes and serialization models must expose distinct typed variants:
>    - `FlatQuotient`: complete exact quotient certificate certifying $d_0^\top y = 0$.
>    - `CurvedConstrained`: complete constrained certificate carrying $(y, z, \lambda, \tau)$ and verifying $d_0^\top y + K^\top z = 0$.
