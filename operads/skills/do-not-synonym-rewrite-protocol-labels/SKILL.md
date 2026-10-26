---
name: do-not-synonym-rewrite-protocol-labels
description: Editorial vocabulary changes must not rename terminal values, schema fields or other protocol identifiers.
operad_source_colours: ["Paper", "Contract"]
operad_target_colour: "Paper"
operad_arity: 2
operad_residual: "unknown"
---

# Do Not Synonym-Rewrite Protocol Labels

**AuthorityEffect:** None.

## Purpose & Invariant

Editorial vocabulary changes must not rename terminal values, schema fields, or other protocol identifiers. Preserve their literal spelling, or introduce an explicit versioned mapping with matching code and tests.

## Anti-Pattern Context

When editing prose, manuscripts, or tables, agents or human authors may attempt to synonymize or "polish" protocol terms—for example, changing a checked loss trap terminal report from `Impossible` to `Unrealizable` in a manuscript table without updating or mapping the underlying protocol and unit test assertions. This creates immediate semantic divergence between the specification and implementation.

## Enforcement & Verification Check

1. **Exact Protocol Literal Alignment:**
   - Any protocol terminal identifier (e.g. `Impossible`, `Admitted`, `Refused`, `NoLoss`) declared in the specification must match the implementation byte-for-byte.
   - If an editorial synonym or user-facing display label is desired, an explicit, versioned display-label mapping dictionary or function must be introduced and tested.

2. **Regression Check:**
   - Run `code/tests/unit_tests/test_progress_observation.py::test_loss_stall_and_successful_zero_cost_terminal_have_distinct_reports`.
   - Compare emitted labels with table WDP-CHS-D03 in the manuscript. Require exact matches or an explicit documented alias for every renamed label.
