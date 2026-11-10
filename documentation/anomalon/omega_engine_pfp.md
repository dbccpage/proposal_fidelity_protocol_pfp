# Anomalon Integration: `omega_engine_pfp`

**AuthorityEffect:** None  
**Status:** Code-Grounded Reference Documentation  
**Repository Path:** `c:\Users\a343o\source\repos\anomalon\omega_engine_pfp`  
**Governing Standard:** Proposal Fidelity Protocol & Symbol Game Bounded Context  

---

## 1. System Role and Overview

`omega_engine_pfp` serves as the sovereign Proposal Fidelity Protocol (PFP) and Symbol Game application within the Anomalon architecture. It coordinates multi-agent cognitive debate, evaluates discrete coboundary descent metrics over candidate proposals, and produces cryptographically verifiable execution receipts.

Under the domain context definition in `omega_engine_pfp/CONTEXT.md`:
- The **Symbol Game** operates as a deterministic control spine where candidate algebraic and discrete proposals are retracted onto admissible invariant manifolds through multi-agent debate.
- A **Retraction Turn** is a discrete step evaluating candidates and computing strict descent metrics.
- The **Obstruction Score** comprises a three-tuple: curvature ($\Gamma_2$), boundary defect norm ($\Phi_1$), and active defect count.
- **Strict Descent** enforces that successive retraction turns monotonically decrease or maintain obstruction norms without boundary leakage.
- Every artifact, turn envelope, and receipt emitted across the application explicitly specifies `AuthorityEffect: None`.

---

## 2. Clean Architecture Layer Hierarchy

The application strictly enforces Clean Architecture isolation boundaries, prohibiting inward dependency leaks:

```
┌────────────────────────────────────────────────────────┐
│                      entrypoints/                      │
│        (CLI commands, HTTP endpoints, Workbench)       │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                      controllers/                      │
│     (pfp_controller, symbol_game_controller, ...)      │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                       use_cases/                       │
│    (execute_stage_pipeline, drive_turn, scoring, ...)  │
└─────────────┬────────────────────────────┬─────────────┘
              │                            │
┌─────────────▼──────────────┐ ┌───────────▼─────────────┐
│       infrastructure/      │ │         domain/         │
│ (task_turn, replay, FFI)   │ │ (contracts, cochain,    │
└────────────────────────────┘ │  entities, aggregates)  │
                               └─────────────────────────┘
```

### 2.1 Domain Layer (`omega_engine_pfp/domain/`)
The domain layer encapsulates enterprise business rules, aggregates, entities, value objects, domain events, and pure ports. It maintains zero dependencies on outer frameworks or I/O devices:
- **Contracts (`domain/contracts/`):**
  - `pfp_calculations.py`: Defines mathematical contracts for exact integer and rational calculations, quotient distances, and defect scoring.
  - `pfp_runtime.py`: Protocol specifications for runtime state transitions and turn lifecycle steps.
- **Cochain Complex (`domain/cochain.py`):**
  - Defines `PromptCellComplex`, `PrimeTriadContext`, and `CochainDisposition`. Models the cochain sequence $C^0 \to C^1 \to C^2$ over $\mathbb{Q}$ where coboundary operators satisfy nilpotence $d_1 \circ d_0 = 0$.
- **Aggregates & Entities (`domain/aggregates/`, `domain/entities/`):**
  - Encapsulates retraction state machines, candidate proposal lifecycles, and verification receipts.
- **Packet Codec (`domain/packet_codec.py`):**
  - The value object kernel executing domain-canonical serialization, SHA-256 digest computation, and tamper verification without floating-point conversion.
- **Glyph Calculus (`domain/glyph_calculus.py`):**
  - Formal symbol manipulation and syntactic verification rules for discrete deformation tokens.

### 2.2 Use Cases Layer (`omega_engine_pfp/use_cases/`)
Thin, focused orchestrators implementing specific application workflows using Railway-Oriented Programming (`Result[T, E]` monad with `Success` and `Refusal` tracks):
- `execute_stage_pipeline.py`: Orchestrates multi-stage PFP retraction sequences.
- `pfp_stages.py`: Defines stage execution steps and transition barriers.
- `pfp_prompt.py`: Compiles, normalizes, and binds prompt templates to candidate contexts.
- `pfp_proposal.py`: Ingests and validates untrusted candidate proposals against registered kill conditions.
- `drive_turn.py`: Coordinates retraction turn progression, invoking mathematical evaluators to check for strict descent.
- `scoring.py`: Computes coboundary and obstruction metric updates, verifying whether proposed changes contractively reduce system defect mass.
- `llm_turn.py`: Handles individual language model turn preparation, sanitization, and response parsing.
- `code_change.py`: Evaluates proposed code modifications, unified diff syntax, and boundary conditions.

