# G18: X-6: The Remaining Definability Census Rows

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to decide the eleven
> undecided rows of the second derivation's definability census over the first-demand rectangle,
> each by an implemented function or a replayed countermodel, for under $1.

## 2. Why This Task

The first-demand rung decided one census row, succession, by a countermodel, and named the other eleven as leftover X-6. Each row needs a precise reading, fixed by a logged declaration: a different reading is a different row. Then it needs either a function of the state's own observables that agrees with the row everywhere on the rectangle, or two states with equal observables and different row values. Generation is hard mainly in the readings and in choosing observables that do not smuggle an index. Verification is cheap: a functional-dependency check by exact grouping over a finite set of replayed nodes.

The task stresses precise declaration, OEWAS (Engine Workflows, Agents, Skills) ledger discipline, and the OEEIS (Engine Epistemic Immune System) danger gate against observables that read a datum index, a token or the round number. A pass decides eleven cells on a bounded rectangle. It does not decide them in general, and FORCED is unavailable until an engine class exists (G17).

## 3. Formal Problem and Bounds

**Pins.** Post-tag research trees at 19L57G1 `b55fc96a`. Nothing here is cited to `3100c4e`.

- **Rows** (`19L57G1:research/second/SEED.md`, Challenge 5): two-ness; a count of observational classes; duration (rounds between growths); adjacency (which pairs a single response can change together); reach (the third-party effect of a response); an invariant (a quantity preserved or monotone across accepted rounds); irreversibility (a state no run returns to); symmetry (the size of the automorphism group); branching (the tie count); exhaustion (a form that distinguishes nobody); recurrence (an isomorphic state revisited). Succession is the twelfth row and is already decided.
- **Classes.** DEFINABLE (a function of the state's own observables exists), USEFUL REALIZATION (exists under an additional declaration, named and priced), FORCED (proved in every surviving engine), NONE OF THESE; and OPEN where undecided.
- **Decided row** (`19L57G1:research/second_index/CLAIM_LEDGER.md`, CENSUS-succession): not definable at the stage reached, by `no_state_function_gives_the_index`, scoped to the grammar, the empty base, the apart-labelling stake and one fixed reading of the index.
- **Rectangle** (`19L57G1:research/second_index/STATUS.md`): three bases (EMPTY, L, F); seven stakes (`free`, `total_apart`, `total_same`, `parity`, `residue_three`, `chain`, `one_sided_total`); every sequence of at most four declared events: 577 sequences from EMPTY, 3928 from L and 14293 from F.

**The problem.** For each of the eleven rows:

1. fix one reading by a logged declaration, with its type (a state property, or a property of a run or a response read at a state);
2. declare the observable signature from the state's own observables only (profiles, automorphism structure, the admitted requirement pattern), never a datum index, a presentation token or the round number;
3. over every node of the rectangle, decide DEFINABLE (exhibit the function and show exact agreement), NOT DEFINABLE (exhibit a replayed pair of nodes with equal signature and different row value), USEFUL REALIZATION (name and price the extra declaration), or OPEN;
4. mark FORCED as unavailable at this stage, with the reason.

Rows about runs (duration, reach, irreversibility, recurrence) must say what "at a state" means before they are decided. A row decided only on the rectangle is a bounded finding; a Lean countermodel or definition makes it a theorem within its scope.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 adding `research/<tree>/`: frozen `PROMPT.md` and `PREDICTIONS.md`, a typed census script that consumes the first-demand rung read-only through its public functions, receipts without timestamps, `CLAIM_LEDGER.md` with one CENSUS row per decided cell, blob pins, and optional core Lean for countermodels. The frozen `solve(case) -> dict` takes `{"row", "reading_id", "base", "stake", "max_events"}` and returns:

- `SOLVED` with `class`, and either `function` (its source digest and exact agreement count) or `countermodel` (two replayable histories, their shared signature and differing values);
- `OUT_OF_SCOPE` when the declared reading needs an engine (FORCED);
- `UNKNOWN` with the guard reached.

A certificate is complete when both countermodel histories replay from their base, the signature is recomputed independently, and every function is checked on every node of the rectangle.

## 5. Participant Packet

Public examples: the succession row as decided, re-encoded in this schema with exact expected output, and one worked declaration for two-ness on the EMPTY base with the `free` stake. The runner, the accounting template and a read-only checkout at `b55fc96a` inside the sandbox complete the packet.

## 6. Judge Packet

- **Held-out depth.** Every decided cell re-checked on sequences of five events. A DEFINABLE claim that fails at five becomes a scored error; a countermodel stays valid.
- **Relabel controls.** Every countermodel repeated with presentation tokens renamed; it must survive, since the signature is supposed to ignore tokens.
- **Poisoned but schema-valid.** A "definable" function that reads list order (an index in disguise); a countermodel whose two histories differ in signature only after canonicalization; a FORCED cell resting on one stake.
- **Checkers.** `python ci/run_gates.py` with the tree registered; an exact checker that recomputes signatures and row values from replayed nodes; an independent second checker in Rust over `core_ooutwire_primitives` (`profile.rs`, `automorphism.rs`, `separability.rs`).
- **Mutation suite.** Perturb one signature component; swap the two countermodel histories' values; drop a node from the agreement check.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E is a brute-force functional-dependency check: for each declared reading and signature, group every node by signature and report the first collision, with no model. E is strong once a reading and signature exist, so the model's contribution is the declarations and any Lean. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `qwen/qwen3-30b-a3b` (30B total), Qwen3 32B, Mistral Small 24B, `meta-llama/llama-3.3-70b-instruct`. Qwen2.5-72B is rejected. Availability and prices come from the pinned registry (U06). Models propose readings and code; the census decides.

## 9. Pass Gates and Statistics

- **Capability.** Every one of the eleven rows carries a declared reading and a class with evidence on the rectangle; every DEFINABLE claim holds at five events; every countermodel replays; the gate runner is green.
- **Differentiation.** Exact McNemar on paired held-out cells (row × base × stake), A against B, C and D. Primary metric: cells decided with complete certificates. Three seeds per arm.

## 10. Interpretation

- **A passes, B fails**: evidence that the game helps produce precise declarations, the hard part here.
- **E matches A**: once readings are fixed, the census is automation.
- **Many NOT DEFINABLE rows** is a finding about the grammar's observables, not a failure.
- **A row DEFINABLE on four events and not on five** shows why bounded definability is recorded with its bound.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: a signature component whose source reads an index, a token or a round counter (an AST scan, as `research/endogenous_demand` does for `reqs`). Signal 2: the function agrees only on the public examples. Both signals quarantine.
- **Thymus.** The succession row and its Lean countermodel form the self panel.
- **Antimorphisms expected.** Readings silently changed between rows; AM-2-style "definable" without a bound.
- **Controls.** No Layer-1 or Layer-2 control. The collision table is the host scratch space. Hooks run only with U16.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare reading and signature), `I` (append nodes), `D` (group by signature), `M` (refuse index-reading signatures), `R` (carry OPEN cells), `T`. Logged measure: undecided cells.

