# NOTEBOOK_PLAN.md — Build Specification for the Symbol Game Interactive Notebook Series

`AuthorityEffect: None.`

This file is the build specification for the 12-part Jupyter notebook series accompanying **The Symbol Game: Three-Layer Sovereignty and Discrete $L_1$ Projection** (Paper 032, `008_mssn_s_n_symbol_game_recovery`). It serves as an exact architectural plan, curriculum guide, and pedagogical standard.

The derivation's direction and mathematical framing are the author's (Jeremy Carroll); the notebooks are an instrument for teaching, visualizing, and objectively testing it. Every notebook is built and reviewed against the non-negotiable house disciplines in §2.

---

## 1. Audience and Purpose

The reader is a researcher, engineer, student, or reviewer who wants to understand why and how the Symbol Game transforms language model interactions from ungrounded, sycophantic chat into verifiable, discrete deductions.

Each notebook enables the reader to:
1. **Trace the Historical Evolution**: Observe how the system grew from MSS-0 relational axioms and $S_n$ arity filtration to modern three-layer sovereignty and discrete $L_1$ coboundary projection.
2. **Interact with the Mathematics**: Use reactive widgets (`ipywidgets`) to build relational state spaces, trigger abstract rewrite rules, fire packet firewalls, and adjust simplicial edge claims to see real-time obstruction norms $\Phi_1$.
3. **Inspect Transformer Mechanics**: Examine empirical open-weights tensor measurements demonstrating $3.14\times$ attention concentration on declared carriers and exact per-token KV Frobenius norm invariance.
4. **Run Live Demos or Replay Audited Receipts**: Connect their own OpenRouter API key or local LLM (Ollama, vLLM), or execute in 100% offline deterministic mock mode reproducing Paper 032 receipts.
5. **Verify Against Machine-Checked Code**: Trace every claim to its exact Python verifier in `code/`, its typed claim ID in `the_symbol_game_three_layer_sovereignty_and_discrete_l1_projection_claim_ledger.md` (`PO032-C01` through `PO032-C74`), and its Lean 4 theorem.

---

## 2. Authoring Disciplines (Non-Negotiable House Style)

Every notebook in this series must strictly adhere to the Genesis authoring standards:

### 2.1 Claim Typing Legend
Every notebook carries this legend near the top, and tags each substantive result with one of the four types:
- **[Pinned]** — Produced by local code, an audited benchmark, or an exact cryptographic receipt (`code/*.json`). Cite by filename/function.
- **[Proved]** — A machine-checked theorem in the companion Lean 4 formalization (`lean4/*.lean`). Cite the theorem name and verified axioms.
- **[Declared]** — An explicit convention, carrier alphabet, cost, or objective chosen by the model. Stated as an assumption, never claimed as forced.
- **[Open]** — An explicit limitation or conjecture for which no exhaustive decision or proof is supplied.

Reference ledger IDs (`PO032-C01` through `PO032-C74`) directly.

### 2.2 Guarded Words
The words *forced, minimal, free, canonical, equivalent, universal, complete* appear only alongside an explicit formal proof or a precisely declared scope. Never use them as casual rhetorical flourish.

### 2.3 CAN-Show / CANNOT-Show Frame
Each notebook carries a dedicated scope box stating plainly what the demonstrated mechanism establishes and what it does **not** establish. Honesty about boundaries is mandatory.

### 2.4 Bind to Pinned Evidence, Don't Re-implement
Prefer importing verified routines from `notebook_lib` or Paper 032's `code/` modules (`l1_symbol_game_governor.py`, `packet_firewall_host.py`, etc.). If an inline toy model is created for pedagogical clarity, label it **Illustrative Model** and assert equality against the pinned verifier in the same notebook.

### 2.5 Zero Floating-Point Arithmetic
All discrete $L_1$ projections, incidence matrices, dual certificates, and coboundary calculations must use exact rational arithmetic (`fractions.Fraction` or integer linear combinations). Never use floating-point comparisons for discrete decisions.

### 2.6 Dual-Mode LLM Integration
Every LLM demonstration must support:
- Live API calls via OpenRouter or local endpoints.
- Deterministic offline mock mode falling back seamlessly to Paper 032 benchmark traces if no API key is present.

### 2.7 Anchor Block
End every notebook with an **Anchors** cell tabulating:
- Paper 032 Sections
- Claim Ledger IDs (`PO032-Cxx`)
- Python Source Verifiers
- Lean 4 Theorem Names
- Cryptographic Audit Receipts

### 2.8 Interactive Exercises
End every instructional notebook with **Student Exercises** featuring collapsible or hidden solutions to reinforce active learning.

---

## 3. Curriculum and Notebook Inventory

The former notebooks `00` through `11` now live in these lesson folders:

