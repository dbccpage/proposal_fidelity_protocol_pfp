# Comprehensive Survey of Workflows and Execution Architecture in Proposal Fidelity Protocol (PFP)

**Repository:** `proposal_fidelity_protocol_pfp` (`c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp`)  
**Date:** 2026-11-06  
**Investigator:** `teamwork_explorer_survey_2`  
**Governing Standard:** Claim Hygiene Rule & Ground Truth Standards (`AuthorityEffect: None`)

---

## 1. Executive Summary & Architectural Overview

The Proposal Fidelity Protocol (PFP) repository implements a deterministic, multi-layer verification and execution architecture designed to govern untrusted model proposals through host-enforced formal checks, cryptographic sealing, exact rational arithmetic, and accounted budget gates.

The execution architecture comprises three distinct operational domains:

1. **Standalone Automated Workflows (WF1–WF5 implemented, WF6–WF49 designed):**
   - **WF1–WF5:** End-to-end implemented and installable via `pfp.workflows` (`pfp/workflows/wf0001` through `wf0005`), registered as console scripts `pfp-wf1` through `pfp-wf5`. They demonstrate progressive procedure extensions: typed envelope check (WF1), full slot reports and emitted operad/DDC candidates (WF2), pre-mining and structural screening with answer-free leak suppression (WF3), five isolated parallel solvers evaluated via Local Green Global Red (LGGR) gluing (WF4), and checked EBNF grammar packet rewriting (WF5).
   - **WF6–WF49:** Cataloged in `workflows/dag/workflow_dag.json` and documented in individual directories (`workflows/wf06_*` through `wf49_*`). They specify experimental sweeps, procedure extensions, task presets, meta-workflows, and harness gates derived from the 204-pilot research estate.
2. **Canonical 11-Stage Staged Pipeline (`RunPfpPipelineUseCase`):**
   - Defined in `pfp/use_cases/pfp_stages.py` and `pfp/domain/stages/stages.py`, mapping an 11-stage pipeline (Stages 1 through 11: Admit, Ideation, Audit, L2 Extraction, Evaluation, Adversarial, Challenge Replay, Selection, Receipt, Hand-off, Evidence Plan) across distinct panel seats (`seat_gauge_breaker`, `seat_defect_hunter`, `seat_adversary`, `seat_primal_dual`, `seat_manuscript_truth`). Host stages (1, 5, 7, 8, 9, 10) are executed by deterministic host checkers; model stages (2, 3, 4, 6, 11) dispatch untrusted requests.
3. **PFP Lab & Symbol Game Governor (`pfp_lab.core`):**
   - Implements the exact weighted constraint graph governor (`pfp_lab/core/governor.py`), evaluating four fundamental proposals (`ASSERT`, `CUT`, `VERIFY`, `RETRACT`) using exact fractions (`fractions.Fraction`), enforcing monotonic descent in defect $D$ and obstruction $\Phi_1$, with zero floating-point tolerances.
4. **Typed Operad Workflow Compiler (`operads/application/typed_workflow_compiler.py`):**
   - Validates planar occurrence graphs, checks input/output port contracts, colour preservation, and capability ceilings, compiling unadmitted candidate instruction plans.
5. **Epistemic Immune System (EIS) & Prompt Sieve / Civilization (PCIV):**
   - Implements antibody lifecycle management, danger signal gating, and Lamarckian prompt evolution / elenchus adversarial testing across prompt families.

Across all workflows, the central invariant is **`AuthorityEffect: None`**: untrusted model outputs hold zero intrinsic authority; every claim must be admitted through deterministic host-side checks, signed manifests, and bit-for-bit replayable verification.

---

## 2. Exhaustive Enumeration of the 49 Workflow Families (WF1–WF49)

The workflow taxonomy is defined canonically in `workflows/dag/workflow_dag.json` and orchestrated according to `workflows/dag/ORCHESTRATION.md`.

### 2.1 Workflow Taxonomy & Classification Matrix

