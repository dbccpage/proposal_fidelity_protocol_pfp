# Proposal Fidelity Protocol (PFP) Workflows & Architecture

**AuthorityEffect**: None.  
**Standard:** Ground Truth Verification and Claim Hygiene Standard  
**Repository:** `proposal_fidelity_protocol_pfp`  

---

## 1. Executive Summary & Master Index

The Proposal Fidelity Protocol (PFP) execution framework treats language model outputs as untrusted candidate proposals. No model response carries intrinsic epistemic authority. Every claim must pass deterministic host-side checks, exact integer or rational evaluation, cryptographic manifest sealing, and accounted budget gates before admission.

The workflow system comprises **49 numbered workflow families** (WF1–WF49) organized as a directed acyclic graph (DAG) in `workflows/dag/workflow_dag.json`:
- **WF1–WF5 (Implemented & Runnable):** Fully implemented in Python under `pfp/workflows/` and installable as CLI entry points (`pfp-wf1` through `pfp-wf5`). They provide an incremental progression of structural constraints: single typed answer (WF1), full slot catalogue and operad candidate emission (WF2), answer-free pre-mining with digit leak suppression (WF3), 5-agent parallel isolated solve evaluated under Local Green Global Red (LGGR) gluing defect analysis (WF4), and EBNF grammar AST rewriting with round-trip preservation checks (WF5).
- **WF6–WF49 (Architectural Proposals & Preset Designs):** Detailed workflow specifications catalogued in `workflows/dag/workflow_dag.json` and `workflows/wf06_*` through `workflows/wf49_*`. These define dialect sweeps, typed refusal gates, bounded check-and-repair loops, local-to-global obstruction certificates, dual-certificate synthesis, cost ladders, tribunal structures, and harness gates derived from the 204-pilot research estate.

### Master Index of Workflows (WF1–WF49)

