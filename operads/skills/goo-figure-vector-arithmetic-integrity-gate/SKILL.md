---
name: goo-figure-vector-arithmetic-integrity-gate
description: "Check preprint figures show consistent vector arithmetic, match residual equations and pass coordinate tests."
status: canonical
operad_source_colours: ["Paper", "Code"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [meta, gate]
---

# goo-figure-vector-arithmetic-integrity-gate

**AuthorityEffect:** None. This gate refuses. It does not mint, promote, or alter doctrine.

## The single rule

> Visual vector figures must satisfy exact mathematical vector arithmetic ($r = x + d_0 f$) and export coordinate dictionaries validated by automated unit tests.

## Invariants

1. **Displayed Arithmetic Consistency**: Plotted arrows, coordinate labels, and algebraic claims in figure captions must agree with exact numerical vector arithmetic.
2. **Residual Equation Adherence**: Plotted residual vectors must satisfy the governing coboundary equations ($r = x + d_0 f$) without geometric distortion.
3. **Exported Coordinate Dictionaries**: Figure scripts must export explicit data mappings (`FIGURE_COORDINATES`) accessible to test runners.
4. **Active Vector Unit Tests**: Unit tests must assert coordinate geometry, vector sums, and non-degeneracy, forbidding tests that merely check file size or generation exit code.

## Verification

```bash
# Run figure coordinate and vector arithmetic assertion suite
pytest coda_atlas/F005_coda/foc/code/tests/test_foc_generate_figures.py
```
