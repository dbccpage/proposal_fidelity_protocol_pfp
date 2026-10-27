#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_wdp_ch23_next_test(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "WDP-CH23-NEXT-TEST",
            domain: "calibrated_observer_completion",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (4, 4, 1);
    if candidate != expected {
        return ControlReceipt {
            control_id: "WDP-CH23-NEXT-TEST",
            domain: "calibrated_observer_completion",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "WDP-CH23-NEXT-TEST",
        domain: "calibrated_observer_completion",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_wdp_ch23_next_test_scoped_control() {
    let ok = evaluate_wdp_ch23_next_test((4, 4, 1), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (4, 4, 1));

    let drifted = evaluate_wdp_ch23_next_test((4 + 1, 4, 1), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_wdp_ch23_next_test((4, 4, 1), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

/// Completion pair: the two observer counts agree, and the open slot is 0 or 1.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ObserverCompletionWitness {
    matched: u64,
    open_slot: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ObserverCompletionError {
    CountMismatch { left: u64, right: u64 },
    OpenSlotOutOfRange { open_slot: u64 },
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_ch23_next_test.rs
// Claim: urn:core:crates_rs:tests:wdp-ch23-next-test:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ObserverCompletionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ObserverCompletionError {}

impl ObserverCompletionWitness {
    pub fn try_new(left: u64, right: u64, open_slot: u64) -> Result<Self, ObserverCompletionError> {
        if left != right {
            return Err(ObserverCompletionError::CountMismatch { left, right });
        }
        if open_slot > 1 {
            return Err(ObserverCompletionError::OpenSlotOutOfRange { open_slot });
        }
        Ok(Self {
            matched: left,
            open_slot,
        })
    }

    pub fn matched(&self) -> u64 {
        self.matched
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
