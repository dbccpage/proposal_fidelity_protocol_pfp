# Comprehensive Code-Grounded Survey of Proposal Fidelity Protocol (PFP)

**Repository:** `proposal_fidelity_protocol_pfp` (`c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp`)  
**Investigating Agent:** `teamwork_explorer_survey_1`  
**Governing Standard:** Claim Hygiene Rule, Ground Truth Discipline, `AuthorityEffect: None`  
**Scope:** Operator Taxonomy, Prompt Families & Lineage, Epistemic Immune System (EIS), Prompt Sieve (P Sieve), and Workflow Architectures.

---

## 1. Executive Summary & Repository Anatomy

This report documents the actual code and data structures implemented in `proposal_fidelity_protocol_pfp`, distinguishing strictly between executable implementations, data assets, and aspirational or retired specifications.

### Key Architectural Estates
1. **The Coloured Operad Spine (`operads/`, `code/rust/core_operad_canon`, `code/rust/core_operad_theory`):**
   - Single point of truth for types: Rust crate `code/rust/core_operad_canon/src/types.rs` defines 56 canonical types (49 settled, 7 proposed) across 6 families.
   - Generated downstream bindings: Python enum module `operads/canon/_generated.py` and JSON mirror `operads/canon/operad_canon.json`.
   - 237 catalogued skill packages in `operads/skills/` mapped to colour signatures `(sources) -> target` over 10 canonical colours.
2. **Epistemic Immune System (EIS) (`eis/`, `code/rust/core_epistemic_immune_system`):**
   - Four-Gate Epistemic Immune Protocol in Rust and Python: Defect Observation $\to$ Thymus Central Tolerance $\to$ Two-Signal Danger Gating $\to$ Human Admission Fence.
   - Dual-store antibody representations: 58 pharmacy tracking records (`eis/antibodies/ab_*.json`), 37 authored YAML specifications (`eis/antibodies/anti_*.yaml`), and 1,069 candidate catalog entries (`eis/antibodies/pharmacy_catalog.json`).
   - Two-Signal Danger Gate enforcing strict independence between detector match (Signal 1) and external host damage (Signal 2) to prevent `TWO_SIGNAL_COLLAPSE`.
3. **Prompt Civilization & Evolution Engine (`code/rust/core_prompt_civilization`):**
   - Reader-relative prompt families (`PromptFamily` DAG) with multi-parent lineage tracking bounded to `max_depth <= 5`.
   - Discrete Deformation Calculus (DDC) step execution recording residual color transitions (`Open`, `Closed`, `Exact`) and DDC letters (`E, R, C, I, Λ, D, M, T`).
   - Append-only prompt organization (`forge_organize_prompt`) with immutable protected spans (`ProtectedSpanV1`) enforcing `PROTECTED_SPAN_MUTATION_REFUSED`.
4. **PFP Workflows (`workflows/`, `pfp/workflows/`):**
   - 49 defined workflows: WF1 to WF5 are fully implemented and runnable (with offline fixtures and live API runners); WF6 to WF49 are detailed architectural designs with dependency DAGs.
   - Host verification discipline: Independent exact checkers (e.g. `integer_sum_judge`) enforce fail-closed evaluation; model self-certification (`"verified": true`) is ignored.

---

## 2. Comprehensive Operator Taxonomy

The codebase defines and utilizes a rich hierarchy of operators. Reading directly from the type table in `code/rust/core_operad_canon/src/types.rs`, `wiki/Operads-Type-Inventory.md`, and domain models across Rust and Python, we identify 22 distinct operator and operand classes:

### Summary Table of Operator Classes

