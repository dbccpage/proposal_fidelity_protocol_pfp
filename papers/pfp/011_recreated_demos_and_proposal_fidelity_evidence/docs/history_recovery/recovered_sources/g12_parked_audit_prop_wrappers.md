# G12: Prop Wrappers for the Parked Isomorphism Modules

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to give every
> Type-valued isomorphism construction in the parked modules a Prop-valued `Nonempty (Iso ...)`
> theorem, with an environment-derived census proving none is missed, for under $1.

## 2. Why This Task

`19L57G1:lean4/ParkedAudit.lean`, at HEAD `b55fc96a`, audits every theorem in the twelve modules that lie outside the root's import closure, and it records its own residual. `Iso` in `Minimality.lean` is Type-valued, so proofs about isomorphisms in the parked modules are definitions, and definitions get no report.

`IsoBridge.lean` contributes zero reports, because its sole declaration is the definition `of_components`. `relabel_iso` and `iso_of_relabel_eq` in `IsoCanon.lean` are in the same position. `EXPECTED_PARKED_REPORTS = 48` in `ci/check_parked_audit.py` pins the total, not the per-module split, so the statement "IsoBridge is audited" is false.

A Prop wrapper whose proof applies the definition makes `collectAxioms` walk the definition's body. Writing one wrapper is trivial. The work is in proving that the census is complete, and the census must be read from the compiled environment: ParkedAudit records that text-based theorem counts have failed twice in this repository.

The task stresses Symbol Game metaprogramming, OEWAS (Engine Workflows, Agents, Skills) audit workflows, and OEEIS (Engine Epistemic Immune System) vacuity detection.

## 3. Formal Problem and Bounds

**Modules.** Twelve modules in `19L57G1:lean4/Derivation/`: `Composing`; `DiffAnchor`, `DiffAnchorCompat`; `FormRenaming`, `FormTransport`, `FormTransportCompat`; `IsoBridge`, `IsoBridgeCompat`; `IsoCanon`, `IsoCanonCompat`; `IsoCollapse`, `IsoCollapseCompat`.

All except `Composing` post-date `3100c4e`. `Iso` itself is at `3100c4e`, in `19L57G1:lean4/Derivation/Minimality.lean`.

**Targets.**

- **P-1 (census).** A Lean `run_cmd` that enumerates the environment in ParkedAudit's `parkedModules` / `constNames` style. It lists every non-theorem declaration of the twelve modules whose type, after its binders, is an application of `Iso`. The list must agree with the wrappers in both directions.
- **P-2 (wrapper).** For each listed `d : ∀ xs, hs → Iso A B`, a theorem `∀ xs, hs → Nonempty (Iso A B)`, proved as `⟨d xs hs⟩`, with identical binders and hypotheses. The named targets are `of_components` (IsoBridge), `relabel_iso` and `iso_of_relabel_eq` (IsoCanon).
- **P-3 (instance).** For each wrapper, one instantiation at a concrete regime whose hypotheses close by `decide` or `rfl`, for example the identity relabelling of `R2L`.
- **P-4 (report).** One `#print axioms` report per wrapper, each within `{propext, Quot.sound}`.

**Constraints.**

- Nothing under `lean4/Derivation/` is edited, because it is sealed.
- No theorem goes into `ParkedAudit.lean`. That file's own doc says such a theorem would compile but its axioms would go uninspected.
- No `@[ext]` is added to a parked structure. That is the known gap, which fails loudly.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 that adds a new research tree. The tree requires `lean4/` read-only by path, as `research/alpha_engine/lean/lakefile.toml` does. It contains: the census, the wrappers and the instances; an axiom census following the `verify_lean.py` pattern; `PROPOSAL.md`, for the author, on whether the parked audit should adopt the wrappers.

`solve` returns one record per listed definition: `SOLVED`: `{definition, wrapper, axioms, instance}`; `OUT_OF_SCOPE`: a witness that the definition's hypotheses are unsatisfiable, so no non-vacuous instance exists; `UNKNOWN`: `ELABORATION_FAILED`.

## 5. Participant Packet

`TASK.md` gives P-1 through P-4, the pins, the constraints and the forbidden tokens.

Public examples:

