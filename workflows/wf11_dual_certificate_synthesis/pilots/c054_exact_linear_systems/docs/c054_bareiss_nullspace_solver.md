# C054: Exact Linear Systems with Inconsistency Witnesses

**AuthorityEffect:** None. **Status:** planned. **Domain:** f_program_synthesis. **Tier:** T1.
**Budget:** $0.10 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen exact solver for `A x = b` that returns a solution with a certified nullspace basis, or a left-null vector proving inconsistency, for under $0.10.

## 2. Why This Task

Every claim here has a short exact certificate, and the checker never needs to trust a rank computation:

- **A solution** is checked by one matrix-vector product.
- **A nullspace basis** is checked by `A N = 0`, plus a rank certificate. A nonsingular `r × r` minor of `A` proves `rank A ≥ r`. `n − r` independent kernel vectors, shown independent by a nonsingular minor of `N`, prove `rank A ≤ r`.
- **Inconsistency** is witnessed by `y` with `yᵀA = 0` and `yᵀb ≠ 0`.

Fraction-free Bareiss elimination (Bareiss 1968) keeps intermediate integers polynomially bounded. Naive rational elimination is correct but can blow up, and float elimination is simply wrong.

This is a T1 warm-up. It stresses the Symbol Game's U10 loop on a task whose estate baseline is strong, the OEWAS (Omega Engine Workflows, Agents, Skills) sampling step, and the OEEIS (Omega Engine Epistemic Immune System) against unproven rank claims. A pass shows certified synthesis, not new linear algebra.

## 3. Formal Problem and Bounds

The input is `A ∈ ℚ^{m×n}` and `b ∈ ℚ^m`, with `0 ≤ m, n ≤ 40`. Integer entries are at most `10¹²` in absolute value, and rational entries have denominators at most `10⁶`.

- **CONSISTENT:** `x` with `A x = b`, and `N ∈ ℚ^{n×(n−r)}` with `A N = 0`. The rank certificate is a row set `R` and a column set `K` with `|R| = |K| = r` and `det A[R, K] ≠ 0`, together with a row set `J` of `N`, `|J| = n − r`, with `det N[J, :] ≠ 0`.
- **INCONSISTENT:** `y ∈ ℚ^m` with `yᵀA = 0` and `yᵀb ≠ 0`.

The hidden set must contain:

- the zero matrix;
- `m = 0` or `n = 0` (declared edge conventions);
- square nonsingular, square singular and wide or tall systems;
- `b = 0`;
- rank-deficient consistent systems;
- entries producing intermediate growth beyond `2⁶⁴`;
- rational entries with coprime large denominators.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model, makes no model calls at scoring, and runs in the U09 sandbox. Rationals are canonical strings: integers carry no slash, and gcd = 1. `N` is given as a list of column vectors.

```json
{"case_id": "ls_ex_01", "A": [["1","2","3"],["2","4","6"]], "b": ["1","2"]}
{"case_id": "ls_ex_01", "status": "SOLVED", "kind": "CONSISTENT", "x": ["1","0","0"], "null_basis": [["-2","1","0"],["-3","0","1"]], "rank": 1, "rank_rows": [0], "rank_cols": [0], "null_rows": [1,2]}
{"case_id": "ls_ex_02", "A": [["1","2","3"],["2","4","6"]], "b": ["1","3"]}
{"case_id": "ls_ex_02", "status": "SOLVED", "kind": "INCONSISTENT", "y": ["-2","1"]}
{"case_id": "ls_ex_07", "status": "OUT_OF_SCOPE", "witness": {"reason": "ROW_LENGTH_MISMATCH", "row": 1}}
{"case_id": "ls_ex_09", "status": "UNKNOWN", "code": "SIZE_LIMIT"}
```

A certificate is complete when every stated equality holds exactly, both minors have nonzero determinant as computed by the checker, the row and column index sets are valid and duplicate-free, and `rank + len(null_basis) = n`.

## 5. Participant Packet

