# Lesson 950.06 -- 1. Multi-Step Interactive Proof Search under Layer 3 Governance

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_950_06_topology50_proof_search.ipynb](../notebooks/lesson_950_06_topology50_proof_search.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 10 - Interactive Theorem Proving: The Topology-50 Benchmark

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Multi-Step Proof Search, Retraction Rollbacks, and Machine-Checked Point-Set Topology*

---

## 1. Multi-Step Interactive Proof Search under Layer 3 Governance

When language models attempt multi-step formal proofs (e.g. in Lean 4), an un-retracted bad tactic contaminates the proof state, leading to inevitable proof failure.

The **Layer 3 Governor** manages proof search as an interactive state tree:
1. **Candidate Tactic Proposal**: The model proposes next tactic $\tau$ at state $s_t$.
2. **Host Lean 4 Verification**: The host sends $\tau$ to the Lean 4 REPL/kernel.
3. **Retraction on Refusal**: If Lean rejects $\tau$ (error/syntax error), the governor rolls back to $s_t$ without state contamination.
4. **Descent Condition**: Admitted moves must strictly reduce remaining open proof goals.

### The Topology-50 Benchmark
Paper 032 tested this governor across **50 held-out point-set topology theorems** in Lean 4:
- **Stored receipt count**: the checked-in JSON says `governed_solved` 50 and `ungoverned_solved` 0. Lean was not re-run, and this page does not call that count a proof.
- **Tactic Verification Rate**: **53.91%** valid tactic proposals.
- **Retraction Frequency**: **46.09%** invalid proposals intercepted and rolled back.
- **Ungoverned Baseline**: the receipt field `ungoverned_solved` is 0. That stored count is not a proof.

## 2. The Retraction Mechanism in Action

Watch how the Layer 3 Governor isolates errors:

```
[Goal: X is open -> compl(X) is closed]
  |
  +-- [Attempt 1: 'apply False.elim'] --> REJECTED by Lean 4!
  |   (Governor triggers RETRACT: state rolled back, no contamination)
  |
  +-- [Attempt 2: 'exact is_closed_compl hX'] --> ADMITTED!
      (Goal closed: Q.E.D.)
```

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - The notebook counts rows in the checked-in receipt. It does not re-run Lean.
>
> **CANNOT-Show**:
> - Does not prove that the governor can solve open mathematical conjectures (e.g. Riemann Hypothesis).

## 4. Student Exercises

### Exercise 10.1: Retraction Dynamics
Why did the ungoverned baseline achieve 0/50 on multi-step proofs despite having access to the same language model?

<details>
<summary><b>Click to reveal solution</b></summary>
Because without a host governor to intercept errors and roll back state, the first invalid tactic proposal corrupts the proof script. The language model then tries to "fix" the error in subsequent turns, entering a compounding hallucination spiral that exhausts generation tokens without closing the goal.
</details>

## 5. Anchors

- **Paper 032 Sections**: §9.1–§9.4
- **Ledger IDs**: `PO032-C64` through `PO032-C70`
- **Code**: `papers/032.../code/interactive_lean4_governor.py`
- **Lean 4**: `lean4/Topology50.lean`
- **Audit Receipt**: `papers/032.../code/topology50_benchmark_receipt.json`

## Anchors

- Former notebook: `10_interactive_lean4_governor_topology50`
- The code checks one finite example. It is not a general proof.
- Open gap: Lean was not re-run. The check reads the checked-in Topology-50 receipt and counts its stored rows.

Tower files for this sitting:

- [research/mssn_sn_tower/_theory/README.md](../../../../../research/mssn_sn_tower/_theory/README.md)
- [research/mssn_sn_tower/_theory/03_the_symbol_game.md](../../../../../research/mssn_sn_tower/_theory/03_the_symbol_game.md)
- [research/mssn_sn_tower/_theory/09_authority_fences.md](../../../../../research/mssn_sn_tower/_theory/09_authority_fences.md)
