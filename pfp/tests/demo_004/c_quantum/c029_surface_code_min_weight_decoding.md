# C029: Minimum-Weight Surface-Code Decoding

**AuthorityEffect:** None. **Status:** planned. **Domain:** c_quantum. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> decoder that returns exact minimum-weight corrections for hidden surface-code syndromes at
> distance 3 to 7, each with a certificate of optimality, for under $1.

## 2. Why This Task

For independent bit-flip errors, a minimum-weight correction for the surface code can be found by minimum-weight perfect matching of the syndrome defects, with lattice path lengths as edge weights (Dennis, Kitaev, Landahl, Preskill 2002). A correction's syndrome is checked by one sparse F2 product. Its optimality has a compact certificate: the dual variables of the matching linear program, including the odd-set constraints, whose objective equals the correction's weight.

The task asks for both halves. A decoder that returns a valid but non-minimal correction fails, and so does one that claims optimality without dual variables that check. It stresses OEWAS (Omega Engine Workflows, Agents, Skills) assembly of graph algorithms and OEEIS (Omega Engine Epistemic Immune System) screening of greedy answers presented as optimal.

## 3. Formal Problem and Bounds

Codes:

- The rotated surface code on a d × d grid of data qubits, with parameters [[d², 1, d]], for d ∈ {3, 5, 7}.
- The toric code on an L × L torus, [[2L², 2, L]] (Kitaev 2003), for L ∈ {3, 4, 5}.

Noise model: X errors only (code-capacity). Input: the Z-type parity-check matrix H_Z (given explicitly), per-qubit positive integer weights w_q ∈ {1, …, 5}, and a syndrome s ∈ F2^m. Find a correction c ∈ F2^n with H_Z c = s that minimizes Σ_q w_q c_q.

This is minimum-weight decoding, not maximum-likelihood decoding. A minimum-weight correction may differ from the true error by a logical operator and is still scored correct. Ties are allowed; any minimizer is accepted.

For the toric code the rows of H_Z sum to zero, so a syndrome of odd total parity is not in the image. That case is `OUT_OF_SCOPE`, with the dependency as witness.

Edge cases: s = 0 (empty correction); a single defect next to a boundary; defects whose cheapest pairing goes through a boundary; a pair of defects closer across the periodic direction of the torus; weighted cases where the minimum path is not the shortest in hop count; an error chain of weight ⌈d/2⌉, where the minimum-weight correction completes a logical operator.

## 4. Deliverable and Output Contract

A frozen module `solve(case: dict) -> dict`. Input and outputs:

```json
{"case_id": "sc_14", "code": "rotated", "distance": 3, "hz": "…m x n 0/1 rows…",
 "weights": [1, 1, 2, 1, 1, 1, 3, 1, 1], "syndrome": [1, 0, 0, 1]}
{"id": "sc_14", "status": "SOLVED", "correction": [4], "weight": 1,
 "certificate": {"pairs": [[0, 3]], "boundary_matches": [],
                 "vertex_duals": ["1/2", "…"], "odd_set_duals": [[[0, 1, 3], "0"]]}}
{"id": "sc_15", "status": "OUT_OF_SCOPE", "witness": {"kind": "odd_parity_on_torus", "rows": "all"}}
{"id": "sc_16", "status": "UNKNOWN", "refusal_code": "DISTANCE_OUT_OF_BOUNDS"}
```

A `SOLVED` answer is complete when: H_Z c = s over F2; the stated weight equals Σ w_q c_q; and the dual variables are feasible for the matching LP on the defect graph (defects plus boundary copies, edge weights equal to exact shortest-path costs that the checker recomputes) and their objective equals the stated weight. The checker never trusts solver-supplied distances.

## 5. Participant Packet