| Workflow | Name | Status | Kind | Layer | Builds On | Normal Calls | Team Pattern | Documentation File |
|:---|:---|:---:|:---:|:---:|:---|:---:|:---|:---|
| **WF1** | Typed answer | `implemented` | `base` | 0 | — | 1 | solo | [`wf0001.md`](wf0001.md) |
| **WF2** | Full slots | `implemented` | `procedure_extension` | 1 | WF1 | 1 | solo | [`wf0002.md`](wf0002.md) |
| **WF3** | Mine, then solve | `implemented` | `procedure_extension` | 1 | WF1 | 2 | relay | [`wf0003.md`](wf0003.md) |
| **WF4** | Five agents + LGGR | `implemented` | `procedure_extension` | 2 | WF3 | 6 | parallel_isolated_then_global | [`wf0004.md`](wf0004.md) |
| **WF5** | Checked rewrite | `implemented` | `procedure_extension` | 3 | WF4 | 6 | parallel_isolated_then_global | [`wf0005.md`](wf0005.md) |
| **WF6** | Dialect sweep | `proposal` | `experiment_design` | 4 | WF5 | 2 + 2k | sweep_with_shared_judge | [`wf0006.md`](wf0006.md) |
| **WF7** | Typed refusal | `proposal` | `procedure_extension` | 1 | WF1 | 1 | red_team_pair | [`wf0007.md`](wf0007.md) |
| **WF8** | Staged sealed packets | `proposal` | `procedure_extension` | 4 | WF2, WF5 | k | relay | [`wf0008.md`](wf0008.md) |
| **WF9** | Bounded check-and-repair | `proposal` | `procedure_extension` | 2 | WF2 | 1..L | proposer_with_residual_feedback | [`wf0009.md`](wf0009.md) |
| **WF10** | Local-to-global obstruction certificate | `proposal` | `task_preset` | 3 | WF4, WF9 | 1 + n_patches | parallel_isolated_then_global | [`wf0010.md`](wf0010.md) |
| **WF11** | Dual-certificate synthesis | `proposal` | `task_preset` | 3 | WF3, WF9 | budget-capped | research_cell | [`wf0011.md`](wf0011.md) |
| **WF12** | Mechanism-control arms | `proposal` | `experiment_design` | 5 | WF6, WF3 | arms x items | sweep_with_shared_judge | [`wf0012.md`](wf0012.md) |
| **WF13** | Exact-domain capsule battery | `proposal` | `task_preset` | 2 | WF1, WF7 | 1 / capsule | solo | [`wf0013.md`](wf0013.md) |
| **WF14** | Immune failure classification | `proposal` | `meta_workflow` | 6 | WF7, WF12 | per candidate | red_team_pair | [`wf0014.md`](wf0014.md) |
| **WF15** | Adversary tribunal | `proposal` | `procedure_extension` | 7 | WF4, WF14 | 2 / claim | tribunal | [`wf0015.md`](wf0015.md) |
| **WF16** | Substrate crosswalk | `proposal` | `task_preset` | 4 | WF5, WF10 | 1 / capsule | research_cell | [`wf0016.md`](wf0016.md) |
| **WF17** | Witnessed-difference programme | `proposal` | `task_preset` | 4 | WF10, WF11 | budget-capped | research_cell | [`wf0017.md`](wf0017.md) |
| **WF18** | Dossier replay campaign | `proposal` | `harness_gate` | 6 | WF6, WF12 | 30 / pilot | sweep_with_shared_judge | [`wf0018.md`](wf0018.md) |
| **WF19** | Failure-derived rule transfer | `proposal` | `experiment_design` | 7 | WF12, WF14 | arms x items | research_cell | [`wf0019.md`](wf0019.md) |
| **WF20** | Derivation loop with lift grants | `proposal` | `procedure_extension` | 8 | WF9, WF10, WF19 | 5 / pilot | research_cell | [`wf0020.md`](wf0020.md) |
| **WF21** | Structural prompt rewriting | `proposal` | `procedure_extension` | 4 | WF5 | 0 or 1 / rule | red_team_pair | [`wf0021.md`](wf0021.md) |
| **WF22** | Certified cost ladder | `proposal` | `experiment_design` | 7 | WF6, WF8, WF18 | items x arms | sweep_with_shared_judge | [`wf0022.md`](wf0022.md) |
| **WF23** | Judge-packet custody audit | `proposal` | `harness_gate` | 4 | WF11 | 0 | red_team_pair | [`wf0023.md`](wf0023.md) |
| **WF24** | Pinned-token operational scratchpad | `proposal` | `procedure_extension` | 2 | WF2 | 1 | solo | [`wf0024.md`](wf0024.md) |
| **WF25** | Hierarchical decimation | `proposal` | `procedure_extension` | 3 | WF24 | 1 | solo | [`wf0025.md`](wf0025.md) |
| **WF26** | Multi-round antibody dialogue | `proposal` | `procedure_extension` | 7 | WF9, WF14 | budget-capped | proposer_with_residual_feedback | [`wf0026.md`](wf0026.md) |
| **WF27** | Hinted retraction with loop detector | `proposal` | `procedure_extension` | 3 | WF9 | budget-capped | proposer_with_residual_feedback | [`wf0027.md`](wf0027.md) |
| **WF28** | Eight-role audit dialogue | `proposal` | `procedure_extension` | 8 | WF15 | 8 | tribunal | [`wf0028.md`](wf0028.md) |
| **WF29** | Checker synthesis scored by mutation kill | `proposal` | `task_preset` | 4 | WF11 | budget-capped | red_team_pair | [`wf0029.md`](wf0029.md) |
| **WF30** | Constraint-forcing anti-recitation | `proposal` | `procedure_extension` | 1 | WF1 | 1 | solo | [`wf0030.md`](wf0030.md) |
| **WF31** | Tournament with held-out CV | `proposal` | `experiment_design` | 1 | WF1 | models x items | sweep_with_shared_judge | [`wf0031.md`](wf0031.md) |
| **WF32** | Claim-scoped receipt | `proposal` | `procedure_extension` | 2 | WF1, WF2 | 1 | solo | [`wf0032.md`](wf0032.md) |
| **WF33** | Recursive re-entry with shared fuel | `proposal` | `procedure_extension` | 9 | WF9, WF20 | fuel-bounded | relay | [`wf0033.md`](wf0033.md) |
| **WF34** | Future-faithful compression & bounded context | `proposal` | `procedure_extension` | 8 | WF8, WF22 | k | relay | [`wf0034.md`](wf0034.md) |
| **WF35** | Proposal-channel comparison | `proposal` | `experiment_design` | 6 | WF6, WF12 | channels x items | sweep_with_shared_judge | [`wf0035.md`](wf0035.md) |
| **WF36** | Guarded staged slot materialisation | `proposal` | `procedure_extension` | 5 | WF8 | k | relay | [`wf0036.md`](wf0036.md) |
| **WF37** | Evidence-bound harness evolution | `proposal` | `meta_workflow` | 8 | WF19, WF22 | budget-capped | research_cell | [`wf0037.md`](wf0037.md) |
| **WF38** | Diagnostic-trace proposal selection | `proposal` | `procedure_extension` | 3 | WF9 | budget-capped | proposer_with_residual_feedback | [`wf0038.md`](wf0038.md) |
| **WF39** | Authority firewall gate | `proposal` | `harness_gate` | 5 | WF1, WF23 | 0 | solo | [`wf0039.md`](wf0039.md) |
| **WF40** | Restart boundary after exhausted repair | `proposal` | `procedure_extension` | 9 | WF9, WF20 | restarts x fuel | proposer_with_residual_feedback | [`wf0040.md`](wf0040.md) |
| **WF41** | Detector adequacy & two-signal admission | `proposal` | `meta_workflow` | 7 | WF14 | budget-capped | red_team_pair | [`wf0041.md`](wf0041.md) |
| **WF42** | Reasoning-trace validation | `proposal` | `procedure_extension` | 5 | WF10, WF21 | budget-capped | red_team_pair | [`wf0042.md`](wf0042.md) |
| **WF43** | Gate-honesty & answer-free leak audit | `proposal` | `harness_gate` | 5 | WF23 | 0 | red_team_pair | [`wf0043.md`](wf0043.md) |
| **WF44** | Exact certificate presets | `proposal` | `task_preset` | 4 | WF11, WF10 | 1 | solo | [`wf0044.md`](wf0044.md) |
| **WF45** | Finite terminal selector & plenitude test | `proposal` | `procedure_extension` | 2 | WF7 | 1 | solo | [`wf0045.md`](wf0045.md) |
| **WF46** | Boundary sufficiency & gluing diagnostic | `proposal` | `procedure_extension` | 3 | WF4 | 5 | parallel_isolated_then_global | [`wf0046.md`](wf0046.md) |
| **WF47** | Resumable bounded frontier search | `proposal` | `procedure_extension` | 3 | WF9 | budget-capped | relay | [`wf0047.md`](wf0047.md) |
| **WF48** | Commit-reveal with hostile mutation gate | `proposal` | `harness_gate` | 5 | WF11, WF23 | budget-capped | red_team_pair | [`wf0048.md`](wf0048.md) |
| **WF49** | Query-preservation stage & mode campaign | `proposal` | `experiment_design` | 8 | WF8, WF22 | modes x items | sweep_with_shared_judge | [`wf0049.md`](wf0049.md) |

