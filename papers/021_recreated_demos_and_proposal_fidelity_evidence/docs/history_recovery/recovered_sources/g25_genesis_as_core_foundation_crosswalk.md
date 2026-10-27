# G25: Genesis as Engine Foundation: A Checked Crosswalk

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to build a crosswalk
> from 19L57G1's primitives to the DDC letters and the Prime algorithms, with every row either
> machine-checked in core Lean or explicitly refused as a chosen analogy, for under $2.

## 2. Why This Task

The estate's own rules say that difference evaluations factor through 19L57G1's genesis primitives and that D2 is embedded in the homology crate. Nothing checks either claim. A crosswalk that separates what is definable (a translation with a theorem) from what is only a chosen analogy would tell the engine which of its foundations are earned and which are declared.

Generation is hard for a reason that is also the point: an analogy is easy to write and hard to refuse. Verification is cheap: each checked row is a Lean statement about a declared translation, and each refused row needs only a stated reason. The task stresses the Symbol Game's refusal letter, OEWAS (Engine Workflows, Agents, Skills) provenance, and the OEEIS (Engine Epistemic Immune System) danger gate against identification smuggling, which is the main risk here.

## 3. Formal Problem and Bounds

**Pins.** Sealed 19L57G1 objects at `3100c4e` (locations read at `b55fc96a`, confirmed at the tag during packet build); 19L57G1 governance text at `b55fc96a`; Core side in this worktree of the_symbol_game.

**The binding constraint** (`19L57G1:CLAUDE.md`, "Refused grid, recorded (author, 2026-08-31)", `b55fc96a`). The author refused an outside classification grid of single-letter slot names offered for the primitive-difference inventory. The offered names are reproduced nowhere in 19L57G1. The clause says any future claim of independent convergence between that inventory and an external architecture's slot grid is false by construction and must cite the clause. The DDC alphabet is an external single-letter grid. Therefore:

- the crosswalk lives on the Core side only; nothing of it is proposed to 19L57G1, overriding the genesis rules' default home for results;
- no row claims convergence, identity or derivation of a DDC letter from 19L57G1; the crosswalk document cites the clause;
- every row is stated with each side in its own vocabulary.

**19L57G1 side (sealed, `3100c4e`).** D2, the oriented two-element structure, is initial among pointed witnessed relations in the bare-witness reading (`CL-PD2-INITIALITY`, `PrimDiff.D2_initial_pointed`). The cost-two floor: the genesis challenge's minimum response costs exactly two items in both readings (`cost1_insufficient_general`, `deltaU0_valid`, `deltaU0F_valid`). The events: `Supply` provably changes nothing; `AdmitDatum`, `AdmitForm`, `AdmitInst`, `AdmitRuleAll` and `Impose` are the only state changes. The native transition codebook is `TransitionAlphabet.lean` and `code/derivation/transition_alphabet.py`, cited by path only.

**Core side (this worktree).** The DDC letters in `core_discrete_deformation_calculus/src/dda_alphabet.rs`: `E` exact repair, `R` residual projection, `C` context exposure, `I` integration, `Λ` lift (a trigger is not a license), `D` descent, `M` refusal or mutation, `T` terminalization (mints no authority). The Prime algorithms: Prime −1, candidate proposal, with no crate owner; Prime 000, declaration then admission (`oeprmalg0_admission.rs`: measuring before admission is unrepresentable) and the twelve-step fill (`oeprmalg0.rs`); Prime 001, intake and inter-carrier transport soundness, where translation does not confer validity and losses are booked in sealed ledgers (`oeprmalg1.rs`); Prime 002, continuation, the anti-cheat halting laws and bounded stopping (`oeprmalg2.rs`).

**Estate claim to test.** `.claude/AGENTS.md` (the GENESIS primitives rule) says D2 is embedded as the canonical 1-simplex in `core_homology`. A search of `core_homology/src` in this worktree for `D2_initial` and `19L57G1` finds nothing. The crosswalk must check that embedding or record it as a chosen analogy.

**The problem.** For each 19L57G1 object above, and for a valid minimum response, a refusal record, and a closed-run terminal:

1. propose the Core-side counterpart or counterparts, or none;
2. where a translation can be defined (for example residual as the number of required pairs not separable), state a property the letter's or algorithm's contract demands and prove it in core Lean about the translation;
3. otherwise record `CHOSEN_ANALOGY` with the reason identification is refused, or `REFUTED` with a witness, or `OPEN` with the test that would decide it;
4. emit every row as a Prime 001 transport: status proposed, never admitted, with a loss ledger naming what the translation forgets (at least readings L versus F, presentation tokens and tied classes).

## 4. Deliverable and Output Contract

A pull request to the_symbol_game only: a core Lean package under [lean4/research_programs](../../../../lean4/research_programs/) (`<program>/`), a `crosswalk.json` and a short report beside the genesis crosswalk demo. The Lean package should `require` 19L57G1's Lean package pinned at `3100c4e`, fetched into untracked build space, so no sealed text enters the_symbol_game. If that is not possible, it may use an independently written reading whose agreement is checked by replaying histories through the sealed Python read-only; copying from sealed paths is forbidden. The frozen `solve(case) -> dict` takes `{"genesis_object", "core_object"}` and returns:

- `SOLVED` with `relation` (`CHECKED` with a Lean declaration and axiom report, `CHOSEN_ANALOGY` with the refusal reason, or `REFUTED` with a witness) and a non-empty `loss_ledger` where the translation is not injective;
- `OUT_OF_SCOPE` when a pair would need an identity claim to state;
- `UNKNOWN` with the deciding test.

## 5. Participant Packet