- `TASK.md` with §3 and §4, the rotated-code and toric-code layouts, the boundary-copy construction for the defect graph, and the matching LP with odd-set constraints written out.
- `examples/`: 10 cases with exact outputs: s = 0, a single interior pair, a boundary match, a weighted detour, a torus wrap-around pair, a chain of weight ⌈d/2⌉ for d = 3, an odd-parity toric syndrome and a malformed case.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 36 syndromes: 8 each for rotated d = 3, 5, 7, and 4 each for toric L = 3, 4, 5, with weights uniform in half the cases and random in {1, …, 5} in the rest. Errors are sampled at several rates so defect counts range from 0 to about 2d.
- **Relabel and gauge controls:** 10 controls: a lattice symmetry of the code (reflection, or translation on the torus) applied to syndrome, weights and H_Z; a relabelling of qubits and checks. The minimum weight is invariant.
- **Poisoned-but-schema-valid cases:** 6 cases where greedy nearest-neighbour pairing is suboptimal, where hop-count distance and weighted distance disagree, and where the minimum crosses a logical class.
- **Exact checker (Rust):** F2 syndrome check, exact shortest paths, and dual feasibility and equality in exact rationals.
- **Independent second checker:** exhaustive enumeration of the coset c₀ + ker H_Z. For rotated d = 7 the kernel has dimension (d² + 1)/2 = 25, about 3.4·10⁷ corrections; for toric L = 5 it has dimension 26. Both are feasible in Rust with bit operations and share no code with matching.
- **Mutation suite:** a correction with the right syndrome and one extra qubit; a correction with the wrong syndrome; a dual that is feasible but has a smaller objective; a dual violating one odd-set constraint; a stated weight not equal to the correction's weight.

## 7. Arms and Baselines

Arms A–D per the protocol, each synthesizing the decoder. Arm E is the no-model baseline: a blossom matching implementation that emits primal and dual solutions, written separately from both checkers. Exhaustive coset search alone cannot serve as E, because it produces no dual certificate. E is expected to pass; the challenge measures whether an arm synthesizes a correct certified decoder. Arm F does not apply.

## 8. Budget, Models and Provenance

$1.00 per arm, enforced before each call. Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, Qwen3 32B, `qwen/qwen3-30b-a3b`. Nothing beyond the protocol.

## 9. Pass Gates and Statistics

- **Capability gate:** 36/36 base and 10/10 controls, both checkers accepting.
- **Primary metric (pre-registered):** per-case certified-optimal rate, A vs B, paired exact McNemar within seed-matched runs.
- **Seeds:** at least 3 per arm.
- **Secondary:** the rate of valid-but-suboptimal corrections, and the rate of optimal corrections without a valid dual.

## 10. Interpretation

- An arm that submits exhaustive search with an enumeration log instead of duals fails the certificate requirement; the certificate format is part of the task.
- Many optimal corrections with invalid duals means the model can decode but cannot certify; compare with C022.
- A pass says nothing about thresholds, circuit-level noise or real-time decoding.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no required OEEIS hooks. Relevant mechanisms:

- **Danger gate:** signal 1 is a correction with the right syndrome; signal 2 is a dual objective below the stated weight. Together they mark a false optimality claim.
- **Kinetic proofreading:** syndrome, then weight, then dual feasibility, then objective equality.
- **Clonal maturation:** repair operands for boundary handling may be refined across distances.

No Layer-1 or Layer-2 controls. Host scratch space (U12) holds the defect list and the checker-computed distance matrix, so the model never computes lattice distances in text.

## 12. Run Folder, DDC Trace and Operand Mining

Expected DDC pattern: `C` (expose layout and syndrome), `I` (integrate the defect graph with boundary copies), `R` (residual: the gap between the current matching weight and the best dual bound), `D` as augmenting steps close the gap, `E` when the gap is zero, and `T`. Logged measures: unmatched defects, primal weight, dual objective and the gap.

Operands expected: (1) add one boundary copy per defect, joined to each other at zero cost; (2) recompute distances with weights, not hop counts; (3) an optimality certificate is a dual solution with zero gap; (4) the toric code's odd-parity syndromes are outside the image.

## 13. Estate Reuse and Prerequisites

- `omega_engine/crates_rs/omega_quantum_physics/src/toric.rs` (2 × 2 toric code) and `binary_field.rs`.
- `omega_engine/crates_rs/omega_majorana` (GF(2) torus parity play, `repair_capacity.rs`) for layouts; its receipts are diagnostic only.
- `omega_engine/crates_rs/omega_homology` (boundary maps: a syndrome is the boundary of an error chain) and `omega_engine/crates_rs/omega_solvers` (network simplex and max-flow, which do not solve general matching).
- A blossom matching implementation with dual output is not in the estate and is new Rust work.
- Upgrades: base only: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).

## 14. Claim Hygiene

- **Supports:** whether an arm can synthesize a minimum-weight decoder that proves optimality through matching duals for small surface and toric codes.
- **Does not support:** claims about decoding thresholds, maximum-likelihood decoding, fault tolerance or hardware.
- **Narrowest defensible claim:** "Arm X returned certified minimum-weight corrections for k of 36 hidden syndromes at distance at most 7."
- **Next test:** C039, which asks for the ground-space degeneracy that the logical classes here index.
