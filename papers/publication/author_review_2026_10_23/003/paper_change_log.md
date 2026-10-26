# Paper 003 change log

## 2026-10-03 — Zenodo deposit publication (v0.1.0 Preprint)

Recorded canonical Zenodo record <https://zenodo.org/records/23114331> (DOI: `10.5281/zenodo.23114331`, Concept DOI: `10.5281/zenodo.23114330`) across deposit metadata, `README.md`, publication catalog, and atlas `zenodo_records.md`.

## 2026-10-02 — First-publication review of v0.1.0

- Distinguished the main host baseline, Appendix A audit, historical correction,
  and current deposit replay. Earlier 1.x labels identify internal drafts.
- Added the complete baseline gate table and distinguished independent check
  derivation from statistical independence and constructed input coverage.
- Scoped fuel to charged batches; identified post-terminal receipt traffic,
  batch size, serialization, and elapsed time as separate resource obligations.
- Narrowed the particle-hole example to its declared transformation/hopping
  model; stated attractive-Hubbard spin/hopping/decoupling assumptions with a
  primary reference; supplied the signed-cycle gauge argument.
- Defined the false-suppression denominator and clarified route multiplicity,
  repeated-look constraints, and the combined-policy D-minus-R estimand.
- Fixed exact threshold helper input validation and finite predicate-mask
  validation; added regression checks without changing the host or gate policy.
- Aligned the declared pytest dependency with the documented 8.3.5 toolchain.
- Replaced the five-question companion with 24 problems over levels 0-7,
  a worked study guide, a separate instructor key, and portable local links.
- Recorded fresh replay separately from historical receipts, rebuilt the PDF,
  and refreshed the manifests and deterministic archive. No provider experiment,
  new route integration, external publication, or DOI is claimed.

## 2026-10-02 — Local candidate repackaging

Aligned the current v0.1.0 candidate title and deposit metadata date with the
actual local rebuild date. Recompiled the manuscript and rebuilt the checksum
envelopes and deterministic ZIP after the quiz companion source freeze. Earlier
author-review revisions and execution receipts retain their original dates.
Current checks are scoped execution evidence; no external deposit, DOI, or
complete mathematical audit is asserted.

## 2026-09-29 — Version 1.2.0 author-review revision

Manuscript:

- Added Appendix A, "Two signals, one detector", with three lemmas and their
  proofs. Lemma A: when Signal 2 is computed from Signal 1, the decision depends
  on the match count alone, `DIAGNOSTIC_ONLY` is reachable only if the two
  signals can disagree about presence, and when Signal 2 is present exactly with
  Signal 1 only `TOLERATED` and one refusal are reachable. Lemma B: the Hill-type
  quorum activates exactly when the positive signals sum to at least
  $K (t/(1-t))^{1/n}$; at $t = 1/2$ the Hill coefficient does not matter, one
  sensor can activate it, and an agent count follows only from a per-sensor
  bound. Lemma C: screening a detector against a self panel is sound for every
  panel exactly when the executed predicate implies the screened one.
- Appendix A.5 audits the repository at commit
  `30609de2c3928238715375a9bac608256fa381d8` against the lemmas: the packaged
  immune demonstration derives Signal 2 from the match count; the allostery gate
  is the sum threshold of Lemma B, with a comment that claims a two-signal
  requirement the code does not enforce; and three of four matchers never
  execute the pattern the screen tests. Each finding names its correction,
  commit `fdc0035a8`, and the test that covers it.
- Appendix A.6 describes anti-skill V2 as a realized admission record of the
  kind Section 3 proposes (closed predicate language, positive and negative
  controls in at least two contexts, derived receipts, a human decision), and
  records that its registry is not active.
- The abstract and Section 3 point to the appendix; Section 8.1 lists the new
  test file.

Package:

- Added `code/detector_lemmas.py` (standard library only, exact fractions,
  refuses floats and Booleans) and `code/tests/test_two_signals_one_detector.py`
  (15 tests, exhaustive over the finite domains stated in the appendix).
