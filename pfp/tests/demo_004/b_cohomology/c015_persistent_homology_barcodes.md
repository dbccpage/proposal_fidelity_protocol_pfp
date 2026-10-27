# C015: Persistent Homology Barcodes with Reduction Certificates

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that returns F₂ persistence barcodes of hidden filtered complexes with up to
> 2,000 simplices, each certified by a reduced boundary matrix, for under $0.50.

## 2. Why This Task

Persistent homology tracks when homology classes are born and die along a filtration. The standard algorithm reduces the filtered boundary matrix by column additions (Edelsbrunner, Letscher and Zomorodian 2002; Zomorodian and Carlsson 2005). The reduction can be written R = D·V with V upper triangular and invertible, and the pairing it yields does not depend on which valid reduction is used (Cohen-Steiner, Edelsbrunner and Morozov 2006). That makes a compact certificate: the submitted R and V. Producing a correct reduction at 2,000 simplices without index or ordering mistakes is error-prone; checking D·V = R over F₂ is one sparse product.

The challenge stresses the Symbol Game's exact host, OEWAS (Engine Workflows, Agents, Skills) synthesis, and no OEEIS (Engine Epistemic Immune System) mechanism beyond the refusal path. A pass shows the game can produce a certified barcode solver. It says nothing about what the bars mean for any data set.

## 3. Formal Problem and Bounds

Input: a list of simplices σ₁, …, σ_N (N ≤ 2,000, dimension ≤ 3), each with a rational filtration value, in an order that is compatible with faces (every face of σ_j appears before σ_j) and non-decreasing in value. D is the N × N boundary matrix over F₂ in this order.

Output: the index pairing and the barcode. Write low(j) for the largest row index with a nonzero entry in column j. Column reduction repeatedly adds an earlier column to a later one while two nonzero columns share the same low. The result R = D·V has V upper triangular with ones on the diagonal, and R is reduced: its nonzero columns have distinct lowest rows. Then (low(j), j) for each nonzero column j of R is a pair: a class born at σ_{low(j)} dies at σ_j. An index i that is no column's lowest row and whose column R_i is zero is essential: born at σ_i, never dies. The value barcode in degree p is the multiset of intervals [value(σ_i), value(σ_j)) for pairs with dim σ_i = p, and [value(σ_i), ∞) for essential i. Zero-length intervals are kept in the index pairing and dropped from the value barcode.

Consistency facts the checker uses: the number of essential classes in degree p equals the F₂ Betti number β_p of the full complex; over F₂, RP² has β = (1, 1, 1), so its filtrations end with one essential bar in each of degrees 0, 1 and 2.

The hidden set must contain N near 2,000, many ties in filtration value, zero-length pairs, RP² and Klein-bottle filtrations (where F₂ and Q answers differ), Vietoris–Rips filtrations of small point sets, and a non-face-compatible order.

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, run in the U09 sandbox:

```json
{"status": "SOLVED", "pairs": [["3", "7"], ["5", "9"]], "essential": ["0"], "barcode": {"0": [["0", "1/2"], ["0", "inf"]], "1": [["1", "3/2"]]}, "R_columns": {"7": ["1", "3"]}, "V_columns": {"7": ["6", "7"]}}
{"status": "OUT_OF_SCOPE", "witness": {"simplex": "12", "missing_earlier_face": "15"}}
{"status": "UNKNOWN", "refusal": "BUDGET_EXHAUSTED"}
```

Columns are sparse lists of row indices (0-based, in input order); unlisted columns of V are unit columns and unlisted columns of R equal D's. The example values are schematic. The certificate is complete when V is upper unitriangular, D·V = R over F₂, R is reduced, and the reported pairs, essential indices and value barcode are exactly those R determines. `OUT_OF_SCOPE` covers orders that are not face-compatible, with the offending simplex and face as witness.

## 5. Participant Packet

- `TASK.md` with the ordering rules, the reduction definition and the certificate format.
- `examples/`: 16 public cases with exact input and output JSON: a filtered triangle, a filtered circle, a filtered S², a torus filtration, an RP² filtration, one tie-heavy case, one zero-length pair, and two bad orders.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 32, eight with N between 1,500 and 2,000.
- **Relabel controls:** 12. Vertex relabelling with the order kept; permutations among simplices of equal value that stay face-compatible. The index pairing may change under the second kind; the value barcode must not, so these controls compare value barcodes only.
- **Poisoned but schema-valid:** 10. RP² and Klein-bottle filtrations (a Q-coefficient solver gets different essential bars); a filtration where the natural-looking pairing by value is not the reduction's pairing; long runs of ties.
- **Exact checker:** new Rust code over F₂: sparse product D·V, triangularity, reducedness, and extraction of pairs. `core_homology::ph_matrix_reduction::reduce_z2` exists but its module is labelled a best-effort shell, so it may serve only after it passes this challenge's mutation suite.
- **Independent second checker:** an established external library, PHAT or GUDHI, run at packet-build time through the crate's existing format adapters (`phat_io.rs`, `gudhi_io.rs`), comparing value barcodes.
- **Checker mutation suite:** a V with a nonzero below the diagonal; an R that is not reduced (two equal lowest rows); a correct R with one pair reported wrongly; an essential class that is actually paired; a barcode with a zero-length bar kept; a pair whose dimensions differ by more than one.

