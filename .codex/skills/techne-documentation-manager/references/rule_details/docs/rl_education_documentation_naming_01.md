# Detailed definition: Education Documentation Naming (1)

**AuthorityEffect:** None.

Parent: [Education Documentation Naming](../../../../../rules/docs/rl_education_documentation_naming.md). Load for the matching predicate, not every task.

# Education Documentation Naming Convention

**AuthorityEffect:** None.

## Snake_case Filenames (No Kebab-case)

All Markdown, YAML, JSON, and Python files under `education/` must use snake_case filenames.

- **Correct:** `wire_and_canonicalization.md`, `functional_metric_ownership.md`
- **Incorrect:** `wire-and-canonicalization.md`, `functional-metric-ownership.md`

Exception: `README.md` (conventional uppercase).

## Numbered Prefix Directories under PFP

Top-level content directories under `.../004_oepfp/` follow a numbered prefix convention:

| Prefix | Directory |
|:---|:---|
| `4_` | `4_symbol_game_packets` |
| `5_` | `5_symbol_game_levels` |
| `6_` | `6_symbol_game_normal_forms` |

New content directories at this level must be assigned the next available number and prefixed accordingly.

Directories that are infrastructure (`_archive/`, `_images/`, `tests/`, `notebook_lib/`, `lessons/`, `reference/`, `fsp/`, `runtime/`, `examples/`, `pfp/`) do not take numbered prefixes.

## Curriculum Lesson Estate 4-Directory Layout Invariant (`RULE_CURRICULUM_4DIR_001`)

All numbered track directories under `education/curriculum/004_oepfp/NNN_*/` (and across all curriculum strands) must strictly adhere to the 4-directory structure:

1. **Directory Structure:**
   - `concepts/`: Textbook markdown concept documents (`lesson_NNN_XX_*.md`).
   - `notebooks/`: Executable Jupyter notebooks (`lesson_NNN_XX_*.ipynb`).
   - `scripts/`: Video lecture transcript/scripts (`lesson_NNN_XX_*.md`).
   - `videos/`: Video media clips and `.gitkeep`.

2. **File Naming & Parity:**
   - Every lesson slug `lesson_NNN_XX_<name>` must exist across all four directories with matching basenames.
   - All files must be pure UTF-8 without BOM and follow snake_case naming.

## Top-Level Documentation Numbered Tracks

High-level documentation and project tracks under `education/documentation/` follow defined series ranges:
- `000_` to `009_`: Foundational mathematics, S(n) discrete manifolds, Genesis, and PFP.
- `100_` to `199_`: Operational infrastructure and cognitive operations (e.g. `160_cognitive_operations/`).
- `200_` to `299_`: Autopoietic self-reasoning engines and advanced research systems (e.g. `200_project_sentinel_codename_adversary_autop_reasoning_engine/`).

## Package Renaming & Subsystem Relocation Protocol (`RULE_PACKAGE_RENAME_SYNC_001`)

Whenever renaming or relocating a documentation or package directory:
1. **Atomic Git Relocation:** Execute `git mv <source> <target>` so git commit history and tracking remain unified without leaving untracked duplicates or ghost directories on disk.
2. **Root Metadata Parity & Backward Aliases:** Immediately update the target directory's root `README.md` frontmatter `title`, `#` title heading, and description. Retain the legacy folder name in the `aliases:` YAML frontmatter array to preserve search indexing, automated routing, and external cross-reference integrity.
3. **Nested Relocation Depth Traversal:** When moving a package into a parent directory (increasing nesting depth), audit all relative markdown links and contract references within the relocated tree. Increment path traversal depth accordingly (e.g., convert `../../` references to `../../../` when referencing sister documentation trees).
4. **Shared Grammar & Tool Resolution Chains:** Inspect standalone checker scripts (`check_*.py`) and test suites (`test_*.py`) for dynamic imports or fallback search paths resolving shared assets (e.g., `check_grammars.py` in `004_oepfp/grammar/`). Update paths to target canonical locations and verify with live test runs.
5. **Strand Verifier & Contract Alignment:** Synchronize canonical directory mappings in test and application adapters (`education/education_app/use_cases/strands/verify_strands.py` and `strand_verifier_adapter.py`) including legacy alias fallbacks, and align references in affected normal form contracts (`nf.*.yaml`).
6. **Four-Host Gate Script Parity & Shape Certification:** If gate scripts (such as `check_lesson_folders.py`) require updated prefix patterns or directory rules, apply changes synchronously across all four host mirror directories (`.agents/`, `.claude/`, `.codex/`, `.grok/`). Execute `check_lesson_folders.py` to verify 0 shape failures and 0 open learning checks, followed by targeted pytest suites across affected modules.

## Sentinel File Protection & Dynamic Root Resolution (`RULE_EDUCATION_ROOT_SENTINEL_001`)

1. **Sentinel Invariant:** Scripts or files whose paths are embedded in curriculum notebooks as `ROOT` discovery sentinels (e.g. `build_system_integration.py`) must never be deleted unless all consuming notebooks are migrated to standard anchors (`curriculum_manifest.yaml` or `.git`).
2. **Three-Digit Prefix Standardization:** Resolvers searching `education/documentation/` MUST prioritize canonical three-digit module folders (e.g., `004_oepfp`, `001_oegen`, `002_oesn`) over legacy unpadded equivalents (e.g., `3_the_symbol_game_proposal_fidelity_protocol_pfp`, `2_genesis`).
3. **PFP Domain vs YAML Placement:** PFP domain Pydantic schemas must reside in `pfp/domain/` with zero host I/O; serialized manifests, prompts, and fixtures must reside in `pfp/infrastructure/yaml_data/`.

## Notebook & Markdown Dual-Text Parity Invariant (`RULE_NOTEBOOK_MARKDOWN_DUAL_TEXT_PARITY_001`)

> **Curriculum Dual-Text Synchronization & Media Grounding:**
>
> 1. **Dual-Text Synchronization:** In curriculum lessons where concept markdown pages (`concepts/lesson_*.md`) duplicate teaching narrative from Jupyter notebooks (`notebooks/lesson_*.ipynb`), modifications to notebook explanatory cells require updating or regenerating the companion markdown page in the same edit. Disjoint drift between notebook content and textbook markdown is forbidden.
> 2. **Empty Media Slot Grounding:** An empty `videos/` directory containing only `.gitkeep` constitutes an unpopulated media slot, not evidence of audiovisual delivery. Claims of pedagogical multimodal completeness must not be asserted until actual video clips are present.
> 3. **Automated Enforcement:** Verified via sovereign entrypoint `education/scripts/verify_dual_text_parity.py::verify_dual_text_parity` scanning all companion pairs across `education/**/curriculum/` for 100% dual-text consistency.
