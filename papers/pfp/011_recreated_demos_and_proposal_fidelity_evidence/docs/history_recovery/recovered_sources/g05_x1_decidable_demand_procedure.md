# G05: X-1: A Decision Procedure for Demand

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to build, in
> core Lean, a decision procedure for whether a regime carries a demand, with a completeness
> proof by induction over the slot list, for under $2.

## 2. Why This Task

`19L57G1:research/second_index/STATUS.md` at HEAD `b55fc96a` records leftover X-1. As things stand, existence of a first count is conditional: `first_demand_exists_when_a_demand_is_decidable` takes a hypothesis `dec : ∀ r, Decidable (HasDemand S r)`, and nothing in the rung supplies it.

The well-formed contexts of a regime are finitely many. The form is bounded by the form list, the slot count by the form's arity, and each slot by the data count, so an enumeration exists. Building it and proving it complete would make the Python rectangle and the Lean statements the same object. STATUS prices X-1 as one moderate rung, mostly the completeness induction over the slot list.

Generating the proof is hard: it is a structural induction on `List (Option Nat)` against a conjunction of well-formedness conditions, with no classical shortcut. Checking it is left to the kernel. The task stresses the Symbol Game's decomposition into lemmas, OEWAS (Engine Workflows, Agents, Skills) Lean workflows, and OEEIS (Engine Epistemic Immune System) policing of `Classical` decidability.

## 3. Formal Problem and Bounds

The objects are at HEAD in `19L57G1:research/second_index/lean/SecondIndex/`:

- `Kernel.lean`: `Ctx` (a form index plus a slot list `List (Option Nat)`), `wfCtx`, `slotOk`, `plug`, `derivable` (which has a `Decidable` instance), `collapsed` and `separable`. These are verbatim reconstructions of the sealed kernel slice, pinned to `19L57G1:lean4/Derivation/Basic.lean`.
- `Inherited.lean`: `Stake` (a label function with a diagonal law), `honour` and `Demand`.
- `Index.lean`: `HasDemand`, `IsFirstDemand` and `least_witness_from`.

There are four targets:

- **X1-a.** An enumeration `ctxs : Regime → List Ctx`. It must be sound (`c ∈ ctxs r → wfCtx r c`) and complete (`wfCtx r c → c ∈ ctxs r`), with completeness proved by induction over `c.slots`.
- **X1-b.** Instances `Decidable (separable r d d')` and `Decidable (HasDemand S r)`, built from X1-a without any classical instance.
- **X1-c.** The rung's existence corollary without `dec`: if some prefix reaches a regime that carries a demand, a first count exists.
- **X1-d.** On the three bases and on a declared sample of regimes, the Lean decision, evaluated by `decide`, equals the demand bit computed by `index.py`.

The edge cases are: regimes with no forms, where the context list is empty; arity-0 forms, which fail the hole requirement `none ∈ c.slots`; arity 3 and above; data count 0; stakes labelled `free` everywhere.

## 4. Deliverable and Output Contract

A pull request to 19L57G1. It is either a rung of the second derivation (`research/second_<rung>/`, under the contract pinned by `research/second/SEED.md`, with `PREDICTIONS.md` frozen before the first compile) or a tree under the scaffold. The tree reconstructs the kernel slice under blob and span pins, as `research/second_index` does, and compares the shared declarations with its own `test_reconstruction.py`.

The tree holds: the Lean files; the axiom census; a Python cross-check of X1-d; a receipt; a claim ledger that moves X-1 to `PROVED_THEOREM`, or records exactly what remains open.

`solve` returns one of three results for each target: `SOLVED` with `{target, lean_names, axioms}`; `OUT_OF_SCOPE` with a witness that completeness fails for the sealed `wfCtx`, such as a well-formed context outside every finite bound; `UNKNOWN` with `NO_PROOF_FOUND`.

## 5. Participant Packet

`TASK.md` gives the frozen types of X1-a through X1-c, the pins and the forbidden tokens.

The public examples are: the reading-L regime after one form admission, with its expected context list; the empty base, whose context list is empty; a poisoned request to decide `HasDemand` via `Classical.propDecidable`, expected to be refused with `CLASSICAL_DECIDABILITY`.

The packet also contains `runner.py` and `accounting.json`.

## 6. Judge Packet

**Gates.** `python ci/run_gates.py` at HEAD, the tree's clean-build axiom audit, and a statement pin for X1-a through X1-c.

