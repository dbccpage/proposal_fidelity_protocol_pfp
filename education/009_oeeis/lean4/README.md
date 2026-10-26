# Lean 4 Proof Kernels — Epistemic Immune System (EIS)

**AuthorityEffect:** None.  
**GenesisEffect:** None.

Mechanized Lean 4 proof kernels, inductive definitions, and verified theorems for the Epistemic Immune System (EIS).

## Formalized Invariants

1. **Antigen vs. Self-Specification Demarcation:** Distinct inductive structures `Antigen` (untrusted candidate stimulus) and `SelfSpec` (protected core invariants).
2. **Central Tolerance & Negative Selection:** Constructive `checkCentralTolerance` destroying self-reactive antibodies; proved by theorem `thymus_rejects_exact_self_match`.
3. **Two-Signal Activation Model:** Inductive states `ActivationState` verifying that full immune activation strictly requires both primary pattern recognition and co-stimulatory danger signal (`full_activation_requires_danger`).
4. **Regulatory T-Cell (Treg) Suppression:** Anergy status suppressing hyperactive guards without system destabilization.
5. **Fail-Closed Boundary Receipts:** Typed `RefusalReceipt` emission with verified `AuthorityEffect: None` invariant (`refusalReceipt_authority_none`).

## Build and Elaboration

To elaborate and check the package:

```bash
cd lean4
lean EpistemicImmuneSystem.lean
# or using Lake
lake build
```
