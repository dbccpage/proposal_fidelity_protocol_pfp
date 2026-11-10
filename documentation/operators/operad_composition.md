# Coloured Operad Composition, Planar Trees, and Immune-Guarded Substitutions

**Domain:** Proposal Fidelity Protocol (PFP) Operadic Composition Engine  
**Authority Posture:** `AuthorityEffect: None`  
**Claim Hygiene Standard:** Ground Truth Discipline; exact algebraic definitions; fail-closed verification.

---

## 1. Categorical Foundations of Coloured Operads

In the Proposal Fidelity Protocol (PFP), workflows, skills, and prompt decompositions are not treated as arbitrary string pipelines. Instead, they are modeled as operations in a **coloured planar multicategory** (coloured operad) $\mathcal{O}$.

An operad formalizes operations with multiple typed inputs and a single typed output:
$$f \in \mathcal{O}(c_1, c_2, \ldots, c_n; c)$$
where $c_1, \ldots, c_n$ are input sorts (source colours) and $c$ is the output sort (target colour). The integer $n = \text{arity}(f)$ denotes the number of input slots.

### The Ten Canonical Sorts
All standard skills and operations in the estate are typed over the 10 canonical sorts defined in `code/rust/core_operad_canon/src/lib.rs` (lines 94–168):

```rust
pub enum OperadColour {
    Audit,    // Symmetry audit, red-team diagnostic, compliance report, or defect escalation
    Code,     // Rust/Python implementation, AST, solver module, or Pydantic schema
    Contract, // Nomos governance contract, prime rule YAML, or API boundary specification
    Diagram,  // DIME figure, quick-start card, AST graph, or visualization artifact
    Ledger,   // Claim queue row, refusal store, hypothesis tree, or issue register entry
    Paper,    // OEARS paper package, LaTeX source, Pandoc AST, or claim ledger
    Post,     // Public math post, Glossa dialect draft, or forum cadence item
    Proof,    // Lean 4 formal proof term, math derivation, or step-truth assertion
    Receipt,  // Evidence receipt, CI report, GTLA swarm review, or SHA256 manifest
    State,    // Repository, session worktree, git ref, or execution environment state
}
```

---

## 2. Operation Architecture and Partial Composition

Defined in `code/rust/core_operad_theory/src/foundation/operation.rs` and `colored_operad.rs`:

```rust
pub struct Operation {
    pub op_id: OperationId,
    pub signature: OperadSignature,
    pub kind: OperationKind,
    pub is_equivariant: bool,
}

pub enum OperationKind {
    Identity { colour: OperadColour },
    Generator,
    Composite { term_hash: String },
}
```

### 2.1 Partial Composition ($\circ_i$)
The fundamental composition law in a planar operad is partial substitution:
$$\circ_i : \mathcal{O}(c_1, \ldots, c_n; c) \times \mathcal{O}(d_1, \ldots, d_m; c_i) \to \mathcal{O}(c_1, \ldots, c_{i-1}, d_1, \ldots, d_m, c_{i+1}, \ldots, c_n; c)$$

Implemented in `PlanarColoredOperad::partial_compose(f, g, i)`:
```rust
pub fn partial_compose(&self, f: &Operation, g: &Operation, i: usize) -> Result<Operation, String> {
    if i >= f.arity() {
        return Err(format!("Insertion index i={} out of range [0, {})", i, f.arity()));
    }
    let target_input = &f.inputs()[i];
    if g.output() != target_input {
        return Err(format!(
            "Partial composition ill-typed: {} expects colour {} at position {}, but {} outputs {}",
            f.op_id.as_str(), target_input.as_str(), i, g.op_id.as_str(), g.output().as_str()
        ));
    }
    let mut new_inputs = f.inputs()[..i].to_vec();
    new_inputs.extend_from_slice(g.inputs());
    new_inputs.extend_from_slice(&f.inputs()[i + 1..]);

    let new_id = OperationId::new(format!("({}_o_{}_{})", f.op_id.as_str(), i, g.op_id.as_str()))?;
    Ok(Operation {
        op_id: new_id,
        signature: OperadSignature::new(new_inputs, f.output().clone()),
        kind: OperationKind::composite(format!("{}_o_{}_{}", f.op_id.as_str(), i, g.op_id.as_str())),
        is_equivariant: false,
        description: format!("Planar composition of {} and {} at slot {}", f.op_id.as_str(), g.op_id.as_str(), i),
    })
}
```

### 2.2 Planar vs. Symmetric Variants
- **`PlanarColoredOperad`:** Inputs are strictly ordered. Shuffling input slots changes the operation. Essential for syntax trees, prompt templates, and non-commutative workflows.
- **`SymmetricColoredOperad`:** Supports symmetric group actions ($\Sigma_n$). An operation can be permuted via `permute_operation(op, permutation)` only when equivariance is formally declared.

