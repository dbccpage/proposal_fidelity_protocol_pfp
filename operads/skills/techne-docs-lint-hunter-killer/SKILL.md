---
name: techne-docs-lint-hunter-killer
description: "Fix markdown lint errors, bad tables, LaTeX delimiters, trailing whitespace and code block syntax."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# Techne Docs Lint Hunter Killer

## Forbidden Surfaces (Never Sweep, Never `--fix`)

Vendored dependency clones and generated build caches are **frozen surfaces**. No lint, format, or `--fix` pass may write to them, and no swarm may "clean up" their markdown.

| Surface | Why it is frozen |
| :--- | :--- |
| `.lake/` | Vendored Lean 4 dependency clones (mathlib, aesop, batteries, Cli, importGraph, LeanSearchClient, plausible, proofwidgets, Qq) plus build cache. Dirtying them makes `lake build` stamp `warning: <pkg>: repository '...' has local changes` into every proof receipt it emits. |
| `target/` | Rust build directory. On Windows dev boxes it also hosts the codex worktrees, whose `.lake/packages` are NTFS junctions back into the main checkout -- so there is exactly ONE physical package tree to protect. |
| `node_modules/`, `.venv/`, `venv/`, `site-packages/`, `.elan/` | Third-party installed packages. Not ours to reformat. |

The authoritative exclusion list is the tracked **`.markdownlintignore`** at the repository root. Because it is tracked, every `git worktree` checkout receives its own copy and the protection propagates automatically.

> **Incident of record (2026-07-29):** a repo-wide formatting sweep rewrote 39 markdown files across the 9 vendored Lean packages (ATX → Setext headings, blank-line insertion inside lists -- the signature of `markdownlint-cli --fix`). Zero `.lean` files were touched, so proof soundness was unaffected -- but the resulting dirty-dependency warnings were baked into `engine/research/published/004_projection_obstruction/PO000_LEAN_AXIOM_REPORT.txt`, which ships inside a Zenodo release bundle. An external referee reading that receipt cannot tell documentation-only dirt from tampered proofs, so it reads as untrustworthy formal evidence.
>
> Root-cause note, verified experimentally (`markdownlint-cli` 0.49.1): by default the tool's glob **does not descend into dot-directories** (`.lake/`, `.github/`, etc. are skipped), so the plain `--fix "**/*.md"` invocation above cannot reach `.lake/` on its own -- reproduced as a negative control. The vendored files are reachable, and were in fact rewritten, only when the sweep is run **with `-d`/`--dot`** (needed elsewhere, since `.github/PULL_REQUEST_TEMPLATE.md` was among the 39 dirtied files). The prior `--ignore "target"` guard would not have helped either way: the physical package tree is `engine/lean4/.lake/packages`, which is NOT under `target/`. `--ignore-path .markdownlintignore` is the fix that holds regardless of whether `--dot` is used.

---

## Quick Commands & Scripts

### 1. Markdown & Document Linting

```powershell
# Run markdown linter auto-fix across the entire repository
# MUST be run from the repository ROOT: --fix REWRITES every file it matches, and the ignore
# list is resolved relative to CWD. NEVER drop --ignore-path -- it is the only thing keeping
# the sweep out of the vendored frozen surfaces listed under "Forbidden Surfaces" below
npx markdownlint-cli --fix "**/*.md" --ignore-path .markdownlintignore

# Check for invisible look-alike Unicode characters (U+2011, U+2013, U+00A7, etc.)
python -c "import glob, collections; [print(f, collections.Counter(c for c in open(f, encoding='utf-8', errors='ignore').read() if ord(c)>127)) for f in glob.glob('**/*.md', recursive=True)]"
```

## 2. Python Code Quality (Ruff)

```powershell
# Python linter check and format
ruff check --fix engine_py/ tests/ scripts/
ruff format engine_py/ tests/ scripts/
```

## 3. Rust Formatting & Clippy

```powershell
# Rust fmt and clippy checks
cargo fmt --all --check
cargo clippy --all-targets --all-features -- -D warnings
```

## 4. JavaScript / TypeScript & Web

