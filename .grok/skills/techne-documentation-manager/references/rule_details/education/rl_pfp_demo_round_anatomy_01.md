# Detailed definition: PFP Demo Round Anatomy & Live-Run Integrity (1)

**AuthorityEffect:** None.

Parent: [PFP Demo Round Anatomy & Live-Run Integrity](../../../../../rules/education/rl_pfp_demo_round_anatomy.md). Load for the matching predicate, not every task.

# Rule: PFP Demo Round Anatomy & Live-Run Integrity

**AuthorityEffect:** None.

Split from [`../claims/rl_review_evidence_reproducibility.md`](../../../../../rules/claims/rl_review_evidence_reproducibility.md) on 2026-10-06; the invariant text is unchanged.

---

## PFP Demo Round Anatomy & Live Execution Integrity Invariant (`RULE_PFP_DEMO_ROUND_ANATOMY_AND_RECEIPT_INTEGRITY_001`)

> **Strict Prohibition of Simulated "Live Runs", Extensible Multi-Stage Modes, & Typed PFP Contracts:**
>
> 1. **Zero Mock or Simulated Provider Receipts in `live_runs/`:**
>    - Any file path or directory designated `live_runs/` must contain EXCLUSIVELY receipts, raw bytes, token usage, latencies, and generation IDs originating from genuine, live network dispatches to an external model/provider backend.
>    - Writing mock, synthetic, scripted, or offline assertion results into `live_runs/` or attributing them to a model provider is strictly prohibited.
>    - If an execution is a host-only assertion or offline regression check, it must be labeled under a dedicated host verification path (e.g. `host_checks/` or `offline_controls/`), never `live_runs/`.
>    - When provider credentials exist in `.env` (e.g., `OPENROUTER_API_KEY`), live rounds must dispatch through the authorized provider adapter (e.g., `openrouter_transport` or `OpenRouterBackend`) and record authentic HTTP responses and generation IDs.
>
> 2. **Extensible Modes & Multi-Stage Architecture:**
>    - Modes in PFP are open and extensible, not restricted to a fixed 6-mode set. PFP evaluates diverse representation modes, including:
>      - Direct plain text baselines
>      - Carrier boundary probes and delta encodings
>      - Adversarial collision and prompt injection probes
>      - Explicit policy, license, and typed abstention modes
>      - Reversible glyph and symbolic wire rewrites (e.g. MSS-N, AST prefix)
>      - Relational and database-constraint schemas (e.g. SQL triggers where relational integrity is tested)
>    - Execution pipelines may span multiple stages (1-stage direct, 2-stage staged reasoning/filtration, or N-stage composition). Each stage transition must declare its input/output types, serialization format, and check frequency.
>
> 3. **Mandatory Typed PFP Round Contract:**
>    - Every round or pilot directory must declare a typed experimental contract:
>      a. `seed` / `stimulus`: Verbatim raw input stimulus and protected task question.
>      b. `prompt_packet`: Formally typed prompt packet envelope with explicit schema and framing.
>      c. `modes_tested`: Declared representation transformations and operational contracts.
>      d. `stages`: Sequence of pipeline stages, intermediate representations, and stopping rules.
>      e. `oracle`: Independent, executable host acceptance rule (models never grade themselves).
>      f. `receipt`: Machine-verifiable execution receipt capturing raw response, outcome status (`ACCEPTED`, `MALFORMED`, `REFUSED`, `WRONG_ANSWER`, `TRUNCATED`), token counts, latency, and actual cost.
>      g. `type_taxonomy`: Explicit classification of the experimental elements across the PFP type vocabulary: `filtration`, `schemas`, `receipts`, `spans`, `normal forms`, `packets`, `fixtures`, `dialects`, `contracts`.
>
> 4. **Token & Cost Minimization Discipline:**
>    - Live runs must spend the absolute minimum tokens and budget needed to observe the targeted behavior.
>    - Reserve worst-case micro-USD prior to network dispatch.
>    - Use compact, high-signal task fixtures and cost-effective provider backends.
>
> 5. **Anti-Bulk Generation & Anti-Vacuous Mock Discipline:**
>    - Autonomous agents must never bulk-generate dozens of placeholder, stub, or simplified mock rounds that test only internal Python parsers while claiming to test PFP.
>    - Every pilot must test genuine model fidelity questions or formally isolate a verified host-side boundary.

