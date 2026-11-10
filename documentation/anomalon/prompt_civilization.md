# Prompt Civilization & Evolution: `omega_prompt_civilization`

**AuthorityEffect:** None  
**Status:** Code-Grounded Reference Documentation  
**Repository Path:** `c:\Users\a343o\source\repos\anomalon\omega_engine\crates_rs\omega_prompt_civilization`  
**Governing Standard:** Prompt Family Graphs, Lamarckian Cochains, Exact PageRank, and Anti-Skill Pharmacy  

---

## 1. Architectural Role and Scope

`omega_prompt_civilization` models the evolution, genealogy, society structure, and metabolic selection of prompts within the Anomalon architecture, while housing the anti-skill pharmacy. Rather than treating prompts as ephemeral strings, this subsystem models prompts as nodes in a typed, content-addressed directed acyclic graph (DAG) called a **Prompt Family**.

The crate enforces two foundational structural principles:
1. **Reader-Relativity:** Prompts are interpreted relative to specific model readers and evaluation seats; performance metrics cannot be abstracted from the evaluating reader.
2. **Separation of Detection from Repair:** Defect detection identifies what is wrong without proposing or laundering a fix.

Every struct, serialization schema, and evaluation receipt emits `AuthorityEffect: None`.

---

## 2. Prompt Family Graph Schema (`src/prompt_family.rs`)

The `PromptFamily` is the formal data structure tracking prompt lineage, nested containment, execution calls, and discrete deformation steps:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PromptFamily {
    pub readers: Vec<Reader>,
    pub nodes: Vec<PromptNode>,
    pub calls: Vec<CallRecord>,
    pub steps: Vec<RepairStep>,
    pub terminal: Option<Terminal>,
}
```

### 2.1 Graph Components and Data Invariants

#### `PromptNode`
Represents an immutable, content-addressed prompt snapshot:
- `prompt_digest`: SHA-256 hash of the exact prompt content (`sha256:...`).
- `relation`: Declares the structural relationship to its parent:
  - `"root"`: Top-level seed prompt.
  - `"contains"`: Sub-prompt nested inside a parent prompt.
  - `"repaired_from"`: Evolutionarily derived prompt produced by repairing a parent prompt.
- `parent_id`: Node ID of the parent prompt node (`None` for root).
- `reader_digest`: Digest of the `Reader` model evaluating this prompt.
- `shape`: Geometric structural profiling:
  - `byte_bucket`: Logarithmic byte length bucket ($\lfloor \log_2(\text{bytes}) \rfloor$).
  - `line_bucket`: Logarithmic line count bucket.
  - `fence_count`: Count of triple-backtick markdown fences (```).
  - `question_count`: Count of interrogation marks (`?`).
- `domain_labels`: Categorical domain hierarchy tracking (`Vec<DomainLabel>`).
- `node_id()`: Computed deterministically as the canonical digest of `[prompt_digest, relation, parent_id, reader_digest]`.

#### `Reader`
Captures model configuration and evaluation parameters:
- `model`: Identifier string (e.g., `"claude-sonnet-5-5"`).
- `router`: Routing gateway (e.g., `"openrouter"`).
- `seat_id`: Evaluator seat (e.g., `"producer (Begemot)"`).
- `tier`: Quality/cost tier.
- `config_digest`: Hash of model hyperparameters.
- `temperature`, `params_billion`, `open_weights`: Execution parameters.

#### `CallRecord`
Captures an individual language model turn invocation:
- `bout_id`: Retraction tournament or session ID.
- `request_digest`, `reply_digest`: Hashes of request and response payloads.
- `reader_digest`: Hash of the evaluating reader.
- `leg_index`: Turn sequence index within the bout.
- `outcome`: Execution outcome (`"OK"` or specific defect code).
- `cost_microusd`: Integer micro-USD cost (e.g., `1500` for \$0.0015).
- `input_tokens`, `output_tokens`: Token consumption metrics.
- `ddc_letter`: Discrete Deformation Calculus transition letter (e.g., `"E"`, `"R"`, `"C"`).
- `residual_colour`: Active obstruction color (`"RED"`, `"BLUE"`).

