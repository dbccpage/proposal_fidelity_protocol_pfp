# Detailed definition: Publication Evidence Closure & Release Integrity (1)

**AuthorityEffect:** None.

Parent: [Publication Evidence Closure & Release Integrity](../../../../../rules/papers/rl_publication_evidence_closure_and_release_integrity.md). Load for the matching predicate, not every task.

# Rule: Publication Evidence Closure & Release Integrity

**AuthorityEffect:** None.

This rule defines publication evidence dependencies, transport scope, claim-pointer quarantine, and release byte custody. Review remediation and package re-certification follow [`rl_publication_review_remediation_and_recertification_discipline.md`](../../../../../rules/papers/rl_publication_review_remediation_and_recertification_discipline.md).

---

## Evidence Closure, Transport Discipline & Byte-Exact Release (`RULE_PUBLICATION_DEPOSIT_TRANSPORT_AND_CLOSURE_001`)

> a. **Scheduler Checks vs. Physical Transport Guarantees:** A predicate controlling computational refinement heuristics (e.g., graph-radius merge envelopes) establishes only that refinement policy. Claims about physical propagation require a separate theorem connecting the implemented dynamics, its hypotheses, and the claimed transport bound. Audits certifying computational compliance must never be framed as guarantees of physical no-leakage or formal no-signalling. Transport comparisons require paired source-perturbed and unperturbed evolutions; stationary marginals or accepted masks alone are insufficient.
> b. **Model Parameter Preservation vs. Numerical Tolerances:** Nonzero model coefficients must never be replaced with zero using an undocumented absolute comparison threshold. Model simplifications must be declared separately from numerical comparison tolerances. Nonzero model fields must be preserved, and physical invariance under simultaneous Hamiltonian scaling $H \to \lambda H$ and time scaling $t \to t/\lambda$ must be enforced.
> c. **Closure of Machine-Checkable Evidence:** Every declared machine-checkable evidence dependency must resolve to an included package artifact or a pinned external artifact with an explicit audit scope and URN. Unresolved dependencies must not be presented as verified evidence; external references must be explicitly labeled `status: external_unverified`.
> d. **Formal Theorem Type Fidelity:** Documentation and docstrings for formal proof files (e.g., Lean 4) must strictly describe the objects, carriers, and hypotheses in their checked types. References to physical trajectory errors or continuous asymptotics are prohibited when the formal declaration only establishes conditional identities on abstract finite sums.
> e. **Tolerance-Dependent Reporting Transparency:** Descriptions of numerical reporting must explicitly declare any comparison tolerance that changes reported values or classifications. A thresholded branch must never be documented as an exact branch. Positive reference errors at or below comparison tolerance must be explicitly documented (e.g. subtolerance dust convention yielding ratio 0 rather than infinity).
> f. **Byte-Exact Release Snapshot & Line-Ending Invariance:** Source text files must be normalized (LF line endings) before hashing. Release archives, loose uploads, and manifests must be generated from the same frozen byte snapshot. Verification scripts must assert exact byte equality between loose upload artifacts and ZIP archive members.
> g. **Supplement Republication Review Remediation & Sovereign Gate Codification (`RULE_SUPPLEMENT_REPUBLICATION_REVIEW_CODIFICATION_001`):**
> Whenever code review findings or republication defects (such as C01–C19) are identified in paper companion software:
> i. **Sovereign Gate Rule Codification:** Every code review finding concerning mathematical validity, certificate verification, capability preservation, input validation, or output collision must be codified as an executable gate rule in `research_papers/domain/rules/supplement_review_rules.py` with corresponding mutation injection and recovery unit tests in `research_papers/tests/rules/test_supplement_review_rules.py`. Unenforced prose rules are prohibited.
> ii. **Model-Bound Witness Verification:** Certificate checkers must recompute invariant quantities directly from primitive models/observers rather than relying on unverified boolean flags or stored claims.
> iii. **Exact Math Isolation:** Exact arithmetic/rational rails must reject binary floats (`float`, `np.floating`) and prevent foreign matrix type coercion.
> iv. **Differential Immutability & Nilpotency:** Coboundary capabilities must enforce differential immutability and verify exact nilpotency ($d_1 d_0 = 0$) at consumer entry points.
> v. **Non-Finite Input Rejection:** Numerical certificates must reject `NaN`, infinities, booleans, and negative norms before evaluating bounds.
> vi. **Atomic Path Separation:** Artifact bundle writers must reject path collisions between certificate and manifest outputs, and disallow overwriting input sources.
> vii. **Five-Step Package Re-Certification:** Following fixes, bytecode (`__pycache__`) must be pruned, checksums regenerated via `scripts/regen_sha256sums.py`, canonical archives built via `scripts/build_release_zip.py`, and deposit verification certified fail-closed via `py -3.12 verify_deposit.py --require-archive` with zero test skips.
---

