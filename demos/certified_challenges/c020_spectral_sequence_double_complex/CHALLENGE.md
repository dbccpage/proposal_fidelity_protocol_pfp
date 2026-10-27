# C020: Spectral Sequence Pages of a Double Complex

**AuthorityEffect:** None. **Status:** planned. **Domain:** b_cohomology. **Tier:** T4.
**Budget:** $2.00 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to produce a
> frozen solver that returns the E² and E^∞ pages of hidden first-quadrant double complexes
> over F₂, with the ranks of every differential, consistent with total homology, for under $2.

## 2. Why This Task

Spectral sequences organize a large homology computation into pages, each computed from the last. They are notoriously error-prone by hand: the differential d_r changes bidegree with r, the "zig-zag" that defines d₂ is easy to get wrong, and the two filtrations of a double complex give different E² pages that must converge to the same total homology (McCleary 2001; Weibel 1994, Chapter 5). Generation is research-grade for a small model. Verification is cheap: the checker computes every page from the filtered total complex by exact F₂ ranks, and total homology gives an independent end-to-end test.

The challenge stresses the Symbol Game's exact host, OEWAS (Engine Workflows, Agents, Skills) decomposition of a hard computation into staged subproblems, and no OEEIS (Engine Epistemic Immune System) mechanism beyond the refusal path. A pass shows the game can produce a certified page solver for small double complexes. It does not cover the Serre or Mayer–Vietoris spectral sequences, whose modules in `core_homology` are shells.

## 3. Formal Problem and Bounds

Input: a double complex over F₂ with C_{p,q} = F₂^{n(p,q)} for 0 ≤ p, q ≤ 5 (and zero elsewhere), n(p,q) ≤ 4, horizontal maps d^h: C_{p,q} → C_{p−1,q} and vertical maps d^v: C_{p,q} → C_{p,q−1} with d^h d^h = 0, d^v d^v = 0 and d^h d^v = d^v d^h (over F₂ commuting and anticommuting coincide). The total complex is Tot_n = ⊕_{p+q=n} C_{p,q} with D = d^h + d^v, so D² = 0.

Filter by columns: F_p Tot = ⊕_{i≤p} C_{i,*}. Then E⁰ = C with d₀ = d^v; E¹ = H(C, d^v); d₁ is induced by d^h, so E² = H^h(H^v(C)); and d_r: E^r_{p,q} → E^r_{p−r, q+r−1}. Since p ≤ 5, every d_r with r ≥ 6 leaves the quadrant and is zero, so E⁶ = E^∞ at the latest, and Σ_{p+q=n} dim E^∞_{p,q} = dim H_n(Tot). The Euler characteristic Σ (−1)^{p+q} dim E^r_{p,q} is the same on every page, since each d_r lowers total degree by one.

**Worked public example (checked by hand for this spec).** Generators a ∈ C_{2,0}, c ∈ C_{1,0}, e ∈ C_{1,1}, f ∈ C_{0,1}, with d^h a = c, d^v e = c, d^h e = f and all other maps zero. The commutation condition holds on every generator. Tot₂ = ⟨a, e⟩ and Tot₁ = ⟨c, f⟩ with D a = c and D e = c + f, which is invertible, so H(Tot) = 0. Column filtration: E¹ = E² has F₂ at (2, 0) (class of a) and at (0, 1) (class of f), and d₂(a) = f through the zig-zag a ↦ d^h a = c = d^v e ↦ d^h e = f. So E³ = E^∞ = 0. Row filtration: taking d^h homology first kills everything, so E² = 0. The two E² pages differ; both converge to H(Tot) = 0.

The hidden set must contain complexes that degenerate at E², complexes with nonzero d₂ and d₃, complexes whose two filtrations have different E² pages, complexes with nonzero total homology in several degrees, and one complex violating the commutation condition.

## 4. Deliverable and Output Contract

A frozen `solve.py` with `def solve(case: dict) -> dict`, run in the U09 sandbox:

```json
{"status": "SOLVED", "filtration": "columns", "E2": {"2,0": "1", "0,1": "1"}, "differentials": [{"r": "2", "from": "2,0", "rank": "1"}], "Einf": {}, "tot_homology": {}}
{"status": "OUT_OF_SCOPE", "witness": {"reason": "DH_DV_NOT_COMMUTING", "generator": "1,2:0"}}
{"status": "UNKNOWN", "refusal": "BUDGET_EXHAUSTED"}
```

This is the worked example; omitted positions are zero. The solver reports, for the declared filtration, dim E²_{p,q} at every position, the rank of every nonzero d_r for r ≥ 2 by source position, dim E^∞_{p,q}, and dim H_n(Tot). A certificate is complete when every reported number equals the checker's, the page recursion holds (dim E^{r+1}_{p,q} = dim E^r_{p,q} − rank of d_r leaving (p,q) − rank of d_r arriving at (p,q)), and the E^∞ sums equal the total homology. Some cases ask for both filtrations.

## 5. Participant Packet

- `TASK.md` with the conventions above, the bidegree of d_r, the recursion identity and the worked example.
- `examples/`: 16 public cases with exact input and output JSON: the worked example in both filtrations, a complex degenerating at E¹, one at E², one with nonzero d₃, one with nonzero total homology in three degrees, and two `OUT_OF_SCOPE` inputs.
- `runner.py`, `accounting.json`.

## 6. Judge Packet

