# Reader-Relative Prompt Families, Lineage DAGs, and Domain Scoping

**Domain:** Proposal Fidelity Protocol (PFP) Prompt Civilization & Lineage Engine  
**Authority Posture:** `AuthorityEffect: None`  
**Claim Hygiene Standard:** Ground Truth Discipline; exact data schemas; anti-circular verification.

---

## 1. Relational Foundations: Prompts as Reader-Relative Problems

In classical generative workflows, a prompt is often conceptualized as a static, sovereign string that yields a single output. In the Proposal Fidelity Protocol (PFP), a prompt is formalized under two relational principles:
1. **Reader Relativity:** A prompt text does not exist in isolation. Its interpretation, tokenization, and failure modes are relative to a specific **`Reader`** (the model, router, temperature, parameter scale, and sampling configuration). The same UTF-8 byte sequence presented to two different readers constitutes two distinct **`PromptNode`**s in the civilization DAG.
2. **Evolutionary Problem to Repair:** A prompt family is a directed acyclic graph (DAG) tracing how an initial stimulus evolves under successive Discrete Deformation Calculus (DDC) repair steps when confronted with host test failures.

Failures are first-class data: every failed generative bout, malformed schema response, or budget exhaustion is permanently recorded in the family ledger.

---

## 2. Prompt Family DAG Data Structure

The prompt family architecture is implemented with exact parity in Rust (`code/rust/core_prompt_civilization/src/prompt_family.rs`) and Python (`ops/adversary/domain/prompt_family.py`).

```rust
pub struct PromptFamily {
    pub readers: Vec<Reader>,
    pub nodes: Vec<PromptNode>,
    pub calls: Vec<CallRecord>,
    pub steps: Vec<RepairStep>,
    pub terminal: Option<Terminal>,
}
```

```
                     ┌────────────────────────────────────────┐
                     │          PromptFamily (DAG)            │
                     └───────────────────┬────────────────────┘
                                         │
        ┌───────────────────┬────────────┴───────┬────────────────────┐
        ▼                   ▼                    ▼                    ▼
   [Readers]             [Nodes]              [Calls]              [Steps]
 Model, config,      Prompt digests,      Bout records,        DDC repair edges,
 sampling params     relations, shapes    tokens, costs        fitness, verdicts
```

### 2.1 `Reader`: The Observing Environment
```rust
pub struct Reader {
    pub model: String,
    pub router: String,
    pub seat_id: String,
    pub tier: String,
    pub config_digest: String,
    pub temperature: Option<String>,
    pub params_billion: Option<serde_json::Number>,
    pub open_weights: Option<bool>,
}
```
- **Digest Computation:** `reader.digest()` produces a canonical SHA-256 digest over sorted JSON keys.
- **Honesty Rule:** Unknown attributes stay `None`. Nothing is backfilled or inferred on a model provider's behalf.

### 2.2 `PromptNode`: The Relational Vertex
```rust
pub struct PromptNode {
    pub prompt_digest: String,
    pub relation: String, // "root" | "contains" | "repaired_from"
    pub shape: Option<Shape>,
    pub parent_id: Option<String>,
    pub reader_digest: Option<String>,
    pub domain_labels: Vec<DomainLabel>,
}
```
- **Node ID Calculation:**
  $$\text{node\_id} = \text{SHA256}([\text{prompt\_digest}, \text{relation}, \text{parent\_id}, \text{reader\_digest}])$$
- **Domain Labels:** Carry `{ label, proposer_reader, status: "proposed" | "checked", check_receipt }`. A domain label remains `"proposed"` until confirmed by an independent external check receipt.

### 2.3 `CallRecord`: Generative Telemetry
```rust
pub struct CallRecord {
    pub bout_id: String,
    pub request_digest: String,
    pub reader_digest: String,
    pub leg_index: i64,
    pub outcome: String,
    pub cost_microusd: Value,
    pub cost_source: Option<String>,
    pub input_tokens: Option<serde_json::Number>,
    pub output_tokens: Option<serde_json::Number>,
    pub max_tokens: Option<serde_json::Number>,
    pub finish_reason: Option<String>,
    pub ddc_letter: Option<String>,
    pub residual_colour: Option<String>,
    pub reply_digest: Option<String>,
}
```
- **Defect Attribution:** An outcome other than `"OK"` records the defect name (`defect()`). Failed generative calls are indexed directly into the cochain history.

### 2.4 `RepairStep`: The DDC Edge
```rust
pub struct RepairStep {
    pub input_node_id: String,
    pub output_node_id: String,
    pub ddc_letter: Option<String>,
    pub residual_before: Option<String>, // "Open" | "Closed" | "Exact"
    pub residual_after: Option<String>,  // "Open" | "Closed" | "Exact"
    pub call_ids: Vec<String>,
    pub fitness: Fitness,
}
```