**Held-out regimes.** Depth-5 prefixes from each base, regimes with an arity-3 form, and two held-out stakes. Each is run with `decide` and compared against the second checker.

**Second checker.** `engine/crates_rs/core_ooutwire_primitives` (`context.rs`, `separability.rs`) enumerates contexts independently.

**Mutation suite.** The judge must reject each of the following: an enumeration that omits the last slot position; `by classical`; `Decidable` obtained through `Nonempty` and choice; completeness stated only for `r.data > 0`; an `axiom` line.

## 7. Arms and Baselines

The arms are A–E. Arm F does not apply.

Arm E is the rung's Python rectangle together with Lean `decide` on concrete regimes, which runs through the existing `derivable` instance only once an enumeration exists. With no enumeration, E cannot even state X1-b, so it scores 0 on X1-a through X1-c.

The informative comparison is A against B and C on X1-a completeness. If A and C tie, the controller and the proof checking are doing the work, not the glyph representation.

## 8. Budget, Models and Provenance

The budget is $2.00 per arm. Candidate models: `meta-llama/llama-3.3-70b-instruct`; `deepseek/deepseek-r1-distill-llama-70b`; Qwen3 32B; a registered Lean-specialised prover within the ceiling.

Lake time counts as tool cost. The host scans for forbidden tokens before every build.

## 9. Pass Gates and Statistics

**Capability gate.** X1-a through X1-c are proved under the statement pin. X1-d agrees on every held-out regime. All gates are green, with every report within `{propext, Quot.sound}`. The poisoned request is refused.

**Differentiation test.** Exact McNemar across arms on the held-out items, with 3 seeds.

**Primary metric.** Targets proved per dollar.

## 10. Interpretation

- **A proves X1-a and B does not.** This is evidence that decomposition into slot-list lemmas helps. It says nothing about demand itself.
- **X1-c is proved.** First-count existence becomes unconditional. That settles a conditional statement, but it adds no demand generator, and OB-1 stays open.
- **`OUT_OF_SCOPE`.** This would expose a flaw in the finiteness argument in STATUS, which would be worth a note to the author.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog row requires none. These are recommended:

- **Danger gate.** Signal 1 is a `Classical`, choice or `propDecidable` epitope. Signal 2 is a report that contains `Classical.choice`.
- **Thymus.** The self panel is the rung's own constructive proofs (`least_witness_from`, `first_demand_unique`), so that bounded upward search is not flagged.
- **Kinetic proofreading.** `HopfieldNinioProofreader` delays acceptance of a completeness lemma that has passed only once.
- **Host scratch space (U12, optional).** It can hold goal states.

## 12. Run Folder, DDC Trace and Operand Mining

**Expected DDC pattern.** `C R E I Λ D M T`: **C** exposes the kernel slice; **R** projects a failed induction onto its missing cases; **E** proves the slot lemmas; **I** assembles the enumeration; **Λ** lifts decidability from `derivable` to `separable` to `HasDemand`; **D** means strictly fewer open goals; **M** refuses classical instances; **T** freezes the result.

**Logged.** Open goals, classical-epitope hits and X1-d disagreements.

**Operands to mine.** Induction over the slot list, carrying the hole requirement as an invariant; a bounded existential over a sound and complete list is `Decidable`; discharge a `dec` hypothesis by constructing an instance, not by assuming one.

## 13. Estate Reuse and Prerequisites

**19L57G1, read-only.** At HEAD: `19L57G1:research/second_index/` (`lean/SecondIndex/*.lean`, `index.py`, `test_reconstruction.py`, `verify_pins.py`) and `19L57G1:research/second/SEED.md`; at `3100c4e`: `19L57G1:lean4/Derivation/Basic.lean`.

**the_symbol_game.** `engine/crates_rs/core_ooutwire_primitives` (`context.rs`) and `pfp/domain/biochem/proofreading.py`.

**Upgrades.**

- Base: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Row: [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** carrying a demand is constructively decidable for the reconstructed kernel, and first-count existence holds without a decidability hypothesis. This is validity in the calculus of inductive constructions (CIC) only.
- **Does not support:**
  - endogenous demand generation (OB-1 is open);
  - reading leftover collapsed pairs as demands;
  - any choice between reading L and reading F.
- **Narrowest defensible claim:** named core-Lean theorems discharge the `dec` hypothesis of `first_demand_exists_when_a_demand_is_decidable`.
- **Next test:** X-3b in Lean, then X-2 once an engine exists.