---

## 3. Planar Trees and Single-Consumer Lowering

Operations in an operad can be represented as rooted planar trees, implemented in `code/rust/core_operad_theory/src/foundation/planar_tree.rs`:

```rust
pub struct PlanarTree {
    pub root: Operation,
    pub children: Vec<TreeChild>,
}

pub enum TreeChild {
    Leaf(OpenLeaf),
    Subtree(PlanarTree),
}
```

### 3.1 Content-Addressed Term Hashing
Every planar tree possesses a deterministic, content-addressed term hash computed via SHA-256 over its preorder traversal:
$$\text{term\_hash}(T) = \text{"tree\_"} + \text{SHA256}\left(\text{root.op\_id} + ";" + \sum_{c \in \text{children}} \text{term\_hash}(c)\right)[:16]$$
This term hash uniquely identifies the composite derivation, preventing structural confusion across runs.

### 3.2 Single-Consumer Planar Tree Lowering
When high-level workflows are written as graphs, they must be compiled into tree terms before execution. The compiler (`operads/application/typed_workflow_compiler.py`, lines 278–303) executes **single-consumer planar tree lowering**:

```python
def _lower_tree(workflow: TypedWorkflowV1, nodes: dict, bindings: dict):
    reached = set()
    occurrence_order = []
    open_inputs = []

    def visit(node_id: str) -> PlanNodeV01:
        reached.add(node_id)
        children = []
        for slot in range(len(nodes[node_id].inputs)):
            source = bindings.get((node_id, slot))
            if source is None:
                open_inputs.append(WorkflowInputV1(node_id, slot))
            else:
                children.append((slot, visit(source)))
        occurrence_order.append(node_id)
        return PlanNodeV01(str(nodes[node_id].operation_id), tuple(children))

    root = visit(workflow.root_node_id)
    if reached != set(nodes):
        raise WorkflowCompileRefusal("UNREACHABLE_NODE", ",".join(sorted(set(nodes) - reached)))
    if tuple(open_inputs) != workflow.inputs:
        raise WorkflowCompileRefusal("ENTRY_BOUNDARY_MISMATCH", "ordered open node/slot references differ")
    return root, tuple(occurrence_order)
```

#### Ground Truth Lowering Invariants:
1. **Single Producer:** Exactly one output binds to each input slot.
2. **Single Consumer:** Each non-root node's output is consumed by exactly one parent slot (multi-consumer fan-out is prohibited; shared dependencies must be duplicated or handled by explicit state passing).
3. **Root Reachability:** All declared nodes must be reachable from `root_node_id`; disconnected subgraphs raise `UNREACHABLE_NODE`.
4. **Boundary Ordering:** Open un-grafted slots must exactly match the declared entry boundary tuple (`ENTRY_BOUNDARY_MISMATCH`).

---

## 4. Planar Graft Sites (`VERTEX, EDGE, TREE`)

To evaluate invariants without corrupting the operational tree, the PFP architecture uses typed **planar grafts**, defined in `pfp/domain/operad/graft.py` (lines 18–105):

```python
class GraftSite(str, enum.Enum):
    VERTEX = "VERTEX"  # Local generator check
    EDGE = "EDGE"      # Partial composition seam check
    TREE = "TREE"      # Global tree composite check
```

```
               [TREE Graft: Evaluates acyclicity, nilpotency d1 ∘ d0 == 0]
                                      │
                                      ▼
                                   (Root)
                                   /    \
     [EDGE Graft: Evaluates] ──>  /      \
     [seam type compatibility]   /        \
                               (Op_A)    (Op_B)
                                 │
     [VERTEX Graft: Evaluates] ─>│
     [generator validity]      (Op_C)
```

### Invariant Evaluation Mechanics
- **`VERTEX` Site:** Evaluates generator validity ($f \in O^+$) before composition. Verifies that the generator's local invariants (e.g. schema compliance, non-empty implementation) are satisfied (`VERTEX generator invariant satisfied`).
- **`EDGE` Site:** Evaluates composition seam boundary type compatibility ($f \circ_i g$). Enforces that the expected input type at port $i$ matches the actual output type of $g$. Any discrepancy raises an edge seam violation (`EDGE seam invariant violated`).
- **`TREE` Site:** Evaluates whole-tree composition properties after AST lowering:
  1. Circular dependency detection: `has_circular_dependency == False`.
  2. Boundary nilpotency: checks that boundary differentials vanish ($\partial_1 \circ \partial_0 = 0$), enforcing `boundary_leakage == 0`.

---

