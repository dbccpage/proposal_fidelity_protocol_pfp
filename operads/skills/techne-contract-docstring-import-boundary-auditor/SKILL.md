---
name: techne-contract-docstring-import-boundary-auditor
description: "Check Python contract files put the docstring first, imports at the head, and have no E402 violations."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [python, contracts, lint, clean-architecture]
---

# Contract Docstring Import Boundary Auditor

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Code hygiene auditor; emits module boundary verification receipts)
**Governance Council:** `L3_logos_techne`

---

## 1. Prime Directive

The **Contract Docstring Import Boundary Auditor** verifies that mechanical Python contract mirrors, QA surfaces, and generated modules maintain docstrings at line 1 and all top-level imports consolidated at the file top, eliminating `E402` lint defects without suppressing linter rules.

---

## 2. Core Invariants & Rules

1. **Docstring Precedence Invariant:**
   - Module docstrings must reside at the very top of the file (line 1), preceding all import statements including `from __future__ import annotations`.
2. **Top-Level Import Consolidation:**
   - All module-level imports must be grouped together immediately following the docstring and future imports, preventing fragmented imports scattered across function definitions.
3. **Zero-Suppression Law:**
   - Never suppress `E402` or `# noqa` violations on contract mirrors; resolve them structurally by re-ordering docstrings and grouping imports.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be pure UTF-8 without BOM and pass `npx markdownlint-cli` with **0 errors and 0 warnings**.
