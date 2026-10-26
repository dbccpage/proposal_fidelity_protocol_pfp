---
name: techne-comment-slop-hunter-killer
description: "Find and re-route chatty LLM comments in Python, Rust, SQL and Lean, keeping docstrings and pragmas."
invocation: on-demand
operad_source_colours: ["Code"]
operad_target_colour: "Receipt"
operad_arity: 1
operad_residual: "diagnostic"
families: [techne, clean-architecture, documentation, comment-hygiene]
---

# Techne Comment Slop Hunter Killer

`AuthorityEffect: None.`

## Overview

`techne-comment-slop-hunter-killer` enforces code comment hygiene across the repository. It scans source code (`.py`, `.rs`, `.sql`, `.lean`) for conversational AI chatter, step-by-step narration, and trivial syntax paraphrasing.

When executed in fix/reroute mode, it extracts low-signal comments from source files and preserves them in structured markdown documentation records under `.agents/documentation/slop_audit/`. This ensures that source code remains clean, sovereign, and uncluttered, while preserving any historical thoughts or explanations in formal documentation custody.

For classification categories and protected pragma specifications, see [Comment Slop Taxonomy](references/comment_slop_taxonomy.md).

---

## Governing Invariants

1. **Docstring Protection Invariant:**
   - Formal Python docstrings (`"""..."""` and `'''...'''`) are never treated as comments or stripped.
   - Rustdoc comments (`///` outer item docs and `//!` inner module docs) are formal documentation attributes (`#[doc = "..."]`) and are strictly protected.
2. **Pragma & Safety Protection Invariant:**
   - Compiler, linter, and typechecker directives (`# noqa`, `# type: ignore`, `// SAFETY:`, `// INVARIANT:`, `// CHECK:`, `// TODO:`, `// FIXME:`, shebangs, encoding cookies) are strictly protected.
3. **Lossless Re-routing Invariant:**
   - Stripped comments are never deleted permanently into the void; they are written to `.agents/documentation/slop_audit/<relative_path>.md` with line numbers and classifications.
4. **Forbidden Surfaces Invariant:**
   - Frozen directories (`.lake/`, `target/`, `node_modules/`, `.venv/`, `quarantine/`, `archive/`) are strictly excluded from scans.

---

## Quick Commands & Scripts

### 1. Scan Only (Diagnostic Mode)

Scan a file, directory, or the active repository for comment slop without modifying code:

```bash
# Scan specific directory
py -3.12 -m omega_engine_operations.use_cases.packaging.comment_slop_router omega_engine_pfp/

# Run via skill entrypoint
py -3.12 omega_engine_operads/skills/techne-comment-slop-hunter-killer/scripts/run.py --scan-only omega_engine_pfp/
```

### 2. Verbose Scan (List Every Finding)

Print file path, line number, category, and cleaned comment text for every detected artifact:

```bash
py -3.12 -m omega_engine_operations.use_cases.packaging.comment_slop_router --verbose omega_engine_pfp/
```

### 3. Fix / Reroute Mode

Extract slop comments, strip them from source code, and append audit records to `.agents/documentation/slop_audit/`:

```bash
py -3.12 -m omega_engine_operations.use_cases.packaging.comment_slop_router --fix omega_engine_pfp/
```

---

## Integration with `auto-docs` & `auto-oe-autop`

- **Session Pipeline (`auto-docs`):** During session documentation compilation, `auto-docs` invokes this skill to inspect all session-touched code files and automatically route extracted comments before committing.
- **Autonomous Meta-Pipeline (`auto-oe-autop`):** Executed during **Stage 7** to enforce zero-comment-slop hygiene across active proposals and refactors.

---

## Mandatory Defect Investigation Logging (`RULE_DEFECT_INVESTIGATION_LOGGING_001`)

Whenever parser exceptions, Unicode encoding failures, or docstring parsing regressions occur during comment extraction:
1. Log an investigation report under `_intelligence/blackrod/investigations/investigation_{YYYYMMDD}_techne_comment_slop_{defect_id}.md`.
2. Record sample code, observed classification, and expected AST behavior.
