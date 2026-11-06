# Post-Round-3 Semantic Review of Accepted LLM Ladder Runs (`2026-10-22`)

- **AuthorityEffect:** `None` (read-only audit report; no run folder or DAG node was modified)
- **Dataset scanned:** 91 Round 3 `ladder_receipt.json` files (`dag/results/<NODE>/runs/20261022T18*_ladder/`) executed after merging PR #169 (`ungroundable` pre-dispatch skip + `verified_lemma_statements` reference check), PR #168/#171 (`FrontierTargets` Lean 4 mechanizations), and PR #175 (`allowed_refs`, `credited_paths`, `GENERATOR_KINDS`/`RELATION_KINDS`/`_is_test_decl`, `relation_overlap`, `STRUCTURAL_STEM_STOP`)
- **Round 3 run outcomes (`91` total):**
  - `accepted`: **57** (`51` via `claude-haiku-5-5` Tier 2; `6` via `claude-sonnet-5-5` Tier 3)
  - `accepted_partial`: **3** (`LQG-SPIN-NETWORK-STATES-IMPORT`, `LQG-TURAEV-VIRO-1992-SOURCE`, `TFQ-0103` — stopped below `min_verified = 2` by `credited_paths` and `relation_overlap`)
  - `not_accepted`: **11**
  - `skipped_ungroundable`: **20** (skipped pre-dispatch at \$0.00 spend by `groundability()`)
- **Baseline compared against:** Round 2 semantic review (`dag/pfp/llm_ladder/semantic_review_2026-10-22.md` and `semantic_review_2026-10-22.json`: 404 accepted runs, 344 non-numeric accepted runs, 1,144 verified non-numeric entries)
- **Companion per-entry & per-run JSON table:** `dag/pfp/llm_ladder/semantic_review_round3_2026-10-22.json`

---

## 1. Executive Summary & Comparison Against Round 2 Baseline

Across the 57 newly accepted Round 3 runs, the tightened host verifier (`dag/pfp/llm_ladder/verify.py`) accepted **209 non-numeric entries** (`generators`: 66, `relations`: 101, `compositions`: 1, `lemmas`: 41) and **46 numeric claims** (which earn no credit toward acceptance or semantic support). Zero Round 3 runs were accepted on numeric claims alone (`numeric_counts=False`).

Every one of the 209 verified non-numeric entries (plus the 6 entries in the 3 `accepted_partial` runs) was audited against:
1. the cited declaration window in the repository (`path::declaration` at its source line), and
2. the target node's statement, derivation markdown, and anchor declarations in `dag/derivation_dag.json`,
using the same four-class rubric (`SUPPORTS`, `TANGENTIAL`, `IRRELEVANT`, `MISLEADING`) and run-level `HOLLOW` definition (zero `SUPPORTS` entries) as `semantic_review_2026-10-22.md`.

### 1.1 Headline Comparison: Round 2 Baseline vs. Round 3 Post-Tightening

