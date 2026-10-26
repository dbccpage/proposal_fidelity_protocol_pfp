---
name: goo-pseudometric-separation-claim-gate
description: "Block point-equality claims from distance zero unless a metric separation axiom is stated."
status: canonical
operad_source_colours: ["Proof", "Audit"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [meta, gate]
---

# goo-pseudometric-separation-claim-gate

**AuthorityEffect:** None. This gate refuses. It does not mint, promote, or alter doctrine.

## The single rule

> A collision bound $\operatorname{dist}(q(x), q(y)) \le 2\varepsilon$ reaching $\varepsilon = 0$ implies equality $q(x) = q(y)$ if and only if the metric separation axiom ($\operatorname{dist}(a, b) = 0 \implies a = b$) is explicitly assumed, or the claim is explicitly stated on the metric quotient $Y/{\sim_0}$.

## Invariants

1. **Pseudometric vs Metric Distinction**: Zero distance in a pseudometric space does not imply identity of underlying elements. Distinct states may reside at distance 0.
2. **Explicit Separation Declaration**: Claims deriving element equality from vanishing distance must explicitly declare the metric separation hypothesis.
3. **Formal Verification Typing**: In Lean 4 formalizations, bounds over pseudometrics must type against `PseudoMetricSpace`, and equality must be scoped to the quotient or require `MetricSpace`.

## Verification

```bash
# Run countermodel and metric separation tests
pytest -k test_pseudometric_zero_error_countermodel
```