| Operator / Entity Class | Implementation Location | Data Structure / Type | Interface / Methods | Lifecycle & Cardinality |
|---|---|---|---|---|
| **1. Skill** | `operads/skills/*/SKILL.md`, `capability_catalog.v1.json` | `TypedCapability` (`kind: "skill"`) | Markdown contract, YAML frontmatter, execution schema | 237 catalogued packages; 5 lifecycle facets (Declared, Bound, Bound, Validated, Admitted) |
| **2. Anti-Skill** | `code/rust/core_epistemic_immune_system/src/anti_skill.rs`, `operads/domain/anti_skills/` | `AntiSkillSpecV2` (Rust), `AntiSkillV2` (Python) | `pattern`, `failure_class`, `screen()`, `retire()` | Type implemented; 0 stored instances in repo. Statuses: `Proposed -> Candidate -> Admitted -> Suspended -> Retired` |
| **3. Rule** | `operads/rules/`, `rules_registry.yaml` | `RuleDocument`, `RuleInvariant` | YAML invariant definitions: `enforced`, `partial`, `candidate` | 50 rule documents carrying 144 invariants (28 enforced, 12 partial, 104 candidate) |
| **4. Anti-Rule** | *Not a discrete code type* | Carried by Anti-Patterns (`AP_*`) and Antibodies | Pattern matching and execution gating | 0 separate types in code; function fulfilled by negative components |
| **5. Agent** | `operads/registry/roles.yaml` | `AgentRole` (role with colour licence) | Input/output colour permissions, tool permissions | 12 declared roles (e.g., `python-dev`, `rust-dev`); 0 catalogued agents in JSON |
| **6. Anti-Agent** | *Not a discrete code type* | Branch termination via typed refusal | `RefusalReason` / `RefusedStatus` stopping harmful execution branches | 0 separate types in code; operational concept cited in `adversary-stale-task-antibody` |
| **7. Antibody (Pharmacy Record)** | `eis/antibodies/ab_*.json` | JSON dictionary (`core.pharmacy.antibody-record`) | `target_pattern`, `action`, `positive_fixture`, `negative_fixture` | 58 records in repo; statuses: `candidate`, `admitted`, `rejected`, `retired` |
| **8. Antibody (Authored Spec)** | `eis/antibodies/anti_*.yaml` | YAML contract (`core.immune.antibody-spec.v1`) | Regex `target_pattern`, `adversarial_mutation_fixture`, `repaired_invariant_fixture` | 37 authored specs in repo; bound to governing invariant rules |
| **9. DDC Operational Transitions** | `code/rust/core_operad_canon/src/lib.rs` | `enum DdcOp` (`E, R, C, I, Λ, D, M, T`) | `letter()`, `from_letter()`, `alphabet()` | 8 closed letters representing lawful cochain transitions |
| **10. DDC Repair Stages** | `operads/contracts/ddc_code_repair_v1.py` | `DdcRepairStage` (`C, R, E, I, M, T`) | Bounded repair stage machine | 6 stages (structural lift $\Lambda$ and descent $D$ excluded) |
| **11. DDC Degree Tower Operators** | `code/rust/core_wdp/src/ddc/degree_tower.rs` | `enum DdaOperationKind` | `SuccessorProbe`, `ResidualUpdate`, `CarrierLift` | 3 degree-tower operation kinds |
| **12. Helpful Pattern (HP)** | `operads/patterns/helpful/` | `HP_<LANG>_<NNN>` markdown contracts | Structural code/prose idiom contracts | 94 files across Python, Rust, Markdown, Math |
| **13. Anti-Pattern (AP)** | `operads/patterns/anti/` | `AP_<LANG>_<NNN>` markdown contracts | Defect detection templates (paired with HP) | 93 files across languages (paired by number, 3 unpaired) |
| **14. Inventory Op** | `operads/skill_operad/yaml/op_inventory.yaml` | `inventory_op` string IDs | Host tool execution: `glossa.*`, `gti.*`, `ara.*`, `mnc.*`, `sfh.*` | 15 declared ops across 5 foundational skills |
| **15. Inventory Anti-Op** | `operads/skill_operad/yaml/op_inventory.yaml` | `inventory_anti_op` string IDs | Refusal triggers: `sfh.refuse_bare_except`, `gti.refuse_sys_path_hack`, etc. | 8 declared anti-ops enforcing hygienic execution |
| **16. Prompt Anti-Op Detectors** | `operads/domain/prompt_hierarchy/evaluator.py` | `prompt_anti_op` identifiers | AST/keyword scan for prompt laundering or smuggled axioms | 7 built-in detectors (`glossa.refuse_*`, `pfp.refuse_*`) |
| **17. Coloured Operad Operation** | `code/rust/core_operad_theory/src/foundation/` | `Operation` (`Identity`, `Generator`, `Composite`) | Multi-colour composition, arity checking | Fundamental building block of operadic algebra |
| **18. Prompt Operad Tree Nodes** | `pfp/domain/operad/prompt.py` | `OperadTreeNode`, `LeafTextSpan`, `NullTree` | `graft(slot, child)`, `verify_against_document()` | Planar tree nodes typing prompt spans with 7 prompt colours |
| **19. Planar Graft Operators** | `pfp/domain/operad/graft.py` | `PlanarGraft`, `enum GraftSite` (`VERTEX`, `EDGE`, `TREE`) | `evaluate_invariants(context)` checking generator, seam, and cycle | 3 canonical graft sites for interrogative checks |
| **20. Polarized Operad Morphisms** | `pfp/domain/operad/operad.py` | `ConstructiveMorphism` ($O^+$), `InterrogativeMorphism` ($O^-$), `RepairMorphism` ($O_{repair}$) | `register_*()`, `partial_compose()`, `grant_slice()` | Strictly partitioned triad governing proposal, audit, and repair |
| **21. Instruction & Obstruction Operands** | `operads/catalog/operands/v1/`, `operads/domain/value_objects/operands.py` | `InstructionOperand`, `ObstructionOperand` | Addressable source byte span + typed operation | 4 instruction operands in repo; 7 obstruction operands declared |
| **22. Prompt Civilization Antimorphisms** | `code/rust/core_prompt_civilization/src/antimorphism.rs` | Antimorphism detectors | Orbit-sum mismatch, sign inversion, stationary repeat | 3 exact 3-way verdict detectors on prompt evolution |
| **23. Prompt Forge Mutation Engine** | `code/rust/core_prompt_civilization/src/forge.rs` | `PromptMutationEngineV1`, `PopulationPolicyV1` | `organize_prompt()`, `apply_mutation()`, `allocate_reserves()` | Append-only organization; protected span immutability |
| **24. Epistemic Sieve Trap Detectors** | `code/rust/core_types/src/epistemic_sieve.rs` | `enum TrapDetector` | 47 discrete detector variants (e.g. `HiddenBoundaryCondition`, `GravitationalAnomaly`) | Emits `TrapAlert` and `EpistemicVerdict` |

