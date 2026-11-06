# Paper 007: first-publication review

Jeremy H. Carroll · Version 0.1.0 · 2026-10-02

**Recommendation:** retain the work as an initial curriculum-design preprint
with the evidence limits now stated in the manuscript. The contribution is an
inspectable method for authoring finite executable lessons, a source-pinned
route map, a worked rational example, and improved teaching materials. No
participant study or quantitative educational-effect result is supplied.

The reviewed package came from commit
`b31360060128d992113b602adee326e70d223340`. All 42 original package files were
verified against their Git blob identities. The historical source audit
baseline is `52cb5457f6c485ba548cfd292f6012a941ed22cf`; 19 cited/import-related
source files were retrieved and Git-verified, and the five route Git trees
contained the 20 named notebooks. These sources were materialized separately
for inspection and focused execution; this was not a complete repository checkout.

## Corrections made

| Finding | Revision | Practical effect |
| --- | --- | --- |
| The 21-name axiom report was described as every declaration, although the full report lists 64 | Distinguish selected names, full package-local declarations, generated/private names, and imported library exclusions | Formal coverage can be audited without inflating the smaller report |
| Whitelisted axioms could be confused with used axioms | State that observed rows use only `propext` and `Quot.sound`; `Classical.choice` is permitted but not observed | A whitelist is not presented as dependency evidence |
| Saved Lean evidence and current commands were not consistently separated | Verify historical source/report hashes and named-census generation, label kernel replay unavailable locally | Retained successful runs are not republished as a fresh run |
| Cycle-sum checks can accept the wrong edge-difference sign | Add a deliberate wrong-sign control and independent predicted-coordinate checks | The lesson shows a plausible fault that a weak invariant misses |
| Five quiz questions used a different triangle and gave little graduated practice | Add 24 four-point problems at eight instructional levels, a worked guide and exact worksheet, and a separate instructor key | Learners can progress from arithmetic to checker, source, formal, and assessment reasoning |
| Stored notebook output could be mistaken for a first learner prediction | Add a proposed first-response/exposure/correction record and an unfamiliar-cycle exercise | Assessment conditions and answer exposure stay visible; the rubric remains unvalidated |
| External relative links break when the deposit is extracted | Pin external links to the historical audit commit; include a source inventory | Readers can recover the cited version and distinguish it from current source |
| Headers and development requirements disagreed | Align current materials to 0.1.0, Python 3.12+, and pytest 8.3.5 | Setup instructions identify the environment actually checked |
| A single record-wide license could misdescribe the mixed archive | Preserve both license texts; give scoped Zenodo mixed-license fields and form instructions | Documentation remains CC BY; source/notebook/Lean remain PolyForm Noncommercial |

Original dated receipts, vendored Lean source, and Lean reports retain their
bytes. The earlier internal 1.1.0 history remains in the change log. Version
0.1.0 identifies the first external preprint candidate.

## Fresh validation and limits

| Check | Observed outcome | Scope |
| --- | --- | --- |
| Standalone package tests | 13 passed, 1 skipped | The skipped printed-block test requires repository initialization dependencies |
| Published Section 3 blocks | All three execute successfully | Seven exact audit-baseline DDC modules; parent-package initialization isolated |
| Retired norm probe | Expected `FunctionalBoundaryUnavailable` | Direct call on the source-bound cochain; not a full route-notebook diagnostic |
| Companion notebook | Six ordinary Python cells reproduce deposited output data | Fresh CPython 3.12.14 process; sequential replay counters, not Jupyter kernel history |
| Replay negative controls | Altered stored output and altered historical source bytes each rejected | Demonstrates two specific integrity failures |
| Study-guide worksheet | Runs exactly as printed, included in the tests | Standard-library arithmetic and deliberate sign-fault control |
| Ruff | Passed on package code and the new publication/replay tools | Selected lint scope |
| Named census generation | Matches the deposited `Census.lean` | Structural generation check, not a Lean kernel execution |
| Historical formal bindings | Six protected formal-source/control hashes and both full-census/report hashes match the retained receipt | Saved source-bound build evidence; not a fresh proof replay |

The fresh Jupyter attempts could not start a kernel: both TCP and IPC socket
operations were unavailable on the review host. The successful alternative
executes the notebook's ordinary Python cells; it does not test Jupyter display,
IPython semantics, or widgets. Lean/Lake were absent, so the formal kernel was
not rerun. The external 20-notebook route, native adapters, complete repository
integration, and learner assessment were not run.

The source-bound checks establish the displayed finite arithmetic and specific
failure controls. The algebraic telescoping derivation supports the stated
closed-walk identity under its definitions. Neither supplies physical,
cognitive, population-transfer, or teaching-efficiency findings.

## Publication package

The Markdown manuscript, TeX, and PDF are synchronized for this candidate.
The [fresh receipt](first_publication_validation_2026_10_02.json) records commands,
versions, source hashes, observed outcomes, and the final PDF/asset bindings.
Manifest verification and deterministic archive verification establish file
identity and the included file set; they do not establish every scholarly claim.

The [deposit notes](zenodo_deposit_notes.md) supply the preprint record fields and
mixed-license declaration. The metadata JSON is a descriptive field draft for
the combined PDF/archive upload, not a legacy single-license API request.
No DOI has been reserved and no Zenodo record has been published by this review.

## Research framing

The two cited primary studies motivate worked examples and progression toward
less guided problems. They do not evaluate these notebooks, establish a
universal lesson duration, or demonstrate transfer into formal verification.
The paper's proposed participant comparison remains future work; its
instructional levels and 96-point rubric remain design choices.

Primary and official sources checked for this review:

- Sweller and Cooper (1985), *Cognition and Instruction*, 2(1), 59–89:
  <https://doi.org/10.1207/s1532690xci0201_3>
- Renkl, Atkinson, Maier, and Staley (2002), *The Journal of Experimental Education*,
  70(4), 293–315: <https://doi.org/10.1080/00220970209599510>
- The related earlier three-author report is separately cataloged at
  <https://doi.org/10.23668/psycharchives.8816>; it must not be confused with the
  four-author journal article.
- Lean's account of axioms and computation:
  <https://lean-lang.org/theorem_proving_in_lean4/Axioms-and-Computation/>
- Zenodo's mixed-license/custom-license guidance:
  <https://help.zenodo.org/docs/deposit/describe-records/licenses/>
- The legacy deposit API's single-license metadata:
  <https://developers.zenodo.org/>
