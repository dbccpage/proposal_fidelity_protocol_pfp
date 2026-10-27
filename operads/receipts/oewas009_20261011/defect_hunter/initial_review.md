# OEWAS009 initial skeptical acceptance review

**CORRECTED ASSUMPTION:** The native-verifier statement below was inherited from the old epic and is false at the inspected base. Read [the explicit correction](native_assumption_correction.md); exact original review bytes are retained in `initial_review_before_correction.snapshot`. This document is an initial review, not current implementation evidence.

**Base:** `c1964010689b0d396ec6392325bd2fe0b26d97d4`. **AuthorityEffect:** None. This is a source inspection, not an executed acceptance receipt.

| Criterion | Existing evidence and smallest remaining behavior | Owner and falsifier |
| --- | --- | --- |
| Canonical custody | OEWAS007 already establishes `_ic` defaults, portable historical mapping and source/snapshot byte custody. Reuse those ports and sealed receipts. | OEOS/custody owners. Never change original registry rows or old receipt bodies to make a gate pass. |
| Typed instruction ingress | OEWAS001 already compiles the typed pair through the existing catalog and candidate plan. Compilation/detector results do not admit execution. | OEWAS001/admission owners. Missing plan/admission remains a separate refusal even after detector CLEAR. |
| Native detector port | The Rust detector/registry/profile functions exist, but the inspected Adversary adapter accepts only the externally supplied Python runtime and reports no native host action. Expose one bounded native action using existing contracts. | Scope Guard/root. Missing runtime, wrong implementation, invalid registry/profile or malformed response cannot become CLEAR. |
| Stage/task correlation | Real `run_bout` already gates non-fixture PRE_DISPATCH and matches PRE_SEAL stage/subject plus dispatch registry/profile. Existing tests characterize these already-GREEN guards. | Root. Replay another task's subject/decision, change request/body/source/approval, or transplant registry/profile; observe zero execution before refused dispatch. PRE_SEAL cannot pass with mismatched dispatch profile. |
| OEEIS candidate custody | Existing real adapter farms CANDIDATE and reads admitted-only guidance. Reuse it, with exact run/task and canonical-path readback. | Syntax Prefilter. Missing/malformed identity, write failure or idempotent retry cannot promote guidance or rewrite the bout outcome. Record typed residuals separately. |
| Evidence/claims | New behavior needs genuine RED/minimal GREEN and production mutation/restoration; already-GREEN behavior is reuse. | Adversary/QA. Pin source and selected host independently. Finite detector clearance is not instruction admission, human approval, future-estate completeness or a scientific theorem. |

Minimal acceptance is an exact native detector result bound to implementation/registry/profile, exact stage/subject and composed pre-dispatch ordering, plus real candidate readback/failure behavior. No new agency registry, generic framework, storage migration or automatic admission is needed. Full epic remains `RESEARCH_HOLD`; the bounded implementation status changes only after final source-matched results are supplied.

Defect Hunter dissent: an injected BoutObserver proves dispatch ordering, while a mock CLEAR gate does not prove native evaluation. A native host that recomputes request-derived identifiers proves finite binding only; it must not be described as independently authenticated admission. The final report must distinguish direct native tests, Python composition tests, source-attested builds and any unchanged historical evidence.