---

## 3. Prompt Families, Prompt Lineage, Domains & DDC

### 3.1 Prompt Family Data Structures
Defined identically in Rust (`code/rust/core_prompt_civilization/src/prompt_family.rs`) and Python (`ops/adversary/domain/prompt_family.py`):

```rust
pub struct PromptFamily {
    pub readers: Vec<Reader>,
    pub nodes: Vec<PromptNode>,
    pub calls: Vec<CallRecord>,
    pub steps: Vec<RepairStep>,
    pub terminal: Option<Terminal>,
}
```

Key sub-structures:
- **`Reader`**: Defines the observing model environment (`model`, `router`, `seat_id`, `tier`, `config_digest`, `temperature`, `params_billion`, `open_weights`). A prompt text read by two different readers constitutes two distinct `PromptNode`s.
- **`PromptNode`**: Represents a prompt instance.
  - `prompt_digest`: SHA-256 of the prompt text.
  - `relation`: Strictly `"root" | "contains" | "repaired_from"`.
  - `parent_id`: Option referencing the parent node id.
  - `reader_digest`: Option identifying the declared reader.
  - `domain_labels`: Vector of `DomainLabel` records (`label`, `proposer_reader`, `status`: `"proposed" | "checked"`, `check_receipt`).
- **`CallRecord`**: Captures every generative call (including failures). Tracks `bout_id`, `request_digest`, `leg_index`, `outcome`, `cost_microusd`, `input_tokens`, `output_tokens`, `ddc_letter`, `residual_colour`.
- **`RepairStep`**: Links `input_node_id` to `output_node_id`, accompanied by:
  - `ddc_letter`: One of `"E", "R", "C", "I", "Λ", "D", "M", "T"`.
  - `residual_before` and `residual_after`: One of `"Open", "Closed", "Exact"`.
  - `fitness`: Vector containing `cost_microusd`, `input_tokens`, `output_tokens`, `checker_verdict` (`"ACCEPT" | "REJECT" | "NOT_MEASURED"`), `checker_id`, and `obstruction_removed: Option<bool>`.