#### `RepairStep`
Binds an evolutionary deformation step between two prompt nodes:
- `input_node_id`, `output_node_id`: Edge connecting parent to repaired prompt.
- `ddc_letter`: Lawful DDC operator assigned to the transition.
- `residual_before`, `residual_after`: Obstruction norms before and after repair.
- `call_ids`: Trace of call records that produced the repair.
- `fitness`: Multi-objective outcome (`Fitness`):
  - `cost_microusd`: Cumulative cost of the step.
  - `input_tokens`, `output_tokens`: Total token footprint.
  - `checker_verdict`: Sovereign verdict from independent checker oracles.
  - `obstruction_removed`: Boolean flag indicating whether the target obstruction was contractively eliminated.

#### `DomainLabel`
Tracks domain and subdomain categorization:
- `label`: Hierarchical path (e.g., `"math.homological.duality"`).
- `proposer_reader`: Hash of the reader proposing the classification.
- `status`: Lifecycle status (`"proposed"` or `"checked"`).
- `check_receipt`: Cryptographic receipt from an independent checker validating applicability.

---

## 3. Ingestion, Nesting, and Evolutionary Lineage

The lifecycle of prompts through the prompt sieve follows structured graph transitions:

```
                  [Raw Seed Prompt Ingested]
                              │
                              ▼
           ┌─────────────────────────────────────┐
           │        Root PromptNode              │
           │  (relation: "root", parent_id: None) │
           └──────────────────┬──────────────────┘
                              │
             Contains Nested  │  Prompt Sieve Parser
             Prompts / Tasks  ▼
           ┌─────────────────────────────────────┐
           │        Child PromptNode             │
           │ (relation: "contains", parent: root)│
           └──────────────────┬──────────────────┘
                              │
             Obstruction      │  DDC Repair Operator
             Elimination      ▼  (Transition E, R, ...)
           ┌─────────────────────────────────────┐
           │        Repaired PromptNode          │
           │  (relation: "repaired_from", ...)   │
           └──────────────────┬──────────────────┘
                              │
                              ▼
           ┌─────────────────────────────────────┐
           │            RepairStep               │
           │  (Residual Delta, Fitness Record)   │
           └─────────────────────────────────────┘
```

1. **Seed Ingestion:** A raw prompt string is sanitized and ingested via `forge.rs`. It is encapsulated in a `PromptNode` with `relation: "root"` and `parent_id: None`.
2. **Nested Prompts ("Prompts Containing Prompts"):** Prompts containing embedded task prompts, system templates, or sub-agent instructions are decomposed into child `PromptNode`s with `relation: "contains"`. The parent ID explicitly points to the enclosing prompt, preserving compositional nesting without text concatenation.
3. **Evolutionary Repair Lineages:** When a prompt generates an obstruction or triggers an anti-skill finding, a repair operator applies a localized edit. The resulting prompt is added as a child `PromptNode` with `relation: "repaired_from"`. A corresponding `RepairStep` records the exact residual reduction, token expenditure, and checker verdict.

---

## 4. Mathematical Selection & Fitness Tracking

`omega_prompt_civilization` avoids heuristic or ungrounded fitness scores, relying on exact rational algebra:

### 4.1 Lamarckian Cochain Tracking (`src/lamarckian.rs`)
Tracks cochain histories across successive retraction turns:
- `LamarckianCochainTrackerV1` and `CochainResidualV1` record the boundary defect norm ($\Phi_1$) and curvature ($\Gamma_2$) across turns.
- Prompts that achieve strict descent in obstruction norms are rewarded in metabolic selection; mutations that increase obstruction are culled.

### 4.2 Exact Rational PageRank (`src/rank.rs`)
Computes graph centrality and prompt influence over the prompt family DAG:
- `ExactPageRankSolverV1` formulates the transition matrix over the field of exact rational numbers $\mathbb{Q}$ using `num_rational::BigRational`.
- Computes exact rational stationary distributions:
  $$p = (1 - d) \frac{\mathbf{1}}{N} + d M p$$
- Ensures zero floating-point drift or convergence ambiguity under declared rational arithmetic assumptions.

### 4.3 Pareto Fitness Frontier (`src/fitness.rs`)
Evaluates multi-objective fitness tradeoffs:
- Objectives: cost (micro-USD), token economy (input + output tokens), and checker accuracy.
- `compute_pareto_fronts_rational()` computes non-dominated Pareto frontiers over exact rational coordinates, identifying Pareto-optimal prompts without arbitrary scalar weighting.

