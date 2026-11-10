# Handoff Report — Survey of Proposal Fidelity Protocol (PFP)

**Agent:** `teamwork_explorer_survey_1`  
**Date:** 2026-11-06  
**Target Recipient:** `parent` (`cd4969be-0ada-47e9-af34-467699d872e1`)  
**Artifact Generated:** `survey_report.md` in the working directory  

---

## 1. Observation

1. **Operad Type Table and Operator Inventory:**
   - In `code/rust/core_operad_canon/src/types.rs` (lines 22–34), `capability_kind` is defined as:
     `values: &["skill", "anti_skill", "rule", "helpful_pattern", "anti_pattern", "antibody"]`.
   - In `code/rust/core_operad_canon/src/lib.rs` (lines 175–197), DDC operations are defined as:
     `enum DdcOp { ExactRepair, ResidualProjection, ContextExposure, Integration, Lift, Descent, Refusal, Terminalize }` with `LETTERS = &["E", "R", "C", "I", "Λ", "D", "M", "T"]`.
   - In `wiki/Operads-Type-Inventory.md` (lines 278–288):
     - Anti-agents: *"No type, file or field. Agents exist only as the 12 roles."*
     - Anti-rules: *"No type. The negative side of a rule is carried by anti-patterns and antibodies; the rules register has no negative entries."*
     - Anti-skill records: *"The anti-skill type is defined, but no anti-skill instance is stored in this repository."* (Count: 0).
     - Skills count: 237 catalogued skill packages.
     - Rules count: 50 rule documents carrying 144 invariants (28 enforced, 12 partial, 104 candidate).
     - Helpful patterns / Anti-patterns: 94 / 93 files.
     - Antibodies: 58 JSON records (`ab_*.json`), 37 YAML specs (`anti_*.yaml`), 1,069 pharmacy catalog entries.

2. **Prompt Family and Lineage Data Structures:**
   - In `code/rust/core_prompt_civilization/src/prompt_family.rs` (lines 109–126, 195–201):
     `PromptFamily` contains `readers: Vec<Reader>`, `nodes: Vec<PromptNode>`, `calls: Vec<CallRecord>`, `steps: Vec<RepairStep>`, `terminal: Option<Terminal>`.
     `PromptNode.relation` is strictly validated (lines 248–255) to be `"root" | "contains" | "repaired_from"`.
     Lines 261–266: `if (node.relation == "root") != node.parent_id.is_none()` enforces that exactly the root has no parent.
     Lines 297–304: Cycle check traverses parent pointers to ensure DAG topology.
   - Lines 398–403: `step.ddc_letter` is validated against `"E" | "R" | "C" | "I" | "Λ" | "D" | "M" | "T"`.
   - Lines 412–421: `residual_before` and `residual_after` are validated against `"Open" | "Closed" | "Exact"`.
   - Lines 455–465: `terminal.kind == "Repaired"` requires a final repair step with `checker_verdict == "ACCEPT"` and `residual_after == "Exact"`.
   - In `code/rust/core_prompt_civilization/src/domain.rs` (lines 20–28), `scope_covers` matches hierarchical domain scopes (e.g. `math.*` covers `math.algebra.cochains`).

3. **Epistemic Immune System (EIS) Code:**
   - In `code/rust/core_epistemic_immune_system/src/lib.rs` (lines 5–9): Defines the Four-Gate Protocol (Defect Observation $\to$ Thymus Central Tolerance $\to$ Two-Signal Danger Gate $\to$ Human Admission Fence).
   - In `code/rust/core_epistemic_immune_system/src/anti_skill.rs` (lines 76–79): Newly harvested anti-skills enter strictly as `AntiSkillStatus::Proposed`.
   - In `code/rust/core_epistemic_immune_system/src/danger_gate.rs` (lines 55–98) and `eis/domain/danger_gate.py` (lines 1–21): `TwoSignalDangerGate` evaluates conjunction of `externally_admitted` AND `detector_match` (Signal 1) AND `independent_danger_signal` (Signal 2) AND `not_suspended`. Signal 1 alone yields `DIAGNOSTIC_ONLY`; Signal 2 alone yields `DIAGNOSTIC_ONLY`. Both required for `QUARANTINED` / `DEFENSIVE_LOCKDOWN`.
   - In `eis/infrastructure/mssn_pharmacy.py` (lines 45–59, 271–444): Reference detector suite evaluates 12 failure classes against candidate JSON/text.

4. **Prompt Sieve Status & Ingestion:**
   - In `education/004_oepfp/docs/21_prompt_template_contracts_and_single_prompt_standard.md` (lines 33–36): Modules `p_star_builder.py`, `runtime.py`, and `tree.py` under `education/pfp/python/` were deleted on 2026-10-10 in commit `e6537cc3cf`. YAML schemas survive in `pfp/infrastructure/yaml/prompts/schemas/`.
   - In `code/rust/core_prompt_civilization/src/forge.rs` (lines 21–57, 161–191): `organize_prompt` ingests seed prompts up to 1 MiB, establishes immutable `original_seed` protected span, appends declared sections (`task`, `constraints`, `acceptance criteria`, `response contract`), and `apply_mutation` raises `PROTECTED_SPAN_MUTATION_REFUSED` if an edit touches any protected span.
   - In `pfp/domain/operad/prompt.py` (lines 18–142): Active prompt tree representation exists as `OperadTreeNode`, `LeafTextSpan`, `PromptColour` (7 colours), and `graft()`.