### 2.3 Infrastructure Layer (`omega_engine_pfp/infrastructure/`)
Contains adapters connecting abstract domain ports to external services, persistence mechanisms, and the native Rust runtime:
- `adapters/pfp_frozen_replay.py`: Supports deterministic offline replay under declared assumptions by binding stored raw model replies to turn digests without calling remote providers.
- `task_turn.py`: Implements task turn formatting and prompt assembly with byte-level parity matching Rust's `omega_symbol_game_runtime::pfp_task_turn`.
- `braid_tournament.py`: Coordinates multi-seat adversarial tournaments between candidate models.
- `retraction_benchmark.py`: Benchmark suite evaluating retraction efficiency across standardized obstruction testbeds.
- `providers.py` & `openrouter_seat_gateway.py`: Model provider gateways enforcing token budget fences, rate-limiting, and key sanitization.
- `pfp_operad.py`: Bridges PFP task turns to planar colored operad composition trees.

### 2.4 Controllers Layer (`omega_engine_pfp/controllers/`)
Translates external inputs into domain use-case commands and serializes domain outcomes into transport representations:
- `pfp_controller.py`: Entrypoint for PFP pipeline execution and stage dispatch.
- `symbol_game_controller.py`: Manages Symbol Game campaign lifecycles and turn requests.
- `symbol_game_engine.py`: Engine coordinator executing turn transitions.
- `prompt_controller.py`: Validates and compiles prompt artifacts.
- `code_change_controller.py`: Ingests, checks, and applies code change proposals.
- `turn_controller.py` & `turn_driver_controller.py`: Manages discrete retraction step requests and descent checks.

### 2.5 Entrypoints (`omega_engine_pfp/entrypoints/`)
Executable entrypoints exposing CLI commands and process runners for batch execution, local testing, and system verification.

---

## 3. Embedded Rust Engine (`omega_pfp_engine` / `pfp-engine`)

Located at `omega_engine_pfp/engine_rs`, the embedded engine is a standalone Rust crate (`omega_pfp_engine`) compiling to the `pfp-engine` binary. It provides a local, low-latency HTTP server (`server.rs`) and CLI suite powering the interactive workbench on `anomalon.com/app`.

```
omega_engine_pfp/engine_rs/src/
├── lib.rs                  # Crate root
├── main.rs                 # CLI & HTTP server entrypoint
├── server.rs               # tiny_http server handling workbench routes
├── density.rs              # Quantum prompt density calculation
├── mine.rs                 # Planar colored operad tree mining
├── turn.rs                 # PFP turn binding & prompt template compilation
├── review.rs               # Paper Review v0 bounded producer-critic loop
├── policy.rs               # Funding policy ledger & idempotency store
├── work.rs                 # Host-funded Anthropic work lane
├── answer.rs               # Response model representations
├── catalog.rs              # Static JSON catalog loaders
├── model.rs                # Model invocation & outcome data types
├── run.rs                  # Run orchestration routines
└── workbench_routes.rs     # HTTP route handlers for /api/beta/pfp/*
```

### 3.1 Quantum Prompt Density (`density.rs`)
Invokes `omega_engines::quantum::prompt_density` to compute byte-feature density diagnostics of input texts:
- **Representation:** Constructs a 128-coordinate density operator $\rho$ from SHA-256-hashed whitespace-delimited words, word positions, and word bigrams across up to 16 consecutive text slices.
- **Invariants:**
  - $\rho$ is positive semidefinite with $\mathrm{Tr}(\rho) = 1$.
  - Computes eigenvalues, purity $\gamma = \mathrm{Tr}(\rho^2)$, Shannon entropy $S = -\sum_i \lambda_i \log_2 \lambda_i$ (bounded at 4 bits across 16 slices), and numerical effective rank.
  - Computes Quantum Jensen-Shannon Divergence (QJSD) in $[0, 1]$ bits between seed text and response text:
    $$D_{\mathrm{QJS}}(\rho_1, \rho_2) = S\left(\frac{\rho_1 + \rho_2}{2}\right) - \frac{1}{2}S(\rho_1) - \frac{1}{2}S(\rho_2)$$
- **Claim Hygiene Scope:** Formally declared as a floating-point diagnostic (`NUMERIC_KIND: "floating-point diagnostic (f64), not a certified value"`). It measures structural byte and token distribution, not semantic truth or reasoning validity. Tolerance tests (`bits_below_pow10`) use pure integer arithmetic to eliminate floating-point non-determinism.

