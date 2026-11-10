# Operator and Operand Taxonomy of the Proposal Fidelity Protocol

**Domain:** Proposal Fidelity Protocol (PFP) Operadic Architecture  
**Authority Posture:** `AuthorityEffect: None`  
**Claim Hygiene Standard:** Ground Truth Discipline; zero promotional language; exact file, type, and count verification.

---

## 1. Executive Overview & Ontological Foundations

The Proposal Fidelity Protocol (PFP) structures verification, code repair, and generative model interactions through a typed operadic framework. Rather than permitting open-ended model self-evaluation, the system represents executable units, checks, constraints, and data spans as typed entities within a planar multicategory (coloured operad).

The system architecture partitions operations into distinct algebraic roles:
1. **Generative / Constructive operations ($O^+$):** Propose candidate code, text spans, or solutions.
2. **Interrogative / Negative operations ($O^-$):** Probe for defects, evaluate invariants, and emit findings or typed refusals.
3. **Corrective / Repair operations ($O_{repair}$):** Apply bounded deformations to eliminate detected defects without acquiring unverified authority.

This document catalogs every operator and operand class recognized across the Rust and Python codebases, citing exact source paths, type representations, lifecycles, and storage counts. Crucially, it distinguishes between executable implementations currently built into code and aspirational or retired specifications.

---

## 2. Master Taxonomy Matrix

The following table summarizes the 24 identified operator and operand classes:

