# C044: Finite Group Identification with Isomorphism Witnesses

**AuthorityEffect:** None. **Status:** planned. **Domain:** e_formal_math. **Tier:** T3.
**Budget:** $1.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a frozen module that identifies hidden groups of order at most 64 by an explicit isomorphism to a catalogued representative, or separates two groups by a recomputable invariant, for under $1.00.

## 2. Why This Task

An isomorphism given as images of generators is cheap to verify. The checker extends the map by breadth-first search, checks consistency, and checks the homomorphism law on at most 64² = 4,096 products. Finding it is hard. There are 51 groups of order 32 and 267 of order 64, and many of them agree on cheap invariants, so identification needs a sequence of invariants that finally separates them, followed by an isomorphism search.

This stresses the Symbol Game's decomposition into invariant stages, the OEWAS (Omega Engine Workflows, Agents, Skills) workflow that orders those stages, and the OEEIS (Omega Engine Epistemic Immune System) against the classic failure of declaring two groups isomorphic because a few invariants agree. A pass shows that a synthesized module identifies these groups without a computer-algebra system. It does not show anything new about groups.

## 3. Formal Problem and Bounds

Inputs are finite groups `G` of order `|G| ≤ 64`, presented in one of three ways:

- permutation generators on at most 16 points;
- invertible matrices over `GF(p)` with `p ≤ 7` and dimension at most 3;
- a full Cayley table with element 0 as the identity.

There are two tasks.

- **IDENTIFY:** return the representative ID `[n, i]` from the shipped catalog, together with the images of the case's generators in that representative's table. Those images must extend to an isomorphism.
- **COMPARE `(G, H)`:** return `ISOMORPHIC` with an isomorphism, or `NOT_ISOMORPHIC` with an invariant from a fixed menu whose recomputed values differ. The menu is:
  - element-order histogram;
  - centre order;
  - derived-subgroup order;
  - abelianization invariant factors;
  - number of subgroups of each order;
  - conjugacy-class size multiset;
  - number of solutions of `x^k = e` for each `k`.

