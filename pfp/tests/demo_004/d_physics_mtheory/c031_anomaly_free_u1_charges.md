# C031: Anomaly-Free Chiral U(1) Charge Assignments

**AuthorityEffect:** None. **Status:** planned. **Domain:** d_physics_mtheory. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> solver that enumerates, up to symmetry, every chiral integer charge assignment with
> Σq = Σq³ = 0 for up to 12 Weyl fermions within a bound, and completes or refutes partial
> spectra, for under $1.

## 2. Why This Task

For a U(1) gauge theory with n left-handed Weyl fermions of integer charges qᵢ, the cubic gauge anomaly and the mixed gauge-gravitational anomaly cancel exactly when Σ qᵢ³ = 0 and Σ qᵢ = 0. A general solution of these two Diophantine equations was given by Costa, Dobrescu and Fox (2019); Allanach, Gripaios and Tooby-Smith (2019) gave a geometric treatment. Checking a proposed assignment takes two sums. Enumerating all of them within a bound, without missing or duplicating any up to symmetry, is where answers go wrong.

The task stresses OEWAS (Omega Engine Workflows, Agents, Skills) search with exact integer residuals, and OEEIS (Omega Engine Epistemic Immune System) screening of vector-like solutions presented as chiral, and of counts that double-count symmetric copies.

## 3. Formal Problem and Bounds

A charge assignment is a multiset of n nonzero integers with gcd 1 (primitive), |qᵢ| ≤ Q, satisfying Σ qᵢ = 0 and Σ qᵢ³ = 0. It is **vector-like** if the multiset equals its own negation (charges pair as q, −q); otherwise it is **chiral**. Two assignments are equivalent if one is a permutation of the other or of its negation. The canonical representative is the lexicographically smaller of sort(q) and sort(−q).

Two query types:

1. **Enumerate** (n ≤ 10, Q ≤ 12): return every chiral canonical representative and the count.
2. **Complete** (n ≤ 12, Q ≤ 2·10⁶): given k fixed charges, find n − k further nonzero charges within the bound making a chiral primitive solution, or state that none exists.

Facts the hidden set uses:

- For n ≤ 4 there is no chiral solution. With q₄ = −(q₁ + q₂ + q₃), the identity (a + b + c)³ − a³ − b³ − c³ = 3(a + b)(b + c)(c + a) forces a pair to cancel, and then the remaining pair cancels too.
- For n = 5, (1, 5, −7, −8, 9) is a chiral solution: 1 + 5 − 7 − 8 + 9 = 0 and 1 + 125 − 343 − 512 + 729 = 0.
- Every other count and every completion answer is computed by the judge's two independent enumerations at packet-build time.

Edge cases: n ≤ 4 (empty list); non-primitive solutions (to be excluded); completions whose only candidates are vector-like; Q near 2·10⁶, where cubes approach 8·10¹⁸ and 64-bit sums overflow.

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Inputs and outputs:

```json
{"case_id": "u1_03", "query": "enumerate", "n": 5, "bound": 10}
{"id": "u1_03", "status": "SOLVED", "count": 2, "solutions": [[-10, -4, -2, 7, 9], [-9, -5, -1, 7, 8]]}
{"case_id": "u1_11", "query": "complete", "n": 7, "bound": 10, "fixed": [5, -8, 2]}
{"id": "u1_11", "status": "SOLVED", "completion": [1, -7, 9, -2]}
{"id": "u1_12", "status": "SOLVED", "completion": null, "claim": "NO_COMPLETION"}
{"id": "u1_13", "status": "OUT_OF_SCOPE", "witness": {"kind": "fixed_charge_exceeds_bound", "index": 1}}
{"id": "u1_14", "status": "UNKNOWN", "refusal_code": "SEARCH_NOT_FINISHED"}
```

