# Handoff Report: PFP Workflows and Execution Architecture Survey

**Investigator:** `teamwork_explorer_survey_2`  
**Date:** 2026-11-06  
**Type:** Hard Handoff (Task Complete)  
**Target:** Multi-agent swarm / Parent orchestrator (`cd4969be-0ada-47e9-af34-467699d872e1`)

---

## 1. Observation

1. **Repository Layout and Installed Workflows:**
   - In `pyproject.toml` (lines 37–41): Console scripts `pfp-wf1` through `pfp-wf5` are registered pointing to `pfp.workflows.wf0001.runner:main` through `pfp.workflows.wf0005.runner:main`. `pfp-lab` and `pfp-lab-web` are registered as console scripts pointing to `pfp_lab.cli.main:entry` and `pfp_lab.web.app:entry` (lines 35–36).
   - In `workflows/README.md` (lines 3–6): "WF1–WF5 run today; WF6–WF49 are proposals with their design written down. Open a folder's README to see what the workflow does...".
   - In `workflows/dag/workflow_dag.json`: Contains 49 workflow nodes (`WF1` through `WF49`), with `schema_version: "pfp.workflow-dag.v1"` and `AuthorityEffect: "None"`. Five nodes (`WF1`–`WF5`) have `"status": "implemented"`; 44 nodes (`WF6`–`WF49`) have `"status": "proposal"`.

2. **Workflow Runtime & Custody:**
   - In `pfp/infrastructure/workflow_runtime.py`:
     - Lines 16–23: `_PREPARED_FILES` (`task.json`, `prepared.json`, `system_prompt.txt`, `user_prompt.txt`, `response_schema.json`) and `_CHECKED_FILES` (`preparation_manifest.json`, `response.raw`, `receipt.json`).
     - Lines 99–116 (`prepare_run`): Writes preparation files and generates `preparation_manifest.json` with SHA-256 digests.
     - Lines 132–182 (`_finish`): Invokes workflow judge, writes `response.raw` and `receipt.json` with `authority_effect: "None"`, and signs `receipt_manifest.json`.
     - Lines 201–250 (`replay_run`): Offline bit-for-bit replay; recomputes all checks without external provider calls and asserts exact hash matches.
   - In `pfp/infrastructure/workflow_accounting.py`:
     - Lines 25–67: `EstimatedBudgetGateway.complete_batch_result` reserves batches atomically with a default $0.004999 budget cap, 2× headroom, and 80% stop threshold.

3. **Multi-Agent Gluing and Leak Suppression:**
   - In `pfp/workflows/wf0003/workflow.py` (lines 156–166): `text_screen` recursively searches for decimal digits in guidance text (`re.search(r"\d", value)`), refusing guidance with `NUMERICAL_GUIDANCE_FORBIDDEN` to prevent answer leakage.
   - In `pfp/workflows/wf0004/workflow.py` (lines 249–286): `evaluate_global` requires all 5 agents to be locally green, correct, and agree on overlap. Invokes `LggrGluingAdapter().evaluate_boundary(local, int(green))` (`ops/adversary/infrastructure/lggr_adapter.py`) to compute gluing defect $\Delta_E = E_G - \prod E_i$.
   - In `pfp/workflows/wf0005/rewrite.py` (lines 23–100): Implements EBNF grammar encoding and decoding, bounding wire bytes ($\le 65536$) and expression depth ($\le 3$).

4. **11-Stage Canonical Pipeline and Kinetic Proofreading:**
   - In `pfp/domain/stages/stages.py` (lines 20–45): Defines 11 stages (`ADMIT`, `IDEATION`, `AUDIT`, `L2_EXTRACTION`, `EVALUATION`, `ADVERSARIAL`, `CHALLENGE_REPLAY`, `SELECTION`, `RECEIPT`, `HAND_OFF`, `EVIDENCE_PLAN`). Host stages are `{1, 5, 7, 8, 9, 10}`.
   - In `pfp/use_cases/pfp_stages.py` (lines 140–208): `RunPfpPipelineUseCase` enforces stage dispatch, terminal evaluation (`BLOCKED_BY_EVIDENCE`, `OPEN_OBSTRUCTION`, `VERIFIED`, `VERIFIED_WITH_RESIDUALS`), and host replay.
   - In `pfp/gate.py` (lines 19–36): `CandidateEvaluationGateV1` enforces F-BIO-02 kinetic proofreading: a candidate marked `REJECTED` raises `STAGE_REENTRY_REFUSED` if re-evaluated by the same checker set.

5. **PFP Lab and Exact Rational Governor:**
   - In `pfp_lab/core/governor.py` (lines 1–80, 248–350): Evaluates `ASSERT`, `CUT`, `VERIFY`, and `RETRACT` over exact rationals (`fractions.Fraction`). Refuses proposals that increase defect $D$ or obstruction $\Phi_1$.

