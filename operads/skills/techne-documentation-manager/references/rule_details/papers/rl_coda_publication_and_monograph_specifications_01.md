# Detailed definition: CODA Publication & Monograph Specifications (1)

**AuthorityEffect:** None.

Parent: [CODA Publication & Monograph Specifications](../../../../../rules/papers/rl_coda_publication_and_monograph_specifications.md). Load for the matching predicate, not every task.

# Rule: CODA Publication Rubric, Monograph Frontmatter & Descriptions Specifications

**AuthorityEffect:** None.

This document codifies the mandatory publication rubric, file quartet layout, proof triad tie-out, frontmatter ordering, descriptions standard, and deposit boundary invariants extracted from `omega_engine_atlas/coda_atlas/_kits/` (`coda_publication_rubric.md`, `descriptions_specification.md`, `paper_frontmatter_specification.md`, `obstruction_paper_kit/`, `paper_template/`). Cross-references: [`rl_research_paper_template_and_harmonization_discipline.md`](../../../../../rules/papers/rl_research_paper_template_and_harmonization_discipline.md), [`rl_research_paper_and_monograph_packaging.md`](../../../../../rules/papers/rl_research_paper_and_monograph_packaging.md), [`rl_paper_harmonization_and_provenance_discipline.md`](../../../../../rules/papers/rl_paper_harmonization_and_provenance_discipline.md).

---

## 1. Research Program Naming & Monograph Slug Invariant (`RULE_CODA_RESEARCH_PROGRAM_NAMING_001`)

> **Research Program & Monograph Naming Syntax:**
>
> 1. **Program Directory Syntax (`NNN_<lowercase_slug>`):**
>    Research Program containers under `omega_research/programs/` or `omega_engine_atlas/coda_atlas/` must follow `^\d{3}_[a-z0-9_]+$`.
>    - Prefix: Exactly three decimal digits `NNN` in `000` to `899` (e.g., `001_coda`, `004_projection_obstruction`).
>    - Separator: Exactly one underscore (`_`). Hyphens or double underscores directly following prefix digits are prohibited.
>    - Slug: Lowercase alphanumeric words separated by single underscores.
> 2. **Strict Lowercase Filename Invariant:**
>    All monograph manuscripts, logs, documentation, and code files must use lowercase filenames (`[a-z0-9_.-]+`). The only permitted uppercase filenames are `README.md`, `LICENSE`, `LICENSE-CODE`, and `MANIFEST.sha256` / `SHA256SUMS`.
> 3. **Tooling Isolation:**
>    Kit directories (`_kits/obstruction_paper_kit/`, `_kits/paper_template/`) are shared tooling. Papers must never be authored or maintained inside kit folders.

---

## 2. Monograph Container Layout & File Trio/Quartet Invariant (`RULE_CODA_PAPER_CONTAINER_LAYOUT_001`)

> **Per-Paper Package Directory Structure:**
>
> Every research paper must inhabit its own dedicated container directory (`<paper_slug>/`) adhering to the canonical container layout:
>
> 1. **Main Monograph (`<paper_slug>.md`):**
>    Contains the core prose, mathematical primitives, formal statements, proofs, worked examples, and discussion. Embedded change logs or raw claim ledger tables are prohibited in the main paper body.
> 2. **Change Log (`<paper_slug>_change_log.md`):**
>    Tracks dated version history, additions, edits, and supersession notes.
> 3. **Optional Math Spine (`<paper_slug>_math_spine.md`):**
>    Dedicated container for extensive multi-page prose proofs when full derivations exceed 500 lines or impair reading flow. Shorter proofs remain inline.
> 4. **Support Documents Directory (`docs/`):**
>    Contains `descriptions.md` (conforming to the Single-Version Unicode Standard), `keywords.md`, `references.md` / `provenance.md`, and checksum manifests.
> 5. **Executable Verification Code Directory (`code/`):**
>    Contains hermetic Python reference engines, exact rational property tests (`<claim_id>_test.py`, `<paper_slug>_replay.py`), and `deposit_paths.py`.
> 6. **Formal Lean 4 Proof Kernel Directory (`lean4/`):**
>    Contains `lakefile.lean` / `lakefile.toml`, `Core.lean`, and `Census.lean`.
> 7. **Lean 4 Module PascalCase Naming Invariant:**
>    All `.lean` proof and model files under `lean4/` must be named in `PascalCase` matching their internal module namespace (e.g., `Core.lean`, `BalancePreservingEdits.lean`, `NativeFutureCompression.lean`). The package configuration file `lakefile.lean` remains lowercase per the official Lake specification.

---

## 3. Proof Triad Tie-Out & Anti-Slop Discipline (`RULE_PROOF_TRIAD_TIE_OUT_001`)

