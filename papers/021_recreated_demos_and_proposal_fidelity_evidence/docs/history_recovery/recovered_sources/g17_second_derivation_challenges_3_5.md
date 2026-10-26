# G17: Second Derivation: Challenges 3 to 5

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to declare the engine
> class of the second derivation's Challenge 3, run every surviving engine forward as Challenge 4
> requires, and decide the Challenge 5 census at every stage reached, for under $2.

## 2. Why This Task

The second derivation of 19L57G1 has closed its inheritance, stream, stake and first-demand rungs, and the engine is the named leftover every later question waits on. The seed makes the work hard to generate: an engine must be declared with every capability counted, bundling is rejected, all tied minima are retained, and every node is replayed from genesis. It also makes it cheap to verify: every decision is by an implemented algorithm, every receipt regenerates byte-identically, and every gate is proved by injection.

The task stresses long-horizon structure in the Symbol Game, OEWAS (Omega Engine Workflows, Agents, Skills) handoffs between stages, and the OEEIS (Omega Engine Epistemic Immune System) danger gate against the seed's guarded words. A pass shows the game can produce a rung-shaped tree that survives the seed's own gates. It does not make the tree a rung of the second derivation; that is the author's decision (§3).

## 3. Formal Problem and Bounds

**Pins.** All facts below are post-tag research trees, read at 19L57G1 `b55fc96a`. None is cited to `3100c4e`.

- **Seed.** `19L57G1:research/second/SEED.md` (its SHA-256 is recorded in `research/second/PLAN.md`). Challenge 3: declare an engine as a generator reading demands off the state, a responder answering by a minimum response under a declared measure, a continuation rule, and a replay rule, with no external act after genesis except those declared; enumerate every minimal engine in the class formed from the surviving stakes of Challenge 2, the two known continuation rules (growth; switch of demand kind) and the validity rules of Challenge 1; count capabilities; reject bundles; retain ties. Challenge 4: run each survivor from each sealed genesis reading to declared bounds, quotient by the implemented isomorphism, retain ties, replay every node, export the frontier, and record terminals as fixpoint, refusal, bound or guard. Challenge 5: decide each census row at every stage as DEFINABLE, USEFUL REALIZATION, FORCED or NONE OF THESE.
- **Inputs from earlier rungs.** `research/second_stake/STATUS.md`: a nine-member stake menu (its rows E1–E9, unrelated to the OB-1 clauses) all retained as survivors for Challenge 3; branch terminal `NO_ENDOGENOUS_STAKE_IN_MENU`; declared-input count two, unchanged; its pending prediction concerns the next uncomputed data count, five. `research/second_stream/STATUS.md`: Challenge 1's universal question OPEN, validity member V1 used, V2 compared on a subset. `research/second_index/STATUS.md`: X-5 (the engine) not started; X-6 (eleven census rows) undecided; one row (succession) decided by countermodel.
- **Seed constraints that bind this task.** §7: "never ask a language model to decide" equality, minimality, isomorphism, survivor counts or proof status. §6: the guarded words (forced, minimal, free, canonical, equivalent, universal, complete, engine) need a proof or a precise conditional scope. §0: the seed's run is isolated from agents and skills.

**Consequence of §0.** A Symbol Game run is not an isolated seed run. The deliverable follows the rung protocol but is a separate research tree that declares its provenance. The seed's next-rung rule currently selects X-3, not the engine, so the tree also records that deviation, as `second_index` recorded its own.

**The problem.** (1) Declare the engine class as the finite product of the nine surviving stakes, the two continuation rules and the validity members V1 and V2. Count every capability each engine declares and enumerate the minimal engines, retaining ties. (2) Run every survivor from genesis L and F to four held data, exporting the frontier and terminal kinds. (3) Decide each of the twelve census rows at every stage reached, now with FORCED available across surviving engines. (4) Answer SEED §5 question 4 (does a minimal engine exist, is it unique up to isomorphism, is it initial in the class) by proof, countermodel or OPEN.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 adding `research/<tree>/` with the rung files the seed names: `PROMPT.md` and `PREDICTIONS.md` frozen by hash before any computation or Lean, code, tests, receipts, `STATUS.md`, `CLAIM_LEDGER.md`, `SOURCE_MANIFEST.json` and `verify_pins.py`. The tree has 95% line and branch coverage measured from inside it, strict typing, and a Lean package for every theorem-level claim. The frozen `solve(case) -> dict` takes `{"engine", "reading", "max_data"}` and returns:

- `SOLVED` with `engine_status` (`SURVIVOR`, `REFUTED` with witness, or `BUNDLE_REJECTED` with its split), `capability_count`, `terminals` by kind, a frontier digest, and `census` rows each with a class and evidence;
- `OUT_OF_SCOPE` when the engine uses an act outside its declaration, with the history that shows it;
- `UNKNOWN` with the guard reached and the exported frontier.