| # | Class Name | Primary Source Location | Code Type / Structure | Storage Count | Built Code Reality |
|---|---|---|---|---|---|
| 1 | **Skill** | `operads/skills/*/SKILL.md`, `operads/domain/capability_catalog_v1.py` | `SkillCapabilityV1`, YAML frontmatter | 237 catalogued packages | Fully functional catalog contract; maps ports across 10 canonical colours. |
| 2 | **Anti-Skill** | `code/rust/core_epistemic_immune_system/src/anti_skill.rs` | `struct AntiSkillSpecV2`, `enum AntiSkillStatus` | 0 stored instances | Rust/Python types fully implemented; 0 live records stored in repo. |
| 3 | **Rule** | `operads/skill_operad/yaml/rules_registry.yaml`, `operads/rules/` | `RuleDocument`, `RuleInvariant` | 50 documents, 144 invariants | Active governance registry: 28 enforced, 12 partial, 104 candidate invariants. |
| 4 | **Anti-Rule** | *Not a discrete type* | Carried by Anti-Patterns (`AP_*`) and Antibodies | 0 standalone types | Conceptual function executed via anti-patterns and refusal gates. |
| 5 | **Agent Role** | `operads/registry/roles.yaml` | `AgentRole` (role with colour licence) | 12 declared roles | Defines colour permissions; 0 catalogued autonomous agents in JSON. |
| 6 | **Anti-Agent** | *Not a discrete type* | Terminal typed refusals (`RefusalReason`) | 0 standalone types | Operational pattern terminating branches upon stale task or constraint violation. |
| 7 | **Antibody (Pharmacy)** | `eis/antibodies/ab_*.json` | JSON dictionary (`core.pharmacy.antibody-record`) | 58 records | Active operational records evaluated by screening runners against fixtures. |
| 8 | **Antibody (Spec)** | `eis/antibodies/anti_*.yaml` | YAML contract (`core.immune.antibody-spec.v1`) | 37 authored specs | Authored regex specifications bound to governing rules; 24 overlap with pharmacy. |
| 9 | **DDC Transitions** | `code/rust/core_operad_canon/src/lib.rs` | `enum DdcOp` (`E, R, C, I, Λ, D, M, T`) | 8 closed letters | Canonical closed alphabet representing lawful discrete deformations. |
| 10 | **DDC Repair Stages** | `operads/contracts/ddc_code_repair_v1.py` | `DdcRepairStage` (`C, R, E, I, M, T`) | 6 stages | Bounded code-repair machine; structural lift $\Lambda$ and descent $D$ excluded. |
| 11 | **DDC Degree Tower Ops**| `code/rust/core_wdp/src/ddc/degree_tower.rs` | `enum DdaOperationKind` | 3 kinds | `SuccessorProbe`, `ResidualUpdate`, `CarrierLift` on cochain complexes. |
| 12 | **Helpful Pattern (HP)**| `operads/patterns/helpful/` | Markdown contract (`HP_<LANG>_<NNN>`) | 94 files | Structural code and prose idiom specifications across 4 languages. |
| 13 | **Anti-Pattern (AP)** | `operads/patterns/anti/` | Markdown contract (`AP_<LANG>_<NNN>`) | 93 files | Structural defect templates paired by number with helpful patterns. |
| 14 | **Inventory Op** | `operads/skill_operad/yaml/op_inventory.yaml` | YAML `ops` entries (`inventory_op`) | 15 declared ops | Executable host-bound tools (`glossa.*`, `sfh.*`, `gti.*`, `ara.*`, `mnc.*`). |
| 15 | **Inventory Anti-Op** | `operads/skill_operad/yaml/op_inventory.yaml` | YAML `anti_ops` entries (`inventory_anti_op`) | 8 declared anti-ops | Pre-execution refusal gates (`sfh.refuse_bare_except`, `gti.refuse_sys_path_hack`). |
| 16 | **Prompt Anti-Op Detector**| `operads/domain/prompt_hierarchy/evaluator.py` | `DEFAULT_KEYWORD_PATTERNS` | 7 built-in detectors | Static AST/keyword scanners checking prompt payloads for smuggled assumptions. |
| 17 | **Coloured Operad Op** | `code/rust/core_operad_theory/src/foundation/operation.rs` | `struct Operation`, `enum OperationKind` | Extensible algebra | Typed operation: `Identity`, `Generator`, or `Composite` with term hash. |
| 18 | **Prompt Operad Tree Node**| `pfp/domain/operad/prompt.py` | `OperadTreeNode`, `LeafTextSpan`, `NullTree` | 7 prompt colours | Planar operad trees representing decomposed prompt spans and congruences. |
| 19 | **Planar Graft Operator** | `pfp/domain/operad/graft.py` | `struct PlanarGraft`, `enum GraftSite` | 3 sites (`V, E, T`) | Evaluates generator validity (V), seam compatibility (E), or tree nilpotency (T). |
| 20 | **Polarized Morphisms** | `pfp/domain/operad/operad.py` | `ConstructiveMorphism`, `InterrogativeMorphism`, `RepairMorphism` | Triad aggregate root | Strictly disjoint sub-operads enforcing partial composition rules. |
| 21 | **Instruction Operand** | `operads/catalog/operands/v1/adversary/`, `operads/domain/value_objects/operands.py` | `InstructionOperand`, `SpanOperand` | 4 instruction files | Explicit addressable byte spans acting as operands in multicategories. |
| 22 | **Prompt Antimorphism** | `code/rust/core_prompt_civilization/src/antimorphism.rs` | `ExactOrbitSumDetector`, `ExactSignInvolutionDetector`, `StationaryRepeatDetector` | 3 exact detectors | Mathematical predicates evaluating prompt evolution anomalies via exact arithmetic. |
| 23 | **Prompt Mutation Engine**| `code/rust/core_prompt_civilization/src/forge.rs` | `PromptMutationEngineV1`, `ProtectedSpanV1` | Engine + policy | Append-only organization; enforces immutable protected span boundaries. |
| 24 | **Epistemic Trap Detector**| `code/rust/core_types/src/epistemic_sieve.rs` | `enum TrapDetector`, `struct TrapAlert` | 47 enum variants | Classifies cognitive, mathematical, and physical failure modes in proposals. |

---

## 3. Detailed Specification of Operator Classes