### 2.5 `Fitness`: Objective Measurement Vector
```rust
pub struct Fitness {
    pub cost_microusd: Value,
    pub input_tokens: Value,
    pub output_tokens: Value,
    pub checker_verdict: String, // "ACCEPT" | "REJECT" | "NOT_MEASURED"
    pub checker_id: Option<String>,
    pub obstruction_removed: Option<bool>,
}
```

### 2.6 `Terminal`: The Sealed Trajectory Status
```rust
pub struct Terminal {
    pub kind: String,   // "Repaired" | "BudgetExhausted" | "TypedResidual"
    pub detail: String, // Must be specific: e.g. "Exact" or "BUDGET_WALL_CLOCK_LIMIT"
}
```

---

## 3. Constitutional Invariants Enforced by `validate_family`

The validation engine in `core_prompt_civilization::prompt_family::validate_family()` strictly enforces the following topological and integrity invariants:

### 3.1 Single Root & Parent Integrity
- **`FAMILY_ROOT_COUNT`:** A family must contain exactly one root node (`relation == "root"`). Multiple roots or zero roots are refused.
- **`FAMILY_ROOT_PARENT`:** Exactly the root node has `parent_id == None`. Every non-root node (`"contains"` or `"repaired_from"`) **must** declare a parent.
- **`FAMILY_NODE_DUPLICATE`:** Node identifiers must be strictly unique within the family.

### 3.2 Strict Acyclicity (`validate_parent_chain`)
- The validator traverses `parent_id` links from every node upward to the root. If any node identifier is encountered twice, validation fails immediately with `FAMILY_CYCLE`.
- Missing parent references raise `FAMILY_PARENT_MISSING`.

### 3.3 Anti-Circularity Rule (`FAMILY_FITNESS_CIRCULAR`)
To eliminate model self-certification:
```rust
if fit.checker_verdict != "NOT_MEASURED" {
    let checker = fit.checker_id.as_ref().filter(|c| !c.is_empty())
        .ok_or_else(|| refuse("FAMILY_CHECKER_MISSING", "a verdict needs a checker id"))?;
    if step_readers.contains(checker) {
        return Err(refuse(
            "FAMILY_FITNESS_CIRCULAR",
            "the checker is one of the step's own readers",
        ));
    }
}
```
A model environment that participated as a reader in a repair step cannot act as the evaluator for that step. Fitness verification must come from an independent host checker or distinct reader seat.

### 3.4 Terminal Repair Integrity
- **`FAMILY_REPAIRED_UNSUPPORTED`:** A family cannot terminate with status `"Repaired"` unless the final repair step has:
  1. `fitness.checker_verdict == "ACCEPT"`
  2. `residual_after == "Exact"`
- **`FAMILY_TERMINAL_DETAIL`:** A terminal of kind `"BudgetExhausted"` must supply a detail code prefixed with `"BUDGET_"`.

---

## 4. Domain Scoping and Prefix Covering

Prompt families are classified into hierarchical domains governed by `code/rust/core_prompt_civilization/src/domain.rs`:

```rust
pub struct DomainPlacementV1 {
    pub placement_id: String,
    pub content_digest: String,
    pub domain_assignment: String,
    pub read_scope: Vec<String>,
    pub disposition: String,
}
```

### 4.1 The Scope Covering Algorithm (`scope_covers`)
Domain hierarchies (domain, subdomain, sub-subdomain) are evaluated via prefix globbing:
```rust
pub(crate) fn scope_covers(scope: &str, target: &str) -> bool {
    if scope == "*" || scope == target {
        return true;
    }
    let Some(stem) = scope.strip_suffix(".*") else {
        return false;
    };
    !stem.is_empty() && (target == stem || target.starts_with(&format!("{stem}.")))
}
```

#### Hierarchy Examples:
- Scope `*`: Matches every target domain.
- Scope `math.*`: Covers `math.algebra`, `math.algebra.cochains`, and `math.analysis`.
- Scope `math.algebra`: Matches exact domain only; does not cover `math.analysis`.

### 4.2 Hard Eligibility Invariant (`F-DOMAIN-01`)
Taxonomy recognition alone never grants admission:
```rust
pub fn hard_domain_eligible(placement: &DomainPlacementV1, query_domain: &str) -> bool {
    placement.disposition == "ADMITTED_LOCAL"
        && placement.read_scope.iter().any(|scope| scope_covers(scope, query_domain))
}
```
A prompt or artifact is eligible for execution in a domain **only** if its placement disposition is explicitly `"ADMITTED_LOCAL"` and the target domain is covered by its declared `read_scope`.