## Claim Evidence Pointer Resolution & Quarantine Invariant

> **Claim Resolution & Historical Quarantine:**
>
> 1. **Claim-to-Evidence Resolution:**
>    In packages retaining claim ledgers or claim summaries, every declared Lean module, formal theorem name, and computational test function must resolve to actual, active code paths. Unaligned or non-existent references are blocker defects.
> 2. **Byte-Pinned Historical Archive Quarantine:**
>    When earlier claims or formulations preserved in byte-pinned historical archives (e.g. `*.tar.gz`) are found to be conditional or superseded, agents must NOT mutate the historical archive bytes. The retraction must be documented via an explicit `superseded_notice.md` or erratum notice outside the frozen archive, preserving byte custody while clarifying scope.

---

## Hermetic Release Archive Purity & Package Directory Preservation Invariant (`RULE_HERMETIC_RELEASE_ARCHIVE_AND_PACKAGE_PURITY_001`)

> **Single Archive & Hermetic Build Directory Preservation Law:**
>
> 1. **Single Release Archive in Estate Root (`RULE_SINGLE_RELEASE_ARCHIVE_IN_ESTATE_001`):**
>    The package root must never retain multiple dated release ZIP archives (`<slug>_<date>.zip`). When a new release archive is generated or updated, any older or secondary release archives must be purged from the estate root so that exactly one release ZIP matching `MANIFEST.sha256` and `SHA256SUMS` remains.
> 2. **Hermetic Lean 4 Package Directory Preservation (`RULE_LEAN4_PACKAGE_DIR_PRESERVATION_001`):**
>    Deposit verification scripts (`verify_deposit.py`) must preserve packaged Lake dependencies (`packagesDir: "p"`) when executing Lean 4 build gates in hermetic environments to prevent unintended external mathlib network cloning. Verification scripts must check toolchain availability (`shutil.which("lake")`) and provide clean skips (`--skip-lake`) when run in offline environments without the Lean compiler installed.
> 3. **Sovereign Rust Math Verification Parity (`RULE_SOVEREIGN_RUST_MATH_VERIFICATION_PARITY_001`):**
>    Sovereign Rust implementations in `engine/crates_rs/` must maintain exact mathematical parity with paper definitions, theorems, and checks. Benchmark cochains and operator norm evaluation must match published paper parameters without truncation or heuristic substitution.
> 4. **External Zenodo Citation Integrity (`RULE_ZENODO_BIBLIOGRAPHY_CROSS_REFERENCE_INTEGRITY_001`):**
>    Bibliographic citations referencing external Zenodo records in `docs/descriptions.md`, study guides, and manuscripts must cross-reference exact Concept and Version DOIs without identifier drift.
> 5. **Claim Discipline Ancillary Sweep (`RULE_CLAIM_DISCIPLINE_PUBLICATION_SWEEP_001`):**
>    Deposit audits must enforce claim hygiene across all accompanying pedagogical, review, and reference documents (`docs/examiner_quiz.md`, `docs/examiner_quiz_solutions.md`, `docs/descriptions.md`, `docs/study_guide.md`, `*_claim_ledger.md`), strictly rejecting un-scoped promotional verbs (`proves`, `universal`).
