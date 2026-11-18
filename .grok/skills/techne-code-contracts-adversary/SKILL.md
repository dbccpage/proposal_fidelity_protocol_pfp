---
name: techne-code-contracts-adversary
description: "Adversarial verification of code contracts, generating hostile inputs to uncover boundary vulnerabilities."

operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
---

# techne-code-contracts-adversary

**Family:** techne-code (see [family_registry.md](../_shared/family_registry.md))

## Constraints

## Pipeline position

## Evidence independence

## Verdict (the gate)

### 7. Scope conformance — `SCOPE_VIOLATION` ext

### 6. Authority hygiene — `AUTHORITY_MINTED` / `SELF_CERTIFICATION` ext

### 5. Census integrity — `CENSUS_DODGED` ext

### 4. Mirror parity — `MIRROR_DRIFT` ext

### 3. Corpus-over-code — `HARDCODED_CORPUS_FACT` ext

### 2. Layer firewall — `LAYER_INVERSION` ext

### 1. Build truth — `UNVERIFIED_BUILD_CLAIM` ext

## Seven gates (recompute independently; emit findings, do not patch)

## MANDATORY first step — the date

## Scope fence

## READ-ONLY

**Target:** `$ARGUMENTS` — `rust-contracts`, `rust-core`, `py-contracts`, `py-core`, or

## description: "Adversarial verification of code contracts, generating hostile inputs to uncover boundary vulnerabilities."

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