---

## PFP Pilot Modus Operandi & Structural Lift Protocol (`RULE_PFP_PILOT_MODUS_OPERANDI_AND_LIFT_PROTOCOL_001`)

> **Mandatory Standard Operating Procedure for Empirical Pilots (`pilot_0000000`–`pilot_0000099`):**
>
> 1. **Strict Root-Level Hygiene & Directory Partitioning:**
>    - The pilot root directory MUST contain exclusively: `spec.yaml`, `seed.yaml`, `prompt_template.yaml`, `p_star.yaml` (and versioned/lifted prompt variants such as `p_star_lifted.yaml`), `README.md`, `results/`, and `tests/`.
>    - No loose trial prompts (`seed_rewrite_*.yaml`, `p_star_rewrite_*.yaml`) or individual model replies (`response_*.yaml`) may reside in the pilot root.
>    - Every prompt execution MUST be encapsulated in a dedicated, sequential, zero-padded test folder (`tests/test_00/` through `tests/test_99/`).
>    - Each test folder MUST contain exactly:
>      - `test_spec.yaml`: Typed metadata (`test_id`, `dialect_name`, `generation_id`, `expected_outcome`, `actual_outcome`, `metrics`).
>      - `input.yaml`: Verbatim prompt payload dispatched to the model.
>      - `response.yaml`: Complete response document capturing `raw_reply`, `reasoning_content`, parsed JSON payload, latency, token metrics, and typed gate receipt.
>
> 2. **Mechanized Mathematical Grounding (Anti-Trivial Seed Directives):**
>    - Advanced pilots (Rungs 2–6) must NEVER use trivial or unverified toy seeds.
>    - The problem seed must be grounded directly in fully tested, mechanized paper claims—specifically Lean 4 Mathlib theorems and Python certified oracles from the `coda_atlas/F004_papers/` estate.
>
> 3. **The 3-Stage Empirical Derivation Protocol:**
>    - **Stage 1 (Bare Seed + 10 Dialect Rewrites):** Test the bare mathematical problem without prompt template guidance or hints across 10 diverse surface dialects:
>      1. *Tier H:* Verbal Topological Covering & Patch Overlap
>      2. *Tier D:* Dense Mathematical Formula
>      3. *Tier S:* Discrete SymSys Glyph Syntax
>      4. *Matrix/Vector:* Incidence & Coordinate Projection System
>      5. *Category Theory:* Covering Diagram & Sheaf Functors
>      6. *Discrete Cochains:* Simplicial Sheaf Complex ($C^0 \xrightarrow{d_0} C^1$)
>      7. *Channel Masking:* Coordinate-Deletion Fiber Projections
>      8. *S(n) Down-Map:* Retraction & Projection Dialect
>      9. *Genesis Relational:* Relational Substrate Coordinate Tables
>      10. *Operator Axiomatic:* Explicitly Licensed Axiomatic System
>    - **Stage 2 ($P^*$ Template Baseline under SPK-001):** Dispatch the canonical problem inside the $P^*$ prompt template under SPK-001 governance. Monitor whether the model requests a structural lift (`rule_request_structural_lift`) when operations lie outside base carrier capacity.
>    - **Stage 3 (DDC Structural Lift Grant):** If a lift is requested or required, grant an explicit DDC Structural Lift contract (`governance-wdp`), extending carrier capacity and operational licenses, driving the model into the exact certified $\ell^1$-regime.
>
> 4. **Zero-Overwrite Versioning & Complete Audit Trail:**
>    - Never overwrite earlier prompt generations or response files.
>    - New iterations must increment generation or version IDs (`p_star_rewrite_XX_v2.yaml`) and preserve immutable lineage records in `lineage.parent_id`.