Public rows: `Supply` (a checked row: the translation leaves the residual unchanged); a valid minimum response against `E` (a checked row on residual descent, using that responses never write `reqs`); and `AdmitDatum` against `C` (a chosen analogy with its reason). Each comes with exact expected output. The runner, the accounting template and read-only checkouts complete the packet.

## 6. Judge Packet

- **Held-out rows.** The remaining events, D2 with the claimed embedding, the cost-two floor, and the four Prime algorithms.
- **Poisoned but schema-valid.** A `CHECKED` row whose Lean proves a property of the translation that the letter's contract does not demand; a row saying a letter "is" an event; a report claiming the alphabet was recovered from genesis; a row with an empty loss ledger on a non-injective translation.
- **Checkers.** The operator builds the package from clean, runs the axiom audit (`{propext, Quot.sound}`, no `Classical.choice`) and a forbidden-token scan including comments, and checks each statement against a frozen statement file by hash. The independent second checker evaluates each checked property on bounded histories replayed through the Rust reading `core_ooutwire_primitives` (`event.rs`, `replay.rs`, `separability.rs`).
- **Mutation suite.** Swap the translation of two events; drop a loss-ledger entry; relabel `CHOSEN_ANALOGY` as `CHECKED`.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E has no model: for every (event, letter) pair it evaluates the letter's contract predicate on translated bounded histories and reports a compatibility table. E proves nothing, and its table is the kind of grid the danger gate watches for; it is a baseline for which rows could be checked, not a result. Arm F does not apply.

## 8. Budget, Models and Provenance

$2.00 per arm, enforced before each call. Candidate models: `deepseek/deepseek-r1-distill-llama-70b`, `meta-llama/llama-3.3-70b-instruct`, Qwen3 32B, `qwen/qwen3-30b-a3b` (30B total). Qwen2.5-72B is rejected. Availability and prices come from the pinned registry (U06). Lean time is tool cost.

## 9. Pass Gates and Statistics

- **Capability.** Every held-out row carries a relation with a complete certificate; every `CHECKED` row compiles within policy; no row claims identity or convergence; the document cites the refusal clause.
- **Scoring.** A correct `CHOSEN_ANALOGY` refusal counts as solved. A `CHECKED` row that fails the statement check scores wrong. `UNKNOWN` scores unsolved.
- **Differentiation.** Exact McNemar on paired held-out rows, A against B, C and D. Primary metric: rows with complete certificates. Three seeds per arm.

## 10. Interpretation

- **Few checked rows, many refusals** is a legitimate result: the foundations are mostly declared, and the estate should say so.
- **The D2 embedding checked** turns an estate rule into a theorem about a named translation; **refused**, the rule text should be corrected.
- **A checked row for the cost-two floor** shows the Core side can price a repair the way genesis does; it is not a derivation of the Core pricing.
- **E's table matching A's checked rows**: the Lean is the contribution.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: identity or convergence wording between a DDC letter or Prime stage and a 19L57G1 object. Signal 2: no Lean declaration backs the row. Both signals quarantine; this is the main hook here.
- **Thymus.** The sealed theorem names used here form the self panel, assembled at run time from the read-only checkout and committed only as digests.
- **Antimorphisms expected.** AM-2-style "the alphabet is grounded in genesis"; laundering a chosen analogy into a checked row.
- **Controls.** No Layer-1 or Layer-2 control. The row table is the host scratch space. Hooks run only with U16.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare the translation), `E` or `M` per row (checked or refused), `R` (carry OPEN rows with their deciding test), `T`. Logged measure: rows without a relation.

Operands to mine:

1. "a crosswalk row is a Prime 001 transport: proposed, with a loss ledger";
2. the chosen-analogy refusal template with its reason;
3. the residual-descent translation (required pairs not separable) as a reusable bridge.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [dda_alphabet.rs](../../../../engine/crates_rs/core_discrete_deformation_calculus/src/dda_alphabet.rs), [oeprmalg0_admission.rs](../../../../engine/crates_rs/core_discrete_deformation_calculus/src/oeprmalg0_admission.rs), [oeprmalg0.rs](../../../../engine/crates_rs/core_discrete_deformation_calculus/src/oeprmalg0.rs), [oeprmalg1.rs](../../../../engine/crates_rs/core_discrete_deformation_calculus/src/oeprmalg1.rs), [oeprmalg2.rs](../../../../engine/crates_rs/core_discrete_deformation_calculus/src/oeprmalg2.rs); [core_ooutwire_primitives](../../../../engine/crates_rs/core_ooutwire_primitives/); [core_homology](../../../../engine/crates_rs/core_homology/); [demo_genesis_crosswalk](../../demos/demo_genesis_crosswalk/) (its native ports are G13).
- 19L57G1: `19L57G1:CLAUDE.md` (refusal clause, `b55fc96a`); `lean4/Derivation/PrimDiff.lean` and `lean4/Derivation/TransitionAlphabet.lean` (sealed, by path and pin only); `19L57G1:research/alpha_engine/harness.py` (`apply_unique_delta` always raises).
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), [U17](../../upgrades/u17_lean_verifier_backend.md).

## 14. Claim Hygiene

- **Supports:** for each row, either a Lean-checked property of a declared translation or a stated refusal, with a loss ledger.
- **Does not support:** that any DDC letter or Prime stage is derived from, identical to, or convergent with a 19L57G1 primitive (the refusal clause makes that false by construction); any claim inside 19L57G1; that uniqueness licenses anything; a choice between readings L and F; physical or ontological truth of either side.
- **Narrowest defensible claim:** under translation T, event X satisfies property P that letter Y's contract requires; every other pairing is a chosen analogy or open.
- **Next test:** extend the checked rows to the Prime 002 halting laws on closed runs, where 19L57G1 proves termination.
