# C042: SAT Encodings with DRAT and LRAT Certificates

**AuthorityEffect:** None. **Status:** planned. **Domain:** e_formal_math. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a frozen encoder-and-prover module that answers hidden combinatorial problems with a checked solution or a DRAT/LRAT refutation of the judge's canonical CNF, for under $0.50.

## 2. Why This Task

Satisfiability answers are cheap to check. A model is checked against the original problem, and an unsatisfiability claim is checked by replaying a clausal proof with drat-trim (Wetzler, Heule, Hunt 2014) or an LRAT checker (Cruz-Filipe et al. 2017). Producing them is not always cheap. Resolution refutations of the pigeonhole formulas need exponential size (Haken 1985), and so do Tseitin formulas on expanders (Urquhart 1987). A plain conflict-driven solver therefore stalls on them, even though extended resolution gives short pigeonhole proofs (Cook 1976) and DRAT's RAT rule on fresh variables can express such definitions.

This stresses the Symbol Game's handling of large certificate artifacts: proofs are files bound by hash, not inline text. It also stresses the OEWAS (Omega Engine Workflows, Agents, Skills) workflow that splits encoding from proving, and the OEEIS (Omega Engine Epistemic Immune System) where solver output is the tempting place to smuggle an unchecked claim. A pass shows that the module encodes and certifies these families. It does not show a better SAT solver.

## 3. Formal Problem and Bounds

Each case is a structured problem `P` from one of five families, together with the judge's canonical CNF `F_P` in DIMACS format and a published variable map. The operator's generator guarantees that `P` has a solution if and only if `F_P` is satisfiable. The second checker cross-tests that correspondence on every public example.

1. Graph `k`-colouring: at most 150 vertices, `k ≤ 6`.
2. Pigeonhole `PHP(n+1, n)` for `5 ≤ n ≤ 14`, plus variants that block or add holes, so some are satisfiable.
3. Latin-square completion: order at most 12, 30–60% pre-filled.
4. Tseitin parity formulas on connected graphs: at most 60 vertices, degree at most 4. Odd total charge makes them unsatisfiable, even charge satisfiable.
5. Exact cover and polyomino tiling on boards up to 10×10.

Symmetry-breaking clauses added to a solver's input change the formula, so a DRAT proof of the augmented formula does not refute `F_P` unless the proof justifies those clauses. Edge cases: empty and tautological clauses in `F_P`, duplicate clauses, satisfiable instances one hole or one colour away from unsatisfiable ones, and graphs with isolated vertices.

## 4. Deliverable and Output Contract

**Mode: frozen module.** The module is `def solve(case: dict) -> dict`, synthesized by the model and making no model calls at scoring time. The sandbox gives every arm the same pinned CaDiCaL binary and the same pinned drat-trim binary. The module may re-encode `P`, but an `UNSAT` answer must refute `F_P` itself. A `SAT` answer is a problem-level solution.

```json
{"case_id": "sat_ex_03", "family": "coloring", "n": 4, "k": 3, "edges": [[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]], "cnf_path": "cases/sat_ex_03.cnf", "cnf_sha256": "<64 hex>"}
{"case_id": "sat_ex_03", "status": "SOLVED", "kind": "UNSAT", "proof_format": "DRAT", "proof_path": "proofs/sat_ex_03.drat", "cnf_sha256": "<64 hex>"}
{"case_id": "sat_ex_01", "status": "SOLVED", "kind": "SAT", "solution": {"colour": [0, 1, 2]}}
{"case_id": "sat_ex_07", "status": "OUT_OF_SCOPE", "witness": {"field": "edges[4]", "reason": "VERTEX_OUT_OF_RANGE"}}
{"case_id": "sat_ex_09", "status": "UNKNOWN", "code": "SOLVER_TIMEOUT"}
```

A complete certificate is one of two things. For `SAT`, a solution that the problem-level checker accepts against `P` directly, with integers only (strict `type(v) is int`, so `True` is rejected). For `UNSAT`, a DRAT or LRAT file whose bound `cnf_sha256` equals the hash of `F_P`, which ends by deriving the empty clause, and which both proof checkers accept.

## 5. Participant Packet