---

## 5. Lineage Tracking & Inheritance Fences

Multi-parent inheritance across prompt generations is governed by `code/rust/core_prompt_civilization/src/genealogy.rs`:

```rust
pub struct InheritanceEdgeV1 {
    pub parent_id: String,
    pub child_id: String,
    pub relationship: InheritanceRelationship, // DirectMutation | Repair | Retry
    pub witness_receipt_digest: String,
}
```

### Constitutional Lineage Fences:
1. **`F-LINEAGE-01` (Witnessed Causal Relation):** Edges exist **only** for witnessed causal relations. Matching objectives, textual similarity, or semantic embeddings alone can never create an inheritance edge.
2. **Cryptographic Witness Receipt:** Every inheritance edge must bind a valid SHA-256 witness receipt digest. Constant strings (e.g. `"sha256:causal_witness_ok"` or `"unverified"`) are refused outright.
3. **Bounded Depth (`max_depth <= 5`):** Multi-parent graph traversal is strictly bounded. Any traversal requesting depth $> 5$ raises `GenealogyError::DepthBoundExceeded`.
4. **Descent Follows Inheritance (`F-PHARM-04`):** Immune memory and defect tracking descend strictly along declared inheritance edges.

---

## 6. How Prompt Shapes Inform Downstream Operators

Syntactic prompt structure is captured through the `Shape` value object (`code/rust/core_prompt_civilization/src/prompt_family.rs`, lines 80–98):

```rust
pub struct Shape {
    pub byte_bucket: u32,
    pub line_bucket: u32,
    pub fence_count: usize,
    pub question_count: usize,
}

impl Shape {
    pub fn from_text(text: &str) -> Self {
        Self {
            byte_bucket: usize::BITS - text.len().leading_zeros(),
            line_bucket: usize::BITS - (text.matches('\n').count() + 1).leading_zeros(),
            fence_count: text.matches("```").count(),
            question_count: text.matches('?').count(),
        }
    }
}
```

### Downstream Operator Selection
The syntactic shape provides deterministic, lightweight metrics that guide which DDC and operad operators are scheduled next:

| Shape Characteristic | Metric Threshold | Inferred Operational Requirement | Scheduled Next Operator |
|---|---|---|---|
| **Large Text Size** | `byte_bucket >= 16` ($> 64$ KiB) | Large monolithic stimulus risking context truncation. | Context exposure (`C`) and prompt decomposition into sub-prompts. |
| **Deep Multiline Structure** | `line_bucket >= 10` ($> 1024$ lines) | Complex structural prose or multiline scripts. | Planar operad tree parsing (`OperadTreeNode`, `LeafTextSpan`). |
| **High Code Fence Density** | `fence_count >= 4` | Embedded scripts, diffs, or code blocks present. | Code repair stage machine (`ddc_code_repair_v1.py`) and AST lint operators (`sfh.scan`). |
| **High Question Density** | `question_count >= 5` | Interrogative ambiguity or multi-part prompt queries. | Interrogative morphism ($O^-$) or slot-filling workflow (`wf0002_full_slots`). |
| **Zero Code Fences** | `fence_count == 0` | Pure prose or mathematical premise. | Claim hygiene linter (`glossa.scan_hype_prose`) and formal proof gates. |

---

## 7. Claim Hygiene Analysis

### 1. What Prompt Families Support:
- Demonstrates a reader-relative DAG tracking prompt modifications, token costs, and DDC repair steps.
- Formally prevents self-certification by enforcing anti-circular fitness (`FAMILY_FITNESS_CIRCULAR`).
- Restricts lineage inheritance to witnessed causal events bounded to `max_depth <= 5`.
- Provides deterministic domain scope matching (`scope_covers`) and syntactic shape classification.

### 2. What Prompt Families Do Not Support:
- Does not demonstrate that tracking prompt lineage ensures optimal prompt convergence.
- Does not show that syntactic shapes reveal semantic model comprehension.
- Does not confer operational authority to generated prompt descendants.

### 3. The Narrowest Defensible Claim:
The PFP prompt civilization engine provides a deterministic, reader-relative DAG and domain-scoping harness that records prompt mutations, enforces anti-circular verification, and indexes failures under `AuthorityEffect: None`.

### 4. The Next Test Needed:
Automated test injection of a circular reader check (where `checker_id == step.call.reader_digest`) to verify that the family validation pipeline consistently raises `FAMILY_FITNESS_CIRCULAR`.
