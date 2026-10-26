# Lean 4 Proof Kernels — Prompt Civilization & Lamarckian Evolution

**AuthorityEffect:** None.  
**GenesisEffect:** None.

Mechanized Lean 4 proof kernels, inductive definitions, and verified theorems for Prompt Civilization and Lamarckian Evolution.

## Formalized Invariants

1. **Carrier Structures:** Constructive definitions for `Genotype`, `Phenotype`, and `Individual`.
2. **Lineage DAG Semantics:** Strictly directed causal edges `LineageEdge` asserting generation monotonicity ($g_{\text{parent}} < g_{\text{child}}$).
3. **Pareto Dominance Irreflexivity:** Verified theorem `paretoDominates_irreflexive` showing that no phenotype dominates itself under multi-objective fitness.
4. **Lamarckian Retro-Inheritance:** Functional update `lamarckianUpdate` capturing runtime reflection feedback written back to prompt genotypes.
5. **Claim Hygiene Gate:** Structured `ClaimHygieneReceipt` ensuring empirical evaluations remain bounded by measured latency, token cost, and correctness without unwarranted extrapolation.

## Build and Elaboration

To elaborate and check the package:

```bash
cd lean4
lean PromptCivilization.lean
# or using Lake
lake build
```
