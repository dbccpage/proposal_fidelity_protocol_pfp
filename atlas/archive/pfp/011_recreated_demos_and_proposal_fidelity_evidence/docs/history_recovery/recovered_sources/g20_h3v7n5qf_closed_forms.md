# G20: H3V7N5QF: Closed Forms for Shortest-Sequence Counts

**AuthorityEffect:** None. **Status:** planned. **Domain:** k_genesis_19l57g1. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md). **Genesis rules:**
[README.md](README.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to guess, verify
> exactly and prove closed forms for five open counts of H3V7N5QF (7:O1, 9:O1, 16:O5, 18:O1 and
> 19:O1), for under $1.

## 2. Why This Task

H3V7N5QF, the sibling testbed of 19L57G1, computes several counts exactly within declared bounds and leaves their closed forms open. That is the classic guess-then-prove shape. Guessing is where a model may help and where a no-model fitter is a real competitor. Checking a guess against the exported evidence is exact and cheap. The proof is the hard part.

The task stresses the Symbol Game's split between conjecture and certificate, OEWAS (Engine Workflows, Agents, Skills) evidence binding, and the OEEIS (Engine Epistemic Immune System) danger gate against calling a fitted formula a closed form. A pass gives proved formulas for counts the repository has only computed. A formula that matches finitely many values without a proof is a conjecture and is scored as one.

## 3. Formal Problem and Bounds

**Pin.** `H3V7N5QF` branch `derivation/next-ten-parallel` at `1681998`. Every value below is read from that pin.

- **7:O1** (`H3V7N5QF:paper/seventh/paper.md` §9). The number of shortest sequences reaching a result with two or more terms. Computed per result within the bound and exact there; with one term it is 1. The paper notes that the least-writing identification of `arb` with `bra` on the two-term state makes the count differ from a count of arrangements.
- **9:O1** (`H3V7N5QF:paper/ninth/paper.md` §9). The same question for the ninth derivation; with one term the count is `C(p + q, p)`.
- **16:O5** (`H3V7N5QF:paper/sixteenth/paper.md` §13). 9:O1 restated for the sixteenth; the counts are exact within the bounds.
- **18:O1** (`H3V7N5QF:paper/eighteenth/paper.md` §6; `evidence/eighteenth/summary.json`). Inside a bound of 3 terms the changes reach 137 written results with the names kept and 69 without them; a closed form for both is open.
- **19:O1** (`H3V7N5QF:paper/nineteenth/paper.md` §6; `evidence/nineteenth/summary.json`). Inside 3 terms: 68 results with the names kept and 19 without them.

**Data.** For 7, 9 and 16, `evidence/<ordinal>/results_bound*_rounds*.csv` carries `shortest_sequences_of_changes` and `shortest_sequences_exact_within_bound` for each result. For 18 and 19, the counts at bounds other than 3 are not in the evidence. They are produced by running the repository's own exploration (`code/run_eighteenth.py`, `code/run_nineteenth.py`) at those bounds, by the operator's second checker at packet build.

**The problem.**

1. For 7, 9 and 16: a formula in the result's own parameters (terms, assertions and their multiplicities, as the CSVs record them) that equals `shortest_sequences_of_changes` on every row whose exact flag is set, including the two-term writing effect 7:O1 names.
2. For 18 and 19: formulas `f(n)` in the term bound `n`, with the names kept and without them, reproducing 137, 69, 68 and 19 at `n = 3`. If a natural closed form exists in another parameter (rounds, not bound), it is accepted with that parameter declared.
3. A proof of each formula: in Lean in H3V7N5QF's own library (Mathlib is permitted there) against the repository's definitions, or a written proof with every lemma checked by exhaustive computation within the bound and marked as such.

## 4. Deliverable and Output Contract

A pull request to H3V7N5QF adding `research/<tree>/`, outside the derivational seal, with the formulas, a typed exact checker, receipts, and Lean where proved. No derivation's `prompt/`, `paper/` or `evidence/` is edited. The frozen `solve(case) -> dict` takes `{"item", "parameters"}` and returns:

- `SOLVED` with `value` (an integer), `formula_id`, and `status` (`"PROVED"` with a Lean declaration or `"CONJECTURED"` with the checked range);
- `OUT_OF_SCOPE` when the parameters fall outside the formula's declared domain;
- `UNKNOWN` with a reason.

A certificate is complete when the value is exact, the formula is evaluated in integer arithmetic, and the proof, if claimed, compiles with its axiom report.

## 5. Participant Packet

Public data: the evidence rows at the smallest bound for each of 7, 9 and 16, and the 18 and 19 counts at `n = 1, 2, 3`, all with exact expected outputs. The runner and the accounting template complete the packet. The solver gets a read-only H3V7N5QF checkout inside the sandbox.

## 6. Judge Packet

- **Held-out values.** The rows at the largest exported bound for 7, 9 and 16 (bound 5 for the seventh and ninth, bound 4 for the sixteenth), and the 18 and 19 counts at `n = 4` (and `n = 5` if the second checker completes within its guard).
- **Relabel controls.** For 18, both beginnings, which the paper records reach the same counts.
- **Poisoned but schema-valid.** A formula that fits the public rows and misses a two-term row where the least-writing identification applies; a `PROVED` status with a Lean file that restates the value by `decide` at one bound only.
- **Checkers.** The exact checker compares integer values against the evidence CSVs and fresh runs. The independent second checker is a separate enumeration written against H3V7N5QF's state definitions, not its explorer. Lean is checked with `python code/lean_report.py` and H3V7N5QF's gates (`code/xry/gate.py`, `ci/check_definitional_citations.py`, `ci/check_vacuous_checks.py`).
- **Mutation suite.** Off-by-one in a binomial; swap names-kept and names-forgotten; drop the one-term case.

## 7. Arms and Baselines

Arms A–D follow the protocol. Arm E is a no-model guesser: exact rational fitting of polynomials, products of binomials and linear recurrences over the declared parameters (for example by exact linear algebra over the rationals), plus the repository's own exploration for fresh values. E is expected to guess some forms; the proof is where arms may differ. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `qwen/qwen3-30b-a3b` (30B total), Qwen3 32B, `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`. Qwen2.5-72B is rejected. Availability and prices come from the pinned registry (U06). Enumeration and Lean time are tool cost.

## 9. Pass Gates and Statistics

- **Capability.** Every held-out value exact for at least four of the five items, and at least one formula `PROVED` with a clean Lean build.
- **Scoring.** A `CONJECTURED` formula that matches all held-out values scores as a verified conjecture, separately from `PROVED`.
- **Differentiation.** Exact McNemar on paired held-out values, A against B, C and D; a second McNemar on proved formulas. Primary metric: items with a proved formula. Three seeds per arm.

## 10. Interpretation

- **E guesses a formula A also guesses**: the guess is automation; compare the proofs.
- **A proves what E only fits**: evidence for the game on the proof side.
- **A formula for 18 or 19 that fails at `n = 4`** shows that three bounded values were not enough, a useful negative.
- **No formula for 7:O1's two-term effect**: the identification is the hard part, as the paper says.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **Danger gate.** Signal 1: "closed form" or "proved" on a formula without a proof artifact. Signal 2: agreement checked on public rows only. Both signals quarantine the claim.
- **Thymus.** The recorded counts (137, 69, 68, 19 and the one-term cases) are the self panel; a formula contradicting them is rejected before scoring.
- **Antimorphisms expected.** AM-2-style generalization from three values; overfitting to one bound.
- **Controls.** No Layer-1 or Layer-2 control. The table of computed values is the host scratch space. Hooks run only with U16.

## 12. Run Folder, DDC Trace and Operand Mining

Each arm writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/`. Expected letters: `C` (declare parameters), `I` (append values), `E` (a formula matches all known values), `M` (a formula refuted by a value), `Λ` (move from fit to proof), `T`. Logged measure: mismatching rows.

Operands to mine:

1. "a fit is a conjecture until proved";
2. a held-out-bound extrapolation check;
3. an exact rational fitting recipe with declared parameter bases.

## 13. Estate Reuse and Prerequisites

- the_symbol_game: [core_linear_algebra](../../../../engine/crates_rs/core_linear_algebra/) (exact rational solving for fits); [core_kernel](../../../../engine/crates_rs/core_kernel/) (exact rationals).
- H3V7N5QF (`1681998`): `H3V7N5QF:code/seventh/`, `H3V7N5QF:code/ninth/`, `H3V7N5QF:code/run_eighteenth.py`, `H3V7N5QF:code/run_nineteenth.py`, `H3V7N5QF:evidence/`, `H3V7N5QF:code/lean_report.py`, `H3V7N5QF:ci/OEWAS_GATES.md`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), [U17](../../upgrades/u17_lean_verifier_backend.md) (with Mathlib for H3V7N5QF).

## 14. Claim Hygiene

- **Supports:** proved closed forms for the items proved, and verified conjectures, each with its checked range.
- **Does not support:** any transfer into 19L57G1 (these proofs may use Mathlib and `Classical.choice`; see G23); any statement beyond the declared domains; any claim about the derivations' seeds; more than validity inside Lean's logic with the axioms reported.
- **Narrowest defensible claim:** for item X, the count equals formula F on its declared domain, proved (or checked through bound B).
- **Next test:** the same items at the next bound, and 3:O5 and 8:O1, which ask the same question.