### 3.1 Class 1: Skill (`TypedCapability`, `kind: "skill"`)
- **Code Locations:** `operads/domain/capability_catalog_v1.py` (lines 166–230), `code/rust/core_operad_canon/src/types.rs` (lines 23–34), `operads/skill_operad/json/capability_catalog.v1.json`.
- **Data Representation:**
  ```python
  @dataclass(frozen=True, slots=True)
  class SkillCapabilityV1:
      skill_id: str
      name: str
      description: str
      source_path: str
      source_digest: str
      source_colours: tuple[str, ...]
      target_colour: str
      arity: int
      residual_effect: str
      invocation: str
      invocation_explicit: bool
      families: tuple[str, ...]
      declared_dependencies: tuple[str, ...]
      declared_triggers: tuple[str, ...]
  ```
- **Lifecycle Facets (5 Orthogonal Dimensions):**
  1. `lifecycle_declaration`: `Declared`, `Abstract`, `Synthesized`.
  2. `lifecycle_schema_binding`: `Unbound`, `Bound`, `AnySchema`.
  3. `lifecycle_executor_binding`: `Unbound`, `Bound`, `ExternalService`.
  4. `lifecycle_validation`: `Unchecked`, `Validated`, `Failed`.
  5. `lifecycle_admission`: `Unadmitted`, `Admitted`, `Retired`.
- **Invariants:**
  - `arity == len(source_colours)`.
  - Input and output colours must belong to the 10 canonical sorts defined in `core_operad_canon::OperadColour`.
  - Unbound executor declarations cannot declare host executor identifiers (`EXECUTOR_BINDING_REFUSED`).
- **Storage Reality:** 237 catalogued skill packages under `operads/skills/`.

---

### 3.2 Class 2: Anti-Skill (`AntiSkillSpecV2`)
- **Code Locations:** `code/rust/core_epistemic_immune_system/src/anti_skill.rs` (lines 14–71), `operads/canon/_generated.py`.
- **Data Representation:**
  ```rust
  pub struct AntiSkillSpecV2 {
      pub schema_version: String,
      pub id: String,
      pub pattern: String,
      pub failure_class: FailureClass,
      pub status: AntiSkillStatus,
      pub authority_effect: String,
      pub target_scope: String,
      pub description: String,
      pub creation_epoch: u64,
  }
  ```
- **Lifecycle States:**
  $$\text{Proposed} \xrightarrow{\text{Thymus Gate}} \text{Candidate} \xrightarrow{\text{Formulary / Human Gate}} \text{Admitted} \rightleftharpoons \text{Suspended} \to \text{Retired}$$
- **Invariants:**
  - `IMMUNE-001`: Constructor `AntiSkillSpecV2::propose()` initializes status exclusively to `AntiSkillStatus::Proposed`. There is no constructor argument allowing self-admission.
- **Storage Reality:** Ground-truth audit confirms **0 stored instances** of `anti_skill` records in the repository. The data types and gate infrastructure are fully implemented in Rust and Python, but live instances are represented as pharmacy records (`ab_*.json`) or authored specs (`anti_*.yaml`).

---

### 3.3 Class 3: Rule (`RuleDocument`, `RuleInvariant`)
- **Code Locations:** `operads/skill_operad/yaml/rules_registry.yaml`, `operads/skill_operad/skill_compiler/rule_gate.py`.
- **Data Representation:** YAML records structured under `core.oewas.rules_registry.v1`:
  - `path`: relative path within `operads/rules/`.
  - `topic`: category string.
  - `skills`: list of governing skill IDs.
  - `invariants`: list of `{ id: str, status: "ENFORCED" | "PARTIAL" | "CANDIDATE", enforced_by: Optional[str] }`.
- **Invariants:**
  - File size ceiling: `size_ceiling_bytes: 12000`.
  - Every invariant must declare a unique string identifier conforming to `RULE_<CATEGORY>_<NAME>_<NNN>`.
- **Storage Reality:** 50 rule markdown documents under `operads/rules/` carrying 144 invariants (28 `ENFORCED`, 12 `PARTIAL`, 104 `CANDIDATE`).

---