The `u1_03` answer was checked by brute-force enumeration while writing this spec; the `u1_11` completion gives the multiset {1, 5, −7, −8, 9, 2, −2}, which is chiral because the multiset is not equal to its negation. An enumeration is correct when the list equals the judge's canonical set exactly, with no duplicates, and `count` equals its length. A completion is correct when the sums vanish, the charges are within bound, the result is primitive and chiral, and it extends the fixed charges. `NO_COMPLETION` is correct only if both judge enumerations find none. `OUT_OF_SCOPE` covers fixed charges that are zero, exceed the bound, or number more than n.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the canonical-form rule, the vector-like definition and the n ≤ 4 identity.
- `examples/`: 10 cases with exact outputs: enumerations for n = 3, 4 (empty), n = 5 with a small bound, and n = 6 with bound 5; four completions (two solvable, one only vector-like, one with no candidate); two malformed.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 12 enumerations (n from 5 to 10) and 20 completions (n from 6 to 12, bounds up to 2·10⁶), with 6 of the completions having no chiral completion.
- **Relabel and gauge controls:** 8 controls: permuting the fixed charges; negating every fixed charge (the answer set negates); swapping which charges are fixed and which are sought for a known solution. The existence answer and the count are invariant.
- **Poisoned-but-schema-valid cases:** 6 cases: completions whose only candidates are vector-like; completions whose only candidates share a common factor of 2; completions near the bound where 64-bit cube sums overflow.
- **Exact checker (Rust):** exact sums in 128-bit or big integers, primitivity, chirality, canonical form and set equality.
- **Independent second checker:** a second enumeration organised as meet-in-the-middle over pairs of partial (Σq, Σq³) sums, written separately from the first, which enumerates multisets directly with pruning. Both must agree on every count and every `NO_COMPLETION` before the packet is sealed.
- **Mutation suite:** a list containing a vector-like solution, a list with a solution and its negation both present, a non-primitive completion, a completion off by one in the cubic sum, a count that differs from the list length.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the solver. Arm E is the no-model baseline: the direct multiset enumerator with sum pruning, run under the same 60-second sandbox limit per case. E should pass most enumerations; large-bound completions are where search strategy matters. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `qwen/qwen3-30b-a3b`. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 32/32 base cases and 8/8 controls.
- **Primary metric (pre-registered):** per-case correct rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** completion accuracy at bounds above 10⁵, and the rate of vector-like or non-primitive answers.

## 10. Interpretation

- A correct count with a wrong list, or the reverse, is scored wrong; both must match.
- If every arm fails only the overflow cases, the failure is integer width, not search.
- Reproducing the judge's enumerations certifies arithmetic. It says nothing about which U(1) extensions of the Standard Model are realized, and a single U(1) with these fermions is not a physical model.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a chiral claim; signal 2 is a multiset equal to its negation. Together they catch the vector-like antimorphism. A global sign flip of a whole list (antimorphism AM-5) is not an error here but must not double the count.
- **Thymus:** the self-panel includes the n ≤ 4 identity, so operands claiming a chiral solution with four fermions are rejected.
- **Kinetic proofreading:** linear sum, then cubic sum, then primitivity, then chirality.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds partial (Σq, Σq³) tables for meet-in-the-middle search.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose query), `I` (integrate fixed charges), `R` (residual: the pair (Σq, Σq³) of the current partial assignment), `D` as the residual reaches (0, 0), `M` on a candidate that fails primitivity or chirality, `E` on an exact solution, `T`. For enumerations, a `Λ` step lifts from partial sums to the meet-in-the-middle table. Logged measure: |Σq| + |Σq³| for each candidate.

Operands expected: (1) the cube-sum factorization that rules out n ≤ 4; (2) the canonical form under permutation and global sign; (3) cube sums in 128-bit or big integers; (4) (1, 5, −7, −8, 9) as a seed for merging constructions.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_kernel` (exact integers and rationals, digests).
- `omega_engine/crates_rs/omega_search` (beam search, constraint satisfaction) for arm A's completion search.
- No anomaly-equation module exists in the estate; both enumerators are new Rust work.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize an exact enumerator and completer for the U(1) anomaly equations within stated bounds.
- **Does not support:** any claim about new physics, dark sectors or string compactifications; any claim that the general solution was rederived.
- **Narrowest defensible claim:** "Arm X matched the judge's exact enumerations and completion answers on k of 32 hidden anomaly queries."
- **Next test:** C032, where anomaly cancellation involves gravitational and tensor multiplets in six dimensions.
