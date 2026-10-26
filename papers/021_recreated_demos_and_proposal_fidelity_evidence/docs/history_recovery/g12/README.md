# G12: actual provider-free Lean reconstruction

This run checks all five original Type-valued isomorphism constructions in the twelve parked modules at `b55fc96a94740b0afde78337350a96d293615f3f`. It uses the installed Lean **4.33.0**, not a newer toolchain. `Derivation.Iso`'s exact declaration is independently byte-equal to the separately retained sealed `3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a` declaration. No source in either external repository was changed.

The main Lean `run_cmd` reads the actual compiled `ModuleData.constNames`, removes theorems, opens all universal binders and checks the resulting head for `Derivation.Iso`. A separate Lean process dumps **all 141 constants in all twelve modules**; a Python walk selects the same five entries. The census contains `of_components`, `symm`, `trans`, `iso_of_relabel_eq` and `relabel_iso`, including the two original held-outs. It is not a source-text theorem count.

`Wrappers.lean` is the operator-written Arm-E template baseline. It constructs each theorem's type by retaining the original binders and hypotheses and wrapping only the terminal `Iso` in `Nonempty`. Its proof is the corresponding `Nonempty.intro` applied to the original definition and every original argument. Lean's normal `addDecl` checks those terms. `Audit.lean` compares each resulting type against the exact elaborated Prop image, requires the two-way census agreement, and rejects a `False` binder. The independent frozen `example` statements compile too.

All five instances are **closed theorems at the original concrete `R2L` regime**. Identity datum/form renamings are actual structures with `rfl` inverse laws and bound-preserving maps; the ordered requirement hypothesis closes by `decide`. Component equality/membership and identical relabelling hypotheses close by reflexivity. The `symm` and `trans` instances use the original `isoRefl` witness. No extra `False` assumption occurs. Every wrapper and every instance depends on exactly `propext` and `Quot.sound`, as reported by actual `Lean.collectAxioms` walks.

The unmodified original gates execute against the retained original source tree/artifact and the fresh original-root build log:

- Parked census: **75 modules, 63 in the root closure, 12 parked**.
- Whole original axiom artifact: **1,530 reports**, with independent name-blind count agreement.
- Original token/axiom whitelist audit: **77 source files / 1,530 reports**.
- The existing **48 parked reports** remain unchanged; the new five reports live in the separate reconstruction.

The five original controls are actual executions. An added `False` binder is kernel-valid but refused as `VACUOUS_WRAPPER`. Dropping the second ordering hypothesis from `of_components` is mathematically provable from the first and the membership equivalence, yet refused as `STATEMENT_PIN_MISMATCH`. A text-only Lean census with exactly the correct entries compiles but lacks the trusted environment-census source custody and is refused. A valid theorem in a counterfactual `controls/ParkedAudit.lean` compiles but is refused by the declared location rule. A valid instance source with `sorry` solely in a comment compiles but the **unchanged original lexical gate** rejects it. Sealed files are never used as mutation targets.

Source recovery is bounded: **86 fixed b55 files / 1,560,263 raw bytes**, plus the separately bound sealed `Minimality.lean`. The complete original Lean source population is required for the parked gate to notice otherwise unimported modules. The manifest pins every raw Git blob and SHA-256. The external-pin availability evidence remains in `../external_pin_availability.json` and the independent replay in `../external_pin_independent_replay.json`; these identity checks are separate from the new mathematical run.

The first original-root build failed on Windows output-path length. Its real output is retained. A separately authored paper config changes only source/build locations, keeps the two original roots/default targets and uses a shorter **worktree-local** `.artifacts/paper011-g12lean` build directory. The copied original config and every original mathematical source stay unchanged. Windows Python's launcher alias also proved unreadable for byte hashing; the final run explicitly supplies and hashes the actual backing interpreter. Failed local elaboration attempts and the earlier style-stage run are retained as intermediate attempts, not final completion receipts.

`receipt.json` binds the final source manifest, actual Lean/Lake/Python binary identities, argv/cwd/return codes, all output streams, all reports, all controls and before/after dependency inventories. The inventories cover all pinned source/gate/artifact files, authored source bytes, installed compiled Lean import/runtime files and local compiled dependencies. Their scope excludes the OS and Python standard library. A fresh `-B` worker cache prefix is required.

The defensible result is that the original **provider-free P1–P4 mathematical baseline and specified falsifiers are checked**. The broader external `ci/run_gates.py` workflow has unrelated Python/research/receipt populations and was not run; the retained parked and full axiom families above were run. No live model arm, raw historical model response, three-seed experiment, exact McNemar test or billed inference measurement is claimed. This does not establish that every parked definition is audited, that every module is audited, a change to the sealed estate, admission authority, or completion of the full G12 experiment. **AuthorityEffect: None.**

Reproduction in this Windows worktree:

```powershell
py -3.12 -B code/genesis_g12_replay.py recover --repo C:/Users/a343o/source/repos/19L57G1
py -3.12 -B code/genesis_g12_replay.py build-original --toolchain C:/Users/a343o/source/repos/.elan/toolchains/leanprover--lean4---v4.33.0
```

Then use `lean` for `Census.lean`/`IndependentDump.lean`, `prepare-pins`, `compile` for `Wrappers.lean`/`Instances.lean`/`Audit.lean`, and `finish` with a **new empty cache prefix** and the explicit readable `--interpreter`. The retained process records contain exact commands. On another checkout, set the separately authored config's short `buildDir` to that checkout's local output directory and record a new config/run digest; preserve the original fixed source manifest.