| NB | Lesson folder | What this sitting checks |
|---|---|---|
| 00 | `970_interactive_foundations/lesson_970_01_1_wager_why_llms_hallucinate_overclaim` | One mock fenced completion and one mock unfenced completion |
| 01 | `800_grammar/lesson_800_02_1_historical_roots_mss_0_genesis_distinction` | One refused self-loop |
| 02 | `800_grammar/lesson_800_04_1_abstract_reduction_systems_ars` | One string rewrite |
| 03 | `950_theory/lesson_950_02_1_three_layers_sovereignty` | One mock fenced completion beside one mock unfenced completion |
| 04 | `900_packets/lesson_900_01_1_4_field_packet_envelope` | One host refusal of `SPECULATE` and of a forbidden character |
| 05 | `700_math/lesson_700_06_1_simplicial_cochains_coboundary_operators` | One consistent obstruction and one frustrated obstruction |
| 06 | `700_math/lesson_700_10_1_total_unimodularity_tum_incidence_matrix` | Subdeterminants of one incidence matrix |
| 07 | `950_theory/lesson_950_04_hott_identity_paths` | One identity-path calculation |
| 08 | `700_math/lesson_700_13_2_empirical_50_task_benchmark_results` | The checked-in 50-task receipt |
| 09 | `950_theory/lesson_950_05_1_what_happens_inside_transformer` | One attention reading |
| 10 | `950_theory/lesson_950_06_topology50_proof_search` | Rows in the checked-in Topology-50 receipt |
| 11 | `970_interactive_foundations/lesson_970_11_1_architecture_governed_agent` | One admitted governed-agent verdict |

## 4. Master Anchor Table

| NB | Lesson folder | Paper 032 Section | Ledger Claims | Python Implementation | Lean 4 Theorem | Audit Receipt |
|---|---|---|---|---|---|---|
| **00** | `970_interactive_foundations/lesson_970_01_1_wager_why_llms_hallucinate_overclaim` | §1, §10 | `PO032-C01`, `PO032-C02` | `notebook_lib/llm_client.py` | — | `code/l1_sparsity_benchmark_receipt.json` |
| **01** | `800_grammar/lesson_800_02_1_historical_roots_mss_0_genesis_distinction` | §2.1–§2.3 | `PO032-C04`..`PO032-C08` | `notebook_lib/governor_adapter.py` | — | — |
| **02** | `800_grammar/lesson_800_04_1_abstract_reduction_systems_ars` | §2.4–§2.5 | `PO032-C09`..`PO032-C14` | `papers/032.../code/arity_rewrite_engine.py` | — | — |
| **03** | `950_theory/lesson_950_02_1_three_layers_sovereignty` | §1.1–§1.3 | `PO032-C15`..`PO032-C21` | `notebook_lib/llm_client.py` | — | `code/attention_entropy_kv_norm_receipt.json` |
| **04** | `900_packets/lesson_900_01_1_4_field_packet_envelope` | §4.1–§4.4 | `PO032-C22`..`PO032-C28` | `papers/032.../code/packet_firewall_host.py` | — | — |
| **05** | `700_math/lesson_700_06_1_simplicial_cochains_coboundary_operators` | §3.1–§3.3 | `PO032-C29`..`PO032-C36` | `papers/032.../code/l1_symbol_game_governor.py` | — | — |
| **06** | `700_math/lesson_700_10_1_total_unimodularity_tum_incidence_matrix` | §3.4 | `PO032-C37`..`PO032-C42` | `papers/032.../code/scaling_benchmark_v20.py` | `TotalUnimodularity.lean` | — |
| **07** | `950_theory/lesson_950_04_hott_identity_paths` | §3.2, §6 | `PO032-C43`..`PO032-C48` | `papers/032.../code/hott_symbol_game.py` | `IdentityTypes.lean` | — |
| **08** | `700_math/lesson_700_13_2_empirical_50_task_benchmark_results` | §7.1–§7.4 | `PO032-C49`..`PO032-C56` | `papers/032.../code/l1_sparsity_bullshit_benchmark.py` | — | `code/l1_sparsity_benchmark_receipt.json` |
| **09** | `950_theory/lesson_950_05_1_what_happens_inside_transformer` | §8.1–§8.4 | `PO032-C57`..`PO032-C63` | `papers/032.../code/attention_entropy_kv_norm_benchmark.py`| — | `code/attention_entropy_kv_norm_receipt.json` |
| **10** | `950_theory/lesson_950_06_topology50_proof_search` | §9.1–§9.4 | `PO032-C64`..`PO032-C70` | `papers/032.../code/interactive_lean4_governor.py` | `Topology50.lean` | `code/topology50_benchmark_receipt.json` |
| **11** | `970_interactive_foundations/lesson_970_11_1_architecture_governed_agent` | §10 | `PO032-C71`..`PO032-C74` | `notebook_lib/governor_adapter.py` | — | — |

---

## 5. Verification and Test Gates

All notebooks are verified by:
1. **Unit Test Suite**: `tests/test_notebook_lib.py` testing `notebook_lib` with >95% statement and branch coverage.
2. **Headless Replay**: `tests/test_notebook_execution.py` executes the notebooks named in that file.
3. **Format & Claim Linting**: Automated checks verifying presence of claim legends, anchors blocks, and absence of unguarded words.
