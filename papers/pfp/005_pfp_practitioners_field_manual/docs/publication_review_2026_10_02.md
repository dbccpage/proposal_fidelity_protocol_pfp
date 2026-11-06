# Paper 005: v0.1 publication review

Reviewed repository snapshot: `e11c07ce90318309f058c8097ffd1c440a8ffb84`.
Candidate: version 0.1.0, 2026-10-02. Review scope: this paper's package, worked
mathematics, source copies, educational companion, and publication assets.

The revised package is suitable as an initial instructional preprint within its
stated finite, offline-reviewed scope. The worked example's lower bound and
matching witness are sound. Several runnable input and evidence boundaries
needed correction before the surrounding guidance could be relied on. Those
corrections are recorded below and covered by regression checks. A fresh native
replay remains an open execution obligation; the revised manuscript does not
claim one. No external Zenodo deposit or DOI was created.

## Findings and corrections

| ID | Finding in the reviewed snapshot | Correction and evidence |
| --- | --- | --- |
| P005-01 | Metadata and description still named internal version 1.2.0 and date 2026-09-28 while the candidate was designated 0.1.0 | Aligned README, description, metadata, and claim-ledger header with 0.1.0 and 2026-10-02; preserved historical records |
| P005-02 | Offline compute_phi1 ignored an undeclared (d,e)=9 claim and returned zero | Reject unknown claim edges before route selection; parameterized wrong-carrier regressions |
| P005-03 | Supported Edge object keys normalized only on the native route; offline lookup returned zero for the three unit claims | Feed normalized claims to the Python enumerator and residual calculation; exact minimum-three regression |
| P005-04 | EDGE_MATCH:d,e verified 0=0 from default lookups, and malformed EDGE_MATCH could raise rather than give a scoped verdict | Require a declared directed edge; refuse absent, reversed, and malformed obligations; distinguish local and global checks |
| P005-05 | ASSERT admitted Boolean or floating-point values; a section CUT could silently ignore an undeclared vertex or admit inexact values | Refuse before active-state mutation; regression checks preserve claims, section, and admitted history |
| P005-06 | Supplying both CUT payloads silently selected the section branch | Return MoveViolation; two-payload regression |
| P005-07 | A relational CUT installed candidate claims before projection; a configured native projection error left them active without a committed history record | Restore the old claims in a finally block before propagating the error; mocked configured-adapter test checks the third calculation's failure |
| P005-08 | README and play_demo docstring still described a blanket native-error fallback | Describe the implemented configured-native versus explicitly unconfigured-Python selection; print and return selected path in worked scripts |
| P005-09 | The scripted session used (1,2,2) while the manuscript used (1,2,3) | Use (1,2,3) throughout the manuscript, session, and capstone; check returned weights and expected transitions |
| P005-10 | Earlier native pass counts read as if they certified this candidate, and the old current receipt ran only the worksheet | Preserve the old records, clearly attribute historical Windows claims, and create a new execution record with the full patched offline suite and actual skips |
| P005-11 | Five quiz questions offered little coverage of the manual's distinct checked quantities and failure boundaries | Expand to 32 questions in Levels 0-7; add worked calculations, dual lower-bound witness, near misses, a local rubric, and a tested executable capstone |
| P005-12 | An unused asyncio pytest option warned without an undeclared plugin | Remove that option from this synchronous package configuration |

## Mathematical and instructional changes

Added an abstract and explicit rational coefficient, unit, and cell declarations.
The score table separates D_c(f) at a chosen potential from Phi_w(c) for fixed
claims, including consistent replacement claims with an unadjusted potential.
The guide explains constant gauge freedom, tied minima, stationary score with
changed claims, ZERO_OBSTRUCTION versus ZERO_DEFECT, and the scope of one-edge
verification. RETRACT can increase discrepancy when restoring the original
instance; CUT non-increase does not prove global session monotonicity or finite
search termination.

The examination preserves the fictional Apartment 50 framing without treating
it as evidence. The bounded-search UNKNOWN example is explicitly an exercise
policy, not an implemented governor terminal status. The study key distinguishes
counterexamples, mathematical obstruction, input refusal, search-bound refusal,
and unavailable execution. Its capstone extends the original session through a
partial improvement with minimum two before exact replacement and restoration.
The rubric is a local teaching choice, not a measured learner-performance claim.

## Current verification and provenance

See [the JSON record](publication_review_2026_10_02.json) for exact commands,
tool versions, source comparisons, stdout/stderr, exit status, pass/skip counts,
and hashes of the tested files. Native tests skip because no reviewed executable
and pin are configured. Four source-object tests also skip because their Git
history is absent from the retrieved snapshot. Separate comparisons retrieve
the original modules at their recorded commits, verify their recorded SHA-256,
and compare the unpatched normalized AST structure. The documented patched
functions/methods are excluded from that structural comparison and checked by
the behavioral regression suite instead.

The revision keeps code/paper_033_execution_receipt.json,
code/cross_domain_symbol_game_receipt.json, and the earlier release_validation
records byte-for-byte. The rebuilt PDF and LaTeX derive from the revised
manuscript. Visual inspection checks the final PDF pages; manifest and archive
verification checks the completed package's byte custody. The execution record
excludes its own hash and the manifest/archive envelopes to avoid a circular
claim; the manifests bind the final record and assets.

## Remaining obligations and release scope

A fresh build and pinned native replay of the patched package is needed before
claiming its current native success. Existing provider scenarios are scripted
implementation examples; no new live-provider, learner, physical-domain, or
cost-comparison experiment was performed. The Python enumerator has no built-in
proposal budget and can grow combinatorially. The declared finite guide remains
useful within these limits.

The release candidate retains version 0.1.0. Its manuscript and documentation are
CC BY 4.0; the existing code and tooling license remains PolyForm Noncommercial
1.0.0. No licensing change, operational authorization, or jurisdiction change
is part of this review.