| WF | Name | Status | Kind | Layer | Depends On | Normal Calls | Team Pattern | Host Checker |
|:---|:---|:---|:---|:---:|:---|:---:|:---|:---|
| **WF1** | Typed answer | `implemented` | base | 0 | — | 1 | solo | `typed_envelope_and_independent_exact_sum` |
| **WF2** | Full slots | `implemented` | procedure_extension | 1 | WF1 | 1 | solo | `typed_envelope_and_independent_exact_sum` |
| **WF3** | Mine, then solve | `implemented` | procedure_extension | 2 | WF1 | 2 | relay | `typed_envelope_and_independent_exact_sum` |
| **WF4** | Five agents + LGGR | `implemented` | procedure_extension | 3 | WF3 | 6 | parallel_isolated_then_global | `typed_envelope_and_independent_exact_sum` |
| **WF5** | Checked rewrite | `implemented` | procedure_extension | 4 | WF4 | 6 | parallel_isolated_then_global | `typed_envelope_and_independent_exact_sum` |
| **WF6** | Dialect sweep | `proposal` | experiment_design | 5 | WF5 | 2 + 2k | sweep_with_shared_judge | family checker (exact linear algebra, graph facts, refusal) |
| **WF7** | Typed refusal | `proposal` | procedure_extension | 1 | WF1 | 1 | red_team_pair | typed refusal checker |
| **WF8** | Staged sealed packets | `proposal` | procedure_extension | 2 | WF2, WF5 | k | relay | per-stage receipts plus family checker |
| **WF9** | Bounded check-and-repair | `proposal` | procedure_extension | 2 | WF2 | 1..L | proposer_with_residual_feedback | repair checker (coboundary or parity) |
| **WF10** | Local-to-global obstruction certificate | `proposal` | task_preset | 4 | WF4, WF9 | 1 + n_patches | parallel_isolated_then_global | exact cochain / homology checker |
| **WF11** | Dual-certificate synthesis | `proposal` | task_preset | 3 | WF3, WF9 | budget-capped | research_cell | exact certificate checker plus independent 2nd checker |
| **WF12** | Mechanism-control arms | `proposal` | experiment_design | 6 | WF6, WF3 | arms x items | sweep_with_shared_judge | integer rank-difference certificate |
| **WF13** | Exact-domain capsule battery | `proposal` | task_preset | 2 | WF1, WF7 | 1 / capsule | solo | per-domain registered checker |
| **WF14** | Immune failure classification | `proposal` | meta_workflow | 7 | WF7, WF12 | per candidate | red_team_pair | detector admission check over sealed panel |
| **WF15** | Adversary tribunal | `proposal` | procedure_extension | 8 | WF4, WF14 | 2 / claim | tribunal | finite model checker |
| **WF16** | Substrate crosswalk | `proposal` | task_preset | 5 | WF5, WF10 | 1 / capsule | research_cell | relation-preservation checker (Lean or finite tables) |
| **WF17** | Witnessed-difference programme | `proposal` | task_preset | 5 | WF10, WF11 | budget-capped | research_cell | witness / countermodel checker |
| **WF18** | Dossier replay campaign | `proposal` | harness_gate | 7 | WF6, WF12 | 30 / pilot | sweep_with_shared_judge | family checker (replay must reproduce every grade) |
| **WF19** | Failure-derived rule transfer | `proposal` | experiment_design | 8 | WF12, WF14 | arms x items | research_cell | original domain judges; disagreement halts |
| **WF20** | Derivation loop with lift grants | `proposal` | procedure_extension | 9 | WF9, WF10, WF19 | 5 / pilot | research_cell | finite witness controls; independent proof review |
| **WF21** | Structural prompt rewriting | `proposal` | procedure_extension | 5 | WF5 | 0 or 1 / rule | red_team_pair | byte-preservation and exact judge |
| **WF22** | Certified cost ladder | `proposal` | experiment_design | 8 | WF6, WF8, WF18 | items x arms | sweep_with_shared_judge | family certificate checkers; hypothesis evaluator |
| **WF23** | Judge-packet custody audit | `proposal` | harness_gate | 4 | WF11 | 0 | red_team_pair | audit report (deterministic host verification) |
| **WF24** | Pinned-token operational scratchpad | `proposal` | procedure_extension | 2 | WF2 | see process | solo | dual holonomy checkers that must agree |
| **WF25** | Hierarchical decimation | `proposal` | procedure_extension | 3 | WF24 | see process | solo | dual checkers |
| **WF26** | Multi-round antibody dialogue | `proposal` | procedure_extension | 8 | WF9, WF14 | see process | proposer_with_residual_feedback | exact oracle |
| **WF27** | Hinted retraction with stationary-loop detector | `proposal` | procedure_extension | 3 | WF9 | see process | proposer_with_residual_feedback | host residual gate (Phi1 = 0) |
| **WF28** | Eight-role audit dialogue | `proposal` | procedure_extension | 9 | WF15 | see process | tribunal | strict L1 descent in host |
| **WF29** | Checker synthesis scored by mutation kill rate | `proposal` | task_preset | 4 | WF11 | see process | red_team_pair | mutation suite plus valid-case panel |
| **WF30** | Constraint-forcing anti-recitation | `proposal` | procedure_extension | 1 | WF1 | see process | solo | exact property checker |
| **WF31** | Multi-agent tournament with held-out CV | `proposal` | experiment_design | 1 | WF1 | see process | sweep_with_shared_judge | exact rational referee |
| **WF32** | Claim-scoped receipt | `proposal` | procedure_extension | 2 | WF1, WF2 | see process | solo | per-claim independent checkers |
| **WF33** | Recursive re-entry with shared fuel | `proposal` | procedure_extension | 10 | WF9, WF20 | see process | relay | per-edge maps plus parent binding |
| **WF34** | Future-faithful compression & bounded context | `proposal` | procedure_extension | 9 | WF8, WF22 | see process | relay | endpoint-state equality & reference retention |
| **WF35** | Proposal-channel comparison | `proposal` | experiment_design | 7 | WF6, WF12 | see process | sweep_with_shared_judge | fixed exact oracle |
| **WF36** | Guarded staged slot materialisation | `proposal` | procedure_extension | 3 | WF8 | see process | relay | exact cochain check |
| **WF37** | Evidence-bound harness evolution | `proposal` | meta_workflow | 10 | WF19, WF22 | see process | research_cell | frozen checkers, isolation, reserved budget |
| **WF38** | Diagnostic-trace proposal selection | `proposal` | procedure_extension | 3 | WF9 | see process | proposer_with_residual_feedback | exact rational diagnostics |
| **WF39** | Authority firewall gate | `proposal` | harness_gate | 5 | WF1, WF23 | see process | solo | guard vector over reply |
| **WF40** | Restart boundary after exhausted repair | `proposal` | procedure_extension | 10 | WF9, WF20 | see process | proposer_with_residual_feedback | trichotomy and lift-witness check |
| **WF41** | Detector adequacy & two-signal admission | `proposal` | meta_workflow | 8 | WF14 | see process | red_team_pair | calibration record and two-signal table |
| **WF42** | Reasoning-trace validation | `proposal` | procedure_extension | 6 | WF10, WF21 | see process | red_team_pair | rational LP primal-dual check |
| **WF43** | Gate-honesty & answer-free leak audit | `proposal` | harness_gate | 5 | WF23 | see process | red_team_pair | replay against audited checkers |
| **WF44** | Exact certificate presets | `proposal` | task_preset | 5 | WF11, WF10 | see process | solo | exact certificate check |
| **WF45** | Finite terminal selector & plenitude test | `proposal` | procedure_extension | 2 | WF7 | see process | solo | deterministic verifier and survivor set |
| **WF46** | Boundary sufficiency & gluing diagnostic | `proposal` | procedure_extension | 4 | WF4 | see process | parallel_isolated_then_global | global evaluator on glued trace |
| **WF47** | Resumable bounded frontier search | `proposal` | procedure_extension | 3 | WF9 | see process | relay | exact sign-gauge verifier |
| **WF48** | Commit-reveal with hostile mutation gate | `proposal` | harness_gate | 5 | WF11, WF23 | see process | red_team_pair | dual checkers plus mutation suite |
| **WF49** | Query-preservation stage & mode campaign | `proposal` | experiment_design | 9 | WF8, WF22 | see process | sweep_with_shared_judge | per-family oracles |

