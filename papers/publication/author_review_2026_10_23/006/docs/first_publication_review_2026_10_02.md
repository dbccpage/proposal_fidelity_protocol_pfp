# Paper 006: first-publication review

2026-10-02 · Version 0.1.0 · AuthorityEffect: None

**Verdict:** the revised manuscript is suitable for an initial Zenodo systems
methods preprint. It contributes a source-bound storage audit, a conditional
retained-anchor argument, exact maintenance arithmetic, and a proposed reuse
procedure. It establishes no authenticated event truth, permanent retention,
integrated semantic miner, detector effectiveness, or external publication.

The starting package was read at
`2830d21f695e28dbfcf4f07e18a66da948b4a65b`. All 31 repository package files
were checked against their Git blob identities; the original archive's 29
members, manifests, and deterministic envelope passed before editing. The historical
implementation audit remains
`52cb5457f6c485ba548cfd292f6012a941ed22cf`; its materialized source bytes were
independently checked against Git identities. This review does not label the
current default branch as that historical implementation.

## Findings and repairs

| Priority | Finding | Revision and evidence |
| --- | --- | --- |
| High | `emit_tail_receipt` reads cached state and does not inspect changed on-disk bytes. | Require successful reopening or integrity verification before persisted-snapshot comparison. A new hostile case changes disk after opening, observes the unchanged cached receipt, and then observes integrity rejection. |
| High | `record_refusal` changes memory before replacement finishes; a failed replacement does not roll back those changes. | State the unacknowledged-append and reconciliation boundary. A single injected `OSError` leaves a three-entry cached receipt and a two-entry persisted file; successful reload restores persisted state. No crash campaign is inferred. |
| Medium | A frozen dataclass and tuple do not freeze nested dictionaries. | State the reference-discipline obligation and replay a nested mutation followed by a later append whose file fails verification. |
| Medium | Count/head equality can coexist with altered header schema/genesis or formatting; the baseline does not validate the header schema. | Add header and whitespace cases and a comparison table. Separate normalized snapshot, raw-file identity, producer authentication, and independently held custody. |
| Medium | Unequal heads are also produced by legitimate extension; digest grouping was stated too broadly as byte identity. | Demonstrate extension and retained-prefix comparison. Specify covered bytes/encoding and the hash assumption; distinguish label hashes, normalized entries, raw proposals, and semantic defects. |
| Medium | Normalization loses caller types and can overwrite stringified keys before hashing. | Show rational-string aliasing and integer/string key collision. Require original authorized bytes and type/encoding declarations for exact reconstruction. |
| Medium | The default branch encoder has changed since the audited commit; historical docstring observations should not describe it as current. | Name the package and audit pins separately and record the current sink's distinct Git blob. Retain the historical audit rather than silently importing later float handling. |
| Medium | Returned clonal or regulatory records can be mistaken for applied purge/downgrade actions. | Explicitly identify consumer integration and applied-action evidence. The methods return records without mutating the frozen rules. |
| Medium | Toxicity is supplied-signal arithmetic; denominator choice and empty samples can distort a safety interpretation. | Compare 1/6 over six supplied pairs with 1/3 conditional on a match. State the 0-or-1 corpus denominator and zero-by-convention empty score. Neither substitutes for independent validity labels and observed suppressions. |
| Medium | Batching invariance needs fixed tau, a nonnegative initial score, and no reset/stimulation between calls. | State those assumptions, separate expiry from decay spacing, and supply exact worksheet calculations and the telescoping proof. |
| Medium | The catalog census required a historical Git object even though the deposit omitted that data. | Include unchanged SHA-256-bound catalog bytes with provenance. The data tests prefer the historical Git object and otherwise use the identical offline snapshot; no detector is executed by loading it. |
| Medium | Current headers retained unqualified internal v1.1 wording; pytest requirements contradicted the documented version. | Align current headers with 0.1.0, retain internal history and old receipts, and pin pytest 8.3.5. The new receipt binds today's files. |
| Medium | Five short quiz questions and a skeletal embedded key did not teach the paper's main implementation boundaries. | Add 24 questions across levels 0-7, a worked study guide, separate instructor key, 96-point rubric, and standard-library worksheet. Remove the repository-only shared worksheet dependency. |

The original earlier corrections remain: the catalog's 61 entries include
56 `candidate` labels and only five `active` labels; 49 fixture pairs are
placeholder comments. A label or identifier digest is not a reproduction or
an active filter. The new snapshot permits census replay, not admission.
The manuscript now also counts the idealized accumulated cost of individual
full-history rewrites; that is elementary accounting, not a benchmark.

## Validation and its limits

- **Focused Python replay:** 51 passed, zero skipped or failed, using Python
  3.12.14 and pytest 8.3.5. This consists of 20 baseline sink checks, 14 baseline
  immune regression checks, 11 revised worked-example/storage-boundary checks,
  three catalog checks, and three explicitly educational toy checks.
- **Lint:** Ruff 0.14.13 passes for the revised package code.
- **Educational replay:** exact normalization examples, Unicode ordering
  counterexample, catalog census, toxicity denominators, decay/stimulation,
  telescoping batch arithmetic, and byte-cost count pass. All 24 questions have
  matching keyed answers; companion links resolve inside the deposit.
- **Publication assets:** the revised manuscript was compiled to PDF, rendered
  for inspection, and checked for overflow/missing glyphs. The final manifests,
  two-way census, deterministic ZIP, and extracted release are verified in the
  accompanying receipt.

The implementation run uses a materialized subset of byte-verified sources
from the historical audit commit, with the canonical self-panel data. It does
not use a full-repository checkout or execute the default branch's revised
encoder. The package catalog tests use the exact bound snapshot; the code
does not pretend that a historical Git commit exists in the local synthetic
snapshot repository. From the archive alone, catalog and toy checks run;
storage checks skip with a source-availability reason until repository source
is supplied. The extracted-copy receipt lists those counts separately.

No native build, full-suite integration, concurrent-writer campaign,
power-failure campaign, provider/model experiment, independent learning study,
or integrated mining-yield experiment was run. The fault injection covers one
named replacement failure only. The successful finite checks do not fill those
gaps. Existing historical release receipts keep their original bytes and hashes.

## Teaching companion

The curriculum proceeds from event/authority distinctions to normalization,
integrity and prefix comparison, failures/resources, catalog provenance,
maintenance records and denominators, exact decay, and research/publication
claims. Learners must supply a calculation or counterexample and state its
contract and limit. The Apartment 50 frame is fictional; the levels and rubric
are an original curriculum, not historical Landau authority or measured gains.

## Publication and source

Use the revised manuscript PDF and matching release ZIP, with version 0.1.0.
Keep the distinct text/documentation CC BY 4.0 and code PolyForm Noncommercial
1.0.0 licenses. No deposit, reserved DOI, or publication action is claimed.
The fresh execution record is
[first_publication_validation_2026_10_02.json](first_publication_validation_2026_10_02.json).

Primary references checked for the stated boundaries include
[RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html),
[RFC 9162](https://www.rfc-editor.org/rfc/rfc9162.html),
[Schneier and Kelsey](https://www.schneier.com/academic/archives/1999/05/secure_audit_logs_to.html),
and [Reflexion v4](https://arxiv.org/abs/2303.11366v4).
The paper does not inherit authenticated logging or reasoning gains from those
references. Tested source hashes, rather than a checksum or a citation alone,
bind the particular implementation behavior reported here.
