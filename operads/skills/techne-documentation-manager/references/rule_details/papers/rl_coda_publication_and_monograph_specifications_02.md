# Detailed definition: CODA Publication & Monograph Specifications (2)

**AuthorityEffect:** None.

Parent: [CODA Publication & Monograph Specifications](../../../../../rules/papers/rl_coda_publication_and_monograph_specifications.md). Load for the matching predicate, not every task.

## 7. Deposit Payload Separation & External Target Fences (`RULE_DEPOSIT_PAYLOAD_SEPARATION_001`)

> **Package Boundary Discipline & Deposition Formatting Helpers:**
>
> 1. **Payload Demarcation:**
>    - Deposit abstract, why-care, and non-claims belong exclusively in `docs/descriptions.md`.
>    - Deposit keywords belong exclusively in `docs/keywords.md`.
>    - The monograph manuscript (`<paper_slug>.md`) must never contain `## Appendix: Zenodo Description` or trailing `**Keywords:**` lists.
> 2. **External Deposition Targets are External Clipboard Helpers Only:**
>    Formatting instructions for `ZENODO-HTML`, `ZENODO-TEXT`, and `MO` (MathOverflow) in `obstruction_paper_kit/description_formatting_zenodo_mo.md` are external helpers for manual browser paste operations. They must never be saved into repository files.
> 3. **Zenodo HTML Sanitization Allowlist:**
>    When preparing external Zenodo HTML clipboard text, strictly restrict markup to allowlisted tags:
>    `a, abbr, acronym, b, blockquote, br, caption, code, div, em, i, li, ol, p, pre, span, strike, strong, sub, table, tbody, thead, th, td, tr, u, ul`.
>    Notice: `<sup>` is prohibited by Zenodo (use Unicode superscripts); `<h1>`–`<h6>` are prohibited (use `<p><strong>Heading.</strong></p>`); `<img>` is prohibited.
> 4. **Verbatim Non-Claims Preservation:**
>    When converting descriptions for external platforms, non-claims paragraphs must be preserved verbatim in substance without softening, hedging, or trimming.

---

## 8. Zenodo Republication Metadata, Manifests & Notebook Execution Invariants (`RULE_CODA_REPUBLICATION_ENVELOPE_001`)

> **Republication Gate & Manifest Invariants:**
>
> 1. **Two-Way Manifest Sealing:**
>    Every publication envelope must provide `MANIFEST.sha256` covering all non-manifest payload files and a distinct `SHA256SUMS` manifest sealing the entire tree (including `MANIFEST.sha256`). Both files must be sorted in ordinal UTF-8 byte order.
> 2. **Zenodo Publication Metadata Companion:**
>    Zenodo republication envelopes must carry `zenodo_metadata.json` matching manuscript front-matter metadata and `release_identity.json` (title, version, publication date, description, license, upload_type, and creators).
> 3. **Public Dialect Token Prohibition:**
>    Public monographs and paper preprints must not include internal governance dialect tokens like `AuthorityEffect`; use `Authorization` in public mechanism inventories and rendered reader-facing documents.
> 4. **Pre-Executed Notebook Invariant:**
>    Jupyter notebooks deposited with research papers under `jupyter_notebooks/` must be fully pre-executed with valid positive integer execution counts (`execution_count >= 1`) and non-error outputs. Null execution counts are prohibited in release envelopes.
