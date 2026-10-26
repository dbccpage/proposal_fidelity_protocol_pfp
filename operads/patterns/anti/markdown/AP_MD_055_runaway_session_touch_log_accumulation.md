---
pattern_id: AP_MD_055
name: runaway_session_touch_log_accumulation
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_055_bounded_session_provenance_and_log_exclusion
language: markdown
authority_effect: None
---

# Anti-Pattern: Runaway Session Touch Log Accumulation (`AP_MD_055`)

## Description

An automated session logger sweeps `git status` without excluding session documentation directories. As subsequent sessions run, previously generated session records are captured as touched files. During large repository refactors, this unconstrained capture emits files listing thousands of hyperlinks (up to 10,451 lines / 2.2 MB in a single file), bloating repository size and clogging git history with self-referential provenance churn.

## Detection Signature

- Session documentation records under `_ic/*/documentation/sessions/` or `.agents/documentation/sessions/` exceed 100 KB or 1,000 lines.
- `Touched Artifacts & Files` contains links to other `session_*_session_summary.md` records.
- `Files Modified in Session` reports thousands of files, with the markdown file body almost entirely composed of file links.
- `auto_docs_service.py` does not filter out `sessions`, `_intelligence`, or `_ic` in `get_session_touched_files`.
- `synthesize_session_documentation` appends all touched files without a maximum ceiling.

## Witness

Historical directory `_ic/nro/documentation/sessions/` accumulated 98 session summary files totaling 27.3 MB across October 3 to October 11, 2026.
Witness file: `session_20261005_191624Z_session_summary.md` (2,205,097 bytes, 10,472 lines):
- Recorded 10,451 touched files in a single session summary.
- Included 10 prior `session_20261003_*.md` files in its own touched files list.
- All 98 files contained empty `failed_claim` template placeholders without substantive lessons.

## Hazard & Failure Mode

- Runaway markdown file bloat exhausts disk budget and pollutes git history.
- Context window exhaustion when agents attempt to read session histories.
- Infinite logging loop where session logs continually record previous session logs.

## Dual Healthy Pattern

See [HP_MD_055_bounded_session_provenance_and_log_exclusion](../../helpful/markdown/HP_MD_055_bounded_session_provenance_and_log_exclusion.md).