---

## 3. Deep-Dive: Implemented Workflows (WF1 through WF5)

The five runnable workflows are fully implemented under `pfp/workflows/` and share common infrastructure in `pfp/infrastructure/workflow_runtime.py`, `pfp/infrastructure/workflow_accounting.py`, and `pfp/infrastructure/workflow_tasks.py`.

### 3.1 WF1 — Typed Answer (`pfp/workflows/wf0001/`)
- **Objective:** Establish the minimal typed task-turn contract without intermediate mining, rewriting, or multi-agent decomposition.
- **Source Files:**
  - `pfp/workflows/wf0001/workflow.py`
  - `pfp/workflows/wf0001/runner.py`
  - `pfp/workflows/wf0001/workflow.json`
  - `pfp/workflows/wf0001/task_spec.schema.json`
- **Inputs:**
  - Task specification dict conforming to `task_spec.schema.json` containing: `task_id`, `seed_prompt`, `input` (e.g. integer array), `answer_schema` (JSON schema), and `checker` (e.g., `integer_sum_v1` or `schema_only`).
- **State Transformations:**
  1. `validate_task(spec)`: Validates spec against `task_spec.schema.json`.
  2. `prepare_task(spec)`: Packages spec into `PfpTaskPrompt`. Invokes `PreparePfpTaskTurnUseCase().execute(basic_template(), task, ATTEMPT_ID)`. Returns `PreparedTaskTurn`.
  3. Prepares frozen execution context: `task.json`, `prepared.json`, `system_prompt.txt`, `user_prompt.txt`, `response_schema.json`, and hashes into `preparation_manifest.json`.
- **Operators Invoked:**
  - Base semantic template projection (`basic_task_template`).
  - Single provider call through accounted gateway.
  - Deterministic judge: `integer_sum_judge` (evaluates `sum(input["values"]) == answer["total"]`).
- **Outputs:**
  - `response.raw`: Raw wire reply from provider.
  - `receipt.json`: Contains status (`HOST_ACCEPTED`, `PROVIDER_COMPLETED`, or `INFRASTRUCTURE_ERROR`), checked envelope, and accounting state.
  - `receipt_manifest.json`: SHA-256 seal of all files.
