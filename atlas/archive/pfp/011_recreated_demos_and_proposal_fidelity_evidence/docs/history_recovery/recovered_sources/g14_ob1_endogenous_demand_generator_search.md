# G14: OB-1: Searching for an Endogenous Demand Generator

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T5.
**Budget:** $5.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to search a declared
> finite class of owed-separation constructs over the sealed 19L57G1 event grammar for an endogenous
> demand generator, and return a Lean-checked survivor, a Lean-checked impossibility on that class,
> or a documented UNKNOWN, for under $5.

## 2. Why This Task

OB-1 is the standing obstruction that everything downstream routes around. 19L57G1 derives no object-language generator of demands; the Alpha Engine keeps OB-1 OPEN and its Driver B waits on a seventh `Event` kind; the estate's own engine reading asks the outside for every demand (`engine/crates_rs/core_ooutwire_primitives/src/outside.rs`).

Generation is hard because a candidate must pass several clauses at once, and every obvious candidate already dies on a named clause. Verification is cheap: a candidate is a finite history replayed from genesis, a call to the sealed `separable` observable, and a small Lean statement. The task stresses the Symbol Game's refusal discipline, OEWAS (Engine Workflows, Agents, Skills) claim hygiene, and the OEEIS (Engine Epistemic Immune System) danger gate, because the most likely honest outcome is a scoped negative. A pass shows the game can run a bounded frontier search to a clean certificate. It does not show that OB-1 is closed outside the declared class.

## 3. Formal Problem and Bounds

**Pins.** Sealed grammar and terminal statement: 19L57G1 `3100c4e`. Research trees: 19L57G1 `b55fc96a`. Sealed file and section locations were read from the `b55fc96a` checkout and are confirmed at the tag when the packet is built.

- **Grammar (sealed, `3100c4e`).** `Regime` with fields data, forms, insts, rules, reqs; six `Event` constructors: `Supply`, `AdmitDatum`, `AdmitForm`, `AdmitInst`, `AdmitRuleAll`, `Impose`. Separability is profile inequality.
- **Known negative (`b55fc96a`, `19L57G1:research/endogenous_demand/CLAIMS.md`).** Outcome B for class `C_reqs` (demand = a member of `reqs`): `e2_on_C_reqs_unsat` and `replay_reqs_iff_impose`, axioms `{propext}`. The instance channel I1 is recorded OPEN. The census rows C1–C9 each fail a named clause; C10 (a new constructor) is outside the class.
- **Restatement (`b55fc96a`, `19L57G1:ob1_e2_restatement/FINDING.md`, census pin `b947873`).** E2′ is an owed separation: a designated pair with `separable` false, no `Impose` at that step, produced by a rule firing or grammar closure and not by a host pick. Under E2′ every row still dies (E1, E2′ or E3), I1 fails E3 on its own witness, and the finding recommends Outcome B on the wider class. It did not prove Outcome B, did not search beyond C1–C9 and I1, and did not formalize E2′ in Lean.
- **Clauses.** E1–E4 are the four clauses as operationalized in `19L57G1:research/endogenous_demand/candidates.py`. E1 fails when the host chooses; E3 fails on an imported or already-separable pair; E4 invariance is recorded there as not attempted.

**The problem.** (a) State E2′ in core Lean over the sealed slice. (b) Declare a finite class K: a construct is a rule from replayed regimes to an optional pair, built from a declared finite list of observables (profiles, collapsed pairs, automorphism orbits, the `reqs` pattern) and never from a datum index, a presentation token or the round number. A rule that meets more than one orbit returns nothing, as the never-selects reader does. (c) Decide, for every construct in K, whether it satisfies E1 ∧ E2′ ∧ E3 on some history of at most four events from genesis L or F with at most four data and arity at most two.

The hidden set must contain host picks disguised as observables (order-of-list reads), C10-shaped proposals, laundered supply (the C3 shape), already-separable pairs (the C9 shape), and the I1 shape.

## 4. Deliverable and Output Contract

A pull request to 19L57G1 adding a new tree `research/<tree>/`: `PROMPT.md` and `PREDICTIONS.md` frozen by hash before computation, `SOURCE_MANIFEST.json` with blob pins, a deterministic typed census script, a core Lean package under `lean/`, receipts under `evidence/` with no timestamps, and `STATUS.md` and `CLAIMS.md`. The frozen `solve(case) -> dict` takes `{"reading", "max_events", "construct"}` and returns one of:

- `SOLVED` with `verdict: "DEFEATED"`, the failing `clause`, and a `witness_history` replayable from genesis;
- `SOLVED` with `verdict: "SURVIVOR"`, the witness history, and Lean declaration names for E2′ and E3 on that history;
- `OUT_OF_SCOPE` with a witness that the construct needs a constructor outside the sealed `Event` type;
- `UNKNOWN` with a reason (`bound_reached` or `lean_open`).

A certificate is complete when every history replays through the sealed kernel and every cited Lean declaration has an axiom report within `{propext, Quot.sound}`. A class-level impossibility (Outcome B on K) is a Lean theorem, not a census.

## 5. Participant Packet

Eleven public examples: C1–C10 and I1 re-encoded as construct specifications, each with exact input and expected output JSON matching the E2 vs E2′ table in `ob1_e2_restatement/FINDING.md`. The packet is built by the operator from a read-only checkout, outside the_symbol_game's tracked tree. The solving system gets that checkout read-only inside the sandbox, the runner, and `accounting.json`.

## 6. Judge Packet

