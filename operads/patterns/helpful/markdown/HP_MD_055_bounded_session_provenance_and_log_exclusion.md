---
pattern_id: HP_MD_055
name: bounded_session_provenance_and_log_exclusion
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_055_runaway_session_touch_log_accumulation
language: markdown
authority_effect: None
---

# Healthy Pattern: Bounded Session Provenance & Log Exclusion (`HP_MD_055`)

## Description

Automated session documentation explicitly ignores session documentation directories from touched file discovery, and bounds the displayed touched artifacts list to a deterministic maximum ceiling with a summary count for remaining items.

## Construction

- In `get_session_touched_files`, filter out paths containing `sessions`, `_intelligence`, `_ic`, and `.system_generated`.
- In `synthesize_session_documentation`, display at most 100 touched files in markdown. If more files are touched, append `- *... and N additional files modified*`.
- When session documentation accumulates in active estates, periodically digest and purge historical provenance files via `/adversary-digests` to maintain terminal estate boundaries.

## Limit

This pattern governs automated session documentation services. It does not replace full git diff inspection for code review or PR audit workflows, where `git diff $(git merge-base main HEAD)...HEAD` remains mandatory.
