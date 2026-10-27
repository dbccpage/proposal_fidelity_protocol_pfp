---
documentation_contract: symbol-game-documentation/v1
title: "Symbol Game Integration with Sentinel AI"
kind: integration-specification
audience:
  - engineers
  - coding-agents
  - product-engineers
status: active
maturity: canonical
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - pfp
  - education/documentation/004_oepfp
last_verified: 2026-10-20
verification_scope: crate, module and type names checked against tracked source; the integration itself is proposed
---

# 07. Symbol Game Integration with Sentinel AI

> **Authority Boundary:** This document defines the integration surface between `symbol_game` and `sentinel_ai`. It does not claim the Symbol Game mints Core authority. Authority belongs to the validators.

> **Current-source status (2026-10-20, pin `c419cc6beb`): proposed integration.** No `sentinel_ai` crate or package is tracked: the name appears in prose and as a path string `engine/products/sentinel_ai/web/app/page.tsx` in the CI impact selector (`operations/use_cases/cicd/impacted_crates.py` lines 157 and 250), and `engine/products/` is not present. None of the endpoints `/api/v1/query`, `/api/v1/query/stream`, `/api/v1/health` or `/api/v1/feedback` is implemented in tracked Python, Rust or TypeScript. The Rust crate is `core_symbol_game` ([Cargo.toml](../../../../engine/crates_rs/core_symbol_game/Cargo.toml)), with 88 `*.rs` files under `src/` and subdirectories `bin/`, `epics/`, `foundation/`, `host/` and `invoke/`. It has no `adapters`, `policies`, `evaluators`, `solvers`, `engines`, `health` or `lifts` modules, so the file counts in "Existing Code Alignment" below are historical. A word search of tracked code found no definition of `PacketCompiler`, `RepairPayload`, `ConfidenceLabel`, `ConsecrationState`, `ImmuneSnapshot`, `ShapeRankings` or `ModelSelector`. `OperatorRegistry` exists only in the unrelated `engines` crate. `symbol_game_math_spine.md` is not present at the path this page assumes.

## 0. Design Principle

The user submits a question. The user receives an answer with a confidence label. Between those two events, the system compiles the question into constrained packets, forces the LLM to emit parseable candidates, validates them mechanically, repairs failures silently, and decodes the result. The user never sees the packet grammar.

## 1. Component Mapping

> **Note (domain-specificity is functorial at the obstruction layer, not the packet layer).** Cross-domain packetization is a domain-indexed FAMILY of Kleisli arrows {η_D^♯ : RawInput_D → TypedPacket_D ⊎ 𝔽}, NOT a single functor. Genuine functoriality lives at the obstruction functor 𝒪^• : ℕ≤5^op → CoCh (spine §III.6); a domain is made concrete by declaring its carrier cochain complex C_D^• and admissible operator families, while the 5 effect-classes (E/I/C/R/M) stay domain-invariant. See canonical math spine §III.6.

The 9 components from the product architecture (`_audit_05`) map to concrete modules:

| #   | Component               | Crate/Module                                     | Traits/Types                                           |
| :-- | :---------------------- | :----------------------------------------------- | :----------------------------------------------------- |
| 1   | User Prompt Intake      | `sentinel_ai::intake`                            | `PromptShape`,`EvidenceCeiling`,`PacketCandidate`      |
| 2   | Packet Compiler         | `symbol_game::adapters`+`symbol_game::policies`  | `PacketCompiler`,`PacketEnvelope`,`ValidatorRoute`     |
| 3   | LLM Candidate Generator | `sentinel_ai::generators`                        | `ModelSelector`,`ModelId`, HTTP/file/claude backends   |
| 4   | Validator Pipeline      | `symbol_game::evaluators`+`symbol_game::solvers` | `LocalValidator`,`BoundaryValidator`,`Terminalizer`    |
| 5   | Repair Loop             | `symbol_game::engines`+`symbol_game::health`     | `RepairPayload`,`RepairBudget`, loop detection         |
| 6   | Response Decoder        | `sentinel_ai::decoders`                          | `ConfidenceLabel`,`EvidenceScope`,`UserResponse`       |
| 7   | Operator Memory         | `symbol_game::lifts`+`symbol_game::policies`     | `OperatorEntry`,`OperatorRegistry`,`ConsecrationState` |
| 8   | Epistemic Immune System | `symbol_game::health`                            | `Antibody`,`ImmuneSnapshot`,`HardRule`                 |
| 9   | Prompt Shape Ranking    | `sentinel_ai::ranking`                           | `GraphNode`,`GraphEdge`,`ShapeRankings`                |