- **Failure & Refusal Behaviors:**
  - `SCHEMA_INVALID`: Response does not conform to `answer_schema`.
  - `JUDGE_FAILED`: Total does not equal exact integer sum.
  - `CALL_ALLOWANCE_EXHAUSTED` / `ESTIMATED_BUDGET_EXCEEDED`: Refusal before dispatch if estimated cost exceeds budget limit ($0.004999 ceiling).

### 3.2 WF2 — Full Slots & Emitted Operad/DDC Moves (`pfp/workflows/wf0002/`)
- **Objective:** Require the model to address an explicit slot catalogue, emit candidate operad operations with literal source grounding, and declare Discrete Deformation Calculus (DDC) moves.
- **Source Files:**
  - `pfp/workflows/wf0002/workflow.py`
  - `pfp/workflows/wf0002/runner.py`
  - `pfp/workflows/wf0002/collection.py`
  - `pfp/workflows/wf0002/slot_catalogue.json`
  - `pfp/workflows/wf0002/answer.schema.json`
  - `pfp/workflows/wf0002/reference/ddc_alphabet.rs.txt`
- **Inputs:**
  - Task specification dict plus pinned slot catalogue (`slot_catalogue.json` containing 16 slots: `carrier`, `equality_policy`, `operands`, `colours`, `operators`, `terminal`, `concrete_spans`, etc.).
- **State Transformations:**
  1. Extends `answer.schema.json` by embedding `task_result` alongside required arrays `slot_report`, `operad_candidates`, and `ddc_moves`.
  2. Injects full template instructing model to cover every slot with `provided` (non-empty value) or `not_applicable`/`unresolved` (empty value + non-empty reason).
  3. `finalize_check(spec, checked)`: Deterministically audits structural integrity:
     - Exact slot coverage (no missing, no duplicate slots; required core slots cannot be unresolved).
     - Operad candidate arity check: `op["arity"] == len(op["source_colours"])`.
     - Source quote verification: `op["source"]["quote"]` must be an exact literal substring of `seed_prompt` or compact sorted `input_json`.
     - Unknown witness reference check: references must only name catalogue slots, emitted operad IDs, or `task_result`.
     - DDC move checks: Move must declare one of the 8 canonical DDC operations:
       - `E` (Exact repair)
       - `R` (Residual projection)
       - `C` (Context exposure)
       - `I` (Integration)
       - `Λ` (Structural lift)
       - `D` (Descent)
       - `M` (Mutation / typed refusal)
       - `T` (Terminalization)
       - Non-empty `local_log` or `refusal` required; operad references must resolve.
- **Outputs:**
  - Standard run files plus `collection.json` (extracted operad candidates and DDC moves marked as unverified candidate material).
- **Failure & Refusal Behaviors:**
  - `SLOT_COVERAGE_OR_DUPLICATES`, `REQUIRED_SLOT_UNRESOLVED`, `ARITY_MISMATCH`, `SOURCE_QUOTE_MISSING`, `UNKNOWN_WITNESS_REF`, `DDC_LOG_OR_REFUSAL_REQUIRED`.
  - Sets `failure_class="WF2_OPERAD_STRUCTURE"` and refuses result if structural checks fail.

### 3.3 WF3 — Mine, Then Solve (`pfp/workflows/wf0003/`)
- **Objective:** Segregate structural feature extraction (mining) from task solution into a 2-stage relay, enforcing strict answer-free leak suppression.
- **Source Files:**
  - `pfp/workflows/wf0003/workflow.py`
  - `pfp/workflows/wf0003/runner.py`
  - `pfp/workflows/wf0003/structured.py`
  - `pfp/workflows/wf0003/mining_answer.schema.json`
- **Inputs:**
  - Standard task specification. Prohibits caller from injecting `pfp_mined_attachment` (`WF3_RESERVED_ATTACHMENT_KEY`).
- **State Transformations (2 Stages):**
  1. **Stage 1 (Mining):**
     - Prompt instructs miner to pre-mine up to 2 typed operations and 4 L2 guidance records (`concrete_spans`, `parameter_bindings`, `instantiated_arguments`, `preservation_obligations`).
     - Instruction explicitly forbids decimal digits in free-text fields.
     - `screen_mining(spec, raw, checked)`:
       - Executes `text_screen`: scans recursively for any decimal digit (`re.search(r"\d", value)`) in guidance text (outside literal quotes), rejecting any numeric leakage (`NUMERICAL_GUIDANCE_FORBIDDEN`).
       - Validates source quote literal occurrence and arity.
     - `freeze_attachment`: Packages accepted mining results into `pfp.wf3.mined-attachment.v1` with canonical JSON SHA-256 digest.
  2. **Stage 2 (Solving):**
     - Solver task is prepared by injecting frozen `pfp_mined_attachment` into task context.
     - Solver response schema restricts operad candidates to those mined in Stage 1.
     - Host executes independent judge on `task_result`.
- **Outputs:**
  - Mining run directory: `mining/` (`task.json`, `prepared.json`, `response.raw`, `receipt.json`).
  - Solver run directory: `solver/` (`task.json`, `prepared.json`, `response.raw`, `receipt.json`).