- **Hidden base cases:** 32 (16 per filtration request, 8 asking for both).
- **Relabel controls:** 12. Basis changes within each C_{p,q} by random invertible F₂ matrices (every dimension and rank unchanged), and transposition p ↔ q (swaps the roles of the two filtrations).
- **Poisoned but schema-valid:** 10. Complexes where d₂ is nonzero only through a zig-zag across three positions; complexes where E² looks like E^∞ but d₃ ≠ 0; complexes where the two filtrations' E² pages have equal Euler characteristic but different dimensions.
- **Exact checker:** new Rust code over F₂ that builds Tot and the column or row filtration, computes E^r_{p} = Z^r_p / B^r_p from ranks of the filtered pieces, and checks the recursion and the abutment. `core_homology`'s `spectral_sequence.rs`, `serre_spectral_sequence.rs` and `mayervietoris_ss.rs` are best-effort shells and cannot serve.
- **Independent second checker:** a separately written Python implementation that computes the pages by iterating homology of (E^r, d_r) with explicit subquotient bases, not from the rank formula.
- **Checker mutation suite:** a d₂ with the wrong target bidegree; an E^∞ whose total-degree sums disagree with H(Tot) by one; a recursion that subtracts only outgoing ranks; E² reported from the wrong filtration; a noncommuting input accepted.

## 7. Arms and Baselines

- **A: Symbol Game.** U05 synthesis, with the computation staged as E¹, then d₁, then each d_r, each stage checked on public examples before the next.
- **B: Ordinary iterative.** **C: Representation ablation.** **D: Repeated sampling**, cost-matched.
- **E: No-model baseline.** The second checker wrapped as `solve`. Building it is part of packet construction; it is expected to solve every case.

Arm F does not apply.

## 8. Budget, Models and Provenance

Candidate models: `deepseek/deepseek-r1-distill-llama-70b`, `meta-llama/llama-3.3-70b-instruct`, DeepSeek-R1-Distill-Qwen 32B (route pinned in U06). $2.00 per arm through `BudgetController`; every call records provider, model ID, generation ID, tokens and billed cost. The sandbox provides the Python standard library only. U10 is recommended, as the [Q40 review](../00_q40_review.md) explains; at T4 the staged construction in arm A depends on stateful synthesis.

## 9. Pass Gates and Statistics

- **Capability gate:** 32/32 hidden base cases with complete certificates, all relabel and transposition controls consistent, all poisoned cases correct, on at least 2 of 3 seeds.
- **Differentiation:** exact McNemar, A against B (primary), A against C and D (Holm), α = 0.05. With 32 cases, only large differences can reach significance; the report states the minimum detectable discordant split.
- **Stage profile:** per arm, the first page at which answers go wrong (E¹, E², d₂, d₃ and above).
- **Economics:** cost per verified success.

## 10. Interpretation

- **A passes, B fails:** staged construction under host checks adds capability on a research-grade computation at this budget.
- **All arms get E² and fail E^∞:** higher differentials are the bottleneck; the zig-zag is the missing step.
- **Arms pass one filtration and fail its transpose:** a convention was hard-coded instead of derived.
- **E matches A:** useful automation, no incremental model advantage.
- **Nothing passes:** at T4 that is an informative null; report the stage profile.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

- **OEEIS:** no catalog hook; the refusal path only.
- **Antimorphisms expected:** AM-2 absolute claims of degeneration at E² ("small complexes always degenerate"); wrong d_r bidegree; E^∞ reported without checking the abutment (AM-3-style skipped precondition).
- **Scratch space (U12, optional):** a page ledger holding each E^r and d_r rank, so later stages read earlier ones from the host. **Layer 2:** grammar-constrained JSON allowed equally. **Layer 1:** not applicable.

## 12. Run Folder, DDC Trace and Operand Mining

Each attempt writes a RunFolderV1 bundle under `_intelligence/symbol_game/runs/<run_id>/` (U01).

Expected DDC pattern: `C`, then `Λ` once per page (lift from E^r to E^{r+1}), with `D`/`M` steps inside each stage as candidate code passes more public pages, `I` when the stages are integrated into one solver, `E` when every public certificate replays, `T`. Logged measures: public cases failed, first failing page, the Euler-characteristic check per page.

Operands this challenge should yield:

```text
operand zigzag_d2.v1 | kind: move | when: computing d2 on a class x at (p, q) | do: take d^h x, write it as d^v y, then return the class of d^h y at (p-2, q+1) | check: matches the checker's d2 rank
operand euler_per_page.v1 | kind: guard | when: any page is reported | do: compare its Euler characteristic with that of Tot | check: equal on every page
operand transpose_control.v1 | kind: guard | when: both filtrations are available | do: compute both and compare abutments | check: both E-infinity pages sum to dim H(Tot) in each degree
```

## 13. Estate Reuse and Prerequisites

- `engine/crates_rs/core_homology` (`chain_complex.rs`, `filtered_complex.rs`, `filtration.rs`; `spectral_sequence.rs`, `serre_spectral_sequence.rs` and `mayervietoris_ss.rs` as shells to be replaced).
- `engine/crates_rs/core_linear_algebra` for ranks; F₂ arithmetic as used in `core_symbol_game_runtime` (`f2.rs`).
- Base upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md).
- Extra upgrades: none in the catalog. Checker work: the exact F₂ page checker in §6.

## 14. Claim Hygiene

- **Supports:** whether a ≤70B-model pipeline produced a solver whose E², differential ranks and E^∞ pages replay exactly on hidden F₂ double complexes, consistent with total homology.
- **Does not support:** spectral sequences of fibrations or covers; coefficients other than F₂; extension problems (over a field, E^∞ fixes each H_n(Tot) up to isomorphism through its dimension, which is all this challenge checks; over Z it does not).
- **Narrowest defensible claim:** the frozen solver returned correct pages and differential ranks on the measured number of hidden double complexes.
- **Next test:** double complexes over Z, where E^∞ no longer determines H(Tot) and extension data must be certified, and the Mayer–Vietoris gluing in `core_solvers` (`solver_mayer_vietoris_gluing.rs`).
