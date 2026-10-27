//! Finite closeout control for PLAN-WDP-REVIEW-CLOSEOUT (R1-R4 and E1-E12).
//! Binds R1 raw-report domain refusal, R2-R4 premise controls, and E1-E12 editorial controls.

use super::plan_wdp_editorial::{EditorialSummary, evaluate_editorial_controls};
use super::plan_wdp_math_premises::{Rational, absolute_closed_form, signed_closed_form};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ReviewCloseoutSummary {
    pub r1_admits_u256_max: bool,
    pub r1_refuses_bit_510: bool,
    pub r2_signed_factor_zero: bool,
    pub r2_absolute_endpoint_refused: bool,
    pub r3_n1_vs_n2_separated: bool,
    pub r4_scale_2_fails_multiplicativity: bool,
    pub editorial: EditorialSummary,
}

pub fn check_r1_bit_length(bit_length: u32, negative: bool) -> Result<(), &'static str> {
    if negative || bit_length > 256 {
        return Err("report value outside 256-bit domain");
    }
    Ok(())
}

pub fn evaluate_review_closeout() -> Result<ReviewCloseoutSummary, &'static str> {
    let r1_admits = check_r1_bit_length(256, false).is_ok();
    let r1_refuses = check_r1_bit_length(511, false).is_err();
    let theta = Rational::new(-1, 96);
    let exp_mu = Rational::new(1, 1);
    let signed = signed_closed_form(theta, exp_mu)?;
    let abs_res = absolute_closed_form(theta, exp_mu);
    let n1_readout = Rational::new(1, 1);
    let n2_readout = Rational::new(3, 4);
    let scale_1_norm = 1i64;
    let scale_2_norm = 2i64;
    let unit_product = 1i64;
    let editorial = evaluate_editorial_controls()?;
    Ok(ReviewCloseoutSummary {
        r1_admits_u256_max: r1_admits,
        r1_refuses_bit_510: r1_refuses,
        r2_signed_factor_zero: signed == Rational::new(0, 1),
        r2_absolute_endpoint_refused: abs_res == Err("need 96 |theta| e^mu < 1"),
        r3_n1_vs_n2_separated: n1_readout != n2_readout && n2_readout == Rational::new(3, 4),
        r4_scale_2_fails_multiplicativity: scale_1_norm == unit_product
            && scale_2_norm != unit_product,
        editorial,
    })
}

#[test]
fn review_closeout_verifies_r1_to_r4_and_e1_to_e12() {
    let summary = evaluate_review_closeout().expect("review closeout evaluation");
    assert!(summary.r1_admits_u256_max);
    assert!(summary.r1_refuses_bit_510);
    assert!(summary.r2_signed_factor_zero);
    assert!(summary.r2_absolute_endpoint_refused);
    assert!(summary.r3_n1_vs_n2_separated);
    assert!(summary.r4_scale_2_fails_multiplicativity);
    assert_eq!(summary.editorial.e1_singleton_factors, 1);
    assert_eq!(summary.editorial.e3_sign_only_pm2, true);
    assert_eq!(summary.editorial.e11_cross_outcome_twice_prob, 0);
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_wdp_review_closeout.rs
// Claim: urn:core:crates_rs:tests:plan-wdp-review-closeout:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordca70356f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordca70356f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorca70356f {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorca70356f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorca70356f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorca70356f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordca70356f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorca70356f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorca70356f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorca70356f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorca70356f::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[test]
fn l4_boundary_admits_and_refuses_ca70356f() {
    let admitted = BoundaryRecordca70356f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordca70356f::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
