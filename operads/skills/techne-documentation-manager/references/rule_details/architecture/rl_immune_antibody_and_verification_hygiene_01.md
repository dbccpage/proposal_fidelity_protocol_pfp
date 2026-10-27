# Detailed definition: Immune Antibody & Verification Hygiene (1)

**AuthorityEffect:** None.

Parent: [Immune Antibody & Verification Hygiene](../../../../../rules/architecture/rl_immune_antibody_and_verification_hygiene.md). Load for the matching predicate, not every task.

# Rule: Immune Antibody Hygiene & Governance Verification

**AuthorityEffect:** None.

This rule codifies learned failure detector and antibody carrier honesty, catalog atomicity, semantic field filter discipline, antibody activation by admission only, and autonomous governance skill self-verification script standards.

---

## Learned Failure Detector & Antibody Hygiene Invariant (`RULE_IMMUNE_ANTIBODY_HYGIENE_001`)

> **Immune & Pharmacy Carrier Honesty:**
>
> 1. **Disentangle Rule Identity from Observation Identity:** An antibody or learned failure detector identity (`antibody_id`) must bind strictly to the invariant failure class, target pattern, and normalized detector/fixture content (`evidence_sha256`). Ephemeral execution parameters (`run_id`, `task_id`, timestamps, process PIDs) belong strictly to observation ledger entries (`AntibodyObservationV1`), never hashed into new candidate rule IDs.
> 2. **Semantic Field Filter Discipline:** Ingestion, backfill, and retirement filters must evaluate typed semantic fields (`failure_class`, `target_pattern`), never asserting against derivative slug strings or assumed ID prefixes.
> 3. **Executable Witness vs. Filename Mining:** Automated mining from source trees or teamwork directories must inspect file ASTs or execution receipts to verify executable test functions or structured verdicts. A candidate rule must never be minted purely from filename substrings.
> 4. **Atomicity of Catalog and File Projections:** Ingestion adapters (such as `JsonPharmacyAdapter`) must maintain strict byte-level parity between aggregate catalogs (`pharmacy_catalog.json`) and individual item files (`ab_*.json`), synchronizing sighting counts (`times_seen`) and payload updates atomically.

## Antibody Activation Is an Admission Act (`RULE_IMMUNE_NO_SELF_ACTIVATION_001`)

> **No Self-Activation:**
>
> 1. **Sightings Only Count:** Stores that count failure sightings (Rust `core_adversary::file_adapters::FileFailureHistory`; Python `FileAntibodyAdapter` in the city and Prompt Civilization) record a new or re-seen pattern as `PENDING`. A sighting count never activates an antibody.
> 2. **Admission Is Kept:** A record is `ACTIVE` only because an admission act wrote it, and it keeps that status when the pattern is seen again.
> 3. **Pharmacy Candidates:** Farming into the OEEIS pharmacy writes `CANDIDATE` only and never rewrites an admitted or rejected entry. Guidance is injected only from entries whose recorded status is `admitted` (`admitted_antibodies`).

## Governance Skill Self-Verification Script Invariant (`RULE_GOVERNANCE_SKILL_SELF_CHECK_001`)

> **Autonomous Skill Self-Verification Standard:**
>
> 1. **Consolidated Governance Skill (`governance-wdp`):**
>    - **CODA checks:** Nine-Layer CODA Stack, Layer 5 = Q (The Continuum), dual-witness certification, and GTLA terminal factorization.
>    - **DDC checks:** Discrete Deformation Calculus 8-letter operational trace alphabet $\mathcal{A}_{\mathrm{DDC}} = \{E, R, C, I, \Lambda, D, M, T\}$, CREDIT loop mnemonic (C·R·E·D·I·T), candidate runtime laws, and minimal finite demos.
>    - **Prime checks:** Foundational Prime Triad: Prime -1 Candidate proposal (ALGOS paper §1.1 `OE001-01`, no crate owner), Prime 000 Declaration order (admission, then twelve-step fill: `oeprmalg0_admission.rs`, `oeprmalg0.rs`), Prime 001 Adapter soundness (`oeprmalg1.rs`), Prime 002 Continuation control (`oeprmalg2.rs`).
> 2. **Mandatory Self-Check Script:**
>    - Every skill under `governance-*` must package a lightweight verification script in `scripts/check_<topic>.py`.
>    - The script must run in $< 1\text{s}$, depend only on the Python standard library, assert internal consistency, and return exit code 0 on PASS or nonzero on FAIL.
>    - Pre-commit gates and AutoP pipeline invocations must execute these check scripts to attest skill package health.

## Negative Governance Boundary Invariant (`RULE_NEGATIVE_GOVERNANCE_BOUNDARIES_001`)

> **Procedural Anti-Ops vs. Empirical Antibodies Boundary:**
>
> 1. **OEWAS Ownership for Anti-Ops & Contract Totality:** Procedural syntax, import boundary, and semantic restriction checkers (Anti-Ops / Anti-Skills) must live solely in `operads` (`domain/anti_skills/`). The package root `operads.domain.anti_skills` is the authoritative single export surface for both definitions (`ACTIVE_ANTI_SKILLS`, `AntiSkillDefinition`) and the full v2 typed evaluation contract suite (`AntiSkillSpecV2`, `AntiSkillEvaluationReceiptV2`, `AntiSkillFixtureBankV1`, `VerifiedAntiSkillRegistryV1`, `canonical_id`, `canonical_json_bytes`). Other crates must import all anti-skill types through OEWAS re-exports.
> 2. **OEEIS Ownership for Antibodies:** Empirical failure detectors (Antibodies) and pharmacy catalogs must live solely in `eis`.
> 3. **Filesystem Custody under `.agents/`:** The filesystem definitions for anti-skills and antibodies reside canonically in `.agents/antiskills/` and `.agents/antibodies/`.
> 4. **Two-Signal Danger Gate Requirement:** In runtime evaluation, an antibody is inert unless its recorded status is `admitted`. Even when admitted, it fires ONLY when both Signal 1 (Epitope detected in candidate payload) AND Signal 2 (Independent host danger signal witnessed by an external observer/test runner) are simultaneously present.


## Addressable Prompt Hierarchy & Non-Prose Gate Binding (`RULE_PROMPT_HIERARCHY_GATE_BINDING_001`)

> **Addressable Prompt Node Gating:**
>
> 1. **Canonical Prompt URI Format:** All workflow prompts must be addressed via the canonical scheme:
>    `prompt://<domain>/<subdomain>/<task>/<stage>/<prompt_id>[/<subprompt_id>]`
> 2. **Companion Sidecar Binding:** Prompts must bind negative governance fences using declarative YAML sidecars (`<prompt_id>.binding.yaml`) defining `oewas_anti_ops` and `oeeis_antibodies`.
> 3. **Executable Gate Clearance Receipt:** Autonomous pipelines must evaluate candidate payloads against the bound node gates using sovereign code (`evaluate_prompt_gates`), issuing a typed `PromptGateReceipt` with `status: PASS` or `status: REFUSED`. Gate clearance must never rely on LLM self-certification or prose reciting.