### 4.4 Prompt Societies and Metabolism (`src/society.rs`, `src/metabolism.rs`)
Organizes prompts into societies (`PromptCivilizationV1`, `PromptSocietyV1`) subject to environmental token budgets and metabolic culling:
- Prompts with low PageRank and dominated Pareto fitness are pruned to prevent memory and state bloat.

---

## 5. The Anti-Skill Pharmacy (`src/pharmacy.rs`)

The anti-skill pharmacy provides a deterministic engine for detecting reasoning defects, structural anti-patterns, and authority masquerading in candidate packets.

### 5.1 The Two Foundational Pharmacy Rules
1. **Detection is Separate from Repair:** A `Finding` names what is wrong and nothing else. No detector returns a patched packet, and there is no field for one. Coupling detection with repair allows a detector to launder its own unverified fix past host review.
2. **"Passing Fixtures Demonstrates Only That":** Directly quoting the module rule in `src/pharmacy.rs`, a clean `DetectorReport` is evidence only that named detectors found no matches on named bytes. It never implies that a candidate is correct, and a clean report is not an admission.

### 5.2 The 12 Experimental Failure Classes
The pharmacy implements deterministic checks for 12 failure classes mined from empirical failure corpora:

| Failure Class | Code | Routing Disposition | Semantic Description |
|---|---|---|---|
| `SelfCertification` | `SELF_CERTIFICATION` | `Refuse` | Candidate model asserting its own correctness or claiming host approval. |
| `FakeReceipt` | `FAKE_RECEIPT` | `Refuse` | Candidate populating digest or receipt fields that only the host may write. |
| `PersonaAuthorityLeak` | `PERSONA_AUTHORITY_LEAK` | `Refuse` | A roleplay persona asserting administrative or execution authority. |
| `SchemaSemanticLaundering` | `SCHEMA_SEMANTIC_LAUNDERING` | `Hold` | Syntactically valid JSON masking unperformed or nonsensical semantics. |
| `PrivateCotDependency` | `PRIVATE_COT_DEPENDENCY` | `Hold` | Conclusions asserting dependence on unrevealed scratchpad reasoning tokens. |
| `ConclusionPreload` | `CONCLUSION_PRELOAD` | `Diag` | Prompt baking the required answer into the instruction text. |
| `TheoremNameLaundering` | `THEOREM_NAME_LAUNDERING` | `Diag` | Invoking a named theorem without demonstrating or stating applicability hypotheses. |
| `OptimalityHallucination` | `OPTIMALITY_HALLUCINATION` | `Diag` | Claiming asymptotic or mathematical optimality without a loss function or bound. |
| `ComplexityHallucination` | `COMPLEXITY_HALLUCINATION` | `Diag` | Asserting algorithmic complexity classes without a cost model or measurements. |
| `BranchDropExhaustion` | `BRANCH_DROP_EXHAUSTION` | `Diag` | Claiming proof by exhaustion while omitting candidate branches. |
| `VersionDuplication` | `VERSION_DUPLICATION` | `Diag` | Submitting byte-identical payloads under incremented version labels. |
| `DetectRepairCoupling` | `DETECT_REPAIR_COUPLING` | `Diag` | Bundling a defect finding with an unverified patch payload. |

### 5.3 Routing Dispositions
A disposition is a host routing decision, not a mathematical theorem:
- **`Disposition::Refuse`:** Hard stop; rejects the packet immediately due to authority violation.
- **`Disposition::Hold`:** Pauses branch progression until required missing evidence or unredacted tokens are supplied.
- **`Disposition::Diag`:** Emits diagnostic feedback without halting the round, guiding subsequent retraction turns.

---

## 6. Defensible Claims and Boundary Summary

1. **What this code supports:**
   - Deterministic graph modeling of prompt families with explicit containment and repair relations.
   - Exact rational PageRank and multi-objective Pareto frontier computation with zero floating-point noise.
   - Formal separation between defect detection and repair proposal.
   - Elimination of self-certification and fake receipts via hard refusal dispositions.

2. **What this code does NOT support:**
   - Broad optimality of prompts (Pareto optimality is strictly relative to the finite evaluated set).
   - Automated repair synthesis (the pharmacy identifies defects; repair requires separate authorized turns).
