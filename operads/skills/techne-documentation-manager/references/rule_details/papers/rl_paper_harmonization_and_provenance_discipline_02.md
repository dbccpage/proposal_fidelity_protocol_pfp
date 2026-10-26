# Detailed definition: Paper Harmonization & Provenance Discipline (2)

**AuthorityEffect:** None.

Parent: [Paper Harmonization & Provenance Discipline](../../../../../rules/papers/rl_paper_harmonization_and_provenance_discipline.md). Load for the matching predicate, not every task.

## TeX and PDF Synchronized Parity Invariant

> **Manuscript Rendering & Deliverable Synchronization:**
>
> 1. **Markdown to TeX and PDF Parity:**
>    Whenever manuscript markdown sources undergo edits affecting mathematical claims, author metadata, dates, or version numbers, the rendered LaTeX (`paper.tex`) and PDF deliverable (`paper.pdf`) must be re-compiled immediately.
> 2. **Zero Glyph Loss & Formatting Integrity:**
>    Recompiled TeX and PDF files must report zero missing characters/glyphs in compiler logs, and formatting must match the published markdown version.

---

## Manuscript Reference Citations Closure Invariant

> **Bibliographic Citation Completeness:**
>
> 1. **Reference Section Requirement:**
>    When a manuscript cites numbered bibliographic references (e.g. `[1]`, `[2]`), an explicit `## References` section must exist resolving every cited bracketed reference index to a complete citation record.
> 2. **No Dangling Citation Pointers:**
>    Dangling citation numbers without a corresponding entry in the bibliography are prohibited.

---

## Manuscript Session Narration Prohibition

> **Formal Monograph Prose Hygiene:**
>
> 1. **No Interactive Dialogue Debris:**
>    Manuscripts and public monographs must present formal mathematical exposition only. Prose must not contain interactive session narration, conversational dialogue ("In this session we...", "The assistant notes..."), or prompt instructions.
