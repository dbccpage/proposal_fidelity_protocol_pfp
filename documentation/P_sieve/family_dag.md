# Prompt Sieve: Prompt Family Directed Acyclic Graphs (DAG)

**AuthorityEffect:** None  
**Module Reference:** `code/rust/core_prompt_civilization/src/prompt_family.rs`  
**Schema Mirror:** `ops/adversary/domain/prompt_family.py`  
**Status:** Implemented in Rust sovereign engine and Python adversary domain  

---

## 1. Executive Summary & Core Definitions

In standard LLM evaluation, prompts are often treated as ephemeral, disconnected string literals. In the Prompt Sieve architecture, prompts are organized into structured, content-addressed genealogy networks called **Prompt Families** (`PromptFamily`).

A prompt family tracks:
1. **Structural Containment**: When a prompt decomposes into nested sub-prompts or sub-tasks (`relation: "contains"`).
2. **Evolutionary Lineage**: When a prompt is repaired, mutated, or adapted across turns (`relation: "repaired_from"`).
3. **Reader Relativity**: Prompts have no observer-independent meaning; every prompt node is relativized to an observing model environment (`Reader`).
4. **Anti-Circularity**: An evaluating checker oracle cannot belong to the same reader set that generated the candidate step (`FAMILY_FITNESS_CIRCULAR`).
5. **Strict DAG Acyclicity**: Parent link traversal prevents circular lineages (`FAMILY_CYCLE`).

---

## 2. The `PromptFamily` Schema

Defined in `code/rust/core_prompt_civilization/src/prompt_family.rs` (lines 195–201):

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

### 2.1 Reader Relativity (`Reader`)

A text string evaluated under different model architectures, sampling temperatures, or system configurations represents distinct cognitive interfaces. Thus, each observing context is explicitly declared as a `Reader`:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
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

**Reader Digest:** The unique identity of a reader is its canonical JSON digest:
$$\text{reader\_digest} = \text{sha256}(\text{sort\_keys}(\text{Reader}))$$

### 2.2 Node Geometry & Relations (`PromptNode`)

