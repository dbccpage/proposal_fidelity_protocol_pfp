# Lesson 700.13 -- 2. Empirical 50-Task Benchmark Results

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_13_2_empirical_50_task_benchmark_results.ipynb](../notebooks/lesson_700_13_2_empirical_50_task_benchmark_results.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Empirical 50-Task Benchmark Results

Across 50 held-out discrete algebraic/topological tasks evaluated in Paper 032:
- **Token Compression Ratio**: $\rho = 2.58\times$ ($-61.22\%$ token support reduction).
- **Conversational Fluff Excision**: $100.0\%$ (reduced from 299 occurrences to exactly 0).
- **Smuggled Ontology Excision**: $100.0\%$ (reduced from 41 occurrences to exactly 0).
- **Unpriced Rewrite Density**: $\delta_{{\text{{unpriced}}}} = 0.000$ (vs $0.932$ for dense CoT).
- **Host Replay Success**: $100.0\%$ (50/50) deterministic Layer 3 replay (vs $0\%$ for dense CoT).

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - Demonstrates that prompt contracts enforcing closed operators eliminate conversational fluff and reduce token support by over $60\%$.
> - Demonstrates that $100\%$ of Symbol Game derivations replay deterministically in $O(K)$ host cycles.
>
> **CANNOT-Show**:
> - Does not show that token compression alone solves reasoning tasks where the model lacks domain knowledge.

## 4. Student Exercises

### Exercise 08.1: Unpriced Rewrite Density
If a proof transcript contains 10 steps, of which 7 cite verified rules and 3 state unproven assertions without citation, what is the unpriced rewrite density $\delta_{\text{unpriced}}$, and does it pass the Symbol Game contract?

<details>
<summary><b>Click to reveal solution</b></summary>
The unpriced rewrite density is $\delta_{\text{unpriced}} = 3 / 10 = 0.300$ (30%).
It fails the Symbol Game contract, which strictly mandates $\delta_{\text{unpriced}} = 0.000$ (every asserted step must cite an approved rule and valid parent evidence).
</details>

## 5. Anchors

- **Paper 032 Sections**: §7.1–§7.4
- **Ledger IDs**: `PO032-C49` through `PO032-C56`
- **Code**: `papers/032.../code/l1_sparsity_bullshit_benchmark.py`
- **Audit Receipt**: `papers/032.../code/l1_sparsity_benchmark_receipt.json`

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `08_l1_sparsity_and_bullshit_excision`
- The code checks one finite example. It is not a general proof.

Tower files for this sitting:

- [research/mssn_sn_tower/math/symbol_game/readme.md](../../../../../research/mssn_sn_tower/math/symbol_game/readme.md)
- [research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md](../../../../../research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md)
- [research/mssn_sn_tower/math/symbol_game/3_math_quotient_obstruction_and_survivors.md](../../../../../research/mssn_sn_tower/math/symbol_game/3_math_quotient_obstruction_and_survivors.md)
