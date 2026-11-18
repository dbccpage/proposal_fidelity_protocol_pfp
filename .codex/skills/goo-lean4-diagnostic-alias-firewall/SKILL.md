---
name: goo-lean4-diagnostic-alias-firewall
description: "Remove Lean 4 compatibility aliases that conflate diagnostic states with authorization decisions."
status: canonical
operad_source_colours: ["Proof"]
operad_target_colour: "Proof"
operad_arity: 1
operad_residual: "unknown"
families: [meta, gate]
---

# goo-lean4-diagnostic-alias-firewall

**AuthorityEffect:** None. This gate refuses. It does not mint, promote, or alter doctrine.

## The single rule

> Formal Lean proof modules must not retain backward-compatibility abbreviations (e.g. `abbrev Survivor := CoherentResidual`) that conflate mathematical trichotomy states with operational decisions.

## Invariants

1. **Epistemic Layer Separation**: Pure mathematical diagnostic trichotomy states (`ExactRepair`, `CoherentResidual`, `NonclosedDefect`) must remain strictly isolated from operational authorization choices (`Survivor`, `OpenObstruction`).
2. **Elimination of Deprecated Aliases**: Backward-compatibility aliases (`abbrev Survivor := ...`, `abbrev Open := ...`) must be fully removed from production Lean modules.
3. **Hypothesis & Theorem Discipline**: Lemma arguments and theorem names must explicitly reflect canonical mathematical definitions (e.g. `hcoherent`, `hnonclosed`, `nonclosed_of_gamma_pos`).

## Verification

```bash
# Verify clean Lean 4 compilation and axiom cleanliness
lake build
lake env lean --run coda_atlas/F005_coda/foc/lean4/coda_foc_20_terminal_completeness.lean
```
