# Detailed definition: Review Evidence Reproducibility (1)

**AuthorityEffect:** None.

Parent: [Review Evidence Reproducibility](../../../../../rules/claims/rl_review_evidence_reproducibility.md). Load for the matching predicate, not every task.

# Review Evidence Reproducibility Rule

**AuthorityEffect:** None.

Every PASS or FAIL verdict in a review report, CI receipt, or audit artifact
must carry the following four fields:

1. **Exact command** — the literal command line executed
2. **Tool version** — the version string of the tool (e.g., `ruff 0.14.13`, `pytest 8.3.5`)
3. **Exit status** — the process exit code
4. **Tested scope** — which files, rules, or configurations were in effect

A verdict without these four fields is NOT reproducible evidence and must
not be cited as a PASS. This applies to ruff, mypy, pytest, Lean lake build,
nbclient replay, and any other tool-based gate.

When tool defaults are version-dependent (e.g., ruff rule selection),
the project configuration (`pyproject.toml`, `lakefile.lean`, etc.) must
pin the selection explicitly so the result is deterministic across versions.

---

## Zero Fallback Digest & Fail-Closed Receipt Invariant

> **Cryptographic Witness & Receipt Generation Integrity:**
>
> 1. **Zero Hardcoded or Simulated Fallback Hashes:** Receipt generators, cryptographic commitment routines, and CI evidence builders must NEVER emit hardcoded, mocked, or fallback hash strings when input files, proof kernels, or build artifacts are missing. Missing prerequisites must immediately raise `FileNotFoundError` or return a typed operational refusal.
> 2. **Hermetic Receipt Test Isolation & Negative Controls:** Test suites verifying receipts must construct isolated run directories via `tmp_path` rather than depending on uncommitted working paths, and MUST include negative controls verifying that missing or tampered bundle files fail closed.

---

## Release Summary & Reference Verification Invariant (`RULE_RELEASE_SUMMARY_AND_REFERENCE_PARITY_001`)

> **Release Summary Identity Binding & Primary Literature Verification:**
>
> 1. **Release Receipt Identity Binding:**
>    Validation summaries in package READMEs and release documentation must be bound directly to a dated validation receipt recording exact test counts, statement coverage, environment, and skipped checks for the current payload. Historical review results must be explicitly labeled with their historical date and preserved as baselines rather than overwritten.
> 2. **Primary Record Reference Verification:**
>    Every bibliographic entry and DOI must be verified against its primary publisher record (matching article title, authors, year, journal, volume, and article number) prior to release. Titles must never be reconstructed from topical memory or subject matter.

---

## Fail-Closed Verifier Execution Invariant

> **Hermetic Failure Propagation:**
>
> 1. **No Silent Pass on Missing Dependencies:**
>    Verification scripts (`verify_deposit.py`, census checkers, and test harnesses) must fail closed with a non-zero exit code (`sys.exit(1)`) whenever an import fails or a required schema validator is missing. Catching `ImportError` or `Exception` and silently proceeding with `pass` is strictly prohibited.
> 2. **Explicit Opt-Out Flags:**
>    Any permissive behavior (such as skipping header validation when tools are absent) must require an explicit, intentional command-line flag (e.g., `--skip-header-schema`).

---

## Cross-References

- Branch-diff audit scope and forbidden words in touched files: [`../git/rl_pr_scope_and_branch_diff_audit.md`](../../../../../rules/git/rl_pr_scope_and_branch_diff_audit.md).
- PFP demo round anatomy and `live_runs/` integrity: [`../education/rl_pfp_demo_round_anatomy.md`](../../../../../rules/education/rl_pfp_demo_round_anatomy.md).
