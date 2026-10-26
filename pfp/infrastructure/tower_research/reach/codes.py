"""The closed registry of refusal codes and caps.

AuthorityEffect: None.

Every code below is proved by one injection test that fails with exactly that
code (``tests/test_reach_receipt.py`` and ``tests/test_reach_transport.py``).
The census test refuses a code that has no injection, and an injection whose
code is not registered here.
"""

from __future__ import annotations

# reach-receipt/1 refusals: code -> (check, trigger). W1-S07 section 7.6,
# with the additions this implementation needs to name every defect exactly.
RECEIPT_CODES: dict[str, tuple[str, str]] = {
    "RR-BYTES": ("K1", "bytes are not ASCII JSON, or not their own canonical re-serialization"),
    "RR-DUP-KEY": ("K1", "a key is repeated in one object"),
    "RR-UNKNOWN-FIELD": ("K1", "a field outside the closed field set"),
    "RR-SCHEMA": ("K1", "a required field is missing, or a field has the wrong type or value"),
    "RR-FLOAT": ("K1", "a float or non-finite literal appears"),
    "RR-RATIONAL": ("K1", "a rational is not canonical num/den, or a JSON integer is negative"),
    "RR-SIZE": ("K1", "the record exceeds the size cap"),
    "RR-PIN": ("K2", "a digest or git id is malformed or does not recompute from pinned bytes"),
    "RR-PRODUCER-VERDICT": ("K3", "the producer declared a grade, terminal, outcome or verdict"),
    "RR-REPLAY": ("K4", "the positive fixture is not accepted on replay, or the checker cannot run"),
    "RR-ROWS": ("K5", "the declared fixture count differs from the fixture rows"),
    "RR-NO-POSITIVE": ("K6", "no positive fixture"),
    "RR-NO-NEGATIVE": ("K6", "the level's own negative instance is missing or not bound to the row"),
    "RR-NO-NEAR-MISS": ("K6", "no near-miss fixture"),
    "RR-NO-FLIP": ("K6", "a claimed clause has no single-edit mutation whose repair flips the verdict"),
    "RR-FIXTURE-PASSED": ("K6", "a fixture expected to be refused was accepted"),
    "RR-WRONG-REASON": ("K6", "a fixture was refused, but not with its exact declared code"),
    "RR-EMPTY-PAYLOAD": ("K6", "the positive payload carries no primitive data"),
    "RR-FLAG-ONLY": ("K6", "the positive payload is flags only, or carries a verdict-named field"),
    "RR-HOLLOW-CHECKER": ("K6", "the checker accepts, or misnames, an empty or flag-only probe"),
    "RR-AMBIGUOUS": ("K7", "more than one candidate is accepted where uniqueness is required"),
    "RR-COUNTERFEIT": ("K8", "a claimed residual class does not recompute (exact with Phi1 > 0)"),
    "RR-LIFT-TRIGGER-ONLY": ("K9", "a lift licence is claimed without every licence condition"),
    "RR-EXHAUSTION": ("K9", "a lift licence is claimed from a search that ended on budget"),
    "RR-ROLLBACK": ("K10", "d(u(x)) differs from x on an admitted old-image case"),
    "RR-NON-DESCENT": ("K10", "a new term is given an old meaning"),
    "RR-AXIOM": ("K11", "an axiom outside the carrier's allowed set, a missing report, or a forbidden token"),
    "RR-STATEMENT": ("K11", "a Lean statement digest does not recompute from source"),
    "RR-TRANSPORT-MISSING": ("K12", "the transport certificate declares no typed map"),
    "RR-TRANSPORT-COLLAPSE": ("K12", "the typed map is not injective on the target image"),
    "RR-TRANSPORT-INVALID": ("K12", "the transport certificate or its loss ledger fails a TC-* check"),
    "RR-LEAK": ("K13", "blindness is claimed while the level's text is in the inputs, or the framing names it"),
    "RR-CHAIN": ("K13", "another receipt is used as evidence"),
    "RR-GATE": ("K14", "a declared gate step is absent from the carrier's workflow at the commit"),
    "RR-NONDETERMINISTIC": ("K15", "a replay or a rebuild differs"),
    "RR-VOCABULARY": ("K16", "a watched term appears in a receipt placed inside 19L57G1"),
}

# Caps lower the terminal or grade instead of refusing (W1-S07 section 7.6).
CAPS: dict[str, str] = {
    "CAP-SELF-CONSISTENT": "the checker is not a registered checker of record, or the row is the target's own",
    "CAP-NAMED": "no transport certificate is declared",
}

# mssn.transport-certificate.v2 and mssn.loss-ledger.v2 refusals
# (W2-C05 section 5.4, with the loss-ledger rules of section 4.6).
TRANSPORT_CODES: dict[str, str] = {
    "TC-V1-PRESENTED-AS-V2": "a runtime V1 certificate is submitted where V2 is required",
    "TC-UNKNOWN-FIELD": "a field outside the closed field set",
    "TC-CRITERION-MISSING": "a criterion block is missing, empty, or N/A without a reason",
    "TC-DIGEST-MISMATCH": "a digest is malformed or does not recompute",
    "TC-SAME-CARRIER": "source and target are the same carrier",
    "TC-UNSOUND-LEDGER": "a loss count is zero or its key is blank",
    "TC-LEDGER-COMMITMENT": "the loss ledger's commitment does not recompute",
    "TC-UNBOOKED-UNMAPPED-SORT": "an unmapped sort is not booked as DROPPED in the loss ledger",
    "TC-UNBOOKED-STANDING-ENTRY": "a carrier's standing loss entry (ties, readings, bounds, blindness) is not booked",
    "TC-BLINDNESS-NOT-DROPPED": "a blind-rung or ascent transport keeps name-blindness instead of dropping it",
    "TC-C3-NOT-APPLICABLE-REFUSED": "criterion 3 is marked N/A where the level names a structure map",
    "TC-COLLAPSE": "the typed map is not a function, or not injective on the target image",
    "TC-REFRAME-REQUIRED": "the carrier or coefficient domain changes silently",
    "TC-STATUS": "status, disposition or ceiling is anything but PROPOSED / TARGET_REPLAY_REQUIRED",
    "TC-UNSUPPORTED-KIND": "a typed-map kind this version does not implement",
}

# Marks on a probe-battery row. A mark is not a refusal: it records why a probe
# was not run. ``tests/test_target_checkers.py`` exercises each one.
PROBE_MARKS: dict[str, str] = {
    "PROBE-IDENTICAL-TO-POSITIVE": "the probe equals the positive payload, so it is inapplicable and not run",
}

# Target-side codes every checker must declare (W2-C05 section 6.1).
TARGET_GENERIC_CODES = ("R_EMPTY_INPUT", "R_VERDICT_FIELD")
