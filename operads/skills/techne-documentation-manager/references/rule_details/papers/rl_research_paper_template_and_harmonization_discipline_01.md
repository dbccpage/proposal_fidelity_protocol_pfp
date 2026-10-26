# Detailed definition: Paper Template & Harmonization Discipline (1)

**AuthorityEffect:** None.

Parent: [Paper Template & Harmonization Discipline](../../../../../rules/papers/rl_research_paper_template_and_harmonization_discipline.md). Load for the matching predicate, not every task.

# Rule: Canonical Research Paper Template & Harmonization Pipeline Invariants

**AuthorityEffect:** None.

All research papers, preprints, and formal monograph packages under `omega_engine_atlas/coda_atlas/` and `omega_research/programs/` must strictly comply with the following invariants. Complete execution pipelines and scaffolding commands reside in [`governance-research-paper-edit-publish`](../../../../governance-research-paper-edit-publish/references/harmonization_pipeline.md). Cross-reference publication rubric and specifications: [`rl_coda_publication_and_monograph_specifications.md`](../../../../../rules/papers/rl_coda_publication_and_monograph_specifications.md).

---

## 1. Canonical Template Adherence (`_kits/paper_template/`)

- **No Bespoke Scripts**: Packages must not implement hand-crafted release scripts; all papers must align with canonical tools in `_kits/paper_template/` (`verify_deposit.py`, `tools/rebuild_release.py`, `tools/replay_lean_axiom_census.py`, `scripts/regen_sha256sums.py`, `scripts/build_deposit_zip.py`).
- **Dynamic File Discovery**: Release tools must dynamically discover files via `deposit_paths.walk_files`; hardcoded static file lists are prohibited.

---

## 2. Harmonization & Verification Discipline

- **Topological Harmonization**: Before submitting for referee review, all derived artifacts (figures, Lean census, checksum manifests, release zips) must be regenerated in strict topological order via `paper_edition.cli rebuild`.
- **Bidirectional Manifest Verification**: `verify_deposit.py` must enforce strict two-way reconciliation between tracked disk files and `MANIFEST.sha256` with zero untracked/scratch file leaks.
- **Two-Way Manifest Sweep & Transient Cache Cleanliness**: `verify_deposit.py` strictly verifies that every disk file is tracked in `MANIFEST.sha256` and vice versa. Prior to manifest re-sealing (`rebuild_release.py`) and verification runs, all transient runtime directories (`__pycache__`, `.pytest_cache`, `.hypothesis`) must be purged. Lean 4 proof kernels under `lean4/` must be included in `MANIFEST.sha256` and `SHA256SUMS` with zero untracked artifacts.

---

## 3. Deterministic Packaging & Lean 4 Axiom Honesty

- **Deterministic Archive Bundling**: Release archives must be built deterministically using fixed DOS timestamps, UNIX create system (`3`), and ordinal UTF-8 entry sorting.
- **Axiom Census Totality**: All Lean 4 proof kernels must compile with exit code 0 against the standard axiom whitelist (`propext`, `Quot.sound`, `Classical.choice`). Any occurrence of `sorry` or unapproved axioms is a blocking gate violation.

---

## 4. Reader-Facing Dialect & Authority Syntax Firewall

- **Zero Governance Token Leakage in Manuscripts**: Internal agent governance syntax (such as `AuthorityEffect: None`, `AuthorityEffect::None`, or `**AuthorityEffect:** None`) must NEVER appear in reader-facing manuscript prose, abstract, body, nonclaims, or companion PDF/TeX artifacts.
- **Academic Nonclaim Standard**: When declaring the absence of operational or legal authority in published monographs read by external researchers, use standard academic phrasing:
  *“This monograph assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing.”*
  (Normalized checklist gate `C02` asserts `"authorityeffect" not in _normalize(raw_pdf_text)`).

---

## 5. LaTeX Typography, Layout & Platform Neutrality Invariants

- **No Pandoc `\maketitle` Blocks (`C03`)**: TeX sources must not include generated `\maketitle` blocks. The title block is the four centered rows Title, Author, Date, and Version. A subtitle is the one extra row between Title and Author.
- **Zero Overfull `\hbox` Clipping (`C03`)**: Compound slashed terms in LaTeX tables (e.g. `carrier/\allowbreak map/\allowbreak unit/\allowbreak calibration`) must provide explicit break points (`\allowbreak`) to prevent margin overflow and text clipping.
- **Platform-Neutral Lean Axiom Reports (`G05`)**: `lean4/axiom_report.txt` headers must omit machine-specific platform target triples (`windows-gnu`, `linux-gnu`, `darwin`), recording only toolchain version, commit hash, and release mode.

