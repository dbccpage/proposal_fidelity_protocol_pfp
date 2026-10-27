# Detailed definition: Paper Harmonization & Provenance Discipline (1)

**AuthorityEffect:** None.

Parent: [Paper Harmonization & Provenance Discipline](../../../../../rules/papers/rl_paper_harmonization_and_provenance_discipline.md). Load for the matching predicate, not every task.

# Rule: Paper Harmonization, Notebook Determinism & Execution Provenance Discipline

**AuthorityEffect:** None.

This rule codifies canonical paper template harmonization pipelines, companion notebook determinism, demo failure propagation, native CLI input strictness, and custody manifest reconciliation.

---

## Research Paper Template & Harmonization Pipeline Invariant

> **Standardized Paper Packaging & Harmonization Discipline:**
>
> 1. **Zero Ad-Hoc Paper Release Tooling:** All research paper and preprint packages under `atlas/coda_atlas/` and `core_research/programs/` must adhere to the canonical template (`atlas/coda_atlas/_kits/paper_template/`). Hand-crafted release scripts with hardcoded file lists are strictly prohibited.
> 2. **Dynamic Deposit Discovery & Two-Way Sweeps:** Deposit packaging and verification tools (`verify_deposit.py`, `rebuild_release.py`) must dynamically discover files via `deposit_paths.py` and enforce bidirectional reconciliation with `MANIFEST.sha256`.
> 3. **Mandatory Pre-Review Harmonization:** Before triggering `/adversary --swarm-type research-paper` or referee gates, agents and authors must execute `paper_edition.cli rebuild` to synchronize derived artifacts (figures, checksums, axiom censuses, zip archives). Review harnesses must support `--auto-rebuild` to repair derived artifact drift automatically.
> 4. **Deterministic Zip Packaging:** Name each active deposit archive for its actual release date and set every ZIP member's DOS timestamp to that same date at 12:00:00, with UNIX host attributes (`create_system = 3`). Never freeze a past release date in a script. Synchronize the manuscript, CFF, metadata, filename, and checksums after a date or version change.
> 5. **Lean 4 Axiom Totality:** Packages containing formal Lean 4 developments must generate a synthetic `Census.lean` covering all declarations, asserting adherence to the standard axiom whitelist (`propext`, `Quot.sound`, `Classical.choice`).
> 6. **Retirement of Claim Ledgers & Examiner Quizzes:**
>    - Claim ledgers (`*_claim_ledger.md`, `claim_ir.yaml`, `claim_code_map.yaml`, `lean_claim_map.md`) are discontinued from paper packages and release verification gates.
>    - Examiner quizzes (`_lev_examiner_theoretical_minimum_quiz/`, `examiner_quiz.md`) must never be added to paper packages unless the user personally and explicitly adds them. Where an authorized educational quiz companion is maintained, empty directory tracking must use `.gitkeep` (which is included in `EXCLUDED_NAMES` in `verify_deposit.py`), and any retained external directory must be declared in `EXCLUDED_DIRS`.
> 7. **Markdown MD004, MD034 & MD035 Formatting Discipline (Zero Horizontal Rules):**
>    - **Zero Horizontal Rules (MD035 Prohibited):** Standalone horizontal rules or decorative divider lines (`---`, `***`, `___`, or repeated dashes `-------------------`) are strictly prohibited in all Markdown files. Never frame headings or divide sections with horizontal rules.
>    - **Clean ATX Headings Exclusively:** All titles, sections, and subsections must use standard ATX heading syntax (`# Title`, `## Section`, `### Subsection`) separated by single blank lines. Setext-style underlines (`===`, `---`) are strictly prohibited.
>    - **MD004 & MD034 Compliance:** Unordered list items must use dash markers (`-`), not asterisks (`*`). All URLs must be formatted as proper Markdown links (`[label](https://example.com)`), never bare URLs.
>    - **Zero Suppression:** Disabling, suppressing, or ignoring markdownlint rules (via HTML comments such as `<!-- markdownlint-disable ... -->` or configuration files) is prohibited. All linter warnings must be resolved by fixing the Markdown sources directly on disk.

---

## Companion Notebook Determinism & Channel F Invariant

