# pilot_0000051 — Projection Obstruction & Observer Visibility (Rung 4)

**AuthorityEffect:** None.  
**Governing Standard:** Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).  
**Task Family:** `projection_obstruction`  
**Host Checker:** `PFP-03-OBSERVER-VISIBILITY`  
**Structure Delta Metric:** `gate_boolean`  
**Mechanization Grounding:** Mathlib / Lean 4: [`po000_l004_observer_visibility.lean`](../../../../omega_engine_atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/lean4/po000_l004_observer_visibility.lean) (`PO000.ObserverVisibility.ThreePatch.three_patch_witness`, `no_recovery_modulus`). Python: [`code/observer_carriers.py`](../../../../omega_engine_atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction/code/observer_carriers.py) (`ThreePatchCertificate`, `three_patch_certificate()`).

The runs below were recorded while this campaign occupied `pilot_0000003`. That directory is the mode-trial refusal slot (`trial_0000003`), so the campaign files live here. Stored test ids and live receipts still name `pilot_0000003`.

---

## 1. Description & Mathematical Setup

This pilot investigates the extraction and derivation fidelity of the core obstruction theorem from paper `PO-000` (§7.4): **Exact Three-Patch Local-Green / Global-Red Observer Visibility Obstruction & Absence of a Recovery Modulus** (Proposition 7.4.5 & Corollary 7.4.6).

### 1.1 Covering Diagram & Sheaf Cochain Complex
Consider a finite covering nerve diagram with 3 open patches $u_1, u_2, u_3$ and 3 pairwise overlaps $x_{12}, x_{23}, x_{31}$. The 6 directed covering edges are:
$$e_1: x_{12} \to u_1, \quad e_2: x_{12} \to u_2$$
$$e_3: x_{23} \to u_2, \quad e_4: x_{23} \to u_3$$
$$e_5: x_{31} \to u_3, \quad e_6: x_{31} \to u_1$$

- **Fibers:** Each edge fiber is $\mathbb{R}^3$ equipped with the exact $\ell^1$ norm $\|v\|_1 = |v_0| + |v_1| + |v_2|$.
- **Restriction Maps:** All restriction homomorphisms are the identity $I_3 \in \mathbb{R}^{3 \times 3}$.
- **Section $s \in C^0$:**
  $$s(u_1) = (1, 0, 0)^T, \quad s(u_2) = (0, 1, 0)^T, \quad s(u_3) = (0, 0, 1)^T$$
  $$s(x_{12}) = s(x_{23}) = s(x_{31}) = (0, 0, 0)^T$$
- **Edge Coboundary $(d_0 s) \in C^1$:**
  $$(d_0 s)_e = s(\text{target}(e)) - s(\text{source}(e))$$
  - $e_1, e_6 \mapsto (1, 0, 0)^T$ (unit vector $e_1$)
  - $e_2, e_3 \mapsto (0, 1, 0)^T$ (unit vector $e_2$)
  - $e_4, e_5 \mapsto (0, 0, 1)^T$ (unit vector $e_3$)

### 1.2 Local Observers & Coordinate Deletion Projections
Three partial observers $\{C_1, C_2, C_3\}$ sample disjoint pairs of edges via coordinate-deletion projectors $\pi_\alpha: \mathbb{R}^3 \to \mathbb{R}^2$:
- $C_1$ watches $\{e_1, e_6\}$ via $\pi_0(v_0, v_1, v_2) = (v_1, v_2)^T$ (deletes coordinate 0).
- $C_2$ watches $\{e_2, e_3\}$ via $\pi_1(v_0, v_1, v_2) = (v_0, v_2)^T$ (deletes coordinate 1).
- $C_3$ watches $\{e_4, e_5\}$ via $\pi_2(v_0, v_1, v_2) = (v_0, v_1)^T$ (deletes coordinate 2).

On each edge $e \in \text{Edges}(\alpha)$, observer $\alpha$ measures the $\ell^1$ norm of the projected coboundary:
$$J^\alpha(s) = \sum_{e \in \text{Edges}(\alpha)} \|\pi_\alpha((d_0 s)_e)\|_1$$

### 1.3 Exact Sovereign Ground Truth
1. **Local Tallies:**
   - On $e_1, e_6$: $(d_0 s) = (1, 0, 0)^T \implies \pi_0((1, 0, 0)^T) = (0, 0)^T \implies J^{C1} = \|0\|_1 + \|0\|_1 = 0$.
   - On $e_2, e_3$: $(d_0 s) = (0, 1, 0)^T \implies \pi_1((0, 1, 0)^T) = (0, 0)^T \implies J^{C2} = \|0\|_1 + \|0\|_1 = 0$.
   - On $e_4, e_5$: $(d_0 s) = (0, 0, 1)^T \implies \pi_2((0, 0, 1)^T) = (0, 0)^T \implies J^{C3} = \|0\|_1 + \|0\|_1 = 0$.
   - **All-Green:** $\max_\alpha J^\alpha = 0 \implies \text{all\_green} = \text{true}$.
2. **Global Raw Defect Norm:**
   $$I(s) = \sum_{k=1}^6 \|(d_0 s)_{e_k}\|_1 = 2 \cdot \|(1,0,0)\|_1 + 2 \cdot \|(0,1,0)\|_1 + 2 \cdot \|(0,0,1)\|_1 = 2(1) + 2(1) + 2(1) = 6$$