Defined in `prompt_family.rs` (lines 109–116):

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PromptNode {
    pub prompt_digest: String,
    pub relation: String,
    pub shape: Option<Shape>,
    pub parent_id: Option<String>,
    pub reader_digest: Option<String>,
    pub domain_labels: Vec<DomainLabel>,
}
```

#### Node Identification Law
The canonical node ID is computed from a strict 4-tuple (`prompt_family.rs`, lines 118–125):
$$\text{node\_id} = \text{canonical\_digest}([\text{prompt\_digest}, \text{relation}, \text{parent\_id}, \text{reader\_digest}])$$

This ensures that identical prompt text placed in a different relational position (e.g. root vs child) or evaluated under a different reader yields distinct, content-addressed node IDs.

#### The Three Canonical Relations
The `relation` field must strictly match one of three strings (`FAMILY_RELATION`):
1. `"root"`: The original seed prompt that initiated the family.
2. `"contains"`: A sub-prompt, sub-task, or embedded clause contained within the parent prompt.
3. `"repaired_from"`: A successor prompt produced by applying a mutation operator or DDC repair transition to the parent prompt.

---

## 3. Structural Validation & Graph Invariants

Validation of a family is performed by `validate_family(&PromptFamily)` (`prompt_family.rs`, lines 475–487). It enforces six invariant rules:

### 3.1 Invariant 1: Exactly One Root (`FAMILY_ROOT_COUNT`)

A prompt family must have a single origin point:

```rust
if family.nodes.iter().filter(|n| n.relation == "root").count() != 1 {
    return Err(refuse("FAMILY_ROOT_COUNT", "a family has exactly one root"));
}
```

Families with 0 roots or multiple competing roots fail closed immediately.

### 3.2 Invariant 2: Root-Parent Duality (`FAMILY_ROOT_PARENT`)

In `validate_prompt_node` (lines 261–266):

```rust
if (node.relation == "root") != node.parent_id.is_none() {
    return Err(refuse(
        "FAMILY_ROOT_PARENT",
        "exactly the root has no parent",
    ));
}
```

- If `node.relation == "root"`, `node.parent_id` **must be `None`**.
- If `node.relation != "root"` (i.e. `"contains"` or `"repaired_from"`), `node.parent_id` **must be `Some(parent_id)`**.

### 3.3 Invariant 3: Acyclicity Enforcement (`validate_parent_chain`)

Graph acyclicity is validated by traversing parent pointers (`prompt_family.rs`, lines 283–306):

```rust
fn validate_parent_chain(
    node: &PromptNode,
    nodes: &BTreeMap<String, &PromptNode>,
) -> Result<(), Refusal> {
    let mut seen = BTreeSet::new();
    let mut cursor = node;
    let node_id = node.node_id()?;
    while let Some(parent) = &cursor.parent_id {
        let next = nodes.get(parent).ok_or_else(|| {
            refuse(
                "FAMILY_PARENT_MISSING",
                format!("node {node_id}: parent {parent}"),
            )
        })?;
        if !seen.insert(parent) {
            return Err(refuse(
                "FAMILY_CYCLE",
                format!("node {} is on a cycle", node.node_id()?),
            ));
        }
        cursor = next;
    }
    Ok(())
}
```

**Traversal Properties:**
- **Referential Integrity:** If any node references a `parent_id` not present in the family's node index, it fails with `FAMILY_PARENT_MISSING`.
- **Acyclicity:** If a node ID is re-visited while walking upward to the root, a cycle is present and execution fails with `FAMILY_CYCLE`. Because every non-root node has a parent and the graph is finite and cycle-free, every parent chain terminates at the unique root.

### 3.4 Invariant 4: Anti-Circularity in Checker Verification (`FAMILY_FITNESS_CIRCULAR`)

When a prompt transition is evaluated, model self-evaluation is strictly prohibited (`prompt_family.rs`, lines 356–385):

```rust
fn validate_step_fitness(fit: &Fitness, step_readers: &BTreeSet<&String>) -> Result<(), Refusal> {
    if !matches!(
        fit.checker_verdict.as_str(),
        "ACCEPT" | "REJECT" | "NOT_MEASURED"
    ) {
        return Err(refuse("FAMILY_VERDICT", ...));
    }
    if fit.checker_verdict != "NOT_MEASURED" {
        let checker = fit
            .checker_id
            .as_ref()
            .filter(|c| !c.is_empty())
            .ok_or_else(|| refuse("FAMILY_CHECKER_MISSING", "a verdict needs a checker id"))?;
        if step_readers.contains(checker) {
            return Err(refuse(
                "FAMILY_FITNESS_CIRCULAR",
                "the checker is one of the step's own readers",
            ));
        }
    } else if fit.checker_id.is_some() || fit.obstruction_removed.is_some() {
        return Err(refuse(
            "FAMILY_VERDICT",
            "NOT_MEASURED carries no checker or removal claim",
        ));
    }
    Ok(())
}
```

If the evaluating `checker_id` matches any reader that participated in generating the generative calls for that step (`step_readers`), the step is rejected with `FAMILY_FITNESS_CIRCULAR`. An LLM cannot grade its own outputs or issue its own verification receipts.

### 3.5 Invariant 5: Reader Admission Fence (`FAMILY_UNKNOWN_READER`)

Every reader referenced by a node (`node.reader_digest`), a call record (`call.reader_digest`), or a domain label proposer (`label.proposer_reader`) must be explicitly declared in the family's `readers` vector. Any reference to an undeclared reader triggers `FAMILY_UNKNOWN_READER`.

### 3.6 Invariant 6: Domain Scoping Receipts (`FAMILY_LABEL_STATUS`)

Domain taxonomy labels attached to nodes (`DomainLabel`) must adhere to strict status progression:
- Status must be either `"proposed"` or `"checked"`.
- If status is `"proposed"`, `check_receipt` **must be absent** (cannot smuggle unverified receipts).
- If status is `"checked"`, `check_receipt` **is mandatory** (`FAMILY_LABEL_UNCHECKED`).

---

## 4. Execution Call Records & Financial Accounting

Every generative API interaction is recorded in the family's `calls` vector as a `CallRecord`:

```rust
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
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

**Financial Invariant:** `cost_microusd` must be a non-negative integer (`FAMILY_COST`). Floating-point currency values are rejected to prevent round-off leakage.

---

## 5. Visual Topology of a Prompt Family DAG

Below is a schematic of a validated Prompt Family DAG demonstrating containment and repair edges:

```
                      [ Node 0: Seed Prompt ]
                      (relation: "root", parent: None)
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       [ Node 1: Sub-Task A ]          [ Node 2: Sub-Task B ]
       (relation: "contains",          (relation: "contains",
        parent: Node 0)                 parent: Node 0)
               │                               │
               ▼ (Defect Observed)             ▼ (Accepted)
       [ Node 3: Repaired Sub-Task A ]
       (relation: "repaired_from",
        parent: Node 1)
```

Every repair step links `input_node_id` to `output_node_id`, ensuring full traceability back to the root seed.

---

## 6. Claim Hygiene & Formal Boundaries

### What This Artifact Supports
- Confirms that `PromptFamily` validates tree structure, enforcing exactly one root, valid parent pointers, and absence of cycles.
- Confirms that checker anti-circularity is strictly enforced: `FAMILY_FITNESS_CIRCULAR` is raised if a reader grades its own step.
- Confirms that reader identity is content-addressed and reader references must be declared.

### What This Artifact Does Not Support
- Does not claim that a valid DAG implies the prompts will perform well empirically on unmeasured tasks.
- Does not grant task success credit; validity is structural compliance only (`AuthorityEffect: None`).
- Does not permit multi-parent lattices in this module; each node has at most one parent pointer (`Option<String>`), enforcing an arborescence (tree DAG).

### Narrowest Defensible Claim
The `PromptFamily` module provides an acyclic, content-addressed arborescence data structure that tracks prompt parentage, structural containment, repair lineages, reader environments, and non-circular verification receipts.

### Next Test Needed
A stress test validating DAG traversal performance under deep linear repair chains ($N > 1000$) to confirm stack safety during parent chain traversal.
