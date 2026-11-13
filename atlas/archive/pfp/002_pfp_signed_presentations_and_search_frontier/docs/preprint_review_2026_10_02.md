# PFP II: first-preprint review

**Decision:** The revised version 0.1.0 is suitable for an initial Zenodo
preprint within its stated scope. No blocking error was found in the balance
proof, fixed-basis matrix reduction, receipt coverage, or restricted
integrated-path gap after the repairs below. This is a reviewer judgment,
not publication acceptance or a general physical sign-problem classification.

**Source reviewed:** dbccpage/the_symbol_game at
`e11c07ce90318309f058c8097ffd1c440a8ffb84`, 2026-10-02.
The [execution receipt](preprint_review_validation_2026_10_02.json) binds
revised inputs by SHA-256; the manifests bind the final deposited file set.

## Mathematical and implementation assessment

The contribution is a reproducible certificate-and-replay protocol using
classical signed-graph balance, plus an exact restricted physical example.
The theorem is attributed, the linear graph solver is the appropriate
baseline, and exponential enumeration exercises the protocol rather than
improving this graph algorithm.

| Claim | Assessment |
| --- | --- |
| Gauge iff closed-walk parity vanishes | XOR proves necessity; root-to-vertex path independence proves sufficiency in each component. Loops and parallel edges are valid declared inputs. |
| Diagonal-sign matrix reduction | The entrywise sign equation exactly matches the bit convention. Zeros impose no constraint; the adapter rejects inexact or malformed matrices. |
| Stoquastic exponential positivity | The diagonal shift makes every series term nonnegative. Norm convergence is now explicit. No estimator-efficiency guarantee follows. |
| Honest frontier and continuation | UNKNOWN retains the suffix. Continuation replays contiguous prior UNKNOWN segments from zero, including bits and actual verdicts. Rehashing a false verdict does not make it pass. |
| Deterministic witness and cursor | Fixed batches and canonical consumption give the same chosen witness and receipt across worker counts; the cursor can advance beyond the first valid candidate. |
| Fock target and all-length gap | The target signs are \(+1,+1,-1\), its energy is four, and its weight is \(-e^{-1}/384\). The checker reproduces 192 paths split 96/96; finite length-three facts and analytic bounds cover every other length. |
| Absolute path convergence | Each of 64 states has at most four outgoing hops, giving \(64e^{4\beta}\) as a bound on the absolute expansion. This is distinct from an individual-path bound or a sampling-cost result. |

The path gap excludes equal-magnitude pairing of individual integrated
rooted sequences under the stated parameters. It does not exclude
time-labelled maps, collective regroupings, other bases, or other estimators.
A general physical adapter is an obligation for those larger applications,
not a missing premise of the already declared restricted theorem.

## Findings and repairs

| Finding | Effect | Resolution |
| --- | --- | --- |
| Malformed native witnesses leaked raw exceptions | Null data raised AttributeError and a truncated walk step raised IndexError, contradicting the documented typed error | Added payload shape/scalar validation and ten fixture-executable regression cases; no Python fallback is allowed |
| Current version references disagreed | The ledger/reference supplement named 1.1.0; PFP I was cited as 1.3.0 despite its current 0.1.0 header | Aligned current first-publication references and preserved historical records |
| README dependencies contradicted project metadata | It named pytest 8.3.5 while the dev requirement is at least 9.0.3 | Reconciled requirements and added the omitted native-refusal command |
| Quiz frontier disagreed with the example | Four candidates and one-based wording obscured the actual eight-candidate enumeration | Declared zero-based assignments, half-open intervals, exact 2-then-1 traces, and full-batch behavior |
| Educational coverage was too narrow | Five brief questions omitted matrix positivity, replay attacks, pairing, and the all-length gap | Added 14 scored problems at Levels 0-7, a preparation guide, and a separate worked key |
| Evidence and companion dependencies escaped the deposit | The current execution reference and an essential worksheet were outside the package | Included this review, its receipt, and package-local required readings/checks |
| Infinite-series convergence was implicit | Finite state count does not imply finite path count | Added explicit matrix and path convergence arguments and a claim-ledger entry |