- **Failure & Refusal Behaviors:**
  - If mining fails screening, runner refuses with `WF3_MINING_NOT_SCREENED`. No fallback to unassisted WF2 is permitted.

### 3.4 WF4 — Five Agents + LGGR Boundary Gluing (`pfp/workflows/wf0004/`)
- **Objective:** Run 5 isolated parallel solvers against a frozen compiled public profile and evaluate the composite result using Local Green Global Red (LGGR) gluing defect analysis.
- **Source Files:**
  - `pfp/workflows/wf0004/workflow.py`
  - `pfp/workflows/wf0004/runner.py`
  - `ops/adversary/infrastructure/lggr_adapter.py`
  - `pfp/workflows/wf0004/workflow.json`
- **Inputs:**
  - Task specification requiring `integer_sum_v1` checker.
- **State Transformations (6 Calls Total):**
  1. **Stage 1:** Mines operations via WF3 mining contract.
  2. **Stage 2:** `freeze_profile`: Compiles public profile `pfp.wf4.public-profile.v1` (frozen slots, operad candidates, mining sha256).
  3. **Stage 3 (Parallel Solvers):** Dispatches 5 independent, isolated solver calls (`agent-1` through `agent-5`) via `ThreadPoolExecutor` and `EstimatedBudgetGateway.complete_batch_result`.
     - Each agent receives only the task context and profile hash; agents NEVER see each other's responses.
  4. **Stage 4 (Evaluation & Gluing):**
     - `evaluate_global(spec, checks)`:
       - Evaluates local structural correctness (`local_green`) for each agent.
       - Evaluates exact semantic correctness (`task_correct`).
       - Checks overlap agreement: all 5 agents must independently arrive at the exact same answer (`totals[0] == totals[1] == ... == totals[4]`).
       - Executes `LggrGluingAdapter().evaluate_boundary(local_evaluators, global_evaluator)`:
         $$\Delta_E = E_G - \prod_{i=1}^5 E_i$$
         - $\Delta_E = -1$: `NegativeGluingDefect_LocalGreenGlobalRed` (all local pass, global fails).
         - $\Delta_E = 1$: `PositiveGluingDefect` (global pass, local fails).
         - $\Delta_E = 0$: `ZeroDefectResidual` (concordant).
       - Audits 11 detector adequacy criteria (minimum trajectory counts, non-vacuousness, null-space soundness $\operatorname{im}(D) \cap K = \{0\}$).
- **Operators Invoked:**
  - `EstimatedBudgetGateway` atomic batch reservation (64-slot limit, barrier synchronization).
  - `LggrGluingAdapter`.
- **Outputs:**
  - Directory structure containing `mining/`, `agent-1/` .. `agent-5/`, and root `global_receipt.json` recording LGGR gluing delta and detector adequacy.
- **Failure & Refusal Behaviors:**
  - Strict non-voting rule: Majority agreement is NOT accepted. If even one agent fails or disagrees, status becomes `TYPED_REFUSAL`.

### 3.5 WF5 — Checked EBNF Grammar Rewrite (`pfp/workflows/wf0005/`)
- **Objective:** Parse a natural language prompt, validate against a strict source language, lower it to a canonical semantic query, encode it into an explicit EBNF packet format, decode it independently, verify round-trip preservation, and feed the rewritten packet into the WF4 multi-agent solver.
- **Source Files:**
  - `pfp/workflows/wf0005/workflow.py`
  - `pfp/workflows/wf0005/runner.py`
  - `pfp/workflows/wf0005/rewrite.py`
  - `pfp/workflows/wf0005/packet.ebnf`
  - `pfp/workflows/wf0005/grammar_provenance.json`
- **Inputs:**
  - Natural language task string starting with `"Calculate the exact sum of "` and ending with `"."`.
- **State Transformations:**
  1. `source_query(seed)`: Parses seed into token sequence, enforces canonical English listing (`a, b, and c`), checks digit limits ($\le 101$ digits), produces canonical query dict.
  2. `encode(protected)`: Compiles AST into EBNF S-expression syntax using `pfp.domain.tower.grammar`:
     ```text
     <sum <exact> <once> <values p10 n5 p2> <total>>
     ```
  3. `decode(wire)`: Bounds wire bytes ($\le 65536$) and parenthesis depth ($\le 3$). Parses packet back to canonical representation.
  4. `round_trip(seed)`: Asserts exact semantic invariance: `decode(encode(source_query(seed))) == source_query(seed)`.
  5. Lowering bundle is frozen with SHA-256 digest (`rewrite_ref`).
  6. Dispatches to 1 miner + 5 parallel solvers conforming to the WF4 structure.
- **Outputs:**
  - Run directory with `rewrite.json`, `mining/`, `agent-1/` through `agent-5/`, and `global_receipt.json`.
