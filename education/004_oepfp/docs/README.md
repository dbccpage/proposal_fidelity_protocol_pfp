---
documentation_contract: symbol-game-documentation/v1
title: "Proposal Fidelity Protocol (PFP) & Symbol Game Reference Documentation"
kind: documentation-hub
audience:
  - engineers
  - coding-agents
  - researchers
status: active
maturity: canonical-navigation
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - pfp
  - engine/crates_rs/core_symbol_game
  - engine/crates_rs/core_symbol_game_runtime
last_verified: 2026-10-20
verification_scope: every file in docs/ indexed and its paths, names and counts checked against source at c419cc6beb; no commands or tests run for the index
---

# Proposal Fidelity Protocol (PFP) & Symbol Game Reference Manuals

**Status:** Canonical Documentation Hub  
**AuthorityEffect:** `None`  
**Governing Standard:** Examiner Theoretical Minimum & Claim Hygiene Rule  

This directory contains reference manuals, architectural specifications, filtration ledgers, and data type profiles for the **Proposal Fidelity Protocol (PFP)** and the **Symbol Game**. Numbered chapters provide a reading route; a chapter's reference status is separate from evidence that its described runtime has been executed.

## Choose a reading route

**Beginner:** read the [finite-QM workflow walkthrough](23_finite_qm_workflow_walkthrough.md), then work the [certificate lesson](../levels/level_finite_qm_certificate_walkthrough.md). You need signed arithmetic and a shell for preparation; the lesson introduces the required matrix notation. Preparation is offline and does not check a certificate.

**Experienced researcher or implementer:** inspect the [prompt, stages and mode](22_unified_pfp_v4_operad_workflow_and_hacks.md), then the actual [prompt template](../../../../pfp/infrastructure/yaml/prompts/finite_qm/prompt_template.yaml), [workflow](../../../../pfp/infrastructure/yaml/prompts/finite_qm/workflow.yaml) and [mode](../../../../pfp/infrastructure/yaml/prompts/finite_qm/mode.yaml). Read the [digest profiles](01_digest_and_canonical_serialization.md) before implementing a new packet producer.

Keep three counts separate: the finite-QM research workflow names **six stages** (P0 to P5 in `workflow.yaml`), the existing public runtime exposes **eleven numbered stages** (`public_stage_count: 11` in [controller.yaml](../../../../pfp/infrastructure/yaml/stages/controller.yaml); model stages 2, 3, 4, 6 and 11, host stages 1, 5, 7, 8, 9 and 10), and the [levels catalogue](../levels/README.md) contains **101 numbered curriculum specifications** (101 files whose names match `level_<digits>_`, rechecked 2026-10-22; the directory also holds other unnumbered pages). A curriculum row is not evidence of an implemented runtime stage. P1 and P3 request preparation and candidate checking are connected. The six-stage workflow also includes research instructions and has no new automatic full live runner.

## One digit, three lists

A learner meets the digit 3 in three places. Each place is a different list.

A **research stage** is a named step in the finite-QM file `workflow.yaml`. The names run from P0 through P5. **P3** means `P3_REPAIR`: prepare a new request and submit a complete replacement certificate.

A **public runtime stage** is a numbered step in `controller.yaml`. There are eleven. Stage **3** is named `audit`. Its executor is `model`.

A **curriculum specification** is a teaching page. The file `level_03_abstract_simplices.md` is one of 101 numbered pages, from `level_00` through `level_100`.

Work the digit before the general rule. Public stage 3 audits a candidate. Research label P3 asks for a repaired certificate. Page level 03 teaches a lesson.

**Check.** A summary says, "The runtime has six stages, because the workflow lists P0 to P5." That summary fails. The workflow list has six research names. The public controller declares `public_stage_count: 11`.

### Spoken segment

About 45 seconds. One idea: the digit 3 names three lists. No screen is required.

