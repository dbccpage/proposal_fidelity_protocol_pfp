# Additional native systems audit — phase 03

Pinned source: `8050c66900899771766f33e8f5fdd200b7dd9120`. Status: **complete_scoped_source_review**.

This phase: **99/99 files**, **76071 lines** fully read. Cumulative native coverage: **153/153**. **0 remain unread**.

All 99 files received complete source inspection and an individual substantive assessment; the preceding two reports account for the other 54 distinct files. Hashing/parsing was not promoted to semantic review. Large pretty-printed JSON fixtures were read in consecutive source chunks with only indentation and external newlines compacted: every key, value, numeric lexeme, digest and string remained visible. Literal U+2028 was preserved with LF-only chunking. Source hashes identify working bytes; git_blob_sha256 additionally identifies pinned Git content for these 99 files. Generated capacity wrappers were inspected but do not certify their enclosing algorithms. All conclusions are implementation checks, bounded counterexamples or explicit proof obligations; no incoming pilots or private benchmark content was inspected.

The JSON contains exact hashes, reviewed ranges, per-file assessments and the complete unread backlog. Tests are not claimed rerun merely because their source was read.

- **NATIVE03-BUG-001: Caller can manufacture replay-sealed isomorphism evidence** — Different normalized terms plus self-consistent comparison hashes and fake hmac-sha256:z...z are refused unsealed, then admitted as CertifiedIsomorphism after public seal; no key or replay supplied.
- **NATIVE03-BUG-002: Foundation agent interpreter ignores supplied capability slice** — An explicitly empty skill/input/output capability slice still permits registering and executing an unlicensed callback; outcome completed=true.
- **NATIVE03-BUG-003: Koszul resolution claim depends on name rather than presentation** — Identical empty presentations named Ass/Renamed return true/false; an uncomputed Renamed_KoszulDual skeleton returns true while is_pairing_computed=false.
- **NATIVE03-BUG-004: Little-disks configuration admits conflicting dimensions** — A configuration of dimension 3 accepts a valid dimension 2 disk centered at [0,0] with radius 0.2. The radius constructor also accepts NaN, although configuration containment subsequently refuses NaN.
- **NATIVE03-RISK-005: Quadratic relation certification validates arithmetic without term semantics** — Terms 'not a tree' and 'not a tree either' with coefficients[1,-1] certify successfully.
- **NATIVE03-BUG-006: Clonal exponential decay stops after sixty halvings** — At generations 60 and 61, base 1/1 and half-life 1 both return 1/1152921504606846976; uncapped halving requires the generation 61 value 1/2305843009213693952.
- **NATIVE03-BUG-007: MHC slice count disagrees with emitted slices** — For char_len 3, window 1 and stride 10, slice_count returns 2 while present_slices("abc") emits 1.
- **NATIVE03-BUG-008: Meta proposals can activate within the current epoch** — new(5); register_proposal(5,"synthetic-new-checker"); get_active_checker_set(5) returns the proposal without enact_epoch.
- **NATIVE03-BUG-009: Rational64 residual descent can panic instead of returning a refusal** — verify_mutation with parent i64::MAX/1 and child -2/1 panics in the current debug build, although both inputs individually represent exact rationals.
- **NATIVE03-BUG-010: Zero evaporation half-life panics** — contributions [0], current_epoch 1 and half_life 0 cause a panic.
- **NATIVE03-BUG-011: Reviewed receipt asserts holdout validation that did not run** — promote_reviewed on supplied CANDIDATE returns reason Passed negative selection and holdout bank falsifiers, with no holdout evidence supplied.
- **NATIVE03-BUG-012: Suite commitment does not bind classifier or labels** — Public synthetic single-row suite retained identical commitment after disposition and classifier_digest were changed.

The sealing finding concerns the kernel public constructor. No cryptographic forgery or deployed-host bypass was demonstrated.

Validation: twelve public synthetic counterexamples reproduced in two fresh Rust probe runs; one focused existing test passed (37 filtered out). The JSON records the corrected overflow control and the disproved protected-span suspicion. Earlier broad runs and their failures remain in the preceding reports; they were not silently rerun or upgraded.

No production fixes, paid calls, private benchmark access or imported-pilot review occurred. The 153-file native source review is complete. The broader repository audit, repairs, universal proofs and empirical adequacy obligations remain open.
