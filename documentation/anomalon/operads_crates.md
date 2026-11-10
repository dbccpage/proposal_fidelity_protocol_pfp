# Anomalon Operad Crates: `omega_operad_theory` and `omega_operads`

**AuthorityEffect:** None  
**Status:** Code-Grounded Reference Documentation  
**Repository Paths:**
- `omega_operad_theory`: `c:\Users\a343o\source\repos\anomalon\omega_engine\crates_rs\omega_operad_theory`
- `omega_operads`: `c:\Users\a343o\source\repos\anomalon\omega_engine\crates_rs\omega_operads`
**Governing Paradigm:** Multi-Category Colored Operad Composition and Immune-Gated Substitution  

---

## 1. Architectural Overview and Separation of Concerns

The Anomalon operadic architecture is factored into two complementary Rust crates:
1. **`omega_operad_theory`**: The sovereign theoretical foundation implementing a 5-tier colored operad hierarchy, algebraic realizations, Koszul deformation theory, geometric Little $n$-Disks topology, and a digest-bearing kernel for execution licenses and 2-cell homotopies.
2. **`omega_operads`**: The applied domain engine providing concrete workflow validation, planar tree substitutions, skill-garden culling, and the critical epistemic bridge where operad composition is gated by the Epistemic Immune System.

Both crates strictly declare and return `AuthorityEffect: None`. Operad operations represent typed algebraic compositions and syntactic trees; they never grant administrative privileges or bypass validation boundaries.

---

## 2. Deep Dive: `omega_operad_theory` (5-Tier Hierarchy)

`omega_operad_theory` organizes abstract operad mathematics into five distinct architectural tiers plus an estate kernel subsystem.

```
┌────────────────────────────────────────────────────────┐
│                   Tier 5: Applications                 │
│      (OEASWorkflowOperad, AgentCapabilitySlice)        │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                    Tier 4: Geometric                   │
│      (LittleDisksConfiguration, Homology Operads)      │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   Tier 3: Deformation                  │
│   (QuadraticOperad, KoszulDualBuilder, BarCobar)       │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   Tier 2: Realization                  │
│    (OperadAlgebra, OperadicModule, Associativity)      │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                   Tier 1: Foundation                   │
│ (OperadColour, Signature, Operation, PlanarTree)       │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                     Kernel Subsystem                   │
│   (Licenses, ProofObligations, 2-Cell Homotopies)      │
└────────────────────────────────────────────────────────┘
```

### 2.1 Tier 1: Foundation (`src/foundation/`)
Provides the atomic mathematical primitives for colored operads:
- **`OperadColour`:** Validated type identifier. Colours must belong to explicit admitted finite palettes (`ADMITTED_FINITE_COLOURS`), preventing arbitrary or unbounded type introduction.
- **`OperadSignature`:** Defines the multi-input, single-output signature $S = (c_1, c_2, \dots, c_n; c_{\mathrm{target}})$, specifying required operand colours and resulting output colour.
- **`Operation`:** Atomic operadic generator characterized by `OperationId`, signature, arity, and an `is_identity` predicate.
- **`PlanarTree`:** Directed planar tree structure with strictly ordered input slots, open leaves (`OpenLeaf`), and internal nodes (`TreeChild`). Ensures non-commutative, position-sensitive operadic composition.
- **`PlanarColoredOperad` & `SymmetricColoredOperad`:** Sovereign operad definitions enforcing unit corollas ($1_c \circ_1 \theta = \theta = \theta \circ_i 1_{c_i}$), associativity under planar composition $\circ_i$, and symmetric group $\Sigma_n$ actions where applicable.
- **`MonoidalOperad`:** Operadic structures compatible with monoidal tensor products.

### 2.2 Tier 2: Realization (`src/realization/`)
Binds abstract operadic operations to concrete computational carriers:
- **`OperadAlgebra`:** Multi-sorted algebra mapping colored operad operations to functions over concrete carrier sets:
  $$A(\theta): A(c_1) \times \dots \times A(c_n) \to A(c_{\mathrm{target}})$$
- **`OperadicModule`:** Endofunctor action over operad colors, supporting left and right module actions that model context propagation and evaluation environments.
- **`StructuralAssociativityWitness`:** Formal verification engine checking the planar operadic associativity law:
  $$(a \circ_i b) \circ_j c = a \circ_i (b \circ_{j - i + 1} c)$$
  Emits verifiable `LawResult` records proving that tree reductions preserve equivalence classes.