### 3.4 Class 4: Anti-Rule
- **Code Locations:** Carried operationally in `operads/patterns/anti/` and `eis/antibodies/`.
- **Data Representation:** No discrete code struct named `AntiRule` exists in the codebase. The concept is realized through:
  1. Anti-Pattern specifications (`AP_<LANG>_<NNN>`).
  2. Antibody specifications (`anti_*.yaml`).
  3. Pre-execution refusal gates (`inventory_anti_op`).
- **Invariants:** Execution stops immediately upon matching an anti-rule detector, returning a typed refusal code.

---

### 3.5 Class 5: Agent Role (`AgentRole`)
- **Code Locations:** `operads/registry/roles.yaml` (lines 4–68), `operads/domain/capability_catalog_v1.py` (lines 290–330).
- **Data Representation:**
  ```yaml
  <role_name>:
    licence:
    - <OperadColour>
  ```
- **Lifecycle:** Static registration. Each role possesses a cryptographic `license_digest` derived from its permitted colour set.
- **Invariants:**
  - An agent role may only invoke skills whose target colour and source colours are subsets of the role's licensed colour set (`SliceViolationError`).
- **Storage Reality:** Exactly **12 agent roles** declared:
  1. `auto-invariants-manager` (Audit, Ledger, Receipt, State)
  2. `blackrod` (Audit, Code, Contract)
  3. `code-testing` (Audit, Code, Receipt, State)
  4. `database` (State)
  5. `devops-git` (State)
  6. `dime-pedagogy` (Diagram, Ledger, Paper, Proof)
  7. `frontend-designer` (Code, Paper, Proof, State)
  8. `math-prof` (Code, Paper, Proof, State)
  9. `paper-builder` (Audit, Paper, Proof, Receipt)
  10. `python-dev` (Audit, Code, Receipt)
  11. `rust-dev` (Audit, Code)
  12. `thanatos` (Audit, Code, Contract, Receipt, State)

---

### 3.6 Class 6: Anti-Agent
- **Code Locations:** Realized through refusal terminal routing in `code/rust/core_types/src/routing.rs` and `skills/adversary-stale-task-antibody/SKILL.md`.
- **Data Representation:** No discrete code struct named `AntiAgent` exists. The operational function is fulfilled by terminal refusal objects (`RefusalReason`, `RefusedStatus`) that immediately kill rogue execution branches or abort subagent swarms when out-of-distribution drift or stale tasks are detected.

---

### 3.7 Class 7: Antibody Pharmacy Record
- **Code Locations:** `eis/antibodies/ab_*.json` (58 files), `code/rust/core_operad_canon/src/types.rs` (lines 528–586).
- **Data Representation:** JSON records implementing schema `core.pharmacy.antibody-record`:
  - `antibody_id`: e.g. `ab_19l57g1_001`.
  - `failure_class`: one of the 12 pharmacy failure classes (e.g. `SELF_CERTIFICATION`, `OPTIMALITY_HALLUCINATION`).
  - `target_pattern`: regex pattern.
  - `action`: `repair | abort | refuse`.
  - `constraint_type`: `ProjectOut | Restrain | Enforce`.
  - `operatorizability`: `repairable | fatal`.
  - `pharmacy_status`: `candidate | admitted | rejected | retired`.
  - `positive_fixture`, `negative_fixture`: exact text fixtures validating sensitivity and specificity.
- **Storage Reality:** 58 JSON tracking files active in `eis/antibodies/`.

---

### 3.8 Class 8: Authored Antibody Specification
- **Code Locations:** `eis/antibodies/anti_*.yaml` (37 files).
- **Data Representation:** YAML records implementing schema `core.immune.antibody-spec.v1`:
  - `canonical_name`: human-readable identifier.
  - `target_pattern`: compiled regex pattern.
  - `governing_invariants`: references to rule invariant IDs.
  - `adversarial_mutation_fixture`: positive test fixture that must trigger the antibody.
  - `repaired_invariant_fixture`: negative test fixture that must pass cleanly.
