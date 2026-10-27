> Source-attributed audit appendix. Source and original-extraction hashes quoted below are distinct from the wrapped release artifact hashes recorded in source_manifest.json. Historical verdicts and quoted terminology are retained as evidence; no estate test or model call was executed by this extraction. Full machine extraction: [curriculum_007_012.json.gz](curriculum_007_012.json.gz).

# Tracks 007–012 forensic curriculum crosswalk

HEAD `58a6a1ef92e155b1fa3783081becb41de3e07734`. AuthorityEffect: None. Static source audit only; no tests, Lean, or Cargo were executed. JSON contains the complete file census, hashes, line-level mathematical/transition excerpts, notebook source cells, and contract identities. “Located” does not mean verified.

| Track | Files | Markdown | Levels | NF contracts |
|---|---:|---:|---:|---:|
| 007_oelggr | 28 | 20 | 10 | 0 |
| 008_oewas | 88 | 57 | 11 | 4 |
| 009_oeeis | 76 | 49 | 11 | 5 |
| 010_oepciv | 80 | 47 | 11 | 5 |
| 011_oeadversary | 54 | 41 | 0 | 0 |
| 012_oecogops | 33 | 22 | 9 | 0 |

## 007_oelggr: Local Green, Global Red

Mathematical primitives:
- Signed evaluator defect Δ_E=E_g−∏E_i ∈ {−1,0,1}; local-green/global-red is −1. `education/documentation/007_oelggr/README.md:51`
- Finite observation fibers Q(v1)=Q(v2), linear kernel and Gram operator QᵀQ. `education/documentation/007_oelggr/levels/level_06_nonlinear_aggregation_adjoint_probing.md:30`
- Inverse systems, completion-relative solutions, 2-adic thread versus integer realization. `education/documentation/007_oelggr/local_green_global_red_foundational_series.md:94`

Transitions and executable evidence:
- Evaluated paths compose only with exact matching intermediate interfaces; six-role planner/proposer/governor/worker/arbiter/auditor overlay. `education/documentation/007_oelggr/local_green_global_red_foundational_series.md:62` [source_declared]
- No-recovery/soundness requires checking the actual joint observation kernel against the defect map. `engine/crates_rs/core_local_green_global_red_lggr/src/lggr_v.rs:88` [executable_owner_located_not_run]

Executable owners: `engine/crates_rs/core_local_green_global_red_lggr/Cargo.toml:3`, `engine/crates_rs/core_local_green_global_red_lggr/src/lggr_v.rs:171`, `engine/crates_rs/core_symbol_game/src/lggr.rs:110`, `pfp/domain/ast_cochain/models.py:19`.

No separate normal-form contract directory was found; its mathematical states and typed verdicts should not be renamed a proved normal form.

Qualifications:
- README cites absent legacy engine/crates/evaluated_path_kernels_local_green_global_red and obsolete series directory 012_...; current paper series is 001_... and Rust package core_epk lives in core_local_green_global_red_lggr.
- Adjoint probes from the same fixed linear Q cannot distinguish a vector in ker Q: <Q*λ,ξ>=<λ,Qξ>=0. Nonlinear Q also needs a derivative at a named base point; a globally linear kernel argument cannot be transferred without premises.
- Level05 all-green iff x lies in joint kernel needs evaluators that exactly test zero defects; arbitrary Boolean evaluators do not imply it. Unbounded inconsistency needs an unbounded carrier/family; a single finite carrier admits a constant upper bound.

## 008_oewas: Workflows, Agents, Skills; operads

Mathematical primitives:
- Closed ten-colour vocabulary State, Proof, Paper, Code, Contract, Receipt, Ledger, Diagram, Audit, Post. `workflows_agents_skills/domain/operad/colours.py:24`
- Multi-input/single-output operations O(c1,…,ck;cout), units, AgentSlice capabilities and planar trees. `education/documentation/008_oewas/levels/README.md:36`

Transitions and executable evidence:
- Partial composition substitutes g inputs at slot i only when target(g)=source(f)[i]. `workflows_agents_skills/domain/operad/operad.py:85` [executable_owner_located_not_run]
- Sequential associativity is checked with an index-shift witness, including wrong-index/boolean/ill-typed controls. `workflows_agents_skills/tests/unit/test_operad_sequential_associativity_witness.py:51` [test_source_located_not_run]
- Negative detectors and Treg supervision remain separate from positive authorization; DDC evidence records observed contraction. `education/documentation/008_oewas/levels/README.md:59` [source_declared]

