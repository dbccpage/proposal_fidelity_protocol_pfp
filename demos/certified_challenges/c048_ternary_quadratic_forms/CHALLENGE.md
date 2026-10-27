# C048: Ternary Quadratic Forms: Solution or Local Obstruction

**AuthorityEffect:** None. **Status:** planned. **Domain:** e_formal_math. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a frozen module that, for hidden forms `ax² + by² + cz² = 0`, returns either a nontrivial integer solution or a place where the Hilbert symbol is −1, for under $0.50.

## 2. Why This Task

Both answers are cheap to check, and both are hard to produce.

- **A solution is checked by evaluation.** Finding one requires either a descent algorithm (Legendre's method) or search within Holzer's bounds (Holzer 1950).
- **An obstruction is checked quickly too.** One Hilbert symbol `(−ac, −bc)_v = −1` at a single place `v` proves there is no rational point (Hasse–Minkowski for ternary forms). Computing that symbol at a given prime needs only valuations and a Legendre symbol, with no factoring. Finding the prime requires factoring the coefficients.

The asymmetry makes this a clean local-global exercise. It stresses the Symbol Game's handling of two certificate types for one question. It stresses the OEWAS (Engine Workflows, Agents, Skills) workflow that runs factorization, local tests and descent as separate stages. It stresses the OEEIS (Engine Epistemic Immune System) against the common error of reporting "no solution found" as "no solution exists".

## 3. Formal Problem and Bounds

Input: integers `a`, `b`, `c` with `|a|, |b|, |c| ≤ 10¹⁸`. A few cases go up to `10³⁰`, so the solver needs arbitrary precision. Coefficients are not guaranteed to be squarefree or pairwise coprime; the module must reduce them.

Legendre's theorem: for nonzero squarefree, pairwise coprime `a`, `b`, `c`, not all of the same sign, `ax² + by² + cz² = 0` has a nontrivial integer solution if and only if all three of these hold:

- `−bc` is a square modulo `|a|`;
- `−ca` is a square modulo `|b|`;
- `−ab` is a square modulo `|c|`.

Equivalently, the Hilbert symbol `(−ac, −bc)_v = 1` at every place `v`. The number of places where it is `−1` is even, so any failure shows up at a finite prime or at `∞`.

The symbol formulas are the standard ones (Serre, *A Course in Arithmetic*, Chapter III):

- **odd `p`:** `(u pᵅ, v pᵝ)_p = (−1)^{αβ(p−1)/2} (u/p)^β (v/p)^α`;
- **`p = 2`:** the `ε`/`ω` formula;
- **`v = ∞`:** `−1` exactly when both arguments are negative.

Edge cases:

- a zero coefficient (then `(1,0,0)`-type solutions exist trivially);
- all coefficients of one sign (the obstruction is at `∞`);
- obstructions only at `2`;
- coefficients sharing large square factors;
- semiprime coefficients with two roughly 30-bit factors.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model and makes no model calls at scoring. Integers are canonical decimal strings.

```json
{"case_id": "tq_ex_01", "a": "1", "b": "1", "c": "-2"}
{"case_id": "tq_ex_01", "status": "SOLVED", "kind": "RATIONAL_POINT", "x": "1", "y": "1", "z": "1"}
{"case_id": "tq_ex_02", "a": "1", "b": "1", "c": "-3"}
{"case_id": "tq_ex_02", "status": "SOLVED", "kind": "LOCAL_OBSTRUCTION", "place": "3"}
{"case_id": "tq_ex_03", "status": "SOLVED", "kind": "LOCAL_OBSTRUCTION", "place": "inf"}
{"case_id": "tq_ex_09", "status": "UNKNOWN", "code": "FACTORING_LIMIT"}
```

A complete certificate is one of two things. A `RATIONAL_POINT` is integers, not all zero, satisfying the equation exactly. A `LOCAL_OBSTRUCTION` is a place `v`, either a prime, which the checker verifies is prime, or `inf`, where `(−ac, −bc)_v = −1`.

`OUT_OF_SCOPE` applies only when the input is malformed, for example a non-integer string, and carries the field. `UNKNOWN` is honest when factoring exceeds the per-case limit. A `LOCAL_OBSTRUCTION` claim on a solvable form cannot pass.

## 5. Participant Packet

- `TASK.md` with the reduction rules, the Hilbert symbol formulas (including `p = 2`) and the JSON Schema.
- 12 public examples with exact input and output JSON: the three examples above; `x² + y² + z²` at `∞`; an obstruction at `2`; a form needing square-factor reduction; a zero coefficient; a large solvable form with its solution; two scaled variants; a malformed input; one `UNKNOWN`.
- `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 40 forms, 20 solvable and 20 obstructed. Of the obstructed forms, 6 are at `∞`, 4 at `2` and 10 at odd primes. Coefficients are random and include adversarial semiprimes.
- **Relabel and gauge controls:** 20, each with the same verdict and a transformed witness: permutations of `(a, b, c)`; multiplying one coefficient by a nonzero square `k²`; multiplying all three by a common nonzero integer; negating all three.
- **Poisoned but schema-valid:** 8.
  - `note` fields claiming "no solution";
  - forms whose only obstruction is at `2` while odd-prime tests pass;
  - coefficients with a shared large square factor;
  - coefficients above `2⁶³`.
- **Exact checker:** Rust with big integers. It evaluates the quadratic, tests the prime by deterministic primality (checked with a second method), and computes Hilbert symbols by the formulas above.
- **Independent second checker:** Python by a different author, plus labels from PARI/GP (`hilbert`, `qfsolve`) pinned at packet-build time.
- **Mutation suite:** the checker must reject: the trivial solution `(0,0,0)`; a solution off by one in `z`; a composite "place"; a prime where the symbol is `+1`; `inf` for a form with mixed signs; a Boolean in a coordinate.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is PARI/GP with `qfsolve`, plus a `hilbert` scan over the primes dividing `2abc`. It is deterministic, strong, and involves no model. A tie with E is expected on correctness. The question is whether a synthesized module without PARI reaches it within the per-case limit. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.50 per arm, about 1.4 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b`. The receipt records the PARI/GP version and hash.

Q40 lessons apply:

- real JSON is shown for both certificate kinds;
- stateful repair carries the module, the failing form and the checker's typed reason;
- several candidates are drawn per turn;
- execution is sandboxed with a 60-second per-case limit;
- budget is checked before every call.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, all 40 base forms are correct, all 20 controls are consistent, and there are no false obstructions or false points.
- **Primary metric (pre-registered):** base forms correct. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Reported separately:** solvable and obstructed rows, because obstructions at `∞` are trivial and must not carry the result. This mirrors the Q40 refusal lesson.
- **Seeds:** 3.

## 10. Interpretation

Obstructions at `∞` and small primes are easy. The evidence is in the rows that need factoring, reduction to squarefree coprime form, and descent to an actual point. If A beats B there, staged local-global decomposition helps. If all arms solve only the `∞` rows, the challenge has not separated them.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is an obstruction claim; Signal 2 is a checker-computed symbol of `+1` at the claimed place.
- **Staged acceptance.** Staged acceptance in the style of `HopfieldNinioProofreader` runs point evaluation before any obstruction search. That order is cheap and removes false obstructions.
- **Expected antimorphisms:**
  - AM-5 (a sign error in `−ac` or `−bc`);
  - AM-2 (asserting unsolvability from failed search);
  - AM-FSP-2 (a composite place).
- **Layer 2:** a grammar mask for integer strings, via `carrier_gbnf` (unwired).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the factorization table and the symbols already computed per prime.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (form exposed), `R` (reduce to squarefree coprime form), `Λ` (split into local tests and descent), `I`, `D` steps as the places are cleared, then either `E` (a point verified) or a direct `T` carrying an obstruction certificate. `M` appears only for `UNKNOWN`. The `ObstructionScore` sets Φ₁ to `|ax² + by² + cz²|` for the current candidate point and `active_count` to places not yet tested; Γ₂ is unused (0).

Operands to mine:

- reduce to squarefree, pairwise coprime form and record the transformation for the witness;
- test `∞` and `2` first;
- a prime witness must divide `2abc`, so scan only those primes;
- search inside Holzer's box before claiming `UNKNOWN`.

## 13. Estate Reuse and Prerequisites

- The catalog row lists no estate reuse. Big integers come from `engine/crates_rs/core_kernel` (`num_bigint` and `num_rational` are already workspace dependencies). The Hilbert-symbol checker is new Rust work.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). No row extras; [U10](../../upgrades/u10_synthesis_loop_v2.md) is recommended.

## 14. Claim Hygiene

- **Supports:** the frozen module settled k of 40 hidden ternary forms with a checked rational point or a checked local obstruction.
- **Does not support:** results on higher-degree or higher-dimensional forms, class-number or genus theory, or any claim that the module factors large integers efficiently.
- **Narrowest defensible claim:** for diagonal ternary forms with coefficients up to 10³⁰, the module's certified settle rate was X, and Y on rows needing factoring.
- **Next test:** non-diagonal ternary forms over ℚ, and quaternary forms, where Hasse–Minkowski still applies but the local analysis changes.
