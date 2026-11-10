# Prompt Sieve: Nested Prompts & Planar Coloured Operad Trees

**AuthorityEffect:** None  
**Module References:** `pfp/domain/operad/prompt.py`, `pfp/domain/operad/graft.py`, `omega_engine/crates_rs/omega_operads`  
**Status:** Implemented in Python domain layer and native Rust operad crates  

---

## 1. Executive Summary & Problem Formulation

In non-trivial multi-turn workflows, a prompt rarely exists as a monolithic flat string. Instead, prompts contain sub-prompts, embedded instructions, few-shot demonstration exemplars, sub-task declarations, and tool call specifications. In the Prompt Sieve architecture, treating nested prompts as unparsed text strings invites prompt injection, scope leakage, and unverified mutation.

To prevent these failure modes, Prompt Sieve models prompts with nested components as **Planar Coloured Operad Trees**. This representation decomposes a composite prompt into:
1. **Leaf Spans (`LeafTextSpan`)**: Immutable text slices bound to exact document byte offsets `[start, end)`.
2. **Internal Operation Nodes (`OperadTreeNode`)**: Multi-input, single-output algebraic operations mapping typed input colours to a target output colour.
3. **Coloured Boundaries**: A multi-sorted type system separating prompt roles (such as `TASK`, `CONTEXT`, `CONSTRAINT`, `ACCEPTANCE_CRITERIA`, `RESPONSE_CONTRACT`, `TOOL_DECLARATION`, `FEW_SHOT_EXAMPLE`) and mathematical sorts (`RawTextSpan`, `Equation`, `IsolatedVariable`, `SubstitutionStep`, `RationalValue`, `InvariantWitness`, `TargetResult`).
4. **Planar Grafting (`graft`)**: Formal tree composition $(\theta \circ_i \phi)$ that validates boundary colour compatibility, enforces span isolation, and propagates defect null trees (`NullTree`) if invariants fail.

---

## 2. Planar Coloured Operad Representation

The algebraic foundations are defined in `pfp/domain/operad/prompt.py` and mirrored in native Rust in `omega_operad_theory` and `omega_operads`.

### 2.1 The Two-Level Colour Typology

Prompt Sieve operates with a dual-level colour typology:
1. **Clause Role Colours (Structural Decomposition):**
   - `TASK`: The core directive or problem statement.
   - `CONTEXT`: Background knowledge, domain setting, or system instructions.
   - `CONSTRAINT`: Negative instructions, budget limits, and formatting bounds.
   - `ACCEPTANCE_CRITERIA`: Specific automated checker conditions required for pass.
   - `RESPONSE_CONTRACT`: JSON schema or formal output envelope specification.
   - `TOOL_DECLARATION`: Declarations of host capabilities and callable tool schemas.
   - `FEW_SHOT_EXAMPLE`: Exemplar question-answer pairs demonstrating expected style.

2. **Semantic / Mathematical Sorts (`PromptColour` in `prompt.py`, lines 18–33):**
   ```python
   class PromptColour(str, Enum):
       RawTextSpan = "RawTextSpan"
       Equation = "Equation"
       IsolatedVariable = "IsolatedVariable"
       SubstitutionStep = "SubstitutionStep"
       RationalValue = "RationalValue"
       InvariantWitness = "InvariantWitness"
       TargetResult = "TargetResult"
   ```

A planar operad signature is defined as an ordered sequence of input colours mapping to an output colour:
$$\text{Op} : (C_1, C_2, \dots, C_k) \to C_{target}$$

### 2.2 Leaf Text Spans (`LeafTextSpan`)

Defined in `pfp/domain/operad/prompt.py` (lines 35–62):