Executable owners: `workflows_agents_skills/domain/operad/operad.py:40`, `workflows_agents_skills/domain/operad/planar.py:104`, `workflows_agents_skills/domain/planar_substitution.py:69`, `research_papers/use_cases/hand_waving_lint.py:60`.

Declared extended-form contracts:
- `nf.cochain.dhnf` — Discrete Hodge Normal Form; status `draft`, verification `absent`. `education/documentation/008_oewas/normal_forms/nf.cochain.dhnf.yaml:4`
- `nf.coda.gbqnf` — Generalized Boundary-Quotient Normal Form; status `draft`, verification `executable`. `education/documentation/008_oewas/normal_forms/nf.coda.gbqnf.yaml:4`
- `nf.coda.mur.transport` — CODA-MUR Representation Transport Contract; status `draft`, verification `absent`. `education/documentation/008_oewas/normal_forms/nf.coda.mur.transport.yaml:3`
- `nf.derivation.aonf` — Active Obstruction Normal Form; status `draft`, verification `executable`. `education/documentation/008_oewas/normal_forms/nf.derivation.aonf.yaml:3`

Qualifications:
- Operad aggregate describes symmetric operads, while inspected computational composition is planar signature substitution. A complete permutation action/equivariance proof is a separate obligation, not supplied by a class label.
- The normal-form README calls nf.derivation.aonf Agent Operad Normal Form; its actual YAML identity is Active Obstruction Normal Form. Use identity.id plus source hash, not acronym expansion, in the new specification.
- Existing curriculum explicitly routes regex hand-waving lint into Adversary. Zero procedural text matching is a proposed migration target, not the current runtime.

## 009_oeeis: Epistemic Immune System

Mathematical primitives:
- Seven disjoint role carriers Spec, FixtureBank, EvaluationReceipt, ExternalDecision, Registry, ActivationProfile, Hit; must_match versus must_not_match fixtures. `education/documentation/009_oeeis/levels/README.md:34`
- Learned guard activates on external admission ∧ detector match ∧ independent danger ∧ not suspended. `education/documentation/009_oeeis/levels/README.md:38`
- At least three pairwise-independent observations support provisional review; provisional finding is not human admission. `education/documentation/009_oeeis/levels/README.md:40`

Transitions and executable evidence:
- Candidate→provisional review assessment preserves candidate status and never admits. `eis/use_cases/antibody_admission.py:5` [executable_owner_located_not_run]
- Guard activation depends on admitted scope, host health and independently grounded danger. `eis/use_cases/guard_activation.py:66` [executable_owner_located_not_run]
- Two-signal collapse is checked when the detector authors its own danger or reuses the matcher evidence. `eis/tests/unit/test_two_signal_independence.py:95` [test_source_located_not_run]

Executable owners: `eis/domain/external_admission.py:66`, `eis/use_cases/guard_activation.py:66`, `engine/crates_rs/core_prompt_civilization/src/pharmacy.rs:33`.

Declared extended-form contracts:
- `nf.epistemic.enf` — Epistemic Normal Form; status `draft`, verification `absent`. `education/documentation/009_oeeis/normal_forms/nf.epistemic.enf.yaml:3`
- `nf.epistemic.odnf` — Observer Distinguishability Normal Form; status `draft`, verification `absent`. `education/documentation/009_oeeis/normal_forms/nf.epistemic.odnf.yaml:3`
- `nf.evidence.cdc` — CDC Evidence Form; status `draft`, verification `absent`. `education/documentation/009_oeeis/normal_forms/nf.evidence.cdc.yaml:3`
- `nf.evidence.loss_ledger` — Loss Ledger Form; status `draft`, verification `absent`. `education/documentation/009_oeeis/normal_forms/nf.evidence.loss_ledger.yaml:3`
- `nf.security.efnf` — Epistemic-Fibration Normal Form; status `draft`, verification `executable`. `education/documentation/009_oeeis/normal_forms/nf.security.efnf.yaml:5`

Qualifications:
- Innate matching, learned-guard activation, external admission and behavioral immunity are different claims.
- Curriculum normal-form frontmatter claims computed/gated; actual four of five copied NF contracts say verification_status absent. Metadata cannot replace executable evidence.
- AB001–019 canonical mathematical register is not the live detector/admission catalog; no blanket AB-id→activated-guard equivalence is established.