"Public stage three is the audit turn. Research label P three is a repair request. Say P three as the letter P and the word three. The lesson file level zero three is a page about abstract simplices. Here is the check. If someone says the runtime has six stages because the research list has six names, the answer is no. The public runtime has eleven stages."

### Video beats

Worked example: the digit 3. The narration is the spoken segment, split across cards.

| Time | On screen | Narration |
| --- | --- | --- |
| 00:00 | digit 3 | A learner meets the digit 3 in three places. |
| 00:08 | public stage 3: audit | Public stage three is the audit turn. |
| 00:18 | P3: repair request | Research label P three is a repair request. |
| 00:28 | level 03: lesson page | The lesson file level zero three is a page about abstract simplices. |
| 00:38 | six names, eleven stages | If someone says the runtime has six stages because the research list has six names, the answer is no. The public runtime has eleven stages. |

---

## Rechecked figures (2026-10-22)

AuthorityEffect: None. Pin `305b9690f97fc3f5c13e361cfe752a6d5dc7ad8d`. The 2026-10-20 pass below is kept. Three index figures were counted again against committed source. `last_verified` in the header stays 2026-10-20 because the rest of the index was not revalidated line by line.

| Figure | Written on 2026-10-20 | Committed source on 2026-10-22 |
| --- | --- | --- |
| Operad catalog `entries` | 584 | 744, equal to the sum of the twelve `coverage.counts` |
| `runtime_actions!` | 149 actions, 56 adapters | 150 actions, 57 adapters; the added row is `f2` / `classify_gauge_board` |
| Numbered level pages | 101 | 101 files named `level_<digits>_`; 128 markdown files sit in `levels/` |

`public_stage_count` is still 11. The research workflow is still P0 through P5. The mode still allows two attempts and lists the same six technique ids. Packet sealing is still NFC, then the marker `core-canonical-v1`, then SHA-256. `jcs.rs` remains a separate RFC 8785 module. Doc 16's typed-capability link now points at `operads/contracts/typed_capabilities_v1.py`. The work-unit pin for `cochain.rs` matches committed blob `298c3b6de889046e380055e8c57807c0a98027a3d5a38f526957f53113b9acc4`. An uncommitted edit of that file was present in this worktree and does not match the pin.

## Source check of this directory (2026-10-20)

AuthorityEffect: None. Pin `c419cc6beb`. Each file below was read and its named paths, modules, commands and counts were checked against tracked source. Where a page described something no longer in code, it now says so in a dated note at the place it occurs; nothing was deleted. The main results:

| Result | Pages |
| --- | --- |
| Describes a former estate or retired code; now marked historical with current homes | [00](00_master_synthesis_and_cartography.md), [02](02_surviving_ideas_ledger.md), [04](04_symbol_game_architecture.md), [06](06_prompt_packet_stage_synthesis.md), [12](12_pr_review_and_verification_loop.md), [13](13_review_findings_and_pilot_runbook.md), [21](21_prompt_template_contracts_and_single_prompt_standard.md) |
| Object model mostly proposed (no matching classes) | [05](05_pfp_and_adversary_swarm_system_design.md), [07](07_sentinel_ai_integration.md) |
| Current and corrected in place (paths, counts, limits) | [01](01_digest_and_canonical_serialization.md), [03](03_context_extension_calculus_and_foundations.md), [08](08_native_rust_host_architecture.md), [09](09_runtime_actions_and_governor.md), [10](10_functional_metric_ownership.md), [11](11_mss_n_machine_wire_registry.md), [14](14_release_checklist.md), [15](15_comparative_tooling_and_external_repositories.md), both 16s, [17](17_runtime_ownership_and_replay.md), [20](20_acsets_dpo_and_optional_backends.md), [22](22_unified_pfp_v4_operad_workflow_and_hacks.md), [23](23_finite_qm_workflow_walkthrough.md) |
| Cites receipts and scripts that are not in the repository | [18](18_original_challenge_play.md) and [19](19_bounded_mechanism_sessions.md) (the 2026-10-16/17 `P*` campaigns); treat their ratios as unverified |
| Archived external text, scope note added | [deep research prompt](pfp_pciv_eis_llms_deep_research_prompt.md) |