| Metric | Round 2 Baseline (`SEMANTIC_REVIEW_2026-10-22`) | Round 3 Batch (`57 accepted` of `91` run) | Change / Direction |
| :--- | ---: | ---: | :--- |
| **Entry-level `SUPPORTS` share** | 891 / 1,144 (**77.88%**) | 159 / 209 (**76.08%**) | -1.80 pp (reflecting 44 newly attempted unanchored Stage 7–10 nodes in Cohort C) |
| **Entry-level `TANGENTIAL` share** | 166 / 1,144 (**14.51%**) | 43 / 209 (**20.57%**) | +6.06 pp (adjacent stage lemmas cited on bibliography/continuum nodes) |
| **Entry-level `IRRELEVANT` share** | 69 / 1,144 (**6.03%**) | 6 / 209 (**2.87%**) | **-3.16 pp (-52.4% relative)** |
| **Entry-level `MISLEADING` share (all tiers)** | 18 / 1,144 (**1.57%**) | 1 / 209 (**0.48%**) | **-1.09 pp (-69.4% relative)** |
| **Entry-level `MISLEADING` share (`claude-haiku-5-5`)** | 3 / 44 (**6.82%**) | 1 / 190 (**0.53%**) | **-6.29 pp (-92.2% relative)** |
| **Run-level `HOLLOW` rate on `PROVED_LEAN` + `COMPUTATIONALLY_CHECKED` nodes** | 19 / 176 (**10.80%**) | 0 / 29 (**0.00%**) | **-10.80 pp (100% eliminated)** |
| **Run-level `HOLLOW` rate on Cohort A (`n=31` re-run R2 false positives)** | 12 / 31 (**38.71%**) | 5 / 28 (**17.86%**) | **-20.85 pp (-53.9% relative)** |
| **Run-level `HOLLOW` rate on Cohort B (`n=16` mechanized `PROVED_LEAN` targets)** | 12 / 14 (**85.71%**) | 0 / 16 (**0.00%**) | **-85.71 pp (100% eliminated)** |
| **Run-level `HOLLOW` rate on Cohort A+B (`n=45` re-run nodes, all R2 runs)** | 24 / 45 (**53.33%**) | 5 / 42 (**11.90%**) | **-41.43 pp (-77.7% relative)** |
| **Run-level Semantic `HOLLOW` rate on Cohort A+B (`n=35` non-numeric R2 runs)** | 14 / 35 (**40.00%**) | 5 / 42 (**11.90%**) | **-28.10 pp (-70.3% relative)** |
| **Run-level Semantic `HOLLOW` rate (`claude-haiku-5-5` Tier 2)** | 6 / 19 (**31.58%**) | 13 / 51 (**25.49%**) | **-6.09 pp (-19.3% relative)** |
| **Run-level `HOLLOW` rate across all 57 Round 3 accepted runs (Cohorts A+B+C)** | 147 / 404 (**36.39%** all) / 87 / 344 (**25.29%** non-num) | 16 / 57 (**28.07%**) | **-8.32 pp vs. R2 all** / +2.78 pp vs. R2 non-num (due to Cohort C first-time unanchored nodes) |
| **Estate-wide active corpus `HOLLOW` rate (replacing 45 re-run nodes with R3)** | 147 / 404 (**36.39%** all) / 87 / 344 (**25.29%** non-num) | 139 / 416 (**33.41%** all) / 89 / 366 (**24.32%** non-num) | **-2.98 pp all** / **-0.97 pp non-num** (while adding 13 newly accepted Cohort C nodes) |

---

## 2. Entry-Level Classification & Provenance Bucket Analysis

### 2.1 Entry Counts by Semantic Class (`57` Accepted Round 3 Runs)

| Class | Generators | Relations | Compositions | Lemmas | Total Entries | Share of 209 | Round 2 Share (of 1,144) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **`SUPPORTS`** | 49 | 73 | 1 | 36 | **159** | **76.08%** | 77.88% |
| **`TANGENTIAL`** | 15 | 23 | 0 | 5 | **43** | **20.57%** | 14.51% |
| **`IRRELEVANT`** | 2 | 4 | 0 | 0 | **6** | **2.87%** | 6.03% |
| **`MISLEADING`** | 0 | 1 | 0 | 0 | **1** | **0.48%** | 1.57% |
| **Total** | **66** | **101** | **1** | **41** | **209** | **100.00%** | **100.00%** |

- **Activation of `verified_lemma_statements` (`0` in Round 2 $\to$ `41` in Round 3):** Following the PR #169 update to `_SYSTEM_P0_RULES` and `verify.py` (allowing a lemma with `lean_skeleton=""` and a verified `ref.status="existing"` to pass with `evidence_status = "declaration_exists_statement_consistent_ref_verified_not_lean_checked"`), 41 lemma entries were verified in Round 3. Of those 41 lemmas, **36 (`87.80%`) are `SUPPORTS`**, **5 (`12.20%`) are `TANGENTIAL`**, and **0 are `IRRELEVANT` or `MISLEADING`**.
- **Elimination of `MISLEADING` Generators (`8` in Round 2 $\to$ `0` in Round 3):** Enforcing `GENERATOR_KINDS = {'def', 'abbrev', 'fn', 'struct', 'structure', 'inductive', 'class'}` and `_is_test_decl` in `verify_p0` reduced `MISLEADING` generators to **0 / 66 (`0.00%`)**, blocking every Round 2 failure mode where a `theorem`, `pub mod`, `const`, or `test_` function was cited as an operad generator.

