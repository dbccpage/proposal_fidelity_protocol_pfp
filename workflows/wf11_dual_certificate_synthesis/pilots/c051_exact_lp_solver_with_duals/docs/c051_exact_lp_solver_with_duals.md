# C051: Exact LP Solver with Dual and Farkas Certificates

**AuthorityEffect:** None. **Status:** planned. **Domain:** f_program_synthesis. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen rational simplex solver that certifies optimality, infeasibility and unboundedness on hidden linear programs for under $0.50.

## 2. Why This Task

This is the Q40 pattern moved to linear programming. A certificate is verified with a handful of exact dot products:

- a primal-dual pair with equal objective values proves optimality (weak duality);
- a Farkas vector proves infeasibility (Farkas' lemma);
- a feasible point plus an improving ray proves unboundedness.

Writing a solver that always emits them is harder than it looks. The known traps are sign conventions, degenerate pivots that cycle under Dantzig's rule, exact rational parsing, and the three-way status split.

This stresses the Symbol Game's synthesis loop (U10): stateful retraction over a module the model can see, typed checker rejections as obstructions, and strict descent across public examples. It stresses the OEWAS (Omega Engine Workflows, Agents, Skills) sampling-and-selection workflow, and the OEEIS (Omega Engine Epistemic Immune System) against sign-inverted duals. A pass shows that a ≤70B model can synthesize a certificate-emitting exact LP solver. It does not show a competitive LP solver.

## 3. Formal Problem and Bounds

Inequality form: maximize `c·x` subject to `A x ≤ b` and `x ≥ 0`, with `A ∈ ℚ^{m×n}`, `b ∈ ℚ^m`, `c ∈ ℚ^n`, `1 ≤ m, n ≤ 30`. Numerators and denominators are at most `10⁹`, and a few cases exceed `2⁶⁴` to catch fixed-width arithmetic.

The three outcomes and their certificates:

- **OPTIMAL:** `x ≥ 0`, `A x ≤ b`, `y ≥ 0`, `Aᵀ y ≥ c`, and `c·x = b·y`.
- **INFEASIBLE:** `y ≥ 0`, `Aᵀ y ≥ 0` and `b·y < 0` (Farkas' lemma for this form).
- **UNBOUNDED:** feasible `x` and `d ≥ 0` with `A d ≤ 0` and `c·d > 0`.

The hidden set must contain:

- degenerate vertices on which Dantzig's largest-coefficient rule can cycle (Bland's rule, Bland 1977, avoids cycling);
- multiple optimal primals and duals (any valid pair is accepted);
- zero rows and zero columns;
- `b` with negative entries (the origin infeasible, so phase one is needed);
- `m = 1` and `n = 1`;
- redundant constraints.

Arithmetic is exact rational throughout. Floating-point output is invalid.

## 4. Deliverable and Output Contract

**Mode: frozen module.** The deliverable is `def solve(case: dict) -> dict`, synthesized by the model, run with no model calls at scoring, and evaluated in the U09 sandbox. Rationals are canonical strings: `"n"` or `"n/d"` with `d > 1`, `gcd(n, d) = 1`, and no slash for integers.

```json
{"case_id": "lp_ex_01", "A": [["1","1"],["1","3"],["1","0"]], "b": ["4","6","3"], "c": ["3","2"]}
{"case_id": "lp_ex_01", "status": "SOLVED", "kind": "OPTIMAL", "x": ["3","1"], "y": ["2","0","1"], "value": "11"}
{"case_id": "lp_ex_02", "A": [["1","1"]], "b": ["-1"], "c": ["1","1"]}
{"case_id": "lp_ex_02", "status": "SOLVED", "kind": "INFEASIBLE", "farkas_y": ["1"]}
{"case_id": "lp_ex_03", "A": [["-1","1"]], "b": ["1"], "c": ["1","0"]}
{"case_id": "lp_ex_03", "status": "SOLVED", "kind": "UNBOUNDED", "x": ["0","0"], "ray": ["1","0"]}
{"case_id": "lp_ex_08", "status": "OUT_OF_SCOPE", "witness": {"field": "A[2]", "reason": "ROW_LENGTH_MISMATCH"}}
{"case_id": "lp_ex_09", "status": "UNKNOWN", "code": "PIVOT_LIMIT"}
```

The first example is degenerate: three constraints are tight at `(3, 1)`. A certificate is complete when every inequality listed in §3 for its kind holds exactly, vector lengths match, all values are canonical, and the stated `value` equals `c·x`. `OUT_OF_SCOPE` covers malformed cases only. `UNKNOWN` is honest, but it scores as unsettled.

## 5. Participant Packet

- `task.md`, which includes the JSON Schema itself, not a prose description of it.
- 14 public examples with verbatim input and output JSON: three degenerate optima; a degenerate program on which Dantzig's rule cycles; two infeasible programs (one needing phase one); two unbounded programs; zero rows and columns; `m = n = 1`; a large-integer case; two malformed inputs.
- `runner.py`, which runs `solve` in the sandbox and checks every public output with the reference checker.
- `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 40 programs: 24 optimal (10 degenerate), 8 infeasible, 8 unbounded.
- **Relabel and gauge controls:** 16. Each must keep its status; certificates are checked afresh.
  - variable permutation (columns of `A` and `c`);
  - constraint permutation;
  - positive row scaling of `A` and `b`;
  - positive scaling of `c`;
  - adding a redundant copy of one constraint.
- **Poisoned but schema-valid:** 8. `note` fields stating a wrong optimum; values like `"2/4"` that are non-canonical in input, which must be normalised on read (the input schema allows them); huge denominators; and a nearly unbounded program whose ray just fails.
- **Exact checker:** Rust over `BigRational` in `omega_engine/crates_rs/omega_solvers`, next to `exact_weighted_l1_lp.rs`.
- **Independent second checker:** Python `fractions`, written by a different author.
- **Mutation suite:** the checker must reject all of the following, and must never raise on malformed certificates, because a crash pauses scoring: one dual sign flipped; `x` perturbed by `1/10⁹` in one coordinate; `value` differing from `c·x`; a Farkas `y` with one negative entry; a ray with `A d ≤ 0` violated in one row; `"0.5"` as a value; Boolean entries; `"1/1"`; a certificate of the wrong kind for the status.

## 7. Arms and Baselines

Arms A to D follow the protocol.

**Arm E** is a pinned exact rational LP solver, for example SoPlex in exact mode or QSopt_ex, chosen and hashed at packet-build time, with its output converted into the same certificates. The estate's `exact_weighted_l1_lp.rs` is an exact sparse revised simplex over ℚ with a dual witness, but only for weighted-ℓ¹ projection problems, so it is not a general E. E should pass everything. A tie with E shows automation at the level of existing tools. The question is whether a ≤70B model can reach it by synthesis. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.50 per arm covers every call used to construct, debug and select. That is about 1.4 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, `deepseek/deepseek-r1-distill-llama-70b`. The module's SHA-256 is published before reveal.

Q40 harness defects this spec closes: (1) the schema and verbatim examples are in every prompt; (2) every repair turn carries `task.md`, the schema, the full current module, the failing input, the expected and actual output, and the checker's typed rejection; (3) arm A samples at least 4 candidates per turn, and arm D spends the whole budget on best-of-N; (4) execution happens only in the U09 subprocess sandbox; (5) `BudgetController` refuses over-budget calls before they are made; (6) checker exceptions pause scoring.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, the frozen module passes 40/40 base cases, all 16 controls, and all 8 poisoned cases with no false `SOLVED`.
- **Primary metric (pre-registered):** base cases passed. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Reported alongside:** Wilson intervals, and cost per verified success.
- **Seeds:** 3. Rows within a seed share one module, so the per-seed results are also reported.

## 10. Interpretation

Status-only correctness is not enough: a module that labels statuses correctly but emits invalid duals fails. If A passes and B fails at equal budget, stateful typed retraction helps synthesis here. If A ties D, sampling explains it. If A passes but needs most of the budget while B fails, record it as a capability difference, not an efficiency one. Infeasible and unbounded cases are the analogue of Q40's refusals and are reported separately.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Kinetic proofreading.** Staged acceptance in the style of `HopfieldNinioProofreader` runs public examples, then the module's own self-check, then relabel self-consistency, before a candidate is frozen.
- **Danger gate.** Signal 1 is a status claim; Signal 2 is a certificate inequality failure.
- **Expected antimorphisms:**
  - AM-5 global sign inversion (duals of the wrong sign, a `≥`/`≤` swap);
  - AM-3 (`SOLVED` without a certificate);
  - AM-4 (the same module resubmitted unchanged, which the host detects by hash and refuses with `M`).
- **Layer 2:** grammar-masked JSON for certificates, via `carrier_gbnf` in `omega_engine_symbol_game/domain/carrier_decoding.py` (unwired). Hosted support for grammars or `response_format` must first be added by U06.
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the current module, the failing-case table and a residual ledger per certificate inequality as scratch state, instead of the growing transcript.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (schema and examples exposed), `Λ` (decompose into parse, phase one, phase two, certify and self-check sub-turns), `I`, `R` (failing public cases with typed reasons), `D` steps that strictly reduce the obstruction score, `E` (all public pass and the self-check is green), `T` (freeze). `M` records refusals and duplicate submissions. The `ObstructionScore` sets Φ₁ to the sum over public cases of the violated certificate mass (`Σ max(0, (Ax − b)_i) + |c·x − b·y|` and the analogues), and `active_count` to failing public cases. Γ₂ is unused (0).

Operands to mine:

- state the dual sign convention for `≤` rows before writing code;
- parse rationals with exact fractions and reject floats;
- switch to Bland's rule after any degenerate pivot;
- run the certificate check inside `solve` before returning.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_solvers` (`exact_weighted_l1_lp.rs`).
- The `omega_symbol_game` binary actions `exact_solve_l1_primal_dual` and `verify_l1_certificate`, for the weighted-ℓ¹ subclass.
- `lean4/LpWeakDuality.lean`, which states weak duality for this matrix form. It imports Mathlib, is not in the core package, and has not been typechecked, so it is not cited as proof.
- The Q40 demo `omega_engine_projects/mssn_sn_symgam/demos/demo_q40_quantum_solver/` for the harness shape to avoid.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extra [U10](../../upgrades/u10_synthesis_loop_v2.md).

## 14. Claim Hygiene

- **Supports:** a named model, through the named arm, synthesized a frozen module that certified k of 40 hidden LPs exactly, verified by two checkers, at the recorded cost.
- **Does not support:** solver speed, numerical LP competence, or any claim that the game beats ordinary workflows unless the McNemar comparison shows it.
- **Narrowest defensible claim:** for inequality-form LPs with `m, n ≤ 30`, synthesis succeeded in s of 3 seeds, with a per-seed hidden pass rate of X.
- **Next test:** [C059](c059_cross_family_transfer_skeleton.md), which transfers this skeleton to max-flow and stabilizer families, and [C060](c060_self_verifying_checker_synthesis.md), which synthesizes the checker instead.