### Existing Code Alignment

The `symbol_game` crate (91 Rust source files) already provides:

- **Evaluators** (22 files): audit, verdict, MSS-mu, Phi analysis, transition checking
- **Solvers** (8 files): expression verification, batch certification
- **Policies** (9 files): contracts, evidence, governance, licensing
- **Lifts** (9 files): lift licensing, cost models, stage-3 review
- **Health** (6 files): quarantine, red flags, structural issues
- **Certificates** (3 files): certificate and refusal types
- **Engines** (4 files): markdown rendering, API, reports

The `sentinel_ai`product has a Next.js web app and a`.docs/src_proposal` Rust skeleton with certificates, policies, replay, terminalizers, types, validators, and witness modules.

## 2. API Surface

### 2.1 HTTP Endpoints

```text
POST /api/v1/query
  Request:  { prompt: string, domain_hint?: string, evidence_ceiling?: string }
  Response: { answer: string, confidence: ConfidenceLabel, evidence_scope: EvidenceScope, caveats: string[] }

POST /api/v1/query/stream
  Request:  same as /query
  Response: Server-Sent Events with intermediate status updates

GET  /api/v1/health
  Response: { status: "ok"|"degraded", validators_active: number, operators_registered: number }

POST /api/v1/feedback
  Request:  { query_id: string, rating: "good"|"bad"|"wrong", details?: string }
  Response: { acknowledged: true }

```

### 2.2 Request/Response Schema

```rust
pub struct QueryRequest {
    pub prompt: String,
    pub domain_hint: Option<DomainId>,
    pub evidence_ceiling: Option<EvidenceCeiling>,
    pub session_id: Option<SessionId>,
}

pub struct QueryResponse {
    pub query_id: QueryId,
    pub answer: String,
    pub confidence: ConfidenceLabel,
    pub evidence_scope: EvidenceScope,
    pub caveats: Vec<String>,
    pub latency_ms: u64,
}

```

### 2.3 Authentication

- API key authentication via `Authorization: Bearer``<key>`` header
- Rate limiting per API key (default: 60 queries/minute)
- User tier determines evidence ceiling caps and repair budget

## 3. Packet Routing

### 3.1 PromptShape Classification

The intake component classifies the user prompt into a shape that determines which packet families are viable:

```rust
pub enum PromptShape {
    FactualLookup,        // → JsonSchema packet
    CodeRewrite,          // → CodeRewriteAst packet
    MathProof,            // → DslCertificateTrace or Sequent packet
    Optimization,         // → LpPrimalDual packet
    Classification,       // → OperatorClassification packet
    CreativeGeneration,   // → minimal validation, ShapeOnly ceiling
    DiagnosticQuery,      // → CochainObstruction packet
    MultiStep,            // → pipeline of multiple packet families
    Ambiguous,            // → prompt clarification before compilation
}

```

### 3.2 Family Selection

The Packet Compiler selects families based on:

1. **PromptShape** → candidate families (hard mapping)
2. **Prompt Shape Ranking** → historical performance per shape+family pair
3. **Operator Memory** → available operators for this domain
4. **Epistemic Immune System** → suppressed patterns to avoid

Selection produces a ranked `Vec``<PacketCandidate>`` with confidence scores.

## 4. Operator Memory Integration

### 4.1 Storage

