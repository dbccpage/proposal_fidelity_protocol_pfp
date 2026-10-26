---
name: goo-quotient-universal-factor-uniqueness-gate
description: "Check quotient models return honest L1 distances, kernel inclusion factorizations and unique quotient factors."
status: canonical
operad_source_colours: ["Proof", "Code"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [meta, gate]
---

# goo-quotient-universal-factor-uniqueness-gate

**AuthorityEffect:** None. This gate refuses. It does not mint, promote, or alter doctrine.

## The single rule

> Computational quotient projections and cochain classifiers must return honest $L^1$ quotient distances $d(x, C) = \|x - Cx\|_1 = \|\operatorname{res}(x)\|_1$, assert kernel inclusion $\ker(C) \subseteq \ker(f)$, and verify universal factor uniqueness.

## Invariants

1. **Non-Degenerate Quotient Metric**: Quotients mediating through idempotent endomorphisms $C$ must compute the true $L^1$ distance $d(x, C) = \|x - Cx\|_1$, forbidding degenerate zero returns on non-trivial residuals.
2. **Kernel Factorization Condition**: Implementations asserting that observable $f$ factors through canonical projection $\pi_C$ must explicitly verify kernel inclusion $\ker(C) \subseteq \ker(f)$.
3. **Universal Factor Uniqueness**: Universal quotient factors must be mathematically unique and verified both computationally and via Lean 4 formalization.

## Verification

```bash
# Run quotient factor uniqueness and kernel tests
pytest coda_atlas/F005_coda/a/code/tests/test_coda_a_core.py
```