- **Failure & Refusal Behaviors:**
  - `WF5_UNSUPPORTED_SEED_LANGUAGE`, `WF5_SOURCE_INTEGER_SYNTAX`, `WF5_UNACCOUNTED_OR_NONCANONICAL_SOURCE`, `WF5_PACKET_DEPTH`. Refuses before any model dispatch.

---

## 4. The 11-Stage Canonical PFP Pipeline (`RunPfpPipelineUseCase`)

Implemented in `pfp/use_cases/pfp_stages.py` and specified in `pfp/domain/stages/stages.py`, this pipeline provides a formal staged progression for complex proposal evaluation.

### 4.1 Stage Architecture & Panel Seats

| Stage | Name | Executor | Panel Seat | Minimum Inputs | Function |
|:---:|:---|:---:|:---|:---:|:---|
| **1** | `ADMIT` | Host | (Host plumbing) | — | Admission check; verifies task declaration, repairs missing declarations via model if necessary. |
| **2** | `IDEATION` | Model | `seat_gauge_breaker` | (1) | Generates initial candidate proposals. |
| **3** | `AUDIT` | Model | `seat_defect_hunter` | (2) | Red team audits candidates for surface defects, invalid assumptions, and gauge violations. |
| **4** | `L2_EXTRACTION` | Model | `seat_gauge_breaker` | (3) | Extracts structural L2 operad candidates, bindings, and preservation invariants. |
| **5** | `EVALUATION` | Host | `seat_adversary` | (2, 4) | Host runs deterministic exact checkers against candidate proposals. Must emit `PASS` or run terminates. |
| **6** | `ADVERSARIAL` | Model | `seat_primal_dual` | (4, 5) | Adversarial challenger constructs countermodels, boundary stresses, and potential leaks. |
| **7** | `CHALLENGE_REPLAY`| Host | (Host plumbing) | (4, 5, 6) | Host independently replays adversary witnesses against the candidate. Identifies obstructions. |
| **8** | `SELECTION` | Host | `seat_manuscript_truth` | (5, 7) | Selects survivor candidates from Stage 5 that resisted Stage 7 obstructions. |
| **9** | `RECEIPT` | Host | (Host plumbing) | (1, 5, 7) | Recomputes final terminal disposition, remaining obligations, and signs execution receipt. |
| **10**| `HAND_OFF` | Host | (Host plumbing) | (9) | Packages execution artifacts for downstream consumers. |
| **11**| `EVIDENCE_PLAN` | Model | (Optional) | (9) | Dispatched only if Stage 9 marks receipt `diagnostic_only`; outlines next required tests. |

### 4.2 Terminal States & Stop Policies
The terminal disposition is computed deterministically in `receipt_terminal(responses)` (`pfp/domain/stages/host_stages.py`):
1. **`BLOCKED_BY_EVIDENCE`:** A deterministic check at Stage 5 failed (`host_verdict != "PASS"` or `exact_checks_passed is not True`), or early stop occurred before Stage 5 pass.
2. **`OPEN_OBSTRUCTION`:** Adversary witnesses replayed successfully at Stage 7, proving the candidate has an uneliminated obstruction.
3. **`VERIFIED`:** All acceptance stages (1, 2, 3, 4, 5, 6, 7, 9) completed, Stage 5 host check passed, zero open obstructions at Stage 7, and zero remaining obligations.
4. **`VERIFIED_WITH_RESIDUALS`:** Stage 5 passed without open obstruction, but some non-critical obligations remain or run stopped early after Stage 5.

### 4.3 Kinetic Proofreading Gate (F-BIO-02)
Implemented in `pfp/gate.py`:
- `CandidateEvaluationGateV1` enforces kinetic proofreading:
  - If a candidate digest is recorded as `REJECTED`, re-evaluation of that candidate by the same frozen checker set in the same generation raises `PermissionError("STAGE_REENTRY_REFUSED")`.
  - Only candidates marked `INCONCLUSIVE` may retry within the declared budget limit.

---

## 5. PFP Lab & Symbol Game Governor (`pfp_lab/core/`)

`pfp_lab` is a standalone, dependency-minimal Python package implementing the exact Proposal Fidelity Protocol for weighted constraint graphs.

### 5.1 Graph State & Mathematical Invariants
- Graph $G = (V, E, w)$ with vertices $V$, directed edges $E$, and positive integer weights $w(e) \in [1, 1000]$.
- Exact State:
  - Section $s: V \to \mathbb{Q}$ (exact vertex potential).
  - Claims $c: E \to \mathbb{Q}$ (exact edge potential differences).
- Exact Defect ($D$):
  $$D(s) = \sum_{(u, v) \in E} w(u, v) \cdot |s(v) - s(u) - c(u, v)|$$
- Obstruction ($\Phi_1$):
  $$\Phi_1(c) = \min_{s} D(s)$$
  Computed via minimum-weight cycle basis or rational linear programming.

