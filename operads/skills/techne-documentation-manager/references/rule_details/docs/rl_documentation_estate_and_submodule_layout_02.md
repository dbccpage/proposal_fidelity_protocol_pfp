# Detailed definition: Documentation Estate & Submodule Layout (2)

**AuthorityEffect:** None.

Parent: [Documentation Estate & Submodule Layout](../../../../../rules/docs/rl_documentation_estate_and_submodule_layout.md). Load for the matching predicate, not every task.

## 5. Internal Markdown Link Relativity Invariant (`RULE_INTERNAL_MARKDOWN_LINK_RELATIVITY_001`)

> **Strict Relative Path Discipline in Repository Markdown:**
>
> 1. **Relative POSIX Paths Only:** All hyperlinks between documentation, contract, and code files committed to the repository must strictly use relative POSIX paths (e.g., `../levels/level_01_symbol_genesis.md`, `../../grammar/mssn.ebnf`).
> 2. **Prohibition of Host-Absolute `file:///` URLs:** Committing host-absolute URLs (`file:///c:/Users/...` or `file:///home/...`) into tracked repository markdown or YAML files is strictly forbidden. Host-absolute paths fail across worktrees, break CI link validation tools, and leak local paths.
> 3. **Assistant Chat vs. Repository File Demarcation:** The instruction to provide clickable `file:///` links applies exclusively to conversational responses rendered in the user interface. It must NEVER be applied to repository files.
> 4. **Monograph Package Subdirectory Depth Rule:** When editing documents inside a monograph package (`papers/NNN_<slug>/`), agents must account for package depth:
>    - Sibling files in same module: use `../../<pillar>/...` (e.g., `../../grammar/mssn.ebnf`, `../../README.md`).
>    - Peer paper packages in same module: use `../<peer_package>/paper.md` (e.g., `../000_mssn/paper.md`).
>    - Other documentation strands: use `../../../<strand>/...` (e.g., `../../../000_pre_genesis/README.md`).
>    - Never emit bare strand-relative paths from nested paper packages.
> 5. **Code-to-Markdown Export Disambiguation:** When exporting source code files into `.md` formats:
>    - Use compound extensions (`{basename}.{ext}.md`) to preserve original source language identification.
>    - Subdirectory hierarchies (`bin/`, submodules) must be strictly preserved to prevent collision overwrites.
> 6. **Automated Documentation & Session Summary Hygiene:**
>    - Autonomous agents and telemetry scripts generating session summaries (`_ic/nro/documentation/sessions/`, `.agents/documentation/sessions/`), catalogs, or reports must NEVER commit `file:///` URLs or host-specific user directory paths (`C:/Users/...` or `/home/...`).
>    - The repository root must be recorded as `.` or a relative root identifier, and all touched artifact links must strictly use repository-relative POSIX paths.
>    - Session logs must ignore prior session summaries and bound displayed touched lists to at most 100 entries (`HP_MD_055`) to prevent runaway markdown file bloat.
> 7. **Linter and Script Constant Cleanliness:**
>    - Python, Rust, and shell scripts within the repository must never define string constants containing host-absolute filesystem paths or `file:///` prefixes.
>    - Directory derivations must be computed dynamically relative to `Path(__file__).resolve()` or runtime configuration arguments.

---

## 6. Single Selected Revision Snapshot Invariant (`RULE_DOCS_SINGLE_REVISION_SNAPSHOT_001`)

> **Architecture Artifact Synchronization Discipline:**
>
> 1. **Single Governing Snapshot:** Every generated architecture review document, dashboard, YAML inventory, and graph census must bind its active measurements to a single explicitly declared Git revision hash.
> 2. **Prohibition of Multi-Revision Header/Footer Drift:** A document header, cards section, finding tables, and footer must never reference competing revision hashes as the "current" or "pinned" revision.
> 3. **Immutable History Demarcation:** Measurements from prior passes (e.g. earlier exploratory scans) must be strictly demarcated as immutable historical records with their original revision and date, and must not be mixed into current projection totals without reconciliation.