A certificate is complete when every node replays from genesis, every receipt regenerates byte-identically, and every theorem-level claim has a Lean declaration with an axiom report within `{propext, Quot.sound}`.

## 5. Participant Packet

Public examples: two engines (one stake with growth under V1, one with the kind switch under V1), each run to three held data with exact expected output produced by the operator. The runner, the accounting template, and a read-only checkout at `b55fc96a` inside the sandbox complete the packet.

## 6. Judge Packet

- **Held-out.** Every engine at five held data, the stage `second_stake` left pending; census rows at that stage; the operator's frozen statements for question 4.
- **Relabel controls.** Each run repeated with presentation tokens renamed; frontiers must agree up to the implemented isomorphism.
- **Poisoned but schema-valid.** A "one declaration" engine that bundles two capabilities; a FORCED row resting on one engine; a receipt with a timestamp; a tie resolved silently.
- **Checkers.** `python ci/run_gates.py` on the PR branch with the tree registered, the axiom audit, and the tree's own injection record. Independent second checker: the Rust reading in `omega_ooutwire_primitives` (`omega.rs`, `closure.rs`, `tree.rs`), replaying the exported frontiers.
- **Mutation suite.** Drop a tie; merge two capabilities; replay one node from a non-genesis state; relabel a terminal kind.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E enumerates the engine product mechanically and runs it with the existing rung code (`second_stake`'s generation and run scripts) and no model. E can produce the bounded runs; it cannot write the Lean or the ledger classification, so it bounds the model's contribution from below. Arm F does not apply.

## 8. Budget, Models and Provenance

$2.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b` (30B total), Qwen3 32B, Gemma 3 27B. Qwen2.5-72B is rejected. Availability and prices come from the pinned registry (U06). Models write code and proofs; implemented algorithms decide. The seed's fifteen-minute gate ceiling per rung applies to the tree's gates.

## 9. Pass Gates and Statistics

- **Capability.** The gate runner is green with the tree registered; coverage and typing floors met; every held-out engine run agrees with the second checker at five data; every census row carries a class and evidence at every stage reached; question 4 answered by proof, countermodel or OPEN.
- **Differentiation.** Exact McNemar on paired held-out rows (engines times stages), A against B, C and D. Primary metric: held-out rows correct with complete certificates. Three seeds per arm.
- **Scoring.** OPEN with the exact obstruction scores unsolved, never wrong.

## 10. Interpretation

- **A passes** gives the second derivation a candidate engine tree for the author to admit, rename as a rung, or refuse. Admission is the author's act.
- **A unique minimal engine** would still not be a license, and any initiality claim needs its universal property proved.
- **No minimal engine**, or a class where every engine bundles, is a valid result under the seed.
- **E matches A on runs** but not on Lean or classification: the model's contribution is the proof and ledger work.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: a guarded word without a proof reference. Signal 2: a missing replay or an unfrozen prediction. Both signals quarantine.
- **Thymus.** The earlier rungs' claim ledgers are the self panel, assembled at run time and committed as digests.
- **Antimorphisms expected.** Bundling presented as one declaration; AM-2-style FORCED from one engine; AM-4-style re-emission of the stake rung's table.
- **Controls.** No Layer-1 or Layer-2 control. The exported frontier is the host scratch space. Hooks run only with U16.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare the class), `M` (reject bundles), `I` (append run nodes), `D` (quotient by isomorphism), `R` (carry OPEN rows), `T` per terminal kind. Logged measures: undecided census cells, unreplayed nodes.

Operands to mine:

1. a capability-counting checklist that rejects bundles;
2. "FORCED needs every surviving engine";
3. the provenance note for model-assisted rung-shaped trees.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [omega_ooutwire_primitives](../../../../omega_engine/crates_rs/omega_ooutwire_primitives/) (`omega.rs`, `closure.rs`, `tree.rs`, `terminal.rs`); [thymus.py](../../../../omega_engine_pfp/domain/immune/thymus.py).
- 19L57G1 (`b55fc96a`): `19L57G1:research/second/` (`SEED.md`, `PLAN.md`, `MANUAL.md`), `19L57G1:research/second_stake/`, `19L57G1:research/second_stream/`, `19L57G1:research/second_index/`, `19L57G1:ci/run_gates.py`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), and [U17](../../upgrades/u17_lean_verifier_backend.md) for the Lean part (the catalog row lists no extras and should add U17).

## 14. Claim Hygiene

- **Supports:** a declared engine class, its bounded runs from both readings, and census classes at the stages reached, all replayable.
- **Does not support:** that the tree is a rung of the isolated second derivation; that two is or is not the floor of declared inputs unless proved; any named known theory (the seed forbids naming one in this repository); any choice between readings L and F; a license from a unique minimal engine; more than validity in the calculus of inductive constructions for its Lean.
- **Narrowest defensible claim:** within the declared class and bounds, these engines survive, these are refuted, and these census cells hold, each with its evidence.
- **Next test:** the six-data stage, and X-2 (the first count under a generated run), which needs this engine.
