# C043: Ramsey and van der Waerden Lower-Bound Constructions

**AuthorityEffect:** None. **Status:** planned. **Domain:** e_formal_math. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a frozen module that returns colourings avoiding monochromatic cliques or arithmetic progressions, below known Ramsey and van der Waerden bounds and under hidden side constraints, for under $1.00.

## 2. Why This Task

Checking a colouring is exhaustive and cheap. K17 has 2,380 four-vertex subsets, and {1, …, 1131} has on the order of 10⁵ six-term progressions. Finding one near the bound is search-hard, and the hidden side constraints (pre-coloured edges or elements) stop a module from simply emitting a memorised Paley colouring. It then has to find an automorphism or relabelling that meets the constraints, or search.

This stresses the Symbol Game's search host under large exact checks, and the cemetery, where near-miss colourings with one monochromatic structure are valuable operand material. It stresses the OEWAS (Omega Engine Workflows, Agents, Skills) workflow that alternates algebraic construction with local search, and the OEEIS (Omega Engine Epistemic Immune System), which must quarantine fabricated "impossibility" claims.

A pass shows that the module constructs these witnesses. It does not show a new Ramsey or van der Waerden bound.

## 3. Formal Problem and Bounds

- **Two-colour Ramsey `(s, t, n)`:** a map `χ: E(K_n) → {0,1}` with no `K_s` in colour 0 and no `K_t` in colour 1. One exists if and only if `n < R(s,t)`.
- **Three-colour triangle `(n)`:** `χ: E(K_n) → {0,1,2}` with no monochromatic triangle. One exists if and only if `n < R(3,3,3)`.
- **Van der Waerden `(r, k, n)`:** `χ: {1,…,n} → {0,…,r−1}` with no monochromatic `k`-term arithmetic progression. One exists if and only if `n < W(r,k)`.

Reference values:

- `R(3,3) = 6`.
- `R(4,4) = 18` (Greenwood & Gleason 1955). The Paley graph on 17 vertices gives a 2-colouring of K17 with no monochromatic K4.
- `R(3,3,3) = 17` (Greenwood & Gleason 1955), so K16 has a 3-colouring with no monochromatic triangle.
- `W(2,3) = 9`.
- `W(2,4) = 35` (Chvátal 1970).
- `W(2,5) = 178` (Stevens & Shantaram 1978).
- `W(2,6) = 1132` (Kouril & Paul 2008).

Any other parameter's bound, and the feasibility of every constrained case, comes from the second checker at packet-build time. That check is a SAT run, with a checked refutation for each infeasible case.

Bounds: Ramsey `n ≤ 17`, triangle `n ≤ 16`, van der Waerden `r = 2`, `k ≤ 6`, `n ≤ 1131`. A constrained case pre-colours up to 12 edges or 40 elements. Edge cases: `n` exactly one below the bound, constraints forcing a relabelled Paley colouring, and constraints that are infeasible at a feasible `n`.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model and makes no model calls at scoring. The sandbox provides the same pinned SAT solver binary to every arm. A Ramsey colouring is a string over the edge colours in lexicographic pair order `(0,1), (0,2), …, (n−2, n−1)`. A van der Waerden colouring is a string of length `n`, with position `i` giving the colour of `i + 1`.

```json
{"case_id": "rv_ex_01", "type": "ramsey2", "s": 3, "t": 3, "n": 5, "fixed": []}
{"case_id": "rv_ex_01", "status": "SOLVED", "kind": "COLOURING", "colours": "0110011010"}
{"case_id": "rv_ex_02", "type": "vdw", "r": 2, "k": 3, "n": 8, "fixed": [[1, 0]]}
{"case_id": "rv_ex_02", "status": "SOLVED", "kind": "COLOURING", "colours": "00110011"}
{"case_id": "rv_ex_05", "status": "OUT_OF_SCOPE", "witness": {"reason": "FIXED_COLOURS_CONTAIN_MONO", "structure": [0, 1, 2]}}
{"case_id": "rv_ex_06", "status": "UNKNOWN", "code": "NOT_FOUND_WITHIN_LIMIT"}
```

A complete certificate is a colouring string of the exact length, drawn from the declared alphabet, agreeing with every fixed colour and containing no forbidden monochromatic structure. `OUT_OF_SCOPE` has two valid witnesses: a monochromatic structure already inside the fixed colours, or an LRAT refutation of the canonical CNF shipped with the case, checked by the C042 pipeline. An infeasible case without such a proof is scored correct only as `UNKNOWN`.

## 5. Participant Packet

