# The Authority Gap: Claims, Verification, and Accountable Use in Agentic AI

Jeremy H. Carroll · Prepared edition 2.1.0 · 2026-10-16

A generated claim, a record of its evaluation, and permission to act on it are different objects. Confusing them allows an output to appear verified without the supporting process. We call this failure counterfeit descent: a claimed evaluation status unsupported by the declared checks and evidence. This paper proposes a contract for recording proposals, provenance, evaluators, unresolved obligations, and authorization decisions. Its mathematical content is narrower: finite counterexamples to composition of local acceptance, a characterization of zero conditional failure rate, and elementary verification-backlog accounting. In particular, zero local-pass/global-fail rate requires acceptance soundness on the accepted population; it does not require a boundary representation to retain every distinction relevant elsewhere. We apply these distinctions to research-paper ingestion, where file integrity, equation fidelity, proof validity, and empirical support require separate records. The reference software checks finite examples and packet consistency. It does not establish the truth of arbitrary claims, authenticate institutional authority, or measure deployment safety.

## This revision

Replaced the false necessity claim in former Lemma 7.1 with Proposition 3.1: zero NGD characterizes acceptance soundness on the evaluated support. Added Example 3.4, where NGD is zero but global evaluation cannot factor through the boundary. Restricted backlog accounting to sustained actual completions and distinguished cohort, window, and throughput ratios. Replaced unsupported deployment claims with explicit contracts and proof limits.

This is a prepared republication package, not a record of a new public deposit. The repository contains October 2026 revisions and earlier release archives; public publication history has not been independently established. Existing DOI references identify prior records or repository-declared lineage. No new version DOI is assigned here.

## Contents

- `the_authority_gap.md`: canonical manuscript; matching `.tex`, `.pdf`, and `.txt` files are generated.
- `the_authority_gap_math_spine.md`: canonical expressions with persistent equation UUIDs.
- `the_authority_gap_math_spine.json`: ordered occurrence bindings, including repeated formulas.
- `*_claim_ledger.md`: claim scope, evidence, and formalization limits; expressions and claims are distinct.
- `docs/paper_inventory.json`: parsed document nodes, byte-addressed source lines, and formula occurrences.
- `docs/render_receipt.json` and `docs/equation_locations.json`: source/build/file digests and PDF destination points.
- `code/`, `code/tests/`, and `lean4/`: finite reference implementation, regressions, and scoped formal proofs.
- `MANIFEST.sha256`, `SHA256SUMS`, and the dated ZIP: reproducible release inventory and standalone verification.

## Build and verify

Use Python 3.12 with the package's test dependencies, Pandoc, XeLaTeX, Poppler (`pdftotext`), and PyMuPDF for PDF occurrence locations. Use the Lean version in `lean4/lean-toolchain`. From this package directory:

```sh
python scripts/paper_spine.py check
python scripts/build_pdf.py
python scripts/paper_spine.py verify
python scripts/paper_spine.py inventory --output docs/paper_inventory.json
python -m pytest -q --confcutdir=. code/tests
python tools/rebuild_release.py .
python tools/rebuild_release.py . --check
python verify_deposit.py --lean
```

A mathematical edit must update the manuscript and its spine entry deliberately, retaining the equation UUID. Run `python scripts/paper_spine.py sync` to rebind occurrences after that edit. New equations require new explicit spine entries. The build never silently adopts changed mathematics.

The text export retains literal LaTeX equations. PDF-extracted prose is in `docs/rendered_text.txt`. Ordered MD/TeX/text checks preserve signs, grouping, commands, and repeated occurrences. PDF checks bind a fresh compilation to exact bytes and locate every occurrence; they do not prove independent symbolic equivalence of rendered glyphs. Written and Lean proof review remain separate. No overall correctness percentage is assigned.

Paper: CC-BY-4.0. Code: see LICENSE-CODE; the existing code license is unchanged.

`python code/verify_witnesses.py` checks the two rational cycle certificates in `docs/witnesses/`. They witness zero and positive repair residuals for those examples only.

`docs/typed_claims.json` and `docs/claim_reviews.json` demonstrate content-bound review records for the two corrected composition claims only. Their summary is not a rating of the entire paper. The Lean correspondence is recorded in `docs/formalization_map.json`.
