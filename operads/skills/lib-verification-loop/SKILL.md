---
name: lib-verification-loop
description: "Verification loop for library documents, ensuring factual accuracy and test consistency."

operad_source_colours: ["Ledger", "Paper"]
operad_target_colour: "Ledger"
operad_arity: 2
operad_residual: "unknown"
---

# lib-verification-loop

## Constraints

## Example Session

**Family:** testing / code-quality (see [family_registry.md](../_shared/family_registry.md))

## Related Skills

## Integration with Hooks

## Continuous Mode

## Output Format

**Report Format for Technical Content:**
**Skip Conditions:**
**Report Format:**
**Counterfeit Descent Indicators:**
**Verification Steps:**
**MANDATORY for authority-bearing outputs:** If the verification target includes claims of certified/verified/authority status, check the obstruction norm.

### Phase 8: Obstruction Norm Gate (Authority Claims Only)

**Skip Conditions (domain expert verification not required):**
**Failure Protocol:**
**Verdict Interpretation:**
**Expert Routing:**
**If technical content detected:**
**MANDATORY for technical content:** If content changes include physics, mathematics, computer science, chemistry, or linguistics content (lessons, documentation, derivations, proofs), verify domain accuracy.

### Phase 7: Domain Expert Verification (Physics/Math/Technical Content Only)

### Phase 6: Diff Review

### Phase 5: Security Scan

### Phase 4: Test Suite

### Phase 3: Lint Check

### Phase 2: Type Check

### Phase 1: Build Verification

### Phase 0: Import Chain Smoke Test (Python pipelines)

## Verification Phases

## When to Activate

## description: Comprehensive verification system for Omega Engine sessions. Use after completing features, before PRs, or when ensuring quality gates pass

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
