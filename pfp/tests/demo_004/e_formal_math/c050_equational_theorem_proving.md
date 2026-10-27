# C050: Equational Theorem Proving with Checkable Rewrite Proofs

**AuthorityEffect:** None. **Status:** planned. **Domain:** e_formal_math. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to prove hidden equational goals from hidden axiom sets, as rewrite sequences checked step by step, or to refute them with finite countermodels, for under $2.00.

## 2. Why This Task

An equational proof written as a chain of axiom applications is trivially checkable. Each step names an axiom, a direction, a position and a substitution, and the checker confirms one subterm replacement. A finite countermodel is checked by exhaustive evaluation. Finding such proofs is research-grade. Short-looking group-theory consequences, such as deriving the right inverse from left axioms, already need non-obvious intermediate terms, and the search space grows quickly with term depth.

This is the T4 member of the family. It stresses the Symbol Game's long-horizon descent, where many turns reduce the distance between the two sides only indirectly. It stresses the OEWAS (Engine Workflows, Agents, Skills) workflow that alternates lemma proposal with proof search. It stresses the OEEIS (Engine Epistemic Immune System) against "proofs" that skip steps. A pass shows checkable proofs of these problems. It says nothing about any open problem, and none is included.

## 3. Formal Problem and Bounds

A case is a signature (at most 4 symbols, arities at most 2), axioms `E` (at most 6 unit equations, universally quantified), and a goal `s = t`. The goal's variables are replaced by fresh constants (skolemized), so it is ground.

- **PROOF:** a sequence `s = u₀, u₁, …, u_k = t`. For each step, `u_{j+1}` is `u_j` with the subterm at position `p` replaced. The replaced subterm is `σ(l)` for an axiom `l = r` used left-to-right (or `σ(r)` right-to-left), and the replacement is `σ(r)` (or `σ(l)`). A step may also cite a proved lemma, which carries its own chain.
- **COUNTERMODEL:** a finite domain of size at most 8, with operation tables, in which every axiom holds under all assignments and the goal fails under a given assignment.

Problems are TPTP-style unit-equality problems (the TPTP library, Sutcliffe) but operator-authored. Symbols are renamed, and the problems are built from theories such as:

- groups from left axioms;
- loops and quasigroups;
- lattices;
- Boolean-algebra fragments;
- combinator identities;
- idempotent semigroups.

Hidden instances are not copied from TPTP, to limit memorisation. Proof lengths range up to about 200 steps. Every theorem or non-theorem label comes from the second checker at packet-build time: an automated prover's proof converted and checked, or a found countermodel. Edge cases: goals that need a lemma used twice, goals true only in larger models, and axioms stated in unusual orientations.

## 4. Deliverable and Output Contract

**Mode: frozen pipeline.** Problems are hidden, so the frozen artifact is the pipeline configuration: engine commit, prompts, operand set, model ID and revision, decoding parameters, seeds and the per-case budget split, bound in `pipeline.lock.json` and hashed before reveal. Terms are JSON arrays in prefix form.

```json
{"case_id": "eq_ex_01", "axioms": [[["f", ["f", "x"]], "x"]], "goal": [["f", ["f", ["f", "a"]]], ["f", "a"]]}
{"case_id": "eq_ex_01", "status": "SOLVED", "kind": "PROOF", "lemmas": [], "steps": [{"axiom": 0, "dir": "lr", "pos": [], "subst": {"x": ["f", "a"]}, "result": ["f", "a"]}]}
{"case_id": "eq_ex_02", "axioms": [[["m", "x", "x"], "x"]], "goal": [["m", "a", "b"], ["m", "b", "a"]]}
{"case_id": "eq_ex_02", "status": "SOLVED", "kind": "COUNTERMODEL", "size": 2, "tables": {"m": [[0, 0], [1, 1]]}, "assignment": {"a": 0, "b": 1}}
{"case_id": "eq_ex_07", "status": "UNKNOWN", "code": "CASE_BUDGET_EXHAUSTED"}
```

A `PROOF` is complete when every step replays exactly, the chain starts at `s` and ends at `t`, and every lemma is itself proved from `E`. A `COUNTERMODEL` is complete when every axiom holds for all `size^vars` assignments and the goal differs under the given assignment. `OUT_OF_SCOPE` applies to a malformed signature or axiom, with the offending field.

## 5. Participant Packet

- `TASK.md` with the term and position syntax, the step format and the JSON Schema.
- 12 public problems with exact input and output JSON: the two examples above; right identity and right inverse from the left group axioms, with full reference chains; an absorption consequence in lattices; a combinator identity; two countermodels (non-commutative idempotent, non-associative loop); a lemma-reuse example; a malformed axiom; one `UNKNOWN`.
- `runner.py`, which replays chains locally, and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 36 problems, 26 theorems and 10 non-theorems, stratified by the length of the reference proof.
- **Relabel and gauge controls:** 12.
  - function symbols and constants renamed;
  - axioms permuted;
  - axioms and the goal reoriented, since equations are symmetric;
  - an equivalent axiomatization, for example groups via a definitional extension.

  Verdicts must match their base.
