# Symbol Game kernel (Lean 4)

**AuthorityEffect:** None.

This folder holds the Lean 4 kernel of the Symbol Game. These are the modules that this repository's curriculum and papers bind as Symbol Game:

- `education/004_oepfp/levels/meta_03_symbol_game_proof_ledger.md` (rows L043_03, L043_05, L043_09 and L043_10);
- the ENC-0890 to ENC-0917 encyclopedia entries;
- `papers/completion_receipt.json`, which pins `lean4/Demo3ProtocolInvariants.lean` by SHA-256. The copy here has those bytes.

Each module was copied byte for byte from `dbccpage/the_symbol_game` at commit `0a5567c9a`. That repository keeps its own copies as working copies, because its code still imports them. `provenance.json` records, for each file, the source, the SHA-256, the score and the PFP document that binds it.

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
| `Demo3ProtocolInvariants` | L2D | Demo 3 protocol invariants |
| `SLevel` | L2D | import of the five modules above that need it |
| `PrimitiveDifference` | L3D | import of `ShadowBoundary` |

Scores follow `SCORING.md` v2.0.0: a level, then the weakest of the five gates. They come from the re-homing review of 2026-10-27, which ran one reviewer pass and one adversary pass per file. **No module here reaches the L4D floor of `SCORING.md` §1.5.** This folder is not in a governed population of `governance/policy.json`, so `governance/tools/checker.py` does not check it.

Not moved, and why:

- `Family` is L2D, but its only import, `Expressivity`, is L1D.
- `ShadowFactorization`, `SnSymbolGameAndPackets`, `SymbolGame`, `Lib`, `TokenFrontier` and `AntimorphicInvolution` are L1D.
- `FiniteConsequences`, `LpWeakDuality` and `TerminalizerPolicy` have no grade, because their builds did not complete.

## Build and audit

The toolchain is core Lean `v4.35.0`, with no Mathlib and no other package.

```bash
cd lean4
lake build                      # library SymbolGameKernel, ten roots
lake env lean AxiomCensus.lean  # every theorem and its axioms
```

`AxiomCensus.lean` lists every theorem the compiled environment assigns to the ten roots, generated lemmas included. It fails if any theorem depends on an axiom outside {propext, Classical.choice, Quot.sound}, so it also catches `sorryAx` and user-declared axioms. `axiom_report.txt` is its output from 2026-10-27:

- 403 theorem constants in total;
- 303 of them use no axioms;
- the axioms used are only `propext` and `Quot.sound`.

Of the 403, 165 are generated lemmas. The other 238 are named theorems, and 167 of those use no axioms.