```powershell
npm run lint                         # Full lint (Biome + oxlint + tsgo)
npx eslint frontend/src/             # ESLint flat config check
```

---

## Zero-Tolerance Formatting Rules

### Markdown & Preprints

1. **ATX Headings Only:** Never use Setext-style headings with long underline dividers (`==========` or `----------`). Use explicit `#`, `##`, `###`.
2. **Standard Math Delimiters:** Standardize all LaTeX math delimiters to `$` for inline math and `$$...$$` for display math. Flag and replace `$...$` or `$$...$$`.
3. **Table Alignment:** Every GFM table must have perfectly aligned header pipes (`|---|---|`) with no missing cells or broken multiline rows.
4. **Code Block Tagging:** Every fenced code block must specify an explicit language tag (e.g., ```text,```python, ```rust,```powershell).
5. **UTF-8 ASCII Cleanliness:** Replace invisible non-breaking hyphens (U+2011), smart quotes, and non-ASCII dashes with standard ASCII equivalents.
6. **MD031 / Blanks Around Fences:** Every fenced code block (```...```) MUST be surrounded by blank lines (both before the opening triple backticks and after the closing triple backticks). Never attach a code fence directly to a list item, heading, table, or paragraph line without a separating blank line (`markdownlint-cli` rule MD031).
7. **No Unicode Header Ornaments:** Never use decorative box-drawing or repeating symbol dividers in headings or comments (such as `# ═════════`, `# ─────────`, `# *********`). Use standard Markdown ATX headings (`#`, `##`, `###`) and standard clean `---` thematic breaks with a blank line before and after.

### Python & Rust Engineering

1. **Pydantic v2 Models:** Ensure all models use Pydantic v2 `BaseModel` with strict field validation.
2. **Unused Imports & Variables:** Remove all unused imports (`F401`) and unused variables (`F841`).
3. **Line Endings:** Enforce consistent LF / CRLF Git settings and remove trailing whitespace.

## Sub-Module: Publication Hard Gates & Markdown De-Linting

1. **Publication Hard Gates:**
   - Literal nonempty `code/` with real Python modules.
   - Non-vacuous test suite (banning empty/assert True tests).
   - Banned `GT*` claim ID prefixes (must use `CODA-*`).
   - Banned host path leaks (no local user paths in published artifacts).
   - Audit/fix receipts MUST reside in `research/audits/`, never inside publication packages.
2. **Markdown De-Linting Law (`RULE_MARKDOWN_DELINTING_001`):**
   - Zero markdown lint errors or warnings permitted.
   - Run `npx markdownlint-cli` on modified docs prior to committing.

## Sub-Module: Bulk Rewrite Artifact Sentinel Protocol (`bulk-rewrite-artifact-sentinel`)

1. **Closing Code Fence Integrity:**
   - Detects trailing tokens appended immediately after closing code fences (such as ``` ext or `span` ext).
   - Closing markdown code fences (```) must never carry info strings, language tags, or trailing noise tokens.
2. **Multi-Host Uniformity Scanning:**
   - Scans across all four skill host trees (`.agents/skills`, `.claude/skills`, `.codex/skills`, `.grok/skills`) to detect cross-host mechanical leakage or uniform corruption signatures resulting from large-scale automated file rewrites, bulk translations, or script passes.
   - Flags identical corruption signatures indicating unvalidated batch operations.
3. **Audit & Non-Destructive Emission:**
   - Emits structured `Audit` receipts binding exact file paths, line numbers, byte offsets, and artifact signatures.
   - Operates with `AuthorityEffect: None`; proposes candidate cleanups without executing unverified batch modifications.

### Mandatory Defect Investigation Logging (`RULE_DEFECT_INVESTIGATION_LOGGING_001`)

Whenever this skill encounters any error, build failure, veto, linter defect, anti-pattern breach, proof/contract obstruction, or process violation:

1. Automatically create a formal investigation report under:
   `_intelligence/blackrod/investigations/investigation_{YYYYMMDD}_{skill_name}_{defect_id}.md`
2. Include full error trace/context, root cause analysis, affected files, and recommended workflow remediation plan for Blackrod review.
