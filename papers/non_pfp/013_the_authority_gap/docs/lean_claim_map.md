# Lean Claim Map: Paper 005 — The Authority Gap

**Paper Target:** `001_finite_obstruction_calculus/005_the_authority_gap`  
**Version:** 2.0.2  
**Mechanization Level:** The three proved rows have Lean 4 declarations in `lean4/AuthorityGap.lean` and Python checks in `code/proved_rows.py`. Definitions, policy rules, and operational rules stay prose.

---

## Claim Mechanization Status

| Claim ID | Monograph Claim Title | Declared Status | Lean 4 Status | Lake Module | Notes |
|---|---|---|---|---|---|
| `CLM-005-001` | Counterfeit Descent Definition | `[DEFINITION]` | `N/A` | None | Foundational operational process definition in prose. |
| `CLM-005-002` | Authority Packet Structure | `[DEFINITION]` | `N/A` | None | Seven-layer systems architecture specification. |
| `CLM-005-003` | Evaluator Sovereignty Principle | `[POLICY RULE]` | `N/A` | None | Normative institutional design constraint ($M \not\Rightarrow E_H$). |
| `CLM-005-004` | Generative Self-Critique Non-Authority | `[POLICY RULE]` | `N/A` | None | Adversarial boundary condition on terminal authority. |
| `CLM-005-005` | Scaling Non-Transfer | `[POLICY RULE]` | `N/A` | None | Structural distinction between proposal mass and authority. |
| `CLM-005-006` | Benchmark Non-Transfer | `[POLICY RULE]` | `N/A` | None | Scope constraint on benchmark evaluation packets. |
| `CLM-005-007` | Local Green / Global Red Defect | `[PROVEN]` | `AuthorityGap.lean` | `hidden_bit_counts`, `local_green_does_not_imply_global`, `unconditional_red_ratio` | Python `calculate_ngd` on the four-point hidden-bit census and the two-point global rejection. |
| `CLM-005-008` | Negative Gluing Defect (NGD) | `[DEFINITION]` | `N/A` | None | Exact rational definition in `mod_authority_gap_core.py`. |
| `CLM-005-009` | Authority Coverage Ratio (ACR) | `[DEFINITION]` | `N/A` | None | Exact rational metric in `mod_authority_gap_core.py`. |
| `CLM-005-010` | Rate Asymmetry Backlog | `[PROVEN, CONDITIONAL]` | `AuthorityGap.lean` | `backlog_positive`, `backlog_example`, `verified_share` | Python `calculate_backlog_accumulation` on (50, 10, 12) and (10, 3, 1). |
| `CLM-005-011` | Exactness Fraud Criterion | `[PROVEN, CONDITIONAL]` | `AuthorityGap.lean` | `missing_descent_is_refuted`, `nonzero_residual_is_refuted`, `scoped_residual_is_outside_this_rule` | Python `evaluate_exactness_fraud_criterion` on the missing-descent packet and the nonzero-residual packet. |
| `CLM-005-012` | Seven-Layer Control Stack | `[DEFINITION]` | `N/A` | None | Architectural pipeline implemented in reference code. |
| `CLM-005-013` | Content/Authority Boundary | `[POLICY RULE]` | `N/A` | None | Defensive engineering rule against prompt-injection escalation. |
| `CLM-005-014` | Minimal Observer Packet Standard | `[OPERATIONAL RULE]` | `N/A` | None | Standard specification for verification handoffs. |

---

## Falsifier Check: `LEAN_TOY`-as-`MECHANIZED`

- **Mechanized proved rows:** CLM-005-007, CLM-005-010, CLM-005-011.
- **Prose rows:** the definitions, policy rules, and operational rules. They are not labeled proved.
- **Result:** The three proved rows name compiling Lean declarations. The other rows are not sold as Lean theorems.
