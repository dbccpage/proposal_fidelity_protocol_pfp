---
name: techne-documentation-manager
description: "Keep sprint documents in the canonical layout and coordinate paper hygiene, claim ledgers and change logs."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# techne-documentation-manager

**AuthorityEffect:** `None`. Enforces claim discipline (`[user_global]`), canonical sprint documentation layout, paper hygiene workflows, and claim ledgers.

## invariance_level: Tier 10

## Core Responsibilities

1. **Sprint Document Governance & Complete Hierarchy Audit (Mandatory Sprint Gate):**
   - Executed during `/sprint-planning-review` and `/sprint-retrospective` stages (or standalone via `/techne-documentation-manager`).
   - Audit `coda_project_planning/sprints/{NNN}/` directory to verify that **all required sprint subdirectories & plan documents exist**:
     Mandatory Subdirectories:
       1. `0_planning_documents/`
       2. `1_sprint_impl_documents/`
     Mandatory Files:
       3. All 8 canonical sprint docs (`sprint_NNN_plan.md`, `pre_sprint_checklist.md`, `kickoff.md`, `review.md`, `quality_gates.md`, `completion.md`, `retrospective.md`, `README.md`).
       4. At least one parent **Epic Plan document** (`epic_{slug}_plan.md` in `plans/epics/`).
       5. At least one parent **Saga Plan document** (`saga_{slug}_plan.md` in `plans/sagas/`).
   - **Superfluous Document Quarantine:** Move any non-canonical document in `coda_project_planning/sprints/{NNN}/` into `0_planning_documents/` or `1_sprint_impl_documents/`.

2. **Documentation Manager Sign-Off Stamp (`DOC_MGR_REVIEWED`) & Handoff to Blackrod:**
   - Upon confirming that all mandatory subdirectories, 8 canonical sprint docs, epic plan doc, and saga plan doc exist for a sprint, `/techne-documentation-manager` signs off on all sprint docs.
   - Marks/stamps the plan document header with **`DOC_MGR_REVIEWED: <YYYY-MM-DD>`** (e.g. `DOC_MGR_REVIEWED: 2026-08-01`).
   - Immediately notifies **`blackrod`** to execute Official Check 2 (independent audit of sprint files, work delivered, deferred work, missing work/tests, and plan/saga alignment).

3. **Paper Hygiene Pipeline:** Coordinate `paper-improver`, `paper-adversary`, `paper-proof-signoff`, and `rip-papers` across published preprints.
4. **Claim Ledger Hygiene:** Ensure every paper `{stem}.md` has a corresponding `{stem}_claim_ledger.md` and `{stem}_change_log.md`, maintaining 100% claim-ID bijection.
5. **Pedagogical Content Management:** Coordinate `lib-pedagogy-improvement` and `lib-education-engine` for curriculum and handout quality.
6. **Epic/Saga/Sprint Hierarchy & Forgery Nemesis Escalation:**
   - Audit `omega_engine/omega_engine_product_planning_office/plans/epics/plans_signoff.md` on every governance pass and during `rip-sprints` execution.
   - Enforce that `SIGNED_COMPLETED_AUTHORITY` is strictly `BLACKROD, OOUTWIRE` for `COMPLETED` status.
   - **Forgery Detection & Blackrod Nemesis Escalation Cascade:** If `/techne-documentation-manager` discovers a forged sign-off or unauthorized signature:
     - Immediately activate the **Blackrod Nemesis Workflow** via `/thanatos-nemesis` (`omega_engine_operads/skills/thanatos-nemesis/SKILL.md`).
     - Notify **`techne-vp`** during `/sprint-vp-briefing`.
     - Notify **`techne-svp`** via report in `/sprint-svp-briefing`.
     - Notify **`blackrod`** and log an investigation document in `omega_engine/anomalon_councils/councils/blackrod/investigations/investigation_{YYYYMMDD}_{breach_id}.md`.
7. **Lower Snake-Case Naming Law Enforcement (`RULE_NAMING_CONVENTION_001`):**
   - Enforce that all created or modified files and directories use lowercase letters and `snake_case` only (except `README.md` and third-party files).
8. **Markdown De-Linting & Linter Defect Investigation Protocol (`RULE_MARKDOWN_DELINTING_001`):**
   - Ensure every `.md` file created or modified is thoroughly de-linted with zero errors and zero warnings.
   - Whenever `/techne-documentation-manager` or `/techne-docs-lint-hunter-killer` encounters any markdown linter error or warning during audit, immediately log a formal investigation report under `omega_engine/anomalon_councils/councils/blackrod/investigations/investigation_{YYYYMMDD}_lint_defect_{id}.md` so Blackrod can remediate the workflow.
9. **Mojibake & Encoding Corruption Screening (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`):**
   - Continuously screen all SKILL.md files, frontmatter descriptions, and estate documentation for broken CP437/Windows-1252 Mojibake corruption (e.g. `Φ`, `—`, `λ`, `Φ₁`, `Γ₂`, `→`, `·`).
   - Automatically repair and convert Mojibake sequences to clean standard UTF-8 characters ($\Phi$, $\lambda$, —, →, ·) or ASCII equivalents.

---

## Related Skills

- `rip-sprints` / `sprint-*` — Sprint lifecycle workflow.
- `thanatos-nemesis` — Blackrod Nemesis Workflow activation for signature forgery containment.
- `techne-vp` — Vice President of Engineering for delivery audit notifications.
- `rip-papers` / `paper-*` — Paper hygiene stages.
- `lib-master-librarian` — O(1) literature filter-select-read indexer.

## Reference dispatch

| Task branch | Read |
| --- | --- |
| Review, apply or shorten a registered rule | [Rule composition index](references/rules_index.md); then only the matching predicate definition |

The compact rules are routes to preserved definitions, not new checks or authority.