- Version 1.2.0, dated 2026-09-29, in the manuscript, claim ledger, `README.md`,
  `docs/descriptions.md`, `zenodo_metadata.json` and `pyproject.toml`.

## 2026-09-28 — Version 1.1.0 author-review revision

Manuscript:

- Rewrote Section 3.1 as four candidate phrase detectors. Each fixture sentence
  is now labelled as constructed text written by the authors. None of the four
  earlier “observed text” quotations was found verbatim in a retained model
  transcript: the AM-FSP-8 sentence adapts an author-written scripted response
  (“a universal” became “an unrestricted”), the AM-FSP-2 sentence is a clause of
  an author-written scripted response, and the AM-FSP-7 and AM-FSP-4 sentences
  have no retained source.
- AM-FSP-2: corrected the physics. The attractive Hubbard model with equal spin
  populations is sign-problem-free in determinant QMC on any lattice; a bipartite
  lattice is needed for the particle-hole transformation. The detector now
  targets only claims of particle-hole symmetry on non-bipartite lattices, and
  the paper records that the earlier phrase “attractive u < 0” would have
  flagged a true statement. The signed-triangle gauge example is kept.
- AM-FSP-7: no longer states Kramers degeneracy as the positivity criterion; cites
  the sufficient conditions of Li, Jiang and Yao (2016) and Wei, Wu, Li, Zhang
  and Xiang (2016), which a phrase match cannot check.
- AM-FSP-4: narrowed to meron-cluster claims; removed the group-averaging
  (Burnside, character-sum) phrases that had been filed under the same
  identifier.
- AM-FSP-8: states that the Troyer–Wiese result concerns a generic solution for
  a class of frustrated models (worst-case hardness), not the failure of any
  particular method.
- Added the provenance of the detector identifiers: an earlier harvest of 112
  rows, 102 author-written and 10 from one model, labelled without an independent
  checker.
- Corrected Sections 4 and 5 against the baseline host: default fuel 12; an
  empty batch is charged and recorded as `ACCEPTED`, not refused; fuel
  exhaustion is recorded on the next attempted batch; digests use ASCII-escaped
  sorted-key JSON, not RFC 8785; the step receipt records moves, not event-byte
  hex. Added Section 4.1 listing how the package re-implementation differs from
  the baseline host.
- Removed the mechanism inventory table. Split Section 8 into package checks and
  repository checks, the latter labelled as requiring the full repository
  checkout. Replaced the verification section with the current text. Corrected
  the Wei et al. (2016) title and added venues, DOIs, and the Troyer–Wiese and
  Chandrasekharan–Wiese references. Reworded the ledger's exclusion concerning
  formal proof-assistant models without changing its meaning.

Withdrawn or narrowed:

- The ledger claim that 28 adversarial probe runs isolated four recurring
  failure modes (13 detections, 15 grounded witnesses) is withdrawn; the 28 rows
  are 18 author-written responses and 10 responses from one model.
- The package receipt check is no longer described as cryptographic
  verification; it recomputes a digest chain and refuses certificate labels.

Package:

- Removed `code/__init__.py` and `code/tests/__init__.py`, which made the
  package's `code/` folder shadow the standard-library `code` module and caused
  a pytest internal error under Python 3.13; added `code/tests/conftest.py`.
- Phrase lists changed in `code/canaries.py` and `code/rust/src/canaries.rs` as
  above; the bare name “troyer-wiese” (a mention, not a claim) was removed.
- `code/native_host_detector.py` now finds the Rust binary only in this package
  or at an explicitly named path, and raises instead of silently falling back.
- Demonstration scripts use explicit checks instead of `assert`. The
  candidate-response demo is offline unless `--live` is given, reads no `.env`
  file implicitly, prints no key, and raises Signal 2 only for structural
  defects, so a phrase match alone stays diagnostic.