- **`Terminal`**: The terminal status of the family: `"Repaired" | "BudgetExhausted" | "TypedResidual"`.

### 3.2 Invariants Enforced by `validate_family`
1. **Root Cardinality:** A family must contain exactly one root node (`relation == "root"`).
2. **Parent Invariant:** The root node has no parent; every non-root node MUST have a parent.
3. **Acyclicity:** `validate_parent_chain` traverses parent links to ensure zero cycles (`FAMILY_CYCLE`).
4. **Checker Anti-Circularity:** If `checker_verdict != "NOT_MEASURED"`, a `checker_id` is mandatory and cannot be one of the step's own readers (`FAMILY_FITNESS_CIRCULAR`).
5. **Terminal Repair Integrity:** A terminal kind of `"Repaired"` is refused unless the final repair step has `fitness.checker_verdict == "ACCEPT"` and `residual_after == "Exact"`.
6. **Budget Termination Detail:** If `terminal.kind == "BudgetExhausted"`, `terminal.detail` must start with `"BUDGET_"`.

### 3.3 Domain, Subdomain, and Sub-subdomain Scoping
Hierarchical domain classification is governed by `code/rust/core_prompt_civilization/src/domain.rs`:
- **Domain Placement (`DomainPlacementV1`):** Holds `placement_id`, `content_digest`, `domain_assignment`, `read_scope`, and `disposition`.
- **Scope Covering Algorithm (`scope_covers`):**
  Matches exact domain names or wildcard prefix hierarchies:
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
  *Example:* Scope `math.*` automatically covers subdomains `math.algebra` and sub-subdomains `math.algebra.cochains`.
- **Hard Eligibility Invariant (`F-DOMAIN-01`):**
  Taxonomy recognition alone never grants admission. `hard_domain_eligible` requires `placement.disposition == "ADMITTED_LOCAL"` AND `query_domain in read_scope`.

### 3.4 Removing Obstruction vs. Creating Structure
In the DDC algebra:
- **Creating Structure:**
  - `C` (Context Exposure): Declares the carrier boundary and active 2-window.
  - `Λ` / `Meta` (Structural Lift): Elevates the representation complex. Enforces that a lift trigger is not a lift license: requires obstruction, preservation, and non-destruction witnesses plus a terminalizer route.
  - `D` (Descent): Refines the indices or window.
- **Removing Obstruction:**
  - `E` (Exact Repair): Discharges the defect outright, driving residual to zero (`residual -> 0`).
  - `R` (Residual Projection): Carries forward irreducible obstruction mass.
  - `I` (Integration): Appends verified delta to the local ledger.
  - `M` (Refusal): Emits a closed refusal code when obstruction cannot be removed.
  - `T` (Terminalize): Seals the status without minting sovereign authority (`AuthorityEffect: None`).

---

## 4. Epistemic Immune System (EIS): Code Reality vs. Spec

### 4.1 The Four-Gate Epistemic Immune Protocol
Implemented in `code/rust/core_epistemic_immune_system/`:
1. **Gate 1: Defect Observation $\to$ `AntiSkillSpecV2` (Status = `Proposed`)**
   - Implemented in `anti_skill.rs`.
   - Constitutional Invariant `IMMUNE-001`: A newly harvested motif constructor explicitly sets `status = AntiSkillStatus::Proposed`. There is no constructor argument allowing self-admission.
2. **Gate 2: Central Tolerance Screen (`ThymusGate`)**
   - Implemented in `thymus.rs`.
   - Law 2: An anti-skill that triggers on any sample in the sealed self-panel is killed immediately (`ThymusVerdict::SelfReactive`).
   - Only surviving, non-self-reactive detectors advance to `Candidate` status.