- **Storage Reality:** 37 YAML specifications in `eis/antibodies/`. 24 names overlap with pharmacy records (`ab_*.json`), but authored specs represent canonical rule bindings rather than empirical telemetry.

---

### 3.9 Class 9: DDC Operational Transitions (`DdcOp`)
- **Code Locations:** `code/rust/core_operad_canon/src/lib.rs` (lines 175–245), `types.rs` (lines 312–322).
- **Data Representation:** Closed 8-letter enumeration:
  ```rust
  pub enum DdcOp {
      ExactRepair,        // "E" — discharge defect outright (residual -> 0)
      ResidualProjection, // "R" — carry forward unremoved obstruction
      ContextExposure,    // "C" — declare/split carrier and active 2-window
      Integration,        // "I" — append verified delta to local ledger
      Lift,               // "Λ" — structural lift or extension
      Descent,            // "D" — descent / re-index
      Refusal,            // "M" — mutation / typed refusal
      Terminalize,        // "T" — record terminal status (AuthorityEffect: None)
  }
  ```
- **Invariants:** The 8 letters are closed. Every letter must match `DdcOp::LETTERS = ["E", "R", "C", "I", "Λ", "D", "M", "T"]`. Emitting `T` records a terminal status; it does not confer authority.

---

### 3.10 Class 10: DDC Repair Stages (`DdcRepairStage`)
- **Code Locations:** `operads/contracts/ddc_code_repair_v1.py` (lines 12–14, 126–135), `types.rs` (lines 323–334).
- **Data Representation:**
  ```python
  STAGES = ("C", "R", "E", "I", "M", "T")
  EXECUTOR_METHODS = tuple(zip(STAGES, (
      "capture", "observe", "evaluate", "incorporate", "disposition", "terminal"
  )))
  ```
- **Invariants:**
  - Bounded to 6 stages. Structural lift ($\Lambda$) and descent ($D$) are excluded from single-turn code repair because code repair modifies implementation within a fixed carrier rather than expanding representation dimension.

---

### 3.11 Class 11: DDC Degree Tower Operators (`DdaOperationKind`)
- **Code Locations:** `code/rust/core_wdp/src/ddc/degree_tower.rs` (lines 250–261).
- **Data Representation:**
  ```rust
  pub enum DdaOperationKind {
      SuccessorProbe,
      ResidualUpdate,
      CarrierLift,
  }
  ```
- **Invariants:**
  - Evaluated on binary cochain complexes.
  - `CarrierLift` repairs by changing the carrier space (pulling back to a covering where the class is exact) rather than updating residual within the existing space. Genuine cohomology classes (`StabilizedSurvivor`) cannot be repaired by `ResidualUpdate`.

---

### 3.12 Class 12: Helpful Pattern (HP)
- **Code Locations:** `operads/patterns/helpful/` (94 files across `python/`, `rust/`, `markdown/`, `math/`).
- **Data Representation:** Markdown contracts (`HP_<LANG>_<NNN>_<NAME>.md`) declaring:
  - Canonical language idiom.
  - Positive code examples.
  - Corresponding anti-pattern ID.
- **Storage Reality:** 94 files.

---

### 3.13 Class 13: Anti-Pattern (AP)
- **Code Locations:** `operads/patterns/anti/` (93 files across `python/`, `rust/`, `markdown/`, `math/`).
- **Data Representation:** Markdown contracts (`AP_<LANG>_<NNN>_<NAME>.md`) declaring:
  - Negative defect template.
  - Paired helpful pattern reference.
  - Regex or AST detection pattern.
- **Storage Reality:** 93 files (paired by index with HP; 3 unpaired).

---

### 3.14 Class 14: Inventory Op (`inventory_op`)
- **Code Locations:** `operads/skill_operad/yaml/op_inventory.yaml` (lines 16–257), `types.rs` (lines 276–286).
- **Data Representation:** Host-bound tool executions:
  `ara.bind_source_hashes`, `ara.receipt`, `ara.refute`, `glossa.merge_hits`, `glossa.propose_replacements`, `glossa.report`, `glossa.scan_hype_code`, `glossa.scan_hype_prose`, `gti.layout_check`, `gti.receipt`, `gti.shadow_scan`, `mnc.gate`, `mnc.purge`, `sfh.report`, `sfh.scan`.
