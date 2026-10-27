# Pandoc & XeLaTeX Build Hygiene

**AuthorityEffect:** None.
**Rule:** `RULE_PANDOC_TEX_BUILD_HYGIENE_001` in `rules/papers/rl_research_paper_template_and_harmonization_discipline.md`.
**Checks:** `research_papers/domain/rules/pandoc_build_rules.py`.

Open this leaf when a Markdown → pandoc → TeX/PDF build fails, when a package
build script declares its own pandoc reader, or when a rebuilt PDF is missing
characters.

## Predicates

| ID | Predicate | Gate rule | Also checked by |
|---|---|---|---|
| P1 | Manuscript has `\( ... \)` math ⇒ every package build script's `--from markdown...` reader contains `+tex_math_single_backslash` | `R_PANDOC_SINGLE_BACKSLASH_MATH` | — |
| P2 | Outside code, math, raw TeX environments and link targets, no `\command` directly follows a letter, digit, colon or closing bracket | `R_MD_PROSE_BACKSLASH` | — |
| P3 | The TeX log has zero `Missing character: There is no X ... in font ...` lines | `R_TEX_MISSING_GLYPHS` (retained `<stem>.log`) | `paper_edition` rebuild PDF step, review Stage 5, checklist `C03` |

## Symptoms → cause

| XeLaTeX symptom | Cause | Fix |
|---|---|---|
| `! Missing $ inserted` / `\mathbb allowed only in math mode` | P1: reader lacks `tex_math_single_backslash` | Use the kit reader `markdown+tex_math_dollars+tex_math_single_backslash+raw_tex+pipe_tables` |
| `! Undefined control sequence` at `W\T`, `L\stall`, `C:\Users` | P2: backslash glued to prose | Write `∖` (U+2216) or `$W\setminus T$`; put paths in `code spans` |
| Exit 0, but characters absent from the PDF | P3: font lacks the glyph | `\newunicodechar{∖}{\um{\setminus}}` in the preamble |

## Glyph mappings used so far

`∖ \setminus`, `∩ \cap`, `∪ \cup`, `ε \varepsilon`, `⁻ ^-`, `↦ \mapsto`,
`∅ \emptyset`, `⋯ \cdots`, `⊆ \subseteq`, `⊂ \subset`, `₅ _5`. The kit preamble
(`_kits/obstruction_paper_kit/obstruction_preamble.tex`) defines
`\um{#1}` as `\ensuremath{#1}`. `describe_missing_glyphs()` prints the
suggested line for each known glyph.

## Commands

```bash
py -3.12 -m research_papers.use_cases.paper_review.cli gates --paper-path <pkg> --format markdown
py -3.12 -m research_papers.use_cases.paper_edition.cli rebuild --paper-path <pkg> --verbose
```

## Anti-patterns

- Copying a pandoc reader string into a package script without
  `tex_math_single_backslash` while the manuscript uses `\( ... \)`. (In
  2026-10, 7 of 18 build scripts in the atlas and projects lacked it.)
- Treating XeLaTeX exit 0 as a clean build without scanning the log.
- Fixing a glued backslash by escaping it as `\\T`; that prints a backslash and
  is still not a set-difference sign.
- Enabling `tex_math_single_backslash` blindly when the prose escapes brackets
  as `\[1\]`: the extension turns `\[ ... \]` into display math.