Operands to mine:

1. "a different reading is a different row";
2. the functional-dependency check as a definability oracle on finite rectangles;
3. an AST guard for index and token reads.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [core_ooutwire_primitives](../../../../engine/crates_rs/core_ooutwire_primitives/) (`profile.rs`, `automorphism.rs`, `observer.rs`, `separability.rs`); [danger_gate.py](../../../../pfp/domain/immune/danger_gate.py).
- 19L57G1 (`b55fc96a`): `19L57G1:research/second_index/` (`index.py`, `CLAIM_LEDGER.md`, `lean/`), `19L57G1:research/second/SEED.md`, `19L57G1:research/second_stake/observables.py`, `19L57G1:ci/run_gates.py`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). [U17](../../upgrades/u17_lean_verifier_backend.md) only if Lean countermodels are submitted.

## 14. Claim Hygiene

- **Supports:** for each declared reading, definability or a countermodel over the rectangle, re-checked at five events.
- **Does not support:** definability beyond the rectangle without a Lean proof; any FORCED cell; any other reading of a row; any named known structure (the seed defers that to its sealed comparison); anything about the located or WLEM/DNE collision cells, which are metatheoretic; any choice between readings L and F.
- **Narrowest defensible claim:** under the stated readings and signatures, these cells are definable on the rectangle and these are not, each with its evidence.
- **Next test:** re-run the census on G17's engine runs, where FORCED becomes decidable.