## 7. Arms and Baselines

- **A: Symbol Game.** U05 synthesis of the reduction and the certificate output.
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, cost-matched.
- **E: No-model baseline.** The standard reduction with clearing (Chen and Kerber 2011; `core_homology` has `twist_algorithm.rs` and `clearing_optimization.rs`), wrapped as `solve`. Clearing zeroes columns without recording the column operations, so E must also recover V for the certificate. Expected to solve every case.

Arm F does not apply.

## 8. Budget, Models and Provenance

Candidate models: `meta-llama/llama-3.3-70b-instruct`, Qwen3-32B, Mistral Small 24B (route pinned in U06). $0.50 per arm through `BudgetController`; every call records provider, model ID, generation ID, tokens and billed cost. The sandbox provides the Python standard library only. The run must finish each case within the sandbox time limit declared in the pre-registration, so an O(N³) dense reduction in pure Python at N = 2,000 is a real risk that the solver has to manage. U10 is recommended, as the [Q40 review](../00_q40_review.md) explains.

## 9. Pass Gates and Statistics

- **Capability gate:** 32/32 hidden base cases with complete certificates, all relabel controls matching in value barcode, all poisoned cases correct, on at least 2 of 3 seeds.
- **Differentiation:** exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05.
- **Scale curve:** success by N band (≤ 200, ≤ 1,000, ≤ 2,000), per arm.
- **Economics:** cost per verified success.

## 10. Interpretation

- **A passes, B fails:** the game adds capability for certified persistence at this budget.
- **All arms pass small N and time out at large N:** the models produced correct but unscalable solvers; sparse columns are the missing step.
- **Failures concentrate on RP² and the Klein bottle:** coefficient confusion, not reduction errors.
- **E matches A:** useful automation, no incremental model advantage.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; the refusal path only.
- **Antimorphisms expected:** pairing by filtration value instead of by reduction; off-by-one index shifts; Q-coefficient reasoning on F₂ tasks; certificates omitted for "obvious" columns (AM-3-style skipped preconditions).
- **Layer 2:** grammar-constrained JSON allowed equally. **Layer 1, scratch space:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01).

Expected DDC pattern: `C`, `D`/`M` over candidate solvers (each accepted revision passing more public cases), `E` when every public certificate replays, `T`. Within one reduction, each column addition that lowers a column's lowest row is a `D` step; logged measures are the number of unreduced collisions, public cases failed and wall-clock per case.

Operands this challenge should yield:

```text
operand essential_equals_betti.v1 | kind: guard | when: a barcode is reported | do: count essential bars per degree and compare with F2 Betti numbers of the full complex | check: equal in every degree
operand clearing_with_v_log.v1 | kind: move | when: using clearing for speed | do: log column operations so V can still be emitted | check: D V = R replays
operand value_barcode_for_ties.v1 | kind: guard | when: filtration values tie | do: compare value barcodes, not index pairs, across equivalent orders | check: relabel controls match
```

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_homology` (`ph_matrix_reduction.rs`, `persistent_homology.rs`, `barcode.rs`, `persistence_pairing.rs`, `twist_algorithm.rs`, `clearing_optimization.rs`, `phat_io.rs`, `gudhi_io.rs`, `vietoris_rips.rs`), all labelled best-effort shells, so each must pass the mutation suite before use.
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: none in the catalog. Checker work: the exact F₂ certificate checker in §6.

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver whose F₂ barcodes and R = D·V certificates replay on hidden filtrations of up to 2,000 simplices.
- **Does not support:** barcodes over Q or Z; stability or statistical claims about data; any topological inference about the source of a point cloud.
- **Narrowest defensible claim:** the frozen solver returned replayable reduction certificates and correct barcodes on the measured number of hidden filtrations.
- **Next test:** persistence with Z coefficients, where torsion enters as in [C013](c013_integral_homology_torsion.md), and larger complexes with cohomology-based algorithms.