### Pandoc & XeLaTeX Source Hygiene (`RULE_PANDOC_TEX_BUILD_HYGIENE_001`)

Three defects stopped or silently damaged one monograph build on 2026-10-06:

1. **Single-backslash math needs its reader extension.** If the manuscript writes inline math as `\( ... \)`, every package build script that declares a pandoc Markdown reader must enable `+tex_math_single_backslash`. Without it pandoc reads `\(` as an escaped parenthesis and passes `\mathbb` as raw TeX outside math mode. The kit reader is `markdown+tex_math_dollars+tex_math_single_backslash+raw_tex+pipe_tables`.
2. **No backslash command glued to a word in prose.** Under `raw_tex`, `W\T` (a set difference) or `C:\Users` becomes an undefined control sequence. Write `∖` (U+2216) or `$W\setminus T$`, and put paths in code spans.
3. **Zero `Missing character` lines in the TeX log.** XeLaTeX drops a glyph the font lacks and still exits 0. Map each one in the preamble with `\newunicodechar`, using the kit's `\um{...}` macro for math symbols.

Checked by `omega_engine_research_papers/domain/rules/pandoc_build_rules.py` (gate rules `R_PANDOC_SINGLE_BACKSLASH_MATH`, `R_MD_PROSE_BACKSLASH` and `R_TEX_MISSING_GLYPHS`). The same log scan runs in `paper_edition` rebuild, in review Stage 5, and in checklist `C03`.

---

## 6. Flexible Release Verifier Parity

- **Dual Verifier Support**: Release validation harnesses must dynamically inspect and run whichever canonical release verifier is present (`verify_deposit.py` or `tools/rebuild_release.py`), ensuring legacy and template-based monograph packages pass Stage 6 without requiring duplicate tooling.

---

## 7. Metadata, Title Glyph Normalization & Triad Date Parity (`A08`, `C02`, `Stage 6`)

- **Title Math Glyph Normalization (`C02`)**: H1 title headings in markdown manuscripts and `zenodo_metadata.json` must avoid raw LaTeX math delimiters `$...$`. Math mode causes XeLaTeX to emit Unicode Mathematical Italic glyphs (e.g. `\U0001d436` for $C$), which fail PyMuPDF normalized text extraction (`_normalize`) against plain ASCII titles. Use markdown superscript (`C^k^`) or LaTeX text commands (`C\textsuperscript{k}`) to guarantee standard ASCII Latin glyph emission.
- **Date & Version Parity (`A08`, `rebuild_release`)**: The release date and semantic version must agree identically across:
  1. `zenodo_metadata.json` (`publication_date` and `version`),
  2. Monograph header (`<div align="center">YYYY-MM-DD</div>` and `<div align="center">Version 1.0.0</div>`),
  3. Package `README.md` (`**Date:** YYYY-MM-DD` and `**Version:** 1.0.0`), and
  4. The deterministic release ZIP filename (`<slug>_YYYY-MM-DD.zip`).
- **Retirement of Claim Ledgers & Landau Quizzes**:
  Claim ledgers (`*_claim_ledger.md`, `claim_ir.yaml`, `claim_code_map.yaml`, `lean_claim_map.md`) are discontinued from paper packages and release verification gates. Lev Landau quizzes (`_lev_landau_theoretical_minimum_quiz/`, `landau_quiz.md`) must never be added to paper packages unless the user personally and explicitly adds them.
- **Lowercase Filenames Discipline**: Use lowercase letters only in filenames that are not `README.md` files (e.g. monographs, documentation, scripts, and reports must be strictly lowercase).

---

## 8. Interactive Notebook Output Persistence & Cross-Host Sync

- **Notebook Replay State (`F02`, Stage 4)**: Deposited Jupyter notebooks must have non-null `execution_count`s and populated output cells; headless replays (`nbclient`) must save executed outputs back to the `.ipynb` file.
- **Atomic Cross-Host Parity (`AutoP Stage 2`)**: Any edit to skills, references, or rule files must be immediately synchronized across all four active host roots (`.agents/`, `.claude/`, `.codex/`, `.grok/`) using `sync_cross_host_skills.py` to ensure byte-level index parity.

---

## 9. Front-Matter Semantic Parity Invariant (`RULE_FRONT_MATTER_SEMANTIC_PARITY_001`)

- **Field Role Preservation:** Rendered front matter must preserve each named source field in its intended role. A missing subtitle must not silently fall back to repeating the title.
- **Verification Check:** Compare the first-page title block with the parsed source metadata: require one title and the exact subtitle. Include first-page visual inspection to catch duplication that text-presence checks alone miss.