- `TASK.md` with the JSON Schema and the empty-matrix conventions.
- 10 public examples with verbatim input and output JSON: the two examples above; a nonsingular 3×3; the zero matrix; `b = 0`; a tall inconsistent system; a rational-entry case; a growth case; `n = 0`; a malformed row.
- `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 32 systems, 22 consistent and 10 inconsistent, with ranks spread from 0 to `min(m, n)`.
- **Relabel and gauge controls:** 12. Each must keep its verdict and rank: row permutation (with `b`); column permutation (the solution coordinates are permuted); scaling a row by a nonzero rational; adding a multiple of one row to another (the solution set is preserved).
- **Poisoned but schema-valid:** 8. `note` fields claiming full rank, non-canonical rationals like `"4/2"` in the input (allowed by the input schema and to be normalised), and systems that are consistent only because of one exact cancellation, which floats miss.
- **Exact checker:** Rust using `bareiss_determinant` in `omega_engine/crates_rs/omega_linear_algebra/src/determinant.rs` after clearing denominators, or the `omega_symbol_game` binary actions `exact_determinant` and `exact_rank`.
- **Independent second checker:** Python `fractions`, by a different author.
- **Mutation suite:** the checker must reject all of the following, and must never raise: `x` off by `1/10⁶` in one coordinate; a null vector not in the kernel; dependent null vectors (the minor is singular); a rank minor with determinant 0; an overstated rank; `y` with `yᵀb = 0`; float strings; Booleans; duplicate index sets.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is the estate's own exact linear algebra in `omega_engine/crates_rs/omega_linear_algebra` (Bareiss determinants, `image_kernel.rs`), wrapped by a deterministic certificate emitter, with no model. It is expected to pass everything. A tie with E means synthesis reached the estate's existing capability; that is the expected ceiling. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.10 per arm, about 280,000 tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen-2.5-7b-instruct`, `meta-llama/llama-3.1-8b-instruct`.

Q40 harness defects this spec closes: (1) schema and verbatim examples in every prompt; (2) every repair turn carries the task, the schema, the full module, the failing case, the expected and actual output, and the typed rejection; (3) at least 4 candidates per turn in A, and best-of-N in D; (4) u09 sandbox only; (5) pre-call `BudgetController`; (6) checker exceptions pause scoring.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, 32/32 base, 12/12 controls, and 8/8 poisoned with no false `SOLVED`.
- **Primary metric (pre-registered):** base cases passed. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Reported alongside:** cost per verified success, and the per-seed distribution.
- **Seeds:** 3.

## 10. Interpretation

The expected failures are missing rank certificates and float leakage, not wrong solutions. If A fixes certificate omissions faster than B, typed residuals help. If all arms pass, the family calibrates the harness. A pass by a 7B or 8B model would be a useful lower bound on model size for certified synthesis at this tier.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is a rank claim; Signal 2 is a singular certificate minor.
- **Kinetic proofreading.** Staged acceptance in the style of `HopfieldNinioProofreader` runs public cases, then the self-check, then the row-operation controls.
- **Expected antimorphisms:**
  - AM-3 (`CONSISTENT` without a rank certificate);
  - AM-FSP-2 (a singular minor offered);
  - AM-5 (a global sign inversion of `x`, which the equality check catches unless `b = 0`; flipping `y` is harmless and is not scored).
- **Layer 2:** grammar-masked JSON via `carrier_gbnf` (unwired, and dependent on U06).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps per-case equality residuals and the determinant verdicts of the minors.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C`, `I`, `R`, `D` steps, `E`, `T`, with `Λ` when rank-certificate extraction is split into its own sub-turn. The `ObstructionScore` sets Φ₁ to the sum of absolute entries of `A x − b`, `A N` and `yᵀA` over the public cases, and `active_count` to missing or singular minors plus failing cases. Γ₂ is unused (0).

Operands to mine:

- record pivot rows and columns during elimination; they are the rank certificate;
- the free-variable identity block gives the null minor for free;
- the last nonzero row of the eliminated augmented matrix gives `y`;
- clear denominators, then run Bareiss.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_linear_algebra`, the catalog reuse row: `determinant.rs` (`bareiss_determinant`) and `image_kernel.rs`.
- The `omega_symbol_game` binary actions `exact_determinant` and `exact_rank`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extra [U10](../../upgrades/u10_synthesis_loop_v2.md).

## 14. Claim Hygiene

- **Supports:** a named model synthesized a frozen module that returned complete exact certificates for k of 32 hidden linear systems, at the recorded cost.
- **Does not support:** numerical linear-algebra competence, speed, or any arm advantage without the paired test.
- **Narrowest defensible claim:** for rational systems with `m, n ≤ 40`, certified synthesis succeeded in s of 3 seeds for $0.10 per arm.
- **Next test:** integer systems with Smith normal form certificates, reusing `smith_normal_form_checked`.