- `TASK.md`: family grammars, the DIMACS conventions, the proof formats and the JSON Schema.
- 10 public examples with exact inputs, canonical CNFs and expected outputs: one satisfiable and one unsatisfiable per family, where the family allows it. The unsatisfiable examples include `PHP(6,5)` with a reference DRAT proof.
- `runner.py`, which runs `solve` in the U09 sandbox and self-checks proofs with the pinned drat-trim.
- `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 40 cases, 8 per family. The families that admit both answers are balanced between satisfiable and unsatisfiable, and the large pigeonhole and Tseitin sizes are over-represented.
- **Relabel and gauge controls:** 16. CNF variable renumbering with polarity flips, clause-order shuffles, vertex relabelling, colour permutation, and Latin-square row, column and symbol permutations, which are isomorphic presentations. Verdicts must match the base case.
- **Poisoned but schema-valid:** 8. `note` fields claiming the wrong answer, boundary instances one hole from flipping, `F_P` with tautologies and duplicates, and a DIMACS header whose clause count is wrong. The correct answer to the last is `OUT_OF_SCOPE` with the line number.
- **Exact checker:** a Rust problem-level checker for `SAT` answers, and drat-trim in backward mode for DRAT, emitting LRAT.
- **Independent second checker:** a separately written problem-level checker in Python, and an independent LRAT checker pinned at packet-build time, preferably a formally verified one. DRAT checkers can differ on unit-clause deletions; the LRAT pass settles that.
- **Mutation suite:** the checker must reject a deleted lemma, a flipped literal in a lemma, a proof without the empty clause, a proof bound to a different CNF hash, a colouring violating one edge, a colour out of range, a Boolean `true` in place of `1`, and a proof that deletes an original clause and later needs it.

## 7. Arms and Baselines

Arms A to D follow the protocol with identical sandbox tools. **Arm E** is the pinned CaDiCaL run directly on `F_P` with DRAT output, checked by drat-trim, with no model and no re-encoding.

The estate's `omega_engine/crates_rs/omega_solvers/src/solver_cadical_unsat_core.rs` cannot serve as E. Its `localize` is a stub that always returns `None`, and the estate has no DRAT or LRAT code. A tie between A and E means the module added nothing beyond calling the solver. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.50 per arm, about 1.4 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, `deepseek/deepseek-r1-distill-llama-70b`. The receipt binds the SHA-256 of the solver and checker binaries, each CNF and each proof.

Q40 lessons apply:

- the JSON Schema and verbatim examples are in the prompt;
- repair turns carry the task, schema, full module and failing case;
- arm A draws at least 4 candidates per turn;
- execution is sandboxed;
- budget is checked before every call.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, the frozen module settles all 40 base cases correctly, all relabel controls agree with their base, and no poisoned case gets a false `SOLVED`. Any accepted proof that the second checker rejects fails the arm.
- **Primary metric (pre-registered):** base cases settled within the 120-second per-case limit. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Secondary:** A vs E on the pigeonhole and Tseitin rows only, plus total proof size.
- **Seeds:** 3; the full distribution is reported.

## 10. Interpretation

Arm E is expected to settle colouring, Latin-square and tiling cases. Large pigeonhole and Tseitin instances are where plain CDCL output runs out of time. If A settles those with short extension-style proofs that both checkers accept, the model contributed to proof construction, not only to the solver call. If A only matches E, the result is automation. A failure on encoding faithfulness, where a module's own encoding is refuted instead of `F_P`, is a harness-visible defect; it is not scored as a pass.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is an `UNSAT` claim; Signal 2 is a proof hash that does not bind `F_P`.
- **Staged acceptance.** Staged acceptance in the style of `HopfieldNinioProofreader` runs hash binding, then drat-trim, then the LRAT replay before a proof is admitted.
- **Expected antimorphisms:** AM-2 CUT_ABSOLUTE_CLAIM (`UNSAT` without a proof), AM-FSP-2 (a proof of the module's own encoding) and AM-3 (a `SAT` claim whose solution skips constraints).
- **Layer 2:** grammar-masked JSON for the status envelope only, via `carrier_gbnf` in `omega_engine_symbol_game/domain/carrier_decoding.py` (unwired). Proofs are files and are never decoded under a mask.
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps a per-family table of encodings tried and their proof sizes.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (family grammar and canonical CNF shown), `Λ` (split into encode, solve and certify sub-turns), `I`, `R` (public cases failing, or proofs rejected), `D` steps, `E`, `T`. `M` records refusals such as timeouts. The `ObstructionScore` sets Φ₁ to the number of public cases unsettled and `active_count` to certificates rejected by drat-trim; Γ₂ is unused (0). Run folders keep proofs by hash in the cemetery, including rejected ones.

Operands to mine:

- refute the canonical CNF, never your own encoding;
- for pigeonhole, emit Cook-style extension definitions as RAT clauses on fresh variables;
- symmetry breaking must be justified in the proof or kept out of `UNSAT` runs;
- map models back to problem level and check there before emitting.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_solvers`, the catalog reuse row. Its CaDiCaL localizer is a stub, so a real solver backend with DRAT output is new work that belongs in that crate.
- Problem-level checkers should go in Rust next to it. The bench harness `bench/matrix/run_repair_matrix.py` shows the arm-matrix shape.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). The catalog row lists no extra upgrades; [U10](../../upgrades/u10_synthesis_loop_v2.md) is recommended because the deliverable is synthesized code.

## 14. Claim Hygiene

- **Supports:** the frozen module settled k of 40 hidden cases, and every `UNSAT` answer carries a proof of the judge's CNF accepted by two independent checkers.
- **Does not support:** a faster SAT solver, general proof-complexity results, or correctness of any encoding beyond the published correspondence.
- **Narrowest defensible claim:** on these five families, the synthesized module's certified settle rate was X, and on the pigeonhole and Tseitin rows it was Y against arm E's Z.
- **Next test:** feed the certified pipeline into C043's infeasible cases, and add PR-style (propagation redundancy) proofs as a second format.