The native change validates transport data before constructing witness
objects. Payload shape is not a proof of witness correctness. The core
Genesis graph/frontier algorithms retain their earlier bytes.

## Executed checks and limits

| Check | Result |
| --- | --- |
| `test_sign_graph.py` | 3 passed |
| `test_frontier_search.py` | 16 passed |
| `test_manuscript_examples.py` | 3 passed |
| `test_exact_fock_gap.py` | 9 passed |
| `test_native_sign_graph.py` | 3 passed, 1 skipped |
| `test_native_refusals.py` after repair | 13 passed |
| Six-file total | **47 passed, 1 skipped, 0 failed** |
| Code lint and added replay-tool lint | Passed |
| Exact Fock checker and all three offline demos | Passed |
| Notebook source calculations | All five code cells passed with assertions active in a fresh isolated Python process |
| New hopping-degree fact | Exhaustive 64-state check confirms maximum degree four |
| Companion | Worked examples, 14 answers, 100-point sum, and required local links checked |
| PDF | Series renderer, three XeLaTeX passes, and visual review |
| Release custody | Manifests and dated ZIP regenerated and checked |

Cargo, rustc, and a compiled native executable are unavailable here. The
native-discovery test therefore skips. Adapter tests using Python or controlled
fixture executables do not certify a Rust build.

Interactive Jupyter startup failed for both TCP and IPC because socket
creation is not permitted in this environment. The included
`tools/replay_notebook_source.py` command then passed all plain-Python source
cells. It does not verify interactive transport, display behavior, or
saved-output byte equality. The earlier kernel receipt remains unchanged
and bound to its dated input hashes.

No live provider call, GPU work, new formal proof, external deposit, or DOI
reservation was performed. The current receipt records interpreter/tool
versions and the executed scope; older counts remain historical.

## The revised Examiner companion

The [quiz](../_lev_examiner_theoretical_minimum_quiz/quiz.md) progresses from
declarations and minimal witnesses through both balance proofs, exact
matrices, exponential positivity, receipt forgery, batching, pairing, and
every Fock length class. The final problem audits the publication claim.

The [guide](../_lev_examiner_theoretical_minimum_quiz/study_guide.md) gives
prerequisites, notation, a reading route, and replay boundaries. The
[worked key](../_lev_examiner_theoretical_minimum_quiz/instructor_key.md)
provides complete solutions and partial-credit allocations totaling 100.
The 80-point competence target and oral defense are teaching conventions;
no measured learner benefit is claimed. Apartment 50 remains fictional
the novelist staging.

## References and Zenodo materials

The accessible author records for
[Klassen and Terhal](https://arxiv.org/abs/1806.05405) and
[Troyer and Wiese](https://arxiv.org/abs/cond-mat/0408370) confirm their
bibliographic entries and the distinction between local basis questions and
generic complexity results. The Harary theorem is proved in the manuscript.
Publisher/Crossref access was unavailable for a fresh page-range check;
the prior checked entry is retained as historical bibliographic evidence.

The title, date 2026-10-02, version 0.1.0, creator, and publication/preprint
designation agree with the descriptive Zenodo metadata. The existing
CC BY 4.0 text/documentation and PolyForm Noncommercial 1.0.0
code/notebook/tooling licenses are preserved.
[Zenodo's mixed-license guidance](https://help.zenodo.org/docs/deposit/describe-records/licenses/)
supports declaring both with their file scopes. This pass did not submit
or validate an API request against Zenodo.

Use the rebuilt PDF and dated release ZIP after reviewing this change set.
A later publication date or further source edits require regenerating the
date-dependent assets and rerunning custody checks for those final bytes.
No external publication status or DOI is inferred.