```python
@dataclass(frozen=True)
class LeafTextSpan:
    id: str
    colour: PromptColour
    content: str
    source_offsets: tuple[int, int]
    document_id: str | None = None
    digest_sha256: str | None = None

    def __post_init__(self) -> None:
        start, end = self.source_offsets
        if start > end:
            raise ValueError(
                f"Start offset {start} exceeds end offset {end} in span '{self.id}'"
            )

    def verify_against_document(self, doc_text: str) -> None:
        start, end = self.source_offsets
        if end > len(doc_text):
            raise ValueError(
                f"End offset {end} exceeds document length {len(doc_text)}"
            )
        slice_text = doc_text[start:end]
        if slice_text != self.content:
            raise ValueError(
                f"Span content mismatch for '{self.id}': expected {self.content!r}, got {slice_text!r}"
            )
```

**Span Invariants:**
- `source_offsets` defines the exact byte interval `(start, end)` in the source document.
- `verify_against_document` enforces that the extracted substring matches `doc_text[start:end]` character-for-character. If text was altered, trimmed, or shifted, verification raises `ValueError`.

### 2.3 Operad Tree Nodes (`OperadTreeNode`)

Defined in `pfp/domain/operad/prompt.py` (lines 94–142):

```python
@dataclass(frozen=True)
class OperadTreeNode:
    operator: PromptOperator
    children: tuple[OperadTreeNode | LeafTextSpan | NullTree, ...]

    @property
    def is_null(self) -> bool:
        return False

    @property
    def output_colour(self) -> PromptColour:
        return self.operator.target_colour
```

Where `PromptOperator` carries:
- `id`: Unique operator identifier.
- `source_colours`: Tuple of input colours corresponding to each child slot.
- `target_colour`: The resulting colour emitted by this operation.
- `arity`: Integer equal to `len(source_colours)`.

---

## 3. Tree Grafting Mechanics: `graft(self, slot, child)`

When a sub-prompt or nested prompt is attached into an open slot $i$ of a parent prompt, the system executes planar grafting (`OperadTreeNode.graft` in `prompt.py`, lines 107–142):

```python
def graft(
    self, slot: int, child: OperadTreeNode | LeafTextSpan | NullTree
) -> OperadTreeNode | NullTree:
    if isinstance(child, NullTree):
        return NullTree(
            ideal_id=child.ideal_id,
            reason=f"grafted child is null tree: {child.reason}",
            target_colour=child.target_colour,
        )
    if slot < 0 or slot >= self.operator.arity:
        raise IndexError(
            f"Slot {slot} out of bounds for operator '{self.operator.id}' (arity {self.operator.arity})"
        )

    expected_colour = self.operator.source_colours[slot]
    actual_colour = (
        child.colour if isinstance(child, LeafTextSpan) else child.output_colour
    )
    if expected_colour != actual_colour:
        raise TypeError(
            f"Boundary colour mismatch at slot {slot}: expected {expected_colour.value}, got {actual_colour.value}"
        )

    new_children = list(self.children)
    while len(new_children) < self.operator.arity:
        new_children.append(
            LeafTextSpan(
                id=f"open_slot_{len(new_children)}",
                colour=self.operator.source_colours[len(new_children)],
                content="",
                source_offsets=(0, 0),
            )
        )
    new_children[slot] = child
    return OperadTreeNode(operator=self.operator, children=tuple(new_children))
```

### 3.1 Step-by-Step Grafting Invariants

1. **Defect / Null Tree Propagation:**
   If `child` is an instance of `NullTree` (representing a rejected, unverified, or refutation-blocked node), grafting does not proceed. Instead, an algebraic ideal absorption occurs: the parent node collapses into a `NullTree` carrying the child's failure reason.
2. **Arity Bounds Checking:**
   If $slot < 0$ or $slot \ge \text{arity}$, `IndexError` is raised.
3. **Boundary Sort Compatibility:**
   The output colour of the child (`child.colour` or `child.output_colour`) must equal the expected input colour `self.operator.source_colours[slot]`. If sorts disagree, execution fails closed with `TypeError: Boundary colour mismatch at slot {slot}`.
4. **Planar Ordering Preservation:**
   Children are stored as an ordered tuple. Existing slots $[0, \dots, i-1]$ and $[i+1, \dots, \text{arity}-1]$ remain intact, preserving planar left-to-right leaf evaluation.

---

## 4. Graft Sites & Invariant Evaluation

