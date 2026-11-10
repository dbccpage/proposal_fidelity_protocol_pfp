# Additional structured evidence audit

Snapshot: `8050c66900899771766f33e8f5fdd200b7dd9120`. Original scope: 32,261 files. This is a bounded evidence audit, not a completed mathematical or every-file review.

All 17,503 JSON/JSONL/YAML files received strict parsing and duplicate-key checks. The schema-grounded pass covered **1,527 files**: 28 judge manifests, 95 score companions, 19 governed run records, 1,070 tower records, and the JSON files supporting 25 derivation/experiment runs. A further 9,973 files were checked only as referenced bytes. The 15,976 structured files without a schema-specific check remain explicitly pending. Nineteen named source/evidence owners were read completely; only these have full-source reading receipts.

## Results that change the evidence assessment

* **Broken tower custody:** all 108 v2 witness-bundle filenames disagree with their actual SHA-256, including LF-normalized bytes and pinned Git blobs. All 108 v2 transport payload digests and all 216 v1/v2 transport record digests fail the producer-defined canonical recomputation, independently of checkout line endings. Loss commitments, canonical byte profiles, declared census arithmetic and fixture-input digests pass. The failures do not justify discarding or rewriting historical evidence.
* **Transport remains unadmitted:** all 216 generated transport records fail the current receiving closed schema despite using the same schema identifier. Their explicit `PROPOSED`, `PENDING` and `TARGET_REPLAY_REQUIRED` fields are consistent with this remaining work. No finite map name or digest establishes target preservation.
* **Scores need fresh bindings:** all 95 scores pass strict model and arithmetic checks, but seven companions fail the owning source/evidence checker, and ten cite two log paths outside the original inventory. Three current Rust source digests differ from their score bindings. A valid score token is not a current validation receipt.
* **Judge manifests have stale entries:** 2,840 listed targets pass their declared byte convention, 171 fail a hash/size comparison, and 40 lie outside the original inventory. C038 and C039 each have an outdated `declared_file_count`; the C021 ordered-lines manifest digest does not recompute. Explicit `CRLF_TO_LF` declarations were honored. Regenerated inventories were not treated as pre-run commitments.
* **Conflicting duplicate keys:** seven evidence JSON files contain 27 repeated keys with different values. They are concentrated in OPERADS source inventories and Paper 011 capture records. A last-value-wins parser hides the ambiguity.
* **One positive receipt is malformed:** the normal-forms 25-test PASS receipt has a bare string at line 159 where a property/value pair is required. Five other parse failures are empty stdout from recorded refused controls, and two are deliberate NaN/Infinity hostile fixtures; these were kept distinct.
* **Checkout conversion explains most run-input differences:** 2,626 input paths fail the raw checkout hash but match both LF-normalized bytes and their pinned Git blobs. A separate 162 target/digest comparisons over 144 input paths still disagree in raw, LF and pinned Git bytes. All outside-inventory paths remain unresolved. The receipts' historical execution claims were neither rerun nor declared false.

Every mismatching reference received a supplementary line-ending/Git diagnostic: 3,192 distinct target/digest/convention/size comparisons in total, with 2,626 explained by checkout conversion and 566 persistent content mismatches. The manifest, score source/evidence and tower findings above all survive that distinction. Raw-byte rule failures remain in the original ledgers, with per-file diagnostic links; they must not be counted as content failures without those qualifications.

## Positive bounded result

All 25 retained v1 derivation/experiment runs and 80 provider receipts pass the audited JSON arithmetic and internal bindings: nonnegative exact token sums, decimal ceiling to microusd, per-stage output caps, recorded price reservations, settled-attempt reconciliation, terminal totals and unique generation IDs. Every terminal still says `analytical_status: UNVERIFIED`. Database custody, provider authenticity, prompt regeneration, observer execution and mathematical proposal correctness remain untested.

The 204 loss ledgers are histograms of *declared* classifications. A correct histogram does not establish that a semantic property was preserved. Similarly, a score's minimum gate and mutation ratio concern the declared grades and selected mutants. These checks cannot bridge task encoding, checker adequacy, or physical interpretation.

## Reproduction and records

Run `additional_structured_evidence_audit.py` with the repository virtual environment and `-B -X utf8`; its zero exit means the audit completed, while failures remain in the ledger. Then run `additional_structured_evidence_hash_diagnostics.py` to compare all mismatches with LF-normalized bytes and original pinned Git blobs. Run `additional_structured_evidence_controls.py` for 15 positive/negative controls (15 passed). `additional_structured_evidence_report.py` assembles this report from the completed ledgers.

* `additional_structured_evidence.json`: claims, findings, source reading receipts, schema-specific per-file checks and precise limits.
* `additional_structured_evidence_automated.jsonl`: all 11,500 bounded per-file records, including referenced-byte-only checks.
* `additional_structured_evidence_references.jsonl`: every attempted reference resolution, expected/actual hash and declared normalization.
* `additional_structured_evidence_structural.jsonl`: all 17,503 parse results, never promoted to semantic review.
* `additional_structured_evidence_unsupported.jsonl`: every structured file still lacking a schema-specific review.
* `additional_structured_evidence_hash_diagnostics.jsonl`: all failing bindings compared with raw/LF/pinned-Git bytes, linked by index from each affected automated record.

No historical file, source implementation or imported top-level pilot was modified. No model calls, benchmark seed reads, private storage or database reads occurred. Counts and hashes of these ledger artifacts appear in the JSON report.