The catalog is exported at packet-build time from the SmallGroups library (Besche, Eick & O'Brien 2002) and keeps its numbering: one Cayley table per isomorphism class for every order in scope. Reference counts are 51 groups of order 32 and 267 of order 64. Edge cases: abelian groups of equal order with different invariant factors, nonabelian pairs that agree on the element-order histogram, direct versus semidirect products, and generating sets with redundant generators.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model, makes no model calls at scoring, runs with no computer-algebra system in the sandbox, and reads the shipped catalog file.

```json
{"case_id": "grp_ex_01", "task": "IDENTIFY", "presentation": "perm", "degree": 2, "gens": [[1, 0]]}
{"case_id": "grp_ex_01", "status": "SOLVED", "kind": "IDENTIFIED", "rep_id": [2, 1], "images": [1]}
{"case_id": "grp_ex_04", "task": "COMPARE", "G": {"presentation": "perm", "degree": 4, "gens": [[1, 2, 3, 0]]}, "H": {"presentation": "perm", "degree": 4, "gens": [[1, 0, 2, 3], [0, 1, 3, 2]]}}
{"case_id": "grp_ex_04", "status": "SOLVED", "kind": "NOT_ISOMORPHIC", "invariant": "element_order_histogram", "G_value": {"1": 1, "2": 1, "4": 2}, "H_value": {"1": 1, "2": 3}}
{"case_id": "grp_ex_07", "status": "OUT_OF_SCOPE", "witness": {"reason": "NOT_ASSOCIATIVE", "triple": [2, 3, 5]}}
{"case_id": "grp_ex_09", "status": "UNKNOWN", "code": "SEARCH_LIMIT"}
```

A complete certificate for `IDENTIFIED` or `ISOMORPHIC` consists of generator images that extend consistently to a bijective homomorphism. The checker never trusts a claimed invariant; for `NOT_ISOMORPHIC` it recomputes the invariant on both groups and requires the values to differ. `OUT_OF_SCOPE` covers three cases, each with its own witness:

- a non-associative table, witnessed by a triple;
- a missing identity or inverse, witnessed by the element;
- generators that generate more than 64 elements, witnessed by 65 distinct words.

## 5. Participant Packet

- `TASK.md` with the three presentation schemas, the invariant menu's exact definitions and the JSON Schema.
- `catalog/`: representative Cayley tables with IDs for all orders at most 64.
- 12 public examples with exact input and output JSON: C2, C4 against C2×C2, S3 by permutations, D4 against Q8 (order 8), two abelian groups of order 16, a `GF(3)` matrix group, a non-associative Latin square, and an oversized generating set.
- `runner.py` and `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 40 cases, 24 IDENTIFY and 16 COMPARE, with at least 12 involving orders 32 or 64.
- **Relabel and gauge controls:** 16. Cayley tables relabelled by a random permutation (fixing the identity label), permutation generators conjugated by a random permutation, different generating sets of the same group, direct-product factors swapped, and matrix groups conjugated by a random invertible matrix. IDENTIFY must return the same `rep_id`.
- **Poisoned but schema-valid:** 8. Quasigroup tables that are not associative, `note` fields claiming isomorphism for a non-isomorphic pair, pairs agreeing on the first four menu invariants, and generator lists containing the identity.
- **Exact checker:** a Rust map extender and homomorphism checker, plus an invariant recomputation for every menu item.
- **Independent second checker:** labels from GAP's `IdGroup` and `IsomorphismGroups`, with GAP pinned at packet-build time, plus an independent Python homomorphism checker.
- **Mutation suite:** the checker must reject a map that is a homomorphism but not injective, a consistent map with one image swapped, a `rep_id` of the right order but the wrong index, an invariant that differs only because of a miscount (the checker recomputes it), and images given as Booleans.

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is GAP 4 with the SmallGroups library, using `IdGroup` and `IsomorphismGroups` on each case. It is deterministic, very strong, and needs no model.

A tie with E is expected on correctness. The measure is whether a model-synthesized module without GAP reaches the same answers. A loss to E on order 64 is informative, not surprising. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$1.00 per arm, about 2.8 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-r1-distill-llama-70b`, `qwen/qwen3-30b-a3b`. The receipt binds the catalog export hash and the GAP version and hash used for labels.

Q40 lessons apply:

- the catalog format and schemas are shown as real JSON;
- repair turns include the module and the failing case;
- arm A samples several candidates per turn;
- execution is sandboxed with a 120-second per-case limit;
- budget is checked before every call.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, all 40 base cases are correct, all relabel controls agree with their base, and no poisoned case gets a false `ISOMORPHIC` or `IDENTIFIED`.
- **Primary metric (pre-registered):** base cases correct on orders 32 and 64. The test is an exact McNemar test on paired (seed, case) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Secondary:** the invariant-stage count per identification.
- **Seeds:** 3.

## 10. Interpretation

Small orders are recall. Orders 32 and 64 carry the evidence. If A succeeds where B fails, the staged invariant plan and typed feedback help. If A ties D, sampling explains it. Because E dominates by construction, a pass supports "a ≤70B model can synthesize a working identifier", not "the game beats computer algebra". A module that only emits invariants and never isomorphisms cannot pass IDENTIFY.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Allosteric consensus.** `AllostericConsensusGate` requires several independent invariants to agree before a candidate representative is tried, which damps single-invariant false positives. This is observational only.
- **Danger gate on `note` fields.**
- **Expected antimorphisms:** AM-2 (claiming `ISOMORPHIC` from matching invariants) and AM-FSP-2 (generator images that are not a homomorphism).
- **Layer 2:** a JSON grammar mask for the envelope, via `carrier_gbnf` (unwired).
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps the table of invariants computed so far, keyed by group, as working memory.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C` (presentation and catalog exposed), `Λ` (lift to an invariant stage plan), `I` (candidate representatives), `R` (the candidate set is still larger than one), `D` steps as each invariant shrinks the set, `E` when an isomorphism verifies, `T`. `M` records refusals. The `ObstructionScore` sets Φ₁ to the number of surviving candidate representatives minus one, `active_count` to failed homomorphism checks, and Γ₂ is unused (0). Failed isomorphism attempts are kept in the cemetery.

Operands to mine:

- compute the invariant menu in order of cost, then search isomorphisms only inside the surviving set;
- choose generator images by element order and centralizer size first;
- treat the Cayley table as the canonical form, converting permutation and matrix inputs by closure;
- recompute invariants, never quote them.

## 13. Estate Reuse and Prerequisites

- The catalog row lists no estate reuse, and there is no group-theory crate. The map extender and invariant checker are new Rust work, for example beside `omega_engine/crates_rs/omega_category_theory`.
- Exact arithmetic for `GF(p)` matrices can reuse `omega_engine/crates_rs/omega_symbol_game_runtime/src/f2.rs` for `p = 2`.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md). No row extras; [U10](../../upgrades/u10_synthesis_loop_v2.md) is recommended.

## 14. Claim Hygiene

- **Supports:** the frozen module identified or separated k of 40 hidden groups with explicit isomorphisms or recomputed invariants, confirmed against GAP labels.
- **Does not support:** a faster or more general identification algorithm than SmallGroups, or any claim about orders above 64.
- **Narrowest defensible claim:** for orders at most 64 in these presentations, the module's certified identification rate was X, and Y on orders 32 and 64.
- **Next test:** order 128 with a restricted invariant menu, and presentations by generators and relations.