## 010_oepciv: Prompt Civilization and Lamarckian evolution

Mathematical primitives:
- Genome versus execution occurrence; causal inheritance DAG versus looser reference graph. `education/documentation/010_oepciv/README.md:61`
- Exact rational Pareto selection, hop-bounded retro-inheritance d≤10 with (1/2)^d attenuation, PageRank and epoch evaporation. `education/documentation/010_oepciv/README.md:63`
- PDNF/RPNF/SCNF/SERNF/provenance are extended form contracts, explicitly not lossless relational normal-form theorems. `education/documentation/010_oepciv/normal_forms/README.md:33`

Transitions and executable evidence:
- Typed failure receipts propose child genome mutations with parent hashes and mutation tags; no in-place unrecorded ancestry change. `education/documentation/010_oepciv/README.md:41` [source_declared]
- Pareto fronts and forge mutation calculus have concrete Rust owners. `engine/crates_rs/core_prompt_civilization/src/lib.rs:29` [executable_owner_located_not_run]
- Forward causal taint and custody invalidation are separate transitions, with durable append-only event identities. `education/documentation/010_oepciv/README.md:68` [source_declared]

Executable owners: `engine/crates_rs/core_prompt_civilization/src/lib.rs:14`, `engine/crates_rs/core_prompt_civilization/src/lib.rs:39`, `education/documentation/010_oepciv/lean4/PromptCivilization.lean:14`.

Declared extended-form contracts:
- `nf.derivation.pdnf` — Primitive Difference Normal Form; status `draft`, verification `executable`. `education/documentation/010_oepciv/normal_forms/nf.derivation.pdnf.yaml:3`
- `nf.derivation.rpnf` — Replay Provenance Normal Form; status `draft`, verification `executable`. `education/documentation/010_oepciv/normal_forms/nf.derivation.rpnf.yaml:3`
- `nf.derivation.scnf` — Separation Cost Normal Form; status `draft`, verification `executable`. `education/documentation/010_oepciv/normal_forms/nf.derivation.scnf.yaml:3`
- `nf.derivation.sernf` — Split Extension-Retraction Normal Form; status `draft`, verification `executable`. `education/documentation/010_oepciv/normal_forms/nf.derivation.sernf.yaml:3`
- `nf.evidence.provenance` — Provenance Form; status `draft`, verification `absent`. `education/documentation/010_oepciv/normal_forms/nf.evidence.provenance.yaml:3`

Qualifications:
- Lamarckian adaptation is a software lineage/update calculus, not evidence that learned text becomes mathematically correct or generally immune.
- Normal-form copies remain draft contracts; provenance form declares verification absent, even though normal-form index says gated true.

## 011_oeadversary: Adversary verification and bout lifecycle

Mathematical primitives:
- Typed bout requests/results, cochain scoring, DDC/DDA traces, claim hygiene, terminal verdicts and custody bundles. `education/documentation/011_oeadversary/08_clean_architecture_runtime_and_persistence.md:45`
- Seven-act pedagogical sequence ends PASS_TO_MASTER / REFUSE / OPEN_RESIDUAL, all authority None. `education/documentation/011_oeadversary/03_7act_dialectic_bout_execution_pipeline.md:39`
- Summary may display Φ1, Γ2, purity and entropy, but display fields are not a density-operator dynamics proof. `education/documentation/011_oeadversary/03_7act_dialectic_bout_execution_pipeline.md:94`

Transitions and executable evidence:
- Prefilter→resources→quarantine→adversarial bout→gauge break→claim hygiene→terminal adjudication is the documented seven-act projection. `education/documentation/011_oeadversary/03_7act_dialectic_bout_execution_pipeline.md:26` [source_declared]
- Provider entry through PFP and exact Rust core is the stated migration architecture; Python retains orchestration and persistence. `education/documentation/011_oeadversary/14_provider_absorption_single_swarm_spoe_and_rust_pipeline.md:1` [source_declared]

Executable owners: `adversary/use_cases/bout_service.py:1088`, `adversary/infrastructure/native_bout.py:170`, `adversary/domain/bout_journal.py:56`, `adversary/tests/test_turn_and_terminal_truth.py:28`.

No separate normal-form contract directory was found; its mathematical states and typed verdicts should not be renamed a proved normal form.

