# G24: Seed-Edit Ablation Bench for the Four Holes

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T5.
**Budget:** $5.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to run H3V7N5QF's
> seed-edit lattice as an ablation bench and decide, for refusal, budget, license and halt, whether
> adding the primitive makes it derivable or only declarable, for under $5.

## 2. Why This Task

The estate's engine reading in Rust keeps four things outside its own derivation: it records refusals, spends a budget, asks for a license before creating structure, and stops at declared terminals. This spec calls these the four holes. H3V7N5QF offers a controlled way to ask whether any of them can be derived rather than declared: each of its derivations differs from its parent by one seed sentence, and its ranked proposals already include a written refusal, a refusal memory and a written budget.

Generation is hard: each edit needs a precise seed sentence, a forgetful map to the parent, and a bounded run; license and halt have no proposal yet. Verification is cheap: compare edited and parent closures under the map at a bound. The task stresses experimental design in the Symbol Game, OEWAS (Engine Workflows, Agents, Skills) provenance, and the OEEIS (Engine Epistemic Immune System) danger gate against identification smuggling. `UNKNOWN` is an honest outcome for any hole.

## 3. Formal Problem and Bounds

**Pins.** H3V7N5QF `1681998`. H3V7N5QF's correspondence document read 19L57G1 at `89fc568a`; this spec uses that reading only through the document. Core side: this worktree of the_symbol_game.

- **Proposals** (`H3V7N5QF:meta/next_ten/selection.md`, a chosen selection measure): rank 4, C07 `04-written-refusal` (parent: twenty-first); rank 5, C01 `05-refusal-memory` (parent: seventeenth); rank 6, C04 `06-written-budget` (parent: ninth). C28 refusal-count and C26 refusal-copy were scored and not selected. No proposal adds a license or a halt.
- **Package format** (each `meta/next_ten/<package>/`): `why.md` (open hypothesis, falsifier, drop condition), `plan.md`, `seed_prompt.md`, `prompt.md`, `diff.patch`. The drop condition includes the case where every new distinction sits only in an external log or a chosen label.
- **Correspondence** (`H3V7N5QF:meta/immune_system/genesis_correspondence.md`): refusal is derived local behavior in the twenty-first derivation, with only a chosen event analogy to 19L57G1; a budget-writing event is refuted as a current seed event; a license has no counterpart (open extension); a halt is refuted as a current event identity, witnessed by `addTerm_legal`. An isomorphism between the two declared change alphabets is **refuted**, with two legal witnesses (`remove_admit_same` in the sixteenth; a refusal that changes no state in the twenty-first).
- **Core side** (`engine/crates_rs/core_ooutwire_primitives/src/`): `refusal.rs`, `budget.rs`, `license.rs`, `terminal.rs`; `core.rs` calls the engine a fold with four holes and `outside.rs` lists what it asks the outside for. Naming the four holes refusal, budget, license and halt is this spec's declaration, not the crate's.

**Classification**, in H3V7N5QF's own status words, for a hole h and an edit that adds one sentence to a parent seed:

- **DERIVABLE:** h's governing behavior is derived or computed in the edited seed and has a state-level effect: under the forgetful map to the parent, the reachable results, rounds or costs differ at some bound, with a replayed witness. The drop condition fails.
- **DECLARABLE ONLY:** at every tested bound the forgetful map is a bijection on closures that preserves rounds and costs, so the new distinction sits only in a log or a label. The drop condition holds.
- **OPEN:** neither is shown.

**The problem.** (1) Write two new proposal packages in the same format: a license record whose value changes which changes are allowed, and an explicit halt with no later change from its outcome, as the correspondence document's test column suggests. (2) For each hole and each edit (04, 05, 06 and the two new packages), run the edited and parent seeds within 3 terms, build the forgetful map, and classify. (3) Where two edits touch the same hole, run both orders and report commutation, as `meta/immune_system/ablation_lattice.md` does for other pairs.

**Invariant.** The refuted alphabet isomorphism must stay refuted. Both witnesses are re-run as controls, and no row may identify H3V7N5QF changes, 19L57G1 events and Core holes with one another; each cross-repository link stays a chosen analogy.

## 4. Deliverable and Output Contract

A pull request to H3V7N5QF adding a fenced subdirectory `meta/<bench>/`. `meta/` is the repository's designated area for Genesis and other outside vocabulary, and its `research/` holds only reading notes. It contains the two new packages, bench receipts and a bench table. `prompt/` is not touched; running any proposal as a numbered derivation is the author's act. Nothing is contributed to 19L57G1 (see G25). The frozen `solve(case) -> dict` takes `{"hole", "edit", "bound"}` and returns:

- `SOLVED` with `classification`, the forgetful-map digest, and for DERIVABLE a replayed witness in the edited closure whose image differs;
- `OUT_OF_SCOPE` when the edit needs a third seed sentence to make the map precise (a drop condition);
- `UNKNOWN` with the bound reached.