- **Poisoned but schema-valid:** 8.
  - non-theorems whose `note` claims a known result;
  - goals true in all small models but false in a model of size 7 or 8;
  - axiom sets that make the theory trivial, where every goal holds (reported separately);
  - `subst` maps binding variables absent from the axiom.
- **Exact checker:** Rust step replayer built on the term machinery in `engine/crates_rs/core_symbol_game_runtime/src/rewriting/`, plus an exhaustive model evaluator.
- **Independent second checker:** a Python replayer and evaluator by a different author.
- **Mutation suite:** the checker must reject: a step at the wrong position; a substitution that fails to match; a skipped step where two rewrites are merged; a lemma that cites itself (a cycle); a countermodel violating one axiom at a single assignment; a countermodel whose goal actually holds; Boolean table entries.

## 7. Arms and Baselines

Arms A to D follow the protocol, with no external prover in their sandbox. **Arm E** is a pinned automated equational prover (for example E, Twee or Waldmeister) plus a finite model finder (for example Mace4). Its proofs pass through a deterministic converter into the step format and then the same checker. A proof the converter cannot express is scored unproved and reported.

E is expected to dominate. A tie means the model adds nothing over automated reasoning. A model win on specific rows would be interesting only if E timed out on them under the same wall-clock limit. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$2.00 per arm: construction at most $0.40, hidden problems at most $1.60 (about $0.033 per case), about 5.7 million tokens in total at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `deepseek/deepseek-r1-distill-llama-70b`, `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`. The receipt records the prover and model-finder versions and hashes, and the converter hash.

Q40 lessons apply:

- real JSON steps are shown;
- repair turns carry the goal, the current chain, and the first failing step with its typed reason;
- several chains are sampled per turn;
- all replay is sandboxed;
- budget is checked before every call.

## 9. Pass Gates and Statistics

- **Soundness gate (hard):** zero accepted proofs or countermodels that the second checker rejects.
- **Capability gate:** in at least 2 of 3 seeds, at least 30 of 36 base problems are settled, all relabel controls agree, and no poisoned non-theorem receives a `PROOF`.
- **Primary metric (pre-registered):** theorems proved. The test is an exact McNemar test on paired (seed, problem) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Reported separately:** countermodels, since they are usually easier.
- **Seeds:** 3.

## 10. Interpretation

Countermodels for small non-theorems are often easy, and they must not carry the headline, which is the Q40 refusal lesson again. The informative rows are long-chain theorems. If A proves more of them than B, the obstruction-guided descent and lemma lifting help. If A ties D, sampling explains it. If E proves everything and A little, this family is not where the game adds value, and that result is still worth recording.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is a "follows from" claim in a `note` or in the output; Signal 2 is a failing replay step.
- **Clonal maturation.** `ClonalSelectionEngine` can mature lemma proposals: lemmas that shorten many chains gain affinity, and unused ones decay.
- **Expected antimorphisms:**
  - AM-3 ASSERT_SKIP (merged steps);
  - AM-4 (the same failing chain resubmitted);
  - AM-2 (claiming a theorem by name);
  - AM-FSP-2 (countermodels that do not satisfy the axioms).
- **Layer 2:** a grammar mask for the step records, via `carrier_gbnf` (unwired). Positions and substitutions are the most error-prone fields.
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the set of proved lemmas and the current frontier terms reachable from each side as working memory, which repair prompts reference by ID.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (axioms and goal exposed), `I` (a chain draft), `R` (the first failing step, plus the remaining gap between the two ends), `Λ` (lift a lemma), `D` steps as the gap shrinks, `E` when the chain closes, `T`. `M` records budget refusals. The `ObstructionScore` sets Φ₁ to the size of the unmatched symmetric difference between the normalized sides (a declared, deterministic term-distance) and `active_count` to failing steps; Γ₂ is unused (0).

Operands to mine:

- prove the right-hand group laws as lemmas first and reuse them;
- try small countermodels (size 2 to 4) before long proof search on suspicious goals;
- orient axioms by term size for the search, but record both directions;
- replay every step locally before emitting.

## 13. Estate Reuse and Prerequisites

- The catalog row lists no estate reuse. Term positions and replay can build on `engine/crates_rs/core_symbol_game_runtime/src/rewriting/`.
- Completed systems from [C046](c046_knuth_bendix_completion.md) can supply normal-form lemmas.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). No row extras; [U12](../../upgrades/u12_host_scratch_space_working_memory.md) is recommended for the lemma store.

## 14. Claim Hygiene

- **Supports:** the pipeline proved or refuted k of 36 hidden equational problems, with every step and every model checked by two independent checkers.
- **Does not support:** progress on any open problem, completeness of the pipeline, or superiority over automated provers unless the data show it row by row.
- **Narrowest defensible claim:** on these operator-authored unit-equality problems, the pipeline's theorem rate was X, against arm E's Y, at the recorded cost.
- **Next test:** longer-chain problems where E needs more than the time limit, run with lemma operands mined from this run.