> **Python $\leftrightarrow$ Lean 4 $\leftrightarrow$ Prose Proof Triad:**
>
> 1. **Small Fragment Verification:**
>    Before drafting claims or proof sketches in the monograph prose, verify small algorithmic and algebraic steps in executable Python (`code/`) and Lean 4 proof obligations.
> 2. **Triad Obligation Alignment:**
>    Every mechanized theorem or lemma must possess matching Python property checks, formal Lean 4 obligations, and explicit prose documentation.
> 3. **Prohibition of Handwaving:**
>    Unchecked prose assertions, unverified conjectures presented as theorems, and ungrounded guesses are prohibited.
> 4. **Canonical Claim Breakdown Types:**
>    When indexing formal obligations, categorize claims strictly under the 7 canonical types: `LEAN4_PROOF`, `PROSE_PROOF`, `CODE_DEMO_PYTHON`, `CODE_DEMO_RUST`, `CODE_DEMO_JS_TS`, `WORKED_EXAMPLE`, or `THEOREM_DEFINITION`.

---

## 4. Four-Line Centered Header (`RULE_PAPER_FRONTMATTER_SEQUENCE_001`)

> **Monograph header:**
>
> The top of a monograph file is four centered lines, and only four lines: Title, Author, Date, Version. The line format is owned by [`paper_frontmatter_specification.md`](../../../../../../omega_engine_atlas/coda_atlas/_kits/paper_frontmatter_specification.md) and checked by `paper_header_schema.py`.
>
> 1. **Title:** `#` plus the monograph title.
> 2. **Author:** the author name. The canonical author is `Jeremy H. Carroll`.
> 3. **Date:** `YYYY-MM-DD`.
> 4. **Version:** `Version X.Y.Z`.
>
> A subtitle, when the manuscript has one, is the single extra centered line between Title and Author.
>
> The section after Version is Abstract (`## Abstract`). No status, license, authority line, architecture table, or refusal box stands between Version and Abstract. Rights grants stay in `LICENSE` and `README.md`. No horizontal rule is permitted above the Abstract. The LaTeX title block is the same rows in a center environment. Pandoc `\maketitle` is prohibited.

---

## 5. Mandatory Monograph Section Skeleton (`RULE_MONOGRAPH_SECTION_SKELETON_001`)

> **10 Canonical Section Categories:**
>
> Every monograph in every Research Program must follow the canonical section ordering:
>
> 1. `FRONTMATTER`: The four centered lines (Title, Author, Date, Version), plus one subtitle line only when the manuscript has a subtitle.
> 2. `ABSTRACT`: The next section. Abstract prose may close with `**Why a researcher should care.**` / `**Why this matters.**`
> 3. `INTRODUCTION`: Section 1 (Context, motivation, related literature).
> 4. `PRIMITIVES_AND_FOUNDATIONS`: Section 2 (Posets, cochains, primitive differences, configurations).
> 5. `CORE_THEOREMS`: Section 3 (Formal statements, proofs, structural bounds, exact potentials).
> 6. `WORKED_EXAMPLE`: Section 4 (Concrete numerical/symbolic instance, failure mode, falsifiability).
> 7. `MECHANIZATION_AND_VERIFICATION`: Section 5 (Python test counts, Lean 4 axiom checks, Lake build).
> 8. `DISCUSSION_NON_CLAIMS`: Section 6 (Scope limits, non-claims, future avenues).
> 9. `REFERENCES`: Bibliography with persistent Zenodo DOIs and literature citations.
> 10. `CLAIM_INDEX`: Claim-ID body index pointing to sibling ledger, or retired packaging index.

---

## 6. Single-Version Unicode Word-Document Standard for descriptions.md (`RULE_DESCRIPTIONS_UNICODE_STANDARD_001`)

> **The "One and Only One" Rule for docs/descriptions.md:**
>
> Every paper package must contain one and only one version of `docs/descriptions.md`. Dual-target variants (`Target 1: ZENODO-HTML` alongside `Target 2: ZENODO-TEXT`) inside repository files are prohibited.
>
> 1. **Zero HTML Tags:**
>    Do not include HTML tags (`<p>`, `<strong>`, `<em>`, `<ul>`, `<ol>`, `<li>`, `<code>`, `<pre>`, `<blockquote>`, `<div>`, `<span>`, `<a>`).
> 2. **Zero LaTeX / TeX Math:**
>    Do not include raw TeX math environments or symbols (`$...$`, `$$...$$`, `\(...\)`, `\[...\]`, `\varepsilon`, `\to`, `\mathbb{R}`).
> 3. **Clean Unicode Typographic Glyphs:**
>    Use standard Unicode mathematical glyphs, Greek characters, and relation symbols directly:
>    `ε`, `→`, `·`, `−` (true Unicode minus U+2212), `≥`, `≤`, `⇒`, `⊗`, `ℝ`, `ℤ`, `‖·‖`, `ℓ¹`, `ℓ²`, `ℓ∞`, `∘`, `im(p)`, `fib(p)`.
> 4. **Canonical 8-Section descriptions.md Skeleton:**
>    - `# [Paper Canonical Title] ([Paper Abbreviation / Code])`
>    - `Subtitle: [Descriptive Subtitle]`
>    - `## Abstract`
>    - `## Why This Matters`
>    - `## Core Theorems`
>    - `## Formal Verification and Computational Artifacts`
>    - `## Scope Boundaries and Non-Claims`
>    - `## Reproduction`
>    - `## Related Identifiers & Citations`

---
