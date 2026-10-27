packet_type: adapter
authority_effect: None
carrier: Rust source code files and modules under engine/crates/ (C⁰)
primary_residual: failing unit/integration tests, Clippy warnings, contract violations (Q¹)
in_scope_repairs: cargo test, clippy fixes, local refactorings (d₀)
deferred_residuals: downstream crate integration, API breaking changes, performance targets
seal_condition: cargo test green, Clippy clean, and terminalize_row Decision::Certified

Rust Obstruction Packet — ODP adapter for Rust / code work
==========================================================

**Date:** 2026-06-20
**Status:** ADAPTER of `core_obstruction_packet_standard.md` for Rust work.

Thesis
------

**A Rust feature is obstruction management over executable carriers.** A PR does **not** say "implemented feature." It reports an obstruction removed.

Field mapping
-------------

| ODP field | Rust instance |
|-----------|---------------|
| Carrier | the touched crate/module/contract set |
| C⁰ | current structs, traits, contracts, schema fields |
| d₀ | permitted refactor / repair operation |
| C¹ | failing tests, missing invariants, boundary violations |
| ZeroRel | type/trait equivalence; contract-schema equality |
| B¹ = im(d₀) | failures removable by **local** refactor |
| Q¹ = C¹/im(d₀) | failures **not** removable by local refactor |
| d₁ | integration coherence across crates/modules |
| C² | the cross-crate integration layer |
| Γ₂ | **cross-boundary breakage** (a green crate, red workspace) |
| Φ₁ | residual-defect mass after allowed refactor (under the test/observer norm) |
| observer / norm | the test suite + clippy `-D warnings` + the contracts v1 gate |
| Λ | new trait, new carrier, new validator, **new packet family** |
| DDA op | recorded transformation class (extract module, add trait, lift carrier) |
| terminal | **Repaired** / **Pending** / **Deferred** |

Bindings
--------

* C⁰ schema : `core_contracts` (the v1 corpus gate is a closure check on C⁰).
* C¹ : the failing test set; `core_epk::Delta_E` is the **evaluator-defect** C¹ instance (local-green/global-red = a nonzero `Γ₂` across the composition boundary).
* Λ : `core_lifts`; preservation witness : `core_discrete_deformation_algebra` (the DDA op records what the lift preserved).
* terminal seal : `core_sweep_kernel::terminalize_row` (sealed) — a "feature accepted" is a terminalized record, author-blind; **never** free-stamped.
* diagnostic-only : the engine's diagnostic types carry `authority_effect = None`; only the terminalizer/certifier mints.

What a PR must report (the obstruction-removed block)
-----------------------------------------------------

```
obstruction removed:
  Φ₁ before:   <residual-defect mass>
  Φ₁ after:    <residual-defect mass>
  Γ₂ before:   <cross-boundary breakage>
  Γ₂ after:    <cross-boundary breakage>
  lift used:   <Λ, or none>
  preservation witness: <what the DDA op preserved>
  terminal status (A4):
    current:        Pending | LiftNeeded
    target:         Repaired | Deferred
    seal condition: <concrete test run or certifier check that flips current to target>
```
(For a v1 where Φ₁/Γ₂ are not yet type-pinned: report C¹-count before/after + the integration check, and mark Φ₁/Γ₂ "estimate".)

Terminal status alignment
-------------------------

* **Repaired**: ExactRepair (C¹ closed by allowed refactor; Γ₂ = 0).
* **Pending**: ClosedSurvivor (stabilized, awaiting certifier/authority seal; Γ₂ = 0).
* **Deferred**: routed to a successor packet (such as a Phase-B packet).

Promotion checklist (Rust module claim)
---------------------------------------

carrier? · C⁰ (types/contracts)? · C¹ (failing tests/invariants)? · d₀ (allowed refactor)? · ZeroRel? · Q¹ declared/refused? · d₁/C² (integration) or out-of-scope? · Φ₁/Γ₂ (or estimate)? · Λ only if licensed? · terminal status? · DDA op recorded?