- **Storage Reality:** Exactly 15 declared ops across 5 foundational skills.

---

### 3.15 Class 15: Inventory Anti-Op (`inventory_anti_op`)
- **Code Locations:** `operads/skill_operad/yaml/op_inventory.yaml`, `types.rs` (lines 287–298).
- **Data Representation:** Host pre-execution refusal triggers:
  `ara.refuse_undeclared_omission`, `ara.refuse_unrecomputed_hash`, `glossa.refuse_missing_claim_envelope`, `gti.refuse_duplicate_test_basename`, `gti.refuse_sys_path_hack`, `sfh.refuse_bare_except`, `sfh.refuse_pass_handler`, `sfh.refuse_rust_unwrap`.
- **Storage Reality:** Exactly 8 declared anti-ops.

---

### 3.16 Class 16: Prompt Anti-Op Detector (`prompt_anti_op`)
- **Code Locations:** `operads/domain/prompt_hierarchy/evaluator.py` (lines 28–58), `types.rs` (lines 299–310).
- **Data Representation:** Built-in keyword patterns checking for smuggled continuum axioms or proxy theorems:
  1. `pfp.refuse_unlicensed_multiplication`
  2. `pfp.refuse_unlicensed_causality`
  3. `pfp.refuse_unmapped_continuum_import`
  4. `pfp.refuse_scalar_proxy_theorem_substitution`
  5. `pfp.refuse_target_fitting_constant_compensation`
  6. `pfp.refuse_witness_certificate_desynchronization`
  7. `glossa.refuse_missing_claim_envelope`
- **Storage Reality:** 7 built-in detector routines.

---

### 3.17 Class 17: Coloured Operad Operation
- **Code Locations:** `code/rust/core_operad_theory/src/foundation/operation.rs` (lines 16–100).
- **Data Representation:**
  ```rust
  pub enum OperationKind {
      Identity { colour: OperadColour },
      Generator,
      Composite { term_hash: String },
  }

  pub struct Operation {
      pub op_id: OperationId,
      pub signature: OperadSignature,
      pub kind: OperationKind,
      pub is_equivariant: bool,
  }
  ```
- **Invariants:** Every operation has a unique `OperationId`, declares a sort signature $(c_1, \ldots, c_n; c)$, and validates that composite term hashes uniquely identify the derivation tree.

---

### 3.18 Class 18: Prompt Operad Tree Nodes
- **Code Locations:** `pfp/domain/operad/prompt.py` (lines 18–142).
- **Data Representation:**
  - `PromptColour`: `RawTextSpan`, `Equation`, `IsolatedVariable`, `SubstitutionStep`, `RationalValue`, `InvariantWitness`, `TargetResult`.
  - `LeafTextSpan`: immutable slice of source document with start/end byte offsets and SHA-256 digest.
  - `OperadTreeNode`: composite tree node holding `operator: PromptOperator` and `children: tuple[OperadTreeNode | LeafTextSpan | NullTree, ...]`.
  - `NullTree`: terminal failure tree carrying `ideal_id`, `reason`, and `target_colour`.
- **Invariants:**
  - Span immutability: `LeafTextSpan.verify_against_document()` raises `ValueError` if the slice text does not match the original document.
  - Grafting boundary sort match: `OperadTreeNode.graft(slot, child)` validates that the child's output colour matches the operator's expected source colour at `slot`.

---

