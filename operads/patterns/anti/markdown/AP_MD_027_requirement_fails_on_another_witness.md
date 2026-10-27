---
pattern_id: AP_MD_027
name: requirement_fails_on_another_witness
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_MD_027_requirement_names_its_witness
language: markdown
authority_effect: None
---

# Anti-Pattern: Requirement Fails On Another Witness (`AP_MD_027`)

## Description

A republication check is `FAIL`, and the errors list repeats that check's requirement sentence. The same check's detail names a different defect and does not mention the requirement's object. A sibling check of that object has another status.

## Detection Signature

- Check `C02` requires that PDF text include the declared title, version, and date, and its status is `FAIL`.
- Its detail names Lean files `dence.lean` and `tudeBridge.lean`. It does not mention a title, version, or date.
- Check `A08` in the same receipt is `PASS` and says the version and date were compared.
- Check `C03` requires that TeX exist and avoid a generated maketitle block, and its status is `FAIL`.
- Its detail names Overfull `\hbox` warnings, bare URLs, and asterisk list markers under `docs/source_archive`. It does not mention `\maketitle`.
- Typed rule `R_NO_MAKETITLE` in the same folder is `PASS`.

## Witness

Historical receipts. This digest did not rerun gates, XeLaTeX, pytest, or Lean, and did not open the PDF. Source folder `_ic/inr/core_paper_reviews/wdp_six_corrections_20261009/`.

`severe_receipt.json` check `C02` has requirement "PDF text includes the declared title, version and date" and detail:

> PDF text defect: references nonexistent Lean files: dence.lean, tudeBridge.lean

The errors array repeats:

> C02 FAIL: PDF text includes the declared title, version and date

Check `A08` is `PASS`. Its detail is:

> Compared metadata version/date with manuscript, README and available citation/project versions.

Check `C03` has requirement "TeX source exists and avoids a generated maketitle block" and detail:

> TeX/Markdown defect: Overfull \hbox (62 warnings) detected in TeX log; layout clipping defect; bare URLs violating MD034 in ['docs/source_archive/coda_component_packages/cs/docs/references.md']; asterisk list style violating MD004 in ['docs/source_archive/coda_component_packages/q/docs/coda_q_legacy_ledger.md', 'docs/source_archive/superseded_derivations_20261008/coda_test_catalog.md', 'docs/source_archive/superseded_derivations_20261008/finite_observation.md'] (expected dash '-')

The errors array repeats:

> C03 FAIL: TeX source exists and avoids a generated maketitle block

`typed_gates.json` rule `R_NO_MAKETITLE` is `PASS` with an empty findings list. `R_NO_TOC` is a separate `FAIL` and names `\tableofcontents` on line 238 of `witnessed_difference_programme.tex`. That row names its own object. It is not this pattern.

## Hazard & Failure Mode

- A later note says the deposited PDF is missing its title, version, or date.
- A later note removes a `\maketitle` that this typed rule did not find.
- The Lean filename fragments, the overfull boxes, and the archive markdown lints drop out of the summary.
- The `A08` version-and-date `PASS` is cited as if `C02` had been repaired, or it is dropped.

## Dual Healthy Pattern

See [HP_MD_027_requirement_names_its_witness](../../helpful/markdown/HP_MD_027_requirement_names_its_witness.md).