## 5. Polarized Operad Morphisms and Role Purity

In `pfp/domain/operad/operad.py` and `morphisms.py`, operad morphisms are partitioned into a strictly disjoint triad:

$$\mathcal{O} = O^+ \sqcup O^- \sqcup O_{\text{repair}}$$

```
                       ┌───────────────────────────────┐
                       │     PolarizedOperadTriad      │
                       └───────────────┬───────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
 [Constructive O^+]           [Interrogative O^-]            [Corrective O_repair]
 Generates proposals          Emits findings                 Proposes repair patches
 Can compose via ∘_i          FORBIDDEN from patching        FORBIDDEN from evaluating
```

### Constitutional Role Laws:
1. **Law of Constructive Purity:** Partial composition $f \circ_i g$ is strictly permitted **only** between constructive morphisms ($O^+$). Calling `partial_compose` on an interrogative or corrective morphism raises `OperadRoleViolationError`.
2. **Law 4 — Detection-Repair Orthogonality:** Interrogative morphisms ($O^-$) inspect candidates and emit `Finding` records. They are strictly forbidden from proposing code repairs. Calling `emit_patch()` raises `ProhibitedRepairError`.
3. **Law 3 — Zero Self-Promoted Authority:** Corrective repair morphisms ($O_{\text{repair}}$) propose candidate patches. They are strictly forbidden from evaluating candidate correctness or issuing admission decisions. Calling `evaluate()` or `admit()` raises `ProhibitedEvaluationError`.
4. **Slice Licensing:** Agent roles cannot invoke arbitrary morphisms. The aggregate root validates that the role has been explicitly granted a licensed slice via `check_slice_permission()`, raising `SliceViolationError` on unlicensed calls.

---

## 6. Immune-Guarded Substitutions

In both Rust (`code/rust/core_operads/src/immune_guards.rs`, lines 19–40) and Python (`operads/application/immune_guards.py`), planar substitution is directly coupled to the Epistemic Immune System (EIS):

```rust
pub fn immune_guarded_substitute(
    theta: &OperadOperation,
    index: &Value,
    phi: &OperadOperation,
    immune: &mut dyn ImmuneScreenPort,
    evidence: DangerScreenRequest<'_>,
) -> Result<OperadOperation, Refusal> {
    let verdict = immune.danger_verdict(evidence.matches, evidence.danger, evidence.detector)?;
    if *verdict.blocks() {
        return Err(Refusal::new(
            "DANGER_GATE_SUPPRESSION",
            format!(
                "Substitution of {} into {} slot {} suppressed: {}",
                phi.name(), theta.name(), python_text(index), verdict.rationale()
            ),
        ));
    }
    substitute(theta, index, phi)
}
```

### Mechanics of Immune Guarding
1. **Screening Request:** Before substituting $\phi$ into slot $i$ of $\theta$, the runtime presents a `DangerScreenRequest` carrying detector matches and external host danger observations.
2. **Two-Signal Evaluation:** The immune port evaluates whether the candidate triggers active antibodies and whether independent host damage is present.
3. **Suppression:** If the immune verdict blocks (`verdict.blocks() == true`), the substitution is refused outright with error code `DANGER_GATE_SUPPRESSION`, preventing the dangerous operator from entering the execution tree.
4. **Allosteric Quorum:** Multi-sensor substitutions utilize `allosteric_consensus_substitute()`, which checks sensor quorum across multiple readings, raising `ALLOSTERIC_QUORUM_NOT_MET` if consensus fails.

---

## 7. Claim Hygiene Analysis

### 1. What Operad Composition Supports:
- Enforces strict planar sorting across 10 canonical colours, preventing type-mismatched or out-of-order execution.
- Verifies that single-consumer tree lowering detects unreachable nodes, cycles, and boundary mismatches prior to plan generation.
- Enforces role separation where defect detectors ($O^-$) cannot generate fixes, and repair engines ($O_{\text{repair}}$) cannot self-certify.
- Demonstrates immune-guarded substitution that suppresses dangerous compositions before AST incorporation.

### 2. What Operad Composition Does Not Support:
- Does not demonstrate that a type-checked operad composition is semantically bug-free.
- Does not show that language models generate schema-valid operations without retries.
- Does not grant execution authority outside host-declared sandboxes.

### 3. The Narrowest Defensible Claim:
The PFP coloured operad framework provides a deterministic, typed planar composition and grafting harness that prevents ill-typed substitutions, detects topological defects, and blocks known failure motifs under `AuthorityEffect: None`.

### 4. The Next Test Needed:
Execution of an automated test suite verifying that an un-licensed agent role attempting to invoke an out-of-slice morphism consistently raises `SliceViolationError`.