### 3.19 Class 19: Planar Graft Operator (`PlanarGraft`)
- **Code Locations:** `pfp/domain/operad/graft.py` (lines 18–105).
- **Data Representation:**
  ```python
  class GraftSite(str, enum.Enum):
      VERTEX = "VERTEX"  # Single generator validity
      EDGE = "EDGE"      # Partial composition seam (f circle_i g)
      TREE = "TREE"      # Whole-tree circularity and boundary nilpotency

  @dataclass(frozen=True)
  class PlanarGraft:
      site: GraftSite
      target_id: str
      morphism_name: str
      seam_index: int | None = None
      expected_type: str | None = None
      actual_type: str | None = None
  ```
- **Invariants:**
  - `EDGE` graft site requires non-null `seam_index`.
  - Whole-tree `TREE` graft checks circular dependencies (`has_circular_dependency == False`) and boundary nilpotency (`boundary_leakage == 0`).

---

### 3.20 Class 20: Polarized Operad Morphisms (`PolarizedOperadTriad`)
- **Code Locations:** `pfp/domain/operad/operad.py` (lines 27–152), `pfp/domain/operad/morphisms.py`.
- **Data Representation:** Aggregate root maintaining strictly partitioned sub-operads:
  - `constructive`: $O^+$ (`ConstructiveMorphism`)
  - `interrogative`: $O^-$ (`InterrogativeMorphism`)
  - `corrective`: $O_{repair}$ (`RepairMorphism`)
- **Invariants:**
  - Partial composition $f \circ_i g$ is strictly restricted to constructive morphisms ($O^+$). Attempting partial composition on interrogative or corrective morphisms raises `OperadRoleViolationError`.
  - Agent roles require licensed slices (`check_slice_permission`).

---

### 3.21 Class 21: Instruction and Obstruction Operands
- **Code Locations:** `operads/domain/value_objects/operands.py` (lines 13–85), `code/rust/core_operad_theory/src/foundation/span_operand.rs` (lines 18–72), `operads/catalog/operands/v1/adversary/`.
- **Data Representation:**
  - `InstructionOperand`: declared instruction clause bound to a `SourceByteSpan`.
  - `SpanOperand`: exact UTF-8 byte span with start/end lines, byte offset/length, SHA-256 digest, and assigned `OperadColour`.
  - `ObstructionOperand`: typed defect carrying diagnostic class and failure class.
