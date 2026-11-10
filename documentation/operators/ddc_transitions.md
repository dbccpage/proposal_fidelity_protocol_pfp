# Discrete Deformation Calculus (DDC): Lawful Transitions, Repair Stages, and Motifs

**Domain:** Proposal Fidelity Protocol (PFP) Cochain Deformation Engine  
**Authority Posture:** `AuthorityEffect: None`  
**Claim Hygiene Standard:** Ground Truth Discipline; exact algebraic definitions; fail-closed verification.

---

## 1. Overview of Discrete Deformation Calculus

Discrete Deformation Calculus (DDC) is the algebraic calculus governing how candidates (code patches, proofs, prompt spans, or configuration structures) evolve when confronted with defects and obstructions. Rather than relying on unconstrained, stochastic re-prompting, DDC models candidate modifications as formal cochain transitions over a declared carrier complex.

Every state in a DDC process is characterized by a **residual tuple**:
$$\text{state} = (\text{carrier}, \text{window}, \text{defect}, \text{residual})$$
where the residual classification is strictly partitioned into:
- **`Open`:** An uncontracted defect exists; verification fails or obligations remain open.
- **`Closed`:** The defect cannot be resolved within the local carrier, but is bounded and cleanly accounted for.
- **`Exact`:** The defect is eliminated ($\text{residual} \to 0$); all verification oracles pass.

All transitions must belong to a closed 8-letter operational alphabet $\mathcal{A}_{\text{DDC}}$.

---

## 2. The Eight Lawful DDC Transitions

Defined canonically in Rust crate `code/rust/core_operad_canon/src/lib.rs` (lines 175–245):

```rust
pub enum DdcOp {
    ExactRepair,        // 'E'
    ResidualProjection, // 'R'
    ContextExposure,    // 'C'
    Integration,        // 'I'
    Lift,               // 'Λ'
    Descent,            // 'D'
    Refusal,            // 'M'
    Terminalize,        // 'T'
}
```

The 8 operations form a closed alphabet. Any transition outside these eight is refused by the runtime:

### 2.1 `E` — Exact Repair
- **Algebraic Effect:** Discharges the observed defect outright, driving the cochain residual to zero ($\text{residual} \to 0$).
- **Precondition:** The defect must be within the coboundary image of the local operator ($\delta u = \text{defect}$).
- **Postcondition:** Post-check verification oracles pass with exit code 0 (`residual_after == "Exact"`).
- **Verification:** An external host oracle confirms all test assertions pass cleanly without regressions.

### 2.2 `R` — Residual Projection
- **Algebraic Effect:** Carries forward irreducible obstruction mass that cannot be resolved within the current local 2-window.
- **Precondition:** Defect has non-zero projection onto the cohomology quotient space ($H^k \neq 0$).
- **Postcondition:** Residual state transitions to `Closed` or records an unremovable residual packet.
- **Verification:** The boundary of the residual is verified to be closed ($\partial r = 0$), preventing uncontracted boundary leakage.

### 2.3 `C` — Context Exposure
- **Algebraic Effect:** Declares or splits the carrier boundary and exposes the active local 2-window.
- **Precondition:** Requires an explicit source manifest and fixed file scope (`relative_file` validation).
- **Postcondition:** The workspace state is snapshotted; baseline check observations are captured.
- **Verification:** Source digests match declared manifests (`SOURCE_DIGEST_REFUSED` if mismatched).

### 2.4 `I` — Integration
- **Algebraic Effect:** Appends a verified delta or cochain update to the local ledger.
- **Precondition:** The patch must pass all declared local checks.
- **Postcondition:** Changes are incorporated into the workspace manifest without conferring repository authority.
- **Verification:** File system diff inspection ensures only paths declared in `write_paths` were altered.

### 2.5 `Λ` (or `Meta`) — Structural Lift
- **Algebraic Effect:** Elevates the representation complex to a higher dimension or covering space.
- **Crucial Invariant:** **Lift trigger is not lift license.** A structural lift cannot be invoked arbitrarily. It requires:
  1. An obstruction witness proving the defect is a genuine cohomology class (`StabilizedSurvivor`) not contractible by local `ResidualUpdate`.
  2. A preservation witness showing that existing ground truth properties are invariant under the pullback.
  3. A non-destruction witness demonstrating that prior verified bounds are maintained.
  4. An explicit terminalizer route guaranteeing eventual termination.

### 2.6 `D` — Descent / Re-indexing
- **Algebraic Effect:** Refines the coordinate index, contracts the active window, or projects from covering space back to the base carrier.
- **Precondition:** Higher-dimensional obstruction has been discharged or factored out.
- **Postcondition:** Returns execution to a lower-degree local evaluation complex.

