---
name: lib-skill-admission-hygiene
description: "Use when adding or reviewing skills. Scans packaging for version, authority ceiling, secrets and curl-pipe-sh."

operad_source_colours: ["Ledger", "Paper"]
operad_target_colour: "Ledger"
operad_arity: 2
operad_residual: "unknown"
---

# lib-skill-admission-hygiene

## References

## Constraints

## Related skills

### Blocking checks (v1)

## Procedure

## When to activate

**AuthorityEffect: None.**

## note: pattern only (skill packaging metadata / selective install / scan); reimplemented

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
