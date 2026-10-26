# G01: original reading-F mathematics

This reconstruction keeps the original G01 mathematical obligations at their source definitions. It adds proofs in Paper 011; it does not edit the 19L57G1 estate or manufacture model trials.

`source_manifest.json` recovers twelve exact Git blobs (107,878 bytes): sealed `3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a` Basic, Inertia and Minimality; `b55fc96a94740b0afde78337350a96d293615f3f` Mention and MinimalityF; six sealed Python package files and the original challenge artifact. The three sealed Lean module blobs are identical at b55. The definitions, including Type-valued `Iso`, are copied unchanged. Local compilation uses the explicitly installed Lean 4.33.0 toolchain; this is a current source reconstruction, not the historical Lean run.

`ResearchG01.lean` proves F-1, F-5 and F-K. The family has one `k`-ary form and one instance containing `k` copies of target datum 1, for every `k ≥ 1`. Its all-hole context separates targets 1 and 2. Isomorphism preserves the sole form's arity, so distinct arities cannot be isomorphic. The sealed `cost1_insufficient_F` proves that every valid two-item witness is minimal under item count.

F-5 uses `[1]`, `[1,1]`, `[1,2]`, `[0,1]` and `[1,0]`, each following its matching new-form declaration. Unary versus binary arity, repeated versus distinct instance arguments, and preservation of the `(1,2)` requirement distinguish the five classes. The latter forces images of target indices to remain targets; a link involving genesis cannot be mistaken for a target-to-target link. These are proofs over complete original `Iso` fields, not a reduced isomorphism definition.

The eight held-out obligations are reconstructed from the original specification's prose. No historical frozen `TASK.md` or concrete eight-type judge packet was retained. `G01Targets.lean` therefore binds explicit newly reconstructed signatures, and `G01Judge.lean` checks those signatures against the submitted names. The local result does not claim identities or pre-run commitments for an unavailable historical packet.

| ID | Original obligation | Retained local witness and outcome |
|---|---|---|
| H01 | F-5 over relabelled R2F | Full five-witness theorem under the `swap01` relabelling, target `(0,2)`; `relabelling_binding` retains every carrier field and the mapped instance arguments. SOLVED. |
| H02 | Family against link from genesis | Every family member has repeated arguments and cannot be isomorphic to `[0,1]`. SOLVED. |
| H03 | Family against link to genesis | Every family member cannot be isomorphic to `[1,0]`. SOLVED. |
| H04 | Fixed arity by decide | `k=3` exact application, two-item length and context separation checked by core `decide`. SOLVED. |
| H05 | k=1 and k=2 matched to bounded classes | Exact equalities to the unary and binary-diagonal witnesses, with full reflexive `Iso` values. SOLVED. |
| H06 | Poison: valid genesis mark | Original b55 `genesis_mark_not_separable` refutes the complete validity request. OUT_OF_SCOPE. |
| H07 | Poison: mu2 nonuniqueness | Exact original `mu2_unique_F` signature shows every valid two-item response of arity sum ≤1 reaches the original `U0F` class. This is the poison witness expressly prescribed by G01. OUT_OF_SCOPE. |
| H08 | Poison: reading identification by Iso | No full `Iso` from a three-datum F result to a two-datum L result: finite-range bounds and inverse laws contradict three distinct images in two positions. OUT_OF_SCOPE. |

The two positive public L examples are also re-proved by exact sealed theorem applications. The mu2 poisoned public example shares H07's original witness.

The closed `theorem_run_v3/receipt.json` has a clean local Lake build, eleven literal target pins, an environment-derived census of all ResearchG01 constants and ninety theorem/auxiliary axiom reports. Every report is within `{propext, Quot.sound}`. An initial audit correctly rejected `Classical.choice` introduced by a tactic's negation preprocessing; explicit constructive introduction repaired the proof without changing any target. Those failures remain diagnostic.

All seven original mutations are rejected, and a valid control remains accepted. Comment-token, Mathlib-import, axiom-line and partial-definition controls are refused before compilation. Actual Lean compilation rejects a weakened extra-False hypothesis, `Classical.em`, and `native_decide`. This installed Lean version exposes the latter as `candidate._native.native_decide.ax_1_1`, rather than the original specification's anticipated `Lean.ofReduceBool`; the literal observed axiom report is retained. The whitelist is unchanged.

The finite runner imports the unchanged sealed Python `min_responses` through an explicit private package spec, never an ambient namespace or `sys.path` insertion. A new empty bytecode-cache prefix ensures the bound source files are its inputs. The native transport wrapper only invokes the existing `omega_ooutwire_primitives` enumeration, replay, quotient and canonicalization functions. It contains no replacement mathematics solver. Its scoped `rustc` build links the exact existing crate archive and dependencies, not a new Cargo build.

Python and Rust refinement ranks yield different serialized representative key values. This discrepancy is preserved in `finite_disagreement_diagnostic_v1` and in each final raw stream. Both original implementations also provide the unchanged all-permutation checker. The adapter verifies each implementation's complete refined partition against that implementation's full-permutation partition, requires every declared class to have exactly its actual members, compares every candidate's shared full-permutation key, and compares all class memberships and sizes. Counts alone never establish agreement.

The finite scope is exactly `max_items=2`, `max_arity=2`: F mu1 has ten deltas in five two-member classes; L mu1 has six in three; both mu2 populations have two in one. The sealed unpruned Python grammar cross-checks the pruned enumeration. This finite computation does not establish the optional F-5+ complete-enumeration theorem in Lean. F-5 is a lower-bound theorem; F-K is the unrestricted positive-arity theorem.

Custody binds source blobs, authored roots, executable/compiler/archive inputs, actual stdout/stderr bytes and the Lean compiled dependency closure. The clean build's source/compiler snapshots precede compilation; the checked compiled closure has separate before/after snapshots around the judge and mutation runs. Small exact owned machinery from theorem_run_v3/native_build_v2 is preserved in `execution_machinery_theorem_v3_native_v2` before the comparison adapter changed. OS, Python standard library and the native linker installation remain outside the declared manifest. Historical diagnostic partial runs are not complete success receipts.

Model/provider accuracy, A–E arms, dollar accounting, McNemar/seed differentiation, estate `ci/run_gates.py` across all twelve families, external research-tree scaffold and the owner PR remain unexecuted. No current result selects between readings, chooses a tied class, establishes a universal property, or grants admission/execution authority. `AuthorityEffect: None`.
