"""Package demonstration 2: the two-signal decision table.

1. Signal 1 (a pattern match) alone is diagnostic only.
2. Signal 2 (a supplied structural defect) alone refuses only when its severity
   is high or critical.
3. Both signals together refuse.
4. A proposal with neither signal is tolerated.

The Rust port is used when its binary has been built (see
``native_host_detector.py``); otherwise the Python reference is used. The
backend is printed. The table does not check that a supplied defect is real.
"""

from danger_gate import DangerDecision, DangerSeverity, Signal1Match, Signal2Danger
from demo_checks import require
from native_host_detector import evaluate_gate


def run_demo() -> dict[str, str | int]:
    print("=" * 70)
    print("DEMO 2: TWO-SIGNAL DECISION TABLE")
    print("=" * 70)

    print("\n[Case 1] Clean proposal (no Signal 1, no Signal 2)")
    dec1, backend = evaluate_gate([])
    print(f"         Backend: {backend}")
    print(f"         Decision: {dec1.decision} (Refusal: {dec1.is_refusal}, Suppressed: {dec1.is_suppressed})")
    print(f"         Rationale: {dec1.rationale}")
    require(dec1.decision == DangerDecision.TOLERATED.value, "clean proposal should be tolerated")
    require(not dec1.is_refusal, "clean proposal should not be refused")
    require(not dec1.is_suppressed, "clean proposal should not be suppressed")

    print("\n[Case 2] Signal 1 alone (a mention of a named pattern)")
    s1 = [
        Signal1Match(
            epitope_name="AM-FSP-8-TROYER-WIESE",
            pattern_matched="Troyer-Wiese sign problem",
            confidence_num=1,
            confidence_den=1,
        )
    ]
    dec2, _ = evaluate_gate(s1, None)
    print(f"         Decision: {dec2.decision} (Refusal: {dec2.is_refusal}, Suppressed: {dec2.is_suppressed})")
    print(f"         Disposition: {dec2.disposition}")
    print(f"         Rationale: {dec2.rationale}")
    require(dec2.decision == DangerDecision.DIAGNOSTIC_ONLY.value, "Signal 1 alone should be diagnostic")
    require(not dec2.is_refusal, "Signal 1 alone should not refuse")
    require(not dec2.is_suppressed, "Signal 1 alone should not suppress")

    print("\n[Case 3] Signal 2 alone (medium structural defect)")
    s2_med = Signal2Danger(
        danger_type="UNOPTIMIZED_CONTRACT_BOUND",
        severity=DangerSeverity.MEDIUM.value,
        defect_count=1,
        evidence_digest="sha256:abcd0001",
    )
    dec3, _ = evaluate_gate([], s2_med)
    print(f"         Decision: {dec3.decision} (Refusal: {dec3.is_refusal}, Suppressed: {dec3.is_suppressed})")
    print(f"         Rationale: {dec3.rationale}")
    require(dec3.decision == DangerDecision.DIAGNOSTIC_ONLY.value, "medium Signal 2 should be diagnostic")
    require(not dec3.is_refusal, "medium Signal 2 alone should not refuse")

    print("\n[Case 4] Signal 2 alone (critical defect: protected host field mutation)")
    s2_crit = Signal2Danger(
        danger_type="PROTECTED_HOST_FIELD_MUTATION",
        severity=DangerSeverity.CRITICAL.value,
        defect_count=1,
        evidence_digest="sha256:crit9999",
    )
    dec4, _ = evaluate_gate([], s2_crit)
    print(f"         Decision: {dec4.decision} (Refusal: {dec4.is_refusal}, Suppressed: {dec4.is_suppressed})")
    print(f"         Disposition: {dec4.disposition}")
    require(dec4.decision == DangerDecision.DEFENSIVE_LOCKDOWN.value, "critical Signal 2 should refuse")
    require(dec4.is_refusal, "critical Signal 2 should refuse")
    require(dec4.is_suppressed, "critical Signal 2 should suppress")

    print("\n[Case 5] Signal 1 and Signal 2 together")
    dec5, _ = evaluate_gate(s1, s2_med)
    print(f"         Decision: {dec5.decision} (Refusal: {dec5.is_refusal}, Suppressed: {dec5.is_suppressed})")
    print(f"         Disposition: {dec5.disposition}")
    print(f"         Rationale: {dec5.rationale}")
    require(dec5.decision == DangerDecision.QUARANTINED.value, "both signals should refuse")
    require(dec5.is_refusal, "both signals should refuse")
    require(dec5.is_suppressed, "both signals should suppress")

    print("\n" + "=" * 70)
    print("DEMO 2 PASSED: all five cases of the decision table behaved as listed.")
    print("=" * 70)
    return {
        "status": "PASSED",
        "demo": "demo2_two_signal_gate",
        "cases_evaluated": 5,
        "backend": backend,
    }


if __name__ == "__main__":
    raise SystemExit(0 if run_demo()["status"] == "PASSED" else 1)