### 2.2 Entry Counts by Citation Provenance Bucket

| Provenance Bucket | `SUPPORTS` | `TANGENTIAL` | `IRRELEVANT` | `MISLEADING` | Total | `SUPPORTS` Rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `1_direct_node_decl` (exact declaration in node's `lean`/`rust`/`python`) | 98 | 2 | 0 | 0 | **100** | **98.00%** |
| `2_node_file_and_decl_in_deriv_md` (node's file + decl in derivation note) | 7 | 0 | 0 | 0 | **7** | **100.00%** |
| `3_node_file_other_decl` (another declaration in node's anchored file) | 35 | 7 | 0 | 0 | **42** | **83.33%** |
| `4_file_and_decl_in_deriv_md` (file & decl named in derivation note) | 6 | 0 | 0 | 0 | **6** | **100.00%** |
| `5_file_in_deriv_md_other_decl` (file named in derivation note, other decl) | 4 | 2 | 0 | 0 | **6** | **66.67%** |
| `7_neighbour_1hop` (declaration from a 1-hop DAG neighbour) | 0 | 10 | 0 | 1 | **11** | **0.00%** |
| `8_known_pos_propagated_multi_hop` (`@KNOWN+` multi-hop propagation) | 6 | 4 | 3 | 0 | **13** | **46.15%** |
| `9_fuzzy_src_match` (`@SRC` stem-overlap fallback candidate) | 2 | 18 | 3 | 0 | **23** | **8.70%** |
| `composition` (wires two generators in the same attempt) | 1 | 0 | 0 | 0 | **1** | **100.00%** |
| **Total** | **159** | **43** | **6** | **1** | **209** | **76.08%** |

- **Anchored / derivation-named files (`buckets 1–5`, 161 entries):** Achieve a **93.79% `SUPPORTS` rate (`150 / 161`)** with **0 `IRRELEVANT`** and **0 `MISLEADING`** entries. The remaining 11 `TANGENTIAL` entries in `buckets 1–5` occur on 4 bibliography/continuum nodes whose `dag/derivation_dag.json` entry or statement explicitly mentions a finite contrast file (`H037FourQubitCssSurfaceCode.lean` on `ADS-HAPPY-2015-SOURCE`, `CausalOrder.lean` on `CQFT-LOCAL-NET-AXIOMS-IMPORT`, `Entanglement.lean` on `CT-MARLETTO-VEDRAL-2017-SOURCE`, and `MajoranaCore.lean::OpenSystemTransferBound` on `MAJ-OPEN-LINDBLAD-TRANSFER-ENVELOPE`), plus 1 auxiliary `c2_mu` table citation on `CQFT-FINITE-CAUSET-IDENTIFICATION`.

---

## 3. Cohort-by-Cohort Analysis of the 91 Round 3 Runs

Because Round 3 targeted three distinct populations of nodes (rather than re-running the 257 already-supported Round 2 nodes), the post-tightening impact is clearest when broken down across the three Round 3 cohorts:

| Cohort | Nodes Run | `skipped_ungroundable` (\$0) | `not_accepted` | `accepted_partial` | `accepted` | `Supported` (`accepted`) | `HOLLOW` (`accepted`) | R3 `HOLLOW` Rate | R2 `HOLLOW` Rate (Same Nodes) |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Cohort A:** Re-run Round 2 false positives | 31 | 0 | 2 | 1 | **28** | **23** | **5** | **17.86%** | **38.71%** (12 / 31) |
| **Cohort B:** Newly mechanized `PROVED_LEAN` frontier & CQFT targets | 16 | 0 | 0 | 0 | **16** | **16** | **0** | **0.00%** | **85.71%** (12 / 14) |
| **Cohort A + B Combined** (all nodes with prior R1/R2 accepted runs) | **45**\* | **0** | **2** | **1** | **42** | **37** | **5** | **11.90%** | **53.33%** all (24 / 45) / **40.00%** non-num (14 / 35) |
| **Cohort C:** Previously unrun index nodes (Stages 7–10) | 46\* | 20 | 9 | 2 | **15**\* | **4**\* | **11** | **84.62%** (11 / 13 non-B) | *(not run in R2)* |
| **All Round 3 Runs Total** | **91** | **20** | **11** | **3** | **57** | **41** | **16** | **28.07%** | — |

*\*Note: 2 of the 16 Cohort B `PROVED_LEAN` nodes (`CQFT-FINITE-STRICT-POSET-SPACELIKE` and `CQFT-NO-SIGNALLING-PRODUCT-LEAN`) were also among the 46 previously unrun index nodes, so `31 (Cohort A) + 14 (Cohort B with prior R1/R2 runs) = 45` nodes with prior R1/R2 accepted runs, and `46 - 2 = 44` non-Cohort-B first-time index nodes.*

### 3.1 Cohort A (`n = 31`): Re-Run Round 2 False Positives (`38.71%` $\to$ `17.86%` `HOLLOW`)
- **3 Round-2 `HOLLOW` nodes blocked from `accepted`:**
  - `TFQ-0001` (`not_accepted`) and `TFQ-0002` (`not_accepted`): Previously passed in Round 2 via `@KNOWN+` multi-hop contagion (`DerivationDagQMClosure.pg_six_operations_and_primdiff_admission_gate`); blocked by `credited_paths`.
  - `TFQ-0103` (`accepted_partial`): Previously passed in Round 2 as Example #14 of the 20 Worst Examples (citing electrostatics probe `probe_b_pentagon_to_quad_exact_invariance` for Ponzano–Regge spin-foam invariance); `relation_overlap` rejected the relation claim, leaving only 1 generator (`< min_verified = 2`) and stopping the run at `accepted_partial`.
- **5 Round-2 `HOLLOW` / `MISLEADING` nodes converted to `Supported` (`100%` genuine support):**
  - `MAJ-KITAEV-SWEETSPOT-EXACT`: Converted from `HOLLOW` (3 `IRRELEVANT` citations to `BornHermitianCarrier.lean`) to `Supported` (3 `SUPPORTS` entries citing `majorana_fock_algebra.rs::kitaev_chain` and `bulk_kitaev_invariant`).
  - `TFQ-0050`: Converted from `HOLLOW` + `MISLEADING` (Example #12 in Round 2) to `Supported` (4 `SUPPORTS` entries citing `catalog.rs::toric_code`, `su2_level.rs::su2_level`, `racah_formula_replays_pentagon_hexagons_and_verlinde_through_maximum_level`, and `unsupported_field_and_unbounded_level_are_typed_refusals`).
  - `TFQ-0125`: Converted from `HOLLOW` + 2 `MISLEADING` (Examples #1 & #2 in Round 2, citing `pub mod engine_bridge;`) to `Supported` (2 `SUPPORTS` entries citing `dag_witnesses.rs::build_derivation_dag_master_witness_receipt` and `master_derivation_dag_witness_receipt_passes_all_33_families`).
  - `TFQ-0161`: Converted from `HOLLOW` + 2 `MISLEADING` (citing `theorem` declarations as `generators`) to `Supported` (5 `SUPPORTS` relations and lemmas citing `FiniteQM.finite_clock_poincare_recurrence_vs_kraus_decoherence`, `qutrit_stabilizer_wigner_nonnegative_vs_magic_negative`, `weyl_heisenberg_finite_trace_obstruction`, and `lorentz_boost_non_unitary_in_finite_dim`).
  - `TFQ-0226`: Converted from `HOLLOW` + `MISLEADING` (Example #3 in Round 2, citing `pub mod finite_valuation;` as an arity-6 generator) to `Supported` (cites `finite_probability/finite_valuation.rs::BooleanValuation`, `SUPPORTS`).
- **Additional `MISLEADING` entries eliminated on already-supported Cohort A nodes:**
  - `AUTH-G5A-CLASS-RELATIVE-TRANSPORT` and `TFQ-0037`: Round 2 `MISLEADING` entries (citing `theorem` as `generator`) were rejected by `GENERATOR_KINDS` and replaced by valid `relation` and `lemma` entries (`3 / 3 SUPPORTS` on each).

### 3.2 Cohort B (`n = 16`): Newly Mechanized `PROVED_LEAN` Frontier & CQFT Targets (`85.71%` $\to$ `0.00%` `HOLLOW`)
- After PR #168 and PR #171 mechanized `lean4/Frontier*.lean`, `lean4/CausalOrder.lean`, and `lean4/NoSignallingCore.lean` and anchored them in `dag/derivation_dag.json`, **all 16 nodes (`100.0%`) were accepted at Tier 2 (`claude-haiku-5-5`) with `0` `HOLLOW` runs**, and **all 83 verified non-numeric entries (`100.0%`) across the 16 runs are `SUPPORTS`**.

### 3.3 Cohort C (`n = 44` non-B first-time index nodes): Pre-Dispatch Skip & `accepted_partial` Filtering
- The 44 remaining previously unrun index nodes in Stages 7–10 consist almost entirely of external literature `SOURCE_RECORD` nodes (`DeWitt 1967`, `Rovelli 1996`, `Page–Wootters 1983`, `Ryu–Takayanagi 2006`, `Maldacena 1997`, `Haag–Kastler 1964`, `Reeh–Schlieder 1961`, `Sorkin 2003`, `Ponzano–Regge 1968`, `Barrett–Crane 1998`, `Zauner 1999`, `Brierley–Weigert 2009`, `Horodecki 1996`, `Peres 1996`), continuum `IMPORTED_ASSUMPTION` nodes, and `OPEN` gap/fence nodes.
- **31 of the 44 (`70.45%`) were prevented from becoming false-positive `accepted` runs:**
  - **20 (`45.45%`)** were skipped pre-dispatch at \$0.00 spend (`skipped_ungroundable`) by `groundability()`.
  - **9 (`20.45%`)** were rejected as `not_accepted`.
  - **2 (`4.55%`)** (`LQG-SPIN-NETWORK-STATES-IMPORT`, `LQG-TURAEV-VIRO-1992-SOURCE`) were capped at `accepted_partial` because `credited_paths` refused to credit `@KNOWN+` neighbour declarations toward `min_verified = 2`.
- Of the 13 accepted Cohort C runs, 2 are `Supported` (`CQFT-FINITE-CAUSET-IDENTIFICATION`, `MUB6-OPENAI-FAMILY-LE-FIVE`) and 11 are `HOLLOW` (`10` with `TANGENTIAL` entries citing adjacent stage files and `1` with `IRRELEVANT` entries on `ADS-HAPPY-TOY-NOT-DUALITY-GAP`; **0 `MISLEADING`**).

---

## 4. Run-Level `HOLLOW` Rate by `node_status` and Model Tier

### 4.1 Breakdown by `node_status` (`57` Accepted Round 3 Runs)

| Node Status (`dag/derivation_dag.json`) | R3 Accepted Runs | R3 `Supported` | R3 `HOLLOW` | R3 `HOLLOW` Rate | R2 Non-Numeric `HOLLOW` Rate |
| :--- | ---: | ---: | ---: | ---: | ---: |
| **`PROVED_LEAN`** | **20** | **20** | **0** | **0.00%** | 3.03% (3 / 99) |
| **`COMPUTATIONALLY_CHECKED`** | **9** | **9** | **0** | **0.00%** | 20.78% (16 / 77) |
| **`IMPORTED_ASSUMPTION`** | **6** | **3** | **3** | **50.00%** | 0.00% (0 / 10) |
| **`OPEN`** | **13** | **6** | **7** | **53.85%** | 59.46% (44 / 74) |
| **`SOURCE_RECORD`** | **6** | **2** | **4** | **66.67%** | 34.78% (8 / 23) |
| **`DEFINITION`** | **3** | **1** | **2** | **66.67%** | 29.27% (12 / 41) |
| **Total** | **57** | **41** | **16** | **28.07%** | **25.29%** (87 / 344) |

> **Key finding by `node_status`:** Across all 29 Round 3 accepted runs on nodes that represent proved or computationally checked claims in the repository (`PROVED_LEAN`: 20, `COMPUTATIONALLY_CHECKED`: 9), the post-tightening `HOLLOW` rate is **0.00% (`0 / 29`)**. Every one of the 16 `HOLLOW` runs in Round 3 occurs on an `OPEN` (`7`), `SOURCE_RECORD` (`4`), `IMPORTED_ASSUMPTION` (`3`), or methodological `DEFINITION` (`2`) node whose statement records that the target theorem, continuum structure, or external paper is not proved as a finite theorem in the checkout.

### 4.2 Breakdown by Model Tier (`57` Accepted Round 3 Runs)

| Model Tier | Accepted Runs | `Supported` | `HOLLOW` | R3 Semantic `HOLLOW` Rate | R2 Semantic `HOLLOW` Rate | Non-Numeric Entries | `SUPPORTS` | `TANGENTIAL` | `IRRELEVANT` | `MISLEADING` | R3 `MISLEADING` Rate | R2 `MISLEADING` Rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **`claude-haiku-5-5` (Tier 2)** | **51** | 38 | 13 | **25.49%** | 31.58% (6 / 19) | **190** | 151 (79.5%) | 32 (16.8%) | 6 (3.2%) | 1 (0.5%) | **0.53%** | 6.82% (3 / 44) |
| **`claude-sonnet-5-5` (Tier 3)** | **6** | 3 | 3 | **50.00%** | 23.83% (66 / 277) | **19** | 8 (42.1%) | 11 (57.9%) | 0 (0.0%) | 0 (0.0%) | **0.00%** | 0.31% (3 / 972) |
| **Total** | **57** | **41** | **16** | **28.07%** | **25.29%** (87 / 344) | **209** | **159 (76.1%)** | **43 (20.6%)** | **6 (2.9%)** | **1 (0.5%)** | **0.48%** | **1.57%** (18 / 1,144) |

*(Note: Tier 0 `free` models were skipped in Round 3 because `OPENROUTER_API_KEY` was not set in the environment, so all 91 runs started at Tier 2 `claude-haiku-5-5` and escalated to Tier 3 `claude-sonnet-5-5` only when Tier 2 failed verification.)*

---

## 5. Audit of the Single `MISLEADING` Entry and the 16 `HOLLOW` Runs in Round 3

### 5.1 The Single `MISLEADING` Entry (`1 / 209 = 0.48%`)
- **`[156]` on `TFQ-0014` (`claude-haiku-5-5`, `relation` `rel_assoc_from_operation`, `MISLEADING`):**
  - **Run:** `TFQ-0014/20261022T181633Z_ladder` (`a2-1`, overall run is **`Supported`** via `[155]` `finite_groupoid_algebra.rs::FiniteGroupoidAlgebra`)
  - **Claim:** `"Associativity holds for the finite groupoid operation used in the convolution generator. [hypotheses: The operation is the finite groupoid operation of a ValidatedFiniteGroupoid G, as used by FiniteGroupoidAlgebra.]"`
  - **Cited declaration:** `code/rust/src/lie_theory/finite_group.rs::check_associativity_for_pair` (`fn`, line 259, offered via `@KNOWN+` from 1-hop neighbour `TFQ-0013`)
  - **Why it passed & why it is `MISLEADING`:** `check_associativity_for_pair` is a method on `FiniteGroup` in `finite_group.rs` checking total multiplication-table associativity `a*(b*c) == (a*b)*c`, not a check on partial groupoid composition in `ValidatedFiniteGroupoid` or `FiniteGroupoidAlgebra`. It passed `relation_overlap` because its function name and body contain the token `associativity` / `NotAssociative`.

### 5.2 Root Causes of the 16 `HOLLOW` Runs in Round 3
1. **5 `HOLLOW` runs where the node's own `dag/derivation_dag.json` entry or statement names a finite contrast/neighbour file (`buckets 1–5`):**
   - `ADS-HAPPY-2015-SOURCE` (`SOURCE_RECORD`), `CQFT-LOCAL-NET-AXIOMS-IMPORT` (`IMPORTED_ASSUMPTION`), `CT-MARLETTO-VEDRAL-2017-SOURCE` (`SOURCE_RECORD`), `LQG-EPRL-VERTEX-IMPORT` (`IMPORTED_ASSUMPTION`), and `MAJ-OPEN-LINDBLAD-TRANSFER-ENVELOPE` (`OPEN`). Because these nodes anchor or name a finite helper file (`H037FourQubitCssSurfaceCode.lean`, `CausalOrder.lean`, `Entanglement.lean`, `H024FourSimplexSpinfoamS4.lean`, `MajoranaCore.lean`) while their prose statement concerns an external publication or continuum obligation, the model's accurate citations of those files are classified as `TANGENTIAL`.
2. **11 `HOLLOW` runs where an unanchored `OPEN` / `DEFINITION` / `SOURCE_RECORD` / `IMPORTED_ASSUMPTION` node was credited via `@SRC` fallback candidates (`buckets 7–9`):**
   - `ADS-HAPPY-TOY-NOT-DUALITY-GAP` (`OPEN`, 3 `IRRELEVANT` from `DiscreteTimeStoneSpec.lean`), `AUTH-BLIND-DERIVATION-PROTOCOL` (`DEFINITION`, 3 `IRRELEVANT` from `HilbertLiftL2Model.lean` and `GenesisFspBridge.lean`), and 9 `TANGENTIAL` runs (`ADS-REGGE-AREA-RT-GAP`, `AUTHF-RICE-GODEL-OPEN`, `CQFT-CAUSAL-FACTORIZATION-IMPORT`, `CQFT-EPSTEIN-GLASER-1973-SOURCE`, `CT-REFUSAL-OBSTRUCTION-ANALOGY`, `DFM-CONTINUUM-INTERFACE`, `LQG-AREA-VOLUME-SPECTRA-SOURCE`, `MUB6-NO-QUARTET-D6`, `PGW-METATHEORY-OBJECT-LANGUAGE-SPLIT`).
   - **Why `credited_paths` allowed them:** In `packets.py` (`compile_p0`, line 365), `credited_paths` currently includes all `@SRC` candidate paths (`{p for _, p, _ in candidates}`), including fuzzy stem-overlap matches with `score < STRONG_SCORE` (`20`). Restricting `credited_paths` on `OPEN`, `DEFINITION`, `SOURCE_RECORD`, and `IMPORTED_ASSUMPTION` nodes to strong anchors (`anchored_files | named_in_statement | {p for score, p, _ in candidates if score >= STRONG_SCORE}`) would downgrade these 11 unanchored runs from `accepted` to `accepted_partial`, reducing the Round 3 `HOLLOW` rate from **28.07% (`16 / 57`)** to **10.87% (`5 / 46`)**.

---

## 6. Claim Hygiene Summary

1. **What this audit supports:**
   - Across the 57 newly accepted Round 3 LLM ladder runs (`209` verified non-numeric entries), the PR #169 and PR #175 verifier tightenings reduced the entry-level `MISLEADING` rate from **1.57% (`18 / 1,144`) in Round 2 to 0.48% (`1 / 209`) in Round 3** (and from **6.82% to 0.53%** on `claude-haiku-5-5`), reduced the entry-level `IRRELEVANT` rate from **6.03% to 2.87%**, eliminated all `MISLEADING` generator citations (`0 / 66`), and activated `verified_lemma_statements` (`41` verified entries, `87.80%` `SUPPORTS`, `0` `IRRELEVANT`/`MISLEADING`).
   - On the 45 nodes in Round 3 that had prior Round 1/2 accepted runs (Cohorts A + B), the run-level `HOLLOW` rate dropped from **53.33% (`24 / 45` all) / 40.00% (`14 / 35` non-numeric) in Round 2 to 11.90% (`5 / 42`) in Round 3**: all 16 newly mechanized `PROVED_LEAN` frontier and CQFT target nodes achieved **0.00% `HOLLOW` (`83 / 83` `SUPPORTS` entries)**, and on the 31 re-run Round 2 false-positive nodes (Cohort A), the `HOLLOW` rate dropped from **38.71% (`12 / 31`) to 17.86% (`5 / 28`)**, with 3 Round-2 hollow nodes blocked from `accepted` and 5 converted to `Supported`.
   - Across all 29 Round 3 accepted runs on `PROVED_LEAN` (`20`) and `COMPUTATIONALLY_CHECKED` (`9`) nodes, the `HOLLOW` rate is **0.00% (`0 / 29`)**.
2. **What this audit does not support:**
   - It does not show that `credited_paths` blocks all `HOLLOW` acceptances on unanchored `OPEN`, `DEFINITION`, `SOURCE_RECORD`, or `IMPORTED_ASSUMPTION` nodes when `@SRC` fuzzy stem matching (`score < STRONG_SCORE`) offers a fallback file into `candidates`: 11 such runs in Round 3 (plus 5 on nodes whose DAG entry anchors a finite contrast file) still reached `accepted` with `TANGENTIAL` (`14` runs) or `IRRELEVANT` (`2` runs) entries, yielding an overall Round 3 `HOLLOW` rate of **28.07% (`16 / 57`)** across Cohorts A+B+C combined.
   - It does not show that a `SUPPORTS` classification on a P0 operad entry discharges an `OPEN` or `IMPORTED_ASSUMPTION` obligation.
3. **The narrowest defensible claim:**
   - The PR #169 + PR #175 verifier tightenings (`allowed_refs`, `credited_paths`, `GENERATOR_KINDS`/`RELATION_KINDS`/`_is_test_decl`, `relation_overlap`, `STRUCTURAL_STEM_STOP`, `groundability()`) combined with the PR #168/#171 `FrontierTargets` mechanizations cut the `HOLLOW` rate on re-run Round 2 nodes by more than two-thirds (`40.00%` semantic-hollow / `53.33%` overall $\to$ `11.90%`), eliminated `HOLLOW` acceptances on `PROVED_LEAN` and `COMPUTATIONALLY_CHECKED` nodes in Round 3 (`0 / 29`), and prevented 31 of 44 (`70.45%`) newly attempted Stage 7–10 bibliography/continuum/gap nodes from becoming false-positive acceptances, while leaving 16 `HOLLOW` acceptances on `OPEN` / `SOURCE_RECORD` / `IMPORTED_ASSUMPTION` / `DEFINITION` nodes.
4. **The next test needed:**
   - Tighten `credited_paths` in `dag/pfp/llm_ladder/packets.py` (`compile_p0`) so that fuzzy `@SRC` fallback candidates (`score < STRONG_SCORE = 20`) are not added to `credited_paths` on `OPEN`, `DEFINITION`, `SOURCE_RECORD`, and `IMPORTED_ASSUMPTION` nodes, and replay `verify_p0` across the 57 Round 3 accepted runs to check that the 11 unanchored `HOLLOW` runs are downgraded to `accepted_partial` without losing any of the 41 `Supported` runs.
