# Mode 06: Chain-of-Thought Boundary Probes & Pre-Declaration Contracts

**Mode ID:** 6  
**Cluster:** Cluster I: Carrier & Representation  
**AuthorityEffect:** None  

## Overview

Mode 06 inspects intermediate reasoning traces, scratchpads, and input boundaries to detect ungrounded heuristic jumps, missing declarations, and category errors before calculation occurs.

## Integration with Demo 001 & ADR

Drawing from `demo_001/round_1/p_star_02_r1_carrier.yaml`, `demo_001/round_1/prompt_result_001.md`, and `adr_reuse_decision.md`:

### 1. Pre-Declaration Boundary Probes (Strategy R1)

Before a model is permitted to evaluate any computational step, a boundary probe requires explicit declaration of:
1. **Carrier Space:** Topological substrate ($K, \mathbb{R}, \mathbb{Z}$).
2. **Domain Measure:** Measure space ($dx$, counting measure $\mu_{\text{count}}$, or differential form).
3. **Operator Typing:** Distinguishing continuous antiderivatives from discrete coboundary differences.
4. **Boundary Verification:** Identifying whether interval endpoints or domain elements are discrete or continuous.

### 2. Boundary Check Receipt Schema

Model outputs must report explicit boundary integrity metrics:
```yaml
boundary_check:
  local_valid: false
  global_valid: false
  boundary_violation: true
  preserved:
    - seed_question
    - policy_boundary
    - evidence_ceiling
    - terminal_target
    - allowed_transforms
```
If `boundary_violation: true`, downstream computation must halt immediately (fail-closed).

### 3. DSPy Contract-Bound Adapter Fence

When utilizing DSPy or teleprompter optimizers to probe prompt variations:
- The adapter serves as a candidate generator and evaluator only.
- Optimizer scores cannot grant release authority or bypass boundary validators.
- All candidate traces must pass through strict `RewriteRequest` and JSON Schema validation.
