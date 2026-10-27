# C053: Assignment Problems with Dual Potentials

**AuthorityEffect:** None. **Status:** planned. **Domain:** f_program_synthesis. **Tier:** T1.
**Budget:** $0.10 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen Hungarian-method solver whose assignments carry dual potentials proving optimality, or a Hall violator proving that no perfect assignment exists, for under $0.10.

## 2. Why This Task

The Hungarian method (Kuhn 1955) is textbook, and its certificate is the whole point. Potentials `u` and `v` with `u_i + v_j ≤ c_ij` on allowed entries, summing to the assignment's cost, prove optimality by LP duality. If some rows cannot be matched, a Hall violator proves it: a row set `S` with fewer allowed columns than rows.

Models often write a solver that finds the right permutation but cannot produce valid potentials, and that is exactly what the checker catches. This is a T1 warm-up for the synthesis loop, like C052. It stresses the Symbol Game's typed residuals (which dual inequality failed, and by how much), the OEWAS (Engine Workflows, Agents, Skills) sampling-and-selection step, and the OEEIS (Engine Epistemic Immune System) on "optimal" claims without duals. A pass shows certified synthesis. It does not show a fast solver.

## 3. Formal Problem and Bounds

An `n × n` cost matrix `C` with `n ≤ 60`, integer entries `|c_ij| ≤ 10¹⁸`, and `null` marking a forbidden pair. Sums can exceed `2⁶³`. The objective is to minimize `Σ_i c_{i,σ(i)}` over permutations `σ` that use only allowed pairs.