Two files share the number 16. They are separate documents with different scopes and are listed as 16a and 16b in section 4; their filenames are unchanged.

## Current implementation and discoveries (2026-10-12)

Start with [current types, capabilities and lessons](16_current_types_and_learnings.md)
and the [practical play guide](../_how_to_play/13_practical_pfp_and_discovery.md).
These describe the consolidated application, bounded live/replay discoveries and
targeted failure learning. Older runbooks retain historical source references;
use the current guide for execution. No fixed pilot count is required.

[Adversary challenge play](18_original_challenge_play.md) composes the shared
workflow, PFP turns and original challenge judges for IDE/OpenRouter execution.
It records actual bounded outcomes and the scientific obligations still open.

[ACSets and DPO experiments](20_acsets_dpo_and_optional_backends.md) add bounded
prompt/cochain controls, registered polygraph steps and one optional Julia/DSPy
demo each. They do not add default runtime dependencies or model-efficacy claims.

## 1. Core Protocols, Semiotics & Foundations

| Document | Semantic Role | Authority Status | Key Invariants |
|---|---|---|---|
| [`00_master_synthesis_and_cartography.md`](00_master_synthesis_and_cartography.md) | Estate Cartography | Canonical Monograph | 4-estate consolidation, Examiner theoretical minimum, and observer-quarantine rules. |
| [`01_digest_and_canonical_serialization.md`](01_digest_and_canonical_serialization.md) | Data Type Specification | Source-inspected Reference | PacketCodec's NFC/tagged `core-canonical-v1` bare SHA-256, separately framed `domain_digest`, and distinct JCS helpers. |
| [`02_surviving_ideas_ledger.md`](02_surviving_ideas_ledger.md) | Filtration Ledger | Canonical Ledger | Fail-closed filtration of candidate research ideas (`ADMIT`, `HOLD`, `USEFUL-BUT-UNSAFE`, `REFUSED`). |
| [`03_context_extension_calculus_and_foundations.md`](03_context_extension_calculus_and_foundations.md) | Foundations & Calculus Monograph | Canonical Spec | GDP-0 minimal difference, PFP within-context integrity ($R_1$), CEC 6-tuple $(C, C', \iota, \pi, \Delta_C, \mathcal{W})$ conservative extension ($R_2$), and three-tier protocol decomposition. |

---

## 2. System Architecture, Swarm Design & Semiotics

| Document | Semantic Role | Authority Status | Key Invariants |
|---|---|---|---|
| [`04_symbol_game_architecture.md`](04_symbol_game_architecture.md) | System Architecture & Repair | Authoritative Master | Finite packet boundary, deterministic mechanical verifiers, fail-closed terminalization, and the CEC-PFP-000 paper repair protocol. |
| [`05_pfp_and_adversary_swarm_system_design.md`](05_pfp_and_adversary_swarm_system_design.md) | Swarm System Design | Authoritative Master | Adversary Base Swarm runtime, 7-Act dialectic bouts, persona panel gates, and conclave invariants. |
| [`06_prompt_packet_stage_synthesis.md`](06_prompt_packet_stage_synthesis.md) | Architectural Semiotics | Authoritative Master | 4-axis separation of Prompt ($A_{\text{stimulus}}$), Packet ($P \in \mathcal{P}$), Stage ($S_n$), and Mode ($M_k$). |
| [`07_sentinel_ai_integration.md`](07_sentinel_ai_integration.md) | Product Integration | Authoritative Spec | Component mapping between `symbol_game` and `sentinel_ai`, API endpoints, and confidence decoders. |
| [`21_prompt_template_contracts_and_single_prompt_standard.md`](21_prompt_template_contracts_and_single_prompt_standard.md) | Single Prompt Standard & Containment | Specification & Monograph (implementation retired 2026-10-10) | $P \mapsto P^* \to \{p_i\}$ decomposition tree, containment cardinality law $\text{cardinality}(n) = 1 + \sum \text{cardinality}(c)$, generation invariance, and SPK-001 policy manifest. |

---

## 3. Host, Wire & Runtime Interfaces

| Document | Semantic Role | Authority Status | Key Invariants |
|---|---|---|---|
| [`08_native_rust_host_architecture.md`](08_native_rust_host_architecture.md) | Native Rust Reference | Supported Laboratory | Request/outcome envelopes, memory fences, and `evaluate_candidate` contracts in `core_symbol_game`. |
| [`09_runtime_actions_and_governor.md`](09_runtime_actions_and_governor.md) | Runtime Action Reference | Supported Laboratory | Engine actions, dispatch boundaries, and execution lifecycle; the `invoke` registry at pin `305b9690` declares 150 actions in 57 adapters, including `f2` / `classify_gauge_board` (full table in the page). |
| [`10_functional_metric_ownership.md`](10_functional_metric_ownership.md) | Metric Ownership | Authoritative Spec | Strict Rust ownership of $\Phi_1, \Gamma_2, \Xi$ exact rational metrics; Python facade delegation boundaries. |
| [`11_mss_n_machine_wire_registry.md`](11_mss_n_machine_wire_registry.md) | Machine Wire Registry | Specification Register (partly implemented) | Global opcodes vs. local child discriminators in the 38-glyph wire alphabet ($\Gamma_{38}$) for Levels 0–21; 18 of 42 constructors have semantic checks in `domain/tower/parser.py`. |

---

## 4. Verification Loops, Review & Tooling Discipline

| Document | Semantic Role | Authority Status | Key Invariants |
|---|---|---|---|
| [`12_pr_review_and_verification_loop.md`](12_pr_review_and_verification_loop.md) | PR Verification Loop & Prompts | Verification Spec (proposed loop) | 5-stage adversary specification, AB-01–07 (labels, not implemented antibodies), targeted test replay, `SwarmEvidenceEnvelopeV1` (written by `swarm_developer.py`), and Claude Code review prompts. |
| [`13_review_findings_and_pilot_runbook.md`](13_review_findings_and_pilot_runbook.md) | Review Findings & Runbook | Operational Runbook | Exact rational duality audit findings; the historical 50-demo command and the current PFP CLI subcommands over the 74-seed catalog. |
| [`14_release_checklist.md`](14_release_checklist.md) | Release Discipline | Operational Contract | Step-by-step preflight checklist for repository releases, secret scrubbing, and receipt-claim bindings. |
| [`15_comparative_tooling_and_external_repositories.md`](15_comparative_tooling_and_external_repositories.md) | Comparative Tooling Evaluation | Reference (unpinned) | Four-axis mapping and evaluation of 18 named external projects (Mathlib4, LeanDojo-v2, LeanCopilot, CivAgent, CatDock, CEO, AgentCiv, sharpen, AutoPrompt, gpt-prompt-engineer, TheBigPromptLibrary, DAIR guide, vLLM, SGLang, LLMLingua, RepE, llm-attacks, Prompt Guard); no commits pinned. |
| 16a [`16_current_types_and_learnings.md`](16_current_types_and_learnings.md) | Current PFP Interfaces & Learning | Source-grounded Reference | Typed prompts/stages/witnesses, conditional mode availability (15 of 20 modes have executors), six guidance kinds, a worked DEMO_07 check and applied bounded-run repairs. |
| 16b [`16_numbered_prompt_roles_and_po035_play.md`](16_numbered_prompt_roles_and_po035_play.md) | Empirical Prompt Contracts & Play | Experimental Reference | Numbered prompt roles (current registry v1.0.4), public workpads, calculation bindings and bounded PO035 failures. |

---

## 5. Runtime, Play, Experiments & Finite-QM Workflow

| Document | Semantic Role | Authority Status | Key Invariants |
|---|---|---|---|
| [`17_runtime_ownership_and_replay.md`](17_runtime_ownership_and_replay.md) | Runtime Ownership & Replay | Source-grounded Runbook | Current owners and commands for demos, matrices, numbered stages, PO035 loops, Paper 008 benchmark and the finite gauge workbench; historical replay profiles. |
| [`18_original_challenge_play.md`](18_original_challenge_play.md) | Original Challenge Play | Runbook with bounded observations | IDE and OpenRouter challenge play through PFP and the original judges; recorded paid attempts (87 replies, $0.03540475 known); untracked `P*` receipts flagged. |
| [`19_bounded_mechanism_sessions.md`](19_bounded_mechanism_sessions.md) | Mechanism Sessions | Runbook; later sections unverified | C006 ASSERT/CUT/LIFT_REQUEST/VERIFY sessions and paid runs; the 2026-10-16/17 C001-C020 `P*` campaign sections cite absent scripts, receipts and functions. |
| [`20_acsets_dpo_and_optional_backends.md`](20_acsets_dpo_and_optional_backends.md) | ACSets & DPO Experiments | Offline Controls | Two 25-case rewriting pilots and one Julia and one DSPy optional demo (14 controls). |
| [`22_unified_pfp_v4_operad_workflow_and_hacks.md`](22_unified_pfp_v4_operad_workflow_and_hacks.md) | Finite-QM Prompt, Stages & Mode | Source-grounded Reference | Six research stages P0–P5, one mode with six techniques and two attempts, 744-entry operad catalog (rechecked 2026-10-22). |
| [`23_finite_qm_workflow_walkthrough.md`](23_finite_qm_workflow_walkthrough.md) | Finite-QM Walkthrough | Instructional | Prepare, bind, check and repair one C4 certificate turn offline. |

---

## 6. Supporting Notes

| Document | Semantic Role | Authority Status | Key Invariants |
|---|---|---|---|
| [`thymus_screening_note.md`](thymus_screening_note.md) | Lean proof note | Proposal (archived Lean receipt) | Lemma C and OEEIS self-panel soundness in core Lean (`lean4/ThymusScreening.lean`, seven `#print axioms` targets). |
| [`pfp_pciv_eis_llms_deep_research_prompt.md`](pfp_pciv_eis_llms_deep_research_prompt.md) | Research prompt archive | Archived external text | Pass-one prompt, five verbatim external model outputs, and a maintained pass-one review with a second-pass prompt. |

---

## 7. Directory Governance Rules

1. **Authority Ceiling:** `AuthorityEffect: None.` Documentation, compiled checker results, and Lean proofs have their stated scopes; none alone grants external operational authority.
2. **Zero Forbidden Hype Verbs:** All documents adhere to `RULE[user_global]` and the forbidden-word list in the PR scope rule (`rl_pr_scope_and_branch_diff_audit.md`); evidence is framed with scoped claims (`supports`, `demonstrates in this toy setting`). Verbatim archived external text, such as the model outputs in the deep research prompt, is quoted, not adopted.
3. **No Redundant Facades:** Documents should correspond to an active, maintained subsystem. Where a page describes a retired subsystem, it is labelled historical in place rather than deleted. Merged documents consolidate redundant stubs and keep unified lineage under numerical prefixes.

- [Runtime ownership and historical replay](17_runtime_ownership_and_replay.md)
- [Adversary original challenge play](18_original_challenge_play.md)
- [Bounded mechanism sessions](19_bounded_mechanism_sessions.md)
- [ACSets and DPO experiments](20_acsets_dpo_and_optional_backends.md)
- [Prompt template contracts & single prompt standard](21_prompt_template_contracts_and_single_prompt_standard.md)
- [Finite-QM prompt, stages and execution mode](22_unified_pfp_v4_operad_workflow_and_hacks.md)
- [Finite-QM workflow walkthrough: prepare, derive, check and repair](23_finite_qm_workflow_walkthrough.md)