3. **Gate 3: Two-Signal Danger Gating (`TwoSignalDangerGate`)**
   - Implemented in `danger_gate.rs` (Rust) and `eis/domain/danger_gate.py` (Python).
   - Constitutional Invariant `IMMUNE-002`: Strict four-part conjunction required for activation:
     $$\text{externally\_admitted}(g, s) \land \text{detector\_match}(g, \text{subject}) \land \text{independent\_danger\_signal}(\text{subject}) \land \neg\text{suspended}(g, s)$$
   - Hard Refusal: Treating Signal 1 (detector match) as its own Signal 2 (danger) raises `TWO_SIGNAL_COLLAPSE`.
4. **Gate 4: External Human Admission Fence (`Formulary` / `ExternalAdmissionRequest`)**
   - Implemented in `formulary.rs` and `admission.rs`.
   - Transitioning `Candidate` $\to$ `Admitted` requires a cryptographic external admission receipt (`AdmissionReceiptV1`) signed by an external human or sovereign authority.

### 4.2 Antibody Data Stores in the Repository
The repository contains two distinct file representations of antibodies that serve different roles:
1. **Pharmacy Tracking Records (`eis/antibodies/ab_*.json` - 58 files):**
   - Schema: `action`, `antibody_id`, `constraint_type`, `description`, `evidence_sha256`, `failure_class`, `negative_fixture`, `operatorizability`, `pharmacy_status`, `positive_fixture`, `severity`, `source_file`, `target_pattern`.
   - Used by the operational screening runner to evaluate historical test fixtures and track times seen.
2. **Authored Antibody Specifications (`eis/antibodies/anti_*.yaml` - 37 files):**
   - Schema: `core.immune.antibody-spec.v1` (`canonical_name`, `target_pattern` regex, `governing_invariants`, `adversarial_mutation_fixture`, `repaired_invariant_fixture`, `source_pilot`).
   - Represents the canonical authored rule binding. 24 names overlap with `ab_*.json` but differ in fixture representation and field semantics.
3. **Mined Candidate Catalog (`eis/antibodies/pharmacy_catalog.json` - 1,069 entries):**
   - Raw harvested failure candidates awaiting central tolerance screening and admission.

### 4.3 Detection Mechanics in Python and Native Rust
- **Python Reference (`eis/infrastructure/mssn_pharmacy.py`):**
  Runs 12 failure classes: `SELF_CERTIFICATION`, `FAKE_RECEIPT`, `CONCLUSION_PRELOAD`, `SCHEMA_SEMANTIC_LAUNDERING`, `THEOREM_NAME_LAUNDERING`, `OPTIMALITY_HALLUCINATION`, `COMPLEXITY_HALLUCINATION`, `BRANCH_DROP_EXHAUSTION`, `PERSONA_AUTHORITY_LEAK`, `PRIVATE_COT_DEPENDENCY`, `VERSION_DUPLICATION`, `DETECT_REPAIR_COUPLING`.
  - Walks strings and object keys.
  - Flags forbidden host-only keys (`verified`, `all_tests_passed`, `status_code`).
  - Detects superlative claims lacking lower bounds (`OPTIMALITY_HALLUCINATION`).
  - Flags private CoT dependencies (`PRIVATE_COT_DEPENDENCY`).
  - `PERSONA_AUTHORITY_LEAK` is Python-only; native Rust runs the other 11 classes.
- **Native Rust (`code/rust/core_prompt_civilization/src/pharmacy.rs`):**
  High-performance AST and token stream scanner compiled into sovereign host binaries.

---

## 5. Prompt Sieve (P Sieve): Ingestion, Decomposition & Evolution

### 5.1 Seed Ingestion & Forge Organization
Implemented in `code/rust/core_prompt_civilization/src/forge.rs`:
- Function `organize_prompt(payload)`:
  - Ingests raw untrusted stimulus $P$ via `OrganizePromptInput { seed, task, constraints, acceptance, response_contract }`.
  - Enforces byte limit: `MAX_ORGANIZE_BYTES = 1,048,576` (1 MiB).
  - Establishes immutable protected span `original_seed` (`start_byte: 0, end_byte: seed.len()`).
  - Appends declared sections (`task`, `constraints`, `acceptance criteria`, `response contract`) wrapped in `[FORGE DECLARED ...]` boundaries.
  - Returns canonical `request_sha256`, `seed_sha256`, `organized_sha256`, and protected span array.