- the `relabel_iso` wrapper, with its identity instance and the expected report;
- a poisoned wrapper that adds `False` to its hypotheses. The expected result is the refusal code `VACUOUS_WRAPPER`.

The packet also includes `runner.py` and `accounting.json`.

## 6. Judge Packet

**Held-out census entries.** The judge's own census may include definitions beyond the three named ones. A text read at HEAD also finds `trans` (IsoCanon) and `symm` (IsoCollapse), both of which build `Iso` values. Wrappers for every entry are held-out statements.

**Statement pin.** For each entry, `example : <frozen Prop image of d's type> := <wrapper>`.

**Gates.** `python ci/run_gates.py` at HEAD, including the parked-module family. It must stay green, with 48 reports.

**Second checker.** An operator-written Python walk over `ModuleData.constNames`, dumped by a separate Lean run.

**Mutation suite.** The judge must reject: a wrapper with one hypothesis dropped; an instance with `sorry` in a comment; a census matched by text; a wrapper placed in `ParkedAudit.lean`.

## 7. Arms and Baselines

The arms are A to E. Arm F does not apply.

Arm E is a template generator, written by the operator before the run, that emits `⟨d ...⟩` wrappers from the elaborated types. E is expected to tie A on P-2 and P-4, so this challenge is a calibration point. The informative items are P-1 (completeness from the environment) and P-3 (non-vacuity), where templates do not help.

## 8. Budget, Models and Provenance

The budget is $1.00 per arm. Candidate models: Qwen3 32B; `meta-llama/llama-3.3-70b-instruct`; `deepseek/deepseek-r1-distill-llama-70b`; a registered Lean-specialised prover within the ceiling.

Lake time counts as tool cost.

## 9. Pass Gates and Statistics

**Capability gate.** The census agrees with the second checker; every entry, held-out ones included, has a pinned wrapper and a non-vacuous instance; every report lies within `{propext, Quot.sound}`; the parked-module gate is unchanged; the poisoned wrapper is refused.

**Differentiation test.** Exact McNemar over the held-out entries, with 3 seeds per arm.

**Primary metric.** Cost per verified entry.

## 10. Interpretation

- **A pass.** The Type-valued isomorphism content of the parked modules has audit reports, through wrappers outside the sealed tree.
- **A report containing `Classical.choice`.** A real finding about sealed content. It is reported to the author, not repaired here.
- **A census with more than five entries.** A better map of the residual.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none of these. They are recommended:

- **Danger gate.** Signal 1 is "module audited" for a module with zero reports. Signal 2 is a wrapper whose statement differs from its definition's type.
- **Thymus.** The self panel is ParkedAudit's 48 existing reports, so constructor-derived lemmas are not flagged.
- **Complement.** Not implemented in the estate, so not used here.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C E Λ I D T`, with `M` on a vacuous wrapper: **C** exposes the environment census; **E** writes the wrappers; **Λ** is the Type-to-Prop lift by `Nonempty`; **I** integrates the census; **D** means fewer unwrapped entries; **T** freezes the result.

**Logged.** Unwrapped entries, vacuous instances and statement-pin failures.

**Operands to mine.** Lift a Type-valued construction to `Nonempty` to audit it; take the census from the environment, never from text; a wrapper needs a witness instance.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only.** At HEAD: `19L57G1:lean4/ParkedAudit.lean`, `19L57G1:ci/check_parked_audit.py`, the twelve parked modules, and `19L57G1:research/alpha_engine/lean/lakefile.toml`; at `3100c4e`: `19L57G1:lean4/Derivation/Minimality.lean`.

**the_symbol_game.** `pfp/domain/immune/`, and `engine/crates_rs/core_ooutwire_primitives` (`canonical.rs`, `renaming.rs`) for the instance regimes.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row: [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** each listed isomorphism construction has a Prop wrapper, a non-vacuous instance, and a report within the whitelist; and the census of such constructions is complete for the compiled environment.
- **Does not support:**
  - that the parked modules are fully audited, since definitions that do not reach `Iso` stay unreported;
  - any change to the sealed tree;
  - any claim beyond validity in the calculus of inductive constructions (CIC).
- **Narrowest defensible claim:** the Type-valued isomorphism content of the parked modules now has named audit reports, through wrappers outside the sealed tree.
- **Next test:** extend the census to every non-theorem declaration of the parked modules that no theorem reaches.