Operators are stored in PostgreSQL (the existing `DATABASE_URL` connection):

```sql
CREATE TABLE operator_registry (
    operator_id UUID PRIMARY KEY,
    operator_class TEXT NOT NULL CHECK (operator_class IN ('E','I','C','R')),
    domain_id TEXT NOT NULL,
    admitted_at TIMESTAMPTZ NOT NULL,
    usage_count BIGINT DEFAULT 0,
    success_count BIGINT DEFAULT 0,
    failure_count BIGINT DEFAULT 0,
    reliability_score DOUBLE PRECISION DEFAULT 1.0,
    consecration_state TEXT DEFAULT 'Candidate',
    last_used TIMESTAMPTZ
);

```

### 4.2 Retrieval and Composition

When the Packet Compiler builds a packet, it queries the registry for operators matching the domain and class:

```rust
impl OperatorRegistry {
    fn get_by_domain_class(&self, domain: &DomainId, class: OperatorClass) -> Vec<OperatorEntry>;
    fn get_consecrated(&self, domain: &DomainId) -> Vec<OperatorEntry>;
    fn compose(&self, op1: &OperatorEntry, op2: &OperatorEntry) -> Option<OperatorEntry>;
}

```

Composition follows the rewrite table from `symbol_game_math_spine.md` §6.7. The composed operator is registered as a new entry if its compressed form is novel.

### 4.3 Decay

Decay runs as a batch job (hourly):

- Time decay: `reliability *= 0.99^days_inactive`
- Failure penalty: `reliability -= 1/(usage_count + 1)` per failure
- Quarantine at `reliability < 0.3`
- Consecrated operators have reliability floor of 0.5

Worked example of the proposed rule (arithmetic only; no implementation exists). Start at `reliability = 1.0`:

| Event | Computation | Reliability |
| --- | --- | --- |
| 30 days inactive | `1.0 * 0.99^30` | 0.7397 (to 4 places) |
| then one failure at `usage_count = 9` | `0.7397 - 1/(9 + 1)` | 0.6397 |
| inactivity alone, from 1.0 | smallest `d` with `0.99^d < 0.3` is `d = 120` | 0.2994, so quarantine after 120 idle days |

Two design gaps follow. First, `reliability_score DOUBLE PRECISION` and the decimal factors are binary floating point, while PFP host metrics are exact rationals ([10](10_functional_metric_ownership.md)); an implementation should state whether this score is a ranking heuristic outside the exact core. Second, "quarantine below 0.3" and "floor 0.5" together mean a consecrated operator can never reach quarantine through decay alone.

## 5. Epistemic Immune System Integration

### 5.1 Antibody Generation

Antibodies are generated automatically from validator rejections:

| Trigger                                   | Antibody Type        | Rule                                     |
| :---------------------------------------- | :------------------- | :--------------------------------------- |
| Same error code 3+ times for shape+family | Suppress             | Block this family for this shape         |
| Operator consecrated                      | Prefer               | Start with this operator for this domain |
| Operator reliability < 0.3                | Quarantine           | Isolate operator pending review          |
| User reports "wrong"                      | Suppress (candidate) | Flag for manual review                   |

### 5.2 Integration Flow

```text
Packet Compiler queries ImmuneSnapshot:
  → suppressed_patterns: skip these families/operators
  → preferred_patterns: prioritize these families/operators
  → quarantined_operators: exclude from composition
  → hard_rules: apply blocking rules before compilation

```

## 6. Prompt Shape Ranking

### 6.1 Graph Structure

The ranking graph has nodes for prompt shapes, packet families, operators, obstruction types, and terminal statuses. Edges record resolution events with weights.

```text
PromptShape --[Produces]--> ObstructionType
ObstructionType --[RepairedBy]--> RepairStrategy
RepairStrategy --[Uses]--> Operator
Operator --[ValidatedBy]--> Validator
ResponseShape --[LeadsTo]--> TerminalStatus

```

### 6.2 Routing Table