- **OPTIMAL:** `σ` together with `u ∈ ℤⁿ` and `v ∈ ℤⁿ` such that `u_i + v_j ≤ c_ij` for every allowed `(i, j)`, and `Σ u + Σ v = Σ c_{i,σ(i)}`. Integer potentials always exist for integer costs.
- **NO_PERFECT_ASSIGNMENT:** a row set `S` with `|N(S)| < |S|`, where `N(S)` is the set of columns allowed to some row in `S` (Hall's condition).

The hidden set must contain:

- negative costs;
- ties with many optimal assignments (any valid answer is accepted);
- costs above `2⁵³`;
- `n = 1`;
- a single allowed entry per row;
- forbidden patterns that pass a row-count check but fail Hall's condition;
- a maximization case flagged `"sense": "max"`, which must be negated consistently.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model, makes no model calls at scoring, and runs in the U09 sandbox. Integers are canonical strings; `σ` is a list of column indices.

```json
{"case_id": "as_ex_01", "sense": "min", "cost": [["4","1","3"],["2","0","5"],["3","2","2"]]}
{"case_id": "as_ex_01", "status": "SOLVED", "kind": "OPTIMAL", "sigma": [1,0,2], "u": ["3","2","2"], "v": ["0","-2","0"], "value": "5"}
{"case_id": "as_ex_04", "sense": "min", "cost": [["1",null,null],["2",null,null],["1","1","1"]]}
{"case_id": "as_ex_04", "status": "SOLVED", "kind": "NO_PERFECT_ASSIGNMENT", "hall_rows": [0,1]}
{"case_id": "as_ex_07", "status": "OUT_OF_SCOPE", "witness": {"reason": "NOT_SQUARE", "row": 2}}
{"case_id": "as_ex_09", "status": "UNKNOWN", "code": "ITERATION_LIMIT"}
```

A certificate is complete when:

- `σ` is a permutation using only allowed entries;
- every dual inequality holds exactly;
- `Σ u + Σ v = value`;
- `value` equals the permutation's cost.

For `NO_PERFECT_ASSIGNMENT`, the checker computes `N(S)` itself. For maximization, the potentials certify the negated problem, which `TASK.md` illustrates.

## 5. Participant Packet

- `TASK.md` with the JSON Schema.
- 10 public examples with verbatim input and output JSON: the 3×3 example above; a tie-heavy matrix; negative costs; `n = 1`; a Hall violation; a maximization case; a cost of `10¹⁸`; a non-square input; a matrix with a forbidden entry; a single allowed entry per row.
- `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 32 matrices: random, low-rank (many ties), sparse allowed patterns, 6 infeasible, and 4 maximization.
- **Relabel and gauge controls:** 12. Each must keep its optimal value, shifted as appropriate: row and column permutations; transposition; adding a constant to one row, which shifts the optimum by that constant and leaves the set of optimal permutations unchanged; adding a constant to all entries.
- **Poisoned but schema-valid:** 8. `note` fields giving a wrong optimum, a Hall violator hidden among rows with many allowed entries, a matrix whose only feasible permutation is expensive, and `null` in every entry of one column.
- **Exact checker:** Rust with `i128`, next to `engine/crates_rs/core_solvers`.
- **Independent second checker:** Python integers, by a different author.
- **Mutation suite:** the checker must reject all of the following, and must never raise: one potential increased by 1 so that a dual inequality breaks; a sum mismatch; a non-permutation `σ` (a repeated column); `σ` using a forbidden entry; a Hall set that actually satisfies Hall's condition; float strings; Booleans.

## 7. Arms and Baselines

Arms A to D follow the protocol.

**Arm E** is the estate's exact network simplex in `engine/crates_rs/core_solvers` (`i128` flows and potentials) on the transportation formulation. Its node potentials give `u` and `v` directly, and infeasibility is converted into a Hall set by the operator's deterministic post-processing.

A floating-point `linear_sum_assignment` is not an admissible E, because costs above `2⁵³` break it. E should pass everything, so a tie with E is expected. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.10 per arm, about 280,000 tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen-2.5-7b-instruct`, `meta-llama/llama-3.1-8b-instruct`.

Q40 harness defects this spec closes: (1) schema and verbatim examples in every prompt; (2) every repair turn carries the task, the schema, the full module, the failing case, the expected and actual output, and the typed rejection; (3) at least 4 candidates per turn in A, and best-of-N in D; (4) u09 sandbox only; (5) pre-call `BudgetController`; (6) checker exceptions pause scoring.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, 32/32 base, 12/12 controls, and 8/8 poisoned with no false `SOLVED`.
- **Primary metric (pre-registered):** base cases passed. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Reported alongside:** cost per verified success.
- **Seeds:** 3.

## 10. Interpretation

The expected failure mode is a correct permutation with invalid potentials. If A repairs that faster than B, because its residual names the violated `(i, j)` and the slack, typed retraction helps. If all arms pass, the family is calibrated but not discriminating. If only D passes, sampling beats structured repair at this budget, and C059's transfer design should take that into account.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is an optimality claim; Signal 2 is a failed dual inequality.
- **Kinetic proofreading.** Staged acceptance in the style of `HopfieldNinioProofreader` runs public cases, then the self-check, then the row-shift controls.
- **Expected antimorphisms:**
  - AM-5 (the `u`/`v` sign convention inverted, or maximization not negated);
  - AM-3 (`OPTIMAL` without potentials);
  - AM-FSP-2 (a Hall set that does not violate Hall's condition).
- **Layer 2:** grammar-masked JSON via `carrier_gbnf` (unwired, and dependent on U06).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the table of violated dual inequalities for the current module on public cases.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C`, `I`, `R` (dual violations), `D` steps, `E`, `T`, with `Λ` when potential extraction is split out. The `ObstructionScore` sets Φ₁ to the sum of positive dual slack violations `Σ max(0, u_i + v_j − c_ij)` plus `|Σu + Σv − value|` over the public cases, and `active_count` to failing cases. Γ₂ is unused (0).

Operands to mine:

- maintain `u` and `v` throughout the algorithm, not reconstructed at the end;
- negate costs for maximization and state it in the output;
- find Hall sets from the alternating-tree rows at failure;
- check the dual inequalities on all allowed entries before returning.

## 13. Estate Reuse and Prerequisites

- The catalog row lists no estate reuse. `engine/crates_rs/core_solvers` (network simplex with `i128` potentials) is the natural E and checker home.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extra [U10](../../upgrades/u10_synthesis_loop_v2.md).

## 14. Claim Hygiene

- **Supports:** a named model synthesized a frozen module that certified k of 32 hidden assignment problems with exact potentials or Hall sets, at the recorded cost.
- **Does not support:** efficiency at large `n`, or any arm advantage without the paired test.
- **Narrowest defensible claim:** for integer `n ≤ 60` assignment problems with forbidden entries, certified synthesis succeeded in s of 3 seeds for $0.10 per arm.
- **Next test:** rectangular and weighted bipartite matching with potentials, and inclusion as a family in [C059](c059_cross_family_transfer_skeleton.md).
