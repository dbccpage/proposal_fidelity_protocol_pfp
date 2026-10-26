# Mode 14: Fail-Closed Typed Refusal as the Winning Move

**Mode ID:** 14  
**Cluster:** Cluster IV: Dialectical & Adversarial  
**AuthorityEffect:** None  

## Overview

Mode 14 establishes that when faced with an ungrounded, ambiguous, or out-of-bounds problem, the sole winning move is the immediate, deterministic emission of an explicit typed refusal rather than guessing or computing a plausible answer.

## Integration with Demo 001 & ADR

Drawing from `demo_001/round_1/p_star_04_r8_refusal.yaml`, `stages/stage_1_compression_gate.yaml`, and the empirical receipt in `demo_001/round_1/prompt_result_001.md`:

### 1. Stage 1 Compression Gate Contract

When a problem payload enters the PFP pipeline, Stage 1 forces an admission decision before any evaluation stage can execute:

```yaml
admission_proposal:
  status: refuse | needs_declaration | admit
  missing_declarations:
    - "Carrier Space (R vs Z)"
    - "Integration Measure (dx vs counting)"
    - "Domain Typing (Interval [0,10] vs Set {0..10})"
  reason: "Undeclared carrier forces unlicensed continuous lift or discrete coercion."
```

### 2. Empirical Verification from Demo 001

In Demo 001, when queried with the flawed integration seed, candidate models evaluated under Mode 14 produced the canonical winning move:

```yaml
numerical_result:
  selected_value: null
  decision: refuse_missing_carrier
  reason: "SPK-001 requires explicit carrier and measure licenses; selecting 50 or 55 would silently promote an unlicensed continuous or discrete interpretation."
```

### 3. Core Operational Invariants

1. **Zero Partial Computation:** The output value must be strictly `null`. Emitting a calculated number (e.g. `50` or `55`) alongside a disclaimer is an immediate failure.
2. **Typed Error Codes:** Refusals must use declared enumerations (`refuse_missing_carrier`, `needs_declaration`, `ERR_UNDECLARED_CARRIER`).
3. **State Immutability:** System state and downstream stage ledgers remain 100% unmutated upon refusal.
