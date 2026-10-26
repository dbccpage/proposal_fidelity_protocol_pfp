---
name: techne-deep-paper-composition-hasher
description: "Extract Markdown formulas and prose claims, hash their normalized text, and record a TeX match only when that digest is equal. PDF text presence and zip membership are separate checks."
operad_source_colours: ["Paper", "Code", "Proof"]
operad_target_colour: "Receipt"
operad_arity: 3
operad_residual: "unknown"
families: [governance, math, verification, paper-review]
---

# Deep Paper Composition Hasher (`techne-deep-paper-composition-hasher`)

**AuthorityEffect:** None.

## Purpose

Type Markdown formulas (`$$...$$`, `\[...\]`, `$...$`, `\(...\)`) and prose claims into Pydantic v2 models and give each one a deterministic UUID.
SHA-256 covers the raw Markdown string, its whitespace-normalized form, and its exact location anchor (`file_path:start_line:end_line:start_byte_offset:end_byte_offset:content_sha256`).
A display formula is an exact TeX match only when the normalized TeX hash equals that Markdown hash.
PDF text presence is recorded only when the full normalized LaTeX occurs in the extracted page text. A symbol, or a short snippet, is not a match.
Claim labels found in PDF text do not make the claim an exact match. The statement is not hashed against TeX or PDF.
Line hashes are counted in `total_lines_hashed` and are not stored on the manifest. `tex_location` and `pdf_location` record exact line/byte/page offsets and location hashes when matched.
Code and Lean bindings come only from claim-ledger evidence locations, copied onto formulas that sit inside the claim. The skill does not assign modules from symbols or from a paper-specific prefix table.
Zip verification passes only when every bound path, every entry in `SHA256SUMS` (or `MANIFEST.sha256`), and `docs/descriptions.md` (if present) is a member of the zip. The receipt records the SHA-256 of the zip bytes. No bindings, or any missing binding or manifest path, is a failure. `--strict` fails when forbidden hype words, in-house jargon/courtroom boilerplate (`dialect_warnings`), or author/date/version mismatches (`identity_checks`) exist. A local YAML or JSON catalog is not a deposit attestation.

## Core Capabilities

1. **Typing (`models.py`)**:
   - Pydantic v2 models for formulas, claims, and location anchors with UTF-8 byte offsets (`start_byte_offset`, `end_byte_offset`) and `location_sha256`.
   - Deterministic UUIDv5 so the same element gets the same id on another run.
   - Dual SHA-256 of the raw string and the normalized string.

2. **Extraction (`hasher.py`)**:
   - Markdown math blocks (`$$...$$`, `\[...\]`, `$...$`, `\(...\)`) and numbered claim headings.
   - TeX `equation`, `align`, `gather`, `\[...\]`, `$$...$$`, `\(...\)`, and `$...$` environments, hashed after the same normalization with line and byte offsets.
   - PDF page text and character offsets when `pymupdf` or `pypdf` is installed.
   - Cross-checks as above. Unmatched means the TeX hash is absent or different. It does not mean "close enough."

3. **Bindings & Zip Verification**:
   - Ledger `file_location`, `module_path`, `lean4.module`, or `code_evidence.tests` values.
   - Checksum manifest (`SHA256SUMS` / `MANIFEST.sha256`) and `docs/descriptions.md` cross-validation against the zip.
   - Coverage fractions count those bindings. They are not a mechanization certificate.

4. **Claim Hygiene, Dialect Firewall & Identity Parity**:
   - Forbidden promotional verbs inside claim statements and prose, with the References section exempt.
   - In-house jargon and over-guarded bureaucratic boilerplate (`AuthorityEffect`, `GTLA`, `Woland`, `OMC`, `REVIEW_SCOPE`, `Withdrawn as a theorem of this deposit`, naked `Paper 001` numbers, relative `.md` links in PDF).
   - Cross-file author, version, and publication date parity across `.md`, `.tex`, `.pdf` (page 1), `README.md`, and `zenodo_metadata.json`.

5. **Evidence Closure & Bibliography Verification**:
   - Every machine-checkable formal reference in claim ledgers must resolve to an included artifact or declare `status: external_unverified` with a pinned URN.
   - Reference titles in manuscripts and bibliographies must match primary publisher records (e.g. via DOI resolution) rather than topic-inferred descriptions.

## CLI Usage

```powershell
# Emit a local catalog. Do not commit it as an attestation.
py -3.12 omega_engine_operads/skills/techne-deep-paper-composition-hasher/hasher.py `
    omega_engine_atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction `
    --output-yaml paper_composition_manifest.yaml

# Fail unless every ledger-bound path and SHA256SUMS entry is in the zip. The receipt stores zip_sha256.
py -3.12 omega_engine_operads/skills/techne-deep-paper-composition-hasher/hasher.py `
    omega_engine_atlas/coda_atlas/F004_papers/002_projection_obstruction/000_projection_obstruction `
    --verify-zip path\to\release.zip `
    --checksum-manifest path\to\SHA256SUMS `
    --receipt-path path\to\paper_composition_receipt.json
```