- The package receipt verifier now returns a typed refusal for non-hex event
  bytes and non-string cell coordinates instead of raising, and an assembled
  receipt is labelled `ASSEMBLED` rather than `VERIFIED` before verification.
- Lint and type-check findings fixed; ruff, pytest, and mypy settings pinned in
  `pyproject.toml`. Release tools refreshed from the series template. Moved
  `completion_supplement.md` to `docs/`. Rewrote `README.md`,
  `docs/descriptions.md`, `docs/references.md`, and `zenodo_metadata.json`;
  removed placeholder DOIs from the references.
- Repaired broken relative links in `docs/validation.md`,
  `docs/review_response.md`, `docs/functional_boundary_register.md`,
  `demos/README.md`, and `demos/demo_eis_failure_classes/README.md`, and removed
  a governance token from `docs/validation.md`. No recorded result, trace, or
  receipt was changed.

## 2026-09-28 — First-publication review revisions (implementation & evidence alignment)

- **Fuel accounting & attempt bounds (Finding 1):** Enforced strict 1-unit attempt cost outside semantic rollback in both Python and Rust hosts. Empty batches and structural rejections (e.g. moves after `VERIFY`) consume 1 unit of attempt fuel. Repeated refusals deplete remaining fuel to 0 and halt in `HostPhase.TERMINAL` with `HostExit.FUEL_EXHAUSTED`, strictly bounding attempts.
- **Cryptographic receipt replay & forgery rejection (Finding 2):** Connected `assemble_receipt()` to real `Demo3HostEngine` execution across all 30 matrix cells (5 fixtures $\times$ 6 arms). Updated `verify_receipt_bytes()` to cryptographically replay SHA-256 event chains from `initial_digest` and reject blank JSON (`{}`), malformed records, chain discontinuities, or unauthenticated certificate claims (`SCOPED_CERTIFICATE`, `ACCEPTED_CERTIFICATE`).
- **Live proposer demo candidate evaluation (Finding 3):** Fully updated `live_proposer_demo.py` to parse candidate response text/JSON, compute real SHA-256 evidence digests, evaluate Two-Signal Gate decisions, and execute valid moves against `Demo3HostEngine`. Structured outcome fields (`synthetic_execution`, `live_acquisition`, `detector_evaluation`, `witness_verification`) separate candidate parsing from route verification, reporting `UNAVAILABLE_VERIFICATION` under missing native ports.
- **Canary patterns & mathematical scope boundaries (Finding 4):** Added exact quoted manuscript failure texts to `canaries.py` and `canaries.rs`; added strict clean-case zero-finding assertions in `demo3_canaries_audit.py` and `test_demo_3_host.py`. Revised §3.1 with the $3 \times 3$ signed triangle counterexample ($H = [[0, 1, -1], [1, 0, 1], [-1, 1, 0]]$ with $S = \operatorname{diag}(1, -1, 1)$), establishing that non-bipartiteness alone does not obstruct a diagonal sign gauge and that frustrated signed cycles are required. Clarified Majorana reflection-positivity vs. Kramers-positivity symmetry classes ($T^2 = -1$), citing Li, Jiang & Yao (2016) and Wei et al. (2016).
- **Decision normalization & RFC 8785 canonical JSON (Finding 5):** Normalized decision enums to wire strings (`FUEL_EXHAUSTED`) in SHA-256 hash preimages; enforced RFC 8785 canonical JSON subset (`ensure_ascii=False, allow_nan=False`).
- **Cross-language parity:** Synchronized `code/rust/src/host.rs` with `code/host_engine.py` (added missing `frustrated_square_diagonal` route, JSON escaping in `initial_digest`, 1-unit attempt fuel charge, `HOLD_DETECTOR_FEEDBACK` move); eliminated hardcoded machine path in `native_host_detector.py`.

## 2026-09-27 — PFP detector-admission paper