> **Deterministic Headless Replay & Payload Protection:**
>
> 1. **Deterministic Exact Arithmetic:** Companion notebooks (`jupyter_notebooks/*.ipynb`) must use exact rational arithmetic (`Fraction`) or deterministic discrete algorithms; unseeded randomness and volatile timestamps are prohibited.
> 2. **Dual-CWD Portability:** Notebook setup cells must resolve the package `code/` module correctly whether executed from the package root or `jupyter_notebooks/`.
> 3. **Clean Ephemeral Replay:** Headless execution (`nbclient`) must execute via isolated ephemeral kernels and reproduce deposited cell output streams bit-for-bit without writing unmanifested files into the release payload.

---

## Demo Failure Propagation & Non-Zero Exit Invariant

> **Demonstration Execution & Negative Control Integrity:**
>
> 1. **Fail-Closed Demo Outlines:**
>    Demonstration scripts (`demo*.py`) and unified runners (`run_demos.py`) must propagate all verification failures, type mismatches, and negative control bypasses as boolean `False` returns and non-zero process exits (`sys.exit(1)`).
> 2. **No Success Reporting on Failure:**
>    Demonstrations must never print "FAIL" or "REFUSED" and subsequently announce "Completed Successfully" or exit `0`.
> 3. **Explicit Runtime Checks over Bare Asserts:**
>    Runtime invariant guards in demonstrations must use explicit `if not condition: return False` checks rather than bare `assert` statements, preventing silent pass-through under optimized execution (`python -O`).
> 4. **Live vs. Mock Execution Disentanglement:**
>    Live demonstrations must distinguish execution success from proposal certification; offline mock runs triggered by missing API keys must be labeled and returned as mock runs, not live experiment passes.

---

## Native CLI Input Strictness & Zero-Default Fallback Invariant

> **Hermetic CLI Contracts:**
>
> 1. **Strict Operation Mode Validation:**
>    Native solver and verifier command-line executables must strictly validate operation modes and reject unknown or misspelled modes with structured error payloads (`status: "ERROR"`).
> 2. **Zero-Default Input Fallback:**
>    Native CLI contracts must distinguish omitted inputs from explicitly empty arrays; omitted graph or matrix fields must NEVER default to empty graphs via `unwrap_or_default()`.
> 3. **Single Representation Enforcement:**
>    Native CLI contracts must require exactly one input representation (e.g., explicit graph vs. matrix vs. integer matrix); ambiguous payloads supplying multiple representations must be rejected.

---

## Provenance Record Reconciliation & Historical Integrity Invariant

> **Custody Manifest Continuity:**
>
> 1. **Preserve Upstream Baselines:**
>    When code or test files are repaired post-capture, `PROVENANCE.md` must preserve the original upstream capture hashes and dates, while recording the verified current file hashes in a separate column.
> 2. **Explicit Change Reconciliation:**
>    Updates to current hashes must include an explicit dated reconciliation entry documenting the intervening change reason.
> 3. **Non-Retroactive Execution Claims:**
>    Historical verification counts (e.g., 18/18 or 19/19 tests) must remain bound to their historical dates and must not be retroactively claimed as passes over modified bytes.

---

## Reproduction Machinery vs. Execution Receipt Demarcation Invariant

> **Script vs. Receipt Separation:**
>
> 1. **Reproduction Script Demarcation:**
>    Manuscripts, documentation, and README files must never describe executable scripts (e.g. `verify_deposit.py`) as "verification reports" or "fresh checks" unless referencing a dated, signed execution receipt emitted during release.
> 2. **Machinery vs. Artifact Distinction:**
>    Reproduction scripts must be explicitly documented as reproduction machinery.

---

## Deposit Rebuild & Verification Manifest Exclusion Parity Invariant

> **Strict Exclusion Set Parity:**
>
> 1. **Identical Exclusion Registers:**
>    Release packaging tools (`rebuild_release.py`, `build_deposit_zip.py`) and verification gates (`verify_deposit.py`) must maintain bit-level identical `EXCLUDED_DIRS` sets. Specifically, compiler target directories (`target/`, `.lake/`, `dist/`, `build/`) must be excluded identically across all release-rebuild and deposit-audit tools.
> 2. **Clean-Tree Release Assertion:**
>    Release archives and checksum manifests must never capture intermediate compiler artifacts (`.rlib`, `.d`, `.exe`, `.rmeta`, lockfiles).

---
