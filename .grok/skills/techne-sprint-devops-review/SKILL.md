---
name: techne-sprint-devops-review
description: "Pre-retro sprint CI gate. local_ci.py, clippy, contract gates, registry integrity, claim IDs, Lean sorry scan."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# Sprint Devops Review

## invariance_level: Tier 11

## Audit Checklist

1. **Local CI (`python scripts/local_ci.py`):**
   - `rustfmt --check` (incremental or full)
   - `v1_contract_gate.ps1` (Rust contract tests pass)
   - `packet-registry integrity` (14 mappings resolve clean)
   - `claim_id_bijection.py` (001_coda claim ID bijection passes 100%)
2. **Lean 4 Sorry-Scan:**
   - Run `lean_gate_audit` sorry-scan across `engine/lean4/`.
3. **Crate & Build Integrity:**
   - Verify touched crates build clean with zero warnings under `clippy -D warnings`.

---

## Verdict

```text
SPRINT_DEVOPS_REVIEW: PASS | BLOCKED
Local CI: PASS / FAIL
Contracts Gate: PASS / FAIL
Lean Sorry-Scan: PASS / FAIL
Clippy: PASS / FAIL
Next step: Proceed to /techne-sprint-retrospective

```

### Mandatory Defect Investigation Logging (`RULE_DEFECT_INVESTIGATION_LOGGING_001`)

Whenever this skill encounters any error, build failure, veto, linter defect, anti-pattern breach, proof/contract obstruction, or process violation:

1. Automatically create a formal investigation report under:
   `_intelligence/blackrod/investigations/investigation_{YYYYMMDD}_{skill_name}_{defect_id}.md`
2. Include full error trace/context, root cause analysis, affected files, and recommended workflow remediation plan for Blackrod review.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
