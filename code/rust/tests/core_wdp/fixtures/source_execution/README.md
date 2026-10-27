# Retained source-execution oracle fixtures

AuthorityEffect: None.

These immutable test data remove the native oracle's dependency on a publication
package's internal files. The Python text is not imported or executed by Cargo.
The Rust oracle still checks both original SHA256 pins, all 3,770 transitions,
ordered runs, prices and prefix composition. No expected value was regenerated.

The original package is
`atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_witnessed_difference_programme/`.

- `inputs.json` is the exact LF content of `manifests/source_replay_inputs.json`
  at `9f2c94ae3cc7c5c57d20cf210bf931790368d489^`.
  SHA256: `09dc95dae426619c2c1237cbcb2080171aab01319b4fa6e8542883dbda2072e9`.
- `verifier.py.txt` is the exact LF content of `scripts/verify_source_execution.py`
  at the same historical revision.
  SHA256: `ed274951037cd7b91b4687a48cdfabfed492dc157035a203234c310fb3b07ff5`.
- `receipt.json` is the exact retained `evidence/source_execution_receipt.json`
  at `e7420ae75737df9dbb0785cc102e8179fa6feb8c`. Its source pins are unchanged.

The first two files were deleted during publication cleanup in commit
`9f2c94ae3cc7c5c57d20cf210bf931790368d489`; the Rust includes were left pointing
at the removed paths. Retaining these bytes does not establish a fresh execution
of the original Python verifier or extend the finite oracle's scope.

## Companion retained oracles

The sibling fixture directories use the same historical revision, original
package and LF-byte custody convention. Their `receipt.json` copies come from
the corresponding `evidence/<family>_receipt.json` at the main revision above.
Their `inputs.json` and `verifier.py.txt` copy
`manifests/<family>_inputs.json` and `scripts/verify_<family>.py` respectively.
No receipt or expected result was regenerated.

| Family | Original input SHA256 | Original verifier SHA256 |
| --- | --- | --- |
| `admission_execution` | `2b2e917be74f08599ea1b964764ed8ac3c8b05743c0015ad804efd9d15141c69` | `de23aa8c28597a39d075f97c5ffe29a41fec9ebf7071320bacbb70f1ef2057ea` |
| `gauge_result` | `71191efcbbd3fc1f3870cc715fd100dbfa6d79d011d31de5c776294c738ea90d` | `c48129a6fc7afd02efa44d17b32d91f2248a116952e6702b590440b96fcd0442` |
| `marked_result` | `c986779d29a5521226c2afd1b70b52c3378314f7cb6ad156c8adffd084d7a9d0` | `7fdb469ceb254317125d334f618f29cd27bc218ce3101724b9de6070d7b5d645` |
| `primitive_execution` | `a68cdcf832c49e5e45f2f364d5dd6002d78629fc85f75bc5f3f86baf49758f16` | `07a2d61b452485a57c1efdc02b5344246ca726a8bd8768bb7b3f27e689cb04ee` |
