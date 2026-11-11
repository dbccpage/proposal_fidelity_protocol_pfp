# Handoff to Claude: Implementing the Remaining 44 Workflow Families (`WF6`–`WF49`) & Local Gemma 4 Execution

**Date:** 2026-11-11  
**Repository:** `c:\Users\a343o\source\repos\proposal_fidelity_protocol_pfp`  
**Base (`main`):** `85f25e2c1575491afe7500dc5c691fe750f21fee` (PR #63 merged)  
**Active PR Branch:** `codex/gemini-five-seam-mechanisms-20261111` ([PR #70](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/70))  
**Live Paid Spend Authorized Without Explicit Per-Manifest User Admission:** `USD 0.000000` (historical settled total remains frozen at `USD 0.055614` / `55,614` microUSD)

---

## 1. What We Have Done So Far

1. **Merged PR #63 into `main` (`85f25e2c`):**
   - `dag/benchmark/eis_pciv_workflows.py` (`eis_pciv_guarded_charpoly_v1`, `eis_pciv_ablation_no_thymus_v1`, `eis_pciv_ablation_single_signal_v1`), `dag/benchmark/host_charpoly_workflows.py`, `pfp_core/{__init__,fidelity,operad_pipe,immunity,civilization,normalize,legacy_importer}.py`, and `benchmarks/industry_replacement/` are all on `main`.
2. **Implemented the 5-Seam LLM Intervention & Receipt-to-Weight Engine ([PR #70](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/pull/70)):**
   - `pfp_core/llm_mechanisms.py` + `pfp_core/tests/test_llm_mechanisms.py` + `benchmarks/llm_mechanisms/{run_five_seam_showcase.py,five_seam_showcase_results.json,README.md,tests/test_five_seam_showcase.py}`:
     - **Seam 1 (Sampling Parameters):** `SamplingConfigV1` + `evaluate_sampling_seam` (`WholeRunBudget`, $T=0$ replicate collapse under `quotient_workflows`, `certificate_first` vs. `majority_vote` / `greedy_first`).
     - **Seam 2 (Logit & Grammar Decode):** `LogitGrammarControllerV1` + `verify_decode_receipt_exact` (`CARRIER_MASK`, `LOGIT_BIAS`, `JSON_SCHEMA`, `GBNF`, and Layer-2 syntax vs. Layer-3 `HostOracleContext` semantic verification).
     - **Seam 3 (Host-Controlled Scratchpad):** `HostScratchSessionV1` + `detect_stationary_attractor_exact` (multi-turn `C006` $K_4$ coboundary repair $\Phi_1: 7 \to 4 \to 1 \to 0$, `AM-4` stationary attractor detection `RepeatedCut`/`RepeatedSettledAssert`, and `Treg` circuit-breaker suspension).
     - **Seam 4 (Attention Heads, KV Surgery & Activation Steering):** `OpenWeightMechanismRunnerV1` + `resolve_transformer_layers` supporting both `Llama`/`Qwen` (`model.model.layers`) and multimodal `Gemma 4` (`model.language_model.layers`) eager attention layouts, EIS Two-Signal gating (`evaluate_attention_intervention_gate`, refusing `TWO_SIGNAL_COLLAPSE`), and orthogonal equal-L2-norm random steering controls (`build_equal_norm_random_vector`).
     - **Seam 5 (Weights / `finetune_on_antibodies` from PFP Verified Receipt Triples):** `ReceiptToWeightPipelineV1` + `LowRankWeightAdapterV1` + `VerifiedReceiptTripleV1` + `WeightAdapterReceiptV1` (disjoint hold-out enforcement `HOLDOUT_CONTAMINATION_REFUSAL`, PCIV taint refusal `TAINTED_LINEAGE_RECEIPT_REFUSED`, witness-multiplicity protection `ALTERNATIVE_VALID_WITNESS_NOT_REJECTED`, `SealedCausalWitness`-bound SFT/DPO JSONL compilation, and frozen-base DPO LoRA training beating an equal-Frobenius-norm random LoRA control on held-out seeds).

---

## 2. Hard Custody & Firewall Rules (Do Not Violate)

1. **32,261 Pinned Files (`dag/file_inventory.json`):**
   - Never modify any file listed in `dag/file_inventory.json` (`test_branch_touches_only_allowed_paths` in `benchmarks/industry_replacement/tests/test_industry_replacement.py` checks `git diff` against `origin/main` and fails if any of the 32,261 pinned files are touched).
   - Note that `pfp/workflows/wf0001`..`wf0005` and existing files under `pfp/`, `eis/`, `pciv/`, `operads/`, and `workflows/wf*` **are** in `dag/file_inventory.json`.
2. **Industry Replacement Manifest Custody (`benchmarks/industry_replacement/manifest_*.json`):**
   - `benchmarks/industry_replacement/build_manifests.py` hashes the import closure of `pfp_core/__init__.py`, `pfp_core/fidelity.py`, `pfp_core/immunity.py`, `pfp_core/civilization.py`, `pfp_core/operad_pipe.py`, `pfp_core/normalize.py`, and `pfp_core/legacy_importer.py`. Do **not** modify those 7 files unless you intentionally rebuild and re-verify the manifests; instead, add new modules under `pfp_core/` (e.g., `pfp_core/workflows_runtime/` or `pfp_core/wf_families.py`) or `dag/benchmark/`.
3. **Evaluator Firewall & Zero Paid Spend:**
   - Never read `dag/benchmark/pilot_20261110/evaluator_rubric.json` or `benchmarks/industry_replacement/sealed_evaluator/t*_sealed.py` constants into any prompt or solver.
   - Make zero live paid API calls (`USD 0.00`).

---

## 3. Primary Task: Implement the Remaining 44 Workflow Families (`WF6` through `WF49`)

In `dag/workflows_dag.json` (built from `dag/reviews/workflows_audit.json` by `dag/build_dags.py`), there are **49** `existing_workflow_family` nodes:
- **5 Implemented (`WF1`–`WF5`):** `WF1` (Typed answer), `WF2` (Full slots), `WF3` (Mine, then solve), `WF4` (Five agents + LGGR), `WF5` (Checked rewrite).
- **44 Proposals (`WF6`–`WF49`):** Listed below in topological layer order (`Layer 1` $\to$ `Layer 9`).

### Topological Build Order for `WF6`–`WF49`

#### Layer 1 (Depends only on `WF1`)
- **`WF7` — Typed refusal** (`deps: ['WF1']`, `merge_into: None`, `path: workflows/wf07_typed_refusal`):
  - *Math / Host Check:* Partition inputs into solvable vs. obstructed (`unsat`/`ambiguous`/`underdetermined`); accept iff solvable inputs get certified solutions and obstructed inputs emit a typed refusal (`RepairRefusalV1` / `REFUSAL_CODE`) with a machine-checked obstruction witness.
- **`WF30` — Constraint-forcing anti-recitation** (`deps: ['WF1']`, `merge_into: None`, `path: workflows/wf30_constraint_forcing_anti_recitation`):
  - *Math / Host Check:* Perturb canonical textbook parameters (e.g. non-standard boundary/gauge coefficients) while preserving exact solver checkability; reject memorized canonical answers that fail the perturbed host predicate.
- **`WF31` — Multi-agent tournament with held-out cross-validation** (`deps: ['WF1']`, `merge_into: None`, `path: workflows/wf31_multi_agent_tournament_with_held_out_cross_validation`):
  - *Math / Host Check:* Multiple candidate proposals evaluated on public checks + disjoint held-out validation splits; refuse selection when calibration and held-out splits overlap.

#### Layer 2 (Depends on `WF1`, `WF2`, `WF7`)
- **`WF9` — Bounded check-and-repair** (`deps: ['WF2']`, `merge_into: None`, `path: workflows/wf09_bounded_check_and_repair`):
  - *Math / Host Check:* Up to $B$ bounded repair turns driven strictly by deterministic host checker diagnostic residuals (`HostOracleContext.failed`), billed to a single `WholeRunBudget`.
- **`WF13` — Exact-domain capsule battery** (`deps: ['WF1', 'WF7']`, `merge_into: 'WF1'`, `path: workflows/wf13_exact_domain_capsule_battery`):
  - *Math / Host Check:* Batch execution over a finite battery of exact-domain capsules (solvable + refusal controls) with per-capsule deterministic verification and denominator preservation.
- **`WF24` — Pinned-token operational scratchpad** (`deps: ['WF2']`, `merge_into: None`, `path: workflows/wf24_pinned_token_operational_scratchpad`):
  - *Math / Host Check:* Host-maintained operational scratchpad (`HostScratchSessionV1`) with pinned token/state digests and zero-authority intermediate steps.
- **`WF32` — Claim-scoped receipt** (`deps: ['WF1', 'WF2']`, `merge_into: None`, `path: workflows/wf32_claim_scoped_receipt`):
  - *Math / Host Check:* Binds each atomic claim in a structured response to the specific host predicate (`evidence_sha256`) that checked it; flags any unchecked claim as `uncertified_obligations`.
- **`WF45` — Finite terminal selector and plenitude test** (`deps: ['WF7']`, `merge_into: None`, `path: workflows/wf45_finite_terminal_selector_and_plenitude_test`):
  - *Math / Host Check:* Exhaustive check that a finite terminal enum covers both solved and refusal outcomes without vacuous pass-through or dead terminal branches.

#### Layer 3 (Depends on Layer 1–2 + `WF3`, `WF4`)
- **`WF10` — Local-to-global obstruction certificate** (`deps: ['WF4', 'WF9']`, `merge_into: 'WF4'`, `path: workflows/wf10_local_to_global_obstruction_certificate`):
  - *Math / Host Check:* Local patch compatibility vs. global 1-cochain cycle residual ($\Phi_1 = \sum_c |r_c|$); certifies either global gluing ($\Phi_1 = 0$ with vertex potential $\phi$) or a non-zero cycle obstruction witness.
- **`WF11` — Dual-certificate synthesis** (`deps: ['WF3', 'WF9']`, `merge_into: 'WF1'`, `path: workflows/wf11_dual_certificate_synthesis`):
  - *Math / Host Check:* Primal solution paired with an exact rational dual witness ($z$) checked for dual feasibility ($|z_e| \le w_e$), divergence matching, and zero primal-dual gap ($\Phi_1(r) = \langle z, r \rangle$, rejecting weak-duality-only lower bounds per `DER-150`).
- **`WF25` — Hierarchical decimation** (`deps: ['WF24']`, `merge_into: None`, `path: workflows/wf25_hierarchical_decimation`):
  - *Math / Host Check:* Eliminate settled degree-2 / tree variables via exact Schur/Gaussian/cochain decimation while preserving fundamental cycle residuals.
- **`WF27` — Hinted retraction with a stationary-loop detector** (`deps: ['WF9']`, `merge_into: 'WF9'`, `path: workflows/wf27_hinted_retraction_with_a_stationary_loop_detector`):
  - *Math / Host Check:* `AM-4` stationary loop detection (`RepeatedCut`, `RepeatedSettledAssert`) paired with answer-free structural retraction hints when $\Phi_1$ fails to descend.
- **`WF38` — Diagnostic-trace proposal selection** (`deps: ['WF9']`, `merge_into: 'WF9'`, `path: workflows/wf38_diagnostic_trace_proposal_selection`):
  - *Math / Host Check:* Ranks candidate repairs by exact host defect reduction ($\Delta \Phi_1 < 0$) rather than model self-confidence.
- **`WF46` — Boundary sufficiency and gluing diagnostic** (`deps: ['WF4']`, `merge_into: None`, `path: workflows/wf46_boundary_sufficiency_and_gluing_diagnostic`):
  - *Math / Host Check:* Verifies whether interface boundary packets between sub-agents uniquely determine global consistency (`TypedPacketShadow` / `DER-05` fibre check).
- **`WF47` — Resumable bounded frontier search** (`deps: ['WF9']`, `merge_into: None`, `path: workflows/wf47_resumable_bounded_frontier_search`):
  - *Math / Host Check:* Checkpointed best-first/beam search over host-verified intermediate states under a single persistent `RunLedger` (forbidding budget reset on resume).

#### Layer 4 (Depends on Layers 1–3 + `WF5`)
- **`WF6` — Dialect sweep** (`deps: ['WF5']`, `merge_into: 'Sweep'`, `path: workflows/wf06_dialect_sweep`):
  - *Math / Host Check:* Compiles $k$ query-preserving prompt dialects ($\text{decode}(\rho_k(s)) = q(s)$) and evaluates pairwise item-by-item host acceptance under matched model/parameters.
- **`WF8` — Staged sealed packets** (`deps: ['WF2', 'WF5']`, `merge_into: None`, `path: workflows/wf08_staged_sealed_packets`):
  - *Math / Host Check:* Multi-stage pipeline where each stage's output packet is SHA-256 sealed (`SealedCausalWitness`) and checked against `ProtectedContract` fences before entering stage $t+1$.
- **`WF16` — Substrate crosswalk** (`deps: ['WF5', 'WF10']`, `merge_into: 'WF5'`, `path: workflows/wf16_substrate_crosswalk`):
  - *Math / Host Check:* Cross-substrate isomorphism check (e.g., mapping graph coboundary / Pauli commutation / finite state transition representations of the same task and verifying identical host verdicts).
- **`WF17` — Witnessed-difference programme** (`deps: ['WF10', 'WF11']`, `merge_into: 'WF10'`, `path: workflows/wf17_witnessed_difference_programme`):
  - *Math / Host Check:* `PrimitiveDifference` (`DER-01`) congruence and separator check: every claimed distinction between two candidate states must provide a separating host predicate.
- **`WF21` — Structural prompt rewriting** (`deps: ['WF5']`, `merge_into: 'WF5'`, `path: workflows/wf21_structural_prompt_rewriting`):
  - *Math / Host Check:* Edit prompts via `PromptMutationEngineV1` outside `ProtectedSpanV1` fences while verifying zero-leakage of answer keys.
- **`WF23` — Judge-packet custody audit** (`deps: ['WF11']`, `merge_into: None`, `path: workflows/wf23_judge_packet_custody_audit`):
  - *Math / Host Check:* Verifies that the evaluator packet contains only public task bindings and raw candidate bytes (zero oracle leakage, forged stdout line rejection).
- **`WF29` — Checker synthesis scored by mutation kill rate** (`deps: ['WF11']`, `merge_into: 'WF11'`, `path: workflows/wf29_checker_synthesis_scored_by_mutation_kill_rate`):
  - *Math / Host Check:* Evaluates candidate host checkers against a battery of positive gold witnesses (must pass 100%) and adversarial mutations (scored by mutation kill fraction).
- **`WF44` — Exact certificate presets** (`deps: ['WF11', 'WF10']`, `merge_into: 'WF11'`, `path: workflows/wf44_exact_certificate_presets`):
  - *Math / Host Check:* Pre-registered exact certificate schemas (`charpoly`, `coboundary_potential`, `pauli_commutation`, `canonical_rational`) with zero-float arithmetic verification.

#### Layer 5 (Depends on Layers 1–4)
- **`WF12` — Mechanism-control arms** (`deps: ['WF6', 'WF3']`, `merge_into: 'Sweep'`, `path: workflows/wf12_mechanism_control_arms`):
  - *Math / Host Check:* Paired ablation arms across the 5 LLM intervention seams (`pfp_core/llm_mechanisms.py`) against matched null/random controls (`delta=0`, `alpha=1`, equal-norm random steering vector, equal-norm random LoRA).
- **`WF36` — Guarded staged slot materialisation** (`deps: ['WF8']`, `merge_into: 'WF8'`, `path: workflows/wf36_guarded_staged_slot_materialisation`):
  - *Math / Host Check:* Progressive slot filling where each slot is type- and invariant-checked before unlocking dependent slots.
- **`WF39` — Authority firewall gate** (`deps: ['WF1', 'WF23']`, `merge_into: None`, `path: workflows/wf39_authority_firewall_gate`):
  - *Math / Host Check:* Enforces `authority_effect == 'None'` on every model, detector, and adapter receipt; refuses any self-certifying or authority-escalating field.
- **`WF42` — Reasoning-trace validation** (`deps: ['WF10', 'WF21']`, `merge_into: None`, `path: workflows/wf42_reasoning_trace_validation`):
  - *Math / Host Check:* Step-by-step trace checker that validates intermediate equations against the terminal answer and refuses traces whose steps contradict the submitted conclusion.
- **`WF43` — Gate-honesty and answer-free leak audit** (`deps: ['WF23']`, `merge_into: None`, `path: workflows/wf43_gate_honesty_and_answer_free_leak_audit`):
  - *Math / Host Check:* Scans all prompt templates, hints, and grammar masks against sealed evaluator literals to certify zero target-answer leakage.
- **`WF48` — Commit-reveal with a hostile mutation gate** (`deps: ['WF11', 'WF23']`, `merge_into: 'WF23'`, `path: workflows/wf48_commit_reveal_with_a_hostile_mutation_gate`):
  - *Math / Host Check:* Commits candidate SHA-256 before grading and runs a hostile mutation sweep to verify the checker rejects perturbed copies of the committed answer.

#### Layer 6 (Depends on Layers 1–5)
- **`WF14` — Immune failure classification** (`deps: ['WF7', 'WF12']`, `merge_into: None`, `path: workflows/wf14_immune_failure_classification`):
  - *Math / Host Check:* Classifies refused runs into epitope categories (`RATIONAL_NONCANONICAL`, `MALFORMED_JSON`, `NONMONIC_LEADING_COEFFICIENT`, `SIGN_MISMATCH`) and tracks support via `AntibodyRegistry`.
- **`WF18` — Dossier replay campaign** (`deps: ['WF6', 'WF12']`, `merge_into: None`, `path: workflows/wf18_dossier_replay_campaign`):
  - *Math / Host Check:* Deterministic zero-call replay of frozen campaign dossiers (`raw_reply_sha256`, `input_sha256`, `source_pins`), refusing any drifted source or binary hash.
- **`WF35` — Proposal-channel comparison** (`deps: ['WF6', 'WF12']`, `merge_into: None`, `path: workflows/wf35_proposal_channel_comparison`):
  - *Math / Host Check:* Compares prompt-level rewrites vs. decoding/activation/weight channels under identical host checkers and token/cost budgets.

#### Layer 7 (Depends on Layers 1–6)
- **`WF15` — Adversary tribunal** (`deps: ['WF4', 'WF14']`, `merge_into: None`, `path: workflows/wf15_adversary_tribunal`):
  - *Math / Host Check:* Proposer + adversarial falsifier + deterministic host judge (`AuthorityEffect: None`); adversary proposals only take effect if confirmed by a failing host test case.
- **`WF19` — Failure-derived rule transfer** (`deps: ['WF12', 'WF14']`, `merge_into: None`, `path: workflows/wf19_failure_derived_rule_transfer`):
  - *Math / Host Check:* Extracts candidate `DetectorRule` / antibody guards from observed failures on training tasks, screens them through `ThymusGate` on a self-panel, and evaluates transfer on disjoint held-out tasks.
- **`WF22` — Certified cost ladder** (`deps: ['WF6', 'WF8', 'WF18']`, `merge_into: 'Sweep'`, `path: workflows/wf22_certified_cost_ladder`):
  - *Math / Host Check:* Escalates from cheap/fast arms to higher-budget arms only on host refusal, charging every rung to a single `WholeRunBudget`.
- **`WF26` — Multi-round antibody dialogue** (`deps: ['WF9', 'WF14']`, `merge_into: None`, `path: workflows/wf26_multi_round_antibody_dialogue`):
  - *Math / Host Check:* Multi-round repair where EIS Two-Signal dispositions inject specific verified failure epitopes into the repair turn without leaking answers.
- **`WF41` — Detector adequacy and two-signal admission** (`deps: ['WF14']`, `merge_into: 'WF14'`, `path: workflows/wf41_detector_adequacy_and_two_signal_admission`):
  - *Math / Host Check:* Enforces `ThymusGate` zero false-positive screening on the self-panel + `assert_signals_independent` (`HOST_OBSERVERS` + `HOST_DANGER_SIGNAL_KINDS`) before any rule can hold a run.

#### Layer 8 (Depends on Layers 1–7)
- **`WF20` — Derivation loop with lift grants** (`deps: ['WF9', 'WF10', 'WF19']`, `merge_into: 'WF9'`, `path: workflows/wf20_derivation_loop_with_lift_grants`):
  - *Math / Host Check:* Iterative derivation loop where `LIFT_REQUEST` grants structural basis data (fundamental cycles, chords, degree specs) without target values when $\Phi_1$ stalls.
- **`WF28` — Eight-role audit dialogue** (`deps: ['WF15']`, `merge_into: None`, `path: workflows/wf28_eight_role_audit_dialogue`):
  - *Math / Host Check:* Structured multi-role audit (proposer, syntax normalizer, domain checker, adversary, thymus screener, lineage auditor, budget controller, host oracle) where only the host oracle can certify.
- **`WF34` — Future-faithful compression and bounded context** (`deps: ['WF8', 'WF22']`, `merge_into: None`, `path: workflows/wf34_future_faithful_compression_and_bounded_context`):
  - *Math / Host Check:* Compresses multi-turn history into a bounded state summary (`O(|E| + b_1)`) proved sufficient for downstream host checks (`DER-05` zero-equivalence quotient).
- **`WF37` — Evidence-bound harness evolution** (`deps: ['WF19', 'WF22']`, `merge_into: None`, `path: workflows/wf37_evidence_bound_harness_evolution`):
  - *Math / Host Check:* Evolves workflow genomes in `Lineage` + `PopulationPolicyV1` (60/30/10 Front/Unmeasured/Baseline reserves) using four-axis Pareto dominance (`pass_rate`, `spent_microusd`, `total_tokens`, `wall_ms`) and transitive taint exclusion.
- **`WF49` — Query-preservation stage and mode campaign** (`deps: ['WF8', 'WF22']`, `merge_into: None`, `path: workflows/wf49_query_preservation_stage_and_mode_campaign`):
  - *Math / Host Check:* Composition of staged sealed packets (`WF8`) and mode/dialect sweeps (`WF6`) with end-to-end query preservation verification.

#### Layer 9 (Depends on Layers 1–8)
- **`WF33` — Recursive re-entry with shared fuel** (`deps: ['WF9', 'WF20']`, `merge_into: None`, `path: workflows/wf33_recursive_re_entry_with_shared_fuel`):
  - *Math / Host Check:* Sub-task decomposition where child invocations draw from a strictly decreasing shared integer fuel counter (`DER-18` no-return termination invariant) and one root `WholeRunBudget`.
- **`WF40` — Restart boundary after exhausted repair** (`deps: ['WF9', 'WF20']`, `merge_into: None`, `path: workflows/wf40_restart_boundary_after_exhausted_repair`):
  - *Math / Host Check:* When bounded repair (`WF9`) or stationary-loop escalation (`AM-4`) exhausts local repair attempts, performs a clean context restart seeded only with the immutable problem specification and verified host refusal receipts (discarding poisoned CoT history) while keeping prior spend locked in the same `WholeRunBudget`.

---

## 4. How to Implement & Test `WF6`–`WF49`

1. **Where to Place Code (Preserving Pinned File Custody):**
   - Implement the executable workflow family runners in a new unpinned package, e.g. `pfp_core/workflow_families/` (with `wf06_to_wf49.py` or per-layer modules `layer1_to_3.py`, `layer4_to_6.py`, `layer7_to_9.py`, and registry `registry.py`), or under `dag/benchmark/wf_family_runners.py`.
   - Do **not** edit any file in `dag/file_inventory.json` or the 7 files in `benchmarks/industry_replacement/manifest_*.json`'s `executed_code` closure (`pfp_core/{__init__,fidelity,immunity,civilization,operad_pipe,normalize,legacy_importer}.py`).
2. **Required Interface per Workflow (`WF6`–`WF49`):**
   - Each workflow `WFk` (`k in 6..49`) must have a registered `WorkflowFamilySpecV1` containing:
     - `wf_id` (`"WF6"` .. `"WF49"`), `name`, `layer` (`1..9`), `depends_on`, `merge_into`, `host_check_id`, `authority_effect="None"`.
     - `execute(task_bundle, *, budget: WholeRunBudget, ...)` that runs deterministically offline against fixture/replay candidates and supports live/local open-weight injection (`OpenWeightMechanismRunnerV1` or provider adapter).
     - At least **1 positive certified fixture** (`HOST_CERTIFIED` / `SOLVED` / valid typed refusal) and **1 adversarial negative/mutation fixture** that must be refused by the workflow's host check (`REFUSED` / `HOLD_OR_REPAIR`).
3. **Wiki & DAG Synchronization (`dag/build_dags.py`):**
   - Notice lines 387–402 of `dag/build_dags.py`:
     ```python
     required={node['id'] for node in wnodes if node.get('runnable') is True
               or node.get('kind')=='executable_benchmark_control'
               or node.get('status')=='implemented'}
     if required-set(documented):
         raise ValueError('Implemented workflows need Wiki entries: '+str(sorted(required-set(documented))))
     ```
   - Before flipping any `WF6`–`WF49` node in `dag/reviews/workflows_audit.json` from `"status": "proposal"` to `"status": "implemented"`, verify whether `wiki/Workflow-WF*.md` is in `dag/file_inventory.json` (none of `wiki/*` are in `dag/file_inventory.json`), create/update `wiki/Workflow-WF6.md`..`wiki/Workflow-WF49.md` and `dag/wiki/workflow_documentation.json` with exact SHA-256 digests, update `dag/reviews/workflows_audit.json` (`status: "implemented"`, `runner_source`, `tests`), and run `python dag/build_dags.py` so `dag/workflows_dag.json` validates with zero missing Wiki entries and `acyclic: True`!

---

## 5. Secondary Task: Pinned Local Open-Weight Gemma 4 Execution

- **Current Hardware / Disk State Note:** As of 2026-11-11, `C:` has `~2.66 GB` free disk space and PyTorch is CPU-only (`2.10.0+cpu`), with only the `Qwen/Qwen2.5-0.5B-Instruct` tokenizer cached in `~/.cache/huggingface/hub`.
- **When Disk Space / Checkpoint Is Staged:**
  1. Stage a pinned local safetensors checkpoint in `eager` attention mode (e.g., `google/gemma-4-9b-it` on a machine/volume with `>= 25 GB` free, or a small local open-weight checkpoint such as `HuggingFaceTB/SmolLM2-135M-Instruct` / `Qwen/Qwen2.5-0.5B-Instruct` / `google/gemma-3-1b-it` once `>3 GB` is freed) with a SHA-256 `custody.json` manifest.
  2. Run `OpenWeightMechanismRunnerV1` and `ReceiptToWeightPipelineV1` (`pfp_core/llm_mechanisms.py`) over:
     - The 3-family algebraic pilot (`cycle_sum`, `product_sign`, `commutation` in `workflows/wf19_failure_derived_rule_transfer/pilots/challenge_suite/local_mechanism_trials.py`), and
     - The 4-task industry replacement suite (`t1`–`t4` in `benchmarks/industry_replacement/arms.py`) under a pre-authorized `WholeRunBudget`.

---

## 6. Completion Conditions

The 44-workflow implementation is complete when all of the following hold:
1. **All 49 Workflow Families (`WF1`–`WF49`) Implemented & Tested:**
   - Every `WF6`–`WF49` has an executable implementation in `pfp_core/workflow_families/` (or `dag/benchmark/`) with both positive certified fixture tests and negative adversarial refusal tests passing under `pytest`.
2. **DAG & Wiki Integrity Verified:**
   - `python dag/build_dags.py` exits `0` with `acyclic: True` and all 49 workflow families (`WF1`–`WF49`) recorded as `implemented` in `dag/workflows_dag.json` with valid `wiki_documentation` SHA-256 pins.
3. **Custody, Firewall, & Linter Gates Green:**
   - `python -m pytest pfp_core/ benchmarks/llm_mechanisms/ benchmarks/industry_replacement/ dag/benchmark/test_source_custody.py -q` passes 100% (including `test_branch_touches_only_allowed_paths` confirming `0` of the `32,261` pinned files in `dag/file_inventory.json` were modified).
   - `python -m ruff check` passes with `0` errors on all new files.
   - Total new live paid API spend is `USD 0.000000`.
4. **Claim Hygiene Summary Included:**
   - Every report and PR description includes: (1) What it supports, (2) What it does not support, (3) The narrowest defensible claim, and (4) The next test needed.