### 2.7 `M` — Mutation / Typed Refusal
- **Algebraic Effect:** Emits a closed refusal code when an obstruction cannot be safely removed or when input contracts are violated.
- **Precondition:** Detection of invalid inputs, out-of-bounds requests, or non-repairable defects.
- **Postcondition:** Execution halts with a typed refusal (`RepairRefusalV1`), stopping further mutation.

### 2.8 `T` — Terminalize
- **Algebraic Effect:** Records a terminal execution status, sealing the trajectory ledger.
- **Crucial Invariant:** Emitting `T` records a terminal status; **it does not mint authority** (`AuthorityEffect: None`).
- **Postcondition:** The output is frozen into `RepairTerminalV1` with `admission: "Unadmitted"` and `production_activation: "HOLD"`.

---

## 3. The Six Repair Stages of Code Repair

In single-turn and local code repair, the DDC algebra is instantiated as a bounded 6-stage state machine defined in `operads/contracts/ddc_code_repair_v1.py` (lines 12–148). Structural lift ($\Lambda$) and descent ($D$) are excluded from single-turn code repair because local code repairs operate on a fixed carrier workspace:

$$\text{STAGES} = (\text{C}, \text{R}, \text{E}, \text{I}, \text{M}, \text{T})$$

```python
EXECUTOR_METHODS = (
    ("C", "capture"),       # Expose context, snapshot baseline checks
    ("R", "observe"),       # Observe failures and open residual defects
    ("E", "evaluate"),      # Apply candidate patch and run checks
    ("I", "incorporate"),   # Integrate changes into state manifest
    ("M", "disposition"),   # Evaluate regressions and determine outcome
    ("T", "terminal")       # Emit terminal record with AuthorityEffect: None
)
```

### Stage Evaluation Logic (`assess(state)`)
The outcome of the repair machine is evaluated strictly through host check comparisons:
```python
def assess(state: RepairStateV1) -> str:
    if state.refusal is not None:
        return "REFUSED"
    before = {row.check_id for row in state.baseline if row.returncode != 0}
    after = {row.check_id for row in state.after if row.returncode != 0}
    if after - before:
        return "REGRESSION"       # New failing checks introduced
    if not before:
        return "NO_REPAIR_NEEDED" # Baseline was already clean
    if not after and state.changed_paths:
        return "REPAIRED"         # All failing checks resolved
    return "PARTIAL" if after < before else "INEFFECTIVE"
```

### Terminal Envelope Invariants (`RepairTerminalV1`)
Every terminal state emitted by the DDC machine enforces strict neutral authority boundaries:
- `schema_version`: `"oeop.ddc-code-repair-terminal.v1"`
- `authority_effect`: `"None"`
- `admission`: `"Unadmitted"`
- `production_activation`: `"HOLD"`
- `evidence_scope`: `"FIXED_LOCAL_COMMANDS"`
- `mathematical_measurement`: `"NOT_MEASURED"`

---

## 4. DDC Degree Tower Operations

On formal cochain complexes (such as binary complexes and simplicial models), DDC operates across degree towers ($k \to k+1$), implemented in `code/rust/core_wdp/src/ddc/degree_tower.rs` (lines 250–326):

```rust
pub enum DdaOperationKind {
    SuccessorProbe,
    ResidualUpdate,
    CarrierLift,
}
```

### 4.1 Operation Mechanics
1. **`SuccessorProbe`:** Measures the coboundary operator $\delta^k$ to detect open defects. Evaluates the dual defect / obstruction ($\gamma$) and the primal distance to the coboundary ($\phi$).
2. **`ResidualUpdate`:** Modifies the cochain within the existing carrier space via XOR sum ($v \oplus \Delta v$). Minimal repair cost is strictly verified against the primal distance:
   $$\text{repair\_cost} = \text{HammingWeight}(\Delta v) == \phi$$
   If `repair_cost != before.phi`, the transition errors with `RepairIsNotMinimal`.
3. **`CarrierLift`:** When a defect has non-zero dual obstruction ($\gamma > 0$), it represents a non-trivial cohomology class (`StabilizedSurvivor`). Such defects cannot be resolved by any `ResidualUpdate` within the base carrier. The system must execute `CarrierLift`, pulling the problem back to a covering space where the class bounds a higher-dimensional cell.

