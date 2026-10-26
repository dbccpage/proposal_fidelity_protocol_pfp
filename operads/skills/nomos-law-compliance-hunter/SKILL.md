---
name: nomos-law-compliance-hunter
description: "Scan a directory or file for contract usage; record uncontracted interfaces and violations; propose updates."

operad_source_colours: ["Contract", "Code"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
---

# nomos-law-compliance-hunter

## authority_effect_ceiling: None

## 1. Compliance Audit Workflow

When invoked as `/nomos-law-compliance-hunter <target_path | crate | package | all>`:

1. **Contract Binding Verification:**
   Inspect source code and markdown documents in the target folder to verify that structures implement or cite contract URNs (e.g. `urn:omega:math:*`, `urn:omega:core:*`).

2. **Violation Recording:**
   Detect uncontracted state boundaries, missing `ContractDescriptors`, unvalidated payload transports, or contract misuse.

3. **Governance Recommendation Engine:**
   Propose new contract templates or updates to existing `{NN}_core_{slug}` contract categories when new uncontracted domain abstractions are uncovered.

---

## 2. Receipt Schema

Emit a `nomos_compliance_hunter_receipt` summary table:

| Field | Status / Value |
| --- | --- |
| Target Path | `<target>` |
| Contract Coverage | `<percentage>%` |
| Direct URN Bindings | `<count>` |
| Contract Violations | `<count>` |
| Recommended Contracts | `<new_contracts_proposed>` |

### Non-Invariant Content & LLM Slop Screening (`RULE_NONINVARIANT_CONTENT_PROHIBITION_001`)

During audit sweeps across preprints, papers, council documents, and skill files:

1. **Screen for Non-Invariant Content & LLM Slop:**
   - Scan for misspellings, adverb soup, generic fluff words ('crucial', 'essential', 'delve', 'game-changing', 'testament'), and ungrounded hype verbs ('proves', 'guarantees', 'flawless', 'weaponized') per `[user_global]` claim discipline.
   - Detect any inconsistencies or non-invariant patterns that warrant new rule candidates for `rules.yaml`.
2. **Mandatory Blackrod Investigation Logging (`RULE_DEFECT_INVESTIGATION_LOGGING_001`):**
   - Whenever non-invariant content, misspellings, LLM slop, or contract/symmetry inconsistencies are discovered, automatically log a formal investigation report under:
     `omega_engine/anomalon_councils/councils/blackrod/investigations/investigation_{YYYYMMDD}_{skill_name}_{defect_id}.md`
   - Detail the defect context, affected file paths, root cause analysis, and proposed `rules.yaml` additions or workflow remediations.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