3. **Visibility Gap:**
   $$\Lambda = I(s) - \max_\alpha J^\alpha(s) = 6 - 0 = 6$$
4. **Absence of Recovery Modulus:**
   Under positive uniform scalings $s_\lambda = \lambda s$ for $\lambda > 0$:
   $$I(s_\lambda) = 6\lambda, \quad \text{while } J^\alpha(s_\lambda) = 0 \quad \forall \alpha, \lambda > 0$$
   No function $f: \mathbb{R}_+ \to \mathbb{R}_+$ can satisfy $I(s_\lambda) \le f(\max_\alpha J^\alpha(s_\lambda))$ because $6\lambda \le f(0)$ is contradicted as $\lambda \to \infty$. Thus $\text{recovery\_modulus\_exists} = \text{false}$.

---

## 2. Claim Hygiene Envelope

### 2.1 What This Pilot Supports
- Supports that the sovereign host checker `PFP-03-OBSERVER-VISIBILITY` deterministically evaluates candidate proposals against the exact Lean 4 / Python certified obstruction ground truth.
- Supports testing of model sensitivity across 10 distinct surface rewrite strategies, ranging from unadorned mathematical plain-text to discrete cochain complexes and S(n) down-maps.
- Supports empirical tracking of whether models correctly detect the coordinate-deletion nullspace, identify the global-red non-vanishing coboundary, compute $\Lambda = 6$, and deduce the impossibility of a recovery modulus.
- Supports detection and granting of typed structural lift requests (`rule_request_structural_lift`).

### 2.2 What This Pilot Does NOT Support
- Does **NOT** support any claim that LLMs generally or reliably reason about algebraic topology, sheaf cohomology, or observer projection gaps.
- Does **NOT** interpret a successful arithmetic derivation as mathematical proof of universal cognitive capability.
- Does **NOT** claim that rejection under bare prompts constitutes an uncorrectable architectural defect rather than a prompt surface sensitivity.

### 2.3 Narrowest Defensible Claim
- Under the declared assumptions and finite 3-patch covering diagram with $\mathbb{R}^3$ $\ell^1$ fibers, the host verification engine deterministically distinguishes exact observer tallies ($J=\{C1:0, C2:0, C3:0\}$, $I=6$, $\Lambda=6$, $\text{recovery\_modulus\_exists}=\text{false}$) from heuristic shortcuts (e.g. Euclidean $\ell^2$ norms, false cancellation, or hallucinated recovery bounds).

### 2.4 Next Test Needed
- Evaluate cross-model sensitivity by dispatching the identical 13-test suite across Frontier reasoning models (e.g. `anthropic/claude-3.7-sonnet`, `openai/o3-mini`, `google/gemini-2.5-pro`) to measure comparative dialect robustness, latency scaling, and structural lift request frequency.

---

## 3. Test & Trial Catalog

| Test ID | Case ID | Generation | Dialect / Intervention | Model | Expected Gate | Actual Gate | Latency (s) | Cost ($) |
|---|---|---|---|---|---|---|---|---|
| `test_00` | `seed_bare` | Gen 0 | Bare Seed Prompt (Unadorned Mathematical Specification) | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 3.66s | $0.000000 |
| `test_01` | `rewrite_01` | Gen 0 | Tier H: Verbal Topological Covering & Patch Overlap | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 4.03s | $0.000000 |
| `test_02` | `rewrite_02` | Gen 0 | Tier D: Dense Mathematical Formula | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 13.95s | $0.000000 |
| `test_03` | `rewrite_03` | Gen 0 | Tier S: Discrete SymSys Syntax | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 22.98s | $0.000000 |
| `test_04` | `rewrite_04` | Gen 0 | Matrix/Vector Algebraic Presentation | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 6.40s | $0.000000 |
| `test_05` | `rewrite_05` | Gen 0 | Category-Theoretic Covering Functor Presentation | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 63.08s | $0.000000 |
| `test_06` | `rewrite_06` | Gen 0 | Discrete Sheaf Cochain Complex ($C^0 \to C^1$) | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 12.83s | $0.000000 |
| `test_07` | `rewrite_07` | Gen 0 | Sensor Array Coordinate-Deletion Channel Masking | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 11.26s | $0.000000 |
| `test_08` | `rewrite_08` | Gen 0 | S(n) Retraction Down-Map Dialect | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 24.25s | $0.000000 |
| `test_09` | `rewrite_09` | Gen 0 | Genesis Relational Substrate Dialect | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 10.16s | $0.000000 |
| `test_10` | `rewrite_10` | Gen 0 | Operator-Licensed Axiomatic Presentation | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 5.30s | $0.000000 |
| `test_11` | `p_star_baseline` | Gen 1 | P* Universal Prompt Template Baseline (SPK-001) | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 166.13s | $0.001044 |
| `test_12` | `p_star_lifted` | Gen 2 | P* Template with DDC Structural Lift Granted (`DDC-LIFT-PO000-001`) | `deepseek/deepseek-v4.1-flash` | ACCEPTED | **ACCEPTED** | 15.42s | $0.001757 |
