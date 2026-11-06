# C047: Recurrence and Generating-Function Discovery

**AuthorityEffect:** None. **Status:** planned. **Domain:** e_formal_math. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a frozen module that finds linear recurrences, with constant or polynomial coefficients, for hidden integer sequences, or proves that none exists within declared bounds, verified on held-out terms and against the hidden law, for under $0.50.

## 2. Why This Task

Checking a proposed recurrence against more terms is cheap. For constant-coefficient (C-finite) sequences, the judge can decide exactly whether a recurrence holds for all `n`. It does this by comparing the proposed characteristic polynomial and initial terms with the hidden law. Guessing is where models fail. They pattern-match famous sequences, overfit the prefix, or ignore a preperiod.

This is a deliberate E-dominated warm-up. Linear algebra over ℚ (Berlekamp–Massey for C-finite sequences, Massey 1969, and a holonomic guesser) should settle every case that is within the bounds. The interesting rows are decoys and poisoned notes.

The challenge stresses the Symbol Game's residual accounting on exact rationals, and the OEWAS (Engine Workflows, Agents, Skills) workflow that tries C-finite before polynomial-coefficient ansätze. It stresses the OEEIS (Engine Epistemic Immune System) against "this is the Fibonacci sequence"-style recall. A pass does not show discovery of new mathematics.

## 3. Formal Problem and Bounds

Input: the first `N` terms (`30 ≤ N ≤ 60`) of an integer sequence `a(0), a(1), …`, with bounds `(r_max, d_max)`, where `r_max ≤ 8` and `d_max ≤ 3`.

A recurrence is `Σ_{i=0}^{r} p_i(n) · a(n+i) = 0` for all `n ≥ n₀`, with each `p_i ∈ ℚ[n]` of degree at most `d`, `r ≤ r_max`, `d ≤ d_max`, and `p_r(n) ≠ 0` for every integer `n ≥ n₀`, so that each term is determined by the previous ones.

The judge generates each sequence from a known law:

- C-finite, with random integer coefficients, repeated roots and roots of unity;
- hypergeometric, first order with polynomial coefficients;
- holonomic of order 2 or 3;
- with a preperiod `n₀ > 0`;
- decoys: C-finite of order above `r_max`, or pseudo-random.

Public reference facts: Fibonacci satisfies `a(n) + a(n+1) − a(n+2) = 0`. The Catalan numbers satisfy `(4n+2)·C(n) − (n+2)·C(n+1) = 0`. Hidden laws are fresh, never taken from published tables.

`NONE_WITHIN_BOUNDS` is a real answer. Take `order = r_max` and `degree = d_max`. The unknown coefficients form a vector of dimension `u = (r+1)(d+1)`, and each equation at index `n` is linear in them. Build a nonsingular `u × u` minor from equations at indices at or beyond the largest start in the declared start range. It proves that only the zero vector fits the prefix, for every start in that range and every smaller order or degree, since those embed as special cases.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model and makes no model calls at scoring. The polynomials `p_i` are lists of canonical rational strings in ascending powers of `n`.

```json
{"case_id": "seq_ex_02", "terms": ["1","1","2","5","14","42","132","429","1430","4862"], "r_max": 2, "d_max": 1}
{"case_id": "seq_ex_02", "status": "SOLVED", "kind": "RECURRENCE", "start": 0, "polys": [["2","4"], ["-2","-1"]]}
{"case_id": "seq_ex_06", "status": "SOLVED", "kind": "NONE_WITHIN_BOUNDS", "order": 2, "degree": 1, "start_range": [0, 5], "minor_rows": [5, 6, 7, 8, 9, 10]}
{"case_id": "seq_ex_08", "status": "OUT_OF_SCOPE", "witness": {"reason": "NON_INTEGER_TERM", "index": 11}}
{"case_id": "seq_ex_09", "status": "UNKNOWN", "code": "SEARCH_LIMIT"}
```

The checks for `RECURRENCE` are:

1. The recurrence holds on all given terms and all held-out terms, which the judge keeps for up to `n = 3N`.
2. The leading polynomial `p_r` has no integer root at or beyond `start`.
3. For C-finite laws, an exact all-`n` check: the proposed characteristic polynomial must annihilate the hidden law. That is, the law's minimal polynomial must divide it, and the initial terms must match.
4. For hypergeometric laws, an exact check that the term ratio `−p_0(n)/p_1(n)` equals the hidden rational ratio.

For higher-order holonomic laws the held-out agreement is evidence only, and it is labelled as such. `NONE_WITHIN_BOUNDS` is checked by one exact determinant, which must be nonzero.

## 5. Participant Packet