---

## 2. Core Runtime Architecture

The PFP execution runtime is implemented in `pfp/infrastructure/workflow_runtime.py`, `pfp/infrastructure/workflow_accounting.py`, and `pfp/infrastructure/workflow_tasks.py`.

```
                    +------------------------------------+
                    |       Task Specification (.json)   |
                    +------------------------------------+
                                      |
                                      v
                    +------------------------------------+
                    |     validate_task() & prepare()    |
                    +------------------------------------+
                                      |
                    +-----------------+------------------+
                    | Frozen Execution Directory        |
                    | - task.json                        |
                    | - prepared.json                    |
                    | - system_prompt.txt                |
                    | - user_prompt.txt                  |
                    | - response_schema.json             |
                    | - preparation_manifest.json (SHA)  |
                    +------------------------------------+
                                      |
                         [ Accounted Budget Gateway ]
                         (Atomic Reservation, $0.004999)
                                      |
                                      v
                             Provider Dispatch
                                      |
                                      v
                    +------------------------------------+
                    | response.raw                       |
                    +------------------------------------+
                                      |
                                      v
                    +------------------------------------+
                    | Deterministic Host Checker / Judge |
                    +------------------------------------+
                                      |
                    +-----------------+------------------+
                    | Sealed Receipt Directory           |
                    | - receipt.json                     |
                    | - receipt_manifest.json (SHA-256)  |
                    | - collection.json (if emitted)     |
                    | - provider.json (if accounted)     |
                    +------------------------------------+
                                      |
                                      v
                    +------------------------------------+
                    | replay_run() (Offline Bit-for-Bit) |
                    +------------------------------------+
```

### 2.1 The `WorkflowRuntime` Lifecycle

The `WorkflowRuntime` class governs the complete lifecycle of a single workflow attempt through four strictly ordered phases:

1. **`prepare_run(spec, output_dir)`:**
   - Validates the input task dictionary against `task_spec.schema.json`.
   - Projects the task through `PreparePfpTaskTurnUseCase` with the workflow's declared system prompt template.
   - Creates the destination folder and atomically writes five immutable preparation files:
     - `task.json`: The raw validated task specification.
     - `prepared.json`: The frozen binding metadata and prompt dictionary.
     - `system_prompt.txt`: UTF-8 encoded system prompt string.
     - `user_prompt.txt`: UTF-8 encoded user prompt string.
     - `response_schema.json`: Strict JSON schema required for the candidate reply.
   - Computes SHA-256 digests of all five files and seals them into `preparation_manifest.json`.
   - **Crucial Invariant:** Preparing a run never connects to the network or calls any provider.

