---
name: techne-sprint-svp-briefing
description: "Escalate unmanageable sprint issues, firewall breaches and high risks (above 0.7) to the SVP of Engineering."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# Sprint Svp Briefing

## status: canonical-candidate

## Prime Directive

```text
Intake VP and Blackrod escalations.
Audit risks exceeding 0.7 severity.
Record critical blockers in the SVP Council Escalation Ledger.
Prepare executive briefing for the Logos Techne Council (L3_logos_techne).
Enact human responsibility and organizational truth without LLM self-certification.

```

---

## Escalation Flow

```text
 ┌───────────────────────┐       ┌──────────────────────┐
 │ /techne-sprint-vp-briefing   │  ──▶  │ /techne-sprint-svp-briefing │  ──▶  Logos Techne Council
 │ (techne-vp & Blackrod)│ >0.7  │ (techne-svp Docket)  │       (L3_logos_techne)
 └───────────────────────┘ Risk  └──────────────────────┘

```

---

## Protocol Execution Steps

1. **Intake & Structural Pre-Gate (HARD BLOCK):**
   - Assert that `1_sprint_impl_documents/` exists and is fully populated (`completion.md`, `devops_review.md`, `retrospective.md`, `vp_briefing.md`).
   - Hard-reject any sprint that bypassed implementation document verification.
   - Inspect `engine/product_planning_office/plans/sprints/{SPRINT_ID}/vp_escalation_to_svp.yaml` (if present).
   - Inspect `engine/product_planning_office/plans/sprints/{SPRINT_ID}/blackrod_action_report.md`.
   - Read `vp_engineering_report.md` / `sprint_{NNN}_vp_briefing.md`.

2. **Severity Audit ($[0, 1]$ scale):**
   - Confirm all escalated items meet or exceed $0.7$ risk severity.
   - Flag any attempts to hide, cover up, or smooth over technical debt or broken quality gates.

3. **Ledger Update:**
   - Append escalated items to `engine/product_planning_office/svp_council_escalation_ledger.yaml`.

4. **Council Briefing Generation:**
   - Create `engine/product_planning_office/plans/sprints/{SPRINT_ID}/svp_logos_techne_council_briefing.md`.
   - Formulate concrete executive motions for procurators of **Logos Techne Council** (`L3_logos_techne`).

---

## Output Artifacts

```text
engine/product_planning_office/plans/sprints/{SPRINT_ID}/svp_logos_techne_council_briefing.md
engine/product_planning_office/svp_council_escalation_ledger.yaml

```

AuthorityEffect: None.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