- **Held-out constructs.** Twenty specifications the solver has not seen, drawn from the five shapes in §3 plus plausible observable-only rules.
- **Relabel controls.** Every construct re-run under a renaming of data tokens. The verdict must not change. These are invariance controls, not trials.
- **Poisoned but schema-valid.** A `SURVIVOR` whose last witness event is `Impose`; a Lean file with `sorry` inside a comment; a claims row labelled endogenous without a certificate.
- **Checkers.** The operator runs `python ci/run_gates.py` on the PR branch with the tree registered (family 11), and the axiom audit `ci/check_declaration_axioms.py`. The exact checker replays every witness through the sealed kernel read-only. The independent second checker replays the same histories through the Rust reading in `core_ooutwire_primitives` (`replay.rs`, `separability.rs`).
- **Mutation suite.** Flip one witness event; drop the no-`Impose` check; permute data so `separable` changes; plant a forbidden token in a comment; move a pinned blob.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E is the repository's own enumeration: `candidates.py` and `reclassify.py`, extended mechanically to enumerate every rule in K by brute force, with no model. If E produces the whole bounded census, the model's contribution is confined to the Lean part (E2′ and any class-level theorem). Arm F does not apply.

## 8. Budget, Models and Provenance

$5.00 per arm, enforced before each call. Candidate models within the ceiling: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b` (30B total), Qwen3 32B, Gemma 3 27B. Qwen2.5-72B is rejected. Availability and prices are checked against the pinned registry (U06), not asserted here. Lean build time is tool cost. No model decides clause membership; the census does, by implemented algorithms.

## 9. Pass Gates and Statistics

- **Capability.** The gate runner is green with the tree registered; the axiom audit is clean; every held-out construct is classified correctly with a complete certificate; no row claims the guarded word without a `SURVIVOR` certificate.
- **Scoring.** `UNKNOWN` scores unsolved, never wrong. A `SURVIVOR` that fails replay scores wrong.
- **Differentiation.** Exact McNemar on paired held-out rows, A against B, C and D. Primary metric: held-out constructs classified with complete certificates. Secondary: Lean statements proved. Three seeds per arm.

## 10. Interpretation

- **A survivor with a certificate** would be the first object-language demand generator on K. It reopens the terminal statement and goes to the author; it is not authority.
- **Outcome B on K in Lean** extends the `C_reqs` result to owed separation within K. OB-1 stays open outside K.
- **UNKNOWN with a bounded census** is still valuable: a non-existence census at four events, the E2′ formalization, and a frontier file.
- **E matches A on the census**: useful automation, no model advantage.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: a row or claim uses a guarded word (endogenous, forced). Signal 2: the row lacks a replayed certificate or touches a sealed path. Both signals quarantine the proposal; one only logs.
- **Thymus.** A self panel of the sealed and research-tree theorem names this task relies on, assembled at run time from the read-only checkout and committed only as digests. Detectors must not fire on it.
- **Antimorphisms expected.** An AM-2-style absolute claim ("no generator exists") without class scope; an AM-4-style stationary repeat, re-proposing a defeated row in new syntax, caught by canonical deduplication.
- **Controls.** No Layer-1 or Layer-2 control (no arm F). The census frontier file is the host scratch space. Hooks run only with U16 and are not scored.

## 12. Run Folder, DDC Trace and Operand Mining

Every arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare K and bounds), `I` (append census rows), `M` (typed refusal per defeated construct, naming its clause), `R` (carry OPEN rows), `D` (move to the held-out depth), `Λ` only for a logged new observable, `T`. Logged measures: undecided constructs and open Lean goals.

Operands to mine:

1. never-selects designation: return nothing on more than one matching orbit;
2. a renaming-equivariance harness that exposes host picks disguised as observables;
3. the E2′ checklist: owed, not imposed, produced by a rule, not already separable;
4. the outside-the-grammar label for any proposal that needs a seventh constructor.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [core_ooutwire_primitives](../../../../engine/crates_rs/core_ooutwire_primitives/) (`replay.rs`, `separability.rs`, `closure.rs`, `outside.rs`); [danger_gate.py](../../../../pfp/domain/immune/danger_gate.py); [thymus.py](../../../../pfp/domain/immune/thymus.py); [cemetery_sink.py](../../../../pfp/infrastructure/persistence/cemetery_sink.py).
- 19L57G1 (`b55fc96a`): `19L57G1:research/endogenous_demand/` (`candidates.py`, `reader.py`, `grammar.py`, `lean/`); `19L57G1:ob1_e2_restatement/reclassify.py`; `19L57G1:research/alpha_engine/STATUS.md`; the reconstruction pattern of `19L57G1:research/second_index/`; `19L57G1:ci/run_gates.py`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), and [U17](../../upgrades/u17_lean_verifier_backend.md) for the Lean part (the catalog row lists no extras and should add U17). [U16](../../upgrades/u16_oeeis_turn_loop_integration.md) is optional, for live hooks.

## 14. Claim Hygiene

- **Supports:** a bounded classification of the declared class K with replayable witnesses and, if proved, an impossibility on K in core Lean.
- **Does not support:** that OB-1 is closed; that no generator exists outside K, under a seventh constructor or under a different brief; that any construct is endogenous without all four clauses; E4 invariance; any license from a unique designation; anything about the four located matrix cells or the four WLEM/DNE collision cells, which are metatheoretic and not search targets; more than validity in the calculus of inductive constructions for any Lean result.
- **Narrowest defensible claim:** within K, on histories of at most four events from genesis L and F, no construct satisfies E1 ∧ E2′ ∧ E3 (or the named construct does, with its certificate).
- **Next test:** widen K by one logged observable, run the held-out five-event depth, and attempt E4.
