# Symbol Game kernel (Lean 4)

**AuthorityEffect:** None.

This folder holds the Lean 4 kernel of the Symbol Game. It covers the modules that this repository's curriculum binds as Symbol Game: rows L043_03, L043_05, L043_09 and L043_10 of `education/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md`, and the ENC-0890 to ENC-0917 encyclopedia entries.

Each module was copied byte for byte from `dbccpage/the_symbol_game` at commit `0a5567c9a`. That repository keeps its own copies as working copies, because its code still imports them. `provenance.json` records, for each file, the source, the SHA-256, the score, the PFP document that binds it, and the caveats on that binding.

## What is here

| Module | Score | Role |
|---|---|---|
| `Sweeper` | L2D | terminal gate; operation output is not authority |
| `TowerZeta` | L2D | positive-delta tower profile |
| `ShadowBoundary` | L3D | shadow collision and non-factorization |
| `TypedPacketShadow` | L2D | typed packet shadow (L043_03) |
| `FidelityAdequacy` | L2D | fidelity adequacy (L043_05) |
| `LiftPatchSemantics` | L2D | lift patch (L043_10) |
| `OperationTreeFold` | L2D | operation fold (L043_09) |
| `SLevel` | L2D | import of the five modules above that need it |
| `PrimitiveDifference` | L3D | import of `ShadowBoundary`; also the Lean anchor of `code/rust/core_homotopy_type_theory` |

Scores follow `SCORING.md` v2.0.0: a level, then the weakest of the five gates. They come from the re-homing review of 2026-10-27, which made one reviewer pass and two adversary passes. **No module here reaches the L4D floor of `SCORING.md` §1.5.** Since 2026-10-27 `lean4/**/*.lean` is in the Lean 4 population of `governance/policy.json`, and its 11 `.lean` files are grandfathered in `governance/baseline.json` at the bytes copied in PR #34. Any edit to one of them ends that exemption, and the edited file then needs a completed `.contract.score.json` companion at the L4D floor.

Not moved, and why:

- `Demo3ProtocolInvariants` is MSS-N, not Symbol Game. Its namespace is `MSSN.Demo3Protocol`, and the finite quantum mechanics repository already holds it, imported as MSS-N. `papers/completion_receipt.json` still pins `lean4/Demo3ProtocolInvariants.lean`; that receipt was made in a `the_symbol_game` checkout.
- `Family` is L2D, but its only import, `Expressivity`, is L1D.
- `ShadowFactorization`, `SnSymbolGameAndPackets`, `SymbolGame`, `Lib`, `TokenFrontier` and `AntimorphicInvolution` are L1D.
- `FiniteConsequences`, `LpWeakDuality` and `TerminalizerPolicy` have no grade, because their builds did not complete.

## Build and audit

The toolchain is core Lean `v4.35.0`, with no Mathlib and no other package.

```bash
cd lean4
lake build                      # library SymbolGameKernel, nine roots
lake env lean AxiomCensus.lean  # every constant, and every theorem's axioms
```

`AxiomCensus.lean` checks every constant the compiled environment assigns to the nine roots: theorems, definitions, instances, generated lemmas and internal auxiliary proofs. It fails in two cases:

- a module declares an `axiom`, even one nothing uses;
- a constant depends on an axiom outside {propext, Classical.choice, Quot.sound}, `sorryAx` included.

`axiom_report.txt` is its output from 2026-10-27:

- 1144 constants checked;
- 375 non-internal theorem constants, 281 of them with no axioms. These are the declared theorems plus generated lemmas and Prop-valued structure fields;
- across all constants, the axioms used are `propext` and `Quot.sound` only.