### 4.2 The `DetectThenRepairPacket` Verification Sequence
Implemented in `core_wdp::ddc::degree_tower::DetectThenRepairPacket::verify()`:
1. Ensure input dimension matches the carrier residual dimension.
2. Verify `before.classification == DegreeTrichotomy::Open` (rejects unneeded repairs).
3. Compute repaired residual $r_{\text{new}} = r_{\text{old}} \oplus \Delta r$.
4. Verify `after.classification == DegreeTrichotomy::Exact` and $\gamma_{\text{after}} = 0$.
5. Verify repair minimality: $\text{cost} == \phi_{\text{before}}$.
6. Bind operations array: `[DdaOperationKind::SuccessorProbe, DdaOperationKind::ResidualUpdate]`.

---

## 5. DDC Short Motifs

In the operand registry and prompt family execution engines (`code/rust/core_operad_canon/src/types.rs`, line 521), DDC operations combine into standard short motifs:

$$\text{Motifs} \subseteq \mathcal{A}_{\text{DDC}}^* = \{\text{CE}, \text{CM}, \text{CR}, \text{EM}, \text{ID}\}$$

| Motif | Full Sequence | Operational Meaning | Typical Use Case |
|---|---|---|---|
| **`CE`** | ContextExposure $\to$ ExactRepair | Clean single-shot resolution: expose context, apply minimal delta, drive residual to zero. | Simple bug fixes, syntax adjustments, schema conformances. |
| **`CM`** | ContextExposure $\to$ Refusal/Mutation | Expose context, inspect invariants, detect unresolvable defect or smuggled axiom, emit typed refusal. | Rejection of out-of-scope prompts, smuggled axioms, or malformed fixtures. |
| **`CR`** | ContextExposure $\to$ ResidualProjection | Expose context, resolve local components, project irreducible residual forward to parent complex. | Multi-tier pipelines where sub-problems pass residuals to higher layers. |
| **`EM`** | ExactRepair $\to$ Refusal/Mutation | Attempt exact repair; upon finding hidden secondary obstruction, transition to typed refusal. | Falsified repair attempts where fixing one check exposes an invariant violation. |
| **`ID`** | Integration $\to$ Descent | Integrate local patch into ledger, then refine window / descend to sub-component. | Hierarchical AST or modular refactoring sweeps. |

*(Note: Legacy operand `op_lean4_constructive_kernel_axiom_audit` previously declared motif `CP`, which is invalid because `P` is not in $\mathcal{A}_{\text{DDC}}$. The canon maps this to `CM`.)*

---

## 6. Obstruction Removal vs. Structure Creation

A central discipline of DDC is the formal mathematical separation between **removing obstruction** and **creating structure**:

```
                       ┌──────────────────────────────┐
                       │  Cochain State (Carrier, r)  │
                       └──────────────┬───────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
   [Obstruction Removal]                             [Structure Creation]
   Operations: {E, R, M}                             Operations: {C, Λ, D}
   - E: Drives residual to zero                      - C: Declares active 2-window
   - R: Projects closed residual                     - Λ: Lifts complex to covering space
   - M: Halts with typed refusal                     - D: Refines/descends coordinates
   Goal: Eliminate defect mass                       Goal: Expand or reindex carrier
```

### Formal Verification Rules
1. **Separation of Concerns:** An obstruction removal operation ($E$) cannot simultaneously alter the carrier boundary or introduce new undefined dimensions.
2. **Structure Creation Requires Witness:** A structure creation operation ($\Lambda$) cannot be justified by mere desire for expressiveness; it must present a certified obstruction receipt ($\gamma > 0$) proving the defect cannot be removed within the current structure.
3. **Fail-Closed Composition:** The composition of obstruction removal and structure creation must be bounded by finite budgets (`max_depth <= 5`, `MAX_ORGANIZE_BYTES = 1,048,576`).

---

## 7. Claim Hygiene Analysis

### 1. What DDC Transitions Support:
- Formulates a deterministic, discrete state-machine for candidate evolution under exact host check verification.
- Enforces minimal repair cost verification ($\text{cost} == \phi$) in degree-tower cochains.
- Distinguishes irreducible topological obstructions from contractible local defects.
- Prevents authority escalation by enforcing `AuthorityEffect: None` across all terminals.

### 2. What DDC Transitions Do Not Support:
- Does not demonstrate that automated code repair can solve arbitrary semantic bugs or halting problems.
- Does not ensure that language model proposals will generate valid repairs.
- Does not grant operational or repository mutation authority without human admission.

### 3. The Narrowest Defensible Claim:
Discrete Deformation Calculus provides an 8-letter formal alphabet and 6-stage repair machine that deterministically executes, verifies, and classifies candidate transformations against host oracles without conferring authority.

### 4. The Next Test Needed:
Execution of a property-based fuzzing test over the `DetectThenRepairPacket` state transitions to confirm that any non-minimal repair ($\text{cost} \neq \phi$) consistently raises `DegreeTowerError::RepairIsNotMinimal`.
