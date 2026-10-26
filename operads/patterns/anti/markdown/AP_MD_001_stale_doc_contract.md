---
pattern_id: AP_MD_001
name: stale_doc_contract
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_001_doc_matches_executable_contract
language: markdown
authority_effect: None
---

# Anti-Pattern: Stale Doc Contract (`AP_MD_001`)

## Description

A skill file, README, or appendix states a contract the executable refuses, or it names a command and version the package does not run.

## Detection Signature

- The prose names a bundle size, reproduction command, or version that the code or `pyproject.toml` contradicts.
- Seen in code-review records for PRs 580, 583, and 588 (`stale-doc-vs-code`, `reproduction-doc-mismatch`, `version-date-parity`).

## Hazard & Failure Mode

- A reader follows the document and gets a refusal or a nonzero exit.
- A release note cites a version the package files do not share.

## Dual Healthy Pattern

See [HP_MD_001_doc_matches_executable_contract](../../helpful/markdown/HP_MD_001_doc_matches_executable_contract.md).