### 5.2 The Four Fundamental Moves (`pfp_lab/core/governor.py`)
1. **`ASSERT` (`AssertMove`):**
   - Proposes a value for an edge claim: $c(u, v) = q \in \mathbb{Q}$.
   - If `enforce_monotonicity=True`, refused with `DefectIncrease` if new defect exceeds prior defect.
2. **`CUT` (`CutMove`):**
   - Proposes either a complete section $s$ or a complete claim set $c$.
   - Admitted only if $D$ (or $\Phi_1$) does not increase:
     - If new defect $<$ old defect $\implies$ `MonotonicDescent` or `ExactRepair` (if $D=0$).
     - If new defect $==$ old defect $\implies$ `IdempotentStationary`.
     - If new defect $>$ old defect $\implies$ `DefectIncrease` (Refused).
   - If claims are replaced, section is updated via projection $P_S$ (`project(graph, claims)`).
3. **`VERIFY` (`VerifyMove`):**
   - Checks an exact obligation:
     - `ZERO_DEFECT`: asserts $D = 0$.
     - `ZERO_OBSTRUCTION`: asserts $\Phi_1 = 0$.
     - `EDGE_MATCH:u,v`: asserts $s(v) - s(u) == c(u, v)$.
   - Does not alter graph state; returns `Verified` or `VerificationFailed`.
4. **`RETRACT` (`RetractMove`):**
   - Rolls back graph state to a named prior step (`target_step_id`), restoring historical section and claims.

---

## 6. Operads & Typed Workflow Compilation (`operads/`)

The `operads` subsystem provides a category-theoretic compilation layer for agent workflows:

- **Contracts (`operads/contracts/typed_workflow_v1.py`):**
  - Defines `TypedWorkflowWireV1`, `WorkflowNodeWireV1`, `WorkflowBindingWireV1`, and `WorkflowInputWireV1`.
  - Schema: `oewas.typed-workflow.v1`, canonicalization profile: `oewas.sorted-ascii-json.v1`.
- **Compiler (`operads/application/typed_workflow_compiler.py`):**
  - `compile_typed_workflow`:
    1. Validates workflow shape and invariants.
    2. Checks source operations from skill documents (`SkillDocumentV3`).
    3. Validates node declarations against cryptographic digests (`source_digest`, `operation_digest`).
    4. Injects native graph validator (`validate_graph: Callable`) to audit DAG topology: detects cycles, orphaned edges, duplicate nodes, and port colour mismatches.
    5. Lowers single-consumer occurrence graph into planar tree `PlanNodeV01`.
    6. Calls `compile_candidate_plan` to verify port contracts and capability ceilings.
    7. Emits `CompiledWorkflowV1` (marked Unadmitted; `AuthorityEffect: None`).
- **Predefined Operational Workflows (`operads/workflows/`):**
  - `contract_compliance_audit_workflow.json`
  - `cppms_commit_sync_workflow.json`
  - `paper_proof_release_workflow.json`
  - Sprint cadence workflows (`sprint_planning.md`, `sprint_execution.md`, `sprint_devops_review.md`, `sprint_retrospective.md`).

---

## 7. Epistemic Immune System (EIS) & Prompt Sieve / Civilization (PCIV)

### 7.1 Epistemic Immune System (`eis/`)
- **Antibody Lifecycle:**
  - `AntibodyCandidate`: extracted from failure logs or adversary traces.
  - `danger_gate.py`: Evaluates two independent danger signals (`two_signal_independence.py`) before activating immune defense.
  - `thymus.py`: Negative selection against non-harmful or self-patterns.
  - `treg.py`: T-regulatory cells suppress hyper-reactive or degenerate antibody rules (`anergy.py`).
  - `clonal_selection.py`: Selectively amplifies high-affinity antibodies that successfully block adversarial attacks.
  - `pharmacy_catalog.py`: Repository of vetted, transferable antibodies.

### 7.2 Prompt Sieve & Prompt Civilization (`pciv/`)
- **Prompt Sieve Intake:**
  - Ingests raw seed prompts. Breaks composite prompts into atomic task components.
  - Identifies prompt lineage, domain, and subdomains.
- **Prompt Ecology & Lamarckian Evolution:**
  - `models.py`: Defines prompt families, variants, lineages, and fitness records.
  - `forge.py`: Forges prompt variants under controlled perturbations (carrier alphabet, dialect, prompt scaffolding).
  - `lamarckian_loop.py`: Retains successful adaptations into the prompt genome based on host acceptance rates.
  - `elenchus.py`: Socratic/adversarial refutation loop; tests prompt robustness against poisoned or out-of-distribution inputs.

---

## 8. Map of Entry Points, CLI Tools, Test Suites & Configurations