### 3.2 Planar Colored Operad Tree Mining (`mine.rs`)
Reuses `omega_symbol_game_runtime::operad` and `omega_operad_theory` to parse unstructured prompt text into structured operadic trees:
- **Decomposition:** Segments seed text into discrete clauses (`Clause`), recording exact start and end byte offsets.
- **Leaf Assignment:** Each clause becomes a leaf in an `OperadTree` assigned an admitted color from `catalog/prompt_operads.v1.json` (e.g., `Stopping`, `Constraint`, `Instruction`, `Role`).
- **Witness Detection:** Scans clauses against cataloged anti-pattern word lists (e.g., self-certifications, unbounded requirements, conflicting directives).
- **Residual Calculation:** Calculates an exact $L_1$ residual norm as the weighted sum of active anti-pattern witnesses:
  $$\|R\|_{L_1} = \sum_{w \in \mathrm{witnesses}} \mathrm{weight}(w)$$
- **Healthy Operation Pairing:** For each anti-pattern witness, the miner pairs it with a healthy unary endomorphism ($A \circ H = \emptyset$) that targets the witnessed clause slot. The operad kernel verifies the graft signature, returning `graft: "TYPED"` upon structural acceptance.

### 3.3 Prompt Turn Binding (`turn.rs`)
Integrates `omega_prompt_civilization::forge` and `omega_symbol_game_runtime::pfp_task_turn`:
- Assembles prompt artifacts by injecting active objectives, demand lists, and obstruction hints.
- Normalizes policies to ensure that admitted constructors, kill conditions, and required reply fields match both in the wire artifact and in canonical cryptographic digest material.

### 3.4 Paper Review v0 (`review.rs`)
Implements a 3-stage bounded producer-critic loop (`plan` $\to$ `section` $\to$ `assemble`) over research manuscripts:
1. `plan`: Segments the paper into sections and paragraphs with exact byte spans. Runs deterministic host checks from `catalog/review_checks.v1.json` and the unhedged-verb claim hygiene antibody `ab_coda_claim_hygiene_unhedged_verbs`.
2. `section`: Dispatches individual sections to dual seats as `PreparedTaskTurn`s:
   - `PRODUCER_SEAT` ("producer (Begemot)"): Proposes findings categorized into `MATH`, `ASSERTION`, `ASSUMPTION`, `CITATION`, `LOCAL_EDIT`, `GLOBAL_EDIT`, `SPELLING`.
   - `CRITIC_SEAT` ("critic (Koroviev)"): Evaluates proposed findings, issuing `KEEP` or `REJECT` verdicts with one-line justifications.
3. `assemble`: Re-derives all metrics from original manuscript bytes and stored model replies. Re-verifies quote anchorage against byte offsets (`UNANCHORED` if missing, `CHECKED` for host checks), producing an annotated report without modifying the manuscript source.

### 3.5 Funding Policy Enforcement (`policy.rs`, `work.rs`)
Enforces strict accounting boundaries across model execution lanes:
- **Execution Lanes:**
  - `offline`: Pure deterministic replay using stored responses.
  - `byok`: Bring-Your-Own-Key lane funded by user-supplied API keys.
  - `sponsor_free`: Host-sponsored free tier with strict daily usage caps.
  - `work_anthropic`: Dedicated host-funded lane for production tasks (`work.rs`).
- **Ledger & Reserves (`policy.rs`):** In-memory ledger tracking provider call counts per UTC day (`DAY_SECS = 86_400`). Enforces single in-flight call per user, pre-dispatch reservation, post-dispatch settlement, and idempotency caching (`MAX_IDEMPOTENCY_ENTRIES = 4096`).
- **Price Catalog (`work.rs`):** Governed by `catalog/work_prices.v1.json`. All prices are recorded as integer micro-USD per million tokens (zero floating point). Enforces daily budget ceilings (`MICRO_USD_PER_CENT = 10_000`).

---

## 4. Packet Schemas and Cryptographic Receipts

All communication envelopes and evaluation outcomes are governed by JSON schemas in `omega_engine_pfp/packet_schemas/`. Each schema enforces content-addressing and immutability:

| Schema Name | Version Marker | Description |
|---|---|---|
| `packet_envelope_v2` | `omega.symbol-game.packet-envelope.v2` | Root content-addressed envelope wrapping LLM turns or code change proposals with SHA-256 digests. |
| `llm_turn_v1` | `omega.symbol-game.llm-turn.v1` | Model turn payload recording prompts, outputs, token metrics, and finish reasons. |
| `code_change_proposal_v1` | `omega.symbol-game.code-change-proposal.v1` | Candidate patch payload containing unified diffs and target file references. |
| `prompt_artifact_v1` | `omega.symbol-game.prompt-artifact.v1` | Compiled prompt specification including objectives, demands, and constraints. |
| `candidate_artifact_v1` | `omega.symbol-game.candidate-artifact.v1` | Untrusted candidate deliverable submitted for evaluation. |
| `coboundary_score_v1` | `omega.symbol-game.coboundary-score.v1` | Exact rational string representation (`"p/q"`) of coboundary metrics; floats rejected. |
| `elimination_receipt_v1` | `omega.symbol-game.elimination-receipt.v1` | Verifiable cryptographic proof that an identified obstruction was contractively eliminated. |
| `evaluation_receipt_v1` | `omega.symbol-game.evaluation-receipt.v1` | Sovereign host evaluation outcome recording rule evaluations and metric transitions. |
| `kill_condition_refusal_map_v1` | — | Closed dictionary mapping kill conditions to typed host refusals and obstruction families. |

### Elimination & Evaluation Receipts
- Receipts carry the immutable signature of the evaluating host, input packet digests, metric deltas, and the explicit assertion:
  ```json
  "authority_effect": "None"
  ```
- Receipts never confer administrative rights; they serve solely as re-playable audit evidence.

---

## 5. Native FFI Bridge (`omega_engine_pfp/ffi.py`)

The Foreign Function Interface bridge enables the Python application layer to invoke native Rust operations executed by the compiled `omega_symbol_game` binary.

### 5.1 Seam Isolation Architecture
In accordance with `RULE_FFI_SEAM_ISOLATION_001`, `ffi.py` does not implement custom binary path searching or process management. Instead, it delegates exclusively to the Omega Engine Operating System (OEOS) native host adapter:
- `find_omega_symbol_game_binary()` queries `omega_engine_operating_system.adapters.rust_host.ffi.locate_host_binary()`.
- Supports the `OMEGA_SYMBOL_GAME_HOST` environment variable for external binary overrides.
- Translates OEOS typed refusals into standard boundary exceptions while preserving failure codes and diagnostic messages.

### 5.2 `RustSymbolGameHost` Implementation
`RustSymbolGameHost` acts as the primary dispatch client. All methods return monadic `Result[Mapping[str, Any], Refusal]` objects:

```python
class RustSymbolGameHost:
    def __init__(self, binary_path: str | Path | None = None) -> None:
        ...
        self._host = native_host.RustSymbolGameHost(
            binary=self._binary_path, timeout_seconds=30
        )

    def invoke_runtime(self, action: str, payload: Any) -> Result[Mapping[str, Any], Refusal]:
        return self._host.invoke_runtime(action, payload)
```

### 5.3 Supported Native Action Domains
Via `invoke_runtime`, `RustSymbolGameHost` executes operations across eight native domains:
1. **Wire Codecs:** `canonical_wire`, `canonical_unwire`, `canonical_json`, `canonical_bytes_hex`, `domain_digest`.
2. **Patch Handling:** `parse_unified_diff`, `create_code_change_proposal`, `submit_patch_candidate`, `evaluate_patch_gates`.
3. **Exact Linear Algebra:** `exact_determinant`, `exact_is_positive_definite`, `exact_ldlt`, `exact_rank`, `exact_leading_minors`, `exact_char_poly`.
4. **Simplicial Topology:** `exact_verify_boundary_closed`, `exact_verify_simplicial_boundary_law`, `exact_ordered_loop_product`, `exact_is_ordered_closure`.
5. **Certified Solvers:** `verify_l1_certificate`, `exact_solve_l1_primal_dual`, `functional_evaluate`, `functional_verify`.
6. **DDC State & Prime Traversal:** `ddc_verify_tape`, `prime_admit`, `prime_replay_decide`, `prime_descent`, `lggr_classify`, `lggr_soundness`.
7. **Immune & Pharmacy:** `pharmacy_detect`, `evaluate_prompt_cochain`.
8. **Formal Verification:** `lean_scan_sources`, `lean_audit_report`, `stabilizer_solve`, `stabilizer_check`.

---

## 6. Verification and Audit Invariants

1. **Zero Authority:** No call, envelope, receipt, or CLI flag across `omega_engine_pfp` may emit or claim elevated authority (`AuthorityEffect: None` is mandatory).
2. **Zero Float Contamination:** Core mathematical evaluations, cochain scoring, price calculations, and wire digests strictly forbid IEEE-754 floating-point numbers, requiring exact rationals or integers.
3. **Deterministic Replay:** Replay execution paths must operate exclusively from stored payload digests and raw reply strings without network access.