- `TASK.md` with the recurrence form, the minor convention for `NONE_WITHIN_BOUNDS` and the JSON Schema.
- 12 public examples with exact input and output JSON: Fibonacci; Catalan; a C-finite sequence with a repeated root; a sequence with period 3; a preperiod case; central binomial coefficients; a pseudo-random decoy; an order-9 decoy under `r_max = 8`; a non-integer term; three generated sequences.
- `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 40 sequences: 14 C-finite, 8 hypergeometric, 6 holonomic of order 2 or 3, 4 with a preperiod, 8 decoys.
- **Relabel and gauge controls:** 16. Each is derived from a base sequence and has its own expected law: an index shift (drop the first `k` terms); scaling by a constant (the law is unchanged); sign alternation `(−1)ⁿ a(n)` (substitute into the law); a reversed-sign ansatz ordering.
- **Poisoned but schema-valid:** 8. `note` fields naming a famous sequence that matches the first 8 terms but diverges later, terms that exceed 2⁶³ within the prefix, and prefixes where a spurious low-order recurrence fits exactly the given `N` terms but fails on the held-out ones.
- **Exact checker:** Rust over `num_rational` (via `core_kernel`), covering recurrence replay, the leading-root check, polynomial divisibility and exact determinants through `engine/crates_rs/core_linear_algebra`.
- **Independent second checker:** Python `fractions` by a different author.
- **Mutation suite:** the checker must reject: a recurrence that fails only at a held-out index; a leading polynomial with an integer root in range; a characteristic polynomial missing one root; a singular minor offered for `NONE_WITHIN_BOUNDS`; the float string `"0.5"` as a coefficient; the trivial all-zero recurrence.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is Berlekamp–Massey over ℚ, followed by a deterministic holonomic guesser that solves the linear system for increasing `(r, d)`, with no model. E should settle every in-bounds case and every decoy. A tie with E is the expected outcome and would confirm that this task is automation. A model arm that beats E would most likely be exploiting a checker defect, which pauses scoring. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.50 per arm, about 1.4 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, `meta-llama/llama-3.1-8b-instruct`.

Q40 lessons apply:

- the schema is shown as real JSON;
- stateful repair carries the module, the failing sequence and the typed rejection;
- several candidates are drawn per turn;
- execution is sandboxed with a 30-second per-case limit;
- budget is checked before every call.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, all 40 base cases are correct, the relabel controls are consistent, and no poisoned case gets a spurious recurrence.
- **Primary metric (pre-registered):** base cases correct. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Secondary:** A vs E, reported for completeness.
- **Seeds:** 3.

## 10. Interpretation

Because E is complete for the declared bounds, this challenge measures whether the game helps a model synthesize the right linear algebra, and whether it resists recall bait. It does not measure mathematical insight. If A passes and B fails, the likely cause is structured repair over typed residuals. If every arm fails the poisoned rows by naming famous sequences, the lesson belongs to the OEEIS, not to the solver.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is a famous-sequence name in a `note` or in the model output; Signal 2 is a held-out mismatch.
- **Thymus-style self panel** over public examples before freezing.
- **Expected antimorphisms:** AM-2 (asserting the sequence is a named one), AM-FSP-2 (a singular minor offered as proof) and AM-4 (re-proposing the same overfit recurrence).
- **Layer 2:** a grammar mask for rational-string arrays, via `carrier_gbnf` (unwired).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the residual vector of the current candidate over all given terms.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (terms and bounds exposed), `I` (ansatz), `R` (residual vector over the prefix), `D` steps as `(r, d)` increase, `E` (zero residual and a nonsingular leading coefficient), `T`. `M` records refusals. The `ObstructionScore` sets Φ₁ to the sum of absolute residuals over the given terms and `active_count` to held-out failures in public replay; Γ₂ is unused (0).

Operands to mine:

- try C-finite by Berlekamp–Massey before any polynomial-coefficient ansatz;
- scan the start index for preperiods;
- prove absence with a nonsingular minor instead of saying "none found";
- ignore sequence names and trust residuals.

## 13. Estate Reuse and Prerequisites

- The catalog row lists no estate reuse. Exact rationals come from `engine/crates_rs/core_kernel`, and determinants from `engine/crates_rs/core_linear_algebra` (`bareiss_determinant`), or from the `exact_determinant` action of the `core_symbol_game` binary.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). No row extras; [U10](../../upgrades/u10_synthesis_loop_v2.md) is recommended.

## 14. Claim Hygiene

- **Supports:** the frozen module recovered k of 40 hidden laws, exactly verified for the C-finite and hypergeometric rows and held-out verified for the holonomic rows, and certified absence for the decoys.
- **Does not support:** a proof that a holonomic recurrence holds for all `n`, closed forms beyond the recurrence, or discovery of new sequences.
- **Narrowest defensible claim:** within `r ≤ 8` and `d ≤ 3`, the module's certified recovery rate was X, with E at Y.
- **Next test:** algebraic generating functions with exact annihilating polynomials, checked by the same exact pipeline.
