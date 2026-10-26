# Detailed definition: Paper Deposit Verifier Attestation & Path Fences (1)

**AuthorityEffect:** None.

Parent: [Paper Deposit Verifier Attestation & Path Fences](../../../../../rules/papers/rl_paper_deposit_verifier_attestation_and_path_fences.md). Load for the matching predicate, not every task.

# Rule: Paper Deposit Verifier Attestation & Path Fences

**AuthorityEffect:** None.

This rule codifies cross-component path case collision fences, historical defect archive preservation, lowercase filename discipline, prohibition of calendar dates in deliverable filenames, exact deposit custody counts, packaged receipt path sanitization, Win32 MAX_PATH depth fences, and deposit verifier attestation honesty. Cross-reference paper mechanization invariants: [`rl_research_paper_and_monograph_packaging.md`](../../../../../rules/papers/rl_research_paper_and_monograph_packaging.md) and release envelope specifications: [`rl_paper_deposit_release_envelope_and_manifest_fences.md`](../../../../../rules/papers/rl_paper_deposit_release_envelope_and_manifest_fences.md).

---

## Deposit Path Cross-Component Case Collision & Archive Preservation Invariant

> **Packaging Path Fences & Historical Counterexample Integrity:**
>
> 1. **Cross-Component Path Case Collision Fences:**
>    - Deposit walkers (`walk_files`) and manifest parsers (`read_manifest`) must track seen files and ancestor directory components, failing closed (`ValueError` with `"case-colliding"`) against file-vs-directory clashes (`Asset` alongside `asset/child`) and directory casing conflicts (`Dir/a` vs `dir/b`) on case-insensitive filesystems.
> 2. **Historical Defect Archive Preservation Discipline:**
>    - When applying discipline fixes, historical defect archives (e.g. `docs/source_archive/*.py.txt`) used by regression and counterexample audits (e.g. `audit_legacy_embedding.py`) must remain permanently intact. Bug remediations apply strictly to active, maintained production copies.
> 3. **Lowercase Filenames Discipline (Except README.md):**
>    - All files across research packages, monographs, atlas libraries, and documentation must strictly use lowercase letters in filenames (`[a-z0-9_.-]+`). The only permitted uppercase filename is `README.md` (and standard `LICENSE` files). Never create or retain uppercase filenames (such as `ATLAS.md` or `*_REPORT.md`).
> 4. **Zero Calendar Dates in Active Deliverable & Manuscript Filenames (`RULE_NO_CALENDAR_DATES_IN_FILENAMES_001`):**
>    - Filenames must never embed calendar date stamps (e.g., `YYYYMMDD`, `YYYY-MM-DD`, `YYYY_MM_DD`, `YYYYMM`).
>    - Deliverables, manuscripts, sections, derivations, checkpoints, prompts, notes, and deposit files must use stable, semantic, content-based names (e.g., `mub6_master_derivation.tex`, `mub6_executive_checkpoint.md`, `subproblem_02_section.tex`).
>    - Chronological sequencing, if required, must be recorded strictly inside internal version metadata, git history, or dedicated append-only change logs (`<slug>_change_log.md`), never in the filesystem pathname.

---

## Deposit Custody Counts Exact Equality Invariant

> **Strict Archive Membership Accounting:**
>
> 1. **Exact Equality vs. Floor Assertions:**
>    Test suites verifying release archive members (e.g. `tests/test_zenodo_release_archive.py`) must assert exact integer equality between actual archive member counts and the authoritative `custody_counts` declared in `release_manifest.json` (`len(members) == custody_counts["archive_members"]`).
> 2. **Prohibition of Loose Inequality Bounds:**
>    Using loose floor assertions (such as `>= 477` or `>= 474`) in custody verifiers is prohibited; loose floors mask accidental file omission, deletion, or unintended file inclusion.

---

## Packaged Receipt Path Sanitization Invariant

> **Hermetic Receipt Environment Isolation:**
>
> 1. **No Absolute Host Paths in Packaged Receipts:**
>    Check receipts, verification manifests, and test outputs packaged inside deposits (e.g. `artifacts/*.json`) must use relative repository paths or standard placeholders (`<repo>/...`), strictly prohibiting absolute local host paths (`C:\Users\...`, `/home/...`, `.codex/worktrees/...`).
> 2. **Portable Path Normalization:**
>    Path fields in serialized receipts and test artifacts must be normalized to forward slashes without host-specific usernames, home directories, or worktree identifiers.

---

## Windows MAX_PATH Depth Fence & Short Slug Invariant (`RULE_WIN32_MAX_PATH_AND_SHORT_SLUG_DISCIPLINE_001`)

> **Path Length and Redundant Nested Slug Prevention:**
>
> 1. **250-Character Hard Path Ceiling:** No path in a research paper package or deposit may exceed 250 characters on standard checkouts. Repository tools must verify package-relative and repo-relative paths against Win32 MAX_PATH limits.
> 2. **Prohibition of Duplicate Long-Named File Stems:** Never repeat a long package directory name as a full filename inside that directory (e.g. `path/to/<89-char-slug>/<89-char-slug>.md`). Packages must use a concise canonical stem (e.g. `covering_edge_descent.md`, `covering_edge_descent.zip`) to prevent path length overflow on Windows systems.
> 3. **Clean Metadata Authority Framing:** Zenodo deposit metadata must declare `Authority status: None.` rather than internal programmatic token strings like `AuthorityEffect: None.`.

---

## Deposit Verifier Attestation Honesty & Strict Test Outcome Census Invariant (`RULE_PAPER_VERIFIER_ATTESTATION_HONESTY_001`)

> **Verifier Attestation Honesty & Strict Test Outcome Census:**
>
> 1. **Archive Attestation Honesty:**
>    - Deposit verification scripts (e.g. `verify_deposit.py`) must never emit an archive-qualified verification verdict (`"selected archive, Python tests and scoped replay verified"`) unless both an explicit release ZIP archive and its matching `.zip.sha256` sidecar have been verified byte-for-byte against the canonical repository envelope.
>    - When executing against the unbundled repository tree without verifying an archive, the verifier must explicitly output that archive verification was NOT performed (e.g. `"PASS (...): repository payload, Python tests and scoped replay verified (archive verification NOT performed)"`).
>    - Verification CLI runners must support a fail-closed option (e.g. `--require-archive`) that raises an immediate error if a release archive is absent or corrupted.
>
> 2. **Strict Test Profile Outcome Census:**
>    - Verifier test runners evaluating strict deposit/release profiles must pass `--runxfail` to pytest so expected failures are not masked.
>    - The verifier must scan the test runner output and reject any suite that reports `skipped`, `xfailed`, or `xpassed` tests, requiring at least one passed test.
>    - Deselected tests corresponding to unrequested native integration tiers must be reported as explicit deselections, never converted into passing assertions.
>
> 3. **Receipt and Build Transient Snapshot Parity:**
>    - Deposit manifests and readiness receipts (e.g. `TEST_READY.md`) must bind the exact tested git commit digest, toolchain versions, outcome counts, and output page counts matching the compiled manuscript build logs (with 0 missing glyphs). Stale compilation logs or historical test counts must not be packaged without their matching artifact snapshots.
