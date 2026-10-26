# Zenodo deposit notes: initial v0.1 preprint

This candidate provides `paper.pdf` as the readable manuscript and the dated
release ZIP as its source/reproduction and learning-material package. Use the
title, creator, version 0.1.0, and description in
[zenodo_metadata.json](../zenodo_metadata.json). Choose **Publication → Preprint**
as the record's resource type. The core contribution is a curriculum-design
method with finite worked examples, not measured educational effectiveness.

## License scope

The package preserves the author's existing licenses:

| Files | License | Local text |
| --- | --- | --- |
| Manuscript Markdown, PDF, TeX; documentation; quiz, guide, instructor key | CC BY 4.0 | [LICENSE](../LICENSE) |
| Python code/tests/tools, notebook, Lean files | PolyForm Noncommercial License 1.0.0 | [LICENSE-CODE](../LICENSE-CODE) |

Zenodo's [current license guidance](https://help.zenodo.org/docs/deposit/describe-records/licenses/)
supports mixed-license uploads and custom licenses. Declare both licenses in the
form with these file scopes. Add the second as a custom license if it is not in
the selector, using the title above and
[the license text](https://polyformproject.org/licenses/noncommercial/1.0.0/).
The rights statements describe different files; they are not an offer to choose
either license for every file.

The combined-deposit `zenodo_metadata.json` is a descriptive form-field draft.
It intentionally omits a scalar `license` that would describe the entire
mixed-license record. The legacy
[deposition API](https://developers.zenodo.org/) documents a single license
applying to all uploaded files; its field structure is different from this
mixed-rights draft. Do not submit this file unchanged as a legacy API request.

## Version and evidence notes

Version 0.1.0 is the initial external preprint designation. Internal revision
1.1.0 and earlier validation records remain historical; no previous Zenodo DOI
is claimed for this version. The metadata publication date is 2026-10-02 for
this candidate; align it with the actual initial publication date when
finalizing the record.

The fresh review verifies finite Python checks, a six-cell ordinary-Python notebook replay,
isolated source-module execution, PDF rendering, and archive identity.
The Lean source and saved reports are unchanged and match the retained
source-bound build record. Lean/Lake were unavailable for fresh kernel replay.
The external 20-notebook route and any human learner study were not rerun.

A saved historical receipt must not be described as current execution, and
the proposed 96-point teaching rubric must not be described as calibrated
certification. No DOI has been reserved and no external record has been
published by this review.
