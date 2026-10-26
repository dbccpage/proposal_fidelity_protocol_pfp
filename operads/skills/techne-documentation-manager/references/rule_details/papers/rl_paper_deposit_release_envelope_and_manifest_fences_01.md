# Detailed definition: Paper Deposit Release Envelope & Manifest Fences (1)

**AuthorityEffect:** None.

Parent: [Paper Deposit Release Envelope & Manifest Fences](../../../../../rules/papers/rl_paper_deposit_release_envelope_and_manifest_fences.md). Load for the matching predicate, not every task.

# Rule: Paper Deposit Release Envelope & Checksum Manifest Fences

**AuthorityEffect:** None.

This rule codifies two-tier checksum manifest parity, release archive root laws, line-ending checksum stability, Zenodo metadata schema integrity, non-vacuous documentation bundles, atomic source-bound release export, declaration-set axiom census, and multi-component license declaration consistency. Cross-reference paper mechanization invariants: [`rl_research_paper_and_monograph_packaging.md`](../../../../../rules/papers/rl_research_paper_and_monograph_packaging.md) and publication specifications: [`rl_coda_publication_and_monograph_specifications.md`](../../../../../rules/papers/rl_coda_publication_and_monograph_specifications.md). For path length, slug, filename date, and verifier attestation fences, see [`rl_paper_deposit_verifier_attestation_and_path_fences.md`](../../../../../rules/papers/rl_paper_deposit_verifier_attestation_and_path_fences.md).

---

## Two-Tier Release Manifest & Archive Root Invariant

> **Two-Tier Checksum Integrity & Archive Structure:**
>
> 1. **Two-Tier Release Manifest Law:** `MANIFEST.sha256` strictly lists release payload files; `SHA256SUMS` lists payload plus `MANIFEST.sha256` and its digest (both sorted in ordinal UTF-8 byte order).
> 2. **Archive Root Prefix & Permissions:** Release ZIPs must contain strictly the files declared in `SHA256SUMS` (including `docs/descriptions.md` if present) under package root or a single root prefix (`{slug}/{member}`, Unix regular file mode `0o100644`). Unmanaged root PDFs or undeclared scratch files are strictly forbidden. Mypy checks must pass with 0 issues across `code/` via scoped overrides, never global `ignore_missing_imports = true`.
> 3. **Topological Build & PDF Staleness Prohibition:** Release archives must never be built while the rendered PDF is stale relative to TeX/Markdown source; modifications to frontmatter, dates, versions, or scopes must re-compile immediately.

---

## Multi-Component License Declaration Mapping Invariant

> **Comprehensive Package Component Licensing:**
>
> 1. **Component-Level License Mapping:**
>    Package documentation (`README.md`) and metadata (`zenodo_metadata.json`) must explicitly declare licensing for each package component: manuscript text (e.g., CC-BY-4.0), software/verification code (e.g., MIT or Apache-2.0), and data/receipt assets.
> 2. **Dual-License Consistency:**
>    When software and prose carry distinct licenses, both licenses must be present in the repository root or documented in the package license matrix, with zero ambiguity as to which license applies to code versus prose.

---

## Deposit Line-Ending Checksum Stability Invariant (`RULE_DEPOSIT_LINE_ENDING_CHECKSUM_STABILITY_001`)

> **Deterministic Cross-Platform Manifest Checksums:**
>
> 1. **LF Line-Ending Normalization:** All text files, scripts (`.sh`, `.bat`, `.py`), and JSON/YAML metadata in release packages must have line endings normalized to LF before computing cryptographic checksums (`SHA256SUMS`, `MANIFEST.sha256`).
> 2. **Automated Manifest Check Gate:** Verifiers must execute `python scripts/regen_sha256sums.py --check` and verify byte-for-byte fidelity across operating systems without silent CRLF mutation.

---

## Zenodo Related Identifier Integrity Invariant (`RULE_ZENODO_RELATED_IDENTIFIER_INTEGRITY_001`)

> **Strict Schema for External & Parent Identifiers:**
>
> 1. **Mandatory Identifier Field:** Every object in `zenodo_metadata.json` under `related_identifiers` must define a non-empty `identifier` field, together with valid `relation`, `resource_type`, and `scheme`.
> 2. **Fail-Closed Validation:** `verify_deposit.py` must reject any entry lacking `identifier` with exit code 1.

---

## Paper Documentation Bundle Invariant (`RULE_PAPER_DOCS_BUNDLE_NON_VACUOUS_001`)

> **Non-Vacuous Release Documentation:**
>
> 1. **Mandatory Documentation Quartet:** Every research deposit under `coda_atlas/` must furnish non-stub documentation in `docs/`: `descriptions.md` (full abstract, theorems, and boundaries), `references.md` (complete bibliography), `keywords.md` (canonical indexing terms), and `quick_start.md` (actionable reproduction commands).
> 2. **Stub Rejection Threshold:** Files in `docs/` under 100 bytes or containing only file stem placeholders are strictly prohibited and fail deposit verification.

---

## Atomic Source-Bound Release Export Invariant (`RULE_ATOMIC_SOURCE_BOUND_RELEASE_EXPORT_001`)

> **Atomic Source-Bound Release Export Law:**
>
> 1. **Frozen Staging Tree Export:** A release must be exported from one frozen staging tree. Corresponding loose and archived members must be byte-identical, every source binding must match the delivered source, and the delivered renderer must accept that source. Any subsequent edit invalidates the release checks.
> 2. **Release Export Verification Check:**
>    - Compare every loose attachment with its corresponding ZIP member.
>    - Verify both checksum manifests (`MANIFEST.sha256` and `SHA256SUMS`).
>    - Compare the TeX manuscript digest with the delivered Markdown.
>    - Exercise the bundled renderer's metadata and body extraction on that exact Markdown before permitting export.

---

## Declaration-Set-Bound Axiom Census Invariant (`RULE_DECLARATION_SET_BOUND_AXIOM_CENSUS_001`)

> **Declaration-Set-Bound Axiom Census Law:**
>
> 1. **Exact Declaration-Set Gate:** A current axiom gate must compare the exact requested declaration names with the exact reported names and bind the result to source hashes, target and toolchain. A historical count must not control an expanded current target.
> 2. **Verification Check:**
>    - Extract the target's `#print axioms` declarations and compare their set with the receipt's declaration set.
>    - Reject missing, extra or duplicate reports and stale source bindings.
>    - Retain historical receipts outside the current comparison (e.g. `historical_axiom_report_*.txt`).

---

## Dual License & Formal Axiom Report Deposit Invariants (`RULE_DEPOSIT_CODE_LICENSE_AND_AXIOM_REPORT_001`)

> **Code License & Formal Axiom Census Artifact Packaging:**
>
> 1. **Dual Code License Law:**
>    Deposits containing executable Python, Rust, or Lean code must supply `LICENSE-CODE` (governing software under `code/`, `scripts/`, and `lean4/`) alongside the text manuscript `LICENSE`.
> 2. **Compiled Axiom Report Artifact:**
>    Deposits with Lean 4 formalizations must include `lean4/axiom_report.txt` documenting all admitted axioms across mechanized modules, confirming zero custom axioms or unverified `sorry` dependencies before republication packaging.
