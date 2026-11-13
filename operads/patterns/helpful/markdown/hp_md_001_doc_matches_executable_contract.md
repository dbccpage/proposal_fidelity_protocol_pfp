---
pattern_id: HP_MD_001
name: doc_matches_executable_contract
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_001_stale_doc_contract
language: markdown
authority_effect: None
---

# Healthy Pattern: Doc Matches The Executable Contract (`HP_MD_001`)

## Description

The document states the contract the code enforces. Reproduction commands are the ones the package runs. Version strings match `pyproject.toml`, the monograph header, and the release metadata in the same change.

## Structural Signature

- Bundle cardinality in `SKILL.md` equals the cardinality the replay function accepts.
- `README` reproduction lines are copied from the command a test invokes.
- One version string is written in the same commit across README, `pyproject.toml`, and the monograph header.

## Remediation Applied

- Edit the prose to the refused or accepted shape the code implements.
- Re-run the documented command and record a zero exit.
