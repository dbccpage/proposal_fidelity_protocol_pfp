packet_type: adapter
authority_effect: None
carrier: Lean theorem statements and proof files under engine/lean4/ (C⁰)
primary_residual: unproven proof gaps, unverified lemmas, contradiction in axioms (Q¹)
in_scope_repairs: Lean proof construction, definitional equality, lemma application (d₀)
deferred_residuals: proof obligations in downstream papers, meta-logic extensions
seal_condition: Lean build clean, print axioms audit, and terminalize_row Decision::Certified on proof obligation rows

Proof Obstruction Packet — ODP adapter for proof / Lean work
============================================================

**Date:** 2026-06-20
**Status:** ADAPTER of `core_obstruction_packet_standard.md` for proof work.

Thesis
------

**A proof is obstruction removal.** A Lean file is **not** "a list of theorems" — it is a **residual-killing ledger**: each statement either closes a C¹ defect by an allowed derivation (B¹), names an irreducible obligation (Q¹), or licenses a lift (Λ).

Field mapping
-------------

| ODP field | Proof instance |
|-----------|----------------|
| Carrier | the claim + its declared definitions/context window |
| C⁰ | definitions, hypotheses, local lemmas |
| d₀ | allowed derivation from definitions/hypotheses (the proof step) |
| C¹ | proof gaps, claim defects, unproven transitions |
| ZeroRel | definitional equality / proven equivalence |
| B¹ = im(d₀) | defects removable by **existing** lemmas |
| Q¹ = C¹/im(d₀) | **irreducible proof obligations** |
| d₁ | compatibility of obligations across contexts |
| C² | the cross-context compatibility layer |
| Γ₂ | contradiction / failed closure / **noncommuting proof square** |
| Φ₁ | the mass of irreducible obligations under the declared rigor norm |
| observer / norm | the declared rigor standard (prose vs Lean-mechanized; axiom budget) |
| Λ | add definition, lemma, witness, or stronger structure |
| DDA op | the transformation class (lemma applied, definition added, structure strengthened) |
| terminal | **theorem** / **refusal** / **oracle-needed** / **open residual** |

Bindings
--------

* C•/d• : `core_homology` (FOC); the Lean kernel (`lake build`, `#print axioms`) is the **mechanized observer** for Φ₁ (axiom-free ⇒ Φ₁ sealed under the mechanized observer, then recorded by terminalizer/certifier if promoted; a clean `#print axioms` does not itself mint platform authority).
* terminal seal : the terminal status is **sealed by the terminalizer / certifier** (`core_sweep_kernel::terminalize_row` / `core_certifiers::certify_checked_packet`), never by a markdown file. The encyclopedia entry (`entries/<layer>/enc-*.md`) is the durable **record** of that sealed status (PROVEN / CONDITIONAL / MECHANIZED / OPEN) — a recorded terminalized residual, not the seal itself.
* promotion gate : `/paper-proof-signoff` + `/paper-release` enforce the ODP promotion checklist for a paper; a theorem claim is not promoted without carrier/C⁰/C¹/Q¹/terminal.

What a Lean file must report (not "theorems proved")
----------------------------------------------------

For each load-bearing result: the **obligation it kills** (Q¹ entry → ExactRepair), or the **residual it carries** (ClosedSurvivor / OpenResidual), or the **contradiction it exposes** (Γ₂ ≠ 0 → ActiveClosureFailure / Refusal). `#print axioms` clean ⇒ the obligation is sealed under the empty-axiom observer.

Terminal classification (proof)
-------------------------------

`theorem` = ExactRepair (Q¹ closed under ZeroRel) · `open residual` = ClosedSurvivor/OpenResidual (Q¹ nonempty, Γ₂ = 0) · `contradiction` = ActiveClosureFailure (Γ₂ ≠ 0) · `oracle-needed` = resolution outside the declared carrier · `refusal` = real obstruction, no licensed lift.

Promotion checklist (proof artifact)
------------------------------------

carrier? · C⁰ (defs/hyps)? · C¹ (gaps)? · d₀ (allowed derivation)? · ZeroRel? · Q¹ (obligations) declared/refused? · d₁/C² (cross-context) or out-of-scope? · Φ₁/Γ₂ (or marked prose-only)? · Λ only if licensed? · terminal status? · DDA op recorded?