6. **Operad Compiler:**
   - In `operads/application/typed_workflow_compiler.py` (lines 327–363): Compiles `TypedWorkflowV1` planar tree into `CompiledWorkflowV1` / `CandidateInstructionPlanV01` while checking port contracts and capability ceilings.

---

## 2. Logic Chain

1. **Premise:** The dispatch instruction requests an enumeration of every workflow in the repository, their inputs, state transformations, outputs, operators, and failure behaviors, along with PFP instantiation and CLI/test mappings.
2. **Direct Finding from Repository Inspection:** The repository segregates workflows into:
   - Implemented automated workflows: WF1 to WF5 in `pfp/workflows/` (runnable offline via `pytest pfp/workflows/tests/test_standalone.py` or CLI `pfp-wf1` .. `pfp-wf5`).
   - Proposed workflow designs: WF6 to WF49 in `workflows/` and `workflows/dag/workflow_dag.json`.
   - Canonical 11-stage pipeline in `pfp/use_cases/pfp_stages.py`.
   - Weighted constraint graph governor in `pfp_lab/core/governor.py`.
   - Category-theoretic typed workflow compiler in `operads/application/typed_workflow_compiler.py`.
3. **Execution Pattern Trace:** Tracing from `WorkflowRuntime` to individual workflow modules reveals an immutable custody chain: every run prepares files into a directory, computes a SHA-256 manifest, executes an accounted provider call or fixture, runs a deterministic host judge, and signs a final receipt manifest.
4. **PFP Gating Invariance:** Verification is strictly one-sided: the host alone accepts; model output agreement is never treated as proof. Leakage is prevented by AST depth bounding (WF5) and digit suppression (WF3). Non-factorization is measured by LGGR $\Delta_E$ (WF4).
5. **Conclusion Formulation:** The architecture constitutes a self-contained, formally governed framework for running untrusted LLM proposals against deterministic oracles.

---

## 3. Caveats

1. **Unexecuted Proposals (WF6–WF49):** WF6 through WF49 are structural designs and specifications extracted from the pilot research estate. They are not implemented as executable runners in this repo; only WF1–WF5 are executable.
2. **Private Model Runtimes for Historical Pilots:** The raw pilot captures in `workflows/library/evidence/` and `workflows/wf*/pilots/` contain historical response artifacts; replicating the live model calls requires private API keys and models that may change over time.
3. **Scope of Claim Hygiene:** The mathematical results (e.g. cycle basis decomposition, Smith normal form in certified challenges C011–C060) are verified for the specific finite combinatorial models declared; they do not imply universal reasoning capability in commercial LLMs.

---

## 4. Conclusion

The Proposal Fidelity Protocol repository contains a fully structured, multi-tier workflow architecture:
- 49 cataloged workflow designs (WF1–WF49), of which WF1–WF5 are runnable via CLI tools `pfp-wf1` .. `pfp-wf5`.
- A 11-stage canonical PFP pipeline (`RunPfpPipelineUseCase`) with 5 specialized panel seats and deterministic host gating.
- An exact rational graph governor (`pfp_lab`) operating over $\mathbb{Q}$ with four fundamental moves (`ASSERT`, `CUT`, `VERIFY`, `RETRACT`).
- An operad workflow compiler (`operads`) enforcing category-theoretic port contracts and single-consumer planar tree lowering.
- Full offline test coverage with 50 certified challenges (C011–C060, ~5,100 tests) and parameterized standalone workflow test suites.
The entire survey is written to `.agents/teamwork/teamwork_explorer_survey_2/survey_report.md`.

---

## 5. Verification Method

To independently verify these findings, run the following commands from the repository root:

1. **Verify Standalone Automated Workflows (WF1–WF5):**
   ```powershell
   python -m pytest pfp/workflows/tests/test_standalone.py -v
   ```
   *Expected:* All parameterized tests pass across WF1–WF5, confirming accounted runs and bit-for-bit replay.

2. **Verify PFP Lab Governor & Exact Rational Arithmetic:**
   ```powershell
   python -m pytest pfp_lab/tests/test_governor.py pfp_lab/tests/test_admission.py -v
   ```
   *Expected:* All tests pass with zero floating-point assertions.

3. **Verify 49 Workflow DAG Nodes:**
   ```powershell
   python -c "import json; d=json.load(open('workflows/dag/workflow_dag.json', encoding='utf-8')); assert len(d['nodes']) == 49; print('Verified 49 nodes in workflow DAG')"
   ```

4. **Verify Certified Challenges:**
   ```powershell
   python -m pytest workflows/tasks/certified_challenges/c011_cycle_rank_ladder_coboundary_repair -q
   ```

*Invalidation Conditions:*
- If any runner allows model output to bypass host verification or claims `AuthorityEffect` other than `"None"`.
- If WF1–WF5 fail offline replay verification (`replay_verified is False`).
