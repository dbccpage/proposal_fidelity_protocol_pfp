---
pattern_id: HP_MD_027
name: requirement_names_its_witness
category: healthy_pattern
operad_type: ColoredOp
operad_source_colours: ["Code"]
operad_target_colour: "Code"
operad_arity: 1
operad_residual: "zero"
dual_pattern: AP_MD_027_requirement_fails_on_another_witness
language: markdown
authority_effect: None
---

# Healthy Pattern: The Requirement Names Its Witness (`HP_MD_027`)

## Description

A failed check is quoted with its requirement and its detail together. If the detail does not mention the requirement's object, that object is not repaired from the row. The sibling check that does name the object keeps its own status.

## Construction

- Write the requirement sentence and the detail in the same note.
- When `C02` is `FAIL` on `dence.lean` and `tudeBridge.lean`, do not say the title, version, or date is missing. Keep `A08` `PASS` as the version-and-date row.
- When `C03` is `FAIL` on overfull boxes, a bare URL, and archive asterisk lists, do not say `\maketitle` is present. Keep `R_NO_MAKETITLE` `PASS`.
- Leave the detail's objects under their own names: two Lean filename fragments, 62 overfull `\hbox` warnings, one bare-URL path, and three `docs/source_archive` markdown paths.
- A `FAIL` whose detail names the requirement's object is not repaired by this pattern. `R_NO_TOC` names `\tableofcontents` on line 238.

## Limit

The witness in [AP_MD_027_requirement_fails_on_another_witness](../../anti/markdown/AP_MD_027_requirement_fails_on_another_witness.md) is the historical folder `wdp_six_corrections_20261009`. No gate, XeLaTeX, pytest, or Lean command was rerun. The PDF was not opened. These rows do not say whether `dence.lean` or `tudeBridge.lean` is a wrapped token or a real name.

`AP_MD_017` still owns `A02` when its detail is "All audited absolute paths must fit 250 characters." That sentence matches the path requirement. This folder's `A02` is that shape, and typed `R_WINDOWS_MAX_PATH` is `PASS` with `max_path_checked` 136. `AP_MD_020` still owns an `F02` sentence that says fresh execution remains unverified. `AP_MD_014` still owns a `PASS` whose counted payload is zero. This folder's `R_CITATION_BIJECTION` is `PASS` with `cited_count` 0 and `bib_count` 0. `D03` is `FAIL` with `Unresolved pytest references: []` and `inspected 0 references`. That empty list is not this pattern and was not given a second id. `AP_MD_009` still owns a nested `PASSED` on a failed exit. This folder's top status is `SIX_SOURCE_CORRECTIONS_VERIFIED_ARTIFACT_REBUILD_BLOCKED`, not `PASSED`.

`/adversarial-receipt-audit` still owns a green render or rebuild claim that does not match the artifact. The PDF digest is unchanged from `before_hashes.json`, `package_pdf_final.json` exits 1 because DejaVu Serif was not found, and the receipt says the PDF bytes were preserved and not synchronized. The packaging rule still forbids a release while that PDF is stale, and it still forbids editing `docs/source_archive` while repairing the live tree. This pattern does not move those archive files and does not say the PDF rendered. `/adversary-proof-scope-rule` still keeps the six source-correction notes inside their stated controls. Focused pytest `106 passed` does not close the blocked republication gate.

## Dual Anti-Pattern

See [AP_MD_027_requirement_fails_on_another_witness](../../anti/markdown/AP_MD_027_requirement_fails_on_another_witness.md).