- Invariant `F-BIO-03`: `PromptMutationEngineV1::apply_mutation` strictly checks that no mutation overlaps or zero-width inserts into a protected span; violations raise `PROTECTED_SPAN_MUTATION_REFUSED`.

### 5.2 Nested Prompt Decomposition & Containment Law
- **Theoretical Contract:**
  Specified in `education/004_oepfp/docs/21_prompt_template_contracts_and_single_prompt_standard.md`:
  $$P \mapsto P^* \to \{p_i\}_{i=1}^k$$
  $$\text{cardinality}(n) = 1 + \sum_{c \in \text{children}(n)} \text{cardinality}(c)$$
  - Root $P^*$ declares subprompts via `decomposition.subprompts` with contiguous ordinals $o_i = i$.
  - All decomposed children share the root's `generation_id` (co-generation event) and record `parents[0] = { prompt_id: ID(P*), relationship: "decompose" }`.
- **Code Ground Truth Audit:**
  As acknowledged in monograph `21_prompt_template_contracts` (lines 33-36), legacy modules `p_star_builder.py`, `tree.py`, and `adapters.py` (which lived under `education/pfp/python/`) were deleted on 2026-10-10 (`e6537cc3cf`).
  In the current repository, prompt decomposition is mediated by:
  1. `core_prompt_civilization/src/prompt_family.rs`: Validates tree structure via `validate_parent_chain`, enforcing DAG relationships `"root" | "contains" | "repaired_from"`.
  2. Categorical Coloured Operad (`pfp/domain/operad/prompt.py`): Models prompts as planar operad trees (`OperadTreeNode`, `LeafTextSpan`, `NullTree`) with grafting operations (`graft`) checking sort compatibility over 7 prompt colours (`RawTextSpan`, `Equation`, `IsolatedVariable`, `SubstitutionStep`, `RationalValue`, `InvariantWitness`, `TargetResult`).

### 5.3 Prompt Evolution, Genealogy & Lamarckian Cochains
- **Genealogy DAG (`code/rust/core_prompt_civilization/src/genealogy.rs`):**
  - Traversal bounded by `max_depth <= 5` (`GenealogyError::DepthBoundExceeded`).
  - Invariant `F-LINEAGE-01`: Edges exist only for witnessed causal relations (`InheritanceRelationship`: `DirectMutation`, `Repair`, `Retry`). Matching text or semantic objectives alone never creates an edge.
  - Each inheritance edge must bind a cryptographic `witness_receipt_digest`.
- **Population Allocation (`code/rust/core_prompt_civilization/src/forge.rs`):**
  - Invariant `F-BIO-05`: `PopulationPolicyV1::allocate_reserves` uses largest-remainder integer allocation. Target proportions: 60% exploited, 30% maturing, 10% unmeasured exploration.
- **Fitness & Lamarckian Cochains (`code/rust/core_prompt_civilization/src/fitness.rs`, `lamarckian.rs`):**
  - Exact rational Pareto frontier computation (`pareto_frontier_rational`) using `num_rational::BigRational`.
  - Cochain history tracker (`LamarckianCochainTrackerV1`) records primal-dual residual progression across prompt repair generations.

---

## 6. Workflow Architectures (WF1 to WF49)

The workflow estate is organized in `workflows/` and `pfp/workflows/`:

### 6.1 Runnable Implementations (WF1–WF5)
1. **WF1: Typed Answer (`wf01_typed_answer` / `pfp/workflows/wf0001`):**
   - **Goal:** One schema-valid answer accepted by the host check, or a typed refusal.
   - **Mechanics:** `PfpTaskPrompt` frozen; single solver reply; parsed into typed envelope; verified by independent host judge (e.g. `integer_sum_judge`).
2. **WF2: Full Slots (`wf02_full_slots` / `pfp/workflows/wf0002`):**
   - **Goal:** Complete slot record plus accepted answer.
   - **Mechanics:** Requires every declared slot $s$ to carry a typed value or explicit typed absence.