5. **Workflows:**
   - In `workflows/README.md` (lines 13–64): WF1 to WF5 are runnable (`wf01_typed_answer` through `wf05_checked_rewrite`). WF6 to WF49 are architectural designs with dependency entries in `workflows/dag/workflow_dag.json`.
   - In `pfp/workflows/wf0001/workflow.py` (lines 48–68): Ingestion via `PfpTaskPrompt`, preparation via `PreparePfpTaskTurnUseCase`, checking via `integer_sum_judge`.

---

## 2. Logic Chain

1. **Operator Inventory Discrepancy Reconciliation:**
   - *Observation:* The user request anticipated 12 to 24 operator types, including anti-skills, anti-rules, and anti-agents.
   - *Evidence:* Code inspection of `code/rust/core_operad_canon/src/types.rs`, `wiki/Operads-Type-Inventory.md`, `eis/antibodies/`, and `pfp/domain/operad/` reveals 22 distinct operator and operand classes.
   - *Deduction:* `skill`, `anti_skill`, `rule`, `helpful_pattern`, `anti_pattern`, `antibody`, and `DdcOp` are formally typed. However, `anti-rule` and `anti-agent` are NOT discrete types in code; they are realized through negative components (anti-patterns, antibodies, and refusal terminals). Furthermore, while the `AntiSkillSpecV2` data structure is implemented, 0 stored instances exist in the repo.

2. **Prompt Family Lineage & DDC Connection:**
   - *Observation:* `PromptFamily` in Rust and Python enforces DAG constraints, reader-relativity, and DDC step progression.
   - *Evidence:* In `prompt_family.rs`, `RepairStep` requires a `ddc_letter` and records `residual_before` and `residual_after` (`Open`, `Closed`, `Exact`). `Fitness` tracks `obstruction_removed: Option<bool>` and an external `checker_id`.
   - *Deduction:* Prompt evolution is explicitly modelled as an obstruction-clearing procedure. Removing an obstruction is verified when a DDC step transitions a residual to `Exact` with an external `ACCEPT` verdict from an independent checker, leading to a `Repaired` terminal. Structural creation is tracked via `C` (Context Exposure) and `Λ` (Lift).

3. **EIS Actual Code vs. Spec:**
   - *Observation:* EIS documentation describes self-tolerance, danger signals, and an antibody pharmacy.
   - *Evidence:* Inspection of `code/rust/core_epistemic_immune_system/` and `eis/domain/` reveals that the Four-Gate Protocol is genuinely implemented in Rust and Python. `TwoSignalDangerGate` strictly prevents single-signal activation, and `ThymusGate` screens candidates against a hardcoded baseline self-panel.
   - *Deduction:* EIS is not merely an aspirational design; its gating logic is concrete and executable. However, the stored antibodies are partitioned into two unmerged formats: 58 `ab_*.json` pharmacy execution records and 37 `anti_*.yaml` authored rule specs.

4. **Prompt Sieve Status:**
   - *Observation:* The user prompt asked how seed prompts enter, decompose into subprompts, form prompt families, and evolve.
   - *Evidence:* Monograph `21_prompt_template_contracts` confirms the retirement of legacy `p_star_builder.py`. Meanwhile, `forge.rs` implements `organize_prompt` with protected spans, and `pfp/domain/operad/prompt.py` implements planar operad tree decomposition with 7 prompt colours.
   - *Deduction:* The prompt ingestion and decomposition pipeline operates via `forge_organize_prompt` for text wrapping and protected span tagging, while semantic and tree decomposition is handled via the Planar Coloured Operad tree structure and `PromptFamily` DAG validation.

---

## 3. Caveats

- `anomalon` external repository crates (`omega_engine_pfp`, `omega_epistemic_immune_system`, etc.) mentioned in follow-up notes were not investigated in this subagent turn, as this subagent was tasked strictly with the comprehensive survey of the local `proposal_fidelity_protocol_pfp` repository.
- The 1,069 entries in `pharmacy_catalog.json` represent harvested candidate entries; the majority have not undergone human admission.
- WF6 through WF49 are structural designs with complete contracts and DAG links, but do not have runnable CLI entry points like WF1–WF5.

---

## 4. Conclusion

The `proposal_fidelity_protocol_pfp` repository provides a concrete, multi-layer framework for evaluating LLM candidate proposals under zero-authority containment (`AuthorityEffect: None`). Over 22 distinct operator and operand classes exist across the Coloured Operad spine, Epistemic Immune System, Prompt Civilization, and Workflow runners. The Epistemic Immune System features an executable Four-Gate Protocol with strict two-signal danger gating. Prompt evolution is modelled as DDC cochain deformation, with prompt families tracked as immutable reader-relative DAGs.

---

## 5. Verification Method

1. **Verify Canonical Operad Types:**
   Run from repository root:
   ```bash
   python -m operads.skill_operad.skill_compiler.operad_type_registry
   ```
   *Expected result:* `types=56 PROPOSED=7 SETTLED=49 findings=0`.

2. **Verify Rust Engine Tests (including DDC, EIS, and Prompt Civilization):**
   Run from `code/rust`:
   ```bash
   cargo test -p core_operad_canon
   cargo test -p core_epistemic_immune_system
   cargo test -p core_prompt_civilization
   cargo test -p core_types
   ```
   *Expected result:* All unit and mutation boundary tests pass.

3. **Verify Runnable Workflows (Offline Fixture Mode):**
   Run from repository root:
   ```bash
   python -m pfp.workflows.wf0001 prepare pfp/workflows/wf0001/examples/integer_sum.task.json --output runs/wf1-test
   python -m pfp.workflows.wf0001 check runs/wf1-test pfp/workflows/wf0001/examples/integer_sum.reply.fixture.json --fixture
   python -m pfp.workflows.wf0001 replay runs/wf1-test
   ```
   *Expected result:* Status ACCEPTED with zero errors and no network requests.