In `pfp/domain/operad/graft.py`, grafting sites are formally classified into three topological locations (`GraftSite`):

```python
@enum.unique
class GraftSite(str, enum.Enum):
    VERTEX = "VERTEX"  # Local generator validity (pre-generation)
    EDGE = "EDGE"      # Composition seam boundary type compatibility
    TREE = "TREE"      # Whole-tree circularity and boundary nilpotency
```

When evaluating a `PlanarGraft` (`graft.py`, lines 71–104):
- **VERTEX ($V$-graft):** Checks that the generator $f \in \mathcal{O}^+$ is admissible and internally valid (`generator_valid`).
- **EDGE ($E$-graft):** Checks that at seam index $i$, `expected_type == actual_type`. If a mismatch is detected, it fails with:
  `EDGE seam invariant violated at index {seam_index}: type mismatch expected '{expected}' but got '{actual}'`.
- **TREE ($T$-graft):** Evaluates composite structural invariants:
  1. Acyclicity: `has_circular_dependency` triggers `TREE composite invariant violated: circular dependency detected in {target_id}`.
  2. Boundary Nilpotency: `boundary_leakage != 0` triggers `TREE composite invariant violated: non-zero boundary leakage {boundary_leakage}` ($d_1 \circ d_0 = 0$).

---

## 5. Epistemic Immune Guarding: `omega_operads`

In the native Rust engine (`omega_engine/crates_rs/omega_operads/src/immune_guards.rs`), planar tree substitutions are directly coupled to the Epistemic Immune System through `immune_guarded_substitute`:

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
                phi.name(),
                theta.name(),
                python_text(index),
                verdict.rationale()
            ),
        ));
    }
    substitute(theta, index, phi)
}
```

If an anti-skill detector or danger gate blocks the proposed child operation $\phi$, the substitution is suppressed with `DANGER_GATE_SUPPRESSION`, preventing unvetted or defective sub-prompts from corrupting parent prompt execution trees.

---

## 6. Span Isolation & Sub-Prompt Containment

When a nested prompt $P^*$ contains sub-prompts $\{p_1, \dots, p_k\}$:
1. **Contiguous Byte Offsets:** Each sub-prompt $p_i$ is bound to non-overlapping source offsets $[s_i, e_i)$ such that $e_i \le s_{i+1}$.
2. **Containment within Document:** For all $i$, $0 \le s_i < e_i \le \text{len}(P^*)$.
3. **Span Mutation Shielding:** Because each $p_i$ is tracked as an individual `LeafTextSpan` with its own `digest_sha256`, modifications to sub-prompt $p_j$ cannot alter the bytes or token offsets of sibling sub-prompt $p_k$.
4. **Decomposition Invariant:**
   $$\text{cardinality}(n) = 1 + \sum_{c \in \text{children}(n)} \text{cardinality}(c)$$
   The total tree cardinality equals 1 plus the sum of all descendant sub-prompts.

---

## 7. Claim Hygiene & Formal Boundaries

### What This Artifact Supports
- Confirms that `pfp/domain/operad/prompt.py` and `omega_operads` model nested prompts as planar operad trees with typed boundary checks.
- Confirms that slot index out-of-bounds raises `IndexError` and colour mismatches raise `TypeError`.
- Confirms that null trees propagate upward upon failed grafting, neutralizing defective composite operations.

### What This Artifact Does Not Support
- Does not claim that colored operad parsing prevents semantic hallucinations inside unconstrained leaf spans.
- Does not grant authority promotion to sub-prompts (`AuthorityEffect: None`).
- Does not claim general natural language decomposition; decomposition is bounded to declared finite operad alphabets and verified text spans.

### Narrowest Defensible Claim
Planar colored operad trees provide a multi-sorted syntax tree representation for nested prompts that checks slot arities, enforces sort compatibility at composition seams, and prevents span overlap.

### Next Test Needed
An integration test verifying that dynamic text replacement in a leaf span correctly recalculates downstream byte offsets across sibling and parent spans without invalidating untouched nodes.
