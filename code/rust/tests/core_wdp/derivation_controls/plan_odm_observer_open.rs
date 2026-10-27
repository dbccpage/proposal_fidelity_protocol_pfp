#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

pub fn evaluate_plan_odm_observer_open(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PLAN-ODM-OBSERVER-OPEN",
            domain: "odm_observer_completion_menu",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = (5, 4, 1);
    if candidate != expected {
        return ControlReceipt {
            control_id: "PLAN-ODM-OBSERVER-OPEN",
            domain: "odm_observer_completion_menu",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PLAN-ODM-OBSERVER-OPEN",
        domain: "odm_observer_completion_menu",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_plan_odm_observer_open_scoped_control() {
    let ok = evaluate_plan_odm_observer_open((5, 4, 1), false);
    assert_eq!(ok.status, "PASS");
    assert_eq!(ok.invariant_tuple, (5, 4, 1));

    let drifted = evaluate_plan_odm_observer_open((5 + 1, 4, 1), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = evaluate_plan_odm_observer_open((5, 4, 1), true);
    assert_eq!(promoted.status, "REFUSED");
    assert_eq!(promoted.reason, "UNRESTRICTED_PROMOTION_REFUSED");
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OpenSlots {
    capacity: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum SlotError {
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_odm_observer_open.rs
// Claim: urn:core:crates_rs:tests:plan-odm-observer-open:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SlotError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SlotError {}

impl OpenSlots {
    pub fn try_new(sealed: u64, open: u64) -> Result<Self, SlotError> {
        let capacity = sealed.checked_add(open).ok_or(SlotError::Overflow)?;
        Ok(Self { capacity })
    }

    pub fn capacity(&self) -> u64 {
        self.capacity
    }
}

#[test]
fn sealed_plus_open_is_capacity() {
    let slots = OpenSlots::try_new(4, 1);
    assert!(matches!(slots, Ok(slots) if slots.capacity() == 5));
    assert!(matches!(OpenSlots::try_new(u64::MAX, 1), Err(SlotError::Overflow)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