Qualifications:
- Seven-act narrative order, eight-scene profile graph and current native runtime are different representations; a rendering is not a transition certificate.
- The old cross-batch test expects four directories below _ic/adversary/runs, which are absent at audited checkout. Do not infer current replayability from historical documentation.
- The documentation explicitly describes a target single sovereign binary; that target is not established by a curriculum declaration.

## 012_oecogops: Cognitive Operations and CWGate

Mathematical primitives:
- 4E cognition; Big Five/HEXACO personality and valence/arousal/dominance affective vectors are scoped model carriers. `education/documentation/012_oecogops/README.md:37`
- Four exploit tiers: argumentative fallacies, perception traps, social/authority skew, epistemic subversion. `education/documentation/012_oecogops/02_cognitive_warfare_gate_and_defense_registry.md:57`
- Coverage ratio counts covered known indicators divided by catalogued indicators; it is not a probability of immunity. `education/documentation/012_oecogops/02_cognitive_warfare_gate_and_defense_registry.md:63`

Transitions and executable evidence:
- Manifest frontmatter is partitioned from narrative prose; declaration/catalog/canary audit produces findings and dispositions. `education/documentation/012_oecogops/02_cognitive_warfare_gate_and_defense_registry.md:41` [source_declared]
- Canary coverage extraction checks AST use rather than crediting an arbitrary matching string literal. `cognitive_operations/tests/test_cwgate_fail_open_register.py:105` [test_source_located_not_run]

Executable owners: `cognitive_operations/ooutwire/cognitive_warfare_gate.py:540`, `cognitive_operations/ooutwire/cwgate_disposition_report.py:143`, `cognitive_operations/use_cases/run_bout.py:46`.

No separate normal-form contract directory was found; its mathematical states and typed verdicts should not be renamed a proved normal form.

Qualifications:
- No standalone normal_forms directory exists in this track; level/disposition contracts are not a proved normal-form reduction.
- The curriculum explicitly disclaims universal human psychological truth and uncatalogued zero-day immunity.
- Finite affective/personality vectors are not density operators on epistemic fiber Hilbert spaces; that construction needs separate mathematical semantics.

## Cross-track findings

**CURR-LATE-01 (high)** AB register existence is not detector activation or full immunity. Canonical cross-batch test checks substring presence only. `tests/fuzzing/test_cross_batch_d1_d20_regression.py:140`, `_ic/adversary/worktree_20261012_intelligence_digestion.md:29`

**CURR-LATE-02 (high)** AONF name collision: README assigns Agent Operad while YAML identity is Active Obstruction. `education/documentation/008_oewas/normal_forms/README.md:44`, `education/documentation/008_oewas/normal_forms/nf.derivation.aonf.yaml:5`

**CURR-LATE-03 (high)** Same-observer adjoint cannot reveal a fixed linear observation kernel; level06 narrative overstates what its own formulas establish. `education/documentation/007_oelggr/levels/level_06_nonlinear_aggregation_adjoint_probing.md:78`, `education/documentation/007_oelggr/levels/level_06_nonlinear_aggregation_adjoint_probing.md:65`

**CURR-LATE-04 (medium)** LGGR curriculum paths cite the obsolete 012_ series and retired Python crates; live crate package core_epk is in core_local_green_global_red_lggr. `education/documentation/007_oelggr/README.md:100`, `engine/crates_rs/core_local_green_global_red_lggr/Cargo.toml:3`

**CURR-LATE-05 (high)** Existing regex lint is explicit evidence against present-tense zero procedural matching; pure operad replacement remains proposed. `education/documentation/008_oewas/multi_agent_swarm_orchestration_and_operad.md:110`, `research_papers/use_cases/hand_waving_lint.py:60`

**CURR-LATE-06 (medium)** Normal-form documentation metadata overstates compared with declared absent verifiers in individual copied contracts. `education/documentation/009_oeeis/normal_forms/README.md:12`, `education/documentation/009_oeeis/normal_forms/nf.epistemic.enf.yaml:12`

## Evidence limits

The mathematical/evidence excerpts in the JSON were selected from every UTF-8 source/document in these six tracks by explicit lexical evidence markers; they are an inventory and navigation aid, not a proof that every prose assertion is correct. Source files and cited external executable owners carry SHA-256 commitments. Copied frontmatter labels such as verified/production/gated are recorded declarations only. Density-operator epistemic semantics, Wilsonian RG identification with BQNF, all-instance operad totality, and generic DPO confluence are additional proposed proof obligations.