3. **WF3: Mine, Then Solve (`wf03_mine_then_solve` / `pfp/workflows/wf0003`):**
   - **Goal:** Frozen operation guidance, followed by an accepted solve.
   - **Mechanics:** Mining stage proposes operad guidance; host screens and freezes guidance hash; solver runs strictly against frozen guidance.
4. **WF4: Five Agents + LGGR (`wf04_five_agents_lggr` / `pfp/workflows/wf0004`):**
   - **Goal:** Five isolated solver replies whose local checks pass and which agree globally.
   - **Mechanics:** Shared mining call $\to$ 5 isolated solvers $\to$ Local Green, Global Red (LGGR) gluing check ($a_1 = a_2 = a_3 = a_4 = a_5 = f(x)$).
5. **WF5: Checked Rewrite (`wf05_checked_rewrite` / `pfp/workflows/wf0005`):**
   - **Goal:** Seed rewrite preserving protected query on declared finite language, then WF4 execution.
   - **Mechanics:** Query preservation check: $\text{decode}(\text{rewrite}(s)) = \text{query}(s)$. If preservation fails, execution stops immediately.

### 6.2 Proposed Workflows (WF6–WF49)
WF6 through WF49 have complete architectural specifications, input/output schemas, and dependency links in `workflows/dag/workflow_dag.json`. Notable examples include:
- **WF6 (Dialect Sweep):** Multi-model dialect robustness evaluation.
- **WF7 (Typed Refusal):** Formalized refusal protocols distinguishing capability boundaries from adversarial resistance.
- **WF11 (Dual-Certificate Synthesis):** Simultaneous primal-dual certificate generation for exact LP and combinatorics.
- **WF14 (Immune Failure Classification):** Automated classification of execution anomalies into the 12 pharmacy failure classes.
- **WF20 (Derivation Loop with Lift Grants):** Controlled structural lifts $\Lambda$ granted only upon presentation of obstruction certificates.
- **WF39 (Authority Firewall Gate):** Enforcement gate ensuring zero candidate outputs mutate repository custody without human witness receipts.

---

## 7. Ground Truth Demarcations & Artifact Claim Hygiene Analysis

In strict accordance with the Claim Hygiene Rule, every claim regarding the PFP repository must be formally bounded:

### 1. What the codebase supports:
- Demonstrates a typed, fail-closed evaluation pipeline for LLM proposals using exact host checkers (in Python and Rust) where model outputs cannot self-certify.
- Implements an exact 8-letter Discrete Deformation Calculus (`core_operad_canon::DdcOp`) and 10-colour planar multicategory typing system (`OperadColour`).
- Implements a Two-Signal Danger Gate in both Rust and Python that refuses single-signal activations and detects `TWO_SIGNAL_COLLAPSE`.
- Implements reader-relative prompt family validation (`PromptFamily`) enforcing DAG acyclicity, unique root invariants, and non-circular fitness checking.
- Demonstrates working, runnable workflows (WF1 to WF5) for single-turn, slot-filled, pre-mined, multi-agent (LGGR), and rewritten prompt tasks.

### 2. What the codebase does NOT support:
- Does not demonstrate that an LLM possesses genuine understanding, error-free reasoning, or autonomous mathematical proof capability.
- Does not contain stored instances of `anti_skill` records (0 instances in repository).
- Does not contain `anti-rule` or `anti-agent` code types (these exist only as conceptual mechanisms realized through anti-patterns, antibodies, and refusal terminals).
- Does not contain an active Python implementation of `p_star_builder.py` or `expand_prompt` (these were retired on 2026-10-10; their contracts survive as YAML schemas).
- Does not grant operational or administrative authority to any generated proposal (`AuthorityEffect: None` is enforced across all types).

### 3. The narrowest defensible claim:
In this toy and laboratory setting, the Proposal Fidelity Protocol provides a deterministic, typed containment envelope and verification harness that enforces schema validity, prevents self-certification, tracks prompt mutation DAGs, and evaluates candidate proposals against external host oracles without conferring authority.

### 4. The next test needed:
Execution of an adversarial mutation battery against the two-signal danger gate in `code/rust/core_epistemic_immune_system` to verify that forged Signal 2 danger signals derived from model text are consistently refused under `TWO_SIGNAL_COLLAPSE`.