### 8.1 Console Entry Points (`pyproject.toml`)
- `pfp-wf1 = "pfp.workflows.wf0001.runner:main"`
- `pfp-wf2 = "pfp.workflows.wf0002.runner:main"`
- `pfp-wf3 = "pfp.workflows.wf0003.runner:main"`
- `pfp-wf4 = "pfp.workflows.wf0004.runner:main"`
- `pfp-wf5 = "pfp.workflows.wf0005.runner:main"`
- `pfp-lab = "pfp_lab.cli.main:entry"`
- `pfp-lab-web = "pfp_lab.web.app:entry"`

### 8.2 Subcommands of `pfp-wf1` .. `pfp-wf5`
- `run <task.json> --output <dir> [--model <id>] [--budget-microusd <int>]`: Executes workflow under accounted ledger.
- `prepare <task.json> --output <dir>`: Prepares task prompts and manifests without dispatching to provider.
- `check <dir> <response.raw>`: Grades an externally supplied raw reply.
- `replay <dir>`: Deterministically replays a completed run; re-evaluates all checks and verifies bit-for-bit against `receipt_manifest.json`.

### 8.3 CLI Commands of `pfp-lab`
- `pfp-lab packs`: Lists built-in scenario packs (`paper-005-worked-session`, `section-repair`, `refusals`, `two-components`).
- `pfp-lab run <file.json> [--receipt <out.json>]`: Executes scenario.
- `pfp-lab verify <receipt.json>`: Verifies receipt hash and recomputes all governor verdicts.
- `pfp-lab stdio`: Starts JSON-RPC stdio server for external GUI frontends (e.g., `csharp/PfpLab.Desktop`).

### 8.4 Clean Architecture CLI (`pfp/entrypoints/cli/pfp.py`)
- `run-demo <demo_id>`
- `verify-contracts`
- `evaluate-gates --candidate-id <id> --state-json <path>`
- `assemble --demo-id <id> --stage <int> --seed-json <path>`
- `run-pilot-suite --pilot-dir <dir> --model <id> --output-dir <dir>`
- `run-seed <seed_id> --stages <1..11> --model <id>`

### 8.5 Test Suites
- `pfp/workflows/tests/`:
  - `test_standalone.py`: Parameterized across all 5 workflows (WF1–WF5), verifying accounted runs, budget caps, path traversal guards, reasoning policy, and replay verification.
- `pfp_lab/tests/`:
  - Comprehensive suite for graph, obstruction, governor, admission, receipts, RPC, and CLI (100% exact rational tests, hypothesis property-based testing).
- `workflows/tasks/certified_challenges/`:
  - 50 challenge packages (`c011` to `c060`), ~5,100 tests verifying exact mathematical certificates across homology, quantum codes, Hodge theory, and graph invariants.
- `eis/tests/` and `pciv/tests/`:
  - Architecture boundary tests, antibody admission, pharmacy search, and prompt evolution tests.

---

## 9. Artifact Evaluation under Claim Hygiene Rules

### 9.1 What the Evidence Supports
1. **Deterministic Host Verification:** The repository code supports the claim that model outputs are treated as untrusted proposals and subjected to deterministic, host-evaluated checkers (exact integer arithmetic, JSON schema validation, exact rational constraint graph evaluation).
2. **Bit-for-Bit Replayability:** The `WorkflowRuntime` supports independent offline verification of sealed runs (`replay_run`) by verifying cryptographic hashes of all inputs, prompts, outputs, and checker results against `receipt_manifest.json`.
3. **Answer-Free Screening:** WF3 code demonstrates that structural extraction can be screened to forbid decimal digits, preventing answer leakage prior to solver dispatch.
4. **Local-to-Global Defect Detection:** The LGGR adapter supports measuring whether local evaluators pass while global composite evaluations fail ($\Delta_E = -1$), providing an explicit non-factorization defect metric.
5. **Exact Rational Governance:** `pfp_lab` demonstrates in a toy setting that graph constraint proposals can be governed with exact rational arithmetic without floating-point drift.

### 9.2 What the Evidence Does Not Support
1. **No Proof of Universal Alignment:** The mechanisms do not prove or guarantee that models will generate truthful or safe answers in unconstrained domains.
2. **No Empirical Claim on Unrun Proposals (WF6–WF49):** WF6 through WF49 are specifications and designs derived from historical pilot records; they do not represent executed or measured benchmark outcomes in this repository.
3. **No General Machine Authority:** The system does not grant authority to models or agent agreement; agreement among five agents in WF4 does not constitute mathematical truth, which is why an independent host checker is mandated.

### 9.3 Narrowest Defensible Claim
The Proposal Fidelity Protocol repository provides an installable reference implementation (WF1–WF5, 11-stage pipeline, PFP Lab) that strictly binds language model proposals to deterministic, host-verified schemas, exact mathematical checks, cryptographic receipt sealing, and accounted budget limits under an explicit `AuthorityEffect: None` security posture.

### 9.4 Next Test Needed
Execute WF9 (Bounded check-and-repair) on certified challenge C011 (`c011_cycle_rank_ladder_coboundary_repair`) with and without the Opus boost step, recording the exact rational duality gap receipts and total API costs across both arms.
