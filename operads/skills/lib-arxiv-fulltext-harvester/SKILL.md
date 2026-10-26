---
name: lib-arxiv-fulltext-harvester
description: "Download arXiv full-text PDFs, extract LaTeX equations, and write literature summaries to the library."

operad_source_colours: ["Ledger", "Paper"]
operad_target_colour: "Ledger"
operad_arity: 2
operad_residual: "unknown"
---

# lib-arxiv-fulltext-harvester

**Ordering:** arXiv first (≈99% success). Do not carpet-scan `markdown/`; Filter-Select-Read via indexes (Paper 007 / `/omega-allopoietic-engine`).

## Host pipeline (`omega_engine_university` CLI — retired)

**Retired path.** `omega_engine_university` was the pre-split repository root and exists in neither CODA nor anomalonpy; the command below is kept for the record and does not run here.

## invariance_level: Tier 16

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