## 5. Participant Packet

Public cases: the budget edit (`06-written-budget`) at 2 terms, with exact expected output from the operator's prototype run, and the two alphabet-refutation witnesses as controls. The runner, the accounting template and a read-only H3V7N5QF checkout inside the sandbox complete it.

## 6. Judge Packet

- **Held-out.** Every edit at 3 terms; C26 and C28 written as packages by the operator and run as unseen edits; order-swapped pairs.
- **Poisoned but schema-valid.** A DECLARABLE ONLY verdict from a map checked on results but not rounds; a DERIVABLE verdict whose witness lives only in a log; a row stating that the alphabets correspond.
- **Checkers.** `meta/next_ten/verify_packages.py` and `prototype.py` for package shape and prototype runs; H3V7N5QF's gates (`code/xry/gate.py`, `ci/check_prose_watchlist.py`, `ci/check_vacuous_checks.py`). Independent second checker: an explorer written from each edited seed text separately from the solver's, run by the operator.
- **Mutation suite.** Make the map non-injective; drop the halt's absorbing clause; re-label a log field as state.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E is H3V7N5QF's own deterministic pipeline (`prototype.py`, `rank.py`, `verify_packages.py`), with no model, applied to the existing packages. E cannot write the license and halt packages, so the model's contribution there is measurable. Arm F does not apply.

## 8. Budget, Models and Provenance

$5.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `qwen/qwen3-30b-a3b` (30B total), Gemma 3 27B. Qwen2.5-72B is rejected. Availability and prices come from the pinned registry (U06). Models draft sentences and code; the maps and closures decide.

## 9. Pass Gates and Statistics

- **Capability.** Every held-out (hole, edit) row classified with a complete certificate at 3 terms; both control witnesses still hold; no identification row.
- **Partial credit.** A complete license or halt package with its bounded falsifier run counts even if its row stays OPEN. `UNKNOWN` scores unsolved, never wrong.
- **Differentiation.** Exact McNemar on paired held-out rows, A against B, C and D. Primary metric: rows classified with certificates. Three seeds per arm.

## 10. Interpretation

- **All four DECLARABLE ONLY** in this seed family supports keeping the holes as outside asks in the Core engine reading; it proves nothing about other seed families.
- **A DERIVABLE hole** gives an edit under which that behavior has state-level consequences, a candidate for the author to commission as a derivation.
- **Non-commuting edits on one hole** show that the order of adding primitives matters there.
- **Any identification** fails the bench regardless of other rows.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: a row uses an identity word (same as, corresponds to, is) between repositories. Signal 2: no translation with a theorem backs it. Both signals quarantine; this is the main hook here.
- **Thymus.** The correspondence document's rows and its two refutation witnesses are the self panel.
- **Antimorphisms expected.** AM-2-style generalization from one seed family; relabelling a log as state.
- **Controls.** No Layer-1 or Layer-2 control. The forgetful-map table is the host scratch space. Hooks run only with U16.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare edit and map), `Λ` (add the primitive sentence), `I` (append closures), `D` (forget back to the parent), `M` (refuse identification rows), `T`. Logged measure: unclassified rows.

Operands to mine:

1. "derivable means a state-level effect under the forgetful map";
2. the package template for one-sentence seed edits;
3. the identification refusal with its two witnesses.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [core_ooutwire_primitives](../../../../engine/crates_rs/core_ooutwire_primitives/) (`refusal.rs`, `budget.rs`, `license.rs`, `terminal.rs`, `outside.rs`, `core.rs`); [danger_gate.py](../../../../pfp/domain/immune/danger_gate.py); [budget.py](../../../../providers/domain/budget.py) (the provider budget, for contrast only).
- H3V7N5QF (`1681998`): `H3V7N5QF:meta/next_ten/`, `H3V7N5QF:meta/immune_system/`, `H3V7N5QF:lean4/Twentyfirst/`, `H3V7N5QF:code/run_twentyfirst.py`, `H3V7N5QF:ci/`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). [U16](../../upgrades/u16_oeeis_turn_loop_integration.md) is needed for the live danger gate.

## 14. Claim Hygiene

- **Supports:** per hole and per edit, a bounded classification with witnesses, and two new proposal packages.
- **Does not support:** any identification of H3V7N5QF changes, 19L57G1 events or Core holes; any statement about 19L57G1 (whose author refused outside classification grids on 2026-08-31); any unbounded claim from a bound-3 run.
- **Narrowest defensible claim:** within 3 terms, adding sentence S to parent P makes hole h derivable (witness W), or leaves it declarable only (map M is a bijection preserving rounds and costs).
- **Next test:** commission the strongest DERIVABLE edit as a numbered derivation, if the author chooses to.