- Rewrote the manuscript as a standalone detector-admission paper and prespecified study protocol, pinned to source base `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
- Distinguished production two-signal admission, Demo 3 route-specific `NO_NATIVE_PORT`, finite fixture checks, and future effectiveness estimates.
- Added a complete worked refusal transaction, matched controls, held-out splits, explicit safety stopping rules, and a bounded reproduction plan.
- Replaced the claim ledger and contradictory current-facing supplements. Preserved historical raw traces and receipts.
- Relabeled earlier validation as historical. No live-model effect estimate or new native build is claimed.

## Earlier entries (historical)

The entries below describe earlier revisions and their evidence at the time.
They do not override the current manuscript or claim ledger.


## 2026-09-24 — initial author-review protocol

- Created the study protocol, claim ledger, direct review response, and package README at the user-requested Paper 003 path.
- Chose detector learning and cross-model transfer as the primary question. Prespecified the D−R effectiveness comparison, independent witness oracle, false-suppression safety outcome, assisted control, and pilot-to-principal decision rule.
- Mapped current Rust pharmacy, symgam CLI, finite Symbol Game host, multipath iterator, lift gate, OEWAS retired Python stubs, and proposed Demo 3 manifest without treating them as one integrated live host.
- Recorded the Genesis comparison as a replayable analogy and the two-spin model as a proposed calibration adapter, with no fermion-sign result.
- Repaired two bounded historical-auditor edge cases in the shared Demo 3 code: contradictory identity witness fields and mixed-type batch parsing. No live transaction runner was added.
- Added the omega_functional sole-calculation gate for Φ₁, Ξ, and Γ₂. Identified existing off-boundary paths as migration work and barred them from future live-study scoring.
- Added a [functional ownership register](docs/functional_boundary_register.md) and routed several finite Rust callers through omega_functional; retired Python DDC functional calculations until a Rust adapter exists. The register keeps remaining violations explicit.
- Source inspection began at Symbol Game 71690cbbc83cff45a6a8f0d8455f90d5f0b083d1, Genesis 89fc568a61eb22100edf4070d40eb1449c350ed4, and H3V7N5QF 64a6fbd0d0ebfa92633e35320df2dbe728220987. The initial draft and auditor changes were subsequently captured in 07e9f187f4e3e19cb0bb0634f046555c52a9486d. This is not a frozen live-study revision.

## 2026-09-24 — recovered session completion

- Recovered the interrupted task from its shared conversation and local session, then isolated commit 07e9f187 on codex/complete-paper-003. The active shared checkout and its untracked Demo 6 were preserved.
- Removed educational duplicate calculators, installed one strict native graph adapter, centralized remaining Rust residual calculations, and retired unsupported Python certificate/proxy APIs.
- Corrected obsolete R1 import links and replayed the reviewer example; added source-pattern regression checks and new refusal tests.
- Kept stored traces and notebook outputs intact. New trace records separate unverified claims from unavailable functionals; prose pairing no longer creates a Demo 2 terminal.
- Added [validation](docs/validation.md) with build/test evidence and explicit runtime availability limits. No model API calls, live study, DOI, deposit, or physical conclusion was produced.

## 0.1.0 — 2026-10-01 — initial Zenodo preprint release designation

Re-designated from internal revision 1.2.0 for the requested initial v0.1
preprint release. Prior corrections, scope limits, and retained pilot records
are unchanged. Derived publication artifacts and manifests must be rebuilt
and current verification recorded before deposit readiness is asserted.

## 2026-10-23 — author-review harness extension

Added a focused research extension linked to Paper 029. Separated implemented mechanisms, externally reported findings and unmeasured model effects. Preserved historical source pins, proofs, release archives and deposited identities. New renderings live in the dated author-review collection.

## Author-review package custody repair — 2026-10-23

Refreshed current draft manifests after manuscript revisions. Historical release
archives and deposited metadata were preserved. Author-review copies now carry
their own manifests and the ledger filename required by the existing verifier.
