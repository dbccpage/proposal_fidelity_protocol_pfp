# Comment Slop Taxonomy & Protection Matrix

`AuthorityEffect: None.`

## 1. Classification Categories

The `techne-comment-slop-hunter-killer` engine classifies comments into four primary categories:

| Category | Description | Examples | Handling |
|---|---|---|---|
| `CONVERSATIONAL_AI_ARTIFACT` | Conversational narration, multi-step instructions, or chat pleasantries. | `// Step 1: Now we calculate the norm`, `# Note: we need to handle this edge case` | Extracted and re-routed to `.agents/documentation/slop_audit/`. |
| `TRIVIAL_SYNTAX_PARAPHRASE` | Redundant comments that merely re-state trivial syntax in English. | `// return true`, `# import modules`, `# increment count` | Extracted and re-routed to `.agents/documentation/slop_audit/`. |
| `LOW_SIGNAL_EDITORIAL` | Subjective commentary, historical residue, or speculation. | `// this might be needed later`, `# hack for testing` | Extracted and re-routed to `.agents/documentation/slop_audit/`. |
| `PROTECTED` | Mandatory tool pragmas, compiler directives, safety proofs, and docstrings. | `// SAFETY: Unsafe block certified`, `# noqa: F401`, `/// Doc comment` | **Preserved intact.** Never stripped or modified. |

---

## 2. Protected Surface Specifications

### A. Python (`.py`)
- **Docstrings:** Module-level, class-level, and function-level docstrings (`"""..."""` and `'''...'''`) are parsed as AST string literals and never classified as comments.
- **Linter & Type Pragmas:** `# noqa`, `# type: ignore`, `# mypy:`, `# pylint:`, `# flake8:`, `# fmt:`, `# coding:`, shebangs (`#!/usr/bin/env python3`).
- **Safety & Invariant Annotations:** `# SAFETY:`, `# INVARIANT:`, `# CHECK:`, `# TODO:`, `# FIXME:`.

### B. Rust (`.rs`)
- **Rustdoc Outer Item Docs (`///`):** Formal API documentation attributes compiling to `#[doc = "..."]`.
- **Rustdoc Inner Module Docs (`//!`):** Crate and module-level formal documentation attributes.
- **Safety Annotations (`// SAFETY:`):** Critical unsafe block justifications required by repository rules.
- **Clippy / Compiler Directives:** `// ALLOW`, `// DENY`, `// WARN`, `// FEATURE`, `// CLANG-FORMAT`.

### C. SQL (`.sql`) & Lean (`.lean`)
- **Directives:** `-- SAFETY:`, `-- INVARIANT:`, `-- TODO:`, `-- FIXME:`.

---

## 3. Re-routing Output Destination

When comments are stripped from a file located at `<rel_path>`, an audit record is generated at:
`.agents/documentation/slop_audit/<rel_path>.md`

Record format:
```markdown
# Comment Slop Audit Record: <rel_path>

AuthorityEffect: None.

**Source File:** `<rel_path>`
**Extracted Comments Count:** N

## Extracted Commentary

- Line XX [CATEGORY]: `comment text`
```