- `TASK.md` with the encodings, the JSON Schema and the canonical CNF generator's description.
- 10 public examples with exact input and output JSON: the two above, K5 and K8 variants, a van der Waerden `k = 4` instance at `n = 30`, a Paley-type instance at small order, a triangle-free 3-colouring of K5, and three negative examples (fixed colours already monochromatic; K6 with `(3,3)`, answered `OUT_OF_SCOPE` with an LRAT proof; `n = 9` with `k = 3`).
- `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 36 cases. Ramsey `(4,4,17)` with 0 to 12 fixed edges; `R(3,3,3)` at `n = 16` with fixed edges; van der Waerden at `k = 4` (`n = 34`), `k = 5` (`n` from 150 to 177) and `k = 6` (`n` from 900 to 1131); and looser controls.
- **Relabel and gauge controls:** 12. Vertex permutations applied to the fixed edges, colour swaps where `s = t`, the reflection `i ↦ n + 1 − i` for van der Waerden, and reordered `fixed` lists. Verdicts must match; colourings are checked directly, not compared.
- **Poisoned but schema-valid:** 8. `note` fields quoting a wrong bound (for example, that K17 is impossible), infeasible cases at `n ≥` the bound, constraint sets infeasible at feasible `n`, and fixed colours given as Booleans.
- **Exact checker:** Rust exhaustive enumeration of every `K_s` subset and every `k`-term progression, with any difference.
- **Independent second checker:** an independent implementation in another language, plus the SAT-based feasibility labels.
- **Mutation suite:** the checker must reject one flipped edge that creates a monochromatic K4, a string one symbol short, colour `2` in a 2-colour case, a colouring that violates a fixed colour, and a colouring that is bad only on a progression with a large common difference. The last one kills checkers that bound the difference.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is the pinned SAT solver on the canonical CNF, with lexicographic symmetry breaking, plus the operator's algebraic seeds (the Paley graph for K17 and a known construction for K16) and a deterministic relabelling search over graph automorphisms to meet fixed edges. No model is involved.

E is expected to solve the Ramsey rows and the smaller van der Waerden rows. The tail near `W(2,5)` and `W(2,6)` is where it may time out. A tie with E means the model added no construction knowledge. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$1.00 per arm, about 2.8 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b`. The receipt binds the SAT solver binary hash, the CNF generator hash and each colouring's SHA-256.

Q40 lessons apply:

- the schema is shown as real JSON;
- repair turns carry the full module and the failing case;
- arm A samples several candidates per turn;
- candidates run in the U09 sandbox with a 300-second per-case limit;
- budget is checked before every call.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, all 36 base cases are settled correctly, all relabel controls agree with their base, and no poisoned or infeasible case gets `SOLVED`.
- **Primary metric (pre-registered):** base cases settled. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Secondary:** A vs E on the `k ≥ 5` rows. Wall-clock time per construction is reported as descriptive only.
- **Seeds:** 3.

## 10. Interpretation

Constructions for K5, K8 or `W(2,3)` are recall, not evidence. The informative rows are the constrained Paley cases, which need a relabelling argument, and the long van der Waerden rows, where a cyclic or algebraic structure can beat blind search. If A beats E on those rows, the model is contributing construction ideas. If A ties D, sampling suffices. A fabricated `OUT_OF_SCOPE` without a proof is scored wrong and recorded as an antimorphism.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is an impossibility claim; Signal 2 is the absence of a checkable refutation. Both are needed to quarantine it.
- **Clonal maturation.** `ClonalSelectionEngine` can mutate local-search move operators, such as flipping one edge in the monochromatic structure, as detectors that rank near misses. This is observational only.
- **Expected antimorphisms:** AM-2 CUT_ABSOLUTE_CLAIM (asserting impossibility), AM-4 (re-emitting the same near-miss colouring) and AM-5 (a global colour inversion, which is harmless only when `s = t`).
- **Layer 2:** a character-level grammar mask (`[01]` or `[012]` of exact length) via `carrier_gbnf` in `omega_engine_symbol_game/domain/carrier_decoding.py` (unwired). The bench shows that grammar masks give parseable output, but parseability is not correctness.
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the list of monochromatic structures in the current best colouring as a working set.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (bounds and fixed colours exposed), `I` (seed construction), `R` (count of monochromatic structures), `D` steps as local search reduces the count, `Λ` when a seed family is swapped (Paley to cyclic), `E` at count zero, `T`. `M` records refusals. The `ObstructionScore` sets Φ₁ to the number of monochromatic forbidden structures, `active_count` to violated fixed colours, and Γ₂ is unused (0). Near-miss colourings are kept whole in the cemetery.

Operands to mine:

- seed from Paley or cyclic colourings, then relabel to meet the fixed colours;
- repair by flipping edges shared by the most monochromatic structures;
- for van der Waerden, try colourings periodic in a prime modulus before local search;
- never claim impossibility without a checked proof.

## 13. Estate Reuse and Prerequisites

- The catalog row lists no estate reuse. The exhaustive checker is new Rust work and belongs next to `omega_engine/crates_rs/omega_solvers`.
- Infeasibility proofs reuse the C042 pipeline ([C042](c042_sat_with_drat_certificates.md)).
- `omega_engine/crates_rs/omega_search` (beam, simulated annealing, genetic) can serve arm E's local search.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). No row extras; [U10](../../upgrades/u10_synthesis_loop_v2.md) is recommended.

## 14. Claim Hygiene

- **Supports:** the frozen module produced k of 36 hidden colourings, each verified exhaustively by two checkers, under hidden side constraints.
- **Does not support:** any new Ramsey or van der Waerden bound, any claim about unknown values, or general combinatorial search ability.
- **Narrowest defensible claim:** for these parameters and constraints, the module's certified construction rate was X, against arm E's Y on the `k ≥ 5` rows.
- **Next test:** off-diagonal Ramsey parameters with bounds supplied by the second checker, and three-colour van der Waerden instances.