2. **`run_accounted(spec, output_dir, gateway, model, max_output_tokens)`:**
   - Enforces the budget ceiling ($0.004999 max liability per run).
   - Validates that the gateway has `max_calls == 1` and has not been depleted.
   - Re-reads and verifies `preparation_manifest.json` before any network activity.
   - Dispatches a single candidate request through `EstimatedBudgetGateway`.
   - Atomically transitions accounting state from `reserved` to `settled` upon reply receipt.
   - Saves raw wire reply to `response.raw` and provider telemetry to `provider.json`.

3. **`check_run(output_dir, reply_path, fixture=False)`:**
   - Used for grading externally supplied replies (e.g. hand-authored fixtures or offline recordings).
   - Verifies preparation integrity via `_load_preparation`.
   - Invokes `workflow.check_reply(spec, raw_reply)` to run deterministic host checks.
   - If the workflow extracts material, runs `collect_emitted` to generate `collection.json`.
   - Writes `receipt.json` and seals the entire directory with `receipt_manifest.json`.

4. **`replay_run(output_dir)`:**
   - Performs offline, zero-network, bit-for-bit replay verification of an existing sealed run.
   - Re-hashes all files named in `receipt_manifest.json` and asserts exact digest equality.
   - Verifies that the implementation code digests and dependencies (`jsonschema`, `PyYAML`) match the recorded runtime identity.
   - Independently reconstructs the preparation turn and re-evaluates `workflow.check_reply` against `response.raw`.
   - Asserts that re-computed status and failure classes match `receipt.json` verbatim.

### 2.2 Manifest Sealing and Cryptographic Custody

Every state transition is bound by SHA-256 content addressing:

$$\text{digest}(b) = \operatorname{SHA256}(b).\text{hexdigest}()$$

The `receipt_manifest.json` records:
- `workflow_id`: Workflow identifier string (e.g. `"WF1"`).
- `version`: Workflow schema version (e.g. `"0.2.0"`).
- `files`: Dictionary mapping every filename in the run directory to its exact SHA-256 hex digest.
- `implementation`: Dictionary recording the SHA-256 digests of all 11 core source files comprising the host evaluation runtime, plus environment package versions.

Any byte-level modification of prompts, inputs, responses, or checker code invalidates the receipt with `RECEIPT_DIGEST_MISMATCH` or `IMPLEMENTATION_MISMATCH`.

### 2.3 Accounted Budget Gateway (`EstimatedBudgetGateway`)

Multi-agent and concurrent workflows (WF4, WF5) execute under `EstimatedBudgetGateway` (`pfp/infrastructure/workflow_accounting.py`):
- **Atomic Batch Reservation:** Up to 64 requests are reserved in a single database transaction against `accounting.sqlite3`.
- **Pre-dispatch Liability Check:** The estimated cost of the entire batch is reserved before any worker thread is spawned. If liability exceeds the configured budget limit, the entire batch is refused with `ESTIMATED_BUDGET_EXCEEDED` before making any API calls.
- **Barrier Synchronization:** A thread barrier (`threading.Barrier(len(requests))`) synchronizes workers so that requests dispatch concurrently.
- **Durable Failure Accounting:** If a worker thread fails or times out, the transaction transitions to `outcome_unknown`, locking the liability so budgets cannot be silently overrun.

---

## 3. Related Systems

- **Canonical 11-Stage Pipeline:** Documented in [`canonical_pipeline.md`](canonical_pipeline.md). Governs staged model proposals across 5 panel seats with kinetic proofreading.
- **PFP Lab Governor:** Documented in [`pfp_lab_governor.md`](pfp_lab_governor.md). Governs weighted constraint graphs with exact rational arithmetic over four fundamental moves (`ASSERT`, `CUT`, `VERIFY`, `RETRACT`).

---

## 4. Claim Hygiene Evaluation

In accordance with repository claim hygiene standards:

1. **What the Evidence Supports:**
   - The repository implements 5 fully functional, installable, deterministic workflows (WF1–WF5) with offline replayable testing.
   - The runtime architecture strictly enforces bit-for-bit cryptographic verification against sealed manifests.
   - Untrusted model outputs are graded solely by deterministic Python host checkers; model consensus does not authorize acceptance.
2. **What the Evidence Does Not Support:**
   - The repository does not establish that language models can reliably solve arbitrary mathematical problems.
   - Workflows WF6 through WF49 are architectural specifications derived from pilot records; they do not represent implemented live automated runners in this repository.
3. **Narrowest Defensible Claim:**
   - The PFP runtime provides a deterministic, cryptographically sealed verification harness that restricts untrusted model interactions to typed JSON contracts, enforces strict cost ceilings, and independently re-evaluates all results without granting intrinsic authority to model text.
4. **Next Test Needed:**
   - Implement an automated runner for WF9 (Bounded check-and-repair) and execute it against certified challenge C011, measuring exact rational defect reductions across repair attempts.