### 2.3 Tier 3: Deformation (`src/deformation/`)
Implements formal algebraic deformation theory and Koszul duality:
- **`QuadraticOperad` & `QuadraticRelation`:** Encapsulates operads generated by binary operations modulo relations in the degree-2 component $\mathcal{P}(2) \otimes \mathcal{P}(2)$.
- **`ColouredCooperad`:** The dual coalgebraic structure with decomposition maps $\Delta: \mathcal{C} \to \mathcal{C} \circ \mathcal{C}$.
- **`KoszulDualBuilder` & `ProposedQuadraticDual`:** Computes the Koszul dual operad $\mathcal{P}^!$, extracting orthogonal annihilators of quadratic relations under the invariant inner product.
- **`BarCobarResolution`:** Constructs the bar construction $B(\mathcal{P})$ and cobar construction $\Omega(\mathcal{C})$, enabling homological resolution and derived deformation analysis.

### 2.4 Tier 4: Geometric (`src/geometric/`)
Topological and geometric realizations:
- **`LittleDisksConfiguration` & `RectilinearDisk`:** Models the little $n$-disks topological operad $D_n$, representing non-overlapping embeddings of $n$-dimensional disks into a bounding unit disk.
- **Homology Operads:** Implements homology operads $H_*(D_n)$:
  - `build_associative_homology_operad()` ($H_*(D_1)$): Yields the ordinary associative operad $\mathrm{Assoc}$.
  - `build_commutative_homology_operad()` ($H_*(D_n)$ for $n \ge 2$): Yields the commutative operad $\mathrm{Comm}$.
  - `build_gerstenhaber_homology_operad()` ($H_*(D_2)$): Yields the Gerstenhaber algebra operad with Lie bracket of degree $-1$ and commutative product.

### 2.5 Tier 5: Applications (`src/applications/`)
Applied workflow orchestrators:
- **`OEASWorkflowOperad`:** Specializes colored operads for agent workflow execution. Binds pipeline stages to admitted port colors (`OEAS_ADMITTED_PORT_COLOURS`).
- **`AgentCapabilitySlice`:** Defines typed capability boundaries for agent execution, establishing which operadic trees an agent role is licensed to evaluate.

### 2.6 The Kernel Subsystem (`src/kernel/`)
The digest-bearing execution kernel enforcing capability control and 2-cell homotopies:
- **Licenses (`ActionLicense`, `AgentLicense`):** Content-addressed authorization tokens authorizing specific operations on bounded data spans.
- **Terms (`OperationTerm`, `LicensedTerm`, `NormalizedTerm`):** Typed syntax terms carrying execution credentials.
- **Obligations (`ProofObligation`, `ObligationBundle`):** Unresolved obligations generated during operadic evaluation that must be discharged by independent certifiers.
- **2-Cell Homotopy (`Path2`, `Homotopy2Cell`, `WhiskerPath2`):** Models 2-dimensional homotopy equivalences between reduction paths:
  - `AtomicPath2`: Elementary rewrites.
  - `HorizontalPath2` & `VerticalPath2`: Horizontal and vertical composition of 2-cells.
  - `WhiskerPath2`: Left and right whiskering of 1-morphisms around 2-cells, formalizing true higher-categorical coherence without ad-hoc path rewrites.

---

## 3. Deep Dive: `omega_operads` (Applied Engine)

`omega_operads` operationalizes operad theory into practical execution pipelines and provides tools for workflow validation, tree modification, and skill lifecycle management.

### 3.1 Planar Substitutions (`src/planar.rs`)
Implements concrete operadic tree grafting:
- **`substitute(theta, index, phi)`:** Substitutes operation $\phi$ into the $i$-th input slot of operation $\theta$ (denoted $\theta \circ_i \phi$).
- Checks signature compatibility:
  $$\mathrm{target\_colour}(\phi) = \mathrm{input\_colours}(\theta)[i]$$
  If types match, it splices the leaf tree, updating arity and re-indexing subsequent open slots.

### 3.2 Workflow Slices and Validation (`src/workflow.rs`)
Validates composite pipeline definitions against strict structural invariants:
- **Input Declaration:** Evaluates JSON/YAML workflow manifests containing `workflow_id`, `source_colours`, `target_colour`, `pipeline`, and `authority_effect`.
- **Validation Engine:** `validate_workflow()` checks that consecutive steps form a valid operad composition chain without type mismatch or unbonded ports.
- **Output:** Emits a `WorkflowReport` containing structural status and structured `WorkflowFinding` items if faults are detected.