- **Invariants:**
  - UTF-8 clean without BOM (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
  - 4 instruction operands in repo: `checker_receipt_required.md`, `claim_hygiene.md`, `critic_json_only.md`, `fixture_never_authorizes.md`.
  - 7 registered operands in canon: `op_exact_cochain_coboundary_repair`, `op_f2_gauge_board_classification`, `op_meron_surgery_sign_inversion`, `op_unpromoted_candidate_template`, `op_adversary_hermetic_task_evidence_attestation`, `op_adversary_strict_typed_input_refusal`, `op_lean4_constructive_kernel_axiom_audit`.

---

### 3.22 Class 22: Prompt Civilization Antimorphisms
- **Code Locations:** `code/rust/core_prompt_civilization/src/antimorphism.rs` (lines 22–110).
- **Data Representation:** Exact 3-way verdict detectors:
  1. `ExactOrbitSumDetector` (`AM-FSP-4-ORBIT-SUM-MISMATCH`): verifies $w_0 - w_1 = 0$ using `num_rational::BigRational`.
  2. `ExactSignInvolutionDetector` (`AM-5-SIGN-INVOLUTION`): verifies parity involution coordinates.
  3. `StationaryRepeatDetector` (`AM-4-STATIONARY-REPEAT`): detects uncontracted cycle repeats.
- **Invariants:** Emits `AntimorphismVerdict`: `ConfirmedHallucination`, `GroundedWitness`, or `CandidateRegexOnly`. Scripted test rows cannot be exported as live model evidence.

---

### 3.23 Class 23: Prompt Forge Mutation Engine
- **Code Locations:** `code/rust/core_prompt_civilization/src/forge.rs` (lines 18–180, 240–290).
- **Data Representation:**
  - `PromptMutationEngineV1`: applies bounded edits to raw prompt byte vectors.
  - `ProtectedSpanV1`: immutable byte range (`name`, `start_byte`, `end_byte`).
  - `PopulationPolicyV1::allocate_reserves`: largest-remainder integer reserve allocation (60% exploited, 30% maturing, 10% unmeasured exploration).
- **Invariants:**
  - `F-BIO-03`: Editing or inserting into a protected span raises `PROTECTED_SPAN_MUTATION_REFUSED`.
  - `MAX_ORGANIZE_BYTES = 1,048,576` (1 MiB ceiling).
  - `original_seed` span is locked from byte 0 to `seed.len()`.

---

### 3.24 Class 24: Epistemic Sieve Trap Detectors
- **Code Locations:** `code/rust/core_types/src/epistemic_sieve.rs` (lines 3–50).
- **Data Representation:** Closed enumeration of 47 diagnostic traps, including:
  `HiddenBoundaryCondition`, `CategoryTheoryLexiconViolation`, `CircularFormalism`, `SignSmoothingRegression`, `PrematureHypothesisCollapse`, `ConstructorCounterfactualViolation`, `FloerWallCrossingViolation`, `GravitationalAnomaly`, `PrematureSheafification`, `SwamplandPathology`.
- **Invariants:**
  - Emits `TrapAlert` and evaluates to `EpistemicVerdict`: `Constructed`, `Plausible`, `Falsified`, `SignObstruction`, `SovereignMirror`, `TopologicallyIrreducible`.

---

## 4. Built Code Reality vs. Aspirational Text

To preserve empirical integrity, the following table contrasts the actual code state against aspirational documentation:

| Domain | What the Code Actually Implements | What Comments / Aspirational Docs Claim | Ground Truth Reality |
|---|---|---|---|
| **Anti-Skills** | Rust struct `AntiSkillSpecV2`, enum `AntiSkillStatus`, Thymus gate screen | A vast empirical repository of harvested anti-skills | **0 stored anti-skill files** exist in repo. Types and gates exist, but data store is empty. |
| **Anti-Rules** | Pattern matching via AP contracts and antibody YAML | Dedicated anti-rule algebra and compiler | No separate `AntiRule` type exists; functionality is subsumed by anti-patterns and refusal gates. |
| **Agent Roles** | 12 static role declarations in `roles.yaml` mapping to colour licences | Dynamic swarms of hundreds of autonomous agents | Only 12 roles are registered; no autonomous agent JSON instances exist in the catalog. |
| **Prompt Decomposition** | `core_prompt_civilization/src/prompt_family.rs` parent chains & planar operad trees | Active legacy modules `p_star_builder.py` and `tree.py` | Legacy decomposition modules were **deleted on 2026-10-10** (`e6537cc3cf`); contracts survive as schemas. |
| **Authority Minting** | `AuthorityEffect: None` explicitly hardcoded across all structs and terminals | Model self-governance or autonomous decision-making | Every operator runs fail-closed; no candidate proposal can grant itself execution authority. |

---

## 5. Claim Hygiene Analysis

### 1. What This Taxonomy Supports:
- Provides an exhaustive, code-grounded catalog of all 24 operator and operand classes implemented in the PFP repository.
- Documents exact file paths, type definitions, invariants, and storage counts.
- Verifies that the codebase implements strict fail-closed boundary enforcement across operadic sorts and DDC transitions.

### 2. What This Taxonomy Does Not Support:
- Does not show that language models possess intrinsic semantic understanding or self-verification capability.
- Does not demonstrate that the 237 catalogued skills are error-free or universally composable.
- Does not grant operational authority to candidate proposals outside declared host test oracles.

### 3. The Narrowest Defensible Claim:
The PFP codebase contains a settled, deterministic taxonomy of 24 operator and operand classes spanning coloured operads, discrete deformation calculus, and epistemic immune monitoring, all operating under `AuthorityEffect: None`.

### 4. The Next Test Needed:
Automated round-trip schema validation between `operads/skill_operad/json/capability_catalog.v1.json` and Rust crate `core_operad_canon` to ensure zero drift across the 24 classes.
