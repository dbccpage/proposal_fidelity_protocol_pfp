# Mode 17: Polygraph Confluence & Multi-Examiner Consensus

**Mode ID:** 17  
**Cluster:** Cluster IV: Dialectical & Adversarial  
**AuthorityEffect:** None  

## Overview

Mode 17 executes parallel multi-examiner evaluations across candidate models or verification nodes to audit whether independent interpretations reach deterministic confluence or bifurcate due to ungrounded assumptions.

## Integration with Demo 001 & ADR

Drawing from `demo_001/round_1/p_star_03_r4_collision.yaml` and `demo_001/round_1/prompt_result_001.md`:

### 1. Multi-Examiner Divergence Audit

When testing prompt fidelity across multiple examiners or reasoning paths:
- **Examiner 1 (Smooth / Calculus prior):** Adopts continuous assumption $\implies 50$.
- **Examiner 2 (Discrete / Arithmetic prior):** Adopts integer counting assumption $\implies 55$.
- **Examiner 3 (Restrained SymSys Auditor):** Detects missing carrier license $\implies \text{refusal / null}$.

### 2. Polygraph Consensus Invariant: No Majority Vote on Assumptions

In standard ensemble systems, models often vote by majority. Mode 17 strictly forbids majority resolution of undeclared assumptions:
1. **Divergence as Witness:** When two examiners produce distinct values ($50 \ne 55$) without explicit domain licensing, the divergence serves as a formal witness of underdetermination.
2. **Consensus Monad:** The polygraph consensus engine collapses all divergent branches into a single fail-closed verdict: `decision: refuse_missing_carrier`.
3. **Receipt Sealing:** The polygraph receipt records both candidate branches and seals the refusal outcome into the run manifest.
