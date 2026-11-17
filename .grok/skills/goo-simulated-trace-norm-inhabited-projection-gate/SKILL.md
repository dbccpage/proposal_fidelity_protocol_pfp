---
name: goo-simulated-trace-norm-inhabited-projection-gate
description: "Evaluates simulated trace-norm oblique projections and verifies dual witness certificates on inhabited state spaces."
status: canonical
operad_source_colours: ["Paper", "Audit"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [meta, gate]
---

# goo-simulated-trace-norm-inhabited-projection-gate

**AuthorityEffect:** None. This gate refuses. It does not mint, promote, or alter doctrine.

## The single rule

> Trace-norm oblique projections $P_\rho^{\|\cdot\|_1}(L) = \operatorname{argmin}_{X \in T_\rho M} \|X - L\|_1$ and dual witness certificates $W \in \partial \|\cdot\|_1(Q)$ must be evaluated on non-empty, inhabited tangent spaces with $\|W\|_\infty \le 1$ and $\langle W, X \rangle = 0$.

## Invariants

1. **State Inhabitation Guarantee**: Projection and duality solvers must verify non-vacuous state space and tangent bundle inhabitation prior to certificate generation.
2. **Exact Duality Gap Bounds**: Duality gaps between primal trace-norm objective and dual witness certificate must meet exact rational tolerance bounds.
3. **Subgradient Witness Properties**: The dual witness $W$ must satisfy operator norm bounds $\|W\|_\infty \le 1$ and exact orthogonality $\langle W, X \rangle = 0$ for all $X \in T_\rho M$.

## Verification

```bash
# Verify trace-norm projection and dual witness certificates
pytest -k test_trace_norm_projection
```
