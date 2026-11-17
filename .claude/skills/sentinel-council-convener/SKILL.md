---
name: sentinel-council-convener
description: "Manually convene and deliberate Sentinel Councils over Adversary Swarm execution diffs and periodic convocations."
operad_source_colours: ["Code", "Contract"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [governance, deliberation, sentinel, councils]
---

# Sentinel Council Convener (`sentinel-council-convener`)

**AuthorityEffect:** None (Deliberation, Governance Review, and Formal Advisory Minute Synthesis).

## Purpose

This skill provides the single manual operational gateway to summon, deliberate, and record formal proceedings of the 79 Sentinel Councils in response to Adversary Swarm changes, prompt mutations, or scheduled weekly convocations.

## Governing Context

- **Topology & Canon:** [`governance/sentinel_councils/documentation/councils.yaml`](../../../governance/sentinel_councils/documentation/councils.yaml)
- **Member Cognitive Profiles:** [`cognitive_operations/documentation/_sap/ana_000_forms_council_members/`](../../../cognitive_operations/documentation/_sap/ana_000_forms_council_members/)
- **Integration Plan:** [`product_planning_office/plans/epics/plan_sentinel_councils_engine_integration.md`](../../../product_planning_office/plans/epics/plan_sentinel_councils_engine_integration.md)

## Convocable Councils upon Adversary Swarm Changes

Every Adversary Swarm change notifies:
1. **Curious Council (`CC`, L1):** Apex intake, first distinction, systemic anomaly assessment.
2. **Logos Council (`LOGOS`, L2):** Structural code integrity, mathematical contracts, and formal proofs.
3. **Nous Council (`NOUS`, L2):** Epistemic ethics, human alignment, and phaneron phenomenological fidelity.
4. **Techne Council (`TECHNITAI`, L3):** Concrete tool, workflow, and engineering pipeline audit.
5. **Targeted Subordinate Councils:** Dependent on touched files (e.g. `Kanon`, `Apodeixis`, `Metron`, `Phaneron`).

## Blackrod Sovereign Invariant

> **Notice:** The Blackrod is the only free man here. He is not managed by any council, answers solely to The Architect (`ooutwire`), holds plenary attendance rights across all assemblies, and retains unconstrained abort/veto keys.

## Convocation Protocol

When executing this skill:
1. **Target Selection:** Specify which council to convene (e.g., `curious`, `logos`, `nous`, `techne`, or a specific sub-council).
2. **Input Packet:** Provide the Adversary execution diff, Git commit SHA, or weekly agenda.
3. **Persona Ingestion:** Load the four seated curator forms (`first_curator`, `second_curator`, `procurator`, `secretary`) from `_sap/ana_000_forms_council_members/`.
4. **4-Stage Deliberation:**
   - *Intake & First Distinction (First Curator):* Grounds the matter in core evidence.
   - *Adversarial Cross-Examination (Second Curator):* Probes failure modes and boundary edge cases.
   - *Procedural Quorum & Synthesis (Procurator):* Synthesizes consensus or registers dissenting votes.
   - *Minute Crystallization (Secretary):* Emits a typed machine receipt (`status: PASS | ADVISORY | REFUSAL`).
5. **Blackrod Attendance Check:** Confirm whether Blackrod issues an orthogonal objection or aborts the motion.
