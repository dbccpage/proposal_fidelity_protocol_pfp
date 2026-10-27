# Local validation — 2026-10-21

This records scoped local observations, not a publication or system grade.

- The shared DDC example returned `REPAIRED`, with six native-coordinated steps,
  baseline exits `[1, 0]`, post-patch exits `[0, 0]`, retained lineage and no
  integration residual. The original source hashes match the request manifest.
  Mathematical measurement is `NOT_MEASURED`; source application is
  `NOT_PERFORMED`; activation remains `HOLD` and admission `Unadmitted`.
- `adversary/tests/test_ddc_code_repair.py`: 22 pytest cases passed,
  Python 3.12, actual configured native host, no provider call.
- Paper 023's existing `code/tests/test_replay.py`: seven pytest cases passed.
  Its `code/replay.py` separately returned all six named controls true.
- Paper 025's unchanged `code/replay.py` returned all five named controls true.
  These are finite replay checks, not five model trials or five pytest cases.
- Each manuscript was rendered with the existing PFP publication module's
  Pandoc and XeLaTeX machinery, three compiler passes per paper. No overfull-line
  or missing-glyph warning was observed. Reader editions span four pages (023),
  three (025) and four (028). First-page title, author, date and version match
  the source. Extracted text blocks remain within page bounds; first pages and
  the new ownership table were also inspected visually.
- Touched Markdown passes the existing markdownlint configuration. The six
  implementation files in `source_provenance.json` match the declared Git
  revision byte-for-byte. Rendering hashes are in each paper's
  `docs/rendering.json`.

The two earlier finite proofs and replay engines are unchanged. Earlier
`replay_receipt.json`, source provenance records, deposited archives, catalogs
and historical renderings outside these author-review editions are not
rewritten or presented as new observations. No Lean proof, dependency,
development gate, model experiment, DOI or external deposit was added.
