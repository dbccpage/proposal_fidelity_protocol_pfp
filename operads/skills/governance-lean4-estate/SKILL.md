---
name: governance-lean4-estate
description: "Consolidated Lean 4 Lake elaboration, axiom honesty, and anti-toy mechanization gate."
operad_source_colours: ["Proof", "Code"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [governance, lean4]
---

# governance-lean4-estate

AuthorityEffect: None.

## The single rule

> Formal Lean 4 evidence must be mechanically elaborated by lake build, remain strictly free of axioms outside {propext, Quot.sound, Classical.choice}, and verify domain invariants rather than trivial toy equivalences. The constructive restriction belongs to the separate Genesis repository, not this monorepo; sealed historical reports retain their recorded policy.

## Consolidated Invariants

1. **Continuous Lake Elaboration**: All registered Lean packages must build cleanly with zero elaboration errors and zero non-whitelisted axioms (`goo-lean4-estate-lake-elaboration-gate`).
2. **Elaboration Over Assertion**: Proof claims must be elaborated proof terms rather than asserted constants or ungrounded `sorry` escapes (`goo-lean4-evidence-gate`).
3. **Anti-Toy Defense**: Formal models must map to actual domain invariants (typing, resource bounds, authority descent) rather than tautological substitutions (`goo-lean4-strict-mechanization-guard`).
4. **Canonical Locus Hygiene**: Lean research programs must reside in canonical directories (`core_research/programs/` and `lean4/research_programs/`) without ambient path escapes (`goo-research-lean4-canonical-locus-guard`).
5. **Provenance Receipt Attestation Fallback**: When local `lake build` is obstructed by upstream community barrel or network isolation failures, proof status may be certified via `{paper_folder}/lean4/PROVENANCE.md` provided all local `*.lean` proof files match their recorded SHA256 digests, the receipt certifies exit code 0, and scans confirm zero `sorry`/`admit` stubs.
6. **Root Lean 4 Package Authority (`MssnSnTower`)**: The repository-level Lean 4 Lake package resides canonically at `lean4/` (`lakefile.lean`, `lake-manifest.json`, `lean-toolchain`). Moving proof models to nested subdirectories or duplicating Lake configurations outside canonical boundaries is prohibited.
7. **Abstract Structure Inhabitation & Domain Contract Pure Axiom Discipline**: When declaring abstract mathematical carriers (e.g. `Vector6`), prefer `structure T where carrier : Unit := () deriving Inhabited, Nonempty` over bare `opaque T : Type` to avoid Lean 4 elaboration synthesis failures (`failed to synthesize instance Inhabited`) while preserving complete representation opacity. Never assert ungrounded domain properties as kernel axioms; define explicit typed Domain Contracts (`def BasisVectorMUContract : Prop := ...`) and pass them as explicit hypotheses, ensuring formal theorems compile cleanly under standard foundational axioms (`[propext]`, zero custom axioms).
8. **Hermetic Offline Lake Builds & Anti-Network Git Clone (`ANTI-LAKE-OFFLINE-NETWORK-CLONE`)**: Lake configurations must be strictly hermetic and offline, free of remote git dependencies (e.g. remote Mathlib4) that trigger network clone failures during local CI sweeps or offline execution. All formal mechanizations must build from core Lean 4 and standard axioms `{propext, Quot.sound, Classical.choice}` or use locally vendored caches.
9. **Audited Source Continuity & Post-Audit Mutation Defense (`ANTI-POST-AUDIT-MUTATION-RACE`)**: Audit receipt emitters and snapshot publishers must record and carry the exact audited source hash map from census collection through to artifact emission. Snapshot staging must validate every byte against that audited map, failing closed with `LEAN_SOURCE_CHANGED` if source files were modified post-census.
10. **Sandboxed Verification Engine & Statement Equality (`LakeSandboxAdapter`)**: Formal challenges evaluate submissions through `LakeSandboxAdapter` (`core_symbol_game::lean_verify`), enforcing AST-level comment/string-safe forbidden construct scanning (`sorry`, `admit`, `axiom`), judge harness statement equality check, and declared axiom set containment before emitting `LeanVerificationReceiptV1`.
11. **Level Engine Sequential Compilation & Axiom Census Audit (`LEVEL-ENGINE-LEAN-AUDIT`)**: The Level Engine certificates under `lean4/research_programs/level_engine` (52 generated certificate modules, `ExactRat`, and `AxiomReport`) must compile sequentially via `symbol-game level-engine --workspace . --lean-root lean4/research_programs/level_engine lean build` (or `lake build +<Module>`). The formal axiom census (`AxiomReport.lean`) evaluates its 1,019 declared targets against the standard foundational policy `{propext, Quot.sound, Classical.choice}` with zero `sorryAx` or custom axioms. Live spec validation still requires the verified read-only pinned vendor checkout (`dbccpage/19L57G1@b368f28c`) per contract `RR-PIN`; this policy correction does not rewrite historical evidence or alter that pin.

## Verification Requirements

Run the Lean 4 estate elaboration and axiom audit:

```bash
python operads/skills/governance-lean4-estate/scripts/check_lean4_estate.py
```