### 3.3 Skill Garden Culling (`src/skill_garden.rs`)
Maintains the health and compactness of candidate agent skill libraries:
- Identifies inactive, superseded, or mathematically redundant skills.
- Evaluates replacement morphisms: if a skill $S_2$ covers the signature and obligations of $S_1$ with strictly lower obstruction cost, $S_1$ is marked for culling.

---

## 4. The Critical Bridge: `immune_guards.rs`

The file `omega_operads/src/immune_guards.rs` represents the **critical bridge between operadic composition and sovereign epistemic immunity**. It establishes that mathematical composability is a necessary, but **not sufficient**, condition for execution.

```
       Candidate Substitution: θ ∘_i φ
                     │
                     ▼
         [Signature Compatibility] ──► Fails: Refusal
                     │
                     ▼ (Passes)
       [Query ImmuneScreenPort]
                     │
      ┌──────────────┴──────────────┐
      │                             │
      ▼                             ▼
[Danger Gate Check]        [Allosteric Quorum]
(Matches + Host Danger)    (Multi-Sensor Consensus)
      │                             │
      ▼                             ▼
 Blocks: Refusal               Blocks: Refusal
"DANGER_GATE_SUPPRESSION"     "ALLOSTERIC_QUORUM_NOT_MET"
      │                             │
      └──────────────┬──────────────┘
                     │ (Both Clear)
                     ▼
       Execute substitute(θ, i, φ)
```

### 4.1 Inward Dependency Isolation
`immune_guards.rs` does not import the concrete `omega_epistemic_immune_system` crate. Instead, it interacts strictly through workflow-owned port interfaces defined in `omega_operads/src/immune_ports.rs`:
- `ImmuneScreenPort`: Abstract port defining screening methods.
- `DetectorIdentity`: Unique detector identifier.
- `DetectorMatch`: Evidence of a regex/pattern hit.
- `HostDangerObservation`: Independent corroborating host signal.
- `SensorReading`: Environmental health observation.

This maintains clean dependency boundaries, allowing the operad engine to run in lightweight environments without compiling the full immune system.

### 4.2 `immune_guarded_substitute`
Before allowing a planar substitution $\theta \circ_i \phi$, the engine evaluates `immune_guarded_substitute`:

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

- **Mechanism:** The host packages observed detector matches and any independent host danger signals into `DangerScreenRequest`.
- **Verdict Evaluation:** Queries `immune.danger_verdict(...)`.
- **Failure Mode:** If the immune port indicates that the danger gate blocks the operation, the substitution fails closed, returning a typed `Refusal` with code `DANGER_GATE_SUPPRESSION`. The syntactic substitution is completely aborted.

### 4.3 `allosteric_consensus_substitute`
For multi-sensor and environmental safety gating:

```rust
pub fn allosteric_consensus_substitute(
    theta: &OperadOperation,
    index: &Value,
    phi: &OperadOperation,
    readings: &[SensorReading],
    immune: &mut dyn ImmuneScreenPort,
) -> Result<OperadOperation, Refusal> {
    let verdict = immune.quorum_verdict(readings)?;
    if *verdict.blocks() {
        return Err(Refusal::new(
            "ALLOSTERIC_QUORUM_NOT_MET",
            format!(
                "Substitution of {} into {} slot {} refused: {}",
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

- **Mechanism:** Evaluates an ensemble of environmental sensor readings (e.g., token consumption, memory pressure, regression indicators).
- **Quorum Requirement:** If an allosteric quorum is not met, substitution is blocked with `ALLOSTERIC_QUORUM_NOT_MET`.

### 4.4 Workflow Policy Integration
`validate_workflow_immune_guard()` checks whole workflow reports against an active `DangerSignalPolicy`:
- If `policy.enforce_danger_gate()` is active, any uncorroborated or dangerous operad operations attach a guard finding to the workflow report, preventing pipeline progression.

---

## 5. Defensible Claims and Boundary Summary

1. **What this code supports:**
   - Rigorous multi-tier operadic type checking with strict planar associativity verification.
   - Formal separation between abstract categorical operads and applied workflow engines.
   - Guaranteed fail-closed substitution suppression when epistemic immune danger gates trigger.
   - Precise 2-cell homotopy path tracking with left/right whiskering.

2. **What this code does NOT support:**
   - Broad semantic safety claims (operads certify syntactic type compatibility; danger gates depend on declared detector patterns and independent host signals).
   - Inversion of authority (an operad operation cannot confer execution rights not granted by the host).