Graph centrality (inverse PageRank) is computed hourly as a batch job. The result is a cached routing table:

```rust
pub struct RoutingTable {
    pub shape_to_families: BTreeMap<PromptShape, Vec<(PacketKind, f64)>>,
    pub family_to_operators: BTreeMap<PacketKind, Vec<(OperatorId, f64)>>,
    pub computed_at: Timestamp,
}

```

Per-request queries hit the cached table, not the graph directly.

## 7. Confidence Labeling

The Response Decoder maps terminal status and authority ceiling to user-facing labels:

| TerminalStatus     | AuthorityCeiling | ConfidenceLabel |
| :----------------- | :--------------- | :-------------- |
| Certificate        | BoundaryChecked  | Verified        |
| Certificate        | LocalReplay      | Verified        |
| Certificate        | ShapeOnly        | HighConfidence  |
| Repair (succeeded) | any              | BestEffort      |
| Refusal            | any              | Refused         |
| OracleNeeded       | any              | CannotVerify    |
| Budget exhausted   | any              | LowConfidence   |

The user sees: answer text, confidence label, evidence scope (what was/was not checked), and caveats.

## 8. Latency Budget

| Component                      | Budget   | Notes                          |
| :----------------------------- | :------- | :----------------------------- |
| Prompt Intake + Classification | 500ms    | Local computation              |
| Packet Compilation             | 200ms    | Registry query + compilation   |
| LLM Generation                 | 10-15s   | Dominant cost                  |
| Validator Pipeline (8 stages)  | 2-5s     | Depends on packet family       |
| Repair Loop (per iteration)    | 5s       | LLM re-generation + validation |
| Response Decoding              | 100ms    | Stateless mapping              |
| **Total (no repair)**          | **~18s** | Within 30s budget              |
| **Total (1 repair)**           | **~23s** | Within 30s budget              |
| **Total (2 repairs)**          | **~28s** | At budget limit                |

Max repair iterations default to 2 to stay within the 30s latency ceiling.

## 9. Deployment Topology

```text
┌─────────────────────────────────────────┐
│  sentinel_ai (Next.js web app)          │
│  ├─ /api/v1/query  → API routes        │
│  ├─ /api/v1/health → health check      │
│  └─ Web UI (chat interface)             │
└──────────────┬──────────────────────────┘
               │ HTTP/gRPC
┌──────────────▼──────────────────────────┐
│  symbol_game (Rust crate, via PyO3)     │
│  ├─ Packet Compiler                     │
│  ├─ Validator Pipeline                  │
│  ├─ Repair Loop                         │
│  ├─ Operator Memory (PostgreSQL)        │
│  └─ Epistemic Immune System             │
└──────────────┬──────────────────────────┘
               │ HTTP (OpenAI-compatible)
┌──────────────▼──────────────────────────┐
│  LLM Backends                           │
│  ├─ Claude (Anthropic API)              │
│  ├─ DeepSeek (OpenAI-compatible)        │
│  ├─ Gemini (Google API)                 │
│  ├─ Local models (Ollama/vLLM)          │
│  └─ File backend (deterministic tests)  │
└─────────────────────────────────────────┘
               │ SQL
┌──────────────▼──────────────────────────┐
│  PostgreSQL                             │
│  ├─ operator_registry                   │
│  ├─ antibody_map                        │
│  ├─ ranking_graph                       │
│  └─ audit_trail                         │
└─────────────────────────────────────────┘

```

### Integration Bridge

The `symbol_game`Rust crate is compiled as a PyO3 extension module (`core_core`). The sentinel_ai Next.js app calls it via:

1. **Direct Python import** from API routes (via `core_core` PyO3 module)
2. **HTTP service** if deployed as a standalone validator service

The `SYMGAME_LLM_ENDPOINT`,`SYMGAME_LLM_MODEL`, and`SYMGAME_LLM_KEY`environment variables configure the LLM backend. The file backend (`--backend file`) enables deterministic testing without LLM API calls.
